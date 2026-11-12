#!/usr/bin/env python3
"""Exact cosine scale ladder with uniform (or seed-0 RR) rank tables in schema rev1."""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

from harness_lib import sha256_file  # noqa: E402
from run_exact_ladder import (  # noqa: E402
    BANK_FILES,
    DEFAULT_CONDITIONS,
    DEFAULT_SCALES,
    EMBEDDER_CONFIG,
    MANIFEST_PATH,
    METRICS,
    PLAN_CHECK_SCALES,
    PROVENANCE_DEFAULT,
    REV1,
    ROOT,
    TOP_K,
    aggregate_metrics,
    apply_seqscan_session,
    build_doc_source_map,
    condition_filter_sql,
    load_manifest,
    load_query_cache,
    parse_plan_scans,
    per_question_metrics,
    plan_probe_errors,
    plan_probe_questions,
    run_openai_preflight,
    session_pg_versions,
    vector_literal,
    write_markdown_summary,
)

DATA = ROOT / "data"
SEED0_MANIFEST = DATA / "erb_scale_manifest_seed0.json"
POOL_FILTER = "embedding IS NOT NULL AND scale_rank < 100000"

LADDERS = {
    "uniform_s42": {"rank_table": "rev1.uniform_rank_s42", "seed": 42},
    "uniform_s0": {"rank_table": "rev1.uniform_rank_s0", "seed": 0},
    "rr_s0": {"rank_table": "rev1.rr_rank_s0", "seed": 0},
}


def pg_connect():
    import psycopg2

    return psycopg2.connect(
        host=os.environ.get("PGHOST", "localhost"),
        port=os.environ.get("PGPORT", "5432"),
        user=os.environ["PGUSER"],
        password=os.environ["PGPASSWORD"],
        dbname=os.environ["PGDATABASE"],
    )


def fetch_pool(cur) -> list[tuple[str, bool, int, str]]:
    cur.execute(
        f"""
        SELECT doc_id, is_gold_anchor, scale_rank, source_type
        FROM document_chunks
        WHERE {POOL_FILTER}
        ORDER BY doc_id
        """
    )
    return [
        (str(r[0]), bool(r[1]), int(r[2]), str(r[3] or ""))
        for r in cur.fetchall()
        if r[0]
    ]


def compare_embedder_pools(cur) -> dict[str, Any]:
    cur.execute(
        f"SELECT doc_id FROM document_chunks WHERE {POOL_FILTER}"
    )
    openai = {str(r[0]) for r in cur.fetchall()}
    cur.execute(
        f"SELECT doc_id FROM document_chunks_titan WHERE {POOL_FILTER}"
    )
    titan = {str(r[0]) for r in cur.fetchall()}
    return {
        "openai_n": len(openai),
        "titan_n": len(titan),
        "only_openai": sorted(openai - titan)[:5],
        "only_titan": sorted(titan - openai)[:5],
        "n_only_openai": len(openai - titan),
        "n_only_titan": len(titan - openai),
        "equal": openai == titan,
    }


def build_uniform_ranks(pool: list[tuple[str, bool, int, str]], seed: int) -> list[tuple[str, int]]:
    anchors = [(did, sr) for did, is_g, sr, _st in pool if is_g]
    anchors.sort(key=lambda x: x[1])
    non = [did for did, is_g, _sr, _st in pool if not is_g]
    rng = np.random.default_rng(seed)
    perm = rng.permutation(len(non))
    shuffled = [non[i] for i in perm]
    out: list[tuple[str, int]] = []
    for i, (did, _sr) in enumerate(anchors):
        out.append((did, i))
    base = len(anchors)
    for j, did in enumerate(shuffled):
        out.append((did, base + j))
    return out


