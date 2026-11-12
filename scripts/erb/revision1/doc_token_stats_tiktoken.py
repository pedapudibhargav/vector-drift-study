#!/usr/bin/env python3
"""Container helper: cl100k_base token counts and 8,191-token char cuts.

Reads JSONL from /work (Docker mount of worktree data/). Host has no tiktoken.
"""

from __future__ import annotations

import json
import os
import random
import sys
from pathlib import Path

INP = Path(os.environ.get("REV1_POOL", "/work/rev1_doc_pool.jsonl"))
OUT = Path(os.environ.get("REV1_CUTS", "/work/rev1_doc_token_cuts.jsonl"))
SPOT = Path(os.environ.get("REV1_SPOT", "/work/rev1_token_spot_check.json"))
MAX_TOK = 8191
SEED = 42
SPOT_N = 5


def get_enc():
    try:
        import tiktoken
    except ImportError:
        raise SystemExit(
            "tiktoken is not importable. Official tiktoken is required "
            "(Docker image vector-drift-research-vector-drift-api). "
            "No pure-Python fallback."
        ) from None
    return tiktoken.get_encoding("cl100k_base"), "tiktoken"


def combined_text(title: str | None, chunk_text: str | None) -> str:
    return f"{title or ''} {chunk_text or ''}"


def cut_char_for_tokens(enc, text: str, tokens: list[int]) -> tuple[int, str]:
    """Char offset of first min(len(tokens), 8191) tokens.

    Prefer decode(tokens[:8191]) when it is a prefix of text. Otherwise binary-search
    the longest prefix with <= 8191 tokens (tokenizer boundary).
    """
    n = len(tokens)
    if n <= MAX_TOK:
        return len(text), "full"
    prefix = enc.decode(tokens[:MAX_TOK])
    if text.startswith(prefix):
        return len(prefix), "decode_prefix"
    lo, hi = 0, len(text)
    while lo < hi:
        mid = (lo + hi + 1) // 2
        nt = len(enc.encode(text[:mid], disallowed_special=()))
        if nt <= MAX_TOK:
            lo = mid
        else:
            hi = mid - 1
    return lo, "binary_search"


def measure(enc, text: str) -> dict:
    tokens = enc.encode(text, disallowed_special=())
    cut, method = cut_char_for_tokens(enc, text, tokens)
    return {
        "chars": len(text),
        "tokens": len(tokens),
        "cut_char_8191": cut,
        "cut_method": method,
    }


def main() -> int:
    enc, enc_name = get_enc()
    print(f"encoder={enc_name}", flush=True)
    n_in = 0
    long_ids: list[str] = []
    with INP.open(encoding="utf-8") as fin, OUT.open("w", encoding="utf-8") as fout:
        for line in fin:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            title = row.get("title")
            chunk = row.get("chunk_text")
            title_chunk = combined_text(title, chunk)
            chunk_only = chunk or ""
            rec = {
                "doc_id": row["doc_id"],
                "source_type": row.get("source_type"),
                "scale_rank": row.get("scale_rank"),
                "is_gold_anchor": bool(row.get("is_gold_anchor")),
                "title_plus_chunk": measure(enc, title_chunk),
                "chunk_text_only": measure(enc, chunk_only),
            }
            fout.write(json.dumps(rec, ensure_ascii=False) + "\n")
            n_in += 1
            if rec["title_plus_chunk"]["tokens"] > MAX_TOK:
                long_ids.append(row["doc_id"])
            if n_in % 5000 == 0:
                print(f"tokenized {n_in}", flush=True)

    rng = random.Random(SEED)
    sample_ids = long_ids[:]
    rng.shuffle(sample_ids)
    sample_ids = sample_ids[:SPOT_N]
    want = set(sample_ids)
    spot_rows: dict[str, dict] = {}
    if want:
        with INP.open(encoding="utf-8") as fin, OUT.open(encoding="utf-8") as cuts:
            cuts_by_id = {}
            for line in cuts:
                rec = json.loads(line)
                if rec["doc_id"] in want:
                    cuts_by_id[rec["doc_id"]] = rec
            for line in fin:
                row = json.loads(line)
                did = row["doc_id"]
                if did not in want:
                    continue
                text = combined_text(row.get("title"), row.get("chunk_text"))
                cut = cuts_by_id[did]["title_plus_chunk"]["cut_char_8191"]
                prefix = text[:cut]
                n_prefix = len(enc.encode(prefix, disallowed_special=()))
                decoded = enc.decode(enc.encode(text, disallowed_special=())[:MAX_TOK])
                spot_rows[did] = {
                    "tokens_full": cuts_by_id[did]["title_plus_chunk"]["tokens"],
                    "cut_char_8191": cut,
                    "tokens_of_text_prefix": n_prefix,
                    "prefix_equals_decode": prefix == decoded,
                    "cut_method": cuts_by_id[did]["title_plus_chunk"]["cut_method"],
                    "delta_from_8191": n_prefix - MAX_TOK,
                }

    SPOT.write_text(
        json.dumps(
            {
                "seed": SEED,
                "encoder": enc_name,
                "n_docs_gt_8191_tokens_title_plus_chunk": len(long_ids),
                "n_tokenized": n_in,
                "spot_check": spot_rows,
                "spot_ids": sample_ids,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"done n={n_in} gt8191_tokens={len(long_ids)} spot={len(spot_rows)}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
