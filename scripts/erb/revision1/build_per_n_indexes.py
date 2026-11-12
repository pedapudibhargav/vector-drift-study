#!/usr/bin/env python3
"""Build per-ladder-size HNSW indexes in schema rev1 (task W8).

One table rev1.n_<embedder>_<N> per scale N with only documents scale_rank < N.
Resumable via rev1.build_log; skips tables already marked complete.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import psycopg2
import psycopg2.extras

ROOT = Path(__file__).resolve().parents[3]
REV1_ART = ROOT / "artifacts" / "published" / "revision1"

DEFAULT_SCALES = (
    5000,
    10000,
    15000,
    20000,
    25000,
    40000,
    50000,
    75000,
    100000,
)

EMBEDDERS: dict[str, dict[str, Any]] = {
    "openai": {
        "source_table": "document_chunks",
        "dim": 1536,
    },
    "titan": {
        "source_table": "document_chunks_titan",
        "dim": 1024,
    },
}


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def pg_connect() -> psycopg2.extensions.connection:
    conn = psycopg2.connect(
        host=os.environ.get("PGHOST", "localhost"),
        port=int(os.environ.get("PGPORT", "5432")),
        user=os.environ["PGUSER"],
        password=os.environ["PGPASSWORD"],
        dbname=os.environ["PGDATABASE"],
        connect_timeout=30,
    )
    conn.autocommit = False
    return conn


def table_name(embedder: str, n: int) -> str:
    return f"n_{embedder}_{n}"


def qualified(embedder: str, n: int) -> str:
    return f'rev1."{table_name(embedder, n)}"'


def hnsw_index_name(embedder: str, n: int) -> str:
    return f"{table_name(embedder, n)}_hnsw"


def btree_index_name(embedder: str, n: int) -> str:
    return f"{table_name(embedder, n)}_source_type"


def ensure_schema(conn: psycopg2.extensions.connection) -> None:
    with conn.cursor() as cur:
        cur.execute("CREATE SCHEMA IF NOT EXISTS rev1")
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS rev1.build_log (
                embedder text NOT NULL,
                scale_n integer NOT NULL,
                table_name text NOT NULL,
                status text NOT NULL DEFAULT 'in_progress',
                row_count bigint,
                expected_row_count bigint,
                hnsw_build_seconds double precision,
                table_bytes bigint,
                hnsw_index_bytes bigint,
                btree_index_bytes bigint,
                total_bytes bigint,
                vacuum_analyze_done boolean DEFAULT false,
                started_at timestamptz,
                completed_at timestamptz,
                error_message text,
                PRIMARY KEY (embedder, scale_n)
            )
            """
        )
    conn.commit()


def expected_row_count(conn: psycopg2.extensions.connection, source_table: str, n: int) -> int:
    with conn.cursor() as cur:
        cur.execute(
            f"""
            SELECT COUNT(*)::bigint
            FROM {source_table}
            WHERE embedding IS NOT NULL
              AND scale_rank IS NOT NULL
              AND scale_rank < %s
            """,
            (n,),
        )
        row = cur.fetchone()
        assert row is not None
        return int(row[0])


def fetch_server_info(conn: psycopg2.extensions.connection) -> dict[str, Any]:
    info: dict[str, Any] = {}
    with conn.cursor() as cur:
        cur.execute("SHOW server_version")
        info["server_version"] = cur.fetchone()[0]
        for guc in (
            "maintenance_work_mem",
            "max_parallel_maintenance_workers",
            "shared_buffers",
            "effective_cache_size",
        ):
            cur.execute(f"SHOW {guc}")
            info[guc] = cur.fetchone()[0]
        cur.execute(
            """
            SELECT extname, extversion
            FROM pg_extension
            WHERE extname IN ('vector', 'plpgsql')
            ORDER BY extname
            """
        )
        info["extensions"] = {r[0]: r[1] for r in cur.fetchall()}
    return info


def log_status(conn: psycopg2.extensions.connection, embedder: str, n: int) -> str | None:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT status FROM rev1.build_log WHERE embedder = %s AND scale_n = %s",
            (embedder, n),
        )
        row = cur.fetchone()
        return None if row is None else str(row[0])


