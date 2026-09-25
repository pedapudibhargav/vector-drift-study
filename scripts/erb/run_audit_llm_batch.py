#!/usr/bin/env python3
"""Batch L4 LLM audit over human_audit CSVs — gpt-4o, hard $2 budget.

Works with or without Postgres:
  - Always writes artifacts/published/llm_audit_report.json (+ .md)
  - If DATABASE_URL reachable, also upserts study_evaluations + audit_cost_ledger

Usage:
  python scripts/erb/run_audit_llm_batch.py
  python scripts/erb/run_audit_llm_batch.py --limit 10   # smoke
  docker exec -e OPENAI_API_KEY=... vector-drift-api \\
    python /app/scripts/erb/run_audit_llm_batch.py
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
import sys
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "erb"))
sys.path.insert(0, str(ROOT / "apps" / "api"))

PUB = ROOT / "artifacts" / "published"
VERIFY_DIRS = [
    ROOT / "artifacts" / "verification",
    ROOT / "docs" / "data" / "verification",
]
DOCS_DIR = ROOT / "data" / "enterprise_rag_bench" / "documents"
QUESTIONS_JSONL = ROOT / "data" / "enterprise_rag_bench" / "questions.jsonl"


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


def load_samples_from_csv() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for csv_path in sorted(PUB.glob("human_audit_n*_raw.csv")):
        with csv_path.open(encoding="utf-8", newline="") as fh:
            for row in csv.DictReader(fh):
                qid = (row.get("question_id") or "").strip()
                if not qid:
                    continue
                hit_raw = str(row.get("hit_at_10") or "").strip().lower()
                rank_s = (row.get("rank") or "").strip()
                dr_s = (row.get("document_recall") or "").strip()
                rows.append(
                    {
                        "question_id": qid,
                        "corpus_scale_size": int(row.get("corpus_scale_size") or 0),
                        "condition": (row.get("condition") or "raw").strip(),
                        "hit_at_10": hit_raw in ("true", "1", "t", "yes"),
                        "rank": int(float(rank_s)) if rank_s else None,
                        "document_recall": float(dr_s) if dr_s else None,
                        "expected_doc_ids": _split_ids(row.get("expected_doc_ids")),
                        "retrieved_doc_ids": _split_ids(row.get("retrieved_doc_ids")),
                        "sample_source": csv_path.name,
                    }
                )
    return rows


def load_wide_samples(pct: float = 5.0, seed: int = 42) -> list[dict[str, Any]]:
    """Stratified ≥pct% of corrected unique (qid × scale × condition) matrix."""
    import random

    corrected = PUB / "erb_full_primary_corrected.json"
    src = corrected if corrected.exists() else PUB / "erb_full_primary200_to100k.json"
    data = json.loads(src.read_text(encoding="utf-8"))
    universe: list[dict[str, Any]] = []
    for run in data.get("runs") or []:
        scale = int(run.get("corpus_scale_size") or 0)
        cond = str(run.get("condition") or "raw")
        seen_q: set[str] = set()
        for q in run.get("per_question") or []:
            qid = str(q.get("question_id") or "")
            if not qid or qid in seen_q:
                continue
            seen_q.add(qid)
            exp = _split_ids(q.get("expected_doc_ids"))
            ret = _split_ids(q.get("retrieved_doc_ids"))
            hit = bool(q.get("hit_at_10"))
            if "hit_at_10" not in q and exp:
                hit = bool(set(exp) & set(ret[:10]))
            universe.append(
                {
                    "question_id": qid,
                    "corpus_scale_size": scale,
                    "condition": cond,
                    "hit_at_10": hit,
                    "rank": q.get("rank"),
                    "document_recall": q.get("document_recall"),
                    "expected_doc_ids": exp,
                    "retrieved_doc_ids": ret,
                    "sample_source": src.name,
                }
            )
    target = max(1, int(math.ceil(len(universe) * (pct / 100.0))))
    # Stratify by (scale, condition, hit/miss)
    buckets: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in universe:
        buckets[(row["corpus_scale_size"], row["condition"], bool(row["hit_at_10"]))].append(row)
    rng = random.Random(seed)
    picked: list[dict[str, Any]] = []
    # proportional take
    for key, bucket in sorted(buckets.items()):
        rng.shuffle(bucket)
        take = max(1, round(target * len(bucket) / len(universe))) if universe else 0
        picked.extend(bucket[:take])
    rng.shuffle(picked)
    if len(picked) < target:
        rest = [r for r in universe if id(r) not in {id(x) for x in picked}]
        rng.shuffle(rest)
        picked.extend(rest[: target - len(picked)])
    # For the default 5% of the 3600-row published matrix, enforce ≥180
    min_floor = 180 if pct >= 5.0 else target
    need = max(target, min_floor)
    if len(picked) < need:
        rest = [r for r in universe if id(r) not in {id(x) for x in picked}]
        rng.shuffle(rest)
        picked.extend(rest[: need - len(picked)])
    print(f"wide_universe={len(universe)} target>={need} ({pct}%) picked={len(picked)} source={src.name}")
    return picked[:need]


# back-compat
def load_samples() -> list[dict[str, Any]]:
    return load_samples_from_csv()


def load_questions() -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for vdir in VERIFY_DIRS:
        qp = vdir / "questions.json"
        if qp.exists():
            blob = json.loads(qp.read_text(encoding="utf-8"))
            for qid, meta in blob.items():
                out[qid] = meta
            break
    if QUESTIONS_JSONL.exists():
        with QUESTIONS_JSONL.open(encoding="utf-8") as fh:
            for line in fh:
                if not line.strip():
                    continue
                row = json.loads(line)
                qid = row.get("question_id") or row.get("id")
                if not qid:
                    continue
                qid = str(qid)
                if qid in out and (out[qid].get("question_text") or out[qid].get("question")):
                    continue
                out[qid] = {
                    "question_id": qid,
                    "question_text": row.get("question") or row.get("question_text") or "",
                    "question_type": row.get("question_type"),
                    "expected_doc_ids": row.get("expected_doc_ids") or [],
                }
    return out


def _doc_index() -> dict[str, Path]:
    index: dict[str, Path] = {}
    if DOCS_DIR.exists():
        for p in DOCS_DIR.glob("*.txt"):
            name = p.name
            if name.startswith("dsid_") and "__" in name:
                index.setdefault(name.split("__", 1)[0], p)
    return index


def load_chunks_index() -> dict[str, str]:
    out: dict[str, str] = {}
    for vdir in VERIFY_DIRS:
        cp = vdir / "chunks_by_id.json"
        if cp.exists():
            out.update({str(k): str(v) for k, v in json.loads(cp.read_text(encoding="utf-8")).items()})
            break
    return out


def ensure_chunk_texts(doc_ids: list[str], chunks: dict[str, str], doc_index: dict[str, Path]) -> None:
    for did in doc_ids:
        if did in chunks and (chunks[did] or "").strip():
            continue
        path = doc_index.get(did)
        if path is None:
            continue
        try:
            # Cap read size — some corpus text files are multi-MB.
            with path.open("r", encoding="utf-8", errors="replace") as fh:
                chunks[did] = fh.read(4000)
        except OSError:
            continue


def build_payload(
    sample: dict[str, Any],
    questions: dict[str, dict[str, Any]],
    chunks: dict[str, str],
    doc_index: dict[str, Path] | None = None,
) -> dict[str, Any]:
    # Prefer raw ERB id when sample uses eval_id (qid::type)
    qid = str(sample["question_id"])
    raw_qid = qid.split("::", 1)[0]
    qmeta = questions.get(qid) or questions.get(raw_qid) or {}
    expected = list(sample["expected_doc_ids"] or qmeta.get("expected_doc_ids") or [])
    retrieved = list(sample["retrieved_doc_ids"] or [])
    if doc_index is not None:
        ensure_chunk_texts(expected + retrieved, chunks, doc_index)
    gold_chunks = []
    for did in expected:
        text = chunks.get(did)
        gold_chunks.append(
            {
                "doc_id": did,
                "preview": (text or "")[:1500],
                "source": "bundle" if text else "missing",
            }
        )
    retrieved_chunks = []
    for i, did in enumerate(retrieved, start=1):
        text = chunks.get(did)
        retrieved_chunks.append(
            {
                "rank": i,
                "doc_id": did,
                "is_gold": did in set(expected),
                "preview": (text or "")[:1200],
                "source": "bundle" if text else "missing",
            }
        )
    return {
        **sample,
        "question_text": qmeta.get("question_text") or qmeta.get("question") or "",
        "question_type": qmeta.get("question_type"),
        "expected_doc_ids": expected,
        "retrieved_doc_ids": retrieved,
        "gold_chunks": gold_chunks,
        "retrieved_chunks": retrieved_chunks,
    }


def find_csv_anomalies(samples: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Catch sampling/export bugs before LLM spend."""
    anomalies: list[dict[str, Any]] = []
    by_key: dict[tuple[str, int, str], list[dict[str, Any]]] = defaultdict(list)
    for s in samples:
        by_key[(s["question_id"], s["corpus_scale_size"], s["condition"])].append(s)
    for key, group in by_key.items():
        if len(group) > 1:
            hits = {g["hit_at_10"] for g in group}
            anomalies.append(
                {
                    "type": "duplicate_sample_key",
                    "question_id": key[0],
                    "corpus_scale_size": key[1],
                    "condition": key[2],
                    "n": len(group),
                    "hit_at_10_values": sorted(hits),
                    "severity": "conflicting" if len(hits) > 1 else "duplicate_ok_same_hit",
                }
            )
    for s in samples:
        exp = set(s["expected_doc_ids"])
        ret = set(s["retrieved_doc_ids"])
        membership = bool(exp & ret)
        if membership != bool(s["hit_at_10"]):
            anomalies.append(
                {
                    "type": "hit_flag_vs_membership",
                    "question_id": s["question_id"],
                    "corpus_scale_size": s["corpus_scale_size"],
                    "hit_at_10": s["hit_at_10"],
                    "id_membership": membership,
                }
            )
    return anomalies


