#!/usr/bin/env python3
"""Create Titan experiment result tables (separate from OpenAI vector_drift_results).

Also realigns document_chunks_titan.scale_rank / source_type / is_gold_anchor
to match document_chunks for shared doc_ids (gold-pin parity).
"""

from __future__ import annotations

import os

import psycopg

DDL = """
CREATE TABLE IF NOT EXISTS experiment_runs_titan (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_name VARCHAR(255) NOT NULL,
    corpus_scale_size INT NOT NULL,
    embedding_model VARCHAR(100) NOT NULL,
    vector_index_type VARCHAR(100) NOT NULL,
    condition VARCHAR(32) DEFAULT 'raw',
    status VARCHAR(50) DEFAULT 'COMPLETED',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS vector_drift_results_titan (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    experiment_run_id UUID REFERENCES experiment_runs_titan(id) ON DELETE CASCADE,
    question_id VARCHAR(128) NOT NULL,
    target_db_id INT NOT NULL DEFAULT 0,
    retrieved_rank INT,
    cosine_similarity FLOAT,
    mrr_score FLOAT,
    recall_at_1 BOOLEAN,
    recall_at_5 BOOLEAN,
    recall_at_10 BOOLEAN,
    document_recall FLOAT,
    condition VARCHAR(32),
    corpus_scale_size INT,
    expected_doc_ids JSONB,
    retrieved_doc_ids JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_experiment_runs_titan_scale
    ON experiment_runs_titan (corpus_scale_size);
CREATE INDEX IF NOT EXISTS idx_vector_drift_titan_run
    ON vector_drift_results_titan (experiment_run_id);
CREATE INDEX IF NOT EXISTS idx_vector_drift_titan_run_q
    ON vector_drift_results_titan (experiment_run_id, question_id);
CREATE INDEX IF NOT EXISTS idx_vector_drift_titan_scale
    ON vector_drift_results_titan (corpus_scale_size, condition);
"""

ALIGN = """
UPDATE document_chunks_titan t
SET scale_rank = o.scale_rank,
    is_gold_anchor = o.is_gold_anchor,
    source_type = o.source_type
FROM document_chunks o
WHERE t.doc_id = o.doc_id
  AND (
    t.scale_rank IS DISTINCT FROM o.scale_rank
    OR t.is_gold_anchor IS DISTINCT FROM o.is_gold_anchor
    OR t.source_type IS DISTINCT FROM o.source_type
  );
"""


def _db_url() -> str:
    return os.environ.get(
        "DATABASE_URL",
        "postgresql://vector_drift:vector_drift@localhost:5432/vector_drift",
    ).replace("postgresql+asyncpg://", "postgresql://")


def main() -> int:
    with psycopg.connect(_db_url()) as conn:
        conn.execute(DDL)
        cur = conn.execute(ALIGN)
        aligned = cur.rowcount if cur is not None else -1
        mismatch = conn.execute(
            """
            SELECT count(*) FROM document_chunks o
            JOIN document_chunks_titan t USING (doc_id)
            WHERE o.scale_rank IS DISTINCT FROM t.scale_rank
            """
        ).fetchone()[0]
        under = conn.execute(
            """
            SELECT
              (SELECT count(*) FROM document_chunks WHERE scale_rank < 100000) AS openai_u,
              (SELECT count(*) FROM document_chunks_titan WHERE scale_rank < 100000) AS titan_u
            """
        ).fetchone()
        conn.commit()
    print(f"schema ready; rows_updated={aligned} rank_mismatch={mismatch} under_100k openai={under[0]} titan={under[1]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
