#!/usr/bin/env python3
"""L4 Hit@10-fairness audit via OpenAI (gpt-4o) — transparent paper secondary layer.

Evaluates the 62 high-priority rows from human_review_queue_openai.csv using:
  - full gold document text from ERB .txt files
  - retrieved top-10 IDs + truncated previews
  - clear rules: agree with Hit@10 when ID membership matches; label_noise when HIT but gold cannot answer

This script uses OPENAI_API_KEY +
AUDIT_LLM_MODEL (default gpt-4o). Optional AUDIT_LLM_BASE_URL for OpenAI-compatible proxies.

Outputs (does not require Postgres):
  artifacts/published/l4_hit_fairness_llm.json
  artifacts/published/l4_hit_fairness_llm.md
  artifacts/published/l4_hit_fairness_llm.csv

Usage:
  python scripts/erb/run_l4_hit_fairness_llm.py
  python scripts/erb/run_l4_hit_fairness_llm.py --limit 3
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import ssl
import sys
import time
import urllib.error
import urllib.request
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
PUB = ROOT / "artifacts" / "published"
DOCS_DIR = ROOT / "data" / "enterprise_rag_bench" / "documents"
MANIFEST = ROOT / "data" / "erb_scale_manifest.json"
SWEEP = PUB / "erb_full_primary200_to100k.json"
QUEUE = PUB / "human_review_queue_openai.csv"
VERIFY_CHUNKS = ROOT / "artifacts" / "verification" / "chunks_by_id.json"

PROMPT_VERSION = "l4-hit-fairness-v1"
DEFAULT_MODEL = "gpt-4o"
PRICE_IN = 2.50
PRICE_OUT = 10.00


def _load_env() -> None:
    for env_path in (ROOT / ".env", Path("/app/.env")):
        if not env_path.exists():
            continue
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
        break


def _ssl_ctx() -> ssl.SSLContext:
    try:
        sys.path.insert(0, str(ROOT / "apps" / "api"))
        from app.ssl_bundle import apply_corporate_ssl_bundle

        bundle = apply_corporate_ssl_bundle()
        if bundle:
            return ssl.create_default_context(cafile=bundle)
    except Exception:
        pass
    return ssl.create_default_context()


def estimate_cost(inp: int, out: int) -> float:
    return round(inp / 1e6 * PRICE_IN + out / 1e6 * PRICE_OUT, 6)


def resolve_doc_path(path_str: str) -> Path | None:
    p = Path(path_str)
    if p.is_file():
        return p
    c = DOCS_DIR / Path(path_str).name
    return c if c.is_file() else None


def load_gold_text(doc_id: str, doc_by_id: dict[str, Any], fallback: dict[str, str]) -> str:
    doc = doc_by_id.get(doc_id)
    if doc:
        p = resolve_doc_path(doc.get("path") or "")
        if p:
            return p.read_text(encoding="utf-8", errors="replace")
    return fallback.get(doc_id) or f"(missing text for {doc_id})"


def clip(s: str, n: int) -> str:
    s = s or ""
    return s if len(s) <= n else s[:n] + "\n…[truncated]"


SYSTEM = """You are an L4 auditor for an IEEE Access study on vector retrieval drift.

PRIMARY PAPER METRIC (L1) — already computed, do not recompute search:
  Hit@10 = true iff gold doc_id appears in retrieved top-10 IDs.

YOUR JOB — judge whether auto Hit@10 is FAIR, and whether gold TEXT answers the question.

Rules (strict):
1) If auto_hit_at_10 matches gold_id_in_top10 (both true or both false) → membership is consistent.
2) human_label_correct = "y" when Hit@10 membership is consistent AND:
   - If HIT: gold text reasonably answers / supports the question (fact present in full gold), OR
   - If MISS: gold may or may not answer; MISS flag itself is still fair because ID not in top-10.
3) human_label_correct = "n" mainly when:
   - HIT but full gold text does NOT answer the question → failure_mode=label_noise
   - Hit flag inconsistent with IDs → failure_mode=other (note inconsistency)
4) Do NOT set "n" merely because a good gold doc was not retrieved (that is a true MISS for drift).
5) Read the FULL gold document; answers may appear only at the end (action items / due dates).
6) Retrieved previews are truncated; use them only as context, not to invent gold facts.

