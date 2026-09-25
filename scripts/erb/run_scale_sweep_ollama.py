#!/usr/bin/env python3
"""Scale sweep against document_chunks_ollama (nomic-embed-text). $0 LLM cost.

Parity with OpenAI arm:
  - stratified_unique primary-200 (eval_id = question_id::question_type)
  - meta filter uses source_types[0] (same as vector_drift_eval)
  - query embeddings cached to avoid re-embedding across scales/conditions
  - HNSW ef_search=200 when index is present
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from paths import (  # noqa: E402
    DEFAULT_SCALES,
    ERB_MANIFEST,
    ERB_RESULTS_DIR,
    EVAL_TOP_K,
)
from ingest_erb_ollama import DIM, OLLAMA_MODEL, ollama_embed, vector_literal  # noqa: E402
from question_identity import stratified_unique  # noqa: E402

QUERY_CACHE = Path(__file__).resolve().parents[2] / "data" / "erb_ollama_query_embed_cache.json"


def _db_url() -> str:
    return os.environ.get(
        "DATABASE_URL",
        "postgresql://vector_drift:vector_drift@localhost:5432/vector_drift",
    ).replace("postgresql+asyncpg://", "postgresql://")


def _eligible(questions: list[dict]) -> list[dict]:
    out: list[dict] = []
    for q in questions:
        qtype = str(q.get("question_type") or "").lower()
        if qtype in {"high_level", "info_not_found"}:
            continue
        if not (q.get("expected_doc_ids") or []):
            continue
        out.append(q)
    return out


def _meta_source_type(q: dict) -> str | None:
    sts = q.get("source_types") or []
    if sts:
        return str(sts[0])
    st = q.get("source_type")
    return str(st) if st else None


def _load_query_cache() -> dict[str, list[float]]:
    if not QUERY_CACHE.exists():
        return {}
    try:
        raw = json.loads(QUERY_CACHE.read_text(encoding="utf-8"))
        if isinstance(raw, dict) and raw.get("model") == OLLAMA_MODEL:
            return {str(k): v for k, v in (raw.get("vectors") or {}).items() if isinstance(v, list)}
    except Exception:  # noqa: BLE001
        pass
    return {}


def _save_query_cache(vectors: dict[str, list[float]]) -> None:
    QUERY_CACHE.parent.mkdir(parents=True, exist_ok=True)
    QUERY_CACHE.write_text(
        json.dumps(
            {
                "model": OLLAMA_MODEL,
                "dim": DIM,
                "count": len(vectors),
                "updated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "vectors": vectors,
            }
        ),
        encoding="utf-8",
    )


def _ensure_query_vectors(questions: list[dict], *, workers: int) -> dict[str, list[float]]:
    cache = _load_query_cache()
    missing = [q for q in questions if str(q["question_id"]) not in cache]
    if missing:
        print(f"embedding {len(missing)} query vectors (cache hit={len(questions)-len(missing)})", flush=True)
        texts = [str(q["question"]) for q in missing]
        # embed in chunks to keep Ollama stable
        chunk = 32
        for i in range(0, len(texts), chunk):
            batch_q = missing[i : i + chunk]
            batch_t = texts[i : i + chunk]
            vecs = ollama_embed(batch_t, workers=workers)
            for q, v in zip(batch_q, vecs):
                cache[str(q["question_id"])] = v
            _save_query_cache(cache)
            print(f"  query cache {min(i+chunk, len(texts))}/{len(texts)}", flush=True)
    return cache


def eval_scale(
    conn,
    questions: list[dict],
    *,
    scale: int,
    top_k: int,
    condition: str,
    qvecs: dict[str, list[float]],
) -> dict:
    hit1 = hit5 = hit10 = 0
    recall_sum = mrr_sum = 0.0
    evaluated = 0
    skipped_meta = 0
    per_q: list[dict] = []

    # Match OpenAI HNSW search settings when index is used
    conn.execute("SET hnsw.ef_search = 200")
    conn.execute("SET hnsw.iterative_scan = relaxed_order")

    for q in questions:
        expected = {str(x) for x in (q.get("expected_doc_ids") or []) if x}
        if not expected:
            continue

        st: str | None = None
        if condition == "meta":
            st = _meta_source_type(q)
            if not st:
                skipped_meta += 1
                continue

        qvec = qvecs[str(q["question_id"])]
        lit = vector_literal(qvec)

        if condition == "meta":
            rows = conn.execute(
                """
                SELECT doc_id, 1 - (embedding <=> %s::vector) AS score
                FROM document_chunks_ollama
                WHERE embedding IS NOT NULL
                  AND scale_rank IS NOT NULL
                  AND scale_rank < %s
                  AND source_type = %s
                ORDER BY embedding <=> %s::vector
                LIMIT %s
                """,
                (lit, scale, st, lit, top_k),
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT doc_id, 1 - (embedding <=> %s::vector) AS score
                FROM document_chunks_ollama
                WHERE embedding IS NOT NULL
                  AND scale_rank IS NOT NULL
                  AND scale_rank < %s
                ORDER BY embedding <=> %s::vector
                LIMIT %s
                """,
                (lit, scale, lit, top_k),
            ).fetchall()

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
                "question_id": q.get("question_id"),
                "question_type": q.get("question_type"),
                "rank": rank,
                "hit_at_1": r1,
                "hit_at_5": r5,
                "hit_at_10": r10,
                "document_recall": recall,
                "mrr": mrr,
                "meta_source_type": st,
            }
        )

    n = evaluated or 1
    return {
        "condition": condition,
        "corpus_scale_size": scale,
        "questions_evaluated": evaluated,
        "questions_skipped_meta": skipped_meta,
        "hit_at_1": round(hit1 / n, 4),
        "hit_at_5": round(hit5 / n, 4),
        "hit_at_10": round(hit10 / n, 4),
        "document_recall": round(recall_sum / n, 4),
        "mrr": round(mrr_sum / n, 4),
        "embedding_model": OLLAMA_MODEL,
        "embedding_dim": DIM,
        "vector_index": "hnsw",
        "ef_search": 200,
        "per_question": per_q,
    }


