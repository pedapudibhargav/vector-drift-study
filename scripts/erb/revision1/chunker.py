#!/usr/bin/env python3
"""Deterministic recursive, token-capped chunker (cl100k_base) for the chunked-control experiment.

Spec (see private/briefs/CHUNK_DESIGN.md): every chunk = "<title>\\n\\n<body piece>", total <= MAX_TOK tokens
(title capped at TITLE_CAP tokens); body is split recursively on ["\\n\\n", "\\n", ". ", " "] (hard token split
last), pieces are merged greedily up to the body budget, and each new chunk starts with the trailing pieces of
the previous chunk totalling <= OVERLAP body tokens. A final chunk with < TAIL_MIN body tokens is merged into the
previous one. Documents whose whole text fits are one chunk.
"""
import argparse, json, sys
from pathlib import Path
import tiktoken

SEPS = ["\n\n", "\n", ". ", " "]
enc = tiktoken.get_encoding("cl100k_base")


def ntok(s):
    return len(enc.encode(s, disallowed_special=()))


def split_rec(text, budget, level=0):
    """Return list of pieces (strings, concatenation == text) each <= budget tokens."""
    if ntok(text) <= budget:
        return [text]
    if level >= len(SEPS):
        ids = enc.encode(text, disallowed_special=())
        return [enc.decode(ids[i:i + budget]) for i in range(0, len(ids), budget)]
    sep = SEPS[level]
    parts = text.split(sep)
    pieces = []
    for i, p in enumerate(parts):
        p2 = p + (sep if i < len(parts) - 1 else "")
        if p2 == "":
            continue
        pieces.extend(split_rec(p2, budget, level + 1) if ntok(p2) > budget else [p2])
    return pieces


def tail_text(text, overlap):
    """Last `overlap` tokens of text, snapped forward to a word start."""
    if overlap <= 0:
        return ""
    ids = enc.encode(text, disallowed_special=())
    if len(ids) <= overlap:
        return text
    t = enc.decode(ids[-overlap:])
    k = 0
    while k < len(t) and not t[k].isspace():
        k += 1
    return t[k:].lstrip(" ") if k < len(t) else ""


def chunk_body(body, budget, overlap, tail_min):
    pieces = split_rec(body, budget - overlap if overlap < budget // 2 else budget)
    counts = [ntok(p) for p in pieces]
    chunks = []  # (text, new_tokens)
    cur = []; cur_new = 0; carry = ""; carry_t = 0
    for p, c in zip(pieces, counts):
        if cur and carry_t + cur_new + c > budget:
            text = carry + "".join(cur)
            chunks.append((text, cur_new))
            carry = tail_text(text, overlap); carry_t = ntok(carry) if carry else 0
            cur = []; cur_new = 0
        cur.append(p); cur_new += c
    if cur:
        chunks.append((carry + "".join(cur), cur_new))
    texts = [t for t, _ in chunks]
    if len(chunks) > 1 and chunks[-1][1] < tail_min:
        # merge the new content of the tiny last chunk into the previous chunk (carry excluded)
        last_new = chunks[-1][0][len(carry):] if chunks[-1][0].startswith(carry) else chunks[-1][0]
        texts[-2] = texts[-2] + last_new
        texts.pop()
    return texts


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--docs", default="/data/chunk_study/docs.jsonl")
    ap.add_argument("--out", required=True)
    ap.add_argument("--max-tok", type=int, default=512)
    ap.add_argument("--overlap", type=int, default=64)
    ap.add_argument("--tail-min", type=int, default=64)
    ap.add_argument("--title-cap", type=int, default=64)
    ap.add_argument("--max-docs", type=int, default=10**9)
    ap.add_argument("--stats-only", action="store_true")
    a = ap.parse_args()
    tot_tok = 0; n_chunks = 0; n_docs = 0; over = 0; hist = {}
    fout = None if a.stats_only else open(a.out, "w")
    for line in open(a.docs):
        d = json.loads(line)
        if n_docs >= a.max_docs:
            break
        n_docs += 1
        title = d["title"].strip()
        tids = enc.encode(title, disallowed_special=())[: a.title_cap]
        title_c = enc.decode(tids)
        text = d["text"]
        body = text[len(d["title"]):].lstrip("\n") if d["title"] and text.startswith(d["title"]) else text
        prefix = title_c + "\n\n"
        pt = len(tids) + 2
        budget = a.max_tok - pt
        texts = chunk_body(body, budget, a.overlap, a.tail_min) if body.strip() else [""]
        for k, t in enumerate(texts):
            ctext = prefix + t
            n = ntok(ctext)
            if n > 8191:
                over += 1
            tot_tok += n; n_chunks += 1
            if fout:
                fout.write(json.dumps({"doc_id": d["doc_id"], "scale_rank": d["scale_rank"], "chunk_idx": k, "n_tokens": n, "text": ctext}) + "\n")
        hist[len(texts)] = hist.get(len(texts), 0) + 1
    print(json.dumps({"docs": n_docs, "chunks": n_chunks, "tokens": tot_tok, "cost_usd_at_0.02_per_M": tot_tok / 1e6 * 0.02,
                      "over_8191": over, "chunks_per_doc_hist": dict(sorted(hist.items()))}))


if __name__ == "__main__":
    main()