def manifest_rank_map(path: Path, pool_ids: set[str], db_rank: dict[str, int]) -> dict[str, int]:
    blob = json.loads(path.read_text(encoding="utf-8"))
    raw: dict[str, list[int]] = {}
    for doc in blob.get("documents") or []:
        did = str(doc.get("doc_id") or "")
        sr = doc.get("scale_rank")
        if not did or sr is None or int(sr) >= 100000:
            continue
        raw.setdefault(did, []).append(int(sr))
    out: dict[str, int] = {}
    for did in pool_ids:
        ranks = raw.get(did)
        if not ranks:
            out[did] = db_rank[did]
            continue
        if len(ranks) == 1:
            out[did] = ranks[0]
        else:
            want = db_rank[did]
            if want in ranks:
                out[did] = want
            else:
                out[did] = min(ranks)
    return out


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
    return len(rows)


def composition_for_scale(
    rank_rows: dict[str, int],
    source: dict[str, str],
    scale: int,
) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for did, rk in rank_rows.items():
        if rk < scale:
            st = source.get(did) or "unknown"
            counts[st] += 1
    return dict(sorted(counts.items()))


def load_rank_map(cur, table: str) -> dict[str, int]:
    cur.execute(f"SELECT doc_id, rank FROM {table}")
    return {str(r[0]): int(r[1]) for r in cur.fetchall()}


def build_all_ranks(cur, *, force: bool = False) -> dict[str, Any]:
    report: dict[str, Any] = {"embedder_pool_check": compare_embedder_pools(cur)}
    pool = fetch_pool(cur)
    pool_ids = {p[0] for p in pool}
    db_rank = {did: sr for did, _g, sr, _st in pool}
    source = {did: st for did, _g, _sr, st in pool}

    for seed in (42, 0):
        table = f"rev1.uniform_rank_s{seed}"
        cur.execute(
            "SELECT COUNT(*) FROM information_schema.tables "
            "WHERE table_schema='rev1' AND table_name=%s",
            (f"uniform_rank_s{seed}",),
        )
        exists = cur.fetchone()[0] > 0
        if exists and not force:
            n = load_rank_map(cur, table)
            report[table] = {"skipped": True, "n_rows": len(n)}
            continue
        rows = build_uniform_ranks(pool, seed)
        n = write_rank_table(cur, table, rows)
        mx = max(r for _, r in rows)
        report[table] = {"n_rows": n, "max_rank": mx, "n_anchors": sum(1 for p in pool if p[1])}

    rr_table = "rev1.rr_rank_s0"
    cur.execute(
        "SELECT COUNT(*) FROM information_schema.tables "
        "WHERE table_schema='rev1' AND table_name='rr_rank_s0'"
    )
    rr_exists = cur.fetchone()[0] > 0
    if rr_exists and not force:
        report[rr_table] = {"skipped": True, "n_rows": len(load_rank_map(cur, rr_table))}
    else:
        mm = manifest_rank_map(SEED0_MANIFEST, pool_ids, db_rank)
        missing = pool_ids - set(mm)
        extra = set(mm) - pool_ids
        if missing or extra:
            raise SystemExit(f"rr_s0 pool mismatch missing={len(missing)} extra={len(extra)}")
        rows = sorted(mm.items(), key=lambda x: x[0])
        n = write_rank_table(cur, rr_table, rows)
        report[rr_table] = {"n_rows": n, "manifest": str(SEED0_MANIFEST.relative_to(ROOT))}

    # N=100000 set check for uniform_s42
    u42 = load_rank_map(cur, "rev1.uniform_rank_s42")
    at_100k = {did for did, rk in u42.items() if rk < 100000}
    rr_at = {did for did, sr in db_rank.items() if sr < 100000}
    report["uniform_s42_at_100k_equals_db_scale"] = at_100k == pool_ids == rr_at

    report["pool_n"] = len(pool)
    report["pool_source_counts"] = dict(
        sorted(Counter(source.get(d, "unknown") for d in pool_ids).items())
    )
    return report


