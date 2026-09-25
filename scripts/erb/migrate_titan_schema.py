#!/usr/bin/env python3
"""Create document_chunks_titan (1024-d) for Amazon Titan Text Embeddings V2 study arm."""

from __future__ import annotations

import os

DDL = """
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS document_chunks_titan (
    id BIGSERIAL PRIMARY KEY,
    url TEXT NOT NULL,
    doc_id TEXT,
    title TEXT,
    chunk_index INTEGER NOT NULL DEFAULT 0,
    chunk_text TEXT NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    embedding vector(1024),
    source_type TEXT,
    scale_rank INTEGER,
    is_gold_anchor BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (url, chunk_index)
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_chunks_titan_doc_id
ON document_chunks_titan (doc_id) WHERE doc_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_chunks_titan_scale_rank
ON document_chunks_titan (scale_rank);
CREATE INDEX IF NOT EXISTS idx_chunks_titan_source_type
ON document_chunks_titan (source_type);

DO $$ BEGIN
    CREATE INDEX IF NOT EXISTS idx_chunks_titan_embedding_hnsw
    ON document_chunks_titan USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);
EXCEPTION WHEN undefined_object OR others THEN
    NULL;
END $$;
"""


def main() -> int:
    import psycopg

    url = os.environ.get(
        "DATABASE_URL",
        "postgresql://vector_drift:vector_drift@localhost:5432/vector_drift",
    ).replace("postgresql+asyncpg://", "postgresql://")
    with psycopg.connect(url) as conn:
        conn.execute(DDL)
        conn.commit()
    print("document_chunks_titan ready (vector 1024)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
