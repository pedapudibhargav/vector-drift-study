"""pgvector similarity search with corpus-scale and metadata filters."""

from __future__ import annotations

import os

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

# HNSW + post-filters (scale_rank / source_type) can return 0 rows even when
# matching chunks exist — the index returns unfiltered neighbors, then WHERE
# drops them. pgvector 0.8+ iterative scans + higher ef_search fix this.
_DEFAULT_EF_SEARCH = 200


def hnsw_ef_search() -> int:
    """Published protocol default 200; override via HNSW_EF_SEARCH for ablations."""
    raw = os.environ.get("HNSW_EF_SEARCH", str(_DEFAULT_EF_SEARCH))
    try:
        val = int(raw)
    except ValueError:
        val = _DEFAULT_EF_SEARCH
    return val if val >= 1 else _DEFAULT_EF_SEARCH


async def _configure_filtered_hnsw(db: AsyncSession) -> None:
    ef = hnsw_ef_search()
    session_sql = (
        "SELECT set_config('hnsw.iterative_scan', 'relaxed_order', true), "
        f"set_config('hnsw.ef_search', '{ef}', true)"
    )
    try:
        await db.execute(text(session_sql))
    except Exception:
        # Older builds may lack iterative_scan; ef_search alone still helps.
        try:
            await db.execute(text(f"SELECT set_config('hnsw.ef_search', '{ef}', true)"))
        except Exception:
            pass


async def query_vectors(
    db: AsyncSession,
    vector: list[float],
    top_k: int = 5,
    metadata_filter: dict[str, str] | None = None,
    *,
    corpus_scale_size: int | None = None,
    force_exact: bool = False,
) -> list[dict]:
    vec_literal = "[" + ",".join(str(v) for v in vector) + "]"
    conditions = ["embedding IS NOT NULL"]
    params: dict = {"vec": vec_literal, "top_k": top_k}
    filtered = False

    if corpus_scale_size is not None:
        conditions.append("scale_rank IS NOT NULL AND scale_rank < :corpus_scale_size")
        params["corpus_scale_size"] = int(corpus_scale_size)
        filtered = True

    if metadata_filter:
        filtered = True
        for i, (k, v) in enumerate(metadata_filter.items()):
            if k == "source_type":
                conditions.append("source_type = :mf_source_type")
                params["mf_source_type"] = v
                continue
            key = f"mf_{i}"
            conditions.append(f"metadata->>'{k}' = :{key}")
            params[key] = v

    if filtered and not force_exact:
        await _configure_filtered_hnsw(db)

    where = " AND ".join(conditions)
    sql = text(f"""
        SELECT id, url, doc_id, chunk_index, chunk_text, metadata, source_type, scale_rank,
               1 - (embedding <=> CAST(:vec AS vector)) AS score
        FROM document_chunks
        WHERE {where}
        ORDER BY embedding <=> CAST(:vec AS vector)
        LIMIT :top_k
    """)

    async def _run(disable_index: bool) -> list[dict]:
        if disable_index:
            await db.execute(text("SELECT set_config('enable_indexscan', 'off', true)"))
            await db.execute(text("SELECT set_config('enable_bitmapscan', 'off', true)"))
        try:
            rows = await db.execute(sql, params)
            return [
                {
                    "id": str(r["id"]),
                    "score": float(r["score"]),
                    "doc_id": r["doc_id"] or r["url"],
                    "metadata": {
                        **(r["metadata"] or {}),
                        "url": r["url"],
                        "doc_id": r["doc_id"] or r["url"],
                        "source_type": r["source_type"],
                        "scale_rank": r["scale_rank"],
                        "chunk_text": r["chunk_text"],
                        "chunk_index": r["chunk_index"],
                    },
                }
                for r in rows.mappings()
            ]
        finally:
            if disable_index:
                await db.execute(text("SELECT set_config('enable_indexscan', 'on', true)"))
                await db.execute(text("SELECT set_config('enable_bitmapscan', 'on', true)"))

    if force_exact:
        return await _run(disable_index=True)

    hits = await _run(disable_index=False)

    # Exact fallback when HNSW still under-fills (dense metadata filters).
    if filtered and len(hits) < top_k:
        hits = await _run(disable_index=True)

    return hits
