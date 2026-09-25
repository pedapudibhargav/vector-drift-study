"""Corpus browse + retrieval inspection for the ERB study."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import text

from app.db.session import SessionLocal
from app.services.embedding import embed_single_text
from app.services.vector_search import query_vectors

router = APIRouter(prefix="/corpus", tags=["corpus"])

_EMBEDDER_TABLES = {
    "openai": "document_chunks",
    "titan": "document_chunks_titan",
}


def _chunk_table(embedder: str) -> str:
    key = (embedder or "openai").lower().strip()
    if key not in _EMBEDDER_TABLES:
        raise HTTPException(status_code=400, detail=f"embedder must be one of {sorted(_EMBEDDER_TABLES)}")
    return _EMBEDDER_TABLES[key]


class SearchRequest(BaseModel):
    query: str = Field(min_length=1)
    top_k: int = Field(default=3, ge=1, le=20)
    corpus_scale_size: int | None = None
    source_type: str | None = None
    embedder: str = "openai"


@router.get("/stats")
async def corpus_stats(embedder: str = Query("openai")) -> dict:
    table = _chunk_table(embedder)
    async with SessionLocal() as db:
        row = (
            await db.execute(
                text(f"""
                    SELECT
                      COUNT(*) FILTER (WHERE embedding IS NOT NULL) AS embedded,
                      COUNT(*) AS total,
                      COUNT(DISTINCT source_type) AS sources,
                      MIN(scale_rank) AS min_rank,
                      MAX(scale_rank) AS max_rank,
                      COUNT(*) FILTER (WHERE scale_rank < 100000) AS under_100k
                    FROM {table}
                    WHERE doc_id IS NOT NULL
                """)
            )
        ).mappings().one()
        by_source = (
            await db.execute(
                text(f"""
                    SELECT source_type, COUNT(*) AS n
                    FROM {table}
                    WHERE embedding IS NOT NULL
                    GROUP BY source_type
                    ORDER BY n DESC
                """)
            )
        ).mappings().all()
    return {
        "embedder": embedder,
        "table": table,
        "embedded": int(row["embedded"] or 0),
        "total_rows": int(row["total"] or 0),
        "under_100k": int(row["under_100k"] or 0),
        "sources": int(row["sources"] or 0),
        "min_scale_rank": row["min_rank"],
        "max_scale_rank": row["max_rank"],
        "by_source": [{"source_type": r["source_type"], "count": int(r["n"])} for r in by_source],
    }


@router.get("/chunks")
async def list_chunks(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    source_type: str | None = None,
    q: str | None = None,
    gold_only: bool = False,
    max_scale_rank: int | None = None,
    embedder: str = Query("openai"),
) -> dict:
    table = _chunk_table(embedder)
    conditions = ["doc_id IS NOT NULL", "embedding IS NOT NULL"]
    params: dict = {
        "limit": page_size,
        "offset": (page - 1) * page_size,
    }
    if source_type:
        conditions.append("source_type = :source_type")
        params["source_type"] = source_type
    if gold_only:
        conditions.append("is_gold_anchor = TRUE")
    if max_scale_rank is not None:
        conditions.append("scale_rank < :max_scale_rank")
        params["max_scale_rank"] = max_scale_rank
    if q:
        conditions.append("(doc_id ILIKE :q OR title ILIKE :q OR chunk_text ILIKE :q)")
        params["q"] = f"%{q}%"
    where = " AND ".join(conditions)
    async with SessionLocal() as db:
        total = (
            await db.execute(text(f"SELECT COUNT(*) FROM {table} WHERE {where}"), params)
        ).scalar_one()
        rows = (
            await db.execute(
                text(f"""
                    SELECT id, doc_id, title, source_type, scale_rank, is_gold_anchor,
                           LEFT(chunk_text, 400) AS preview
                    FROM {table}
                    WHERE {where}
                    ORDER BY scale_rank NULLS LAST, id
                    LIMIT :limit OFFSET :offset
                """),
                params,
            )
        ).mappings().all()
    return {
        "embedder": embedder,
        "table": table,
        "page": page,
        "page_size": page_size,
        "total": int(total),
        "items": [dict(r) for r in rows],
    }


@router.get("/chunks/{doc_id}")
async def get_chunk(doc_id: str, embedder: str = Query("openai")) -> dict:
    table = _chunk_table(embedder)
    async with SessionLocal() as db:
        row = (
            await db.execute(
                text(f"""
                    SELECT id, doc_id, title, source_type, scale_rank, is_gold_anchor,
                           chunk_text, metadata
                    FROM {table}
                    WHERE doc_id = :doc_id
                    LIMIT 1
                """),
                {"doc_id": doc_id},
            )
        ).mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="doc not found")
    return {"embedder": embedder, **dict(row)}


@router.post("/search")
async def search_chunks(body: SearchRequest) -> dict:
    if body.embedder.lower() != "openai":
        raise HTTPException(
            status_code=400,
            detail="Interactive search currently supports embedder=openai only; Titan ladder metrics are on /api/metrics/vector-drift?embedder=titan",
        )
    vec = await embed_single_text(body.query)
    mf = {"source_type": body.source_type} if body.source_type else None
    async with SessionLocal() as db:
        hits = await query_vectors(
            db,
            vec,
            top_k=body.top_k,
            metadata_filter=mf,
            corpus_scale_size=body.corpus_scale_size,
        )
    return {
        "query": body.query,
        "embedder": "openai",
        "top_k": body.top_k,
        "corpus_scale_size": body.corpus_scale_size,
        "hits": [
            {
                "rank": i,
                "doc_id": h.get("doc_id"),
                "score": h.get("score"),
                "source_type": (h.get("metadata") or {}).get("source_type"),
                "title": (h.get("metadata") or {}).get("title"),
                "preview": ((h.get("metadata") or {}).get("chunk_text") or "")[:500],
            }
            for i, h in enumerate(hits, start=1)
        ],
    }
