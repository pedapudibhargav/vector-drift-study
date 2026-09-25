from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import ssl_bundle
from app.config import settings
from app.db.session import close_db, init_db
from app.routes import audit, chat, corpus, metrics

ssl_bundle.apply_corporate_ssl_bundle()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield
    await close_db()


app = FastAPI(
    title="Vector Drift Research API",
    description="EnterpriseRAG-Bench corpus scaling & metadata filtering study",
    version="0.3.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "OPTIONS"],
    allow_headers=["*"],
)

app.include_router(chat.router, prefix="/api", tags=["chat"])
app.include_router(metrics.router, prefix="/api/metrics", tags=["metrics"])
app.include_router(corpus.router, prefix="/api", tags=["corpus"])
app.include_router(audit.router, prefix="/api/audit", tags=["audit"])


@app.get("/api")
async def api_root() -> dict:
    return {
        "service": "vector-drift-research",
        "study": "enterprise_rag_bench",
        "docs": "/api/docs",
        "endpoints": {
            "health": "/api/health",
            "chat_stream": "/api/chat/stream",
            "scaling_summary": "/api/metrics/scaling",
            "corpus_stats": "/api/corpus/stats",
            "corpus_chunks": "/api/corpus/chunks",
            "corpus_search": "/api/corpus/search",
            "audit_status": "/api/audit/status",
            "audit_queue": "/api/audit/queue",
            "audit_review": "/api/audit/overview",
        },
    }


@app.get("/api/health")
async def health() -> dict:
    return {"status": "ok", "study": "enterprise_rag_bench"}
