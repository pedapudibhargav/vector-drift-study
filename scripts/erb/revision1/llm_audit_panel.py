#!/usr/bin/env python3
"""Second-round LLM relevance audit panel (revision 1, task G6).

Multi-judge harness with stricter rubric, quote verification, and mock self-tests.
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
from collections import defaultdict
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
FROZEN_PLAN_PATH = DATA / "llm_audit_plan_gpt4o.json"
PRIMARY200_PATH = ROOT / "artifacts" / "published" / "primary_questions_200.json"
OUT_JSON = REV1 / "llm_audit_panel.json"
OUT_MD = REV1 / "llm_audit_panel.md"
TIKTOKEN_CACHE = DATA / "tiktoken_cache"
TOKEN_CUTS_PATH = DATA / "rev1_doc_token_cuts.jsonl"

PROMPT_VERSION = "rev1-audit-panel-v2"
RUBRIC_INSTRUCTIONS = (
    "A document FULLY ANSWERS the question only if every part of the question can be answered "
    "from the document alone. It PARTIALLY answers if it contains some but not all of what is "
    "needed, or only background. It does NOT answer if it is about something else or lacks the "
    "requested information. First think step by step in at most 80 words. Then give a verdict. "
    "You must quote, verbatim and in double quotes, the single sentence or phrase from the document "
    "that best supports your verdict; if there is none, write the empty string and the verdict must "
    'be \'no\'. Respond with JSON only: {"reasoning": "...", "quote": "...", "verdict": "full" | '
    '"partial" | "no"}.'
)

JUDGE_USER_PREFIX = """You are a strict relevance judge for enterprise RAG evaluation.

Question:
{question}

Document (standalone; no metadata beyond this text):
{document}

