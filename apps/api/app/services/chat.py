import json
import logging
import time
import uuid
from collections.abc import AsyncGenerator

from openai import APIConnectionError, AuthenticationError, RateLimitError

from app.clients import get_openai_client
from app.config import settings
from app.db.repository import create_chat_session, persist_retrieval
from app.db.session import SessionLocal
from app.schemas import ChatRequest
from app.services.embedding import EMBEDDING_DIMENSIONS, EMBEDDING_MODEL, embed_single_text
from app.services.vector_search import query_vectors

logger = logging.getLogger(__name__)

CHAT_COMPLETION_MODEL = "gpt-4o-mini"


async def check_openai_connection() -> str:
    if not settings.openai_api_key or settings.openai_api_key.startswith("sk-your"):
        return "not_configured"
    try:
        client = get_openai_client()
        await client.models.list()
        return "connected"
    except AuthenticationError:
        return "auth_error"
    except (APIConnectionError, RateLimitError, Exception) as exc:
        logger.warning("OpenAI health check failed: %s", exc)
        return "error"


async def query_vector_db(
    vector: list[float],
    top_k: int,
    metadata_filter: dict[str, str] | None = None,
) -> list[dict]:
    async with SessionLocal() as db:
        return await query_vectors(db, vector, top_k=top_k, metadata_filter=metadata_filter)


async def stream_chat_response(request: ChatRequest) -> AsyncGenerator[str, None]:
    session_id: uuid.UUID | None = None

    yield _ndjson("status", {"phase": "embedding", "message": "Generating query embedding..."})

    try:
        query_vector = await embed_single_text(request.message)
    except Exception as exc:
        yield _ndjson("error", {"message": f"Embedding failed: {exc}"})
        return

    yield _ndjson("embedding", {
        "model": EMBEDDING_MODEL,
        "dimensions": EMBEDDING_DIMENSIONS,
        "sample": query_vector[:5],
    })

    yield _ndjson("status", {"phase": "retrieval", "message": "Querying pgvector..."})

    t0 = time.perf_counter()
    try:
        matches = await query_vector_db(
            query_vector,
            request.top_k,
            request.metadata_filter if request.use_metadata_filter else None,
        )
    except Exception as exc:
        yield _ndjson("error", {"message": f"Retrieval failed: {exc}"})
        return
    latency_ms = (time.perf_counter() - t0) * 1000

    yield _ndjson("retrieval", {
        "top_k": request.top_k,
        "use_metadata_filter": request.use_metadata_filter,
        "metadata_filter": request.metadata_filter,
        "corpus_size": request.corpus_size,
        "match_count": len(matches),
        "latency_ms": round(latency_ms, 2),
        "matches": matches,
    })

    try:
        async with SessionLocal() as db:
            session_id = await create_chat_session(db)
            event_id = await persist_retrieval(
                db,
                session_id=session_id,
                query_text=request.message,
                corpus_size=request.corpus_size,
                use_metadata_filter=request.use_metadata_filter,
                metadata_filter=request.metadata_filter,
                top_k=request.top_k,
                embedding_model=EMBEDDING_MODEL,
                matches=matches,
                latency_ms=latency_ms,
            )
            yield _ndjson("persisted", {"session_id": str(session_id), "event_id": str(event_id)})
    except Exception as exc:
        logger.warning("Failed to persist retrieval to PostgreSQL: %s", exc)

    context = _build_context(matches)
    yield _ndjson("status", {"phase": "generation", "message": "Generating response..."})

    try:
        client = get_openai_client()
        stream = await client.chat.completions.create(
            model=CHAT_COMPLETION_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a research assistant for corpus scaling and vector drift analysis. "
                        "Answer based on the retrieved context. Cite source URLs when available."
                    ),
                },
                {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {request.message}"},
            ],
            stream=True,
        )
        async for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                yield _ndjson("token", {"content": delta})
    except Exception as exc:
        yield _ndjson("error", {"message": f"Generation failed: {exc}"})
        return

    yield _ndjson("done", {"model": CHAT_COMPLETION_MODEL})


def _build_context(matches: list[dict]) -> str:
    if not matches:
        return "No relevant documents retrieved from pgvector."
    parts = []
    for i, match in enumerate(matches, 1):
        meta = match.get("metadata", {})
        text = meta.get("text", meta.get("chunk_text", ""))
        url = meta.get("url", "unknown")
        score = match.get("score", 0)
        parts.append(f"[{i}] (score={score:.4f}, url={url})\n{text}")
    return "\n\n".join(parts)


def _ndjson(event: str, data: dict) -> str:
    return json.dumps({"event": event, "data": data}) + "\n"