def exact_search_ladder(
    cur,
    table: str,
    rank_table: str,
    vec: list[float],
    scale: int,
    extra_where: str,
    extra_params: tuple,
    top_k: int,
) -> list[tuple[str, float]]:
    lit = vector_literal(vec)
    ew = extra_where.replace("source_type", "d.source_type")
    sql = f"""
        SELECT d.doc_id, 1 - (d.embedding <=> %s::vector) AS score
        FROM {table} d
        INNER JOIN {rank_table} r ON r.doc_id = d.doc_id
        WHERE d.embedding IS NOT NULL
          AND r.rank < %s
          {ew}
        ORDER BY d.embedding <=> %s::vector, d.doc_id
        LIMIT %s
    """
    params = (lit, scale, *extra_params, lit, top_k)
    cur.execute(sql, params)
    return [(str(r[0]), float(r[1])) for r in cur.fetchall() if r[0]]


def run_plan_checks_ladder(
    cur,
    table: str,
    rank_table: str,
    conditions: list[str],
    probe_questions: list[dict],
    qvecs: dict[str, list[float]],
    doc_source: dict,
    scales: tuple[int, ...] = PLAN_CHECK_SCALES,
) -> list[dict]:
    checks: list[dict] = []
    for question in probe_questions:
        eid = question["eval_id"]
        vec = qvecs.get(eid)
        if vec is None:
            checks.append(
                {
                    "table": table,
                    "rank_table": rank_table,
                    "eval_id": eid,
                    "skipped": True,
                    "skip_reason": "missing_query_vector",
                }
            )
            continue
        for scale in scales:
            for cond in conditions:
                extra, params = condition_filter_sql(cond, question, doc_source)
                extra = extra.replace("source_type", "d.source_type")
                lit = vector_literal(vec)
                sql = f"""
                    EXPLAIN
                    SELECT d.doc_id, 1 - (d.embedding <=> %s::vector) AS score
                    FROM {table} d
                    INNER JOIN {rank_table} r ON r.doc_id = d.doc_id
                    WHERE d.embedding IS NOT NULL
                      AND r.rank < %s
                      {extra}
                    ORDER BY d.embedding <=> %s::vector, d.doc_id
                    LIMIT %s
                """
                cur.execute(sql, (lit, scale, *params, lit, TOP_K))
                plan_lines = [r[0] for r in cur.fetchall()]
                scan_node_types, hnsw_index_scan, innermost = parse_plan_scans(plan_lines)
                checks.append(
                    {
                        "table": table,
                        "rank_table": rank_table,
                        "condition": cond,
                        "scale": scale,
                        "eval_id": eid,
                        "innermost_scan_node_type": innermost,
                        "scan_node_types": scan_node_types,
                        "hnsw_index_scan": hnsw_index_scan,
                        "plan": plan_lines,
                    }
                )
    return checks


def plan_checks_failed(checks: list[dict]) -> bool:
    return any(bool(c.get("hnsw_index_scan")) for c in checks)


def out_path(ladder: str, embedder: str, bank: str) -> Path:
    return REV1 / f"exact_ladder_{ladder}_{embedder}_{bank}.json"


def cell_cache_path(ladder: str, embedder: str, bank: str) -> Path:
    return DATA / f"rev1_uniform_ladder_cache_{ladder}_{embedder}_{bank}.jsonl"


def cell_key(condition: str, scale: int) -> str:
    return f"{condition}|{scale}"


def load_finished_cells(path: Path) -> dict[str, dict]:
    done: dict[str, dict] = {}
    if not path.is_file():
        return done
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            done[rec["cell"]] = rec["run"]
    return done


