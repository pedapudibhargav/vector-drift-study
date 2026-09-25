from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.db.session import check_db_connection, check_vector_db
from app.schemas import ChatRequest, HealthStatus
from app.services.chat import check_openai_connection, stream_chat_response
from app import __version__

router = APIRouter()


@router.get("/health", response_model=HealthStatus)
async def health() -> HealthStatus:
    openai_status = await check_openai_connection()
    vector_status = await check_vector_db()
    postgres_status = await check_db_connection()

    core_ok = postgres_status == "connected" and vector_status.startswith("connected")
    overall = "healthy" if core_ok and openai_status == "connected" else "degraded"
    return HealthStatus(
        status=overall,
        openai=openai_status,
        vector_db=vector_status,
        postgres=postgres_status,
        version=__version__,
    )


@router.post("/chat/stream")
async def chat_stream(request: ChatRequest) -> StreamingResponse:
    return StreamingResponse(
        stream_chat_response(request),
        media_type="application/x-ndjson",
    )
