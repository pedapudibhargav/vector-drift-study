import logging

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings
from app.db.models import Base
from app.db.audit_schema import ensure_audit_schema
from app.db.experiment_schema import ensure_experiment_schema
from app.db.vector_schema import ensure_vector_schema

logger = logging.getLogger(__name__)

engine = create_async_engine(
    settings.database_url,
    echo=False,
    pool_pre_ping=True,
)
SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await ensure_vector_schema(conn)
        await ensure_experiment_schema(conn)
        await ensure_audit_schema(conn)
    logger.info("Database schema ready")


async def close_db() -> None:
    await engine.dispose()


async def check_db_connection() -> str:
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return "connected"
    except Exception as exc:
        logger.warning("Database health check failed: %s", exc)
        return "error"


async def check_vector_db() -> str:
    try:
        async with engine.connect() as conn:
            row = await conn.execute(
                text("SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname = 'vector') AS ok")
            )
            if not row.scalar_one():
                return "extension_missing"
            chunks = await conn.execute(
                text(
                    "SELECT COUNT(*) FROM information_schema.tables "
                    "WHERE table_name = 'document_chunks'"
                )
            )
            if not chunks.scalar_one():
                return "schema_pending"
            count = await conn.execute(text("SELECT COUNT(*) FROM document_chunks"))
            return f"connected:{count.scalar_one()}_chunks"
    except Exception as exc:
        logger.warning("Vector DB health check failed: %s", exc)
        return "error"
