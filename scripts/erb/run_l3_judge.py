#!/usr/bin/env python3
"""L3 gpt-4o-mini relevance judge — stratified subsample, reuses query embed cache.

Join to L1 rows:
  llm_eval_results.experiment_run_id = experiment_runs.id
  llm_eval_results.question_id       = vector_drift_results.question_id
  AND vector_drift_results.experiment_run_id points at the matching L1 run
    (same corpus_scale_size + condition via experiment_runs).

question_id alone is NOT unique across scales — always join with run / scale.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import random
import sys
import time
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from paths import (  # noqa: E402
    ERB_MANIFEST,
    ERB_RESULTS_DIR,
    EXCLUDED_QUESTION_TYPES,
    QUERY_EMBED_CACHE,
    api_pythonpath,
)

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


def stratified_sample(questions: list[dict], n: int, seed: int = 42) -> list[dict]:
    eligible = [
        q
        for q in questions
        if (q.get("expected_doc_ids") or [])
        and (q.get("question_type") or "") not in EXCLUDED_QUESTION_TYPES
    ]
    by: dict[str, list[dict]] = defaultdict(list)
    for q in eligible:
        by[str(q.get("question_type") or "unknown")].append(q)
    rng = random.Random(seed)
    picked: list[dict] = []
    total = len(eligible)
    for _, bucket in sorted(by.items()):
        rng.shuffle(bucket)
        take = max(1, round(n * len(bucket) / total)) if total else 0
        picked.extend(bucket[:take])
    rng.shuffle(picked)
    return picked[:n]


async def run_judge(
    *,
    scales: list[int],
    n_questions: int,
    condition: str,
    seed: int,
) -> dict:
    from app import ssl_bundle

    ssl_bundle.apply_corporate_ssl_bundle()

    from openai import OpenAI
    from sqlalchemy import text
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

    from app.services.embedding import embed_single_text, validate_embedding
    from app.services.vector_search import query_vectors
    from cost_tracker import assert_budget, record_judge

    manifest = json.loads(ERB_MANIFEST.read_text(encoding="utf-8"))
    questions = stratified_sample(list(manifest.get("questions") or []), n_questions, seed=seed)
    print(f"L3 stratified questions={len(questions)} scales={scales} condition={condition}")

    cache: dict[str, list[float]] = {}
    if QUERY_EMBED_CACHE.exists():
        cache = {
            k: list(v)
            for k, v in json.loads(QUERY_EMBED_CACHE.read_text(encoding="utf-8")).items()
        }

    db_url = os.environ.get(
        "DATABASE_URL",
        "postgresql+asyncpg://vector_drift:vector_drift@localhost:5432/vector_drift",
    )
    if db_url.startswith("postgresql://"):
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    engine = create_async_engine(db_url, pool_pre_ping=True)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

    # Pre-embed / cache all judge questions once
    for q in questions:
        qid = str(q["question_id"])
        if qid not in cache:
            assert_budget()
            cache[qid] = validate_embedding(await embed_single_text(q["question"]))
    QUERY_EMBED_CACHE.parent.mkdir(parents=True, exist_ok=True)
    QUERY_EMBED_CACHE.write_text(json.dumps(cache), encoding="utf-8")

    all_results: list[dict] = []
    async with session_factory() as db:
        for scale in scales:
            assert_budget()
            run_id = (
                await db.execute(
                    text(
                        """
                        INSERT INTO experiment_runs
                            (run_name, corpus_scale_size, embedding_model, vector_index_type, condition, status)
                        VALUES (:name, :scale, 'text-embedding-3-small', 'pgvector_hnsw', :condition, 'COMPLETED')
                        RETURNING id
                        """
                    ),
                    {
                        "name": f"l3_judge_{condition}_n{scale}_s{seed}",
                        "scale": scale,
                        "condition": condition,
                    },
                )
            ).scalar_one()

            scale_scores: list[float] = []
            for q in questions:
                expected = {str(x) for x in (q.get("expected_doc_ids") or []) if x}
                mf = None
                if condition == "meta" and q.get("source_types"):
                    mf = {"source_type": q["source_types"][0]}
                vec = cache[str(q["question_id"])]
                hits = await query_vectors(
                    db, vec, top_k=3, metadata_filter=mf, corpus_scale_size=scale
                )
                contexts = []
                for h in hits:
                    meta = h.get("metadata") or {}
                    contexts.append(
                        {
                            "doc_id": h.get("doc_id"),
                            "score": h.get("score"),
                            "text": (meta.get("chunk_text") or h.get("chunk_text") or "")[:1200],
                        }
                    )
                prompt = (
                    "Score how relevant the retrieved documents are for answering the question.\n"
                    'Return JSON only: {"relevance":0-3,"rationale":"..."} where '
                    "0=irrelevant,1=weak,2=partial,3=highly relevant to the gold answer.\n"
                    f"Question: {q['question']}\n"
                    f"Gold doc ids: {sorted(expected)}\n"
                    f"Retrieved:\n{json.dumps(contexts, indent=2)}\n"
                )
                assert_budget()
                resp = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0,
                    response_format={"type": "json_object"},
                )
                usage = resp.usage
                cost = 0.0
                if usage:
                    record_judge(
                        input_tokens=usage.prompt_tokens or 0,
                        output_tokens=usage.completion_tokens or 0,
                        note=f"l3 {q['question_id']} n={scale}",
                    )
                    cost = (usage.prompt_tokens or 0) / 1e6 * 0.15 + (
                        usage.completion_tokens or 0
                    ) / 1e6 * 0.60
                content = resp.choices[0].message.content or "{}"
                try:
                    parsed = json.loads(content)
                except json.JSONDecodeError:
                    parsed = {"relevance": 0, "rationale": content[:500]}
                rel = float(parsed.get("relevance") or 0)
                scale_scores.append(rel)
                label_hit = bool(expected & {str(c.get("doc_id") or "") for c in contexts})
                await db.execute(
                    text(
                        """
                        INSERT INTO llm_eval_results (
                            experiment_run_id, question_id, evaluator_model,
                            answer_relevance_score, cost_usd, reasoning_summary
                        ) VALUES (
                            :run_id, :qid, 'gpt-4o-mini', :rel, :cost, :why
                        )
                        """
                    ),
                    {
                        "run_id": str(run_id),
                        "qid": q["question_id"],
                        "rel": rel,
                        "cost": cost,
                        "why": json.dumps(
                            {
                                "rationale": parsed.get("rationale"),
                                "label_hit_at_3": label_hit,
                                "corpus_scale_size": scale,
                                "condition": condition,
                                "retrieved_doc_ids": [c.get("doc_id") for c in contexts],
                            }
                        )[:2000],
                    },
                )
                all_results.append(
                    {
                        "question_id": q["question_id"],
                        "question_type": q.get("question_type"),
                        "scale": scale,
                        "condition": condition,
                        "relevance": rel,
                        "label_hit_at_3": label_hit,
                        "experiment_run_id": str(run_id),
                    }
                )
            await db.commit()
            mean = sum(scale_scores) / max(len(scale_scores), 1)
            print(f"L3 n={scale} mean_relevance={mean:.3f} n={len(scale_scores)}")

    await engine.dispose()
    return {
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "n_questions": len(questions),
        "scales": scales,
        "condition": condition,
        "seed": seed,
        "join_hint": (
            "JOIN llm_eval_results ler ON ler.question_id = vdr.question_id "
            "JOIN experiment_runs er ON er.id = ler.experiment_run_id "
            "WHERE er.corpus_scale_size = vdr.corpus_scale_size AND er.condition = vdr.condition"
        ),
        "results": all_results,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scales", type=int, nargs="+", default=[5000, 40000])
    parser.add_argument("--n-questions", type=int, default=40)
    parser.add_argument("--condition", choices=("raw", "meta"), default="raw")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    _load_env()
    out = asyncio.run(
        run_judge(
            scales=list(args.scales),
            n_questions=args.n_questions,
            condition=args.condition,
            seed=args.seed,
        )
    )
    ERB_RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    path = (
        ERB_RESULTS_DIR
        / f"l3_judge_{args.condition}_{'-'.join(map(str, args.scales))}_n{args.n_questions}.json"
    )
    path.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print("wrote", path)
    print(json.dumps({k: v for k, v in out.items() if k != "results"}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
