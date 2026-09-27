"""Sync pgvector HNSW evaluation via psycopg2 (no SQLAlchemy).

Parity with ``app.services.vector_search`` / ``run_ef_search_ablation.eval_scale_raw``.
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any

from paths import QUERY_EMBED_CACHE


def db_url_sync() -> str:
    return os.environ.get(
        "DATABASE_URL",
        "postgresql://vector_drift:vector_drift@localhost:5432/vector_drift",
    ).replace("postgresql+asyncpg://", "postgresql://")


def vector_literal(vec: list[float]) -> str:
    return "[" + ",".join(str(v) for v in vec) + "]"


def load_query_cache(qids: list[str], cache_path: Path | None = None) -> dict[str, list[float]]:
    path = cache_path or QUERY_EMBED_CACHE
    if not path.exists():
        raise SystemExit(f"missing query embed cache: {path}")
    cache_raw = json.loads(path.read_text(encoding="utf-8"))
    cache: dict[str, list[float]] = {}
    for qid in qids:
        v = cache_raw.get(qid)
        if isinstance(v, list):
            cache[qid] = v
        elif isinstance(v, dict) and "embedding" in v:
            cache[qid] = v["embedding"]
    missing = [qid for qid in qids if qid not in cache]
    if missing:
        raise SystemExit(f"missing {len(missing)} query embeddings (e.g. {missing[:3]})")
    return cache


def eval_scale_raw(
    conn,
    questions: list[dict],
    *,
    scale: int,
    top_k: int = 10,
    ef_search: int = 200,
    qvecs: dict[str, list[float]],
    condition: str = "raw",
) -> dict[str, Any]:
    """Sync HNSW eval on document_chunks (scale_rank < N)."""
    hit1 = hit5 = hit10 = 0
    recall_sum = mrr_sum = 0.0
    evaluated = skipped = 0
    exact_fallbacks = 0
    per_q: list[dict] = []

    cur = conn.cursor()
    cur.execute(f"SET hnsw.ef_search = {ef_search}")
    try:
        cur.execute("SET hnsw.iterative_scan = relaxed_order")
    except Exception:
        conn.rollback()

    for q in questions:
        expected = {str(x) for x in (q.get("expected_doc_ids") or []) if x}
        if not expected:
            skipped += 1
            continue

        qid = str(q["question_id"])
        if qid not in qvecs:
            skipped += 1
            continue

        metadata_filter = ""
        params_extra: tuple = ()
        if condition == "meta":
            source_types = q.get("source_types") or []
            if not source_types:
                skipped += 1
                continue
            metadata_filter = " AND source_type = %s"
            params_extra = (str(source_types[0]),)

        lit = vector_literal(qvecs[qid])
        sql = f"""
            SELECT doc_id, 1 - (embedding <=> %s::vector) AS score
            FROM document_chunks
            WHERE embedding IS NOT NULL
              AND scale_rank IS NOT NULL
              AND scale_rank < %s
              {metadata_filter}
            ORDER BY embedding <=> %s::vector
            LIMIT %s
        """
        params = (lit, scale, *params_extra, lit, top_k)
        cur.execute(sql, params)
        rows = cur.fetchall()

        if len(rows) < top_k:
            exact_fallbacks += 1
            cur.execute("SET enable_indexscan = off")
            cur.execute("SET enable_bitmapscan = off")
            try:
                cur.execute(sql, params)
                rows = cur.fetchall()
            finally:
                cur.execute("SET enable_indexscan = on")
                cur.execute("SET enable_bitmapscan = on")

        retrieved = [r[0] for r in rows if r[0]]
        rank = None
        for i, doc_id in enumerate(retrieved, start=1):
            if doc_id in expected:
                rank = i
                break
        hit_ids = expected & set(retrieved)
        recall = len(hit_ids) / max(len(expected), 1)
        mrr = 1.0 / rank if rank else 0.0
        r1 = rank == 1 if rank else False
        r5 = rank is not None and rank <= 5
        r10 = rank is not None and rank <= 10
        hit1 += int(r1)
        hit5 += int(r5)
        hit10 += int(r10)
        recall_sum += recall
        mrr_sum += mrr
        evaluated += 1
        per_q.append(
            {
                "question_id": qid,
                "rank": rank,
                "hit_at_1": r1,
                "hit_at_5": r5,
                "hit_at_10": r10,
                "mrr": mrr,
                "document_recall": recall,
                "retrieved_doc_ids": retrieved,
            }
        )

    n = evaluated or 1
    return {
        "condition": condition,
        "corpus_scale_size": scale,
        "ef_search": ef_search,
        "questions_evaluated": evaluated,
        "questions_skipped": skipped,
        "exact_fallbacks": exact_fallbacks,
        "hit_at_1": round(hit1 / n, 4),
        "hit_at_5": round(hit5 / n, 4),
        "hit_at_10": round(hit10 / n, 4),
        "document_recall": round(recall_sum / n, 4),
        "mrr": round(mrr_sum / n, 4),
        "per_question": per_q,
    }


def run_endpoint_sweep(
    conn,
    questions: list[dict],
    qvecs: dict[str, list[float]],
    *,
    scales: list[int],
    conditions: list[str],
    top_k: int = 10,
    ef_search: int = 200,
) -> list[dict]:
    results: list[dict] = []
    for n in scales:
        for condition in conditions:
            t0 = time.time()
            print(f"sync eval N={n} condition={condition} ef_search={ef_search} …", flush=True)
            summary = eval_scale_raw(
                conn,
                questions,
                scale=n,
                top_k=top_k,
                ef_search=ef_search,
                qvecs=qvecs,
                condition=condition,
            )
            elapsed = round(time.time() - t0, 1)
            summary["elapsed_s"] = elapsed
            summary["run_name"] = f"erb_{condition}_n{n}"
            results.append(summary)
            print(
                f"  Hit@1={summary['hit_at_1']:.3f} Hit@5={summary['hit_at_5']:.3f} "
                f"Hit@10={summary['hit_at_10']:.3f} MRR={summary['mrr']:.3f} ({elapsed}s)",
                flush=True,
            )
    return results
