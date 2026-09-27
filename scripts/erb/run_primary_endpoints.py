#!/usr/bin/env python3
"""Run OpenAI endpoint sweeps for a published primary question bank.

Loads question IDs from ``artifacts/published/primary_questions_{n}.json``,
reuses cached query embeddings where available (embeds missing IDs via API),
and writes a compact endpoint artifact.

Usage (primary-400 endpoints on seed-42 ranks):
  ./.venv/bin/python scripts/erb/run_primary_endpoints.py --primary-n 400

Full ladder (expensive):
  ./.venv/bin/python scripts/erb/run_primary_endpoints.py --primary-n 400 \\
    --scales 5000 10000 15000 20000 25000 40000 50000 75000 100000 \\
    --out artifacts/published/erb_full_primary400_to100k.json
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
DEFAULT_SCALES = (5_000, 50_000, 100_000)


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


def _load_questions(primary_n: int, primary_path: Path | None) -> tuple[list[dict], dict]:
    bank_path = primary_path or (PUB / f"primary_questions_{primary_n}.json")
    if not bank_path.exists():
        raise SystemExit(f"primary bank missing: {bank_path} (run build_primary_questions.py first)")
    bank = json.loads(bank_path.read_text(encoding="utf-8"))
    manifest = json.loads(ERB_MANIFEST.read_text(encoding="utf-8"))
    all_q = {q["question_id"]: q for q in manifest.get("questions") or []}
    qids = list(bank["question_ids"])
    questions = [all_q[qid] for qid in qids if qid in all_q]
    if len(questions) != primary_n:
        raise SystemExit(f"expected {primary_n} questions, resolved {len(questions)}")
    return questions, bank


def _load_cache() -> dict[str, list[float]]:
    cache: dict[str, list[float]] = {}
    if QUERY_EMBED_CACHE.exists():
        raw = json.loads(QUERY_EMBED_CACHE.read_text(encoding="utf-8"))
        for k, v in raw.items():
            if isinstance(v, list):
                cache[k] = v
            elif isinstance(v, dict) and "embedding" in v:
                cache[k] = v["embedding"]
    return cache


async def _run(args: argparse.Namespace) -> dict:
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

    from app.services.vector_drift_eval import run_erb_vector_drift

    questions, bank = _load_questions(args.primary_n, args.primary_file)
    cache = _load_cache()
    scales = list(args.scales)
    conditions = [c.strip() for c in args.conditions.split(",") if c.strip()]

    engine = create_async_engine(_db_url(), pool_pre_ping=True)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    results: list[dict] = []

    async with session_factory() as db:
        for n in scales:
            for condition in conditions:
                t0 = time.time()
                print(f"primary-{args.primary_n} N={n} condition={condition} …", flush=True)
                summary = await run_erb_vector_drift(
                    db,
                    run_name=f"erb_primary{args.primary_n}_{condition}_n{n}",
                    corpus_scale_size=n,
                    top_k=args.top_k,
                    condition=condition,
                    questions=questions,
                    query_embed_cache=cache,
                    persist=not args.no_persist,
                )
                elapsed = round(time.time() - t0, 1)
                slim = {k: v for k, v in summary.items() if k != "per_question"}
                slim["elapsed_s"] = elapsed
                results.append(summary)
                print(
                    f"  Hit@10={slim['hit_at_10']:.3f} MRR={slim['mrr']:.3f} ({elapsed}s)",
                    flush=True,
                )

    QUERY_EMBED_CACHE.parent.mkdir(parents=True, exist_ok=True)
    QUERY_EMBED_CACHE.write_text(json.dumps(cache), encoding="utf-8")

    payload = {
        "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "manifest": str(ERB_MANIFEST),
        "primary_bank": str(args.primary_file or PUB / f"primary_questions_{args.primary_n}.json"),
        "question_sample_seed": bank.get("seed", 42),
        "primary_n": args.primary_n,
        "scales": scales,
        "conditions": conditions,
        "top_k": args.top_k,
        "runs": [
            {
                "condition": r["condition"],
                "corpus_scale_size": r["corpus_scale_size"],
                "hit_at_1": r["hit_at_1"],
                "hit_at_5": r["hit_at_5"],
                "hit_at_10": r["hit_at_10"],
                "mrr": r["mrr"],
                "document_recall": r["document_recall"],
                "questions_evaluated": r["questions_evaluated"],
            }
            for r in results
        ],
    }
    out = args.out or (PUB / f"erb_seed42_endpoints_primary{args.primary_n}.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"wrote {out}")
    await engine.dispose()
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--primary-n", type=int, default=400)
    parser.add_argument("--primary-file", type=Path, default=None)
    parser.add_argument("--scales", type=int, nargs="+", default=list(DEFAULT_SCALES))
    parser.add_argument("--conditions", default="raw")
    parser.add_argument("--top-k", type=int, default=10)
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument("--no-persist", action="store_true")
    args = parser.parse_args()
    _load_env()
    asyncio.run(_run(args))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
