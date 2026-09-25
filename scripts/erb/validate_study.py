#!/usr/bin/env python3
"""Code-level validation of ERB study invariants + optional gpt-4o-mini relevance judge."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from paths import ERB_MANIFEST, DEFAULT_SCALES, EVAL_TOP_K, api_pythonpath  # noqa: E402

sys.path.insert(0, str(api_pythonpath()))


def _load_env() -> None:
    for env_path in (Path("/app/.env"), Path(__file__).resolve().parents[2] / ".env"):
        if not env_path.exists():
            continue
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
        break


def validate_manifest(manifest: dict) -> list[str]:
    errors: list[str] = []
    docs = manifest.get("documents") or []
    questions = manifest.get("questions") or []
    if not docs:
        errors.append("manifest has zero documents")
    ranks = [d["scale_rank"] for d in docs]
    if ranks != list(range(len(ranks))):
        errors.append("scale_rank not contiguous from 0")
    anchors = [d for d in docs if d.get("is_gold_anchor")]
    if anchors and any(a["scale_rank"] >= len(anchors) for a in anchors):
        # anchors should be the first A ranks
        max_anchor = max(a["scale_rank"] for a in anchors)
        if max_anchor >= len(anchors):
            errors.append("gold anchors not packed at front of scale_rank")
    for q in questions:
        expected = q.get("expected_doc_ids") or []
        if not expected:
            errors.append(f"{q.get('question_id')} missing expected_doc_ids")
    return errors


async def validate_db(scales: list[int]) -> list[str]:
    from sqlalchemy import text
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

    errors: list[str] = []
    db_url = os.environ.get(
        "DATABASE_URL",
        "postgresql+asyncpg://vector_drift:vector_drift@localhost:5432/vector_drift",
    )
    if db_url.startswith("postgresql://"):
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    engine = create_async_engine(db_url, pool_pre_ping=True)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as db:
        n = (await db.execute(text("SELECT COUNT(*) FROM document_chunks WHERE embedding IS NOT NULL"))).scalar_one()
        if n < min(scales):
            errors.append(f"only {n} embedded docs; need >= {min(scales)} for smallest scale")
        missing = (
            await db.execute(
                text(
                    "SELECT COUNT(*) FROM document_chunks "
                    "WHERE embedding IS NOT NULL AND (scale_rank IS NULL OR doc_id IS NULL)"
                )
            )
        ).scalar_one()
        if missing:
            errors.append(f"{missing} embedded rows missing scale_rank/doc_id")
    await engine.dispose()
    return errors


async def run_llm_judge(
    *,
    scale: int,
    limit: int,
    condition: str,
) -> dict:
    from app import ssl_bundle

    ssl_bundle.apply_corporate_ssl_bundle()

    from openai import OpenAI
    from sqlalchemy import text
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

    from app.services.embedding import embed_single_text
    from app.services.vector_search import query_vectors
    from cost_tracker import record_judge
    from paths import ERB_MANIFEST

    manifest = json.loads(ERB_MANIFEST.read_text(encoding="utf-8"))
    questions = list(manifest.get("questions") or [])[:limit]

    db_url = os.environ.get(
        "DATABASE_URL",
        "postgresql+asyncpg://vector_drift:vector_drift@localhost:5432/vector_drift",
    )
    if db_url.startswith("postgresql://"):
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    engine = create_async_engine(db_url, pool_pre_ping=True)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

    results: list[dict] = []
    async with session_factory() as db:
        run_id = (
            await db.execute(
                text("""
                    INSERT INTO experiment_runs
                        (run_name, corpus_scale_size, embedding_model, vector_index_type, condition, status)
                    VALUES (:name, :scale, 'text-embedding-3-small', 'pgvector_hnsw', :condition, 'COMPLETED')
                    RETURNING id
                """),
                {"name": f"llm_judge_{condition}_n{scale}", "scale": scale, "condition": condition},
            )
        ).scalar_one()

        for q in questions:
            expected = set(q.get("expected_doc_ids") or [])
            mf = None
            if condition == "meta" and q.get("source_types"):
                mf = {"source_type": q["source_types"][0]}
            vec = await embed_single_text(q["question"])
            hits = await query_vectors(db, vec, top_k=3, metadata_filter=mf, corpus_scale_size=scale)
            contexts = []
            for h in hits:
                contexts.append(
                    {
                        "doc_id": h.get("doc_id"),
                        "score": h.get("score"),
                        "text": ((h.get("metadata") or {}).get("chunk_text") or "")[:1200],
                    }
                )
            prompt = (
                "Score how relevant the retrieved documents are for answering the question.\n"
                "Return JSON only: {\"relevance\":0-3,\"rationale\":\"...\"} where "
                "0=irrelevant,1=weak,2=partial,3=highly relevant to the gold answer.\n"
                f"Question: {q['question']}\n"
                f"Gold doc ids: {sorted(expected)}\n"
                f"Retrieved:\n{json.dumps(contexts, indent=2)}\n"
            )
            resp = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0,
                response_format={"type": "json_object"},
            )
            usage = resp.usage
            if usage:
                record_judge(
                    input_tokens=usage.prompt_tokens or 0,
                    output_tokens=usage.completion_tokens or 0,
                    note=f"judge {q['question_id']} n={scale}",
                )
            content = resp.choices[0].message.content or "{}"
            try:
                parsed = json.loads(content)
            except json.JSONDecodeError:
                parsed = {"relevance": 0, "rationale": content[:500]}
            rel = float(parsed.get("relevance") or 0)
            await db.execute(
                text("""
                    INSERT INTO llm_eval_results (
                        experiment_run_id, question_id, evaluator_model,
                        answer_relevance_score, cost_usd, reasoning_summary
                    ) VALUES (
                        :run_id, :qid, 'gpt-4o-mini',
                        :rel, 0, :why
                    )
                """),
                {
                    "run_id": str(run_id),
                    "qid": q["question_id"],
                    "rel": rel,
                    "why": str(parsed.get("rationale") or "")[:2000],
                },
            )
            results.append({"question_id": q["question_id"], "relevance": rel})
        await db.commit()
    await engine.dispose()
    avg = sum(r["relevance"] for r in results) / max(len(results), 1)
    return {"scale": scale, "condition": condition, "n": len(results), "mean_relevance": round(avg, 3), "results": results}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=ERB_MANIFEST)
    parser.add_argument("--llm-judge", action="store_true")
    parser.add_argument("--judge-limit", type=int, default=30)
    parser.add_argument("--judge-scale", type=int, default=5000)
    parser.add_argument("--condition", choices=("raw", "meta"), default="raw")
    args = parser.parse_args()
    _load_env()

    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    errors = validate_manifest(manifest)
    errors.extend(asyncio.run(validate_db(list(DEFAULT_SCALES[:2]))))
    if errors:
        print("VALIDATION_FAIL")
        for e in errors:
            print(f" - {e}")
        # soft-fail on scale coverage during partial ingest
        hard = [e for e in errors if "need >=" not in e]
        if hard:
            return 1
    else:
        print("VALIDATION_OK")

    if args.llm_judge:
        out = asyncio.run(
            run_llm_judge(scale=args.judge_scale, limit=args.judge_limit, condition=args.condition)
        )
        print(json.dumps({k: v for k, v in out.items() if k != "results"}, indent=2))
        Path("data/results").mkdir(parents=True, exist_ok=True)
        Path(f"data/results/llm_judge_n{args.judge_scale}_{args.condition}.json").write_text(
            json.dumps(out, indent=2), encoding="utf-8"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
