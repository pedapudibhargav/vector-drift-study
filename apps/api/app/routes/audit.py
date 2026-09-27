"""Human + LLM audit API: queue, detail with chunk text, labels, paper checklist, export."""

from __future__ import annotations

import csv
import io
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import PlainTextResponse, StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import PROJECT_ROOT
from app.db.audit_schema import PAPER_CHECKLIST_SEED
from app.db.session import SessionLocal
from app.services import audit_llm as audit_llm_svc

router = APIRouter()

FAILURE_MODES = [
    "embedding_near_miss",
    "lexical_mismatch",
    "semantic_near_miss",
    "wrong_source_type",
    "stale_gold",
    "chunk_too_thin",
    "multi_gold_partial",
    "metadata_needed",
    "label_noise",
    "other",
]

ARTIFACT_CANDIDATES = [
    PROJECT_ROOT / "artifacts" / "published",
    Path("/app/artifacts/published"),
    PROJECT_ROOT / "data" / "results",
]
VERIFY_CANDIDATES = [
    PROJECT_ROOT / "artifacts" / "verification",
    PROJECT_ROOT / "docs" / "data" / "verification",
    Path("/app/artifacts/verification"),
    Path("/app/docs/data/verification"),
]

_SWEEP_INDEX: dict[tuple[str, int, str], dict[str, Any]] | None = None
_MANIFEST_Q: dict[str, dict[str, Any]] | None = None
_TRIAGE_INDEX: dict[tuple[str, int, str], dict[str, Any]] | None = None


def _find_published_dir() -> Path | None:
    for p in ARTIFACT_CANDIDATES:
        if p.is_dir():
            return p
    return None


def _find_verify_dir() -> Path | None:
    for p in VERIFY_CANDIDATES:
        if (p / "questions.json").exists() or (p / "chunks_by_id.json").exists():
            return p
    return None


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _split_ids(raw: Any) -> list[str]:
    if raw is None:
        return []
    if isinstance(raw, list):
        return [str(x) for x in raw if x]
    s = str(raw).strip()
    if not s:
        return []
    if s.startswith("["):
        try:
            return [str(x) for x in json.loads(s) if x]
        except json.JSONDecodeError:
            pass
    return [p for p in s.split("|") if p]


def _parse_hit(raw: Any) -> bool | None:
    if raw is None or raw == "":
        return None
    if isinstance(raw, bool):
        return raw
    s = str(raw).strip().lower()
    if s in ("true", "1", "t", "yes"):
        return True
    if s in ("false", "0", "f", "no"):
        return False
    return None


def _load_sweep_index() -> dict[tuple[str, int, str], dict[str, Any]]:
    global _SWEEP_INDEX
    if _SWEEP_INDEX is not None:
        return _SWEEP_INDEX
    idx: dict[tuple[str, int, str], dict[str, Any]] = {}
    pub = _find_published_dir()
    candidates = []
    if pub:
        candidates.extend(
            [
                pub / "erb_full_primary200_to100k.json",
                pub / "erb_full_primary_corrected.json",
            ]
        )
    candidates.append(PROJECT_ROOT / "data" / "results" / "erb_scale_sweep_20260920T203818Z.json")
    for path in candidates:
        if not path.exists():
            continue
        try:
            blob = _load_json(path)
        except Exception:  # noqa: BLE001
            continue
        for run in blob.get("runs") or []:
            scale = int(run.get("corpus_scale_size") or 0)
            cond = str(run.get("condition") or "raw")
            for q in run.get("per_question") or []:
                qid = str(q.get("question_id") or "")
                if not qid:
                    continue
                idx[(qid, scale, cond)] = q
                # also index bare erb id when present
                bare = str(q.get("erb_question_id") or "")
                if bare and bare != qid:
                    idx.setdefault((bare, scale, cond), q)
        break
    _SWEEP_INDEX = idx
    return idx


def _load_manifest_questions() -> dict[str, dict[str, Any]]:
    global _MANIFEST_Q
    if _MANIFEST_Q is not None:
        return _MANIFEST_Q
    out: dict[str, dict[str, Any]] = {}
    for path in (
        PROJECT_ROOT / "data" / "erb_scale_manifest.json",
        Path("/app/data/erb_scale_manifest.json"),
    ):
        if not path.exists():
            continue
        try:
            blob = _load_json(path)
        except Exception:  # noqa: BLE001
            continue
        for q in blob.get("questions") or []:
            eval_id = str(q.get("eval_id") or q.get("question_id") or "")
            if not eval_id:
                continue
            out[eval_id] = q
            bare = str(q.get("erb_question_id") or "")
            qtype = str(q.get("question_type") or "")
            if bare and qtype:
                out.setdefault(f"{bare}::{qtype}", q)
            if bare:
                out.setdefault(bare, q)
        break
    _MANIFEST_Q = out
    return out


