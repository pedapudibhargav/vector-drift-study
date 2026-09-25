#!/usr/bin/env python3
"""Ensure ERB study tables for per-query hits, costs, and LLM validation."""

from __future__ import annotations

import os
import sys

import psycopg

DDL = """
CREATE EXTENSION IF NOT EXISTS vector;

ALTER TABLE document_chunks ADD COLUMN IF NOT EXISTS doc_id TEXT;
ALTER TABLE document_chunks ADD COLUMN IF NOT EXISTS source_type TEXT;
ALTER TABLE document_chunks ADD COLUMN IF NOT EXISTS scale_rank INTEGER;
ALTER TABLE document_chunks ADD COLUMN IF NOT EXISTS is_gold_anchor BOOLEAN NOT NULL DEFAULT FALSE;

CREATE UNIQUE INDEX IF NOT EXISTS idx_document_chunks_doc_id
ON document_chunks (doc_id) WHERE doc_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_chunks_scale_rank ON document_chunks (scale_rank);
CREATE INDEX IF NOT EXISTS idx_chunks_source_type ON document_chunks (source_type);

CREATE TABLE IF NOT EXISTS experiment_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_name VARCHAR(255) NOT NULL,
    corpus_scale_size INT NOT NULL,
    embedding_model VARCHAR(100) NOT NULL,
    vector_index_type VARCHAR(100) NOT NULL,
    condition VARCHAR(32) DEFAULT 'raw',
    status VARCHAR(50) DEFAULT 'COMPLETED',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

ALTER TABLE experiment_runs ADD COLUMN IF NOT EXISTS condition VARCHAR(32) DEFAULT 'raw';

CREATE TABLE IF NOT EXISTS vector_drift_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    experiment_run_id UUID REFERENCES experiment_runs(id) ON DELETE CASCADE,
    question_id VARCHAR(50) NOT NULL,
    target_db_id INT NOT NULL DEFAULT 0,
    retrieved_rank INT,
    cosine_similarity FLOAT,
    euclidean_distance FLOAT,
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

ALTER TABLE vector_drift_results ADD COLUMN IF NOT EXISTS document_recall FLOAT;
ALTER TABLE vector_drift_results ADD COLUMN IF NOT EXISTS condition VARCHAR(32);
ALTER TABLE vector_drift_results ADD COLUMN IF NOT EXISTS corpus_scale_size INT;
ALTER TABLE vector_drift_results ADD COLUMN IF NOT EXISTS expected_doc_ids JSONB;
ALTER TABLE vector_drift_results ADD COLUMN IF NOT EXISTS retrieved_doc_ids JSONB;

CREATE TABLE IF NOT EXISTS retrieval_hit_details (
    id BIGSERIAL PRIMARY KEY,
    experiment_run_id UUID REFERENCES experiment_runs(id) ON DELETE CASCADE,
    question_id TEXT NOT NULL,
    condition TEXT NOT NULL,
    corpus_scale_size INT NOT NULL,
    hit_rank INT NOT NULL,
    doc_id TEXT NOT NULL,
    score FLOAT,
    is_gold BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_hit_details_run ON retrieval_hit_details (experiment_run_id);
CREATE INDEX IF NOT EXISTS idx_hit_details_q ON retrieval_hit_details (question_id, corpus_scale_size);

CREATE TABLE IF NOT EXISTS llm_eval_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    experiment_run_id UUID REFERENCES experiment_runs(id) ON DELETE CASCADE,
    question_id VARCHAR(50) NOT NULL,
    evaluator_model VARCHAR(100) NOT NULL,
    faithfulness_score FLOAT,
    answer_relevance_score FLOAT,
    context_recall_score FLOAT,
    context_precision_score FLOAT,
    latency_ms INT,
    cost_usd DECIMAL(10, 6),
    reasoning_summary TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS erb_cost_events (
    id BIGSERIAL PRIMARY KEY,
    kind TEXT NOT NULL,
    tokens INT,
    input_tokens INT,
    output_tokens INT,
    docs INT,
    cost_usd DOUBLE PRECISION NOT NULL,
    note TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_llm_eval_question ON llm_eval_results (question_id);
CREATE INDEX IF NOT EXISTS idx_vector_drift_run_question
ON vector_drift_results (experiment_run_id, question_id);
CREATE INDEX IF NOT EXISTS idx_llm_eval_run_question
ON llm_eval_results (experiment_run_id, question_id);
"""


def main() -> int:
    url = os.environ.get(
        "DATABASE_URL",
        "postgresql://vector_drift:vector_drift@localhost:5432/vector_drift",
    ).replace("postgresql+asyncpg://", "postgresql://")
    with psycopg.connect(url) as conn:
        conn.execute(DDL)
        conn.commit()
    print("ERB study schema ready")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
