"""Append-only cost ledger for ERB embeddings and LLM judges."""

from __future__ import annotations

import json
import os
import threading
import time
from pathlib import Path
from typing import Any

# text-embedding-3-small and gpt-4o-mini list prices (USD / 1M tokens) as of study freeze.
PRICE_EMBED_PER_1M = 0.02
PRICE_GPT4O_MINI_IN_PER_1M = 0.15
PRICE_GPT4O_MINI_OUT_PER_1M = 0.60
# Hard stop for paid OpenAI spend (embeddings + judge). Ollama is $0 and uncapped.
BUDGET_CAP_USD = float(os.environ.get("ERB_BUDGET_CAP_USD", "5.50"))

_LOCK = threading.Lock()


def budget_ok(path: Path | None = None) -> bool:
    totals = load(path)["totals"]
    return float(totals.get("total_cost_usd") or 0) < BUDGET_CAP_USD


def assert_budget(path: Path | None = None) -> None:
    if not budget_ok(path):
        raise RuntimeError(
            f"ERB paid cost would exceed BUDGET_CAP_USD={BUDGET_CAP_USD}; "
            "halt OpenAI calls (Ollama arm may continue)"
        )


def default_path() -> Path:
    here = Path(__file__).resolve()
    for base in (here.parents[2], Path("/app")):
        candidate = base / "data" / "erb_cost_tracker.json"
        if base.exists():
            return candidate
    return Path("data/erb_cost_tracker.json")


def _empty() -> dict[str, Any]:
    return {
        "currency": "USD",
        "prices": {
            "embedding_per_1m": PRICE_EMBED_PER_1M,
            "gpt4o_mini_in_per_1m": PRICE_GPT4O_MINI_IN_PER_1M,
            "gpt4o_mini_out_per_1m": PRICE_GPT4O_MINI_OUT_PER_1M,
        },
        "totals": {
            "embed_tokens": 0,
            "judge_input_tokens": 0,
            "judge_output_tokens": 0,
            "embed_cost_usd": 0.0,
            "judge_cost_usd": 0.0,
            "total_cost_usd": 0.0,
        },
        "events": [],
    }


def load(path: Path | None = None) -> dict[str, Any]:
    p = path or default_path()
    if not p.exists():
        return _empty()
    return json.loads(p.read_text(encoding="utf-8"))


def _save(data: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2), encoding="utf-8")
    tmp.replace(path)


def record_embedding(
    *,
    tokens: int,
    docs: int,
    note: str = "",
    path: Path | None = None,
) -> dict[str, Any]:
    p = path or default_path()
    cost = tokens / 1_000_000.0 * PRICE_EMBED_PER_1M
    with _LOCK:
        data = load(p)
        data["totals"]["embed_tokens"] += int(tokens)
        data["totals"]["embed_cost_usd"] = round(
            data["totals"]["embed_tokens"] / 1_000_000.0 * PRICE_EMBED_PER_1M, 6
        )
        data["totals"]["total_cost_usd"] = round(
            data["totals"]["embed_cost_usd"] + data["totals"]["judge_cost_usd"], 6
        )
        data["events"].append(
            {
                "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "kind": "embedding",
                "tokens": int(tokens),
                "docs": int(docs),
                "cost_usd": round(cost, 6),
                "note": note,
            }
        )
        _save(data, p)
        return data["totals"]


def record_judge(
    *,
    input_tokens: int,
    output_tokens: int,
    note: str = "",
    path: Path | None = None,
) -> dict[str, Any]:
    p = path or default_path()
    cost = (
        input_tokens / 1_000_000.0 * PRICE_GPT4O_MINI_IN_PER_1M
        + output_tokens / 1_000_000.0 * PRICE_GPT4O_MINI_OUT_PER_1M
    )
    with _LOCK:
        data = load(p)
        data["totals"]["judge_input_tokens"] += int(input_tokens)
        data["totals"]["judge_output_tokens"] += int(output_tokens)
        data["totals"]["judge_cost_usd"] = round(
            data["totals"]["judge_input_tokens"] / 1_000_000.0 * PRICE_GPT4O_MINI_IN_PER_1M
            + data["totals"]["judge_output_tokens"] / 1_000_000.0 * PRICE_GPT4O_MINI_OUT_PER_1M,
            6,
        )
        data["totals"]["total_cost_usd"] = round(
            data["totals"]["embed_cost_usd"] + data["totals"]["judge_cost_usd"], 6
        )
        data["events"].append(
            {
                "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "kind": "judge",
                "input_tokens": int(input_tokens),
                "output_tokens": int(output_tokens),
                "cost_usd": round(cost, 6),
                "note": note,
            }
        )
        _save(data, p)
        return data["totals"]
