#!/usr/bin/env python3
"""Exact cosine ladders over rev1.emb_all_openai joined to pool rank tables."""

from __future__ import annotations

import argparse
import json
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

from build_pool_union import (  # noqa: E402
    EMB_TABLE,
    build_union_and_ranks,
    load_rank_map,
    pg_connect,
    table_exists,
)
from harness_lib import sha256_file  # noqa: E402
from run_exact_ladder import (  # noqa: E402
    BANK_FILES,
    DEFAULT_CONDITIONS as ALL_CONDITIONS,
    MANIFEST_PATH,
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
OPENAI_CACHE = DATA / "erb_query_embed_cache.json"
POOL_FILTER = "rev1.emb_all_openai UNION document_chunks(+pool_ext if present)"
DEFAULT_SCALE_TOKENS = (
    "5000",
    "10000",
    "15000",
    "20000",
    "25000",
    "40000",
    "50000",
    "75000",
    "100000",
    "150000",
    "full",
)
DEFAULT_CONDITIONS = ("raw", "meta_first", "meta_in")
PLAN_CHECK_SCALES = (5000, 50000, 100000)

LADDERS = {
    "prop_s42": {"rank_table": "rev1.prop_rank_s42", "seed": 42},
    "prop_s0": {"rank_table": "rev1.prop_rank_s0", "seed": 0},
    "rr_full": {"rank_table": "rev1.rr_full_rank", "seed": None},
    "prop_evalgold_s42": {"rank_table": "rev1.prop_evalgold_s42", "seed": 42},
}
for _s in range(1, 9):
    LADDERS[f"prop_s{_s}"] = {"rank_table": f"rev1.prop_rank_s{_s}", "seed": _s}


def parse_scale_tokens(text: str) -> list[int | str]:
    out: list[int | str] = []
    for raw in text.split(","):
        tok = raw.strip()
        if not tok:
            continue
        if tok.lower() == "full":
            out.append("full")
        else:
            out.append(int(tok))
    return out


def composition_for_cutoff(
    rank_rows: dict[str, int],
    source: dict[str, str],
    *,
    scale: int | None,
    full: bool,
) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for did, rk in rank_rows.items():
        if full or (scale is not None and rk < scale):
            st = source.get(did) or "unknown"
            counts[st] += 1
    return dict(sorted(counts.items()))


def exact_search_ladder(
    cur,
    table: str,
    rank_table: str,
    vec: list[float],
    *,
    scale: int | None,
    full: bool,
    extra_where: str,
    extra_params: tuple,
    top_k: int,
) -> list[tuple[str, float]]:
    lit = vector_literal(vec)
    ew = extra_where.replace("source_type", "d.source_type")
    if full:
        rank_pred = ""
        params: tuple = (lit, *extra_params, lit, top_k)
    else:
        rank_pred = "AND r.rank < %s"
        params = (lit, scale, *extra_params, lit, top_k)
    sql = f"""
        SELECT d.doc_id, 1 - (d.embedding <=> %s::vector) AS score
        FROM {table} d
        INNER JOIN {rank_table} r ON r.doc_id = d.doc_id
        WHERE d.embedding IS NOT NULL
          {rank_pred}
          {ew}
        ORDER BY d.embedding <=> %s::vector, d.doc_id
        LIMIT %s
    """
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
    scales: list[int],
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


def out_path(ladder: str) -> Path:
    return REV1 / f"exact_ladder_pool_{ladder}_openai_primary200.json"


def cell_cache_path(ladder: str, bank: str) -> Path:
    return DATA / f"rev1_pool_ladder_cache_{ladder}_openai_{bank}.jsonl"


def cell_key(condition: str, scale_token: int | str) -> str:
    return f"{condition}|{scale_token}"


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


def append_cell_cache(path: Path, condition: str, scale_token: int | str, run: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(
            json.dumps({"cell": cell_key(condition, scale_token), "run": run}, ensure_ascii=True)
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


def load_union_source(cur) -> dict[str, str]:
    cur.execute(f"SELECT doc_id, source_type FROM {EMB_TABLE}")
    return {str(r[0]): str(r[1] or "unknown") for r in cur.fetchall() if r[0]}


def resolve_scale(
    token: int | str, union_n: int
) -> tuple[int, str, bool, bool]:
    """Return (scale_int, label, is_full, skip). skip if numeric scale exceeds union and is not full."""
    if token == "full":
        return union_n, "full", True, False
    n = int(token)
    if n > union_n:
        return n, str(n), False, True
    return n, str(n), False, False


def run_ladder(args: argparse.Namespace) -> int:
    ladder = args.ladder
    if ladder not in LADDERS:
        raise SystemExit(f"unknown ladder {ladder}")
    rank_table = LADDERS[ladder]["rank_table"]
    embedder = "openai"
    bank = args.bank
    manifest = load_manifest()
    doc_source = build_doc_source_map(manifest)
    questions = load_questions(manifest, bank, args.max_questions)
    eval_ids = [q["eval_id"] for q in questions]
    cache_path = args.cache or OPENAI_CACHE
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

    scale_tokens = parse_scale_tokens(args.scales)
    conditions = [c.strip() for c in args.conditions.split(",") if c.strip()]
    for c in conditions:
        if c not in ALL_CONDITIONS and c not in DEFAULT_CONDITIONS:
            raise SystemExit(f"unknown condition {c}")

    conn = pg_connect()
    conn.autocommit = True
    cur = conn.cursor()

    if args.build_union:
        rep = build_union_and_ranks(cur, force=args.force_union)
        print(json.dumps(rep, indent=2, default=str))

    if not table_exists(cur, "rev1", "emb_all_openai"):
        print("FAIL: missing rev1.emb_all_openai; run build_pool_union.py", file=sys.stderr)
        return 1
    rank_name = rank_table.split(".", 1)[1]
    if not table_exists(cur, "rev1", rank_name):
        print(f"FAIL: missing rank table {rank_table}; run build_pool_union.py", file=sys.stderr)
        return 1

    cur.execute(f"SELECT COUNT(*) FROM {EMB_TABLE}")
    union_n = int(cur.fetchone()[0])
    rank_map = load_rank_map(cur, rank_table)
    source_db = load_union_source(cur)
    for did, st in source_db.items():
        if did not in doc_source:
            doc_source[did] = st

    apply_seqscan_session(cur)
    pg_version, pgvector_version = session_pg_versions(cur)
    probes = plan_probe_questions(questions)
    plan_scale_ints = [
        s
        for s in PLAN_CHECK_SCALES
        if s <= union_n and (s in scale_tokens or any(isinstance(t, int) and t == s for t in scale_tokens))
    ]
    requested_ints = [int(t) for t in scale_tokens if t != "full" and int(t) <= union_n]
    if not plan_scale_ints:
        plan_scale_ints = sorted(set(requested_ints))[:3]
    plan_checks = run_plan_checks_ladder(
        cur, EMB_TABLE, rank_table, conditions, probes, qvecs, doc_source, plan_scale_ints
    )
    if plan_probe_errors(plan_checks, qvecs):
        return 1

    out = args.out or out_path(ladder)
    scratch = args.cell_cache or cell_cache_path(ladder, bank)
    if args.force and scratch.is_file():
        scratch.unlink()
    finished = load_finished_cells(scratch)

    created_at = datetime.now(timezone.utc).isoformat()
    comp_meta: dict[str, dict[str, int]] = {}
    skipped_scales: list[dict[str, Any]] = []

    for cond in conditions:
        for token in scale_tokens:
            scale_int, label, is_full, skip = resolve_scale(token, union_n)
            ck = cell_key(cond, token)
            if skip:
                skipped_scales.append(
                    {"condition": cond, "scale": scale_int, "reason": f"scale>{union_n}"}
                )
                print(f"skip scale {scale_int} > union_n={union_n}", flush=True)
                continue
            if ck in finished and not args.force:
                run_cached = finished[ck]
                if run_cached.get("corpus_composition"):
                    comp_meta[label] = run_cached["corpus_composition"]
                print(
                    f"skip cached {ladder} openai {bank} {cond} N={label}",
                    flush=True,
                )
                continue
            if missing:
                print(f"skip cell (missing vectors): {cond} N={label}", flush=True)
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
                    EMB_TABLE,
                    rank_table,
                    qvecs[eid],
                    scale=scale_int,
                    full=is_full,
                    extra_where=extra,
                    extra_params=params,
                    top_k=TOP_K,
                )
                retrieved = [d for d, _ in rows]
                scores = [s for _, s in rows]
                m = per_question_metrics(expected, retrieved, scores, TOP_K)
                per_q.append({"question_id": eid, **m})
            elapsed = round(time.time() - t0, 3)
            metrics = aggregate_metrics(per_q)
            comp = composition_for_cutoff(
                rank_map, source_db, scale=scale_int, full=is_full
            )
            comp_meta[label] = comp
            run = {
                "condition": cond,
                "scale": scale_int,
                "scale_label": label,
                "n_questions": len(per_q),
                "elapsed_s": elapsed,
                "metrics": metrics,
                "per_question": per_q,
                "corpus_composition": comp,
                "corpus_n": sum(comp.values()),
            }
            finished[ck] = run
            append_cell_cache(scratch, cond, token, run)
            print(
                f"{ladder} openai {bank} {cond} N={label} "
                f"Hit@10={metrics['hit_at_10']:.4f} ({elapsed}s)",
                flush=True,
            )

    cur.close()
    conn.close()

    runs = []
    for c in conditions:
        for token in scale_tokens:
            ck = cell_key(c, token)
            if ck in finished:
                runs.append(finished[ck])

    payload = {
        "meta": {
            "created_at": created_at,
            "ladder": ladder,
            "rank_table": rank_table,
            "seed": LADDERS[ladder].get("seed"),
            "embedder": "openai",
            "bank": bank,
            "search_mode": "exact",
            "session_settings": {"enable_indexscan": "off", "enable_bitmapscan": "off"},
            "postgresql_version": pg_version,
            "pgvector_version": pgvector_version,
            "top_k": TOP_K,
            "scales": [t if t == "full" else int(t) for t in scale_tokens],
            "full_n": union_n,
            "union_document_count": union_n,
            "conditions": conditions,
            "table": EMB_TABLE,
            "rank_table_name": rank_table,
            "manifest_sha256": sha256_file(MANIFEST_PATH),
            "query_cache_path": str(cache_path.relative_to(ROOT)),
            "query_cache_sha256": sha256_file(cache_path),
            "plan_check": plan_checks,
            "pool_filter": POOL_FILTER,
            "composition_at_scales": comp_meta,
            "max_questions": args.max_questions,
            "cell_cache": str(Path(scratch)),
            "skipped_scales": skipped_scales,
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
    parser.add_argument("--build-union", action="store_true")
    parser.add_argument("--force-union", action="store_true", help="Rebuild union and ranks")
    parser.add_argument("--ladder", choices=tuple(LADDERS.keys()), default="prop_s42")
    parser.add_argument("--bank", choices=("primary200", "primary400"), default="primary200")
    parser.add_argument("--scales", default=",".join(DEFAULT_SCALE_TOKENS))
    parser.add_argument("--conditions", default=",".join(DEFAULT_CONDITIONS))
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument("--cache", type=Path, default=None)
    parser.add_argument("--cell-cache", type=Path, default=None)
    parser.add_argument("--provenance", type=Path, default=PROVENANCE_DEFAULT)
    parser.add_argument("--skip-preflight", action="store_true")
    parser.add_argument("--max-questions", type=int, default=None)
    parser.add_argument("--force", action="store_true", help="Re-run cells ignoring cache")
    args = parser.parse_args()
    return run_ladder(args)


if __name__ == "__main__":
    raise SystemExit(main())
