from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import PROJECT_ROOT
from app.db.models import CorpusRun, RetrievalEvent
from app.db.repository import get_scaling_summary
from app.db.session import SessionLocal

router = APIRouter()


async def get_db() -> AsyncSession:
    async with SessionLocal() as session:
        yield session


@router.get("/scaling")
async def scaling_summary(db: AsyncSession = Depends(get_db)) -> dict:
    """Aggregated recall/hit-rate metrics per corpus size for scaling law plots."""
    rows = await get_scaling_summary(db)
    return {"metrics": rows, "count": len(rows)}


@router.get("/vector-drift")
async def vector_drift_ladder(
    embedder: str = Query("openai", pattern="^(openai|titan)$"),
    condition: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Per-scale Hit@k summary from OpenAI or Titan experiment result tables."""
    if embedder == "titan":
        runs_table = "experiment_runs_titan"
        results_table = "vector_drift_results_titan"
        model_default = "amazon.titan-embed-text-v2:0"
        model_filter = "amazon.titan-embed-text-v2:0"
    else:
        runs_table = "experiment_runs"
        results_table = "vector_drift_results"
        model_default = "text-embedding-3-small"
        model_filter = "text-embedding-3-small"

    cond_clause = ""
    params: dict = {"model": model_filter}
    if condition:
        cond_clause = "AND latest.condition = :condition"
        params["condition"] = condition

    rows = (
        await db.execute(
            text(f"""
                WITH latest AS (
                  SELECT DISTINCT ON (corpus_scale_size, condition)
                    id, corpus_scale_size, condition, embedding_model
                  FROM {runs_table}
                  WHERE embedding_model = :model
                    AND condition IN ('raw', 'meta')
                    AND run_name LIKE 'erb_%'
                  ORDER BY corpus_scale_size, condition, created_at DESC
                )
                SELECT
                  latest.corpus_scale_size,
                  latest.condition,
                  latest.embedding_model,
                  COUNT(*) AS n,
                  AVG(CASE WHEN v.recall_at_1 THEN 1.0 ELSE 0.0 END) AS hit_at_1,
                  AVG(CASE WHEN v.recall_at_5 THEN 1.0 ELSE 0.0 END) AS hit_at_5,
                  AVG(CASE WHEN v.recall_at_10 THEN 1.0 ELSE 0.0 END) AS hit_at_10,
                  AVG(v.mrr_score) AS mrr,
                  AVG(v.document_recall) AS document_recall
                FROM latest
                JOIN {results_table} v ON v.experiment_run_id = latest.id
                WHERE 1=1 {cond_clause}
                GROUP BY 1, 2, 3
                ORDER BY 1, 2
            """),
            params,
        )
    ).mappings().all()
    return {
        "embedder": embedder,
        "results_table": results_table,
        "embedding_model": (rows[0]["embedding_model"] if rows else model_default),
        "runs": [
            {
                "corpus_scale_size": int(r["corpus_scale_size"] or 0),
                "condition": r["condition"],
                "n": int(r["n"] or 0),
                "hit_at_1": round(float(r["hit_at_1"] or 0), 4),
                "hit_at_5": round(float(r["hit_at_5"] or 0), 4),
                "hit_at_10": round(float(r["hit_at_10"] or 0), 4),
                "mrr": round(float(r["mrr"] or 0), 4),
                "document_recall": round(float(r["document_recall"] or 0), 4),
            }
            for r in rows
        ],
        "count": len(rows),
    }


@router.get("/openai-vs-titan")
async def openai_vs_titan() -> dict:
    """Published OpenAI vs Titan comparison artifact (if present)."""
    path = PROJECT_ROOT / "artifacts" / "published" / "openai_vs_titan_primary200.json"
    if not path.is_file():
        raise HTTPException(status_code=404, detail="openai_vs_titan_primary200.json not found yet")
    import json

    return json.loads(path.read_text(encoding="utf-8"))


@router.get("/corpus-runs")
async def list_corpus_runs(db: AsyncSession = Depends(get_db)) -> dict:
    result = await db.execute(select(CorpusRun).order_by(CorpusRun.corpus_size))
    runs = result.scalars().all()
    return {
        "runs": [
            {
                "id": str(r.id),
                "corpus_size": r.corpus_size,
                "namespace": r.namespace,
                "page_count": r.page_count,
                "chunk_count": r.chunk_count,
                "status": r.status,
                "started_at": r.started_at.isoformat() if r.started_at else None,
                "completed_at": r.completed_at.isoformat() if r.completed_at else None,
            }
            for r in runs
        ]
    }


@router.get("/retrieval-events")
async def list_retrieval_events(
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
) -> dict:
    result = await db.execute(
        select(RetrievalEvent).order_by(RetrievalEvent.created_at.desc()).limit(limit)
    )
    events = result.scalars().all()
    return {
        "events": [
            {
                "id": str(e.id),
                "query_text": e.query_text[:200],
                "corpus_size": e.corpus_size,
                "use_metadata_filter": e.use_metadata_filter,
                "match_count": e.match_count,
                "latency_ms": e.latency_ms,
                "created_at": e.created_at.isoformat() if e.created_at else None,
            }
            for e in events
        ]
    }
