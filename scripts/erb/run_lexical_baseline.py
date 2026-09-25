#!/usr/bin/env python3
"""Postgres full-text (ts_rank) lexical baseline at each corpus scale."""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from paths import DEFAULT_SCALES, ERB_MANIFEST, ERB_RESULTS_DIR, EVAL_TOP_K  # noqa: E402


def _db_url() -> str:
    url = os.environ.get(
        "DATABASE_URL",
        "postgresql://vector_drift:vector_drift@localhost:5432/vector_drift",
    )
    return url.replace("postgresql+asyncpg://", "postgresql://")


def ensure_fts(conn) -> None:
    conn.execute(
        """
        ALTER TABLE document_chunks
          ADD COLUMN IF NOT EXISTS fts tsvector;
        """
    )
    # Backfill missing
    conn.execute(
        """
        UPDATE document_chunks
        SET fts = to_tsvector('english', coalesce(title,'') || ' ' || coalesce(chunk_text,''))
        WHERE fts IS NULL AND embedding IS NOT NULL;
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_chunks_fts
        ON document_chunks USING gin (fts);
        """
    )
    conn.commit()


def load_questions(manifest: Path, *, primary: int | None, seed: int = 42) -> list[dict]:
    data = json.loads(manifest.read_text(encoding="utf-8"))
    qs = list(data.get("questions") or [])
    if not primary or primary <= 0 or primary >= len(qs):
        return qs
    # stratified sample
    import random
    from collections import defaultdict

    rng = random.Random(seed)
    by_type: dict[str, list[dict]] = defaultdict(list)
    for q in qs:
        by_type[str(q.get("question_type") or "other")].append(q)
    # proportional
    total = len(qs)
    picked: list[dict] = []
    for t, bucket in by_type.items():
        n = max(1, round(primary * len(bucket) / total))
        rng.shuffle(bucket)
        picked.extend(bucket[:n])
    rng.shuffle(picked)
    return picked[:primary]


def eval_scale(conn, questions: list[dict], *, scale: int, top_k: int) -> dict:
    hit1 = hit5 = hit10 = 0
    recall_sum = 0.0
    mrr_sum = 0.0
    evaluated = 0
    per_q: list[dict] = []

    for q in questions:
        expected = {str(x) for x in (q.get("expected_doc_ids") or []) if x}
        if not expected:
            continue
        # plainto_tsquery is robust to punctuation
        rows = conn.execute(
            """
            SELECT doc_id,
                   ts_rank_cd(fts, plainto_tsquery('english', %s)) AS score
            FROM document_chunks
            WHERE embedding IS NOT NULL
              AND scale_rank IS NOT NULL
              AND scale_rank < %s
              AND fts @@ plainto_tsquery('english', %s)
            ORDER BY score DESC
            LIMIT %s
            """,
            (q["question"], scale, q["question"], top_k),
        ).fetchall()
        retrieved = [r[0] for r in rows if r[0]]
        # If FTS matches fewer than top_k, pad empty — rank only over matches
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
                "question_id": q["question_id"],
                "rank": rank,
                "hit_at_10": r10,
                "document_recall": recall,
                "mrr": mrr,
                "retrieved_doc_ids": retrieved,
            }
        )

    n = evaluated or 1
    return {
        "condition": "lexical_fts",
        "corpus_scale_size": scale,
        "questions_evaluated": evaluated,
        "hit_at_1": round(hit1 / n, 4),
        "hit_at_5": round(hit5 / n, 4),
        "hit_at_10": round(hit10 / n, 4),
        "document_recall": round(recall_sum / n, 4),
        "mrr": round(mrr_sum / n, 4),
        "per_question": per_q,
    }