def _load_triage_index() -> dict[tuple[str, int, str], dict[str, Any]]:
    global _TRIAGE_INDEX
    if _TRIAGE_INDEX is not None:
        return _TRIAGE_INDEX
    out: dict[tuple[str, int, str], dict[str, Any]] = {}
    pub = _find_published_dir()
    if pub is None:
        _TRIAGE_INDEX = out
        return out
    path = pub / "human_review_queue_openai.csv"
    if not path.exists():
        _TRIAGE_INDEX = out
        return out
    with path.open(encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            qid = (row.get("question_id") or "").strip()
            if not qid:
                continue
            scale = int(row.get("corpus_scale_size") or 0)
            cond = (row.get("condition") or "raw").strip()
            out[(qid, scale, cond)] = {
                "priority": (row.get("priority") or "normal").strip() or "normal",
                "llm_label": (row.get("llm_label") or "").strip() or None,
                "llm_failure_mode": (row.get("llm_failure_mode") or "").strip() or None,
                "llm_issues": (row.get("llm_issues") or "").strip() or None,
                "llm_reasoning": (row.get("llm_reasoning") or "").strip() or None,
            }
    _TRIAGE_INDEX = out
    return out


async def _upsert_sample(
    db: AsyncSession,
    *,
    qid: str,
    scale: int,
    condition: str,
    hit: bool | None,
    rank: int | None,
    doc_rec: float | None,
    expected: list[str],
    retrieved: list[str],
    src: str,
    priority: str | None = None,
) -> None:
    await db.execute(
        text(
            """
            INSERT INTO audit_samples (
                question_id, corpus_scale_size, condition,
                hit_at_10, rank, document_recall,
                expected_doc_ids, retrieved_doc_ids, sample_source, priority
            ) VALUES (
                :qid, :scale, :cond, :hit, :rank, :dr,
                CAST(:exp AS jsonb), CAST(:ret AS jsonb), :src, :pri
            )
            ON CONFLICT (question_id, corpus_scale_size, condition) DO UPDATE SET
                hit_at_10 = COALESCE(EXCLUDED.hit_at_10, audit_samples.hit_at_10),
                rank = COALESCE(EXCLUDED.rank, audit_samples.rank),
                document_recall = COALESCE(EXCLUDED.document_recall, audit_samples.document_recall),
                expected_doc_ids = CASE
                    WHEN jsonb_array_length(EXCLUDED.expected_doc_ids) > 0
                    THEN EXCLUDED.expected_doc_ids ELSE audit_samples.expected_doc_ids END,
                retrieved_doc_ids = CASE
                    WHEN jsonb_array_length(EXCLUDED.retrieved_doc_ids) > 0
                    THEN EXCLUDED.retrieved_doc_ids ELSE audit_samples.retrieved_doc_ids END,
                sample_source = COALESCE(EXCLUDED.sample_source, audit_samples.sample_source),
                priority = COALESCE(EXCLUDED.priority, audit_samples.priority)
            """
        ),
        {
            "qid": qid,
            "scale": scale,
            "cond": condition,
            "hit": hit,
            "rank": rank,
            "dr": doc_rec,
            "exp": json.dumps(expected),
            "ret": json.dumps(retrieved),
            "src": src,
            "pri": priority,
        },
    )


async def _seed_samples_from_csv(db: AsyncSession) -> int:
    pub = _find_published_dir()
    if pub is None:
        return 0
    inserted = 0
    sweep = _load_sweep_index()

    # Legacy worksheets
    for csv_path in sorted(pub.glob("human_audit_n*_raw.csv")):
        with csv_path.open(encoding="utf-8", newline="") as fh:
            reader = csv.DictReader(fh)
            for row in reader:
                qid = (row.get("question_id") or "").strip()
                if not qid:
                    continue
                scale = int(row.get("corpus_scale_size") or 0)
                condition = (row.get("condition") or "raw").strip()
                hit = _parse_hit(row.get("hit_at_10"))
                rank_s = (row.get("rank") or "").strip()
                rank = int(float(rank_s)) if rank_s else None
                dr_s = (row.get("document_recall") or "").strip()
                doc_rec = float(dr_s) if dr_s else None
                expected = _split_ids(row.get("expected_doc_ids"))
                retrieved = _split_ids(row.get("retrieved_doc_ids"))
                await _upsert_sample(
                    db,
                    qid=qid,
                    scale=scale,
                    condition=condition,
                    hit=hit,
                    rank=rank,
                    doc_rec=doc_rec,
                    expected=expected,
                    retrieved=retrieved,
                    src=csv_path.name,
                    priority="normal",
                )
                inserted += 1

    # Primary L4 pack: OpenAI stratified queue (may lack doc IDs — join sweep)
    openai_path = pub / "human_review_queue_openai.csv"
    if openai_path.exists():
        with openai_path.open(encoding="utf-8", newline="") as fh:
            for row in csv.DictReader(fh):
                qid = (row.get("question_id") or "").strip()
                if not qid:
                    continue
                scale = int(row.get("corpus_scale_size") or 0)
                condition = (row.get("condition") or "raw").strip()
                hit = _parse_hit(row.get("hit_at_10"))
                priority = (row.get("priority") or "normal").strip() or "normal"
                expected = _split_ids(row.get("expected_doc_ids"))
                retrieved = _split_ids(row.get("retrieved_doc_ids"))
                rank = None
                doc_rec = None
                sq = sweep.get((qid, scale, condition))
                if sq:
                    if not expected:
                        expected = list(sq.get("expected_doc_ids") or [])
                    if not retrieved:
                        retrieved = list(sq.get("retrieved_doc_ids") or [])
                    if hit is None:
                        hit = bool(sq.get("hit_at_10"))
                    rank = sq.get("rank")
                    doc_rec = sq.get("recall") or sq.get("document_recall")
                await _upsert_sample(
                    db,
                    qid=qid,
                    scale=scale,
                    condition=condition,
                    hit=hit,
                    rank=int(rank) if rank is not None else None,
                    doc_rec=float(doc_rec) if doc_rec is not None else None,
                    expected=expected,
                    retrieved=retrieved,
                    src=openai_path.name,
                    priority=priority,
                )
                inserted += 1

    await db.commit()
    return inserted


async def get_db() -> AsyncSession:
    async with SessionLocal() as session:
        yield session


async def _ensure_paper_checklist(db: AsyncSession) -> None:
    for item in PAPER_CHECKLIST_SEED:
        exists = await db.execute(
            text(
                """
                SELECT 1 FROM study_evaluations
                WHERE eval_scope = 'paper_claim'
                  AND claim_key = :key
                  AND evaluator_kind = 'human'
                  AND auditor_id = '_template'
                LIMIT 1
                """
            ),
            {"key": item["claim_key"]},
        )
        if exists.first():
            continue
        await db.execute(
            text(
                """
                INSERT INTO study_evaluations (
                    eval_scope, claim_key, evaluator_kind, auditor_id,
                    status, checklist_json, notes
                ) VALUES (
                    'paper_claim', :key, 'human', '_template',
                    'pending', CAST(:cj AS jsonb), :notes
                )
                """
            ),
            {
                "key": item["claim_key"],
                "cj": json.dumps(
                    {
                        "title": item["title"],
                        "detail": item["detail"],
                        "category": item["category"],
                    }
                ),
                "notes": item["title"],
            },
        )
    await db.commit()


async def _chunk_texts(db: AsyncSession, doc_ids: list[str]) -> dict[str, dict[str, Any]]:
    """Load chunk text for review UI. Prefer full body so end-of-file facts (due dates) are visible."""
    out: dict[str, dict[str, Any]] = {}
    if not doc_ids:
        return out
    # DB first — full text (LEFT truncates were hiding action-item due dates)
    try:
        from sqlalchemy import bindparam

        stmt = text(
            """
            SELECT doc_id, chunk_text AS preview,
                   source_type, title, scale_rank
            FROM document_chunks
            WHERE doc_id IN :ids
            """
        ).bindparams(bindparam("ids", expanding=True))
        rows = await db.execute(stmt, {"ids": doc_ids})
        for r in rows.mappings():
            out[str(r["doc_id"])] = {
                "doc_id": str(r["doc_id"]),
                "preview": r["preview"] or "",
                "source_type": r["source_type"],
                "title": r["title"],
                "scale_rank": r["scale_rank"],
                "source": "db",
            }
    except Exception:  # noqa: BLE001 — table may be empty / missing cols
        pass

    missing = [d for d in doc_ids if d not in out]
    if not missing:
        return out

    vdir = _find_verify_dir()
    if vdir is None:
        return out
    chunks_path = vdir / "chunks_by_id.json"
    if not chunks_path.exists():
        return out
    try:
        blob = _load_json(chunks_path)
    except Exception:  # noqa: BLE001
        return out
    for did in missing:
        text_val = blob.get(did)
        if text_val:
            out[did] = {
                "doc_id": did,
                "preview": str(text_val),
                "source_type": None,
                "title": None,
                "scale_rank": None,
                "source": "verification_bundle",
            }
    return out


async def _question_meta(db: AsyncSession, question_id: str) -> dict[str, Any]:
    """Resolve question text for bare IDs or eval_id = question_id::question_type."""
    qid = (question_id or "").strip()
    qtype_hint: str | None = None
    bare = qid
    if "::" in qid:
        bare, qtype_hint = qid.split("::", 1)

    def _pack(row: dict[str, Any], forced_type: str | None = None) -> dict[str, Any]:
        text_q = row.get("question_text") or row.get("question") or ""
        return {
            "question_text": text_q,
            "question_type": forced_type or row.get("question_type"),
            "expected_doc_ids": list(row.get("expected_doc_ids") or []),
        }

    # 1) Scale manifest (has eval_id + full text)
    man = _load_manifest_questions()
    for key in (qid, f"{bare}::{qtype_hint}" if qtype_hint else "", bare):
        if key and key in man:
            packed = _pack(man[key], qtype_hint)
            if packed["question_text"]:
                return packed

    # 2) Verification questions.json (may be sparse)
    vdir = _find_verify_dir()
    if vdir and (vdir / "questions.json").exists():
        try:
            qs = _load_json(vdir / "questions.json")
            meta = qs.get(qid) or qs.get(bare) or {}
            if meta and (meta.get("question_text") or meta.get("question")):
                return _pack(meta, qtype_hint)
        except Exception:  # noqa: BLE001
            pass

    # 3) ERB jsonl (questions + extras); match type when present
    paths = (
        PROJECT_ROOT / "data" / "enterprise_rag_bench" / "extra_questions.jsonl",
        PROJECT_ROOT / "data" / "enterprise_rag_bench" / "questions.jsonl",
        Path("/app/data/enterprise_rag_bench/extra_questions.jsonl"),
        Path("/app/data/enterprise_rag_bench/questions.jsonl"),
    )
    fallback: dict[str, Any] | None = None
    for path in paths:
        if not path.exists():
            continue
        with path.open(encoding="utf-8") as fh:
            for line in fh:
                if not line.strip():
                    continue
                row = json.loads(line)
                rid = str(row.get("question_id") or row.get("id") or "")
                rtype = str(row.get("question_type") or "")
                if rid != bare and rid != qid:
                    continue
                if qtype_hint and rtype == qtype_hint:
                    return _pack(row, qtype_hint)
                if fallback is None:
                    fallback = row
    if fallback:
        return _pack(fallback, qtype_hint or fallback.get("question_type"))

    # 4) DB (unused placeholder — keep signature)
    _ = db
    return {"question_text": "", "question_type": qtype_hint, "expected_doc_ids": []}


class LabelBody(BaseModel):
    question_id: str
    corpus_scale_size: int
    condition: str = "raw"
    auditor_id: str = Field(min_length=1, max_length=64)
    label_correct: Literal["y", "n", "unsure"]
    failure_mode: str | None = None
    notes: str | None = None
    status: Literal["pending", "in_progress", "done", "skipped"] = "done"


class ChecklistBody(BaseModel):
    claim_key: str
    auditor_id: str = Field(min_length=1, max_length=64)
    status: Literal["pending", "in_progress", "done", "skipped"] = "done"
    label_correct: Literal["y", "n", "unsure"] | None = None
    notes: str | None = None


class LlmAssistBody(BaseModel):
    question_id: str
    corpus_scale_size: int
    condition: str = "raw"
    auditor_id: str = "llm"


@router.get("/status")
async def audit_status(db: AsyncSession = Depends(get_db)) -> dict:
    await _seed_samples_from_csv(db)
    await _ensure_paper_checklist(db)
    samples = await db.execute(text("SELECT COUNT(*) FROM audit_samples"))
    human_done = await db.execute(
        text(
            """
            SELECT COUNT(*) FROM study_evaluations
            WHERE eval_scope = 'retrieval_row'
              AND evaluator_kind = 'human'
              AND auditor_id <> '_template'
              AND label_correct IS NOT NULL
              AND status = 'done'
            """
        )
    )
    llm_n = await db.execute(
        text(
            """
            SELECT COUNT(*) FROM study_evaluations
            WHERE evaluator_kind = 'llm' AND eval_scope = 'retrieval_row'
            """
        )
    )
    spent = await audit_llm_svc.spent_usd(db)
    return {
        "samples": int(samples.scalar_one() or 0),
        "human_labels_done": int(human_done.scalar_one() or 0),
        "llm_labels": int(llm_n.scalar_one() or 0),
        "llm_budget_usd": audit_llm_svc.BUDGET_USD,
        "llm_spent_usd": round(spent, 6),
        "llm_remaining_usd": round(max(0.0, audit_llm_svc.BUDGET_USD - spent), 6),
        "llm_model": audit_llm_svc.DEFAULT_MODEL,
        "failure_modes": FAILURE_MODES,
        "target_human_labels": 40,
    }


@router.get("/overview")
async def audit_overview(db: AsyncSession = Depends(get_db)) -> dict:
    """Paper-facing numbers, formulas, and progress for the review hub."""
    await _seed_samples_from_csv(db)
    pub = _find_published_dir()
    fit: dict[str, Any] = {}
    sweep_summary: dict[str, Any] = {}
    if pub:
        for name in (
            "erb_full_primary200_to100k_fit.json",
            "erb_primary200_to100k_fit.json",
        ):
            p = pub / name
            if p.exists():
                fit = _load_json(p)
                break
        for name in (
            "erb_full_primary200_to100k.json",
            "erb_primary200_to100k.json",
        ):
            p = pub / name
            if p.exists():
                data = _load_json(p)
                runs = data.get("runs") or []
                sweep_summary = {
                    "n_runs": len(runs),
                    "scales": sorted({r.get("corpus_scale_size") for r in runs if r.get("corpus_scale_size")}),
                    "conditions": sorted({r.get("condition") for r in runs if r.get("condition")}),
                    "source": str(p.name),
                }
                break

    progress = await db.execute(
        text(
            """
            SELECT corpus_scale_size, condition,
                   COUNT(*) AS n_samples,
                   COUNT(*) FILTER (
                     WHERE EXISTS (
                       SELECT 1 FROM study_evaluations e
                       WHERE e.eval_scope = 'retrieval_row'
                         AND e.evaluator_kind = 'human'
                         AND e.auditor_id <> '_template'
                         AND e.question_id = s.question_id
                         AND e.corpus_scale_size = s.corpus_scale_size
                         AND e.condition = s.condition
                         AND e.label_correct IS NOT NULL
                     )
                   ) AS n_labeled
            FROM audit_samples s
            GROUP BY 1, 2
            ORDER BY 1, 2
            """
        )
    )
    by_scale = [dict(r) for r in progress.mappings()]

    auditors = await db.execute(
        text(
            """
            SELECT auditor_id, COUNT(*) AS n
            FROM study_evaluations
            WHERE eval_scope = 'retrieval_row'
              AND evaluator_kind = 'human'
              AND auditor_id <> '_template'
              AND label_correct IS NOT NULL
            GROUP BY 1
            ORDER BY 2 DESC
            """
        )
    )

    failure_counts = await db.execute(
        text(
            """
            SELECT corpus_scale_size, failure_mode, COUNT(*) AS n
            FROM study_evaluations
            WHERE eval_scope = 'retrieval_row'
              AND evaluator_kind = 'human'
              AND failure_mode IS NOT NULL
              AND failure_mode <> ''
            GROUP BY 1, 2
            ORDER BY 1, 3 DESC
            """
        )
    )

    spent = await audit_llm_svc.spent_usd(db)
    return {
        "fit": fit,
        "sweep_summary": sweep_summary,
        "progress_by_scale": by_scale,
        "auditors": [dict(r) for r in auditors.mappings()],
        "failure_mode_counts": [dict(r) for r in failure_counts.mappings()],
        "llm": {
            "budget_usd": audit_llm_svc.BUDGET_USD,
            "spent_usd": round(spent, 6),
            "remaining_usd": round(max(0.0, audit_llm_svc.BUDGET_USD - spent), 6),
            "model": audit_llm_svc.DEFAULT_MODEL,
        },
        "formulas": {
            "hit_at_k": "Hit@k = 1 if ∃ gold doc_id ∈ top-k retrieved IDs else 0",
            "scaling": fit.get("fit_hit_at_10", {}).get("form") or "a - b*log(N)",
            "delta_meta": (fit.get("fit_delta_meta_hit_at_10") or {}).get("form")
            or "c*log(N/N0)",
        },
        "reviewer_guidance": [
            "Confirm Hit@10 is ID set-membership, not free-text answer quality.",
            "Read gold chunk text on every miss and every label_correct=n/unsure.",
            "Assign failure_mode taxonomically; use notes for edge cases.",
            "Second auditor: label an overlapping subset; compare in Export summary.",
            "Paper checklist tab: tick claims, formulas, figures, AI disclosure.",
            "LLM assist is optional; human label is authoritative for L4.",
        ],
    }


@router.get("/queue")
async def audit_queue(
    scale: int | None = None,
    condition: str | None = None,
    auditor_id: str = Query(default="BP"),
    unlabeled_only: bool = False,
    priority: str | None = Query(default=None, description="high|normal or omit for all"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    await _seed_samples_from_csv(db)
    clauses = ["TRUE"]
    params: dict[str, Any] = {"auditor": auditor_id}
    if scale is not None:
        clauses.append("s.corpus_scale_size = :scale")
        params["scale"] = scale
    if condition:
        clauses.append("s.condition = :cond")
        params["cond"] = condition
    if priority:
        clauses.append("COALESCE(s.priority, 'normal') = :pri")
        params["pri"] = priority
    where = " AND ".join(clauses)
    rows = await db.execute(
        text(
            f"""
            SELECT s.question_id, s.corpus_scale_size, s.condition,
                   s.hit_at_10, s.rank, s.document_recall,
                   s.expected_doc_ids, s.retrieved_doc_ids, s.sample_source,
                   COALESCE(s.priority, 'normal') AS priority,
                   e.label_correct, e.failure_mode, e.notes, e.status AS my_status,
                   e.updated_at AS my_updated_at,
                   (
                     SELECT COUNT(*) FROM study_evaluations e2
                     WHERE e2.eval_scope = 'retrieval_row'
                       AND e2.evaluator_kind = 'human'
                       AND e2.auditor_id <> '_template'
                       AND e2.question_id = s.question_id
                       AND e2.corpus_scale_size = s.corpus_scale_size
                       AND e2.condition = s.condition
                       AND e2.label_correct IS NOT NULL
                   ) AS n_human_labels,
                   (
                     SELECT COUNT(*) FROM study_evaluations e3
                     WHERE e3.eval_scope = 'retrieval_row'
                       AND e3.evaluator_kind = 'llm'
                       AND e3.question_id = s.question_id
                       AND e3.corpus_scale_size = s.corpus_scale_size
                       AND e3.condition = s.condition
                   ) AS n_llm_labels
            FROM audit_samples s
            LEFT JOIN study_evaluations e
              ON e.eval_scope = 'retrieval_row'
             AND e.evaluator_kind = 'human'
             AND e.auditor_id = :auditor
             AND e.question_id = s.question_id
             AND e.corpus_scale_size = s.corpus_scale_size
             AND e.condition = s.condition
            WHERE {where}
            ORDER BY
              CASE WHEN COALESCE(s.priority, 'normal') = 'high' THEN 0 ELSE 1 END,
              s.hit_at_10 ASC NULLS FIRST,
              s.corpus_scale_size,
              s.question_id
            """
        ),
        params,
    )
    triage = _load_triage_index()
    items = []
    for r in rows.mappings():
        item = dict(r)
        for k in ("expected_doc_ids", "retrieved_doc_ids"):
            v = item.get(k)
            if isinstance(v, str):
                item[k] = json.loads(v)
        if unlabeled_only and item.get("label_correct"):
            continue
        key = (item["question_id"], int(item["corpus_scale_size"]), item["condition"])
        t = triage.get(key) or {}
        item["llm_label"] = t.get("llm_label")
        item["llm_failure_mode"] = t.get("llm_failure_mode")
        item["llm_reasoning"] = t.get("llm_reasoning")
        items.append(item)
    return {"items": items, "count": len(items), "auditor_id": auditor_id}


@router.get("/item")
async def audit_item(
    question_id: str,
    corpus_scale_size: int,
    condition: str = "raw",
    auditor_id: str = "BP",
    db: AsyncSession = Depends(get_db),
) -> dict:
    await _seed_samples_from_csv(db)
    row = await db.execute(
        text(
            """
            SELECT * FROM audit_samples
            WHERE question_id = :qid AND corpus_scale_size = :scale AND condition = :cond
            LIMIT 1
            """
        ),
        {"qid": question_id, "scale": corpus_scale_size, "cond": condition},
    )
    sample = row.mappings().first()
    if not sample:
        raise HTTPException(404, "sample not in audit queue — seed CSVs under artifacts/published/")
    sample_d = dict(sample)
    for k in ("expected_doc_ids", "retrieved_doc_ids"):
        v = sample_d.get(k)
        if isinstance(v, str):
            sample_d[k] = json.loads(v)

    expected = list(sample_d.get("expected_doc_ids") or [])
    retrieved = list(sample_d.get("retrieved_doc_ids") or [])
    qmeta = await _question_meta(db, question_id)
    if not expected and qmeta.get("expected_doc_ids"):
        expected = list(qmeta["expected_doc_ids"])
        sample_d["expected_doc_ids"] = expected

    id_hit = bool(set(expected) & set(retrieved))
    texts = await _chunk_texts(db, list(dict.fromkeys(expected + retrieved)))

    gold_chunks = []
    for did in expected:
        t = texts.get(did) or {"doc_id": did, "preview": "(text not found)", "source": "missing"}
        gold_chunks.append({**t, "is_gold": True})

    retrieved_chunks = []
    for i, did in enumerate(retrieved, start=1):
        t = texts.get(did) or {"doc_id": did, "preview": "(text not found)", "source": "missing"}
        retrieved_chunks.append(
            {**t, "rank": i, "is_gold": did in set(expected)}
        )

    evals = await db.execute(
        text(
            """
            SELECT evaluator_kind, auditor_id, label_correct, failure_mode, notes,
                   status, relevance_score, reasoning_summary, model, cost_usd,
                   latency_ms, checklist_json, updated_at, created_at
            FROM study_evaluations
            WHERE eval_scope = 'retrieval_row'
              AND question_id = :qid
              AND corpus_scale_size = :scale
              AND condition = :cond
            ORDER BY evaluator_kind, auditor_id
            """
        ),
        {"qid": question_id, "scale": corpus_scale_size, "cond": condition},
    )
    evaluations = []
    my_label = None
    for e in evals.mappings():
        ed = dict(e)
        for ts in ("updated_at", "created_at"):
            if ed.get(ts) is not None:
                ed[ts] = ed[ts].isoformat()
        evaluations.append(ed)
        if e["evaluator_kind"] == "human" and e["auditor_id"] == auditor_id:
            my_label = ed

    triage = _load_triage_index()
    triage_info = triage.get(
        (question_id, int(corpus_scale_size), condition)
    ) or {
        "priority": sample_d.get("priority") or "normal",
        "llm_label": None,
        "llm_failure_mode": None,
        "llm_issues": None,
        "llm_reasoning": None,
    }

    return {
        "sample": sample_d,
        "question_text": qmeta.get("question_text") or "",
        "question_type": qmeta.get("question_type"),
        "id_membership_hit": id_hit,
        "hit_flag_consistent": (bool(sample_d.get("hit_at_10")) == id_hit),
        "gold_chunks": gold_chunks,
        "retrieved_chunks": retrieved_chunks,
        "evaluations": evaluations,
        "my_label": my_label,
        "failure_modes": FAILURE_MODES,
        "auditor_id": auditor_id,
        "triage": triage_info,
        "how_to_decide": [
            "1. Read the question (large text below).",
            "2. Read the GOLD document — does it actually answer the question?",
            "3. Scan RETRIEVED #1–#10 — is the gold doc_id present? (membership = Hit@10).",
            "4. Label y if auto Hit@10 matches what you see; n if wrong; unsure if gold text is bad/noisy.",
            "5. On miss or n: pick a failure mode; add a short note.",
        ],
    }


@router.put("/label")
async def save_label(body: LabelBody, db: AsyncSession = Depends(get_db)) -> dict:
    if body.failure_mode and body.failure_mode not in FAILURE_MODES:
        raise HTTPException(400, f"failure_mode must be one of {FAILURE_MODES}")
    if body.label_correct == "n" and not body.failure_mode:
        # soft require — still allow but warn via response
        pass

    sample = await db.execute(
        text(
            """
            SELECT hit_at_10, rank, document_recall, expected_doc_ids, retrieved_doc_ids
            FROM audit_samples
            WHERE question_id = :qid AND corpus_scale_size = :scale AND condition = :cond
            """
        ),
        {
            "qid": body.question_id,
            "scale": body.corpus_scale_size,
            "cond": body.condition,
        },
    )
    s = sample.mappings().first()
    if not s:
        raise HTTPException(404, "unknown audit sample")

    existing = await db.execute(
        text(
            """
            SELECT id FROM study_evaluations
            WHERE eval_scope = 'retrieval_row'
              AND question_id = :qid
              AND corpus_scale_size = :scale
              AND condition = :cond
              AND evaluator_kind = 'human'
              AND auditor_id = :auditor
            LIMIT 1
            """
        ),
        {
            "qid": body.question_id,
            "scale": body.corpus_scale_size,
            "cond": body.condition,
            "auditor": body.auditor_id,
        },
    )
    row_id = existing.scalar_one_or_none()
    params = {
        "qid": body.question_id,
        "scale": body.corpus_scale_size,
        "cond": body.condition,
        "auditor": body.auditor_id,
        "label": body.label_correct,
        "fm": body.failure_mode,
        "notes": body.notes,
        "status": body.status,
        "hit": s["hit_at_10"],
        "rank": s["rank"],
        "dr": s["document_recall"],
        "exp": json.dumps(s["expected_doc_ids"] if not isinstance(s["expected_doc_ids"], str) else json.loads(s["expected_doc_ids"])),
        "ret": json.dumps(s["retrieved_doc_ids"] if not isinstance(s["retrieved_doc_ids"], str) else json.loads(s["retrieved_doc_ids"])),
    }
    if row_id:
        await db.execute(
            text(
                """
                UPDATE study_evaluations SET
                    label_correct = :label,
                    failure_mode = :fm,
                    notes = :notes,
                    status = :status,
                    hit_at_10 = :hit,
                    rank = :rank,
                    document_recall = :dr,
                    expected_doc_ids = CAST(:exp AS jsonb),
                    retrieved_doc_ids = CAST(:ret AS jsonb),
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = :id
                """
            ),
            {**params, "id": row_id},
        )
    else:
        await db.execute(
            text(
                """
                INSERT INTO study_evaluations (
                    eval_scope, question_id, corpus_scale_size, condition,
                    evaluator_kind, auditor_id, label_correct, failure_mode, notes, status,
                    hit_at_10, rank, document_recall, expected_doc_ids, retrieved_doc_ids
                ) VALUES (
                    'retrieval_row', :qid, :scale, :cond,
                    'human', :auditor, :label, :fm, :notes, :status,
                    :hit, :rank, :dr, CAST(:exp AS jsonb), CAST(:ret AS jsonb)
                )
                """
            ),
            params,
        )
    await db.commit()
    return {"ok": True, "auditor_id": body.auditor_id, "question_id": body.question_id}


@router.post("/llm-assist")
async def llm_assist(body: LlmAssistBody, db: AsyncSession = Depends(get_db)) -> dict:
    detail = await audit_item(
        question_id=body.question_id,
        corpus_scale_size=body.corpus_scale_size,
        condition=body.condition,
        auditor_id=body.auditor_id,
        db=db,
    )
    payload = {
        "question_id": body.question_id,
        "corpus_scale_size": body.corpus_scale_size,
        "condition": body.condition,
        "hit_at_10": detail["sample"].get("hit_at_10"),
        "expected_doc_ids": detail["sample"].get("expected_doc_ids"),
        "retrieved_doc_ids": detail["sample"].get("retrieved_doc_ids"),
        "question_text": detail.get("question_text"),
        "gold_chunks": [
            {"doc_id": c["doc_id"], "preview": (c.get("preview") or "")[:1500]}
            for c in detail.get("gold_chunks") or []
        ],
        "retrieved_chunks": [
            {
                "rank": c.get("rank"),
                "doc_id": c["doc_id"],
                "is_gold": c.get("is_gold"),
                "preview": (c.get("preview") or "")[:1200],
            }
            for c in (detail.get("retrieved_chunks") or [])[:10]
        ],
    }
    try:
        result = await audit_llm_svc.run_audit_llm(db, payload)
    except RuntimeError as exc:
        raise HTTPException(402, str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(500, f"LLM assist failed: {exc}") from exc

    auditor = f"llm:{result['model']}"
    existing = await db.execute(
        text(
            """
            SELECT id FROM study_evaluations
            WHERE eval_scope = 'retrieval_row'
              AND question_id = :qid
              AND corpus_scale_size = :scale
              AND condition = :cond
              AND evaluator_kind = 'llm'
              AND auditor_id = :auditor
            LIMIT 1
            """
        ),
        {
            "qid": body.question_id,
            "scale": body.corpus_scale_size,
            "cond": body.condition,
            "auditor": auditor,
        },
    )
    row_id = existing.scalar_one_or_none()
    params = {
        "qid": body.question_id,
        "scale": body.corpus_scale_size,
        "cond": body.condition,
        "auditor": auditor,
        "label": result.get("label_correct"),
        "fm": result.get("failure_mode"),
        "notes": None,
        "hit": detail["sample"].get("hit_at_10"),
        "rank": detail["sample"].get("rank"),
        "dr": detail["sample"].get("document_recall"),
        "exp": json.dumps(detail["sample"].get("expected_doc_ids") or []),
        "ret": json.dumps(detail["sample"].get("retrieved_doc_ids") or []),
        "rel": result.get("relevance_score"),
        "reason": result.get("reasoning_summary"),
        "model": result.get("model"),
        "pv": result.get("prompt_version"),
        "lat": result.get("latency_ms"),
        "cost": result.get("cost_usd"),
        "inp": result.get("input_tokens"),
        "out": result.get("output_tokens"),
        "cj": json.dumps(result.get("checklist_json") or {}),
    }
    if row_id:
        await db.execute(
            text(
                """
                UPDATE study_evaluations SET
                    label_correct = :label, failure_mode = :fm, status = 'done',
                    relevance_score = :rel, reasoning_summary = :reason,
                    model = :model, prompt_version = :pv, latency_ms = :lat,
                    cost_usd = :cost, input_tokens = :inp, output_tokens = :out,
                    checklist_json = CAST(:cj AS jsonb),
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = :id
                """
            ),
            {**params, "id": row_id},
        )
    else:
        await db.execute(
            text(
                """
                INSERT INTO study_evaluations (
                    eval_scope, question_id, corpus_scale_size, condition,
                    evaluator_kind, auditor_id, label_correct, failure_mode, status,
                    hit_at_10, rank, document_recall, expected_doc_ids, retrieved_doc_ids,
                    relevance_score, reasoning_summary, model, prompt_version,
                    latency_ms, cost_usd, input_tokens, output_tokens, checklist_json
                ) VALUES (
                    'retrieval_row', :qid, :scale, :cond,
                    'llm', :auditor, :label, :fm, 'done',
                    :hit, :rank, :dr, CAST(:exp AS jsonb), CAST(:ret AS jsonb),
                    :rel, :reason, :model, :pv, :lat, :cost, :inp, :out, CAST(:cj AS jsonb)
                )
                """
            ),
            params,
        )
    await db.commit()
    return {"ok": True, "result": result, "stored_as": auditor}


@router.get("/checklist")
async def get_checklist(
    auditor_id: str = "BP",
    db: AsyncSession = Depends(get_db),
) -> dict:
    await _ensure_paper_checklist(db)
    templates = await db.execute(
        text(
            """
            SELECT claim_key, checklist_json, notes
            FROM study_evaluations
            WHERE eval_scope = 'paper_claim' AND auditor_id = '_template'
            ORDER BY claim_key
            """
        )
    )
    mine = await db.execute(
        text(
            """
            SELECT claim_key, status, label_correct, notes, updated_at
            FROM study_evaluations
            WHERE eval_scope = 'paper_claim'
              AND evaluator_kind = 'human'
              AND auditor_id = :auditor
            """
        ),
        {"auditor": auditor_id},
    )
    by_me = {r["claim_key"]: dict(r) for r in mine.mappings()}
    items = []
    for t in templates.mappings():
        cj = t["checklist_json"] or {}
        if isinstance(cj, str):
            cj = json.loads(cj)
        me = by_me.get(t["claim_key"]) or {}
        items.append(
            {
                "claim_key": t["claim_key"],
                "title": cj.get("title") or t["notes"],
                "detail": cj.get("detail"),
                "category": cj.get("category"),
                "status": me.get("status") or "pending",
                "label_correct": me.get("label_correct"),
                "notes": me.get("notes"),
                "updated_at": me["updated_at"].isoformat() if me.get("updated_at") else None,
            }
        )
    return {"items": items, "auditor_id": auditor_id}


@router.put("/checklist")
async def save_checklist(body: ChecklistBody, db: AsyncSession = Depends(get_db)) -> dict:
    await _ensure_paper_checklist(db)
    existing = await db.execute(
        text(
            """
            SELECT id FROM study_evaluations
            WHERE eval_scope = 'paper_claim'
              AND claim_key = :key
              AND evaluator_kind = 'human'
              AND auditor_id = :auditor
            LIMIT 1
            """
        ),
        {"key": body.claim_key, "auditor": body.auditor_id},
    )
    row_id = existing.scalar_one_or_none()
    if row_id:
        await db.execute(
            text(
                """
                UPDATE study_evaluations SET
                    status = :status, label_correct = :label, notes = :notes,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = :id
                """
            ),
            {
                "id": row_id,
                "status": body.status,
                "label": body.label_correct,
                "notes": body.notes,
            },
        )
    else:
        tpl = await db.execute(
            text(
                """
                SELECT checklist_json FROM study_evaluations
                WHERE eval_scope = 'paper_claim' AND claim_key = :key
                  AND auditor_id = '_template' LIMIT 1
                """
            ),
            {"key": body.claim_key},
        )
        cj = tpl.scalar_one_or_none()
        await db.execute(
            text(
                """
                INSERT INTO study_evaluations (
                    eval_scope, claim_key, evaluator_kind, auditor_id,
                    status, label_correct, notes, checklist_json
                ) VALUES (
                    'paper_claim', :key, 'human', :auditor,
                    :status, :label, :notes, CAST(:cj AS jsonb)
                )
                """
            ),
            {
                "key": body.claim_key,
                "auditor": body.auditor_id,
                "status": body.status,
                "label": body.label_correct,
                "notes": body.notes,
                "cj": json.dumps(cj if isinstance(cj, dict) else (json.loads(cj) if isinstance(cj, str) else {})),
            },
        )
    await db.commit()
    return {"ok": True}


@router.get("/llm-report")
async def llm_report(db: AsyncSession = Depends(get_db)) -> dict:
    """Serve latest batch LLM audit report (file + DB summary)."""
    report: dict[str, Any] = {}
    # Prefer the OpenAI wide audit cited in the paper; llm_audit_report.json is the legacy batch output.
    candidates = [
        base / name
        for base in (PROJECT_ROOT / "artifacts" / "published", Path("/app/artifacts/published"))
        for name in ("llm_audit_report_openai.json", "llm_audit_report.json")
    ]
    for path in candidates:
        if path.exists():
            report = _load_json(path)
            report["_source_file"] = str(path)
            break

    llm_rows = await db.execute(
        text(
            """
            SELECT question_id, corpus_scale_size, condition, label_correct, failure_mode,
                   reasoning_summary, relevance_score, cost_usd, model, checklist_json, updated_at
            FROM study_evaluations
            WHERE eval_scope = 'retrieval_row' AND evaluator_kind = 'llm'
            ORDER BY corpus_scale_size, question_id
            """
        )
    )
    db_items = []
    for r in llm_rows.mappings():
        d = dict(r)
        if d.get("updated_at") is not None:
            d["updated_at"] = d["updated_at"].isoformat()
        if d.get("cost_usd") is not None:
            d["cost_usd"] = float(d["cost_usd"])
        db_items.append(d)

    spent = await audit_llm_svc.spent_usd(db)
    return {
        "file_report": report or None,
        "db_llm_rows": db_items,
        "db_llm_count": len(db_items),
        "llm_budget_usd": audit_llm_svc.BUDGET_USD,
        "llm_spent_usd": round(spent, 6),
        "llm_model": audit_llm_svc.DEFAULT_MODEL,
    }


@router.get("/export")
async def export_audit(
    format: Literal["csv", "json", "markdown"] = "csv",
    db: AsyncSession = Depends(get_db),
) -> Any:
    rows = await db.execute(
        text(
            """
            SELECT s.question_id, s.corpus_scale_size, s.condition,
                   s.hit_at_10, s.rank, s.document_recall,
                   s.expected_doc_ids, s.retrieved_doc_ids,
                   e.evaluator_kind, e.auditor_id, e.label_correct, e.failure_mode,
                   e.notes, e.status, e.relevance_score, e.reasoning_summary,
                   e.model, e.cost_usd, e.updated_at
            FROM audit_samples s
            LEFT JOIN study_evaluations e
              ON e.eval_scope = 'retrieval_row'
             AND e.question_id = s.question_id
             AND e.corpus_scale_size = s.corpus_scale_size
             AND e.condition = s.condition
             AND e.auditor_id <> '_template'
            ORDER BY s.corpus_scale_size, s.question_id, e.evaluator_kind, e.auditor_id
            """
        )
    )
    records = []
    for r in rows.mappings():
        d = dict(r)
        for k in ("expected_doc_ids", "retrieved_doc_ids"):
            v = d.get(k)
            if isinstance(v, list):
                d[k] = "|".join(str(x) for x in v)
            elif v is not None and not isinstance(v, str):
                d[k] = json.dumps(v)
        if d.get("updated_at") is not None:
            d["updated_at"] = d["updated_at"].isoformat()
        if d.get("cost_usd") is not None:
            d["cost_usd"] = float(d["cost_usd"])
        records.append(d)

    human = [r for r in records if r.get("evaluator_kind") == "human" and r.get("label_correct")]
    summary = {
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "n_evaluation_rows": len(records),
        "n_human_labels": len(human),
        "by_scale_failure_modes": {},
        "agreement_note": "Compare overlapping auditor_id pairs manually from CSV.",
    }
    for r in human:
        scale = str(r.get("corpus_scale_size"))
        fm = r.get("failure_mode") or "(none)"
        summary["by_scale_failure_modes"].setdefault(scale, {})
        summary["by_scale_failure_modes"][scale][fm] = (
            summary["by_scale_failure_modes"][scale].get(fm, 0) + 1
        )

    confirmed = sum(1 for r in human if r.get("label_correct") == "y")
    paper_blurb = (
        f"On a stratified audit of {len(human)} labeled retrieval rows "
        f"({confirmed}/{len(human)} confirmed automated Hit@10 labels as fair). "
        f"Failure-mode counts by scale: {json.dumps(summary['by_scale_failure_modes'])}."
    )
    summary["paper_paragraph_draft"] = paper_blurb

    if format == "json":
        return {"summary": summary, "rows": records}

    if format == "markdown":
        md = [
            "# L4 Human Audit Export",
            "",
            f"_Exported {summary['exported_at']}_",
            "",
            "## Draft paper paragraph",
            "",
            paper_blurb,
            "",
            "## Failure modes by scale",
            "",
            "```json",
            json.dumps(summary["by_scale_failure_modes"], indent=2),
            "```",
            "",
            f"Human labels: **{len(human)}** | Evaluation rows (human+llm): **{len(records)}**",
            "",
        ]
        return PlainTextResponse("\n".join(md), media_type="text/markdown")

    buf = io.StringIO()
    fields = [
        "question_id",
        "corpus_scale_size",
        "condition",
        "hit_at_10",
        "rank",
        "document_recall",
        "expected_doc_ids",
        "retrieved_doc_ids",
        "evaluator_kind",
        "auditor_id",
        "label_correct",
        "failure_mode",
        "notes",
        "status",
        "relevance_score",
        "reasoning_summary",
        "model",
        "cost_usd",
        "updated_at",
    ]
    w = csv.DictWriter(buf, fieldnames=fields, extrasaction="ignore")
    w.writeheader()
    for r in records:
        w.writerow(r)
    data = buf.getvalue().encode("utf-8")
    return StreamingResponse(
        iter([data]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=human_audit_labeled_export.csv"},
    )