def run_llm_one(client: Any, model: str, payload: dict[str, Any], prog: dict[str, Any]) -> dict[str, Any]:
    from app.services.audit_llm import build_prompt, estimate_cost

    prompt = build_prompt(payload, prog)
    t0 = time.perf_counter()
    if callable(client):
        # urllib fallback client(model, messages) -> (content, inp, out)
        content, inp, out = client(model, prompt)
    else:
        resp = client.chat.completions.create(
            model=model,
            temperature=0.1,
            response_format={"type": "json_object"},
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a careful IR + RAG evaluation auditor. "
                        "Be skeptical of empty chunks and inconsistent Hit flags. JSON only."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
        )
        content = (resp.choices[0].message.content or "{}").strip()
        usage = resp.usage
        inp = int(getattr(usage, "prompt_tokens", 0) or 0)
        out = int(getattr(usage, "completion_tokens", 0) or 0)
    latency_ms = int((time.perf_counter() - t0) * 1000)
    cost = estimate_cost(inp, out)
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError:
        parsed = {
            "label_correct": "unsure",
            "failure_mode": "other",
            "reasoning_summary": content[:500],
            "pipeline_issues": ["json_parse_error"],
        }
    return {
        "model": model,
        "latency_ms": latency_ms,
        "cost_usd": cost,
        "input_tokens": inp,
        "output_tokens": out,
        "parsed": parsed,
        "programmatic": prog,
    }