def table_exists(conn: psycopg2.extensions.connection, embedder: str, n: int) -> bool:
    tname = table_name(embedder, n)
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT 1 FROM pg_tables
            WHERE schemaname = 'rev1' AND tablename = %s
            """,
            (tname,),
        )
        return cur.fetchone() is not None


def index_metadata(
    conn: psycopg2.extensions.connection, embedder: str, n: int
) -> dict[str, Any]:
    tname = table_name(embedder, n)
    out: dict[str, Any] = {"hnsw": None, "source_type_btree": None}
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(
            """
            SELECT indexname, indexdef
            FROM pg_indexes
            WHERE schemaname = 'rev1' AND tablename = %s
            """,
            (tname,),
        )
        for row in cur.fetchall():
            iname = row["indexname"]
            idef = row["indexdef"] or ""
            if "hnsw" in idef.lower():
                out["hnsw"] = {"name": iname, "indexdef": idef}
            elif "source_type" in idef:
                out["source_type_btree"] = {"name": iname, "indexdef": idef}
    return out


def relation_sizes(
    conn: psycopg2.extensions.connection, embedder: str, n: int
) -> dict[str, int]:
    tname = table_name(embedder, n)
    hname = hnsw_index_name(embedder, n)
    bname = btree_index_name(embedder, n)
    sizes: dict[str, int] = {}
    with conn.cursor() as cur:
        cur.execute("SELECT pg_relation_size(%s::regclass)", (f"rev1.{tname}",))
        sizes["table_bytes"] = int(cur.fetchone()[0])
        cur.execute(
            """
            SELECT COALESCE(pg_relation_size(%s::regclass), 0)
            """,
            (f"rev1.{hname}",),
        )
        sizes["hnsw_index_bytes"] = int(cur.fetchone()[0])
        cur.execute(
            """
            SELECT COALESCE(pg_relation_size(%s::regclass), 0)
            """,
            (f"rev1.{bname}",),
        )
        sizes["btree_index_bytes"] = int(cur.fetchone()[0])
        cur.execute("SELECT pg_total_relation_size(%s::regclass)", (f"rev1.{tname}",))
        sizes["total_bytes"] = int(cur.fetchone()[0])
    return sizes


def is_complete(
    conn: psycopg2.extensions.connection,
    embedder: str,
    n: int,
    expected: int,
) -> bool:
    if log_status(conn, embedder, n) != "complete":
        return False
    if not table_exists(conn, embedder, n):
        return False
    meta = index_metadata(conn, embedder, n)
    if not meta.get("hnsw") or not meta.get("source_type_btree"):
        return False
    with conn.cursor() as cur:
        cur.execute(f"SELECT COUNT(*)::bigint FROM {qualified(embedder, n)}")
        actual = int(cur.fetchone()[0])
    if actual != expected:
        return False
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT vacuum_analyze_done FROM rev1.build_log
            WHERE embedder = %s AND scale_n = %s
            """,
            (embedder, n),
        )
        row = cur.fetchone()
        if not row or not row[0]:
            return False
    return True


def drop_table(conn: psycopg2.extensions.connection, embedder: str, n: int) -> None:
    with conn.cursor() as cur:
        cur.execute(f"DROP TABLE IF EXISTS {qualified(embedder, n)} CASCADE")
        cur.execute(
            """
            UPDATE rev1.build_log
            SET status = 'dropped'
            WHERE embedder = %s AND scale_n = %s
            """,
            (embedder, n),
        )
    conn.commit()


