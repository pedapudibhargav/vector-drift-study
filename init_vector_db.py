#!/usr/bin/env python3
"""Initialize PostgreSQL + pgvector schema for document chunks."""

from __future__ import annotations

import os
import sys

import psycopg

DDL = """
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS document_chunks (
    id BIGSERIAL PRIMARY KEY,
    url TEXT NOT NULL,
    title TEXT,
    chunk_index INTEGER NOT NULL,
    chunk_text TEXT NOT NULL,
    token_count INTEGER,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    embedding vector(1536),
    doc_id TEXT,
    source_type TEXT,
    scale_rank INTEGER,
    is_gold_anchor BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (url, chunk_index)
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_document_chunks_doc_id
ON document_chunks (doc_id) WHERE doc_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_chunks_metadata ON document_chunks USING gin (metadata);
CREATE INDEX IF NOT EXISTS idx_chunks_url ON document_chunks (url);
CREATE INDEX IF NOT EXISTS idx_chunks_scale_rank ON document_chunks (scale_rank);
CREATE INDEX IF NOT EXISTS idx_chunks_source_type ON document_chunks (source_type);

CREATE INDEX IF NOT EXISTS idx_chunks_embedding_hnsw
ON document_chunks USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

CREATE TABLE IF NOT EXISTS crawl_runs (
    id BIGSERIAL PRIMARY KEY,
    mode TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'running',
    target_count INTEGER NOT NULL,
    primary_only BOOLEAN NOT NULL DEFAULT FALSE,
    stored_count INTEGER NOT NULL DEFAULT 0,
    primary_stored_count INTEGER NOT NULL DEFAULT 0,
    fetched_count INTEGER NOT NULL DEFAULT 0,
    skipped_non_200 INTEGER NOT NULL DEFAULT 0,
    skipped_duplicate INTEGER NOT NULL DEFAULT 0,
    errors INTEGER NOT NULL DEFAULT 0,
    checkpoint JSONB,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE
);

CREATE TABLE IF NOT EXISTS dataset_urls (
    id BIGSERIAL PRIMARY KEY,
    url TEXT UNIQUE NOT NULL,
    title TEXT,
    domain_type TEXT,
    service_category TEXT,
    page_type TEXT,
    path_depth INTEGER,
    is_primary_candidate BOOLEAN NOT NULL DEFAULT FALSE,
    primary_domain TEXT,
    http_status INTEGER NOT NULL DEFAULT 200,
    identified_at TIMESTAMP WITH TIME ZONE NOT NULL,
    crawl_run_id BIGINT REFERENCES crawl_runs(id),
    crawl_state TEXT NOT NULL DEFAULT 'stored',
    ingestion_status TEXT NOT NULL DEFAULT 'pending',
    html_content TEXT,
    text_content TEXT,
    text_quality JSONB,
    chunk_count INTEGER NOT NULL DEFAULT 0,
    last_error TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_dataset_urls_ingestion ON dataset_urls (ingestion_status);
CREATE INDEX IF NOT EXISTS idx_dataset_urls_primary ON dataset_urls (is_primary_candidate);
CREATE INDEX IF NOT EXISTS idx_dataset_urls_identified ON dataset_urls (identified_at DESC);
CREATE INDEX IF NOT EXISTS idx_crawl_runs_status ON crawl_runs (status, mode);

CREATE TABLE IF NOT EXISTS experiment_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_name VARCHAR(255) NOT NULL,
    corpus_scale_size INT NOT NULL,
    embedding_model VARCHAR(100) NOT NULL,
    vector_index_type VARCHAR(100) NOT NULL,
    status VARCHAR(50) DEFAULT 'COMPLETED',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS vector_drift_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    experiment_run_id UUID REFERENCES experiment_runs(id) ON DELETE CASCADE,
    question_id VARCHAR(50) NOT NULL,
    target_db_id INT NOT NULL,
    retrieved_rank INT,
    cosine_similarity FLOAT,
    euclidean_distance FLOAT,
    mrr_score FLOAT,
    recall_at_1 BOOLEAN,
    recall_at_5 BOOLEAN,
    recall_at_10 BOOLEAN,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

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

CREATE INDEX IF NOT EXISTS idx_experiment_runs_scale ON experiment_runs (corpus_scale_size);
CREATE INDEX IF NOT EXISTS idx_vector_drift_run ON vector_drift_results (experiment_run_id);
CREATE INDEX IF NOT EXISTS idx_llm_eval_run ON llm_eval_results (experiment_run_id);
"""


def main() -> int:
    dsn = os.environ.get(
        "DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/vector_drift_db",
    ).replace("postgresql+asyncpg://", "postgresql://")
    try:
        with psycopg.connect(dsn, autocommit=True) as conn:
            conn.execute(DDL)
        print(f"Vector DB initialized: {dsn.split('@')[-1]}")
        return 0
    except Exception as exc:
        print(f"init_vector_db failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