def append_cell_cache(path: Path, condition: str, scale: int, run: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(
            json.dumps({"cell": cell_key(condition, scale), "run": run}, ensure_ascii=True)
            + "\n"
        )


def load_questions(manifest: dict, bank: str, max_questions: int | None) -> list[dict]:
    bank_path = BANK_FILES[bank]
    bank_data = json.loads(bank_path.read_text(encoding="utf-8"))
    eval_ids = list(bank_data["question_ids"])
    if max_questions is not None:
        eval_ids = eval_ids[: int(max_questions)]
    by_eval = {q["eval_id"]: q for q in manifest.get("questions") or []}
    missing = [e for e in eval_ids if e not in by_eval]
    if missing:
        raise SystemExit(f"manifest missing {len(missing)} eval_ids from {bank}")
    return [by_eval[e] for e in eval_ids]


def run_ladder(args: argparse.Namespace) -> int:
    ladder = args.ladder
    if ladder not in LADDERS:
        raise SystemExit(f"unknown ladder {ladder}")
    rank_table = LADDERS[ladder]["rank_table"]
    embedder = args.embedder
    bank = args.bank
    cfg = EMBEDDER_CONFIG[embedder]
    manifest = load_manifest()
    doc_source = build_doc_source_map(manifest)
    questions = load_questions(manifest, bank, args.max_questions)
    eval_ids = [q["eval_id"] for q in questions]
    cache_path = args.cache or cfg["cache_path"]
    qvecs, missing = load_query_cache(embedder, eval_ids, cache_path)

    pf = run_openai_preflight(
        embedder,
        bank,
        questions,
        qvecs,
        skip_preflight=args.skip_preflight,
        provenance_path=args.provenance,
    )
    if pf != 0:
        return pf

    scales = [int(x) for x in args.scales.split(",") if x.strip()]
    conditions = [c.strip() for c in args.conditions.split(",") if c.strip()]

    conn = pg_connect()
    conn.autocommit = True
    cur = conn.cursor()

    if args.build_ranks:
        rep = build_all_ranks(cur, force=args.force_ranks)
        print(json.dumps(rep, indent=2))

    cur.execute(
        "SELECT COUNT(*) FROM information_schema.tables "
        "WHERE table_schema='rev1' AND table_name=%s",
        (rank_table.split(".")[1],),
    )
    if cur.fetchone()[0] == 0:
        print(f"FAIL: missing rank table {rank_table}; run with --build-ranks", file=sys.stderr)
        return 1

    rank_map = load_rank_map(cur, rank_table)
    source_db = {did: doc_source.get(did, "unknown") for did in rank_map}

    apply_seqscan_session(cur)
    pg_version, pgvector_version = session_pg_versions(cur)
    probes = plan_probe_questions(questions)
    plan_checks = run_plan_checks_ladder(
        cur, cfg["table"], rank_table, conditions, probes, qvecs, doc_source
    )
    if plan_probe_errors(plan_checks, qvecs):
        return 1

    out = args.out or out_path(ladder, embedder, bank)
    scratch = cell_cache_path(ladder, embedder, bank)
    if args.force and scratch.is_file():
        scratch.unlink()
    finished = load_finished_cells(scratch)

    created_at = datetime.now(timezone.utc).isoformat()
    comp_meta: dict[str, dict[str, int]] = {}

    for cond in conditions:
        for scale in scales:
            ck = cell_key(cond, scale)
            if ck in finished and not args.force:
                if finished[ck].get("corpus_composition"):
                    comp_meta[str(scale)] = finished[ck]["corpus_composition"]
                print(
                    f"skip cached {ladder} {embedder} {bank} {cond} N={scale}",
                    flush=True,
                )
                continue
            if missing:
                print(f"skip cell (missing vectors): {cond} N={scale}", flush=True)
                continue

            t0 = time.time()
            per_q: list[dict] = []
            for q in questions:
                eid = q["eval_id"]
                expected = {str(x) for x in (q.get("expected_doc_ids") or []) if x}
                if not expected:
                    continue
                extra, params = condition_filter_sql(cond, q, doc_source)
                rows = exact_search_ladder(
                    cur,
                    cfg["table"],
                    rank_table,
                    qvecs[eid],
                    scale,
                    extra,
                    params,
                    TOP_K,
                )
                retrieved = [d for d, _ in rows]
                scores = [s for _, s in rows]
                m = per_question_metrics(expected, retrieved, scores, TOP_K)
                per_q.append({"question_id": eid, **m})
            elapsed = round(time.time() - t0, 3)
            metrics = aggregate_metrics(per_q)
            comp = composition_for_scale(rank_map, source_db, scale)
            comp_meta[str(scale)] = comp
            run = {
                "condition": cond,
                "scale": scale,
                "n_questions": len(per_q),
                "elapsed_s": elapsed,
                "metrics": metrics,
                "per_question": per_q,
                "corpus_composition": comp,
            }
            finished[ck] = run
            append_cell_cache(scratch, cond, scale, run)
            print(
                f"{ladder} {embedder} {bank} {cond} N={scale} Hit@10={metrics['hit_at_10']:.4f} ({elapsed}s)",
                flush=True,
            )

    cur.close()
    conn.close()

    runs = [finished[cell_key(c, s)] for c in conditions for s in scales if cell_key(c, s) in finished]
    runs.sort(key=lambda r: (conditions.index(r["condition"]) if r["condition"] in conditions else 99, r["scale"]))

    payload = {
        "meta": {
            "created_at": created_at,
            "ladder": ladder,
            "rank_table": rank_table,
            "seed": LADDERS[ladder].get("seed"),
            "embedder": embedder,
            "bank": bank,
            "search_mode": "exact",
            "session_settings": {"enable_indexscan": "off", "enable_bitmapscan": "off"},
            "postgresql_version": pg_version,
            "pgvector_version": pgvector_version,
            "top_k": TOP_K,
            "scales": scales,
            "conditions": conditions,
            "table": cfg["table"],
            "manifest_sha256": sha256_file(MANIFEST_PATH),
            "query_cache_path": str(cache_path.relative_to(ROOT)),
            "query_cache_sha256": sha256_file(cache_path),
            "plan_check": plan_checks,
            "pool_filter": POOL_FILTER,
            "composition_at_scales": comp_meta,
            "max_questions": args.max_questions,
            "cell_cache": str(scratch.relative_to(ROOT)),
        },
        "runs": runs,
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    write_markdown_summary(out.with_suffix(".md"), payload)
    print(f"wrote {out}")
    if plan_checks_failed(plan_checks):
        print("FAIL: plan check reports HNSW index scan", file=sys.stderr)
        return 1
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build-ranks", action="store_true", help="Create rev1 rank tables")
    parser.add_argument("--force-ranks", action="store_true", help="Rebuild rank tables")
    parser.add_argument("--ladder", choices=tuple(LADDERS.keys()), default="uniform_s42")
    parser.add_argument("--embedder", choices=("openai", "titan"))
    parser.add_argument("--bank", choices=("primary200", "primary400"), default="primary200")
    parser.add_argument("--scales", default=",".join(str(s) for s in DEFAULT_SCALES))
    parser.add_argument("--conditions", default=",".join(DEFAULT_CONDITIONS))
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument("--cache", type=Path, default=None)
    parser.add_argument("--provenance", type=Path, default=PROVENANCE_DEFAULT)
    parser.add_argument("--skip-preflight", action="store_true")
    parser.add_argument("--max-questions", type=int, default=None)
    parser.add_argument("--force", action="store_true", help="Re-run cells ignoring cache")
    args = parser.parse_args()

    if args.build_ranks and not args.embedder:
        conn = pg_connect()
        conn.autocommit = True
        cur = conn.cursor()
        rep = build_all_ranks(cur, force=args.force_ranks)
        cur.close()
        conn.close()
        print(json.dumps(rep, indent=2))
        return 0

    if not args.embedder:
        parser.error("--embedder required unless --build-ranks only")
    return run_ladder(args)


if __name__ == "__main__":
    raise SystemExit(main())