def create_and_fill(
    conn: psycopg2.extensions.connection,
    embedder: str,
    n: int,
    dim: int,
    source_table: str,
    expected: int,
) -> None:
    qtable = qualified(embedder, n)
    started = utc_now()
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO rev1.build_log (
                embedder, scale_n, table_name, status, expected_row_count, started_at
            ) VALUES (%s, %s, %s, 'in_progress', %s, %s)
            ON CONFLICT (embedder, scale_n) DO UPDATE SET
                status = 'in_progress',
                expected_row_count = EXCLUDED.expected_row_count,
                started_at = EXCLUDED.started_at,
                error_message = NULL
            """,
            (embedder, n, table_name(embedder, n), expected, started),
        )
        cur.execute(f"DROP TABLE IF EXISTS {qtable} CASCADE")
        cur.execute(
            f"""
            CREATE TABLE {qtable} (
                doc_id text PRIMARY KEY,
                source_type text NOT NULL,
                is_gold_anchor boolean NOT NULL,
                embedding vector({dim}) NOT NULL
            )
            """
        )
        cur.execute(
            f"""
            INSERT INTO {qtable} (doc_id, source_type, is_gold_anchor, embedding)
            SELECT doc_id, source_type, is_gold_anchor, embedding
            FROM {source_table}
            WHERE embedding IS NOT NULL
              AND scale_rank IS NOT NULL
              AND scale_rank < %s
            """,
            (n,),
        )
    conn.commit()


def build_indexes(
    conn: psycopg2.extensions.connection, embedder: str, n: int
) -> float:
    qtable = qualified(embedder, n)
    hname = hnsw_index_name(embedder, n)
    bname = btree_index_name(embedder, n)
    with conn.cursor() as cur:
        cur.execute("SET maintenance_work_mem = '2GB'")
        cur.execute("SET max_parallel_maintenance_workers = 4")
        t0 = time.perf_counter()
        cur.execute(
            f"""
            CREATE INDEX "{hname}" ON {qtable}
            USING hnsw (embedding vector_cosine_ops)
            WITH (m = 16, ef_construction = 64)
            """
        )
        hnsw_seconds = time.perf_counter() - t0
        cur.execute(
            f"""
            CREATE INDEX "{bname}" ON {qtable} (source_type)
            """
        )
    conn.commit()
    return hnsw_seconds


def vacuum_analyze(conn: psycopg2.extensions.connection, embedder: str, n: int) -> None:
    old = conn.autocommit
    conn.commit()
    conn.autocommit = True
    try:
        with conn.cursor() as cur:
            cur.execute(f"VACUUM ANALYZE {qualified(embedder, n)}")
    finally:
        conn.autocommit = old


def finalize_log(
    conn: psycopg2.extensions.connection,
    embedder: str,
    n: int,
    expected: int,
    hnsw_seconds: float,
    sizes: dict[str, int],
    vacuum_done: bool,
) -> dict[str, Any]:
    with conn.cursor() as cur:
        cur.execute(f"SELECT COUNT(*)::bigint FROM {qualified(embedder, n)}")
        row_count = int(cur.fetchone()[0])
    meta = index_metadata(conn, embedder, n)
    completed = utc_now()
    with conn.cursor() as cur:
        cur.execute(
            """
            UPDATE rev1.build_log SET
                status = 'complete',
                row_count = %s,
                hnsw_build_seconds = %s,
                table_bytes = %s,
                hnsw_index_bytes = %s,
                btree_index_bytes = %s,
                total_bytes = %s,
                vacuum_analyze_done = %s,
                completed_at = %s
            WHERE embedder = %s AND scale_n = %s
            """,
            (
                row_count,
                hnsw_seconds,
                sizes["table_bytes"],
                sizes["hnsw_index_bytes"],
                sizes["btree_index_bytes"],
                sizes["total_bytes"],
                vacuum_done,
                completed,
                embedder,
                n,
            ),
        )
    conn.commit()
    return {
        "embedder": embedder,
        "scale_n": n,
        "table_name": f"rev1.{table_name(embedder, n)}",
        "row_count": row_count,
        "expected_row_count": expected,
        "hnsw_build_seconds": round(hnsw_seconds, 3),
        "sizes_bytes": sizes,
        "indexes": meta,
        "vacuum_analyze_done": vacuum_done,
        "completed_at": completed,
    }


def _walk_plans(node: dict[str, Any]) -> list[dict[str, Any]]:
    nodes = [node]
    for child in node.get("Plans") or []:
        nodes.extend(_walk_plans(child))
    return nodes


def hnsw_plan_check(conn: psycopg2.extensions.connection, embedder: str, n: int, dim: int) -> dict[str, Any]:
    qtable = qualified(embedder, n)
    probe = [0.0] * dim
    probe[0] = 1.0
    lit = "[" + ",".join(str(x) for x in probe) + "]"
    with conn.cursor() as cur:
        cur.execute(
            f"""
            EXPLAIN (FORMAT JSON)
            SELECT doc_id FROM {qtable}
            ORDER BY embedding <=> %s::vector
            LIMIT 1
            """,
            (lit,),
        )
        plan = cur.fetchone()[0]
    plan0 = plan[0]["Plan"]
    nodes = _walk_plans(plan0)
    innermost = None
    for node in reversed(nodes):
        if node.get("Index Name"):
            innermost = node
            break
    index_scan = innermost or {}
    index_name = str(index_scan.get("Index Name") or "")
    node_type = str(index_scan.get("Node Type") or plan0.get("Node Type", ""))
    expected_hnsw = hnsw_index_name(embedder, n)
    uses_hnsw = index_name == expected_hnsw or "hnsw" in index_name.lower()
    return {
        "node_type": node_type,
        "index_name": index_name,
        "uses_hnsw_index_scan": uses_hnsw,
        "plan_root": plan0,
    }


def load_build_log(conn: psycopg2.extensions.connection, embedder: str | None) -> list[dict[str, Any]]:
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        if embedder:
            cur.execute(
                """
                SELECT * FROM rev1.build_log
                WHERE embedder = %s
                ORDER BY scale_n
                """,
                (embedder,),
            )
        else:
            cur.execute("SELECT * FROM rev1.build_log ORDER BY embedder, scale_n")
        return [dict(r) for r in cur.fetchall()]


def write_artifacts(
    conn: psycopg2.extensions.connection,
    server: dict[str, Any],
    runs: list[dict[str, Any]],
    embedder: str,
    scales: list[int],
    docker_df: dict[str, Any] | None,
) -> None:
    REV1_ART.mkdir(parents=True, exist_ok=True)
    build_log = load_build_log(conn, embedder)
    payload = {
        "generated_at": utc_now(),
        "embedder": embedder,
        "scales_requested": scales,
        "server": server,
        "docker_system_df": docker_df,
        "tables_built_this_run": runs,
        "build_log": build_log,
    }
    json_path = REV1_ART / f"per_n_index_build_{embedder}.json"
    json_path.write_text(json.dumps(payload, indent=2, default=str) + "\n", encoding="utf-8")

    lines = [
        "# Per-N HNSW index build log (revision 1, W8)",
        "",
        f"Generated: {payload['generated_at']}",
        "",
        "## Server",
        "",
        f"- Version: {server.get('server_version')}",
        f"- maintenance_work_mem (session at build): 2GB",
        f"- max_parallel_maintenance_workers (session at build): 4",
        f"- pgvector: {server.get('extensions', {}).get('vector', '?')}",
        "",
    ]
    if docker_df:
        lines.append("## Docker disk (`docker system df`)")
        lines.append("")
        lines.append("```json")
        lines.append(json.dumps(docker_df, indent=2))
        lines.append("```")
        lines.append("")

    lines.extend(
        [
            "## Build results (this run)",
            "",
            "| N | rows | expected | HNSW build (s) | table (MB) | HNSW idx (MB) | btree (MB) | total (MB) |",
            "|---:|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    rows_for_md = [
        r
        for r in runs
        if not r.get("skipped") and r.get("sizes_bytes")
    ]
    if not rows_for_md:
        for row in build_log:
            if row.get("status") in ("complete", "dropped"):
                rows_for_md.append(
                    {
                        "scale_n": row["scale_n"],
                        "row_count": row["row_count"],
                        "expected_row_count": row["expected_row_count"],
                        "hnsw_build_seconds": row.get("hnsw_build_seconds") or 0,
                        "sizes_bytes": {
                            "table_bytes": row.get("table_bytes") or 0,
                            "hnsw_index_bytes": row.get("hnsw_index_bytes") or 0,
                            "btree_index_bytes": row.get("btree_index_bytes") or 0,
                            "total_bytes": row.get("total_bytes") or 0,
                        },
                    }
                )
    for r in rows_for_md:
        sz = r["sizes_bytes"]
        lines.append(
            f"| {r['scale_n']:,} | {r['row_count']:,} | {r['expected_row_count']:,} | "
            f"{r['hnsw_build_seconds']:.2f} | {sz['table_bytes']/1e6:.2f} | "
            f"{sz['hnsw_index_bytes']/1e6:.2f} | {sz['btree_index_bytes']/1e6:.2f} | "
            f"{sz['total_bytes']/1e6:.2f} |"
        )
    md_path = REV1_ART / f"per_n_index_build_{embedder}.md"
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def docker_system_df() -> dict[str, Any]:
    docker_bin = "/Applications/Docker.app/Contents/Resources/bin/docker"
    try:
        proc = subprocess.run(
            [docker_bin, "system", "df", "--format", "{{json .}}"],
            capture_output=True,
            text=True,
            timeout=60,
        )
        if proc.returncode != 0:
            return {"error": proc.stderr.strip() or f"exit {proc.returncode}"}
        rows = []
        for line in proc.stdout.splitlines():
            line = line.strip()
            if line:
                rows.append(json.loads(line))
        return {"raw_lines": rows, "stdout": proc.stdout}
    except (OSError, subprocess.TimeoutExpired, json.JSONDecodeError) as exc:
        return {"error": str(exc)}


def parse_scales(s: str | None) -> list[int]:
    if not s:
        return list(DEFAULT_SCALES)
    out = [int(x.strip()) for x in s.split(",") if x.strip()]
    return sorted(out)


def drop_existing(conn: psycopg2.extensions.connection, embedder: str, scales: list[int]) -> None:
    for n in scales:
        if table_exists(conn, embedder, n):
            print(f"DROP {embedder} N={n:,}", flush=True)
            drop_table(conn, embedder, n)


def build_one(
    conn: psycopg2.extensions.connection,
    embedder: str,
    n: int,
    cfg: dict[str, Any],
) -> dict[str, Any] | None:
    source_table = cfg["source_table"]
    dim = cfg["dim"]
    expected = expected_row_count(conn, source_table, n)

    if is_complete(conn, embedder, n, expected):
        sizes = relation_sizes(conn, embedder, n)
        with conn.cursor() as cur:
            cur.execute(f"SELECT COUNT(*)::bigint FROM {qualified(embedder, n)}")
            row_count = int(cur.fetchone()[0])
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT hnsw_build_seconds, vacuum_analyze_done
                FROM rev1.build_log
                WHERE embedder = %s AND scale_n = %s
                """,
                (embedder, n),
            )
            log_row = cur.fetchone()
        hnsw_s = float(log_row[0]) if log_row and log_row[0] is not None else 0.0
        print(
            f"SKIP complete {embedder} N={n:,} rows={row_count:,} expected={expected:,}",
            flush=True,
        )
        return {
            "embedder": embedder,
            "scale_n": n,
            "skipped": True,
            "row_count": row_count,
            "expected_row_count": expected,
            "hnsw_build_seconds": hnsw_s,
            "sizes_bytes": sizes,
            "vacuum_analyze_done": bool(log_row and log_row[1]),
        }

    print(f"BUILD start {embedder} N={n:,} expected_rows={expected:,}", flush=True)
    try:
        create_and_fill(conn, embedder, n, dim, source_table, expected)
        hnsw_seconds = build_indexes(conn, embedder, n)
        sizes = relation_sizes(conn, embedder, n)
        vacuum_analyze(conn, embedder, n)
        rec = finalize_log(conn, embedder, n, expected, hnsw_seconds, sizes, True)
        rec["skipped"] = False
        print(
            f"BUILD done {embedder} N={n:,} rows={rec['row_count']:,} "
            f"hnsw_s={hnsw_seconds:.2f} total_mb={sizes['total_bytes']/1e6:.1f}",
            flush=True,
        )
        return rec
    except Exception as exc:
        conn.rollback()
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE rev1.build_log SET status = 'failed', error_message = %s
                WHERE embedder = %s AND scale_n = %s
                """,
                (str(exc), embedder, n),
            )
        conn.commit()
        print(f"BUILD FAILED {embedder} N={n:,}: {exc}", flush=True)
        raise


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--embedder", choices=sorted(EMBEDDERS), required=True)
    parser.add_argument(
        "--scales",
        default=None,
        help="Comma-separated ladder sizes (default: full ladder)",
    )
    parser.add_argument(
        "--drop-existing",
        action="store_true",
        help="Drop rev1.n_<embedder>_<N> tables (and build_log rows) for requested scales",
    )
    parser.add_argument(
        "--plan-check",
        action="store_true",
        help="After build, EXPLAIN one-vector query and print HNSW plan check (smoke)",
    )
    parser.add_argument(
        "--skip-docker-df",
        action="store_true",
        help="Do not run docker system df",
    )
    args = parser.parse_args()

    scales = parse_scales(args.scales)
    cfg = EMBEDDERS[args.embedder]

    docker_df = None if args.skip_docker_df else docker_system_df()

    conn = pg_connect()
    try:
        ensure_schema(conn)
        server = fetch_server_info(conn)

        if args.drop_existing:
            drop_existing(conn, args.embedder, scales)
            if not args.plan_check:
                write_artifacts(conn, server, [], args.embedder, scales, docker_df)
                return

        runs: list[dict[str, Any]] = []
        for n in scales:
            rec = build_one(conn, args.embedder, n, cfg)
            if rec:
                runs.append(rec)

        if args.plan_check and scales:
            n = scales[0]
            if table_exists(conn, args.embedder, n):
                check = hnsw_plan_check(conn, args.embedder, n, cfg["dim"])
                print(
                    f"PLAN_CHECK N={n:,} node={check['node_type']} "
                    f"hnsw={check['uses_hnsw_index_scan']} index={check['index_name']}",
                    flush=True,
                )
                for r in runs:
                    if r.get("scale_n") == n:
                        r["plan_check"] = check
                        break
                else:
                    runs.append({"scale_n": n, "plan_check": check})

        write_artifacts(conn, server, runs, args.embedder, scales, docker_df)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
