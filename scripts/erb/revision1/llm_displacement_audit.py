#!/usr/bin/env python3
"""LLM relevance audit for documents that displace gold at 100k (revision 1, task G3).

Judges displacers vs 5k non-gold competitors, gold calibration, and random corpus controls.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

import numpy as np
import psycopg2

ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / "data"
REV1 = ROOT / "artifacts" / "published" / "revision1"
LADDER_PATH = REV1 / "exact_ladder_openai_primary200.json"
MANIFEST_PATH = DATA / "erb_scale_manifest.json"
CACHE_PATH = Path(os.environ["AUDIT_CACHE"]) if os.environ.get("AUDIT_CACHE") else DATA / "llm_audit_cache.jsonl"
PLAN_PATH = DATA / "llm_audit_plan.json"
OUT_JSON = REV1 / "llm_displacement_audit.json"
OUT_MD = REV1 / "llm_displacement_audit.md"
TIKTOKEN_CACHE = DATA / "tiktoken_cache"
TOKEN_CUTS_PATH = DATA / "rev1_doc_token_cuts.jsonl"

PROMPT_VERSION = "rev1-displacement-audit-v1"
JUDGE_MODEL_OPENAI = "gpt-4o"
PRICE_IN_PER_M = 2.5
PRICE_OUT_PER_M = 10.0
MAX_DOC_TOKENS = 6000
SEED_ITEMS = 42
SEED_GOLD = 42
SEED_RANDOM = 42
SEED_ORDER = 42
DISPLACED_CAP = 60
GOLD_N = 30
RANDOM_N = 15
PRIMARY_N = 200

JUDGE_USER_TEMPLATE = """You are a strict relevance judge for enterprise RAG evaluation.

Question:
{question}

Document (standalone; no metadata beyond this text):
{document}

Does this document BY ITSELF contain the information needed to answer the question?