def main() -> int:
    import psycopg

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=ERB_MANIFEST)
    parser.add_argument("--scales", type=int, nargs="+", default=list(DEFAULT_SCALES))
    parser.add_argument("--top-k", type=int, default=EVAL_TOP_K)
    parser.add_argument("--primary-questions", type=int, default=200)
    parser.add_argument("--conditions", nargs="+", default=["raw", "meta"])
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args()

    data = json.loads(args.manifest.read_text(encoding="utf-8"))
    eligible = _eligible(list(data.get("questions") or []))
    questions = stratified_unique(eligible, args.primary_questions, seed=42)
    print(
        f"primary bank n={len(questions)} eligible={len(eligible)} model={OLLAMA_MODEL}",
        flush=True,
    )

    qvecs = _ensure_query_vectors(questions, workers=args.workers)

    conn = psycopg.connect(_db_url())
    try:
        max_n = conn.execute(
            "SELECT COALESCE(MAX(scale_rank)+1,0) FROM document_chunks_ollama "
            "WHERE embedding IS NOT NULL"
        ).fetchone()[0]
        covered = int(
            conn.execute(
                "SELECT COUNT(*) FROM document_chunks_ollama WHERE embedding IS NOT NULL"
            ).fetchone()[0]
        )
        scales = [n for n in args.scales if n <= int(max_n) and n <= covered]
        if not scales:
            raise SystemExit(f"no ollama scales feasible coverage_rows={covered} max_rank+1={max_n}")

        runs = []
        for n in scales:
            for cond in args.conditions:
                summary = eval_scale(
                    conn, questions, scale=n, top_k=args.top_k, condition=cond, qvecs=qvecs
                )
                slim = {k: v for k, v in summary.items() if k != "per_question"}
                print(json.dumps(slim), flush=True)
                runs.append(summary)

        payload = {
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "arm": "ollama",
            "embedding_model": OLLAMA_MODEL,
            "embedding_dim": DIM,
            "question_count": len(questions),
            "primary_questions": args.primary_questions,
            "seed": 42,
            "identity": "question_id::question_type",
            "embedded_coverage_rows": covered,
            "embedded_coverage_max_rank_plus_1": int(max_n),
            "scales": scales,
            "runs": [{k: v for k, v in r.items() if k != "per_question"} for r in runs],
            "runs_with_per_question": runs,
        }
        ERB_RESULTS_DIR.mkdir(parents=True, exist_ok=True)
        out = args.out or (
            ERB_RESULTS_DIR
            / f"erb_ollama_sweep_{time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())}.json"
        )
        out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        # also publish thin copy without per_question for size
        pub = Path(__file__).resolve().parents[2] / "artifacts" / "published" / "erb_ollama_primary200_to100k.json"
        pub.parent.mkdir(parents=True, exist_ok=True)
        thin = dict(payload)
        thin.pop("runs_with_per_question", None)
        pub.write_text(json.dumps(thin, indent=2), encoding="utf-8")
        print(f"wrote {out}", flush=True)
        print(f"wrote {pub}", flush=True)
    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
