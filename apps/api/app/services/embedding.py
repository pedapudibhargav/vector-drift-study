"""OpenAI embedding pipeline — production settings for RAG ingestion."""

from __future__ import annotations

import asyncio
import logging
import random
import time

import tiktoken
from openai import APIStatusError, AsyncOpenAI, OpenAI, RateLimitError
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import resolve_openai_api_key

logger = logging.getLogger(__name__)

EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIMENSIONS = 1536
MAX_INPUT_TOKENS = 8191
EMBED_BATCH_SIZE = 100
EMBED_BATCH_PAUSE_S = 3.0  # pause between batches to avoid RPM 429s
ENCODING_NAME = "cl100k_base"
MAX_RETRIES = 8
INITIAL_BACKOFF_S = 2.0

_enc: tiktoken.Encoding | None = None


def get_encoding() -> tiktoken.Encoding:
    global _enc
    if _enc is None:
        _enc = tiktoken.get_encoding(ENCODING_NAME)
    return _enc


def truncate_for_embedding(text: str) -> str:
    """Truncate to model context. Falls back to char budget if tiktoken SSL/download fails."""
    try:
        enc = get_encoding()
        tokens = enc.encode(text, disallowed_special=())
        if len(tokens) <= MAX_INPUT_TOKENS:
            return text
        return enc.decode(tokens[:MAX_INPUT_TOKENS])
    except Exception as exc:  # noqa: BLE001
        logger.warning("tiktoken unavailable (%s); using char truncate", exc)
        # ~4 chars/token conservative budget
        max_chars = MAX_INPUT_TOKENS * 4
        return text if len(text) <= max_chars else text[:max_chars]


def vector_literal(vec: list[float]) -> str:
    return "[" + ",".join(str(v) for v in vec) + "]"


def validate_embedding(vec: list[float], *, dims: int = EMBEDDING_DIMENSIONS) -> list[float]:
    """Reject empty / wrong-dim / non-finite / near-zero vectors before DB write."""
    if not vec or len(vec) != dims:
        raise ValueError(f"bad embedding length={len(vec) if vec else 0} expected={dims}")
    norm_sq = 0.0
    for x in vec:
        if x != x or x in (float("inf"), float("-inf")):  # NaN / Inf
            raise ValueError("embedding contains non-finite values")
        norm_sq += float(x) * float(x)
    if norm_sq < 1e-12:
        raise ValueError("embedding near-zero norm")
    return vec


def _is_retryable(exc: Exception) -> bool:
    if isinstance(exc, RateLimitError):
        return True
    if isinstance(exc, APIStatusError):
        return exc.status_code in (429, 500, 502, 503, 504)
    return False


def _retry_delay(exc: Exception, attempt: int) -> float:
    if isinstance(exc, APIStatusError) and exc.status_code == 429:
        retry_after = exc.response.headers.get("retry-after") if exc.response else None
        if retry_after:
            try:
                return float(retry_after) + random.uniform(0.5, 1.5)
            except ValueError:
                pass
        return max(8.0, INITIAL_BACKOFF_S * (2**attempt)) + random.uniform(0, 1.0)
    return INITIAL_BACKOFF_S * (2**attempt) + random.uniform(0, 0.5)


def _embedding_client_sync(*, api_key: str | None = None) -> OpenAI:
    from app import ssl_bundle

    ssl_bundle.apply_corporate_ssl_bundle()
    key = api_key or resolve_openai_api_key()
    return OpenAI(api_key=key, max_retries=0)


async def _embedding_client_async() -> AsyncOpenAI:
    from app import ssl_bundle

    ssl_bundle.apply_corporate_ssl_bundle()
    return AsyncOpenAI(api_key=resolve_openai_api_key(), max_retries=0)