def _make_urllib_client(api_key: str, base_url: str | None = None) -> Any:
    import urllib.error
    import urllib.request

    endpoint = (base_url or "https://api.openai.com/v1").rstrip("/") + "/chat/completions"
    use_json_mode = not bool(base_url)  # Ollama often lacks response_format

    def _call(model: str, prompt: str) -> tuple[str, int, int]:
        def _post(with_json_mode: bool) -> dict[str, Any]:
            payload: dict[str, Any] = {
                "model": model,
                "temperature": 0.1,
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "You are a careful IR + RAG evaluation auditor. "
                            "Be skeptical of empty chunks and inconsistent Hit flags. JSON only."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
            }
            if with_json_mode:
                payload["response_format"] = {"type": "json_object"}
            # Local Ollama: prefer CPU if Metal OOMs (AUDIT_OLLAMA_NUM_GPU=0)
            if base_url and "11434" in base_url:
                num_gpu = os.environ.get("AUDIT_OLLAMA_NUM_GPU")
                opts: dict[str, Any] = {"temperature": 0.1}
                if num_gpu is not None:
                    opts["num_gpu"] = int(num_gpu)
                payload["options"] = opts
            body = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                endpoint,
                data=body,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=60) as resp:
                return json.loads(resp.read().decode("utf-8"))

        try:
            data = _post(use_json_mode)
        except urllib.error.HTTPError as exc:
            err = exc.read().decode("utf-8", errors="replace")
            if use_json_mode and exc.code in (400, 404, 422):
                data = _post(False)
            else:
                raise RuntimeError(f"OpenAI HTTP {exc.code}: {err[:400]}") from exc
        content = data["choices"][0]["message"]["content"] or "{}"
        usage = data.get("usage") or {}
        return (
            content.strip(),
            int(usage.get("prompt_tokens") or 0),
            int(usage.get("completion_tokens") or 0),
        )

    return _call


