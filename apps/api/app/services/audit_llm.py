"""Budget-capped LLM auditor for L4 (pipeline + chunk + Hit@10 fairness).

Model choice: gpt-4o (reasoning). Cursor "Luna" is not an OpenAI API model in this
stack — use AUDIT_LLM_BASE_URL only if you have an OpenAI-compatible Luna endpoint.
gpt-4o-mini is reserved for L3 relevance; L4 needs stronger reasoning on text+IDs.
"""

from __future__ import annotations

import json
import os
import time
from typing import Any

# gpt-4o list prices USD / 1M tokens
PRICE_IN = float(os.environ.get("AUDIT_LLM_PRICE_IN_PER_1M", "2.50"))
PRICE_OUT = float(os.environ.get("AUDIT_LLM_PRICE_OUT_PER_1M", "10.00"))
BUDGET_USD = float(os.environ.get("AUDIT_LLM_BUDGET_USD", "2.0"))
DEFAULT_MODEL = os.environ.get("AUDIT_LLM_MODEL", "gpt-4o")
PROMPT_VERSION = "audit-v2-pipeline"


def estimate_cost(input_tokens: int, output_tokens: int) -> float:
    return round(
        input_tokens / 1_000_000.0 * PRICE_IN + output_tokens / 1_000_000.0 * PRICE_OUT,
        6,
    )


async def spent_usd(db: Any) -> float:
    from sqlalchemy import text

    row = await db.execute(text("SELECT COALESCE(SUM(cost_usd), 0) FROM audit_cost_ledger"))
    return float(row.scalar_one() or 0.0)


async def remaining_usd(db: Any) -> float:
    return max(0.0, BUDGET_USD - await spent_usd(db))


async def assert_budget(db: Any, estimated: float = 0.05) -> None:
    rem = await remaining_usd(db)
    if rem < estimated:
        raise RuntimeError(
            f"Audit LLM budget exhausted or too low "
            f"(remaining=${rem:.4f}, need≈${estimated:.4f}, cap=${BUDGET_USD:.2f})"
        )


async def record_cost(
    db: Any,
    *,
    model: str,
    input_tokens: int,
    output_tokens: int,
    cost_usd: float,
    note: str = "",
) -> None:
    from sqlalchemy import text

    await db.execute(
        text(
            """
            INSERT INTO audit_cost_ledger (kind, model, input_tokens, output_tokens, cost_usd, note)
            VALUES ('audit_llm', :model, :inp, :out, :cost, :note)
            """
        ),
        {
            "model": model,
            "inp": int(input_tokens),
            "out": int(output_tokens),
            "cost": float(cost_usd),
            "note": note,
        },
    )


def programmatic_checks(payload: dict[str, Any]) -> dict[str, Any]:
    """Free deterministic checks before / alongside LLM."""
    expected = [str(x) for x in (payload.get("expected_doc_ids") or []) if x]
    retrieved = [str(x) for x in (payload.get("retrieved_doc_ids") or []) if x]
    hit_auto = bool(payload.get("hit_at_10"))
    membership = bool(set(expected) & set(retrieved))
    gold_chunks = payload.get("gold_chunks") or []
    ret_chunks = payload.get("retrieved_chunks") or []
    empty_gold = [
        c.get("doc_id")
        for c in gold_chunks
        if not (c.get("preview") or "").strip() or c.get("source") == "missing"
    ]
    empty_ret = [
        c.get("doc_id")
        for c in ret_chunks
        if not (c.get("preview") or "").strip() or c.get("source") == "missing"
    ]
    issues: list[str] = []
    if membership != hit_auto:
        issues.append("hit_flag_inconsistent_with_id_membership")
    if not expected:
        issues.append("missing_expected_doc_ids")
    if not retrieved:
        issues.append("missing_retrieved_doc_ids")
    if empty_gold:
        issues.append("empty_or_missing_gold_chunk_text")
    if len(empty_ret) >= 5:
        issues.append("many_missing_retrieved_chunk_texts")
    if payload.get("question_text") in (None, ""):
        issues.append("missing_question_text")
    return {
        "id_membership_hit": membership,
        "hit_flag_consistent": membership == hit_auto,
        "empty_gold_doc_ids": empty_gold,
        "empty_retrieved_doc_ids": empty_ret[:10],
        "programmatic_issues": issues,
    }


