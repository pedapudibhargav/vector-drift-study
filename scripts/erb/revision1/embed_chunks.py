#!/usr/bin/env python3
"""Embed chunk JSONL with OpenAI text-embedding-3-small; resumable shards; hard USD cap. Key from env only."""
import argparse, json, os, sys, time, threading, urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import numpy as np

PRICE = 0.02 / 1e6
ROOT = Path(__file__).resolve().parents[3]


_PACE = threading.Lock()
_NEXT = [0.0]
TPM_BUDGET = 700_000  # stay below the 1M tokens/min org limit


def _pace(est_tokens):
    """Global pacing across worker threads so requests never exceed TPM_BUDGET."""
    with _PACE:
        now = time.time()
        start = max(now, _NEXT[0])
        _NEXT[0] = start + est_tokens / (TPM_BUDGET / 60.0)
    if start > now:
        time.sleep(start - now)


def embed(texts, key):
    body = json.dumps({"model": "text-embedding-3-small", "input": texts}).encode()
    est = sum(len(t) for t in texts) / 3.3
    fails = 0
    while True:
        _pace(est)
        req = urllib.request.Request("https://api.openai.com/v1/embeddings", data=body,
                                     headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"})
        try:
            d = json.loads(urllib.request.urlopen(req, timeout=120).read())
            return [x["embedding"] for x in sorted(d["data"], key=lambda x: x["index"])], d["usage"]["total_tokens"]
        except urllib.error.HTTPError as e:
            if e.code == 429:  # rate limit: wait and retry indefinitely (free)
                time.sleep(15); continue
            fails += 1
            print("HTTP", e.code, e.read()[:200], flush=True)
            if e.code in (500, 502, 503) and fails < 30:
                time.sleep(min(60, 2 ** min(fails, 6))); continue
            raise
        except Exception as ex:
            fails += 1
            print("ERR", repr(ex)[:200], flush=True)
            if fails >= 30:
                raise
            time.sleep(min(60, 2 ** min(fails, 6)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--chunks", required=True); ap.add_argument("--outdir", required=True)
    ap.add_argument("--max-docs-rank", type=int, default=10**9, help="only chunks with scale_rank < this")
    ap.add_argument("--max-usd", type=float, required=True); ap.add_argument("--batch", type=int, default=128)
    ap.add_argument("--shard", type=int, default=10000); ap.add_argument("--workers", type=int, default=4)
    a = ap.parse_args()
    key = os.environ["OPENAI_API_KEY"]
    out = Path(a.outdir); out.mkdir(parents=True, exist_ok=True)
    rows = [json.loads(l) for l in open(a.chunks) if json.loads(l)["scale_rank"] < a.max_docs_rank] if False else []
    with open(a.chunks) as f:
        for l in f:
            d = json.loads(l)
            if d["scale_rank"] < a.max_docs_rank:
                rows.append(d)
    est_tok = sum(r["n_tokens"] for r in rows)
    print(f"chunks={len(rows)} est_tokens={est_tok} est_usd={est_tok*PRICE:.3f} cap={a.max_usd}", flush=True)
    if est_tok * PRICE > a.max_usd:
        sys.exit("estimate exceeds cap")
    meta_path = out / "meta.jsonl"
    with meta_path.open("w") as f:
        for r in rows:
            f.write(json.dumps({"doc_id": r["doc_id"], "scale_rank": r["scale_rank"], "chunk_idx": r["chunk_idx"], "n_tokens": r["n_tokens"]}) + "\n")
    spent = [0]; lock = threading.Lock()
    nshards = (len(rows) + a.shard - 1) // a.shard

    def do_shard(si):
        p = out / f"emb_{si:05d}.npy"
        if p.exists():
            return
        part = rows[si * a.shard:(si + 1) * a.shard]
        vecs = []
        for i in range(0, len(part), a.batch):
            with lock:
                if spent[0] * PRICE > a.max_usd:
                    raise RuntimeError("spend cap hit")
            v, tok = embed([r["text"] for r in part[i:i + a.batch]], key)
            with lock:
                spent[0] += tok
            vecs.extend(v)
        np.save(p.with_suffix(".tmp.npy"), np.asarray(vecs, dtype=np.float32))
        os.replace(p.with_suffix(".tmp.npy"), p)
        with lock:
            print(f"shard {si+1}/{nshards} done, tokens so far {spent[0]}, usd {spent[0]*PRICE:.3f}", flush=True)
        with open(ROOT / "data" / "chunk_study" / "embed_spend.jsonl", "a") as f:
            f.write(json.dumps({"t": time.strftime("%FT%TZ", time.gmtime()), "outdir": str(out), "shard": si, "usd_cum_this_run": round(spent[0] * PRICE, 4)}) + "\n")

    with ThreadPoolExecutor(a.workers) as ex:
        list(ex.map(do_shard, range(nshards)))
    print(f"DONE tokens={spent[0]} usd={spent[0]*PRICE:.3f}", flush=True)


if __name__ == "__main__":
    main()