def try_persist_db(results: list[dict[str, Any]], spent_events: list[dict[str, Any]]) -> str:
    url = os.environ.get("DATABASE_URL", "")
    if not url:
        return "skipped:no_DATABASE_URL"
    sync = url.replace("postgresql+asyncpg://", "postgresql://")
    try:
        import psycopg
    except ImportError:
        return "skipped:no_psycopg"
    try:
        with psycopg.connect(sync) as conn:
            # Ensure schema exists (minimal)
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS audit_samples (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    question_id VARCHAR(64) NOT NULL,
                    corpus_scale_size INT NOT NULL,
                    condition VARCHAR(32) NOT NULL,
                    hit_at_10 BOOLEAN,
                    rank INT,
                    document_recall DOUBLE PRECISION,
                    expected_doc_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
                    retrieved_doc_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
                    sample_source TEXT,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE (question_id, corpus_scale_size, condition)
                );
                CREATE TABLE IF NOT EXISTS study_evaluations (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    eval_scope VARCHAR(32) NOT NULL DEFAULT 'retrieval_row',
                    question_id VARCHAR(64),
                    corpus_scale_size INT,
                    condition VARCHAR(32),
                    claim_key VARCHAR(128),
                    evaluator_kind VARCHAR(16) NOT NULL,
                    auditor_id VARCHAR(64) NOT NULL,
                    label_correct VARCHAR(16),
                    failure_mode VARCHAR(64),
                    notes TEXT,
                    status VARCHAR(32) NOT NULL DEFAULT 'pending',
                    hit_at_10 BOOLEAN,
                    rank INT,
                    document_recall DOUBLE PRECISION,
                    expected_doc_ids JSONB,
                    retrieved_doc_ids JSONB,
                    relevance_score DOUBLE PRECISION,
                    reasoning_summary TEXT,
                    model VARCHAR(100),
                    prompt_version VARCHAR(32),
                    latency_ms INT,
                    cost_usd DECIMAL(10, 6),
                    input_tokens INT,
                    output_tokens INT,
                    checklist_json JSONB,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS audit_cost_ledger (
                    id BIGSERIAL PRIMARY KEY,
                    kind TEXT NOT NULL,
                    model TEXT,
                    input_tokens INT,
                    output_tokens INT,
                    cost_usd DOUBLE PRECISION NOT NULL,
                    note TEXT,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                );
                """
            )
            for r in results:
                s = r["sample"]
                conn.execute(
                    """
                    INSERT INTO audit_samples (
                        question_id, corpus_scale_size, condition, hit_at_10, rank,
                        document_recall, expected_doc_ids, retrieved_doc_ids, sample_source
                    ) VALUES (%s,%s,%s,%s,%s,%s,%s::jsonb,%s::jsonb,%s)
                    ON CONFLICT (question_id, corpus_scale_size, condition) DO UPDATE SET
                        hit_at_10 = EXCLUDED.hit_at_10,
                        expected_doc_ids = EXCLUDED.expected_doc_ids,
                        retrieved_doc_ids = EXCLUDED.retrieved_doc_ids
                    """,
                    (
                        s["question_id"],
                        s["corpus_scale_size"],
                        s["condition"],
                        s["hit_at_10"],
                        s.get("rank"),
                        s.get("document_recall"),
                        json.dumps(s["expected_doc_ids"]),
                        json.dumps(s["retrieved_doc_ids"]),
                        s.get("sample_source"),
                    ),
                )
                auditor = f"llm:{r['model']}"
                parsed = r["parsed"]
                cj = {
                    "pipeline_issues": r.get("pipeline_issues") or [],
                    "programmatic": r.get("programmatic"),
                    "raw": parsed,
                }
                existing = conn.execute(
                    """
                    SELECT id FROM study_evaluations
                    WHERE eval_scope='retrieval_row' AND question_id=%s
                      AND corpus_scale_size=%s AND condition=%s
                      AND evaluator_kind='llm' AND auditor_id=%s
                    LIMIT 1
                    """,
                    (s["question_id"], s["corpus_scale_size"], s["condition"], auditor),
                ).fetchone()
                if existing:
                    conn.execute(
                        """
                        UPDATE study_evaluations SET
                          label_correct=%s, failure_mode=%s, status='done',
                          relevance_score=%s, reasoning_summary=%s, model=%s,
                          prompt_version=%s, latency_ms=%s, cost_usd=%s,
                          input_tokens=%s, output_tokens=%s, checklist_json=%s::jsonb,
                          hit_at_10=%s, rank=%s, document_recall=%s,
                          expected_doc_ids=%s::jsonb, retrieved_doc_ids=%s::jsonb,
                          updated_at=CURRENT_TIMESTAMP
                        WHERE id=%s
                        """,
                        (
                            parsed.get("label_correct"),
                            parsed.get("failure_mode"),
                            parsed.get("relevance_score"),
                            parsed.get("reasoning_summary"),
                            r["model"],
                            "audit-v2-pipeline",
                            r["latency_ms"],
                            r["cost_usd"],
                            r["input_tokens"],
                            r["output_tokens"],
                            json.dumps(cj),
                            s["hit_at_10"],
                            s.get("rank"),
                            s.get("document_recall"),
                            json.dumps(s["expected_doc_ids"]),
                            json.dumps(s["retrieved_doc_ids"]),
                            existing[0],
                        ),
                    )
                else:
                    conn.execute(
                        """
                        INSERT INTO study_evaluations (
                          eval_scope, question_id, corpus_scale_size, condition,
                          evaluator_kind, auditor_id, label_correct, failure_mode, status,
                          hit_at_10, rank, document_recall, expected_doc_ids, retrieved_doc_ids,
                          relevance_score, reasoning_summary, model, prompt_version,
                          latency_ms, cost_usd, input_tokens, output_tokens, checklist_json
                        ) VALUES (
                          'retrieval_row', %s, %s, %s, 'llm', %s, %s, %s, 'done',
                          %s, %s, %s, %s::jsonb, %s::jsonb,
                          %s, %s, %s, 'audit-v2-pipeline', %s, %s, %s, %s, %s::jsonb
                        )
                        """,
                        (
                            s["question_id"],
                            s["corpus_scale_size"],
                            s["condition"],
                            auditor,
                            parsed.get("label_correct"),
                            parsed.get("failure_mode"),
                            s["hit_at_10"],
                            s.get("rank"),
                            s.get("document_recall"),
                            json.dumps(s["expected_doc_ids"]),
                            json.dumps(s["retrieved_doc_ids"]),
                            parsed.get("relevance_score"),
                            parsed.get("reasoning_summary"),
                            r["model"],
                            r["latency_ms"],
                            r["cost_usd"],
                            r["input_tokens"],
                            r["output_tokens"],
                            json.dumps(cj),
                        ),
                    )
            for ev in spent_events:
                conn.execute(
                    """
                    INSERT INTO audit_cost_ledger (kind, model, input_tokens, output_tokens, cost_usd, note)
                    VALUES ('audit_llm', %s, %s, %s, %s, %s)
                    """,
                    (ev["model"], ev["input_tokens"], ev["output_tokens"], ev["cost_usd"], ev["note"]),
                )
            conn.commit()
        return "ok"
    except Exception as exc:  # noqa: BLE001
        return f"error:{exc}"


def _resolve_api_key() -> str:
    key = (os.environ.get("OPENAI_API_KEY") or "").strip()
    if key and not key.startswith("sk-your"):
        return key
    for env_path in (ROOT / ".env", Path("/app/.env")):
        if not env_path.is_file():
            continue
        for line in env_path.read_text(encoding="utf-8").splitlines():
            if not line.startswith("OPENAI_API_KEY="):
                continue
            candidate = line.split("=", 1)[1].strip().strip('"').strip("'")
            if candidate and not candidate.startswith("sk-your"):
                return candidate
    return key


def main() -> int:
    _load_env()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, default=0, help="Max rows (0=all)")
    parser.add_argument("--dry-run", action="store_true", help="Programmatic only, no LLM calls")
    parser.add_argument(
        "--wide",
        action="store_true",
        help="Sample from corrected full ladder (not just human_audit CSVs)",
    )
    parser.add_argument(
        "--pct",
        type=float,
        default=5.0,
        help="With --wide, sample at least this %% of unique matrix (default 5 → ≥180 of 3600)",
    )
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument(
        "--report-stem",
        type=str,
        default="llm_audit_report",
        help="Output basename under artifacts/published/ (no extension). "
        "Use distinct stems per provider (e.g. llm_audit_report_openai).",
    )
    args = parser.parse_args()

    try:
        from app import ssl_bundle

        ssl_bundle.apply_corporate_ssl_bundle()
    except Exception:  # noqa: BLE001
        pass

    # Prefer in-repo auditor helpers
    sys.path.insert(0, str(ROOT / "apps" / "api"))
    from app.services.audit_llm import (  # noqa: WPS433
        BUDGET_USD,
        DEFAULT_MODEL,
        programmatic_checks,
    )

    if args.wide:
        samples = load_wide_samples(pct=args.pct, seed=args.seed)
        anomalies = find_csv_anomalies(samples)
    else:
        samples = load_samples_from_csv()
        anomalies = find_csv_anomalies(samples)
    # Deduplicate by key keeping first occurrence for LLM
    seen: set[tuple[str, int, str]] = set()
    unique: list[dict[str, Any]] = []
    for s in samples:
        key = (s["question_id"], s["corpus_scale_size"], s["condition"])
        if key in seen:
            continue
        seen.add(key)
        unique.append(s)
    if args.limit > 0:
        unique = unique[: args.limit]

    questions = load_questions()
    chunks = load_chunks_index()
    doc_index = _doc_index()
    print(
        f"samples_csv={len(samples)} unique={len(unique)} "
        f"questions={len(questions)} chunks_bundle={len(chunks)} "
        f"doc_files={len(doc_index)} anomalies={len(anomalies)}"
    )

    model = os.environ.get("AUDIT_LLM_MODEL", DEFAULT_MODEL)
    budget = float(os.environ.get("AUDIT_LLM_BUDGET_USD", str(BUDGET_USD)))
    results: list[dict[str, Any]] = []
    spent_events: list[dict[str, Any]] = []
    spent = 0.0

    client = None
    if not args.dry_run:
        api_key = _resolve_api_key()
        if not api_key or api_key.startswith("sk-your"):
            print("ERROR: OPENAI_API_KEY missing", file=sys.stderr)
            return 2
        base = os.environ.get("AUDIT_LLM_BASE_URL", "").strip() or None
        try:
            from openai import OpenAI

            if os.environ.get("AUDIT_LLM_FORCE_URLLIB", "").strip() in {"1","true","yes"}:
                raise ImportError("forced urllib")
            kwargs: dict[str, Any] = {"api_key": api_key, "timeout": 60.0}
            if base:
                kwargs["base_url"] = base
            client = OpenAI(**kwargs)
            print("LLM client: openai SDK", flush=True)
        except ImportError:
            client = _make_urllib_client(api_key, base)
            print("LLM client: urllib fallback", flush=True)

    for i, sample in enumerate(unique, start=1):
        print(f"… preparing {i}/{len(unique)} {sample['question_id']}", flush=True)
        payload = build_payload(sample, questions, chunks, doc_index)
        prog = programmatic_checks(payload)
        if args.dry_run or client is None:
            results.append(
                {
                    "sample": sample,
                    "model": None,
                    "cost_usd": 0.0,
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "latency_ms": 0,
                    "parsed": {
                        "label_correct": "unsure" if prog["programmatic_issues"] else "y",
                        "failure_mode": None,
                        "reasoning_summary": "dry-run programmatic only",
                        "pipeline_issues": prog["programmatic_issues"],
                    },
                    "programmatic": prog,
                    "pipeline_issues": prog["programmatic_issues"],
                }
            )
            continue
        if spent + 0.02 > budget:
            print(f"STOP budget remaining={budget - spent:.4f} at row {i}/{len(unique)}", flush=True)
            break
        try:
            out = run_llm_one(client, model, payload, prog)
        except Exception as exc:  # noqa: BLE001
            err_s = str(exc).lower()
            # Soft-retry rate limits instead of burning the rest of the queue as fails.
            if "429" in err_s or "rate limit" in err_s:
                wait_s = 5.0
                import re

                m = re.search(r"try again in ([0-9.]+)\s*s", str(exc), re.I)
                if m:
                    wait_s = min(30.0, float(m.group(1)) + 1.0)
                print(f"rate-limit hit; sleeping {wait_s:.1f}s then retrying {sample['question_id']}", flush=True)
                time.sleep(wait_s)
                try:
                    out = run_llm_one(client, model, payload, prog)
                except Exception as exc2:  # noqa: BLE001
                    print(f"LLM fail {sample['question_id']} after retry: {exc2}", flush=True)
                    results.append(
                        {
                            "sample": sample,
                            "model": model,
                            "cost_usd": 0.0,
                            "input_tokens": 0,
                            "output_tokens": 0,
                            "latency_ms": 0,
                            "parsed": {
                                "label_correct": "unsure",
                                "failure_mode": "other",
                                "reasoning_summary": f"llm_error: {exc2}",
                                "pipeline_issues": ["llm_call_failed"],
                            },
                            "programmatic": prog,
                            "pipeline_issues": prog["programmatic_issues"] + ["llm_call_failed"],
                        }
                    )
                    continue
            else:
                print(f"LLM fail {sample['question_id']}: {exc}", flush=True)
                results.append(
                    {
                        "sample": sample,
                        "model": model,
                        "cost_usd": 0.0,
                        "input_tokens": 0,
                        "output_tokens": 0,
                        "latency_ms": 0,
                        "parsed": {
                            "label_correct": "unsure",
                            "failure_mode": "other",
                            "reasoning_summary": f"llm_error: {exc}",
                            "pipeline_issues": ["llm_call_failed"],
                        },
                        "programmatic": prog,
                        "pipeline_issues": prog["programmatic_issues"] + ["llm_call_failed"],
                    }
                )
                # Fail fast on network / auth — do not burn the queue
                if any(
                    x in err_s
                    for x in ("403", "401", "tunnel", "nodename", "network", "timed out", "timeout")
                ):
                    print("STOP: LLM transport/auth failure — aborting remaining rows", flush=True)
                    break
                continue
        spent += float(out["cost_usd"])
        spent_events.append(
            {
                "model": out["model"],
                "input_tokens": out["input_tokens"],
                "output_tokens": out["output_tokens"],
                "cost_usd": out["cost_usd"],
                "note": f"{sample['question_id']}@{sample['corpus_scale_size']}",
            }
        )
        issues = list(prog.get("programmatic_issues") or [])
        for x in (out["parsed"].get("pipeline_issues") or []):
            if x and x not in issues:
                issues.append(x)
        results.append(
            {
                "sample": sample,
                "model": out["model"],
                "cost_usd": out["cost_usd"],
                "input_tokens": out["input_tokens"],
                "output_tokens": out["output_tokens"],
                "latency_ms": out["latency_ms"],
                "parsed": out["parsed"],
                "programmatic": prog,
                "pipeline_issues": issues,
            }
        )
        print(
            f"[{i}/{len(unique)}] {sample['question_id']} N={sample['corpus_scale_size']} "
            f"label={out['parsed'].get('label_correct')} cost=${out['cost_usd']:.4f} "
            f"spent=${spent:.4f}",
            flush=True,
        )

    labels = Counter(r["parsed"].get("label_correct") for r in results)
    modes = Counter(r["parsed"].get("failure_mode") for r in results if r["parsed"].get("failure_mode"))
    issue_counts = Counter()
    for r in results:
        for iss in r.get("pipeline_issues") or []:
            issue_counts[iss] += 1

    flagged = [
        r
        for r in results
        if r["parsed"].get("label_correct") in ("n", "unsure")
        or (r.get("pipeline_issues") or [])
        or not (r.get("programmatic") or {}).get("hit_flag_consistent", True)
    ]

    report = {
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "model": model,
        "budget_usd": budget,
        "spent_usd": round(spent, 6),
        "n_evaluated": len(results),
        "n_unique_samples": len(unique),
        "n_csv_rows": len(samples),
        "label_counts": dict(labels),
        "failure_mode_counts": dict(modes),
        "pipeline_issue_counts": dict(issue_counts),
        "csv_anomalies": anomalies,
        "n_flagged": len(flagged),
        "flagged_rows": [
            {
                "question_id": r["sample"]["question_id"],
                "corpus_scale_size": r["sample"]["corpus_scale_size"],
                "hit_at_10": r["sample"]["hit_at_10"],
                "label_correct": r["parsed"].get("label_correct"),
                "failure_mode": r["parsed"].get("failure_mode"),
                "pipeline_issues": r.get("pipeline_issues"),
                "reasoning_summary": r["parsed"].get("reasoning_summary"),
            }
            for r in flagged
        ],
        "rows": [
            {
                "question_id": r["sample"]["question_id"],
                "corpus_scale_size": r["sample"]["corpus_scale_size"],
                "condition": r["sample"]["condition"],
                "hit_at_10": r["sample"]["hit_at_10"],
                "label_correct": r["parsed"].get("label_correct"),
                "failure_mode": r["parsed"].get("failure_mode"),
                "relevance_score": r["parsed"].get("relevance_score"),
                "chunk_quality_score": r["parsed"].get("chunk_quality_score"),
                "reasoning_summary": r["parsed"].get("reasoning_summary"),
                "pipeline_issues": r.get("pipeline_issues"),
                "cost_usd": r["cost_usd"],
                "model": r["model"],
            }
            for r in results
        ],
        "paper_paragraph_draft": (
            f"LLM L4 assist ({model}) labeled {len(results)} stratified audit rows "
            f"(y={labels.get('y', 0)}, n={labels.get('n', 0)}, unsure={labels.get('unsure', 0)}; "
            f"spend ${spent:.3f} of ${budget:.2f}). "
            f"Top pipeline issues: {dict(issue_counts.most_common(5))}. "
            f"CSV anomalies detected: {len(anomalies)}. "
            "Human confirmation remains authoritative for camera-ready counts."
        ),
    }

    PUB.mkdir(parents=True, exist_ok=True)
    stem = (args.report_stem or "llm_audit_report").strip() or "llm_audit_report"
    out_json = PUB / f"{stem}.json"
    out_json.write_text(json.dumps(report, indent=2), encoding="utf-8")
    md_lines = [
        "# LLM L4 Audit Report",
        "",
        f"_Generated {report['exported_at']}_",
        "",
        f"- Model: `{model}`",
        f"- Report stem: `{stem}`",
        f"- Evaluated: **{len(results)}** / {len(unique)} unique samples",
        f"- Spend: **${spent:.4f}** / ${budget:.2f}",
        f"- Labels: {dict(labels)}",
        f"- Failure modes: {dict(modes)}",
        f"- Pipeline issues: {dict(issue_counts)}",
        f"- CSV anomalies: **{len(anomalies)}**",
        f"- Flagged for human review: **{len(flagged)}**",
        "",
        "## Draft paragraph",
        "",
        report["paper_paragraph_draft"],
        "",
        "## CSV anomalies",
        "",
        "```json",
        json.dumps(anomalies, indent=2),
        "```",
        "",
        "## Flagged rows",
        "",
    ]
    for f in report["flagged_rows"][:40]:
        md_lines.append(
            f"- `{f['question_id']}` N={f['corpus_scale_size']} hit={f['hit_at_10']} "
            f"label={f['label_correct']} issues={f['pipeline_issues']}: "
            f"{f.get('reasoning_summary')}"
        )
    out_md = PUB / f"{stem}.md"
    out_md.write_text("\n".join(md_lines) + "\n", encoding="utf-8")
    # Keep legacy filenames pointing at the latest run for the Review UI.
    if stem != "llm_audit_report":
        (PUB / "llm_audit_report.json").write_text(out_json.read_text(encoding="utf-8"), encoding="utf-8")
        (PUB / "llm_audit_report.md").write_text(out_md.read_text(encoding="utf-8"), encoding="utf-8")

    db_status = try_persist_db(results, spent_events) if not args.dry_run else "skipped:dry-run"
    print(f"wrote {out_json}")
    print(f"wrote {out_md}")
    print(f"db_persist={db_status}")
    print(report["paper_paragraph_draft"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
