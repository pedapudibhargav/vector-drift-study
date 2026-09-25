"""EnterpriseRAG-Bench vector-drift evaluation (Document Recall@K / MRR)."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from uuid import uuid4

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.embedding import EMBEDDING_MODEL, embed_single_text
from app.services.vector_search import query_vectors

logger = logging.getLogger(__name__)


def _default_manifest_path() -> Path:
    here = Path(__file__).resolve()
    for base in (here.parents[2], here.parents[4] if len(here.parents) > 4 else here.parents[2]):
        candidate = base / "data" / "erb_scale_manifest.json"
        if candidate.exists():
            return candidate
    return Path("/app/data/erb_scale_manifest.json")


def load_erb_questions(manifest_path: Path | None = None) -> list[dict]:
    path = manifest_path or _default_manifest_path()
    data = json.loads(path.read_text(encoding="utf-8"))
    return list(data.get("questions") or [])


def _hit_metrics(hits: list[dict], expected: set[str], top_k: int) -> dict:
    retrieved: list[str] = []
    scores: list[float] = []
    for hit in hits[:top_k]:
        doc_id = hit.get("doc_id") or (hit.get("metadata") or {}).get("doc_id") or ""
        if doc_id:
            retrieved.append(str(doc_id))
            scores.append(float(hit.get("score") or 0))
    retrieved_set = set(retrieved)
    hit_ids = expected & retrieved_set
    recall = len(hit_ids) / max(len(expected), 1)
    rank: int | None = None
    best_score: float | None = None
    for i, doc_id in enumerate(retrieved, start=1):
        if doc_id in expected:
            rank = i
            best_score = scores[i - 1]
            break
    mrr = 1.0 / rank if rank else 0.0
    return {
        "recall": recall,
        "hit_at_1": rank == 1 if rank else False,
        "hit_at_5": rank is not None and rank <= 5,
        "hit_at_10": rank is not None and rank <= 10,
        "mrr": mrr,
        "rank": rank,
        "score": best_score,
        "retrieved_doc_ids": retrieved,
        "retrieved_scores": scores,
    }


async def run_erb_vector_drift(
    db: AsyncSession,
    *,
    run_name: str,
    corpus_scale_size: int,
    top_k: int = 10,
    condition: str = "raw",
    questions: list[dict] | None = None,
    question_limit: int | None = None,
    query_embed_cache: dict[str, list[float]] | None = None,
    persist: bool = True,
    force_exact: bool = False,
) -> dict:
    qs = list(questions or load_erb_questions())
    if question_limit and question_limit > 0:
        qs = qs[:question_limit]

    run_id = str(uuid4())
    index_type = "pgvector_exact" if force_exact else "pgvector_hnsw"
    if persist:
        await db.execute(
            text("""
                INSERT INTO experiment_runs
                    (id, run_name, corpus_scale_size, embedding_model, vector_index_type, condition, status)
                VALUES (:id, :name, :scale, :model, :index_type, :condition, 'COMPLETED')
            """),
            {
                "id": run_id,
                "name": run_name,
                "scale": corpus_scale_size,
                "model": EMBEDDING_MODEL,
                "index_type": index_type,
                "condition": condition,
            },
        )

    totals = {
        "recall_sum": 0.0,
        "hit_1": 0,
        "hit_5": 0,
        "hit_10": 0,
        "mrr_sum": 0.0,
        "evaluated": 0,
        "skipped": 0,
    }
    per_question: list[dict] = []
    cache = query_embed_cache if query_embed_cache is not None else {}

    for q in qs:
        question_id = q["question_id"]
        expected = {str(x) for x in (q.get("expected_doc_ids") or []) if x}
        if not expected:
            totals["skipped"] += 1
            continue

        metadata_filter: dict[str, str] | None = None
        if condition == "meta":
            source_types = q.get("source_types") or []
            if not source_types:
                totals["skipped"] += 1
                continue
            metadata_filter = {"source_type": str(source_types[0])}

        try:
            if question_id in cache:
                query_vec = cache[question_id]
            else:
                query_vec = await embed_single_text(q["question"])
                cache[question_id] = query_vec
        except Exception as exc:
            logger.warning("Skip %s embed failed: %s", question_id, exc)
            totals["skipped"] += 1
            continue

        hits = await query_vectors(
            db,
            query_vec,
            top_k=top_k,
            metadata_filter=metadata_filter,
            corpus_scale_size=corpus_scale_size,
            force_exact=force_exact,
        )
        metrics = _hit_metrics(hits, expected, top_k=top_k)
        if not metrics["retrieved_doc_ids"]:
            logger.warning(
                "Empty retrieval for %s condition=%s scale=%s (hits_raw=%s)",
                question_id,
                condition,
                corpus_scale_size,
                len(hits),
            )
        totals["recall_sum"] += metrics["recall"]
        totals["hit_1"] += int(metrics["hit_at_1"])
        totals["hit_5"] += int(metrics["hit_at_5"])
        totals["hit_10"] += int(metrics["hit_at_10"])
        totals["mrr_sum"] += metrics["mrr"]
        totals["evaluated"] += 1
        per_question.append(
            {
                "question_id": question_id,
                "erb_question_id": q.get("erb_question_id") or question_id.split("::", 1)[0],
                "question_type": q.get("question_type"),
                "condition": condition,
                "corpus_scale_size": corpus_scale_size,
                "expected_doc_ids": sorted(expected),
                "n_hits_raw": len(hits),
                **{k: v for k, v in metrics.items() if k != "retrieved_scores"},
            }
        )

        if persist:
            await db.execute(
                text("""
                    INSERT INTO vector_drift_results (
                        experiment_run_id, question_id, target_db_id,
                        retrieved_rank, cosine_similarity,
                        mrr_score, recall_at_1, recall_at_5, recall_at_10,
                        document_recall, condition, corpus_scale_size,
                        expected_doc_ids, retrieved_doc_ids
                    ) VALUES (
                        :run_id, :qid, 0,
                        :rank, :score,
                        :mrr, :r1, :r5, :r10,
                        :doc_recall, :condition, :scale,
                        CAST(:expected AS jsonb), CAST(:retrieved AS jsonb)
                    )
                """),
                {
                    "run_id": run_id,
                    "qid": question_id,
                    "rank": metrics["rank"],
                    "score": metrics["score"],
                    "mrr": metrics["mrr"],
                    "r1": metrics["hit_at_1"],
                    "r5": metrics["hit_at_5"],
                    "r10": metrics["hit_at_10"],
                    "doc_recall": metrics["recall"],
                    "condition": condition,
                    "scale": corpus_scale_size,
                    "expected": json.dumps(sorted(expected)),
                    "retrieved": json.dumps(metrics["retrieved_doc_ids"]),
                },
            )
            for i, (doc_id, score) in enumerate(
                zip(metrics["retrieved_doc_ids"], metrics["retrieved_scores"]), start=1
            ):
                await db.execute(
                    text("""
                        INSERT INTO retrieval_hit_details (
                            experiment_run_id, question_id, condition, corpus_scale_size,
                            hit_rank, doc_id, score, is_gold
                        ) VALUES (
                            :run_id, :qid, :condition, :scale,
                            :rank, :doc_id, :score, :is_gold
                        )
                    """),
                    {
                        "run_id": run_id,
                        "qid": question_id,
                        "condition": condition,
                        "scale": corpus_scale_size,
                        "rank": i,
                        "doc_id": doc_id,
                        "score": score,
                        "is_gold": doc_id in expected,
                    },
                )

    if persist:
        await db.commit()

    n = totals["evaluated"] or 1
    summary = {
        "experiment_run_id": run_id,
        "run_name": run_name,
        "condition": condition,
        "corpus_scale_size": corpus_scale_size,
        "vector_index_type": index_type,
        "force_exact": force_exact,
        "questions_evaluated": totals["evaluated"],
        "questions_skipped": totals["skipped"],
        "document_recall": round(totals["recall_sum"] / n, 4),
        "hit_at_1": round(totals["hit_1"] / n, 4),
        "hit_at_5": round(totals["hit_5"] / n, 4),
        "hit_at_10": round(totals["hit_10"] / n, 4),
        "mrr": round(totals["mrr_sum"] / n, 4),
        "per_question": per_question,
    }
    logger.info(
        "ERB vector drift eval: %s",
        {k: v for k, v in summary.items() if k != "per_question"},
    )
    return summary


async def run_benchmark_vector_drift(
    db: AsyncSession,
    *,
    run_name: str,
    corpus_scale_size: int = 200,
    top_k: int = 10,
    benchmark_path: Path | None = None,
) -> dict:
    return await run_erb_vector_drift(
        db,
        run_name=run_name,
        corpus_scale_size=corpus_scale_size,
        top_k=top_k,
        condition="raw",
        questions=None if benchmark_path is None else load_erb_questions(benchmark_path),
    )
