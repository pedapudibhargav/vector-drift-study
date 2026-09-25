#!/usr/bin/env python3
"""MVP exact cosine control at selected scales (ANN confounder check).

Uses cached query embeddings + same primary-200 questions as the published HNSW
ladder. Compares exact vs published HNSW Hit@k at N∈{5k,50k,100k}, raw (+ optional meta).

Usage (host, dockerized Postgres on localhost:5432):
  DATABASE_URL=postgresql+asyncpg://vector_drift:vector_drift@localhost:5432/vector_drift \\
    python3 scripts/erb/run_exact_control_mvp.py

  python3 scripts/erb/run_exact_control_mvp.py --scales 5000,50000,100000 --conditions raw
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from paths import ERB_MANIFEST, QUERY_EMBED_CACHE, api_pythonpath  # noqa: E402

sys.path.insert(0, str(api_pythonpath()))
PUB = ROOT / "artifacts" / "published"
SWEEP = PUB / "erb_full_primary200_to100k.json"
PRIMARY = PUB / "primary_questions_eval.json"


def _load_env() -> None:
    env_path = ROOT / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
    # Host runs cannot resolve docker service hostname
    url = os.environ.get("DATABASE_URL", "")
    if "vector-drift-db" in url:
        os.environ["DATABASE_URL"] = url.replace("vector-drift-db", "localhost")


def _db_url() -> str:
    url = os.environ.get(
        "DATABASE_URL",
        "postgresql+asyncpg://vector_drift:vector_drift@localhost:5432/vector_drift",
    )
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return url


async def _run(args: argparse.Namespace) -> dict:
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

    from app.services.vector_drift_eval import run_erb_vector_drift

    manifest = json.loads(ERB_MANIFEST.read_text(encoding="utf-8"))
    all_q = {q["question_id"]: q for q in manifest["questions"]}
    primary = json.loads(PRIMARY.read_text(encoding="utf-8"))
    qids = list(primary["question_ids"])
    questions = [all_q[qid] for qid in qids if qid in all_q]
    if len(questions) != 200:
        raise SystemExit(f"expected 200 primary questions, got {len(questions)}")

    cache_raw = json.loads(QUERY_EMBED_CACHE.read_text(encoding="utf-8"))
    # cache may be {qid: vec} or {qid: {embedding: vec}}
    cache: dict[str, list[float]] = {}
    for qid in qids:
        v = cache_raw.get(qid)
        if isinstance(v, list):
            cache[qid] = v
        elif isinstance(v, dict) and "embedding" in v:
            cache[qid] = v["embedding"]
    missing = [qid for qid in qids if qid not in cache]
    if missing:
        raise SystemExit(f"missing {len(missing)} query embeddings in cache (e.g. {missing[:3]})")

    sweep = json.loads(SWEEP.read_text(encoding="utf-8"))
    hnsw_idx: dict[tuple[int, str], dict] = {}
    for run in sweep["runs"]:
        hnsw_idx[(int(run["corpus_scale_size"]), run["condition"])] = run

    scales = [int(x) for x in args.scales.split(",") if x.strip()]
    conditions = [c.strip() for c in args.conditions.split(",") if c.strip()]

    engine = create_async_engine(_db_url())
    Session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    results: list[dict] = []
    comparisons: list[dict] = []

    async with Session() as db:
        for n in scales:
            for cond in conditions:
                t0 = time.time()
                print(f"exact control N={n} condition={cond} …", flush=True)
                summary = await run_erb_vector_drift(
                    db,
                    run_name=f"exact_control_mvp_N{n}_{cond}",
                    corpus_scale_size=n,
                    top_k=10,
                    condition=cond,
                    questions=questions,
                    query_embed_cache=cache,
                    persist=False,
                    force_exact=True,
                )
                elapsed = round(time.time() - t0, 1)
                hnsw = hnsw_idx.get((n, cond))
                # HNSW metrics may live on run or need recompute from per_question
                h10 = h1 = mrr = None
                if hnsw:
                    if "hit_at_10" in hnsw:
                        h10, h1, mrr = hnsw.get("hit_at_10"), hnsw.get("hit_at_1"), hnsw.get("mrr")
                    else:
                        pqs = hnsw.get("per_question") or []
                        if pqs:
                            h10 = sum(1 for p in pqs if p.get("hit_at_10")) / len(pqs)
                            h1 = sum(1 for p in pqs if p.get("hit_at_1")) / len(pqs)
                            mrr = sum(float(p.get("mrr") or 0) for p in pqs) / len(pqs)

                cmp = {
                    "corpus_scale_size": n,
                    "condition": cond,
                    "n_questions": summary["questions_evaluated"],
                    "exact_hit_at_1": summary["hit_at_1"],
                    "exact_hit_at_10": summary["hit_at_10"],
                    "exact_mrr": summary["mrr"],
                    "hnsw_hit_at_1": round(h1, 4) if h1 is not None else None,
                    "hnsw_hit_at_10": round(h10, 4) if h10 is not None else None,
                    "hnsw_mrr": round(mrr, 4) if mrr is not None else None,
                    "delta_hit_at_10_exact_minus_hnsw": (
                        round(summary["hit_at_10"] - float(h10), 4) if h10 is not None else None
                    ),
                    "elapsed_s": elapsed,
                }
                # per-query disagreement count
                if hnsw and hnsw.get("per_question"):
                    hmap = {p["question_id"]: p for p in hnsw["per_question"]}
                    disagree = 0
                    for p in summary["per_question"]:
                        hp = hmap.get(p["question_id"])
                        if hp and bool(hp.get("hit_at_10")) != bool(p.get("hit_at_10")):
                            disagree += 1
                    cmp["hit10_disagreements"] = disagree
                print(
                    f"  exact Hit@10={summary['hit_at_10']:.3f} "
                    f"HNSW Hit@10={cmp['hnsw_hit_at_10']} "
                    f"Δ={cmp['delta_hit_at_10_exact_minus_hnsw']} "
                    f"({elapsed}s)",
                    flush=True,
                )
                results.append({k: v for k, v in summary.items() if k != "per_question"})
                # keep slim per_question for artifact
                results[-1]["per_question"] = [
                    {
                        "question_id": p["question_id"],
                        "hit_at_10": p["hit_at_10"],
                        "hit_at_1": p["hit_at_1"],
                        "mrr": p["mrr"],
                        "rank": p.get("rank"),
                    }
                    for p in summary["per_question"]
                ]
                comparisons.append(cmp)

    await engine.dispose()

    report = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "protocol": "exact cosine (enable_indexscan=off) vs published HNSW ladder",
        "primary_n": 200,
        "scales": scales,
        "conditions": conditions,
        "comparisons": comparisons,
        "runs": results,
        "interpretation_note": (
            "If exact Hit@10 still declines with N similarly to HNSW, drift is not solely "
            "an ANN artifact. If exact stays flat while HNSW drops, HNSW parameters dominate."
        ),
    }
    out = PUB / "exact_control_mvp.json"
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    md = [
        "# Exact-search MVP control",
        "",
        report["interpretation_note"],
        "",
        "| N | cond | exact Hit@10 | HNSW Hit@10 | Δ (exact−HNSW) | Hit@10 disagreements |",
        "|---|------|--------------|-------------|----------------|----------------------|",
    ]
    for c in comparisons:
        md.append(
            f"| {c['corpus_scale_size']} | {c['condition']} | {c['exact_hit_at_10']} | "
            f"{c['hnsw_hit_at_10']} | {c['delta_hit_at_10_exact_minus_hnsw']} | "
            f"{c.get('hit10_disagreements', '—')} |"
        )
    md_path = PUB / "exact_control_mvp.md"
    md_path.write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"wrote {out}")
    print(f"wrote {md_path}")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scales", default="5000,50000,100000")
    parser.add_argument("--conditions", default="raw")
    args = parser.parse_args()
    _load_env()
    asyncio.run(_run(args))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