"""

MAX_DOC_TOKENS = 6000
SEED_ORDER = 42
SEED_NEAR_MISS = 42
NEAR_MISS_N = 20
GOLD_N = 15
RANDOM_N = 10
PRIMARY_N = 200

CATEGORY_FORBIDDEN = re.compile(
    r"(displacer|competitor5k|gold_control|random_control|near_miss)",
    re.IGNORECASE,
)
CORPUS_SIZE_FORBIDDEN = re.compile(r"\b(?:5000|100000|100k)\b", re.IGNORECASE)

Category = Literal["displacer", "competitor5k", "gold_control", "random_control", "near_miss"]
Verdict = Literal["full", "partial", "no", "unsupported", "invalid"]

LEGACY_ANSWER_MAP = {"yes": "full", "partial": "partial", "no": "no"}


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


def load_ladder_raw() -> dict[str, dict]:
    ladder = json.loads(LADDER_PATH.read_text(encoding="utf-8"))
    for run in ladder.get("runs") or []:
        if run.get("condition") == "raw" and int(run["scale"]) == 100000:
            return {pq["question_id"]: pq for pq in run.get("per_question") or []}
    raise SystemExit("ladder missing raw run at 100000")


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


def normalize_ws(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip()).casefold()


def quote_in_document(quote: str, document: str) -> bool:
    if not quote:
        return False
    return normalize_ws(quote) in normalize_ws(document)


def assert_blinding(prompt: str, eval_id: str, doc_id: str) -> None:
    """Judge must not see category labels, ladder sizes, eval/doc ids (document body excluded for organic text)."""
    doc_marker = "Document (standalone; no metadata beyond this text):"
    doc_pos = prompt.find(doc_marker)
    if doc_pos < 0:
        header_and_question = prompt
        tail_after_doc = ""
    else:
        header_and_question = prompt[:doc_pos]
        after = prompt[doc_pos + len(doc_marker) :]
        rubric_pos = after.find(RUBRIC_INSTRUCTIONS[:32])
        tail_after_doc = after[rubric_pos:] if rubric_pos >= 0 else ""
    harness_visible = header_and_question + tail_after_doc
    if CATEGORY_FORBIDDEN.search(harness_visible):
        raise AssertionError("blinding check failed: category name in prompt framing")
    if CORPUS_SIZE_FORBIDDEN.search(harness_visible):
        raise AssertionError("blinding check failed: corpus size token in prompt framing")
    q_start = harness_visible.find("Question:")
    q_end = harness_visible.find(doc_marker) if doc_marker in harness_visible else len(harness_visible)
    question_block = harness_visible[q_start:q_end] if q_start >= 0 else ""
    if eval_id and eval_id in question_block:
        raise AssertionError("blinding check failed: eval_id in question block")
    if doc_id and doc_id in prompt:
        raise AssertionError("blinding check failed: doc_id in prompt")


@dataclass
class AuditItem:
    item_id: str
    category: Category
    eval_id: str
    doc_id: str
    question: str
    document_trunc: str
    prompt: str
    prompt_tokens_est: int
    near_miss_donor_eval_id: str | None = None


def parse_judge_json(text: str) -> dict[str, str]:
    text = (text or "").strip()
    try:
        obj = json.loads(text)
    except json.JSONDecodeError as e:
        raise ValueError(f"invalid JSON: {e}") from e
    if not isinstance(obj, dict):
        raise ValueError("response must be a JSON object")
    reasoning = obj.get("reasoning")
    quote = obj.get("quote")
    verdict = obj.get("verdict")
    if not isinstance(reasoning, str):
        raise ValueError("reasoning must be a string")
    if quote is None:
        raise ValueError("quote must be present")
    if not isinstance(quote, str):
        raise ValueError("quote must be a string")
    if not isinstance(verdict, str):
        raise ValueError("verdict must be a string")
    verdict_l = verdict.lower().strip()
    if verdict_l not in ("full", "partial", "no"):
        raise ValueError(f"invalid verdict: {verdict!r}")
    if verdict_l in ("full", "partial") and not quote.strip():
        raise ValueError("full/partial requires non-empty quote")
    if not quote.strip() and verdict_l != "no":
        raise ValueError("empty quote requires verdict no")
    return {"reasoning": reasoning[:2000], "quote": quote[:2000], "verdict": verdict_l}


def apply_quote_verification(parsed: dict[str, str], document: str) -> tuple[str, bool]:
    v = parsed["verdict"]
    q = parsed["quote"]
    if v in ("full", "partial"):
        if not quote_in_document(q, document):
            return "unsupported", True
    return v, False


def load_frozen_plan_specs() -> tuple[list[dict], dict[str, Any]]:
    plan = json.loads(FROZEN_PLAN_PATH.read_text(encoding="utf-8"))
    items = plan.get("items") or []
    meta = dict(plan.get("meta") or {})
    gold_seen = 0
    random_seen = 0
    picked: list[dict] = []
    for row in items:
        cat = row["category"]
        if cat in ("displacer", "competitor5k"):
            picked.append(row)
        elif cat == "gold_control":
            if gold_seen < GOLD_N:
                picked.append(row)
                gold_seen += 1
        elif cat == "random_control":
            if random_seen < RANDOM_N:
                picked.append(row)
                random_seen += 1
    return picked, meta


def build_near_miss_specs(
    q100: dict[str, dict],
    questions: dict[str, dict],
    primary_ids: list[str],
    rng: np.random.Generator,
) -> list[dict]:
    hit_primary = [qid for qid in primary_ids if qid in q100 and q100[qid].get("hit_at_10")]
    primary_set = set(primary_ids)
    by_type_st: dict[tuple[str, str], list[str]] = defaultdict(list)
    for qid in primary_ids:
        if qid not in primary_set or qid not in questions:
            continue
        q = questions[qid]
        key = (q["question_type"], q["source_types"][0])
        by_type_st[key].append(qid)
    for key in by_type_st:
        by_type_st[key] = sorted(by_type_st[key])

    eligible_anchors = [
        qid
        for qid in hit_primary
        if len([d for d in by_type_st.get((questions[qid]["question_type"], questions[qid]["source_types"][0]), []) if d != qid])
        > 0
    ]
    if len(eligible_anchors) < NEAR_MISS_N:
        raise SystemExit(
            f"only {len(eligible_anchors)} near_miss-eligible primary-200 hit@10@100k, need {NEAR_MISS_N}"
        )
    pool = np.array(sorted(eligible_anchors))
    anchor_ids = sorted(rng.choice(pool, size=NEAR_MISS_N, replace=False).tolist())

    specs: list[dict] = []
    for eval_id in anchor_ids:
        q = questions[eval_id]
        key = (q["question_type"], q["source_types"][0])
        donors = [d for d in by_type_st.get(key, []) if d != eval_id]
        donor = str(rng.choice(donors))
        gold_d = set(questions[donor]["expected_doc_ids"])
        ret = q100[donor].get("retrieved_doc_ids") or []
        doc_id = first_non_gold(ret, gold_d)
        if not doc_id:
            raise SystemExit(f"near_miss: no top non-gold for donor {donor}")
        item_id = stable_item_id("near_miss", eval_id, doc_id)
        specs.append(
            {
                "item_id": item_id,
                "category": "near_miss",
                "eval_id": eval_id,
                "doc_id": doc_id,
                "near_miss_donor_eval_id": donor,
            }
        )
    return specs


def build_items(tokenizer: Tokenizer) -> tuple[list[AuditItem], dict[str, Any]]:
    frozen, frozen_meta = load_frozen_plan_specs()
    q100 = load_ladder_raw()
    questions = load_questions()
    primary_ids = json.loads(PRIMARY200_PATH.read_text(encoding="utf-8")).get("question_ids") or []
    rng = np.random.default_rng(SEED_NEAR_MISS)
    near_specs = build_near_miss_specs(q100, questions, primary_ids, rng)

    all_specs: list[dict] = []
    for row in frozen:
        all_specs.append(
            {
                "item_id": row["item_id"],
                "category": row["category"],
                "eval_id": row["eval_id"],
                "doc_id": row["doc_id"],
                "near_miss_donor_eval_id": None,
            }
        )
    all_specs.extend(near_specs)

    doc_ids = sorted({s["doc_id"] for s in all_specs})
    conn = pg_connect()
    texts: dict[str, str] = {}
    with conn.cursor() as cur:
        for i in range(0, len(doc_ids), 500):
            batch = doc_ids[i : i + 500]
            cur.execute(
                "SELECT doc_id, chunk_text FROM document_chunks WHERE doc_id = ANY(%s)",
                (batch,),
            )
            for did, chunk_text in cur.fetchall():
                texts[str(did)] = chunk_text or ""
    conn.close()
    missing = [d for d in doc_ids if d not in texts]
    if missing:
        raise SystemExit(f"missing chunk_text for {len(missing)} docs")

    items: list[AuditItem] = []
    for spec in all_specs:
        eval_id = spec["eval_id"]
        doc_id = spec["doc_id"]
        category: Category = spec["category"]
        question = questions[eval_id]["question"]
        body, _ = tokenizer.truncate_chunk(texts[doc_id], doc_id, MAX_DOC_TOKENS)
        prompt = JUDGE_USER_PREFIX.format(question=question, document=body) + RUBRIC_INSTRUCTIONS
        assert_blinding(prompt, eval_id, doc_id)
        items.append(
            AuditItem(
                item_id=spec["item_id"],
                category=category,
                eval_id=eval_id,
                doc_id=doc_id,
                question=question,
                document_trunc=body,
                prompt=prompt,
                prompt_tokens_est=tokenizer.count_text(prompt, None),
                near_miss_donor_eval_id=spec.get("near_miss_donor_eval_id"),
            )
        )

    counts: dict[str, int] = defaultdict(int)
    for it in items:
        counts[it.category] += 1
    meta = {
        "displaced_count_full": frozen_meta.get("displaced_count_full"),
        "displaced_eval_ids": frozen_meta.get("displaced_eval_ids"),
        "category_counts": dict(counts, total=len(items)),
        "near_miss_anchor_eval_ids": [s["eval_id"] for s in near_specs],
        "frozen_plan": str(FROZEN_PLAN_PATH.relative_to(ROOT)),
        "tokenizer": "tiktoken_cl100k_base" if tokenizer.enc is not None else "tiktoken_cuts_fallback",
    }
    return items, meta


def cache_path_for_judge(judge_name: str) -> Path:
    return DATA / f"llm_audit_panel_cache_{judge_name}.jsonl"


def load_cache(path: Path) -> dict[str, dict]:
    if not path.exists():
        return {}
    out: dict[str, dict] = {}
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                row = json.loads(line)
                out[str(row["item_id"])] = row
    return out


def append_cache(path: Path, row: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=True) + "\n")


def order_items(items: list[AuditItem]) -> list[tuple[AuditItem, str]]:
    rng = np.random.default_rng(SEED_ORDER)
    idx = np.arange(len(items))
    rng.shuffle(idx)
    ordered: list[tuple[AuditItem, str]] = []
    for i, pos in enumerate(idx):
        it = items[int(pos)]
        ordered.append((it, opaque_id(it.item_id, i)))
    return ordered


def mock_response(
    item: AuditItem,
    mode: str = "normal",
) -> str:
    if mode == "invalid_json":
        return "not json at all"
    if mode == "bad_quote":
        return json.dumps(
            {
                "reasoning": "fabricated support",
                "quote": "this phrase does not appear in the document at all",
                "verdict": "full",
            }
        )
    h = int(hashlib.sha256(f"{item.category}|{item.item_id}".encode()).hexdigest(), 16)
    if item.category == "gold_control":
        verdict = "full" if h % 4 else "partial"
    elif item.category in ("random_control", "near_miss"):
        verdict = "no" if h % 3 == 0 else ("partial" if h % 3 == 1 else "no")
    else:
        verdict = ["full", "partial", "no"][h % 3]
    quote = ""
    if verdict in ("full", "partial"):
        words = (item.document_trunc or "").split()
        quote = " ".join(words[:12]) if words else ""
        if not quote:
            verdict = "no"
    return json.dumps({"reasoning": f"mock {verdict}", "quote": quote, "verdict": verdict})


def cursor_judge(prompt: str, workspace: Path, model: str, timeout: int) -> str:
    cmd = [
        "cursor-agent",
        "-p",
        "--mode",
        "ask",
        "--sandbox",
        "enabled",
        "--trust",
        "--model",
        model,
        "--workspace",
        str(workspace),
        prompt,
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, check=False)
    if proc.returncode != 0:
        raise RuntimeError(f"cursor-agent failed: {proc.stderr[:500]}")
    return proc.stdout


OPENAI_PRICE_IN = 2.00 / 1e6   # USD per input token (third-party reported; unverified)
OPENAI_PRICE_OUT = 12.00 / 1e6  # USD per output token (reasoning tokens billed as output)
OPENAI_STATE: dict[str, Any] = {"usd": 0.0, "cap": 3.0, "effort": "medium", "calls": 0}


def openai_judge(prompt: str, model: str, timeout: int) -> str:
    import urllib.request

    if OPENAI_STATE["usd"] >= OPENAI_STATE["cap"]:
        raise SystemExit(f"OpenAI spend cap reached: {OPENAI_STATE['usd']:.3f} USD")
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        raise SystemExit("OPENAI_API_KEY not set")
    body = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "reasoning_effort": OPENAI_STATE["effort"],
        "max_completion_tokens": 8000,
    }
    req = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=json.dumps(body).encode(),
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            d = json.loads(r.read())
    except Exception as e:  # noqa: BLE001
        raise RuntimeError(f"openai call failed: {str(e)[:300]}") from None
    u = d.get("usage", {})
    cost = u.get("prompt_tokens", 0) * OPENAI_PRICE_IN + u.get("completion_tokens", 0) * OPENAI_PRICE_OUT
    OPENAI_STATE["usd"] += cost
    OPENAI_STATE["calls"] += 1
    with open(DATA / "llm_audit_panel_spend.jsonl", "a") as f:
        f.write(json.dumps({"t": utc_now(), "model": model, "usage": u, "usd": round(cost, 5),
                            "cum_usd": round(OPENAI_STATE["usd"], 4)}) + "\n")
    return d["choices"][0]["message"]["content"] or ""


def judge_once(
    provider: str,
    item: AuditItem,
    workspace: Path,
    cursor_model: str,
    timeout: int,
    mock_mode: str,
) -> str:
    if provider == "mock":
        return mock_response(item, mock_mode)
    if provider == "cursor":
        return cursor_judge(item.prompt, workspace, cursor_model, timeout)
    if provider == "openai":
        return openai_judge(item.prompt, cursor_model, timeout)
    raise SystemExit(f"unknown provider {provider!r}")


def process_response(raw: str, document: str) -> dict[str, Any]:
    try:
        parsed = parse_judge_json(raw)
    except ValueError as e:
        return {
            "verdict": "invalid",
            "reasoning": "",
            "quote": "",
            "raw_verdict": None,
            "quote_downgraded": False,
            "parse_error": str(e),
        }
    verdict, downgraded = apply_quote_verification(parsed, document)
    return {
        "verdict": verdict,
        "reasoning": parsed["reasoning"],
        "quote": parsed["quote"],
        "raw_verdict": parsed["verdict"],
        "quote_downgraded": downgraded,
        "parse_error": None,
    }


def run_judging(
    items: list[AuditItem],
    judge_name: str,
    provider: str,
    cursor_model: str,
    workspace: Path,
    max_calls: int,
    call_timeout: int,
    mock_mode: str = "normal",
) -> dict[str, Any]:
    cache_path = cache_path_for_judge(judge_name)
    cache = load_cache(cache_path)
    ordered = order_items(items)
    calls = 0
    n_new = 0
    n_skip_cached = 0
    invalid_n = 0
    quote_down_n = 0

    for it, opaque in ordered:
        if it.item_id in cache:
            n_skip_cached += 1
            continue
        if calls >= max_calls:
            print(f"stopped at --max-calls={max_calls}", file=sys.stderr)
            break
        raw = None
        result = None
        for attempt in range(2):
            try:
                raw = judge_once(provider, it, workspace, cursor_model, call_timeout, mock_mode)
                result = process_response(raw, it.document_trunc)
            except (ValueError, RuntimeError, subprocess.TimeoutExpired) as e:
                result = {
                    "verdict": "invalid",
                    "reasoning": "",
                    "quote": "",
                    "raw_verdict": None,
                    "quote_downgraded": False,
                    "parse_error": str(e),
                }
            calls += 1
            if result["verdict"] != "invalid":
                break
            invalid_n += 1
        if result is None:
            continue
        if result.get("quote_downgraded"):
            quote_down_n += 1
        row = {
            "item_id": it.item_id,
            "opaque_id": opaque,
            "category": it.category,
            "eval_id": it.eval_id,
            "doc_id": it.doc_id,
            "verdict": result["verdict"],
            "raw_verdict": result.get("raw_verdict"),
            "reasoning": result.get("reasoning"),
            "quote": result.get("quote"),
            "quote_downgraded": result.get("quote_downgraded"),
            "parse_error": result.get("parse_error"),
            "provider": provider,
            "judge_name": judge_name,
            "cursor_model": cursor_model if provider in ("cursor", "openai") else None,
            "prompt_version": PROMPT_VERSION,
            "judged_at": utc_now(),
        }
        append_cache(cache_path, row)
        cache[it.item_id] = row
        n_new += 1

    return {
        "judge_name": judge_name,
        "provider": provider,
        "cursor_model": cursor_model,
        "items_total": len(items),
        "judgments_new": n_new,
        "judgments_cached": n_skip_cached,
        "api_calls_session": calls,
        "invalid_session": invalid_n,
        "quote_downgraded_session": quote_down_n,
        "cache_path": str(cache_path.relative_to(ROOT)),
    }


def load_extra_caches(entries: list[str]) -> dict[str, dict[str, dict]]:
    out: dict[str, dict[str, dict]] = {}
    for entry in entries:
        if "=" not in entry:
            raise SystemExit(f"--extra-cache must be name=path, got {entry!r}")
        name, rel = entry.split("=", 1)
        path = Path(rel) if Path(rel).is_absolute() else ROOT / rel
        cache = load_cache(path)
        mapped: dict[str, dict] = {}
        for iid, row in cache.items():
            leg = str(row.get("answers") or row.get("verdict") or "no").lower()
            verdict = LEGACY_ANSWER_MAP.get(leg, leg if leg in ("full", "partial", "no") else "no")
            mapped[iid] = {**row, "verdict": verdict, "judge_name": name}
        out[name] = mapped
    return out


def is_relevant(verdict: str) -> bool:
    return verdict in ("full", "partial")


def cohens_kappa(a: list[bool], b: list[bool]) -> float | None:
    if len(a) != len(b) or not a:
        return None
    n = len(a)
    agree = sum(1 for x, y in zip(a, b) if x == y)
    po = agree / n
    p_a = sum(a) / n
    p_b = sum(b) / n
    pe = p_a * p_b + (1 - p_a) * (1 - p_b)
    if abs(1 - pe) < 1e-12:
        return 1.0
    return (po - pe) / (1 - pe)


def category_verdict_stats(rows: list[dict]) -> dict[str, Any]:
    labels = ("full", "partial", "no", "unsupported", "invalid")
    n = len(rows)
    counts = {lb: 0 for lb in labels}
    quote_down = 0
    for r in rows:
        v = str(r.get("verdict") or "invalid")
        if v not in counts:
            v = "invalid"
        counts[v] += 1
        if r.get("quote_downgraded"):
            quote_down += 1
    shares = {k: (v / n if n else None) for k, v in counts.items()}
    wilson: dict[str, list] = {}
    for lb in labels:
        lo, hi = wilson_ci(counts[lb], n) if n else (None, None)
        wilson[lb] = [round(lo, 4) if lo is not None else None, round(hi, 4) if hi is not None else None]
    rel_k = counts["full"] + counts["partial"]
    rlo, rhi = wilson_ci(rel_k, n) if n else (None, None)
    return {
        "n": n,
        "counts": counts,
        "shares": {k: round(v, 4) if v is not None else None for k, v in shares.items()},
        "wilson95_by_verdict": wilson,
        "full_or_partial_share": round(rel_k / n, 4) if n else None,
        "full_or_partial_wilson95": [round(rlo, 4) if rlo is not None else None, round(rhi, 4) if rhi is not None else None],
        "quote_downgraded_count": quote_down,
    }


def analyze_multi(
    items: list[AuditItem],
    judge_caches: dict[str, dict[str, dict]],
    plan_meta: dict[str, Any],
    run_metas: list[dict[str, Any]],
) -> dict[str, Any]:
    item_by_id = {it.item_id: it for it in items}
    categories = ("displacer", "competitor5k", "gold_control", "random_control", "near_miss")
    item_ids = {it.item_id for it in items}
    displaced_eval_ids = set(plan_meta.get("displaced_eval_ids") or [])

    per_judge: dict[str, Any] = {}
    for jname, cache in judge_caches.items():
        by_cat: dict[str, Any] = {}
        for cat in categories:
            rows = [cache[iid] for iid in item_ids if iid in cache and item_by_id[iid].category == cat]
            by_cat[cat] = category_verdict_stats(rows)
        cal = {
            "gold_control_full_or_partial": by_cat["gold_control"]["full_or_partial_share"],
            "gold_control_wilson95": by_cat["gold_control"]["full_or_partial_wilson95"],
            "random_control_full_or_partial": by_cat["random_control"]["full_or_partial_share"],
            "near_miss_full_or_partial": by_cat["near_miss"]["full_or_partial_share"],
        }
        displacer_full = sum(
            1
            for it in items
            if it.category == "displacer" and it.item_id in cache and cache[it.item_id].get("verdict") == "full"
        )
        comp_full = sum(
            1
            for it in items
            if it.category == "competitor5k" and it.item_id in cache and cache[it.item_id].get("verdict") == "full"
        )
        per_judge[jname] = {
            "by_category": by_cat,
            "calibration": cal,
            "displacer_full_count": displacer_full,
            "displacer_full_over_primary200": round(displacer_full / PRIMARY_N, 4),
            "competitor5k_full_count": comp_full,
            "competitor5k_full_over_primary200": round(comp_full / PRIMARY_N, 4),
            "judgments_in_cache": len([i for i in item_ids if i in cache]),
            "quote_downgraded_total": sum(
                1 for i in item_ids if i in cache and cache[i].get("quote_downgraded")
            ),
        }

    judge_names = list(judge_caches.keys())
    pairwise: list[dict[str, Any]] = []
    for i in range(len(judge_names)):
        for j in range(i + 1, len(judge_names)):
            a_name, b_name = judge_names[i], judge_names[j]
            a_cache, b_cache = judge_caches[a_name], judge_caches[b_name]
            shared = sorted(item_ids & set(a_cache) & set(b_cache))
            rel_a = [is_relevant(str(a_cache[i]["verdict"])) for i in shared]
            rel_b = [is_relevant(str(b_cache[i]["verdict"])) for i in shared]
            full_a = [str(a_cache[i]["verdict"]) == "full" for i in shared]
            full_b = [str(b_cache[i]["verdict"]) == "full" for i in shared]
            agree_rel = sum(1 for x, y in zip(rel_a, rel_b) if x == y) / len(shared) if shared else None
            agree_full = sum(1 for x, y in zip(full_a, full_b) if x == y) / len(shared) if shared else None
            pairwise.append(
                {
                    "judges": [a_name, b_name],
                    "n_shared": len(shared),
                    "agreement_full_or_partial": round(agree_rel, 4) if agree_rel is not None else None,
                    "kappa_full_or_partial": round(cohens_kappa(rel_a, rel_b), 4)
                    if cohens_kappa(rel_a, rel_b) is not None
                    else None,
                    "agreement_full": round(agree_full, 4) if agree_full is not None else None,
                    "kappa_full": round(cohens_kappa(full_a, full_b), 4)
                    if cohens_kappa(full_a, full_b) is not None
                    else None,
                }
            )

    displacer_items = [it for it in items if it.category == "displacer"]
    majority: dict[str, Any] = {}
    n_judges = len(judge_names)
    if n_judges:
        full_votes_by_q: dict[str, list[bool]] = defaultdict(list)
        for it in displacer_items:
            for jn in judge_names:
                if it.item_id in judge_caches[jn]:
                    full_votes_by_q[it.eval_id].append(judge_caches[jn][it.item_id].get("verdict") == "full")
        n_half = sum(1 for votes in full_votes_by_q.values() if sum(votes) >= math.ceil(n_judges / 2))
        comp_items = [it for it in items if it.category == "competitor5k"]
        comp_votes: dict[str, list[bool]] = defaultdict(list)
        for it in comp_items:
            for jn in judge_names:
                if it.item_id in judge_caches[jn]:
                    comp_votes[it.eval_id].append(judge_caches[jn][it.item_id].get("verdict") == "full")
        n_comp_half = sum(1 for votes in comp_votes.values() if sum(votes) >= math.ceil(n_judges / 2))
        majority = {
            "judges_considered": judge_names,
            "displaced_questions_with_displacer_full_majority": n_half,
            "upper_bound_hit10_drop_attributable": round(n_half / PRIMARY_N, 4),
            "displaced_questions_with_competitor5k_full_majority": n_comp_half,
            "competitor5k_full_majority_over_primary200": round(n_comp_half / PRIMARY_N, 4),
            "denominator_primary_bank": PRIMARY_N,
            "displaced_M_full": len(displaced_eval_ids),
        }

    total_calls = sum(int(m.get("api_calls_session") or 0) for m in run_metas)

    return {
        "meta": {
            "created_at": utc_now(),
            "prompt_version": PROMPT_VERSION,
            "rubric": RUBRIC_INSTRUCTIONS,
            "category_counts_planned": plan_meta.get("category_counts"),
            "displaced_M_full": plan_meta.get("displaced_count_full"),
            "judges": judge_names,
            "run_metas": run_metas,
        },
        "per_judge": per_judge,
        "pairwise_agreement": pairwise,
        "displacer_majority_vote": majority,
        "harness": {
            "total_api_calls_reported": total_calls,
        },
        "judgments": [
            {
                "item_id": it.item_id,
                "category": it.category,
                "eval_id": it.eval_id,
                "doc_id": it.doc_id,
                **{
                    jn: judge_caches[jn].get(it.item_id, {}).get("verdict")
                    for jn in judge_names
                },
            }
            for it in sorted(items, key=lambda x: x.item_id)
        ],
    }


def write_md(report: dict[str, Any]) -> str:
    m = report["meta"]
    lines = [
        "# LLM audit panel (revision 1, G6)",
        "",
        f"Generated: {m['created_at']}",
        "",
        "## Rubric",
        "",
        m["rubric"],
        "",
        "## Models / judges",
        "",
        f"Judges: `{', '.join(m['judges'])}`",
        "",
        f"Planned items: `{json.dumps(m['category_counts_planned'])}`",
        "",
        "## Per-judge category shares (Wilson 95% per verdict label)",
        "",
    ]
    for jname, block in report["per_judge"].items():
        lines.append(f"### Judge `{jname}`")
        lines.append("")
        lines.append(
            f"- API judgments in cache: {block['judgments_in_cache']}; "
            f"quote downgrades: {block['quote_downgraded_total']}"
        )
        lines.append(
            f"- Displacer `full` count: {block['displacer_full_count']} "
            f"({block['displacer_full_over_primary200']} / 200)"
        )
        lines.append("")
        lines.append("| category | n | full | partial | no | unsupported | invalid | full+partial | Wilson |")
        lines.append("| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |")
        for cat, s in block["by_category"].items():
            c = s["counts"]
            wi = s["full_or_partial_wilson95"]
            lines.append(
                f"| {cat} | {s['n']} | {c['full']} | {c['partial']} | {c['no']} | "
                f"{c['unsupported']} | {c['invalid']} | {s['full_or_partial_share']} | {wi[0]}–{wi[1]} |"
            )
        cal = block["calibration"]
        lines.append("")
        lines.append(
            f"- Calibration gold full+partial: **{cal['gold_control_full_or_partial']}** "
            f"(Wilson {cal['gold_control_wilson95']})"
        )
        lines.append(f"- Random control full+partial: **{cal['random_control_full_or_partial']}**")
        lines.append(f"- Near-miss control full+partial: **{cal['near_miss_full_or_partial']}**")
        lines.append("")

    lines += ["## Pairwise agreement", ""]
    for p in report.get("pairwise_agreement") or []:
        lines.append(f"- `{p['judges']}`: n={p['n_shared']}, κ(full±partial)={p['kappa_full_or_partial']}, κ(full)={p['kappa_full']}")

    maj = report.get("displacer_majority_vote") or {}
    lines += [
        "",
        "## Displacer majority (`full` by ≥ half of judges)",
        "",
        f"- Count: **{maj.get('displaced_questions_with_displacer_full_majority')}** / displaced M={maj.get('displaced_M_full')}",
        f"- Upper bound on Hit@10 drop (÷200): **{maj.get('upper_bound_hit10_drop_attributable')}**",
        "",
        f"Total API calls (session metas): {report['harness']['total_api_calls_reported']}",
    ]
    return "\n".join(lines) + "\n"


def run_dry(items: list[AuditItem], meta: dict[str, Any], max_calls: int) -> None:
    print("=== dry-run ===")
    print(json.dumps(meta["category_counts"], indent=2))
    print(f"estimated_calls={min(len(items), max_calls)} (items={len(items)}, max_calls={max_calls})")
    for i, it in enumerate(items[:2]):
        print(f"\n--- prompt {i + 1} (category hidden from judge) ---\n")
        print(it.prompt[:2500] + ("…" if len(it.prompt) > 2500 else ""))


def run_self_tests(items: list[AuditItem], judge_name: str) -> dict[str, Any]:
    results: dict[str, Any] = {}
    sample = items[0]

    try:
        assert_blinding(sample.prompt, sample.eval_id, sample.doc_id)
        results["blinding"] = "PASS"
    except AssertionError as e:
        results["blinding"] = f"FAIL: {e}"

    bad = process_response(mock_response(sample, "bad_quote"), sample.document_trunc)
    results["bad_quote_caught"] = "PASS" if bad["verdict"] == "unsupported" and bad["quote_downgraded"] else "FAIL"
    results["bad_quote_verdict"] = bad["verdict"]

    inv = process_response(mock_response(sample, "invalid_json"), sample.document_trunc)
    results["invalid_json"] = "PASS" if inv["verdict"] == "invalid" else "FAIL"

    # schema: empty quote with full fails parse
    try:
        parse_judge_json(json.dumps({"reasoning": "x", "quote": "", "verdict": "full"}))
        results["schema_reject_empty_quote"] = "FAIL"
    except ValueError:
        results["schema_reject_empty_quote"] = "PASS"

    return results


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--provider", choices=("cursor", "mock", "openai"), default="mock")
    parser.add_argument("--cursor-model", default="composer-2.5")
    parser.add_argument("--judge-name", default="mock_a", help="Cache suffix llm_audit_panel_cache_<name>.jsonl")
    parser.add_argument("--max-calls", type=int, default=160)
    parser.add_argument("--max-usd", type=float, default=3.0)
    parser.add_argument("--effort", default="medium")
    parser.add_argument("--call-timeout", type=int, default=600)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--analyze", action="store_true")
    parser.add_argument("--judges", default="", help="Comma-separated judge names for --analyze")
    parser.add_argument("--extra-cache", action="append", default=[], help="name=path for legacy caches")
    parser.add_argument("--workspace", type=Path, default=ROOT)
    parser.add_argument("--self-test", action="store_true", help="Run harness unit checks (no API)")
    parser.add_argument(
        "--mock-mode",
        choices=("normal", "invalid_json", "bad_quote"),
        default="normal",
    )
    args = parser.parse_args()

    OPENAI_STATE["cap"] = args.max_usd
    OPENAI_STATE["effort"] = args.effort
    tokenizer = Tokenizer.load()
    items, plan_meta = build_items(tokenizer)

    if args.self_test:
        print(json.dumps(run_self_tests(items, args.judge_name), indent=2))
        return 0

    if args.dry_run:
        run_dry(items, plan_meta, args.max_calls)
        return 0

    run_meta: dict[str, Any] = {"provider": args.provider, "judge_name": args.judge_name}

    if args.analyze:
        judge_names = [j.strip() for j in args.judges.split(",") if j.strip()]
        if not judge_names:
            judge_names = [args.judge_name]
        judge_caches: dict[str, dict[str, dict]] = {}
        for jn in judge_names:
            judge_caches[jn] = load_cache(cache_path_for_judge(jn))
        judge_caches.update(load_extra_caches(args.extra_cache))
        report = analyze_multi(items, judge_caches, plan_meta, [])
        OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
        OUT_JSON.write_text(json.dumps(report, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
        OUT_MD.write_text(write_md(report), encoding="utf-8")
        print(json.dumps({"wrote": [str(OUT_JSON), str(OUT_MD)], "category_counts": plan_meta["category_counts"]}, indent=2))
        return 0

    run_meta.update(
        run_judging(
            items,
            args.judge_name,
            args.provider,
            args.cursor_model,
            args.workspace,
            args.max_calls,
            args.call_timeout,
            args.mock_mode,
        )
    )
    judge_caches = {args.judge_name: load_cache(cache_path_for_judge(args.judge_name))}
    report = analyze_multi(items, judge_caches, plan_meta, [run_meta])
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(report, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    OUT_MD.write_text(write_md(report), encoding="utf-8")
    print(
        json.dumps(
            {
                "category_counts": plan_meta["category_counts"],
                "judgments_new": run_meta.get("judgments_new"),
                "judgments_cached": run_meta.get("judgments_cached"),
                "api_calls": run_meta.get("api_calls_session"),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