Respond with JSON only (no markdown):
{{"answers": "yes" | "partial" | "no", "reason": "<=40 words"}}"""

JSON_ANSWER_RE = re.compile(
    r'"answers"\s*:\s*"(yes|partial|no)"',
    re.IGNORECASE,
)

Category = Literal["displacer", "competitor5k", "gold_control", "random_control"]
Answer = Literal["yes", "partial", "no"]


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def wilson_ci(k: int, n: int, z: float = 1.96) -> tuple[float | None, float | None]:
    if n <= 0:
        return None, None
    p = k / n
    z2 = z * z
    denom = 1.0 + z2 / n
    center = (p + z2 / (2.0 * n)) / denom
    margin = (z * math.sqrt((p * (1.0 - p) + z2 / (4.0 * n)) / n)) / denom
    return max(0.0, center - margin), min(1.0, center + margin)


def pg_connect() -> psycopg2.extensions.connection:
    conn = psycopg2.connect(
        host=os.environ.get("PGHOST", "localhost"),
        port=int(os.environ.get("PGPORT", "5433")),
        user=os.environ["PGUSER"],
        password=os.environ["PGPASSWORD"],
        dbname=os.environ["PGDATABASE"],
        connect_timeout=30,
    )
    conn.autocommit = True
    return conn


@dataclass
class Tokenizer:
    enc: Any | None
    cuts: dict[str, dict[str, int]]

    @classmethod
    def load(cls) -> Tokenizer:
        os.environ.setdefault("TIKTOKEN_CACHE_DIR", str(TIKTOKEN_CACHE))
        enc = None
        try:
            import tiktoken
        except ImportError:
            pass
        else:
            enc = tiktoken.get_encoding("cl100k_base")
        cuts = load_token_cuts()
        return cls(enc=enc, cuts=cuts)

    def truncate_chunk(self, text: str, doc_id: str, max_tokens: int) -> tuple[str, int]:
        if self.enc is not None:
            tokens = self.enc.encode(text or "", disallowed_special=())
            if len(tokens) <= max_tokens:
                return text or "", len(tokens)
            return self.enc.decode(tokens[:max_tokens]), max_tokens
        stats = self.cuts.get(doc_id)
        if not stats:
            est = max(1, len(text or "") // 4)
            if est <= max_tokens:
                return text or "", est
            keep = max(1, len(text) * max_tokens // est)
            return (text or "")[:keep], max_tokens
        tokens = int(stats["tokens"])
        chars = int(stats["chars"])
        if tokens <= max_tokens:
            return text or "", tokens
        keep = max(1, int(chars * max_tokens / tokens))
        return (text or "")[:keep], max_tokens

    def count_text(self, text: str, doc_id: str | None = None) -> int:
        if self.enc is not None:
            return len(self.enc.encode(text or "", disallowed_special=()))
        if doc_id and doc_id in self.cuts:
            stats = self.cuts[doc_id]
            chars = max(1, len(text or ""))
            return max(1, int(stats["tokens"] * chars / stats["chars"]))
        return max(1, len(text or "") // 4)


def load_token_cuts() -> dict[str, dict[str, int]]:
    if not TOKEN_CUTS_PATH.exists():
        return {}
    out: dict[str, dict[str, int]] = {}
    with TOKEN_CUTS_PATH.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            ct = row.get("chunk_text_only") or {}
            if "tokens" in ct and "chars" in ct:
                out[str(row["doc_id"])] = {"tokens": int(ct["tokens"]), "chars": int(ct["chars"])}
    return out


def load_ladder_raw() -> tuple[dict[str, dict], dict[str, dict]]:
    ladder = json.loads(LADDER_PATH.read_text(encoding="utf-8"))
    by_scale: dict[int, dict[str, dict]] = {}
    for run in ladder.get("runs") or []:
        if run.get("condition") != "raw":
            continue
        scale = int(run["scale"])
        by_scale[scale] = {pq["question_id"]: pq for pq in run.get("per_question") or []}
    if 5000 not in by_scale or 100000 not in by_scale:
        raise SystemExit("ladder missing raw runs at 5000 or 100000")
    return by_scale[5000], by_scale[100000]


def load_questions() -> dict[str, dict]:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    return {q["eval_id"]: q for q in manifest.get("questions") or []}


def first_non_gold(retrieved: list[str], gold: set[str]) -> str | None:
    for doc_id in retrieved:
        if doc_id not in gold:
            return doc_id
    return None


def stable_item_id(category: str, eval_id: str, doc_id: str) -> str:
    raw = f"{PROMPT_VERSION}|{category}|{eval_id}|{doc_id}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]


def opaque_id(item_id: str, order_index: int) -> str:
    h = hashlib.sha256(f"{item_id}|{order_index}|{SEED_ORDER}".encode()).hexdigest()
    return f"doc_{h[:12]}"


@dataclass
class AuditItem:
    item_id: str
    category: Category
    eval_id: str
    doc_id: str
    question: str
    prompt: str
    prompt_tokens_est: int


def build_plan(
    q5: dict[str, dict],
    q100: dict[str, dict],
    questions: dict[str, dict],
    rng_displaced: np.random.Generator,
    rng_gold: np.random.Generator,
    rng_random: np.random.Generator,
    tokenizer: Tokenizer,
) -> tuple[list[AuditItem], dict[str, Any]]:
    displaced_ids: list[str] = []
    for qid in sorted(q5.keys()):
        if qid not in q100:
            continue
        if q5[qid].get("hit_at_10") and not q100[qid].get("hit_at_10"):
            displaced_ids.append(qid)

    meta: dict[str, Any] = {
        "displaced_count_full": len(displaced_ids),
        "displaced_sampled": False,
        "displaced_eval_ids": [],
    }

    sample_ids = list(displaced_ids)
    if len(sample_ids) > DISPLACED_CAP:
        meta["displaced_sampled"] = True
        pick = rng_displaced.choice(sample_ids, size=DISPLACED_CAP, replace=False)
        sample_ids = sorted(pick.tolist())
    meta["displaced_eval_ids"] = sample_ids

    items_spec: list[tuple[Category, str, str]] = []

    for eval_id in sample_ids:
        gold = set(questions[eval_id]["expected_doc_ids"])
        ret100 = q100[eval_id].get("retrieved_doc_ids") or []
        ret5 = q5[eval_id].get("retrieved_doc_ids") or []
        d100 = first_non_gold(ret100, gold)
        d5 = first_non_gold(ret5, gold)
        if not d100 or not d5:
            raise SystemExit(f"displaced question {eval_id} missing non-gold displacer or competitor")
        items_spec.append(("displacer", eval_id, d100))
        items_spec.append(("competitor5k", eval_id, d5))

    gold_pool = sorted(qid for qid, pq in q100.items() if pq.get("hit_at_10"))
    if len(gold_pool) < GOLD_N:
        raise SystemExit(f"only {len(gold_pool)} gold-control-eligible questions, need {GOLD_N}")
    gold_pick = sorted(rng_gold.choice(gold_pool, size=GOLD_N, replace=False).tolist())
    for eval_id in gold_pick:
        gold_ids = questions[eval_id]["expected_doc_ids"]
        doc_id = gold_ids[0]
        items_spec.append(("gold_control", eval_id, doc_id))

    manifest_docs = json.loads(MANIFEST_PATH.read_text(encoding="utf-8")).get("documents") or []
    corpus_ids = [d["doc_id"] for d in manifest_docs if int(d["scale_rank"]) < 100000]

    all_qids = sorted(q5.keys())
    random_qids = sorted(rng_random.choice(all_qids, size=RANDOM_N, replace=False).tolist())
    for eval_id in random_qids:
        gold = set(questions[eval_id]["expected_doc_ids"])
        top10 = set(q100[eval_id].get("retrieved_doc_ids") or [])
        exclude = gold | top10
        candidates = [d for d in corpus_ids if d not in exclude]
        if not candidates:
            raise SystemExit(f"no random control candidate for {eval_id}")
        doc_id = str(rng_random.choice(candidates))
        items_spec.append(("random_control", eval_id, doc_id))

    conn = pg_connect()
    doc_ids = sorted({doc_id for _, _, doc_id in items_spec})
    texts: dict[str, str] = {}
    with conn.cursor() as cur:
        for i in range(0, len(doc_ids), 500):
            batch = doc_ids[i : i + 500]
            cur.execute(
                "SELECT doc_id, chunk_text FROM document_chunks WHERE doc_id = ANY(%s)",
                (batch,),
            )
            for doc_id, chunk_text in cur.fetchall():
                texts[str(doc_id)] = chunk_text or ""
    conn.close()
    missing = [d for d in doc_ids if d not in texts]
    if missing:
        raise SystemExit(f"missing chunk_text for {len(missing)} docs (e.g. {missing[:3]})")

    audit_items: list[AuditItem] = []
    for category, eval_id, doc_id in items_spec:
        question = questions[eval_id]["question"]
        raw_text = texts[doc_id]
        doc_body, _ntok = tokenizer.truncate_chunk(raw_text, doc_id, MAX_DOC_TOKENS)
        prompt = JUDGE_USER_TEMPLATE.format(question=question, document=doc_body)
        prompt_tokens_est = tokenizer.count_text(prompt, doc_id=None)
        item_id = stable_item_id(category, eval_id, doc_id)
        audit_items.append(
            AuditItem(
                item_id=item_id,
                category=category,
                eval_id=eval_id,
                doc_id=doc_id,
                question=question,
                prompt=prompt,
                prompt_tokens_est=prompt_tokens_est,
            )
        )

    meta["category_counts"] = {
        "displacer": sum(1 for c, _, _ in items_spec if c == "displacer"),
        "competitor5k": sum(1 for c, _, _ in items_spec if c == "competitor5k"),
        "gold_control": sum(1 for c, _, _ in items_spec if c == "gold_control"),
        "random_control": sum(1 for c, _, _ in items_spec if c == "random_control"),
        "total": len(items_spec),
    }
    meta["gold_control_eval_ids"] = gold_pick
    meta["random_control_eval_ids"] = random_qids
    meta["tokenizer"] = "tiktoken_cl100k_base" if tokenizer.enc is not None else "tiktoken_cuts_fallback"
    return audit_items, meta


def load_cache() -> dict[str, dict]:
    if not CACHE_PATH.exists():
        return {}
    out: dict[str, dict] = {}
    with CACHE_PATH.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            out[str(row["item_id"])] = row
    return out


def append_cache(row: dict) -> None:
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with CACHE_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=True) + "\n")


def parse_judge_json(text: str) -> tuple[Answer, str]:
    text = (text or "").strip()
    try:
        obj = json.loads(text)
        ans = str(obj.get("answers", "")).lower()
        reason = str(obj.get("reason", ""))[:500]
    except json.JSONDecodeError:
        m = JSON_ANSWER_RE.search(text)
        if not m:
            raise ValueError(f"could not parse judge JSON from: {text[:200]!r}")
        ans = m.group(1).lower()
        reason = text[:200]
    if ans not in ("yes", "partial", "no"):
        raise ValueError(f"invalid answers value: {ans!r}")
    return ans, reason  # type: ignore[return-value]


def mock_judge(category: Category, item_id: str, prompt: str) -> tuple[Answer, str, int, int]:
    h = int(hashlib.sha256(f"{category}|{item_id}".encode()).hexdigest(), 16)
    if category == "gold_control":
        ans: Answer = "yes" if h % 5 else "partial"
    elif category == "random_control":
        ans = "no" if h % 3 == 0 else ("partial" if h % 3 == 1 else "yes")
    else:
        answers: list[Answer] = ["yes", "partial", "no"]
        ans = answers[h % 3]
    reason = f"mock {category} judgment {ans}"
    in_tok = max(1, len(prompt) // 4)
    out_tok = 32
    return ans, reason, in_tok, out_tok


def openai_judge(prompt: str, model: str, max_usd: float, spent: float) -> tuple[Answer, str, int, int]:
    api_key = (os.environ.get("OPENAI_API_KEY") or "").strip()
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY missing")
    est = len(prompt) // 4 * PRICE_IN_PER_M / 1e6 + 40 * PRICE_OUT_PER_M / 1e6
    if spent + est > max_usd:
        raise RuntimeError(f"would exceed --max-usd={max_usd} (spent≈{spent:.4f})")

    url = "https://api.openai.com/v1/chat/completions"
    body = {
        "model": model,
        "temperature": 0,
        "response_format": {"type": "json_object"},
        "messages": [
            {
                "role": "system",
                "content": "Return JSON only with keys answers and reason.",
            },
            {"role": "user", "content": prompt},
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
    with urllib.request.urlopen(req, timeout=180) as resp:
        payload = json.loads(resp.read().decode("utf-8"))
    usage = payload.get("usage") or {}
    content = payload["choices"][0]["message"]["content"]
    ans, reason = parse_judge_json(content)
    in_tok = int(usage.get("prompt_tokens") or 0)
    out_tok = int(usage.get("completion_tokens") or 0)
    return ans, reason, in_tok, out_tok


def cursor_judge(prompt: str, workspace: Path) -> tuple[Answer, str, int, int]:
    cmd = [
        "cursor-agent",
        "-p",
        "--mode",
        "ask",
        "--sandbox",
        "enabled",
        "--trust",
        "--model",
        os.environ.get("AUDIT_CURSOR_MODEL", "gpt-5.3-codex"),
        "--workspace",
        str(workspace),
        prompt,
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=600, check=False)
    if proc.returncode != 0:
        raise RuntimeError(f"cursor-agent failed: {proc.stderr[:500]}")
    out = proc.stdout
    ans, reason = parse_judge_json(out)
    in_tok = max(1, len(prompt) // 4)
    out_tok = max(1, len(out) // 4)
    return ans, reason, in_tok, out_tok


def judge_item(
    provider: str,
    item: AuditItem,
    workspace: Path,
    model: str,
    max_usd: float,
    spent: float,
) -> tuple[Answer, str, int, int, float]:
    if provider == "mock":
        ans, reason, in_tok, out_tok = mock_judge(item.category, item.item_id, item.prompt)
    elif provider == "openai":
        ans, reason, in_tok, out_tok = openai_judge(item.prompt, model, max_usd, spent)
    elif provider == "cursor":
        ans, reason, in_tok, out_tok = cursor_judge(item.prompt, workspace)
    else:
        raise SystemExit(f"unknown provider {provider!r}")
    cost = in_tok / 1e6 * PRICE_IN_PER_M + out_tok / 1e6 * PRICE_OUT_PER_M
    return ans, reason, in_tok, out_tok, cost


def order_items(items: list[AuditItem]) -> list[tuple[AuditItem, str]]:
    rng = np.random.default_rng(SEED_ORDER)
    idx = np.arange(len(items))
    rng.shuffle(idx)
    ordered: list[tuple[AuditItem, str]] = []
    for i, pos in enumerate(idx):
        it = items[int(pos)]
        oid = opaque_id(it.item_id, i)
        ordered.append((it, oid))
    return ordered


def estimate_spend(items: list[AuditItem]) -> dict[str, float]:
    in_tok = sum(it.prompt_tokens_est for it in items)
    out_tok = 40 * len(items)
    cost = in_tok / 1e6 * PRICE_IN_PER_M + out_tok / 1e6 * PRICE_OUT_PER_M
    return {"input_tokens_est": float(in_tok), "output_tokens_est": float(out_tok), "usd_est": round(cost, 4)}


def run_dry(items: list[AuditItem], meta: dict[str, Any]) -> None:
    est = estimate_spend(items)
    print("=== dry-run ===")
    print(json.dumps(meta["category_counts"], indent=2))
    print(f"displaced |M| full={meta['displaced_count_full']} sample={len(meta['displaced_eval_ids'])}")
    print(f"token/cost estimate: {est}")
    for i, it in enumerate(items[:2]):
        print(f"\n--- prompt {i+1} ({it.category}, opaque would be blind) ---\n")
        print(it.prompt[:2000] + ("…" if len(it.prompt) > 2000 else ""))


def run_judging(
    items: list[AuditItem],
    meta: dict[str, Any],
    provider: str,
    model: str,
    max_usd: float,
    workspace: Path,
) -> dict[str, Any]:
    cache = load_cache()
    ordered = order_items(items)
    spent = 0.0
    n_new = 0
    in_tok_total = 0
    out_tok_total = 0

    for it, opaque in ordered:
        if it.item_id in cache:
            continue
        ans, reason, in_tok, out_tok, cost = judge_item(provider, it, workspace, model, max_usd, spent)
        spent += cost
        in_tok_total += in_tok
        out_tok_total += out_tok
        row = {
            "item_id": it.item_id,
            "opaque_id": opaque,
            "category": it.category,
            "eval_id": it.eval_id,
            "doc_id": it.doc_id,
            "answers": ans,
            "reason": reason,
            "provider": provider,
            "model": model if provider == "openai" else (os.environ.get("AUDIT_CURSOR_MODEL", "gpt-5.3-codex") if provider == "cursor" else "mock"),
            "prompt_version": PROMPT_VERSION,
            "input_tokens": in_tok,
            "output_tokens": out_tok,
            "cost_usd": round(cost, 6),
            "judged_at": utc_now(),
        }
        append_cache(row)
        cache[it.item_id] = row
        n_new += 1
        if provider == "openai" and spent >= max_usd:
            print(f"stopped at max-usd {max_usd}", file=sys.stderr)
            break

    return {
        "provider": provider,
        "model": model,
        "items_total": len(items),
        "judgments_new": n_new,
        "judgments_cached": len(items) - n_new,
        "spend_usd_session": round(spent, 6),
        "input_tokens_session": in_tok_total,
        "output_tokens_session": out_tok_total,
        "plan_meta": meta,
    }


def category_stats(rows: list[dict], category: Category) -> dict[str, Any]:
    subset = [r for r in rows if r.get("category") == category]
    n = len(subset)
    counts = {a: 0 for a in ("yes", "partial", "no")}
    for r in subset:
        counts[str(r.get("answers"))] = counts.get(str(r.get("answers")), 0) + 1
    shares = {k: (v / n if n else None) for k, v in counts.items()}
    rel = (counts["yes"] + counts["partial"]) / n if n else None
    lo, hi = wilson_ci(counts["yes"] + counts["partial"], n) if n else (None, None)
    wilson_by_label = {}
    for label in ("yes", "partial", "no"):
        wlo, whi = wilson_ci(counts[label], n) if n else (None, None)
        wilson_by_label[label] = [
            round(wlo, 4) if wlo is not None else None,
            round(whi, 4) if whi is not None else None,
        ]
    out: dict[str, Any] = {
        "n": n,
        "counts": counts,
        "shares": {k: round(v, 4) if v is not None else None for k, v in shares.items()},
        "wilson95_by_label": wilson_by_label,
        "yes_plus_partial_share": round(rel, 4) if rel is not None else None,
        "yes_plus_partial_wilson95": [round(lo, 4) if lo is not None else None, round(hi, 4) if hi is not None else None],
    }
    if category == "gold_control":
        ylo, yhi = wilson_ci(counts["yes"], n)
        out["yes_share"] = round(counts["yes"] / n, 4) if n else None
        out["yes_wilson95"] = [round(ylo, 4) if ylo is not None else None, round(yhi, 4) if yhi is not None else None]
    return out


def is_relevant(ans: str) -> bool:
    return ans in ("yes", "partial")


def mcnemar_paired(displacer: dict[str, str], competitor: dict[str, str]) -> dict[str, Any]:
    keys = sorted(set(displacer) & set(competitor))
    b = c = 0
    for k in keys:
        d_rel = is_relevant(displacer[k])
        c_rel = is_relevant(competitor[k])
        if d_rel and not c_rel:
            b += 1
        elif c_rel and not d_rel:
            c += 1
    n_disc = b + c
    if n_disc == 0:
        chi2 = 0.0
    else:
        chi2 = (abs(b - c) - 1) ** 2 / n_disc if n_disc else 0.0
    return {
        "n_pairs": len(keys),
        "b_displacer_rel_competitor_not": b,
        "c_competitor_rel_displacer_not": c,
        "mcnemar_chi2_with_continuity": round(chi2, 4),
        "note": "McNemar-style discordant counts on same displaced questions (yes+partial=relevant)",
    }


def analyze(cache: dict[str, dict], meta: dict[str, Any], run_meta: dict[str, Any]) -> dict[str, Any]:
    rows = list(cache.values())
    by_cat = {
        "displacer": category_stats(rows, "displacer"),
        "competitor5k": category_stats(rows, "competitor5k"),
        "gold_control": category_stats(rows, "gold_control"),
        "random_control": category_stats(rows, "random_control"),
    }

    displacer_by_q: dict[str, str] = {}
    comp_by_q: dict[str, str] = {}
    for r in rows:
        if r["category"] == "displacer":
            displacer_by_q[r["eval_id"]] = r["answers"]
        if r["category"] == "competitor5k":
            comp_by_q[r["eval_id"]] = r["answers"]

    paired = mcnemar_paired(displacer_by_q, comp_by_q)

    n_displaced = meta["displaced_count_full"]
    n_yes_displacer = sum(1 for r in rows if r["category"] == "displacer" and r["answers"] == "yes")
    label_bound = n_yes_displacer / PRIMARY_N

    total_cost = sum(float(r.get("cost_usd") or 0) for r in rows)

    return {
        "meta": {
            "created_at": utc_now(),
            "prompt_version": PROMPT_VERSION,
            "prompt_template": JUDGE_USER_TEMPLATE,
            "provider": run_meta.get("provider"),
            "model": run_meta.get("model"),
            "judge_model_openai_default": JUDGE_MODEL_OPENAI,
            "displaced_M_full": n_displaced,
            "displaced_M_judged": len(meta.get("displaced_eval_ids") or []),
            "category_counts_planned": meta.get("category_counts"),
            "cache_path": str(CACHE_PATH.relative_to(ROOT)),
        },
        "category_summaries": by_cat,
        "comparisons": {
            "displacer_vs_competitor5k_mcnemar": paired,
            "displacer_yes_plus_partial": by_cat["displacer"]["yes_plus_partial_share"],
            "competitor5k_yes_plus_partial": by_cat["competitor5k"]["yes_plus_partial_share"],
            "random_control_yes_plus_partial": by_cat["random_control"]["yes_plus_partial_share"],
        },
        "calibration": {
            "gold_control_yes_share": by_cat["gold_control"].get("yes_share"),
            "gold_control_yes_wilson95": by_cat["gold_control"].get("yes_wilson95"),
        },
        "label_incompleteness": {
            "displaced_questions_with_yes_displacer": n_yes_displacer,
            "upper_bound_hit10_drop_attributable": round(label_bound, 4),
            "denominator_primary_bank": PRIMARY_N,
            "caveat": "Only the top non-gold displacer per displaced question was judged.",
        },
        "usage": {
            "judgments_in_cache": len(rows),
            "total_cost_usd_cached": round(total_cost, 4),
            "last_run": run_meta,
        },
        "judgments": [
            {
                "item_id": r["item_id"],
                "opaque_id": r.get("opaque_id"),
                "category": r["category"],
                "eval_id": r["eval_id"],
                "doc_id": r["doc_id"],
                "answers": r["answers"],
                "reason": r.get("reason"),
                "input_tokens": r.get("input_tokens"),
                "output_tokens": r.get("output_tokens"),
                "cost_usd": r.get("cost_usd"),
            }
            for r in sorted(rows, key=lambda x: x.get("opaque_id") or x["item_id"])
        ],
    }


def write_md(report: dict[str, Any]) -> str:
    m = report["meta"]
    lines = [
        "# LLM displacement relevance audit (revision 1, G3)",
        "",
        f"Generated: {m['created_at']}",
        "",
        "## Setup",
        f"- Provider: `{m.get('provider')}`; model: `{m.get('model')}`",
        f"- Displaced |M| (full): **{m['displaced_M_full']}**; judged sample: **{m['displaced_M_judged']}**",
        f"- Planned items: `{json.dumps(m['category_counts_planned'])}`",
        "",
        "## Prompt template",
        "```",
        m["prompt_template"],
        "```",
        "",
        "## Category relevance (Wilson 95% on yes+partial unless noted)",
        "",
        "| category | n | yes | partial | no | yes+partial share | Wilson 95% |",
        "| --- | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for cat, s in report["category_summaries"].items():
        c = s["counts"]
        wi = s["yes_plus_partial_wilson95"]
        lines.append(
            f"| {cat} | {s['n']} | {c['yes']} | {c['partial']} | {c['no']} | "
            f"{s['yes_plus_partial_share']} | {wi[0]}–{wi[1]} |"
        )
    lines += [
        "",
        "## Comparisons",
        f"- Displacer yes+partial: **{report['comparisons']['displacer_yes_plus_partial']}**",
        f"- Competitor@5k yes+partial: **{report['comparisons']['competitor5k_yes_plus_partial']}**",
        f"- Random control yes+partial: **{report['comparisons']['random_control_yes_plus_partial']}**",
        f"- McNemar paired: `{json.dumps(report['comparisons']['displacer_vs_competitor5k_mcnemar'])}`",
        "",
        "## Calibration (gold control)",
        f"- Gold `yes` share: **{report['calibration']['gold_control_yes_share']}** "
        f"(Wilson {report['calibration']['gold_control_yes_wilson95']})",
        "",
        "## Label incompleteness bound",
        f"- Displaced with displacer judged `yes`: **{report['label_incompleteness']['displaced_questions_with_yes_displacer']}**",
        f"- Hit@10 drop bound (yes displacers / 200): **{report['label_incompleteness']['upper_bound_hit10_drop_attributable']}**",
        f"- Caveat: {report['label_incompleteness']['caveat']}",
        "",
        f"Total cached spend (USD): {report['usage']['total_cost_usd_cached']}",
    ]
    return "\n".join(lines) + "\n"


def save_plan_snapshot(items: list[AuditItem], plan_meta: dict[str, Any]) -> None:
    PLAN_PATH.parent.mkdir(parents=True, exist_ok=True)
    PLAN_PATH.write_text(
        json.dumps(
            {
                "saved_at": utc_now(),
                "prompt_version": PROMPT_VERSION,
                "meta": plan_meta,
                "items": [
                    {
                        "item_id": it.item_id,
                        "category": it.category,
                        "eval_id": it.eval_id,
                        "doc_id": it.doc_id,
                    }
                    for it in items
                ],
            },
            indent=2,
            ensure_ascii=True,
        )
        + "\n",
        encoding="utf-8",
    )


def load_plan_snapshot() -> tuple[list[str], dict[str, Any]] | None:
    if not PLAN_PATH.exists():
        return None
    obj = json.loads(PLAN_PATH.read_text(encoding="utf-8"))
    if obj.get("prompt_version") != PROMPT_VERSION:
        return None
    item_ids = [r["item_id"] for r in obj.get("items") or []]
    return item_ids, obj.get("meta") or {}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--provider", choices=("openai", "cursor", "mock"), default="mock")
    parser.add_argument("--model", default=JUDGE_MODEL_OPENAI)
    parser.add_argument("--max-usd", type=float, default=4.0)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--analyze", action="store_true")
    parser.add_argument("--workspace", type=Path, default=ROOT)
    args = parser.parse_args()

    plan_meta: dict[str, Any]
    items: list[AuditItem]

    snap = load_plan_snapshot() if args.analyze else None
    if snap is not None:
        _, plan_meta = snap
        items = []
        tokenizer = None
    else:
        tokenizer = Tokenizer.load()
        if args.provider != "mock" and tokenizer.enc is None:
            print("note: tiktoken unavailable; truncating judge input with the stored per-document token counts / chars-per-token estimate", flush=True)
        q5, q100 = load_ladder_raw()
        questions = load_questions()
        rng_d = np.random.default_rng(SEED_ITEMS)
        rng_g = np.random.default_rng(SEED_GOLD)
        rng_r = np.random.default_rng(SEED_RANDOM)
        items, plan_meta = build_plan(q5, q100, questions, rng_d, rng_g, rng_r, tokenizer)

    if args.dry_run:
        run_dry(items, plan_meta)
        save_plan_snapshot(items, plan_meta)
        return 0

    run_meta = {
        "provider": args.provider,
        "model": args.model,
        "dry_run": False,
        "analyze_only": bool(args.analyze),
    }

    if args.analyze:
        cache = load_cache()
        expected = len(snap[0]) if snap else len(items)
        if len(cache) < expected:
            print(f"warning: cache has {len(cache)}/{expected} judgments", file=sys.stderr)
        report = analyze(cache, plan_meta, run_meta)
        OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
        OUT_JSON.write_text(json.dumps(report, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
        OUT_MD.write_text(write_md(report), encoding="utf-8")
        print(json.dumps({"wrote": [str(OUT_JSON), str(OUT_MD)], "displaced_M": plan_meta["displaced_count_full"]}, indent=2))
        return 0

    if not items:
        raise SystemExit("internal: missing plan items for judging run")

    save_plan_snapshot(items, plan_meta)
    run_meta.update(run_judging(items, plan_meta, args.provider, args.model, args.max_usd, args.workspace))
    cache = load_cache()
    report = analyze(cache, plan_meta, run_meta)
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(report, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    OUT_MD.write_text(write_md(report), encoding="utf-8")
    print(
        json.dumps(
            {
                "|M|": plan_meta["displaced_count_full"],
                "category_counts": plan_meta["category_counts"],
                "judgments_new": run_meta.get("judgments_new"),
                "judgments_cached": run_meta.get("judgments_cached"),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
