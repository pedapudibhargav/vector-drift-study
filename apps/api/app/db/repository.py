import math
import uuid
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import ChatSession, CorpusRun, RetrievalEvent, RetrievalMatch, ScalingMetric


async def create_chat_session(session: AsyncSession) -> uuid.UUID:
    row = ChatSession()
    session.add(row)
    await session.flush()
    return row.id


async def persist_retrieval(
    session: AsyncSession,
    *,
    session_id: uuid.UUID | None,
    query_text: str,
    corpus_size: int | None,
    use_metadata_filter: bool,
    metadata_filter: dict | None,
    top_k: int,
    embedding_model: str,
    matches: list[dict],
    latency_ms: float | None = None,
) -> uuid.UUID:
    event = RetrievalEvent(
        session_id=session_id,
        query_text=query_text,
        corpus_size=corpus_size,
        use_metadata_filter=use_metadata_filter,
        metadata_filter=metadata_filter,
        top_k=top_k,
        embedding_model=embedding_model,
        match_count=len(matches),
        latency_ms=latency_ms,
    )
    session.add(event)
    await session.flush()

    for rank, match in enumerate(matches, 1):
        meta = match.get("metadata") or {}
        session.add(
            RetrievalMatch(
                event_id=event.id,
                chunk_id=match.get("id", ""),
                rank=rank,
                score=float(match.get("score") or 0),
                url=meta.get("url") or meta.get("source_url"),
                page_type=meta.get("page_type"),
                chunk_metadata=meta,
            )
        )

    await session.commit()
    return event.id


async def upsert_corpus_run(
    session: AsyncSession,
    corpus_size: int,
    namespace: str,
    *,
    page_count: int = 0,
    chunk_count: int = 0,
    status: str = "pending",
    manifest: dict | None = None,
) -> uuid.UUID:
    result = await session.execute(
        select(CorpusRun).where(
            CorpusRun.corpus_size == corpus_size,
            CorpusRun.namespace == namespace,
        )
    )
    row = result.scalar_one_or_none()
    if row is None:
        row = CorpusRun(
            corpus_size=corpus_size,
            namespace=namespace,
            page_count=page_count,
            chunk_count=chunk_count,
            status=status,
            manifest=manifest,
        )
        session.add(row)
    else:
        row.page_count = page_count
        row.chunk_count = chunk_count
        row.status = status
        row.manifest = manifest
        if status == "complete":
            row.completed_at = datetime.now(timezone.utc)
    await session.commit()
    await session.refresh(row)
    return row.id


async def record_scaling_metric(
    session: AsyncSession,
    *,
    corpus_size: int,
    metric_name: str,
    raw_value: float | None,
    filtered_value: float | None,
    sample_count: int = 0,
    params: dict | None = None,
    corpus_run_id: uuid.UUID | None = None,
) -> uuid.UUID:
    delta = None
    if raw_value is not None and filtered_value is not None and raw_value > 0:
        delta = ((filtered_value - raw_value) / raw_value) * 100

    row = ScalingMetric(
        corpus_run_id=corpus_run_id,
        corpus_size=corpus_size,
        metric_name=metric_name,
        raw_value=raw_value,
        filtered_value=filtered_value,
        delta_pct=delta,
        sample_count=sample_count,
        params=params,
    )
    session.add(row)
    await session.commit()
    await session.refresh(row)
    return row.id


async def get_scaling_summary(session: AsyncSession) -> list[dict]:
    """Aggregate metrics per corpus_size for scaling law visualization."""
    result = await session.execute(
        select(
            ScalingMetric.corpus_size,
            ScalingMetric.metric_name,
            func.avg(ScalingMetric.raw_value).label("avg_raw"),
            func.avg(ScalingMetric.filtered_value).label("avg_filtered"),
            func.avg(ScalingMetric.delta_pct).label("avg_delta_pct"),
            func.count(ScalingMetric.id).label("samples"),
        )
        .group_by(ScalingMetric.corpus_size, ScalingMetric.metric_name)
        .order_by(ScalingMetric.corpus_size)
    )
    return [
        {
            "corpus_size": r.corpus_size,
            "metric_name": r.metric_name,
            "avg_raw": round(r.avg_raw, 4) if r.avg_raw is not None else None,
            "avg_filtered": round(r.avg_filtered, 4) if r.avg_filtered is not None else None,
            "avg_delta_pct": round(r.avg_delta_pct, 2) if r.avg_delta_pct is not None else None,
            "samples": r.samples,
        }
        for r in result.all()
    ]


def compute_scaling_law_params(corpus_sizes: list[int], recall_values: list[float]) -> dict:
    """
    Estimate draft scaling law parameters from empirical recall@K data.
    R(N) = R₀·e^(-λN) + R_max·(1 - e^(-λN))·F_meta
    Returns simplified λ estimate; full fit requires scipy (future work).
    """
    if len(corpus_sizes) < 2:
        return {"lambda": None, "r0": recall_values[0] if recall_values else None}

    n0, n1 = corpus_sizes[0], corpus_sizes[-1]
    r0, r1 = recall_values[0], recall_values[-1]
    if r0 <= 0 or n1 <= n0:
        return {"r0": r0, "r_end": r1}

    # Simple exponential decay estimate: λ ≈ -ln(r1/r0) / (N1 - N0)
    lam = -math.log(max(r1, 0.001) / max(r0, 0.001)) / (n1 - n0)
    return {"r0": round(r0, 4), "r_end": round(r1, 4), "lambda": round(lam, 6)}