def persist_lexical_run(conn, summary: dict) -> str:
    """Write experiment_runs + per-question vector_drift_results for lexical arm."""
    import uuid

    run_id = str(uuid.uuid4())
    conn.execute(
        """
        INSERT INTO experiment_runs
            (id, run_name, corpus_scale_size, embedding_model, vector_index_type, condition, status)
        VALUES (%s, %s, %s, %s, %s, %s, 'COMPLETED')
        """,
        (
            run_id,
            f"erb_lexical_n{summary['corpus_scale_size']}",
            int(summary["corpus_scale_size"]),
            "postgres_ts_rank_cd",
            "gin_fts",
            "lexical_fts",
        ),
    )
    for q in summary.get("per_question") or []:
        conn.execute(
            """
            INSERT INTO vector_drift_results (
                experiment_run_id, question_id, target_db_id,
                retrieved_rank, cosine_similarity,
                mrr_score, recall_at_1, recall_at_5, recall_at_10,
                document_recall, condition, corpus_scale_size,
                expected_doc_ids, retrieved_doc_ids
            ) VALUES (
                %s, %s, 0,
                %s, NULL,
                %s, %s, %s, %s,
                %s, 'lexical_fts', %s,
                %s::jsonb, %s::jsonb
            )
            """,
            (
                run_id,
                str(q.get("question_id") or ""),
                q.get("rank"),
                float(q.get("mrr") or 0.0),
                bool(q.get("rank") == 1),
                bool(q.get("rank") is not None and q["rank"] <= 5),
                bool(q.get("hit_at_10")),
                float(q.get("document_recall") or 0.0),
                int(summary["corpus_scale_size"]),
                json.dumps([]),
                json.dumps(q.get("retrieved_doc_ids") or []),
            ),
        )
        for i, doc_id in enumerate(q.get("retrieved_doc_ids") or [], start=1):
            conn.execute(
                """
                INSERT INTO retrieval_hit_details (
                    experiment_run_id, question_id, condition, corpus_scale_size,
                    hit_rank, doc_id, score, is_gold
                ) VALUES (%s, %s, 'lexical_fts', %s, %s, %s, NULL, FALSE)
                """,
                (
                    run_id,
                    str(q.get("question_id") or ""),
                    int(summary["corpus_scale_size"]),
                    i,
                    str(doc_id),
                ),
            )
    conn.commit()
    return run_id


def main() -> int:
    import psycopg

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=ERB_MANIFEST)
    parser.add_argument("--scales", type=int, nargs="+", default=list(DEFAULT_SCALES))
    parser.add_argument("--top-k", type=int, default=EVAL_TOP_K)
    parser.add_argument("--primary-questions", type=int, default=200)
    parser.add_argument("--persist-db", action="store_true", default=True)
    parser.add_argument("--no-persist-db", action="store_false", dest="persist_db")
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args()

    questions = load_questions(args.manifest, primary=args.primary_questions)
    conn = psycopg.connect(_db_url())
    try:
        ensure_fts(conn)
        # Cap scales by embedded coverage (count of ranks filled is safer than MAX)
        max_n = conn.execute(
            """
            SELECT COALESCE(
              (SELECT COUNT(*) FROM document_chunks
               WHERE embedding IS NOT NULL AND scale_rank IS NOT NULL
                 AND scale_rank < 100000),
              0
            )
            """
        ).fetchone()[0]
        # Also allow MAX for contiguous prefix check
        max_rank_plus = conn.execute(
            "SELECT COALESCE(MAX(scale_rank)+1,0) FROM document_chunks "
            "WHERE embedding IS NOT NULL AND scale_rank IS NOT NULL AND scale_rank < 100000"
        ).fetchone()[0]
        coverage = min(int(max_n), int(max_rank_plus)) if max_rank_plus else int(max_n)
        scales = [n for n in args.scales if n <= coverage]
        if not scales:
            raise SystemExit(f"no scales <= embedded coverage {coverage}")

        runs = []
        for n in scales:
            summary = eval_scale(conn, questions, scale=n, top_k=args.top_k)
            if args.persist_db:
                rid = persist_lexical_run(conn, summary)
                summary["experiment_run_id"] = rid
            slim = {k: v for k, v in summary.items() if k != "per_question"}
            print(json.dumps(slim), flush=True)
            runs.append(summary)

        payload = {
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "method": "postgres_ts_rank_cd + plainto_tsquery(english)",
            "question_count": len(questions),
            "primary_questions": args.primary_questions,
            "embedded_coverage": coverage,
            "scales": scales,
            "persisted_db": bool(args.persist_db),
            "runs": [{k: v for k, v in r.items() if k != "per_question"} for r in runs],
            "per_question_by_scale": {
                str(r["corpus_scale_size"]): r["per_question"] for r in runs
            },
        }
        ERB_RESULTS_DIR.mkdir(parents=True, exist_ok=True)
        out = args.out or (
            ERB_RESULTS_DIR
            / f"erb_lexical_baseline_{time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())}.json"
        )
        out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print(f"wrote {out}", flush=True)
    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