Return ONLY one JSON object:
{
  "human_label_correct": "y"|"n"|"unsure",
  "human_failure_mode": null|"label_noise"|"embedding_near_miss"|"semantic_near_miss"|"lexical_mismatch"|"wrong_source_type"|"stale_gold"|"chunk_too_thin"|"multi_gold_partial"|"metadata_needed"|"other",
  "gold_answers_question": true|false,
  "answer_span": "≤240 char quote from gold or null",
  "human_notes": "one sentence"
}
"""


def build_user_payload(row: dict[str, Any]) -> str:
    parts = [
        f"row_id: {row['row_id']}",
        f"question_id: {row['question_id']}",
        f"N={row['corpus_scale_size']} condition={row['condition']}",
        f"auto_hit_at_10: {row['auto_hit_at_10']} ({'HIT' if row['auto_hit_at_10'] else 'MISS'})",
        f"gold_id_in_top10: {row['gold_id_in_top10']}",
        f"gold_rank: {row.get('gold_rank')}",
        "",
        "QUESTION:",
        row["question"],
        "",
        "GOLD DOCUMENT(S) — FULL TEXT:",
    ]
    for g in row["gold_docs"]:
        parts += [f"### {g['doc_id']}", g["text"], ""]
    parts.append("RETRIEVED TOP-10 (★ = gold id):")
    for r in row["retrieved"]:
        star = " ★GOLD" if r["is_gold"] else ""
        parts.append(f"#{r['rank']} {r['doc_id']}{star} title={r.get('title') or ''}")
        parts.append(clip(r.get("preview") or "", 900))
        parts.append("")
    parts.append("Respond with the JSON object only.")
    return "\n".join(parts)


def call_openai(model: str, user: str, base_url: str | None) -> dict[str, Any]:
    api_key = os.environ.get("OPENAI_API_KEY") or ""
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY missing")
    url = (base_url.rstrip("/") if base_url else "https://api.openai.com/v1") + "/chat/completions"
    body = {
        "model": model,
        "temperature": 0,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": user},
        ],
    }
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )
    ctx = _ssl_ctx()
    last_err: Exception | None = None
    for attempt in range(6):
        try:
            with urllib.request.urlopen(req, context=ctx, timeout=180) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
            usage = payload.get("usage") or {}
            content = payload["choices"][0]["message"]["content"]
            parsed = json.loads(content)
            return {
                "parsed": parsed,
                "input_tokens": int(usage.get("prompt_tokens") or 0),
                "output_tokens": int(usage.get("completion_tokens") or 0),
                "raw": content,
            }
        except urllib.error.HTTPError as exc:
            last_err = exc
            if exc.code in (429, 500, 502, 503) and attempt < 5:
                time.sleep(2 ** attempt)
                continue
            raise
        except Exception as exc:  # noqa: BLE001
            last_err = exc
            if attempt < 5:
                time.sleep(2 ** attempt)
                continue
            raise
    raise RuntimeError(last_err)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--priority", default="high", choices=["high", "all"])
    parser.add_argument("--budget-usd", type=float, default=float(os.environ.get("L4_FAIRNESS_BUDGET_USD", "5.0")))
    parser.add_argument("--sleep", type=float, default=0.4)
    args = parser.parse_args()
    _load_env()

    model = os.environ.get("AUDIT_LLM_MODEL", DEFAULT_MODEL)
    base_url = os.environ.get("AUDIT_LLM_BASE_URL", "").strip() or None

    man = json.loads(MANIFEST.read_text(encoding="utf-8"))
    qmeta = {(q.get("eval_id") or q.get("question_id")): q for q in man["questions"]}
    doc_by_id = {d["doc_id"]: d for d in man["documents"]}
    fallback = {}
    if VERIFY_CHUNKS.exists():
        fallback = json.loads(VERIFY_CHUNKS.read_text(encoding="utf-8"))

    sweep = json.loads(SWEEP.read_text(encoding="utf-8"))
    sidx: dict[tuple[str, int, str], dict[str, Any]] = {}
    for run in sweep["runs"]:
        scale = int(run["corpus_scale_size"])
        cond = run["condition"]
        for pq in run["per_question"]:
            sidx[(pq["question_id"], scale, cond)] = pq

    queue_rows = list(csv.DictReader(QUEUE.open(encoding="utf-8")))
    if args.priority == "high":
        queue_rows = [r for r in queue_rows if (r.get("priority") or "") == "high"]
    if args.limit and args.limit > 0:
        queue_rows = queue_rows[: args.limit]

    work: list[dict[str, Any]] = []
    for i, r in enumerate(queue_rows, 1):
        qid = r["question_id"]
        scale = int(r["corpus_scale_size"])
        cond = r["condition"]
        pq = sidx.get((qid, scale, cond))
        qm = qmeta.get(qid) or {}
        expected = list((pq or {}).get("expected_doc_ids") or qm.get("expected_doc_ids") or [])
        retrieved = list((pq or {}).get("retrieved_doc_ids") or [])
        hit = bool(pq.get("hit_at_10")) if pq is not None else str(r.get("hit_at_10")).lower() == "true"
        id_hit = bool(set(expected) & set(retrieved))
        gold_docs = [
            {"doc_id": did, "text": load_gold_text(did, doc_by_id, fallback)} for did in expected
        ]
        ret_rows = []
        for rank, did in enumerate(retrieved, 1):
            preview = fallback.get(did) or ""
            if not preview:
                p = resolve_doc_path((doc_by_id.get(did) or {}).get("path") or "")
                if p:
                    preview = p.read_text(encoding="utf-8", errors="replace")
            ret_rows.append(
                {
                    "rank": rank,
                    "doc_id": did,
                    "is_gold": did in set(expected),
                    "title": (doc_by_id.get(did) or {}).get("title"),
                    "preview": clip(preview, 1200),
                }
            )
        work.append(
            {
                "row_id": i,
                "question_id": qid,
                "corpus_scale_size": scale,
                "condition": cond,
                "question": qm.get("question") or "",
                "auto_hit_at_10": hit,
                "gold_id_in_top10": id_hit,
                "gold_rank": (pq or {}).get("rank"),
                "gold_docs": gold_docs,
                "retrieved": ret_rows,
            }
        )

    results: list[dict[str, Any]] = []
    spent = 0.0
    print(
        f"L4 fairness audit model={model} rows={len(work)} budget=${args.budget_usd} "
        f"base_url={base_url or 'api.openai.com'} prompt={PROMPT_VERSION}",
        flush=True,
    )

    for row in work:
        est = 0.08
        if spent + est > args.budget_usd:
            print(f"BUDGET STOP spent=${spent:.4f} cap=${args.budget_usd}", flush=True)
            break
        user = build_user_payload(row)
        t0 = time.time()
        try:
            out = call_openai(model, user, base_url)
            cost = estimate_cost(out["input_tokens"], out["output_tokens"])
            spent += cost
            parsed = out["parsed"]
            label = parsed.get("human_label_correct")
            if label not in ("y", "n", "unsure"):
                label = "unsure"
            fm = parsed.get("human_failure_mode")
            if fm == "":
                fm = None
            rec = {
                "row_id": row["row_id"],
                "question_id": row["question_id"],
                "corpus_scale_size": row["corpus_scale_size"],
                "condition": row["condition"],
                "auto_hit_at_10": row["auto_hit_at_10"],
                "gold_id_in_top10": row["gold_id_in_top10"],
                "gold_answers_question": parsed.get("gold_answers_question"),
                "human_label_correct": label,
                "human_failure_mode": fm,
                "answer_span": parsed.get("answer_span"),
                "human_notes": parsed.get("human_notes"),
                "model": model,
                "prompt_version": PROMPT_VERSION,
                "cost_usd": cost,
                "input_tokens": out["input_tokens"],
                "output_tokens": out["output_tokens"],
                "latency_s": round(time.time() - t0, 2),
            }
        except Exception as exc:  # noqa: BLE001
            rec = {
                "row_id": row["row_id"],
                "question_id": row["question_id"],
                "corpus_scale_size": row["corpus_scale_size"],
                "condition": row["condition"],
                "auto_hit_at_10": row["auto_hit_at_10"],
                "gold_id_in_top10": row["gold_id_in_top10"],
                "gold_answers_question": None,
                "human_label_correct": "unsure",
                "human_failure_mode": "other",
                "answer_span": None,
                "human_notes": f"llm_error: {exc}",
                "model": model,
                "prompt_version": PROMPT_VERSION,
                "cost_usd": 0.0,
                "input_tokens": 0,
                "output_tokens": 0,
                "latency_s": round(time.time() - t0, 2),
            }
        results.append(rec)
        print(
            f"[{rec['row_id']}/{len(work)}] {rec['question_id']} N={rec['corpus_scale_size']} "
            f"hit={rec['auto_hit_at_10']} → {rec['human_label_correct']} "
            f"gold_ans={rec['gold_answers_question']} ${rec['cost_usd']:.4f} spent=${spent:.4f}",
            flush=True,
        )
        time.sleep(args.sleep)

    labels = Counter(r["human_label_correct"] for r in results)
    modes = Counter(r["human_failure_mode"] for r in results if r.get("human_failure_mode"))
    gold_yes = sum(1 for r in results if r.get("gold_answers_question") is True)
    gold_no = sum(1 for r in results if r.get("gold_answers_question") is False)
    # Consistency: HIT + gold answers → expect y; HIT + not answer → expect n label_noise
    agree = sum(1 for r in results if r["human_label_correct"] == "y")
    report = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "prompt_version": PROMPT_VERSION,
        "model": model,
        "base_url": base_url or "https://api.openai.com/v1",
        "n_rows_requested": len(work),
        "n_rows_evaluated": len(results),
        "spent_usd": round(spent, 4),
        "budget_usd": args.budget_usd,
        "label_counts": dict(labels),
        "failure_mode_counts": {str(k): v for k, v in modes.items()},
        "gold_answers_question_true": gold_yes,
        "gold_answers_question_false": gold_no,
        "agree_y_rate": round(agree / max(len(results), 1), 3),
        "transparency_note": (
            "L4 is LLM-assisted secondary audit of Hit@10 fairness and gold-text adequacy. "
            "Primary paper claims remain L1 labeled IR (unique eval IDs, membership Hit@k) "
            "on the integrity-clean scale ladder. Cursor Luna is not used as an API model; "
            f"this run used {model} via OpenAI-compatible HTTP."
        ),
        "results": results,
    }

    PUB.mkdir(parents=True, exist_ok=True)
    json_path = PUB / "l4_hit_fairness_llm.json"
    json_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    csv_path = PUB / "l4_hit_fairness_llm.csv"
    fields = [
        "row_id",
        "question_id",
        "corpus_scale_size",
        "condition",
        "auto_hit_at_10",
        "gold_id_in_top10",
        "gold_answers_question",
        "human_label_correct",
        "human_failure_mode",
        "answer_span",
        "human_notes",
        "cost_usd",
    ]
    with csv_path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for r in results:
            w.writerow(r)

    md_path = PUB / "l4_hit_fairness_llm.md"
    md = [
        "# L4 Hit@10 fairness — LLM audit (secondary)",
        "",
        report["transparency_note"],
        "",
        f"- Model: `{model}` · prompt `{PROMPT_VERSION}`",
        f"- Rows: **{len(results)}** / {len(work)} · spent **${spent:.4f}** / ${args.budget_usd}",
        f"- Labels: `{dict(labels)}`",
        f"- Gold answers question: true={gold_yes} false={gold_no}",
        f"- Failure modes: `{dict(modes)}`",
        "",
        "## Per-row",
        "",
        "| # | question_id | N | cond | Hit@10 | gold_ans | label | mode | notes |",
        "|---|-------------|---|------|--------|----------|-------|------|-------|",
    ]
    for r in results:
        notes = (r.get("human_notes") or "").replace("|", "/").replace("\n", " ")[:120]
        md.append(
            f"| {r['row_id']} | `{r['question_id']}` | {r['corpus_scale_size']} | {r['condition']} | "
            f"{r['auto_hit_at_10']} | {r.get('gold_answers_question')} | **{r['human_label_correct']}** | "
            f"{r.get('human_failure_mode')} | {notes} |"
        )
    md_path.write_text("\n".join(md) + "\n", encoding="utf-8")

    print(f"wrote {json_path}")
    print(f"wrote {csv_path}")
    print(f"wrote {md_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