def _embed_batch_sync(client: OpenAI, texts: list[str]) -> list[list[float]]:
    inputs = [truncate_for_embedding(t) for t in texts]
    for attempt in range(MAX_RETRIES):
        try:
            response = client.embeddings.create(
                model=EMBEDDING_MODEL,
                input=inputs,
                dimensions=EMBEDDING_DIMENSIONS,
            )
            return [item.embedding for item in response.data]
        except Exception as exc:
            if not _is_retryable(exc) or attempt == MAX_RETRIES - 1:
                raise
            delay = _retry_delay(exc, attempt)
            logger.warning(
                "Embedding batch retry %s/%s after %.1fs: %s",
                attempt + 1,
                MAX_RETRIES,
                delay,
                exc,
            )
            time.sleep(delay)
    raise RuntimeError("embedding batch failed after retries")


async def _embed_batch_async(client: AsyncOpenAI, texts: list[str]) -> list[list[float]]:
    inputs = [truncate_for_embedding(t) for t in texts]
    for attempt in range(MAX_RETRIES):
        try:
            response = await client.embeddings.create(
                model=EMBEDDING_MODEL,
                input=inputs,
                dimensions=EMBEDDING_DIMENSIONS,
            )
            return [item.embedding for item in response.data]
        except Exception as exc:
            if not _is_retryable(exc) or attempt == MAX_RETRIES - 1:
                raise
            delay = _retry_delay(exc, attempt)
            logger.warning(
                "Embedding batch retry %s/%s after %.1fs: %s",
                attempt + 1,
                MAX_RETRIES,
                delay,
                exc,
            )
            await asyncio.sleep(delay)
    raise RuntimeError("embedding batch failed after retries")


def embed_texts_sync(texts: list[str], *, api_key: str | None = None) -> list[list[float]]:
    key = api_key or resolve_openai_api_key()
    if not key or key.startswith("sk-your"):
        raise ValueError("OPENAI_API_KEY not set — load root .env before embedding")
    client = _embedding_client_sync(api_key=key)
    vectors: list[list[float]] = []
    for start in range(0, len(texts), EMBED_BATCH_SIZE):
        batch = texts[start : start + EMBED_BATCH_SIZE]
        vectors.extend(_embed_batch_sync(client, batch))
        if start + EMBED_BATCH_SIZE < len(texts):
            time.sleep(EMBED_BATCH_PAUSE_S)
    return vectors


async def embed_texts_async(texts: list[str], *, client: AsyncOpenAI | None = None) -> list[list[float]]:
    if client is None:
        client = await _embedding_client_async()
    vectors: list[list[float]] = []
    for start in range(0, len(texts), EMBED_BATCH_SIZE):
        batch = texts[start : start + EMBED_BATCH_SIZE]
        vectors.extend(await _embed_batch_async(client, batch))
        if start + EMBED_BATCH_SIZE < len(texts):
            await asyncio.sleep(EMBED_BATCH_PAUSE_S)
    return vectors


async def embed_single_text(text: str) -> list[float]:
    vectors = await embed_texts_async([text])
    return vectors[0]


async def embed_url_chunks(db: AsyncSession, url: str) -> int:
    """Embed and persist all chunks for one URL."""
    row = await db.execute(
        text("""
            SELECT chunk_index, chunk_text
            FROM document_chunks
            WHERE url = :url AND embedding IS NULL
            ORDER BY chunk_index
        """),
        {"url": url},
    )
    chunks = list(row.mappings())
    if not chunks:
        return 0

    vectors = await embed_texts_async([c["chunk_text"] for c in chunks])
    for chunk, vector in zip(chunks, vectors):
        await db.execute(
            text("""
                UPDATE document_chunks
                SET embedding = CAST(:vec AS vector),
                    metadata = COALESCE(metadata, '{}'::jsonb)
                        || jsonb_build_object('embedded', true, 'embedding_model', CAST(:model AS text))
                WHERE url = :url AND chunk_index = :idx
            """),
            {
                "vec": vector_literal(vector),
                "url": url,
                "idx": chunk["chunk_index"],
                "model": EMBEDDING_MODEL,
            },
        )
    return len(vectors)