def build_prompt(payload: dict[str, Any], prog: dict[str, Any]) -> str:
    gold_snips = payload.get("gold_chunks") or []
    ret_snips = payload.get("retrieved_chunks") or []
    return f"""You are the L4 auditor for an IEEE Access paper on vector retrieval drift (EnterpriseRAG-Bench).

Evaluate this ONE retrieval row end-to-end. Priorities:
1) Hit@10 correctness: Hit@10=True iff ANY expected_doc_id is in top-10 retrieved IDs (set membership), NOT answer quality.
2) Chunk quality: are gold/retrieved bodies non-empty and on-topic for the question?
3) Failure taxonomy on misses / bad labels.
4) Flag pipeline discrepancies (wrong gold, mangled IDs, empty text, hit flag vs membership mismatch).

Programmatic pre-checks (trust but verify): {json.dumps(prog)}

Return STRICT JSON:
{{
  "label_correct": "y"|"n"|"unsure",
  "failure_mode": "embedding_near_miss"|"lexical_mismatch"|"multi_gold_partial"|"metadata_needed"|"label_noise"|"other"|null,
  "relevance_score": 0-3,
  "chunk_quality_score": 0-3,
  "id_membership_ok": boolean,
  "pipeline_issues": ["short_code", ...],
  "severity_flags": ["short_code", ...],
  "reasoning_summary": "<=100 words"
}}

question_id: {payload.get("question_id")}
corpus_scale_size: {payload.get("corpus_scale_size")}
condition: {payload.get("condition")}
hit_at_10_auto: {payload.get("hit_at_10")}
expected_doc_ids: {json.dumps(payload.get("expected_doc_ids") or [])}
retrieved_doc_ids: {json.dumps(payload.get("retrieved_doc_ids") or [])}
question_text: {payload.get("question_text") or ""}

GOLD CHUNKS (truncated):
{json.dumps(gold_snips, ensure_ascii=False)[:5000]}

RETRIEVED CHUNKS (rank order, truncated):
{json.dumps(ret_snips, ensure_ascii=False)[:6500]}
"""


async def run_audit_llm(db: Any, payload: dict[str, Any]) -> dict[str, Any]:
    from openai import OpenAI

    from app.config import resolve_openai_api_key, settings

    prog = programmatic_checks(payload)
    await assert_budget(db, estimated=0.03)
    model = os.environ.get("AUDIT_LLM_MODEL", DEFAULT_MODEL)
    base_url = os.environ.get("AUDIT_LLM_BASE_URL", "").strip() or None
    api_key = resolve_openai_api_key() or settings.openai_api_key
    if not api_key or api_key.startswith("sk-your"):
        raise RuntimeError("OPENAI_API_KEY missing for audit LLM")

    client_kwargs: dict[str, Any] = {"api_key": api_key}
    if base_url:
        client_kwargs["base_url"] = base_url
    client = OpenAI(**client_kwargs)

    prompt = build_prompt(payload, prog)
    t0 = time.perf_counter()
    messages = [
        {
            "role": "system",
            "content": (
                "You are a careful IR + RAG evaluation auditor. "
                "Be skeptical of empty chunks and inconsistent Hit flags. JSON only."
            ),
        },
        {"role": "user", "content": prompt},
    ]
    create_kwargs: dict[str, Any] = {
        "model": model,
        "temperature": 0.1,
        "messages": messages,
    }
    # Some local models reject response_format
    if not os.environ.get("AUDIT_LLM_BASE_URL"):
        create_kwargs["response_format"] = {"type": "json_object"}
    try:
        resp = client.chat.completions.create(**create_kwargs)
    except Exception:
        create_kwargs.pop("response_format", None)
        resp = client.chat.completions.create(**create_kwargs)
    latency_ms = int((time.perf_counter() - t0) * 1000)
    content = (resp.choices[0].message.content or "{}").strip()
    usage = resp.usage
    inp = int(getattr(usage, "prompt_tokens", 0) or 0)
    out = int(getattr(usage, "completion_tokens", 0) or 0)
    cost = estimate_cost(inp, out)
    await assert_budget(db, estimated=cost)
    await record_cost(
        db,
        model=model,
        input_tokens=inp,
        output_tokens=out,
        cost_usd=cost,
        note=f"{payload.get('question_id')}@{payload.get('corpus_scale_size')}",
    )

    try:
        parsed = json.loads(content)
    except json.JSONDecodeError:
        parsed = {
            "label_correct": "unsure",
            "failure_mode": "other",
            "relevance_score": None,
            "chunk_quality_score": None,
            "reasoning_summary": content[:500],
            "id_membership_ok": prog.get("hit_flag_consistent"),
            "pipeline_issues": ["json_parse_error"],
            "severity_flags": [],
        }

    # Prefer programmatic membership when LLM is silent
    if parsed.get("id_membership_ok") is None:
        parsed["id_membership_ok"] = prog.get("hit_flag_consistent")

    issues = list(prog.get("programmatic_issues") or [])
    for x in parsed.get("pipeline_issues") or []:
        if x and x not in issues:
            issues.append(x)
    for x in parsed.get("severity_flags") or []:
        if x and x not in issues:
            issues.append(f"disc:{x}")

    return {
        "model": model,
        "prompt_version": PROMPT_VERSION,
        "latency_ms": latency_ms,
        "cost_usd": cost,
        "input_tokens": inp,
        "output_tokens": out,
        "label_correct": parsed.get("label_correct"),
        "failure_mode": parsed.get("failure_mode"),
        "relevance_score": parsed.get("relevance_score"),
        "reasoning_summary": parsed.get("reasoning_summary"),
        "checklist_json": {
            "id_membership_ok": parsed.get("id_membership_ok"),
            "chunk_quality_score": parsed.get("chunk_quality_score"),
            "pipeline_issues": issues,
            "programmatic": prog,
            "raw": parsed,
        },
        "budget_remaining_usd": await remaining_usd(db),
    }
