#!/usr/bin/env python3
"""Build rev1.emb_all_openai and pool rank tables (prop_s42, prop_s0, rr_full).

Union is document_chunks (embedding IS NOT NULL) plus rev1.pool_ext_openai when
that table exists. Duplicate doc_ids across the union are refused.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

from run_exact_ladder import MANIFEST_PATH  # noqa: E402

N_GOLD_ANCHORS = 627
EMB_TABLE = "rev1.emb_all_openai"
PROP_TABLES = {42: "rev1.prop_rank_s42", 0: "rev1.prop_rank_s0"}
RR_TABLE = "rev1.rr_full_rank"
POOL_EXT = ("rev1", "pool_ext_openai")


def pg_connect():
    import psycopg2

    return psycopg2.connect(
        host=os.environ.get("PGHOST", "localhost"),
        port=os.environ.get("PGPORT", "5432"),
        user=os.environ["PGUSER"],
        password=os.environ["PGPASSWORD"],
        dbname=os.environ["PGDATABASE"],
    )


def table_exists(cur, schema: str, name: str) -> bool:
    cur.execute(
        "SELECT COUNT(*) FROM information_schema.tables "
        "WHERE table_schema=%s AND table_name=%s",
        (schema, name),
    )
    return int(cur.fetchone()[0]) > 0


def table_columns(cur, schema: str, name: str) -> set[str]:
    cur.execute(
        "SELECT column_name FROM information_schema.columns "
        "WHERE table_schema=%s AND table_name=%s",
        (schema, name),
    )
    return {str(r[0]) for r in cur.fetchall()}


def qualified(schema: str, name: str) -> str:
    return f"{schema}.{name}"


def load_manifest_first_ranks() -> dict[str, int]:
    blob = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    first: dict[str, int] = {}
    for doc in blob.get("documents") or []:
        did = str(doc.get("doc_id") or "")
        sr = doc.get("scale_rank")
        if not did or sr is None:
            continue
        if did not in first:
            first[did] = int(sr)
    return first


def write_rank_table(cur, table: str, rows: list[tuple[str, int]]) -> int:
    schema, name = table.split(".", 1)
    cur.execute(f"CREATE SCHEMA IF NOT EXISTS {schema}")
    cur.execute(f"DROP TABLE IF EXISTS {table}")
    cur.execute(f"CREATE TABLE {table} (doc_id text PRIMARY KEY, rank int)")
    if not rows:
        return 0
    from psycopg2.extras import execute_values

    execute_values(
        cur,
        f"INSERT INTO {table} (doc_id, rank) VALUES %s",
        rows,
        page_size=5000,
    )
    cur.execute(f"CREATE INDEX IF NOT EXISTS {name}_rank_idx ON {table} (rank)")
    return len(rows)


def load_rank_map(cur, table: str) -> dict[str, int]:
    cur.execute(f"SELECT doc_id, rank FROM {table}")
    return {str(r[0]): int(r[1]) for r in cur.fetchall()}


def fetch_chunk_rows(cur) -> list[tuple[str, bool, int | None, str]]:
    cur.execute(
        """
        SELECT doc_id, is_gold_anchor, scale_rank, source_type
        FROM document_chunks
        WHERE embedding IS NOT NULL
        ORDER BY doc_id
        """
    )
    out: list[tuple[str, bool, int | None, str]] = []
    for r in cur.fetchall():
        if not r[0]:
            continue
        sr = None if r[2] is None else int(r[2])
        out.append((str(r[0]), bool(r[1]), sr, str(r[3] or "")))
    return out


def refuse_duplicate_doc_ids(cur, pool_ext_exists: bool) -> None:
    cur.execute(
        """
        SELECT doc_id, COUNT(*) AS n
        FROM document_chunks
        WHERE embedding IS NOT NULL
        GROUP BY doc_id
        HAVING COUNT(*) > 1
        LIMIT 5
        """
    )
    chunk_dups = cur.fetchall()
    if chunk_dups:
        sample = [str(r[0]) for r in chunk_dups]
        raise SystemExit(f"duplicate doc_ids in document_chunks: {sample}")

    if not pool_ext_exists:
        return

    ext = qualified(*POOL_EXT)
    cur.execute(
        f"""
        SELECT doc_id, COUNT(*) AS n
        FROM {ext}
        GROUP BY doc_id
        HAVING COUNT(*) > 1
        LIMIT 5
        """
    )
    ext_dups = cur.fetchall()
    if ext_dups:
        sample = [str(r[0]) for r in ext_dups]
        raise SystemExit(f"duplicate doc_ids in {ext}: {sample}")

    cur.execute(
        f"""
        SELECT c.doc_id
        FROM document_chunks c
        INNER JOIN {ext} p ON p.doc_id = c.doc_id
        WHERE c.embedding IS NOT NULL
        LIMIT 5
        """
    )
    overlap = [str(r[0]) for r in cur.fetchall()]
    if overlap:
        raise SystemExit(
            f"union has duplicate doc_ids across document_chunks and {ext}: {overlap}"
        )


def build_emb_all(cur, *, force: bool) -> dict[str, Any]:
    report: dict[str, Any] = {}
    schema, name = EMB_TABLE.split(".", 1)
    cur.execute("CREATE SCHEMA IF NOT EXISTS rev1")
    exists = table_exists(cur, schema, name)
    pool_ext_exists = table_exists(cur, *POOL_EXT)
    report["pool_ext_exists"] = pool_ext_exists

    if exists and not force:
        cur.execute(f"SELECT COUNT(*) FROM {EMB_TABLE}")
        n = int(cur.fetchone()[0])
        cur.execute(
            f"SELECT source_type, COUNT(*) FROM {EMB_TABLE} GROUP BY source_type"
        )
        src = {str(r[0] or "unknown"): int(r[1]) for r in cur.fetchall()}
        report[EMB_TABLE] = {"skipped": True, "n_rows": n, "source_counts": dict(sorted(src.items()))}
        print(f"{EMB_TABLE} exists n={n} (skip; --force to rebuild)")
        print(f"per_source={json.dumps(dict(sorted(src.items())))}")
        return report

    refuse_duplicate_doc_ids(cur, pool_ext_exists)

    cur.execute(f"DROP TABLE IF EXISTS {EMB_TABLE}")
    cur.execute(
        f"""
        CREATE TABLE {EMB_TABLE} (
            doc_id text PRIMARY KEY,
            source_type text,
            embedding vector(1536),
            manifest_scale_rank int
        )
        """
    )
    cur.execute(
        f"""
        INSERT INTO {EMB_TABLE} (doc_id, source_type, embedding, manifest_scale_rank)
        SELECT doc_id, source_type, embedding, scale_rank
        FROM document_chunks
        WHERE embedding IS NOT NULL
        """
    )
    n_chunks = cur.rowcount if cur.rowcount is not None and cur.rowcount >= 0 else None
    n_ext = 0
    if pool_ext_exists:
        ext = qualified(*POOL_EXT)
        cols = table_columns(cur, *POOL_EXT)
        if "doc_id" not in cols or "embedding" not in cols:
            raise SystemExit(f"{ext} missing doc_id or embedding columns: {sorted(cols)}")
        st_expr = "source_type" if "source_type" in cols else "NULL"
        cur.execute(
            f"""
            INSERT INTO {EMB_TABLE} (doc_id, source_type, embedding, manifest_scale_rank)
            SELECT p.doc_id, {st_expr}, p.embedding, NULL
            FROM {ext} p
            """
        )
        n_ext = int(cur.rowcount or 0)

    cur.execute(f"SELECT COUNT(*) FROM {EMB_TABLE}")
    n = int(cur.fetchone()[0])
    cur.execute(f"SELECT source_type, COUNT(*) FROM {EMB_TABLE} GROUP BY source_type")
    src = {str(r[0] or "unknown"): int(r[1]) for r in cur.fetchall()}
    report[EMB_TABLE] = {
        "skipped": False,
        "n_rows": n,
        "n_from_document_chunks": n_chunks,
        "n_from_pool_ext": n_ext,
        "source_counts": dict(sorted(src.items())),
    }
    print(f"{EMB_TABLE} n={n} from_chunks={n_chunks} from_pool_ext={n_ext}")
    print(f"per_source={json.dumps(dict(sorted(src.items())))}")
    return report


def fetch_union_ids(cur) -> list[str]:
    cur.execute(f"SELECT doc_id FROM {EMB_TABLE} ORDER BY doc_id")
    return [str(r[0]) for r in cur.fetchall() if r[0]]


def build_prop_ranks(
    union_ids: list[str],
    gold_ordered: list[str],
    seed: int,
) -> list[tuple[str, int]]:
    gold_set = set(gold_ordered)
    missing = [g for g in gold_ordered if g not in set(union_ids)]
    if missing:
        raise SystemExit(f"gold anchors missing from union: {missing[:5]} n={len(missing)}")
    non = sorted(did for did in union_ids if did not in gold_set)
    rng = np.random.default_rng(seed)
    perm = rng.permutation(len(non)) if non else np.array([], dtype=np.int64)
    shuffled = [non[int(i)] for i in perm]
    out: list[tuple[str, int]] = []
    for i, did in enumerate(gold_ordered):
        out.append((did, i))
    base = len(gold_ordered)
    for j, did in enumerate(shuffled):
        out.append((did, base + j))
    return out


def build_rr_full_ranks(
    union_ids: list[str],
    db_rank: dict[str, int],
    first_manifest: dict[str, int],
) -> tuple[list[tuple[str, int]], dict[str, Any]]:
    """Original schedule: DB scale_rank for indexed docs; extras continue after 100k."""
    union_set = set(union_ids)
    rows: list[tuple[str, int]] = []
    n_first_ne_db = 0
    n_from_db = 0
    n_from_manifest_only = 0
    extras: list[str] = []
    for did in union_ids:
        db_sr = db_rank.get(did)
        first = first_manifest.get(did)
        if db_sr is not None:
            if first is not None and first != db_sr:
                n_first_ne_db += 1
            rows.append((did, db_sr))
            n_from_db += 1
        elif first is not None:
            rows.append((did, first))
            n_from_manifest_only += 1
        else:
            extras.append(did)
    extras.sort()
    assigned = [r for _, r in rows]
    start = 100000
    if assigned:
        start = max(start, max(assigned) + 1)
    for i, did in enumerate(extras):
        rows.append((did, start + i))
    meta = {
        "n_from_db_scale_rank": n_from_db,
        "n_from_manifest_only": n_from_manifest_only,
        "n_extended": len(extras),
        "extended_rank_start": start if extras else None,
        "n_first_occurrence_ne_db": n_first_ne_db,
        "union_n": len(union_set),
    }
    return rows, meta


def gold_ordered_ids(chunk_rows: list[tuple[str, bool, int | None, str]]) -> list[str]:
    anchors = [(did, sr if sr is not None else 10**12) for did, is_g, sr, _st in chunk_rows if is_g]
    anchors.sort(key=lambda x: (x[1], x[0]))
    return [did for did, _sr in anchors]


def build_all_ranks(cur, *, force: bool = False) -> dict[str, Any]:
    report: dict[str, Any] = {}
    if not table_exists(cur, "rev1", "emb_all_openai"):
        raise SystemExit("missing rev1.emb_all_openai; build the union first")
    union_ids = fetch_union_ids(cur)
    chunk_rows = fetch_chunk_rows(cur)
    db_rank = {did: sr for did, _g, sr, _st in chunk_rows if sr is not None}
    gold = gold_ordered_ids(chunk_rows)
    report["n_gold_anchors"] = len(gold)
    if len(gold) != N_GOLD_ANCHORS:
        print(f"WARN: gold anchors={len(gold)} expected {N_GOLD_ANCHORS}", file=sys.stderr)
    first_manifest = load_manifest_first_ranks()

    for seed, table in PROP_TABLES.items():
        schema, name = table.split(".", 1)
        exists = table_exists(cur, schema, name)
        if exists and not force:
            nmap = load_rank_map(cur, table)
            report[table] = {"skipped": True, "n_rows": len(nmap)}
            print(f"{table} exists n={len(nmap)} (skip)")
            continue
        rows = build_prop_ranks(union_ids, gold, seed)
        n = write_rank_table(cur, table, rows)
        mx = max((r for _, r in rows), default=-1)
        report[table] = {
            "n_rows": n,
            "max_rank": mx,
            "n_anchors": len(gold),
            "seed": seed,
        }
        print(f"{table} n={n} max_rank={mx} n_anchors={len(gold)}")

    schema, name = RR_TABLE.split(".", 1)
    exists = table_exists(cur, schema, name)
    if exists and not force:
        nmap = load_rank_map(cur, RR_TABLE)
        report[RR_TABLE] = {"skipped": True, "n_rows": len(nmap)}
        print(f"{RR_TABLE} exists n={len(nmap)} (skip)")
    else:
        rows, meta = build_rr_full_ranks(union_ids, db_rank, first_manifest)
        n = write_rank_table(cur, RR_TABLE, rows)
        report[RR_TABLE] = {"n_rows": n, **meta}
        print(
            f"{RR_TABLE} n={n} from_db={meta['n_from_db_scale_rank']} "
            f"extended={meta['n_extended']} first_ne_db={meta['n_first_occurrence_ne_db']}"
        )

    report["union_n"] = len(union_ids)
    cur.execute(f"SELECT source_type, COUNT(*) FROM {EMB_TABLE} GROUP BY source_type")
    report["union_source_counts"] = dict(
        sorted((str(r[0] or "unknown"), int(r[1])) for r in cur.fetchall())
    )
    print(f"union_n={report['union_n']}")
    print(f"union_source_counts={json.dumps(report['union_source_counts'])}")
    return report


def build_union_and_ranks(cur, *, force: bool = False) -> dict[str, Any]:
    report = build_emb_all(cur, force=force)
    report.update(build_all_ranks(cur, force=force))
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--force",
        action="store_true",
        help="Rebuild emb_all_openai and rank tables even if they exist",
    )
    args = parser.parse_args()
    conn = pg_connect()
    conn.autocommit = True
    cur = conn.cursor()
    try:
        report = build_union_and_ranks(cur, force=args.force)
    finally:
        cur.close()
        conn.close()
    print(json.dumps({k: v for k, v in report.items() if k != "plan"}, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
