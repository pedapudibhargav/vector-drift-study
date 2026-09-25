import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class CorpusRun(Base):
    """One ingestion pass at a corpus size milestone (100 → 2000 pages)."""

    __tablename__ = "corpus_runs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    corpus_size: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    namespace: Mapped[str] = mapped_column(String(128), nullable=False)
    page_count: Mapped[int] = mapped_column(Integer, default=0)
    chunk_count: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(32), default="pending")  # pending|running|complete|failed
    manifest: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    retrieval_events: Mapped[list["RetrievalEvent"]] = relationship(back_populates="corpus_run")
    scaling_metrics: Mapped[list["ScalingMetric"]] = relationship(back_populates="corpus_run")


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    retrieval_events: Mapped[list["RetrievalEvent"]] = relationship(back_populates="session")


class RetrievalEvent(Base):
    """One vector search call — raw or metadata-filtered."""

    __tablename__ = "retrieval_events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("chat_sessions.id"), nullable=True
    )
    corpus_run_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("corpus_runs.id"), nullable=True
    )
    query_text: Mapped[str] = mapped_column(Text, nullable=False)
    corpus_size: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    use_metadata_filter: Mapped[bool] = mapped_column(Boolean, default=False)
    metadata_filter: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    top_k: Mapped[int] = mapped_column(Integer, default=5)
    embedding_model: Mapped[str] = mapped_column(String(64), default="text-embedding-3-small")
    match_count: Mapped[int] = mapped_column(Integer, default=0)
    latency_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    session: Mapped["ChatSession | None"] = relationship(back_populates="retrieval_events")
    corpus_run: Mapped["CorpusRun | None"] = relationship(back_populates="retrieval_events")
    matches: Mapped[list["RetrievalMatch"]] = relationship(
        back_populates="event", cascade="all, delete-orphan"
    )


class RetrievalMatch(Base):
    __tablename__ = "retrieval_matches"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("retrieval_events.id"), nullable=False, index=True
    )
    chunk_id: Mapped[str] = mapped_column(String(64), nullable=False)
    rank: Mapped[int] = mapped_column(Integer, nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False)
    url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    page_type: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    chunk_metadata: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    event: Mapped["RetrievalEvent"] = relationship(back_populates="matches")


class ScalingMetric(Base):
    """
    Computed research metrics per corpus size N.
    Supports scaling law: R(N) = R₀·e^(-λN) + R_max·(1 - e^(-λN))·F_meta
    """

    __tablename__ = "scaling_metrics"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    corpus_run_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("corpus_runs.id"), nullable=True
    )
    corpus_size: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    metric_name: Mapped[str] = mapped_column(String(64), nullable=False)  # recall_at_k, hit_rate, mrr
    raw_value: Mapped[float | None] = mapped_column(Float, nullable=True)       # no metadata filter
    filtered_value: Mapped[float | None] = mapped_column(Float, nullable=True)  # with metadata filter
    delta_pct: Mapped[float | None] = mapped_column(Float, nullable=True)       # filtered - raw
    sample_count: Mapped[int] = mapped_column(Integer, default=0)
    params: Mapped[dict | None] = mapped_column(JSONB, nullable=True)  # λ, R₀, R_max, F_meta
    computed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    corpus_run: Mapped["CorpusRun | None"] = relationship(back_populates="scaling_metrics")
