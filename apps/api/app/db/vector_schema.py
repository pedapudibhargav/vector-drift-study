"""DDL for pgvector tables — mirrors init_vector_db.py."""

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection

VECTOR_DDL = """
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
"""

ERB_ALTERS = """
ALTER TABLE document_chunks ADD COLUMN IF NOT EXISTS doc_id TEXT;
ALTER TABLE document_chunks ADD COLUMN IF NOT EXISTS source_type TEXT;
ALTER TABLE document_chunks ADD COLUMN IF NOT EXISTS scale_rank INTEGER;
ALTER TABLE document_chunks ADD COLUMN IF NOT EXISTS is_gold_anchor BOOLEAN NOT NULL DEFAULT FALSE;
"""


async def ensure_vector_schema(conn: AsyncConnection) -> None:
    for stmt in VECTOR_DDL.split(";"):
        s = stmt.strip()
        if s:
            await conn.execute(text(s))
    for stmt in ERB_ALTERS.split(";"):
        s = stmt.strip()
        if s:
            await conn.execute(text(s))

    await conn.execute(
        text("""
        DO $$ BEGIN
            CREATE INDEX IF NOT EXISTS idx_chunks_embedding_hnsw
            ON document_chunks USING hnsw (embedding vector_cosine_ops)
            WITH (m = 16, ef_construction = 64);
        EXCEPTION WHEN undefined_object OR others THEN
            NULL;
        END $$;
        """)
    )
