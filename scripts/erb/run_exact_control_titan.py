#!/usr/bin/env python3
"""Exact cosine control for the Titan V2 arm (ANN confounder check, mirrors Sec. V-F).

Same primary-200 bank, same cached Titan query vectors, same gold IDs as the
published Titan HNSW ladder. Exact search = index/bitmap scans disabled so
Postgres performs a sequential scan with exact cosine ordering.

Writes (default --out-dir artifacts/published):
  - exact_control_titan.json
  - exact_control_titan.md

Usage:
  .venv/bin/python scripts/erb/run_exact_control_titan.py --scales 5000,50000,100000
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ingest_erb_titan import vector_literal  # noqa: E402
from paths import ROOT  # noqa: E402
from run_scale_sweep_titan import QUERY_CACHE, _db_url  # noqa: E402

PUB = ROOT / "artifacts" / "published"
TITAN_SWEEP = PUB / "erb_titan_primary200_to100k.json"
METRICS = ("hit_at_1", "hit_at_5", "hit_at_10", "mrr", "document_recall")


def _load_hnsw(path: Path) -> dict[tuple[int, str], dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    runs = data.get("runs_with_per_question") or data["runs"]
    out = {}
    for r in runs:
        if not r.get("per_question"):
            raise SystemExit(f"{path} lacks per_question rows; re-export Titan sweep first")
        out[(int(r["corpus_scale_size"]), r["condition"])] = r
    return out


def _exact_topk(conn, vec: list[float], *, scale: int, top_k: int, source_type: str | None):
    lit = vector_literal(vec)
    where = "embedding IS NOT NULL AND scale_rank IS NOT NULL AND scale_rank < %s"
    params: list = [lit, scale]
    if source_type:
        where += " AND source_type = %s"
        params.append(source_type)
    params += [lit, top_k]
    return conn.execute(
        f"""
        SELECT doc_id, 1 - (embedding <=> %s::vector) AS score
        FROM document_chunks_titan
        WHERE {where}
        ORDER BY embedding <=> %s::vector
        LIMIT %s
        """,
        params,
    ).fetchall()


def main() -> int:
    import psycopg

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scales", default="5000,50000,100000")
    parser.add_argument("--conditions", default="raw")
    parser.add_argument("--top-k", type=int, default=10)
    parser.add_argument("--sweep", type=Path, default=TITAN_SWEEP)
    parser.add_argument("--out-dir", type=Path, default=PUB)
    args = parser.parse_args()

    hnsw = _load_hnsw(args.sweep)
    cache = json.loads(QUERY_CACHE.read_text(encoding="utf-8"))["vectors"]
    scales = [int(x) for x in args.scales.split(",") if x.strip()]
    conditions = [c.strip() for c in args.conditions.split(",") if c.strip()]

    conn = psycopg.connect(_db_url(), autocommit=True)
    conn.execute("SET enable_indexscan = off")
    conn.execute("SET enable_bitmapscan = off")

    comparisons, runs = [], []
    try:
        for n in scales:
            for cond in conditions:
                ref = hnsw[(n, cond)]
                t0 = time.time()
                per_q = []
                for hp in ref["per_question"]:
                    eval_id = str(hp["question_id"])
                    expected = set(hp["expected_doc_ids"])
                    st = hp.get("meta_source_type") if cond == "meta" else None
                    rows = _exact_topk(conn, cache[eval_id], scale=n, top_k=args.top_k, source_type=st)
                    retrieved = [r[0] for r in rows if r[0]]
                    if len(retrieved) < args.top_k:
                        raise SystemExit(f"under-filled exact retrieval eval_id={eval_id} N={n}")
                    rank = next((i for i, d in enumerate(retrieved, 1) if d in expected), None)
                    per_q.append(
                        {
                            "question_id": eval_id,
                            "question_type": hp.get("question_type"),
                            "rank": rank,
                            "hit_at_1": rank == 1,
                            "hit_at_5": rank is not None and rank <= 5,
                            "hit_at_10": rank is not None and rank <= 10,
                            "mrr": 1.0 / rank if rank else 0.0,
                            "document_recall": len(expected & set(retrieved)) / max(len(expected), 1),
                            "retrieved_doc_ids": retrieved,
                        }
                    )
                k = len(per_q)
                exact = {m: round(sum(float(p[m]) for p in per_q) / k, 4) for m in METRICS}
                hmap = {str(p["question_id"]): p for p in ref["per_question"]}
                disagree = sum(
                    1 for p in per_q if bool(hmap[p["question_id"]]["hit_at_10"]) != p["hit_at_10"]
                )
                same_lists = sum(
                    1 for p in per_q if hmap[p["question_id"]]["retrieved_doc_ids"] == p["retrieved_doc_ids"]
                )
                cmp = {
                    "corpus_scale_size": n,
                    "condition": cond,
                    "n_questions": k,
                    **{f"exact_{m}": v for m, v in exact.items()},
                    **{f"hnsw_{m}": ref[m] for m in METRICS},
                    "delta_hit_at_10_exact_minus_hnsw": round(exact["hit_at_10"] - ref["hit_at_10"], 4),
                    "delta_hit_at_1_exact_minus_hnsw": round(exact["hit_at_1"] - ref["hit_at_1"], 4),
                    "hit10_disagreements": disagree,
                    "identical_top10_lists": same_lists,
                    "elapsed_s": round(time.time() - t0, 1),
                }
                print(json.dumps(cmp), flush=True)
                comparisons.append(cmp)
                runs.append({"corpus_scale_size": n, "condition": cond, **exact, "per_question": per_q})
    finally:
        conn.close()

    report = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "arm": "titan_v2",
        "embedding_model": "amazon.titan-embed-text-v2:0",
        "embedding_dim": 1024,
        "protocol": "exact cosine (enable_indexscan=off, enable_bitmapscan=off) vs published Titan HNSW ladder",
        "hnsw_source": "artifacts/published/erb_titan_primary200_to100k.json",
        "primary_n": 200,
        "scales": scales,
        "conditions": conditions,
        "comparisons": comparisons,
        "runs": runs,
    }
    args.out_dir.mkdir(parents=True, exist_ok=True)
    out = args.out_dir / "exact_control_titan.json"
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    md = [
        "# Exact-search control — Titan V2",
        "",
        "| N | cond | exact Hit@1 | HNSW Hit@1 | exact Hit@10 | HNSW Hit@10 | Δ10 (exact−HNSW) | disagreements | identical top-10 |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for c in comparisons:
        md.append(
            f"| {c['corpus_scale_size']} | {c['condition']} | {c['exact_hit_at_1']} | {c['hnsw_hit_at_1']} | "
            f"{c['exact_hit_at_10']} | {c['hnsw_hit_at_10']} | {c['delta_hit_at_10_exact_minus_hnsw']} | "
            f"{c['hit10_disagreements']} | {c['identical_top10_lists']}/{c['n_questions']} |"
        )
    (args.out_dir / "exact_control_titan.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
