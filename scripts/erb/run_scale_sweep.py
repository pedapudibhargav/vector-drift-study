#!/usr/bin/env python3
"""Run raw vs metadata retrieval sweeps across corpus scales."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from paths import (  # noqa: E402
    DEFAULT_SCALES,
    ERB_MANIFEST,
    ERB_RESULTS_DIR,
    QUERY_EMBED_CACHE,
    SMOKE_SCALES,
    api_pythonpath,
)

sys.path.insert(0, str(api_pythonpath()))



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


async def _run(args: argparse.Namespace) -> dict:
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

    from app.services.vector_drift_eval import run_erb_vector_drift

    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    questions = list(manifest.get("questions") or [])
    if getattr(args, "primary_questions", 0) and args.primary_questions > 0:
        from question_identity import stratified_unique

        questions = stratified_unique(questions, int(args.primary_questions), seed=42)
        print(f"primary stratified unique eval_ids={len(questions)}")
        # Persist the exact primary set used for this sweep
        primary_out = ERB_RESULTS_DIR.parent.parent / "artifacts" / "published" / "primary_questions_eval.json"
        try:
            primary_out.parent.mkdir(parents=True, exist_ok=True)
            primary_out.write_text(
                json.dumps(
                    {
                        "seed": 42,
                        "count": len(questions),
                        "unique_eval_ids": True,
                        "question_ids": [q["question_id"] for q in questions],
                        "erb_question_ids": [q.get("erb_question_id") for q in questions],
                        "question_types": [q.get("question_type") for q in questions],
                    },
                    indent=2,
                ),
                encoding="utf-8",
            )
            print(f"wrote {primary_out}")
        except Exception as exc:  # noqa: BLE001
            print(f"warn: could not write primary set: {exc}")
    if args.question_limit and args.question_limit > 0:
        questions = questions[: args.question_limit]

    doc_count = int(manifest.get("document_count") or 0)
    # Prefer actual embedded coverage so we do not advertise empty scales.
    try:
        from sqlalchemy import text as sql_text
        from sqlalchemy.ext.asyncio import create_async_engine

        _db = os.environ.get(
            "DATABASE_URL",
            "postgresql+asyncpg://vector_drift:vector_drift@localhost:5432/vector_drift",
        )
        if _db.startswith("postgresql://"):
            _db = _db.replace("postgresql://", "postgresql+asyncpg://", 1)
        _eng = create_async_engine(_db)
        async with _eng.connect() as conn:
            embedded_max = (
                await conn.execute(
                    sql_text(
                        "SELECT COALESCE(MAX(scale_rank)+1,0) FROM document_chunks "
                        "WHERE embedding IS NOT NULL AND scale_rank IS NOT NULL"
                    )
                )
            ).scalar_one()
        await _eng.dispose()
        doc_count = min(doc_count, int(embedded_max or 0)) if embedded_max else doc_count
    except Exception as exc:
        print(f"warn: could not read embedded coverage: {exc}")

    # Only evaluate explicitly requested ladder points that fit embedded coverage.
    # Never auto-append full manifest size (that produced a bogus N≈185k point).
    scales = sorted({n for n in args.scales if n <= doc_count})
    if not scales:
        raise SystemExit(f"No valid scales for document_count={doc_count}")

    db_url = os.environ.get("DATABASE_URL") or os.environ.get(
        "ERB_DATABASE_URL",
        "postgresql+asyncpg://vector_drift:vector_drift@localhost:5432/vector_drift",
    )
    if db_url.startswith("postgresql://"):
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)

    engine = create_async_engine(db_url, pool_pre_ping=True)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    cache: dict[str, list[float]] = {}
    if QUERY_EMBED_CACHE.exists() and not args.reset_query_cache:
        raw = json.loads(QUERY_EMBED_CACHE.read_text(encoding="utf-8"))
        cache = {k: list(v) for k, v in raw.items()}

    results: list[dict] = []
    async with session_factory() as db:
        for n in scales:
            for condition in ("raw", "meta"):
                summary = await run_erb_vector_drift(
                    db,
                    run_name=f"erb_{condition}_n{n}",
                    corpus_scale_size=n,
                    top_k=args.top_k,
                    condition=condition,
                    questions=questions,
                    query_embed_cache=cache,
                    persist=not args.no_persist,
                )
                slim = {k: v for k, v in summary.items() if k != "per_question"}
                # Keep per_question in saved payload for audit/CIs; print slim only.
                results.append(summary)
                print(json.dumps(slim))

    QUERY_EMBED_CACHE.parent.mkdir(parents=True, exist_ok=True)
    QUERY_EMBED_CACHE.write_text(json.dumps(cache), encoding="utf-8")

    # pair delta_meta
    by_key = {(r["corpus_scale_size"], r["condition"]): r for r in results}
    deltas: list[dict] = []
    for n in scales:
        raw = by_key.get((n, "raw"))
        meta = by_key.get((n, "meta"))
        if not raw or not meta:
            continue
        deltas.append(
            {
                "corpus_scale_size": n,
                "delta_hit_at_10": round(meta["hit_at_10"] - raw["hit_at_10"], 4),
                "delta_document_recall": round(meta["document_recall"] - raw["document_recall"], 4),
                "delta_mrr": round(meta["mrr"] - raw["mrr"], 4),
                "raw_hit_at_10": raw["hit_at_10"],
                "meta_hit_at_10": meta["hit_at_10"],
            }
        )

    payload = {
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "manifest": str(args.manifest),
        "document_count": doc_count,
        "scales": scales,
        "top_k": args.top_k,
        "question_count": len(questions),
        "runs": results,
        "deltas": deltas,
    }
    ERB_RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    out = args.out or (
        ERB_RESULTS_DIR / f"erb_scale_sweep_{time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())}.json"
    )
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"wrote {out}")
    await engine.dispose()
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=ERB_MANIFEST)
    parser.add_argument("--smoke", action="store_true", help="Use smoke scales")
    parser.add_argument("--scales", type=int, nargs="+", default=None)
    parser.add_argument("--top-k", type=int, default=10)
    parser.add_argument("--question-limit", type=int, default=0)
    parser.add_argument(
        "--primary-questions",
        type=int,
        default=0,
        help="Stratified sample size for main tables (0 = all eligible)",
    )
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument("--no-persist", action="store_true")
    parser.add_argument("--reset-query-cache", action="store_true")
    args = parser.parse_args()
    _load_env()
    if args.scales:
        args.scales = list(args.scales)
    elif args.smoke:
        args.scales = list(SMOKE_SCALES)
    else:
        args.scales = list(DEFAULT_SCALES)
    asyncio.run(_run(args))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
