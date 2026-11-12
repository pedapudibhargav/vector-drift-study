#!/usr/bin/env python3
"""Integrity checks for chunk embedding shards. Usage: validate_chunk_embeddings.py CHUNKS.jsonl EMBDIR [--spot N]"""
import sys, json, os, hashlib, random, argparse, urllib.request
import numpy as np
ap = argparse.ArgumentParser(); ap.add_argument("chunks"); ap.add_argument("emb"); ap.add_argument("--spot", type=int, default=0)
ap.add_argument("--complete", action="store_true"); ap.add_argument("--shard", type=int, default=10000)
a = ap.parse_args()
rows = [json.loads(l) for l in open(a.chunks)]
N = len(rows); S = a.shard; ns = (N + S - 1) // S
meta = [json.loads(l) for l in open(os.path.join(a.emb, "meta.jsonl"))]
bad = []
def chk(c, m):
    if not c: bad.append(m); print("FAIL:", m)
chk(len(meta) == N, f"meta rows {len(meta)} != chunks {N}")
keys = [(r["doc_id"], r["chunk_idx"]) for r in rows]
chk(len(set(keys)) == N, "duplicate (doc_id,chunk_idx) in chunk file")
chk(all((m["doc_id"], m["chunk_idx"], m["n_tokens"]) == (r["doc_id"], r["chunk_idx"], r["n_tokens"]) for m, r in zip(meta, rows)), "meta != chunk file order")
# chunk_idx contiguous per doc, scale_rank non-decreasing
last = {}; prev_rank = -1; ok_c = ok_r = True
for r in rows:
    exp = last.get(r["doc_id"], -1) + 1
    if r["chunk_idx"] != exp: ok_c = False
    last[r["doc_id"]] = r["chunk_idx"]
    if r["scale_rank"] < prev_rank: ok_r = False
    prev_rank = r["scale_rank"]
chk(ok_c, "chunk_idx not contiguous per doc"); chk(ok_r, "scale_rank decreases")
LIM = int(os.environ.get("CHUNK_LIM", "512")); lastidx = {}
for r in rows: lastidx[r["doc_id"]] = max(lastidx.get(r["doc_id"], 0), r["chunk_idx"])
chk(all(r["text"].strip() and r["n_tokens"] > 0 for r in rows), "empty text or n_tokens<=0")
chk(all(r["n_tokens"] <= LIM + 2 or (r["chunk_idx"] == lastidx[r["doc_id"]] and r["n_tokens"] <= LIM + 63) for r in rows), f"chunk over {LIM} tokens that is not a merged final chunk (<= {LIM+63})")
present = []; hashes = {}; nrows = 0; dupe_vec = 0; dupe_vec_diff_text = 0
for si in range(ns):
    p = os.path.join(a.emb, f"emb_{si:05d}.npy")
    if not os.path.exists(p): continue
    present.append(si)
    X = np.load(p); exp = min(S, N - si * S)
    chk(X.shape == (exp, 1536), f"shard {si} shape {X.shape} expected {(exp,1536)}")
    chk(bool(np.isfinite(X).all()), f"shard {si} non-finite")
    n = np.linalg.norm(X, axis=1)
    chk(bool(np.all(np.abs(n - 1) < 1e-3)), f"shard {si} norm range {n.min():.4f}-{n.max():.4f}")
    for j in range(len(X)):
        h = hashlib.md5(X[j].tobytes()).hexdigest()
        t = rows[si * S + j]["text"]
        if h in hashes:
            dupe_vec += 1
            if hashes[h] != t: dupe_vec_diff_text += 1
        else: hashes[h] = t
    nrows += len(X)
print(f"shards present {len(present)}/{ns}; rows embedded {nrows}; duplicate vectors {dupe_vec} (with different text: {dupe_vec_diff_text})")
chk(dupe_vec_diff_text == 0, "identical vectors for different texts")
if a.complete: chk(len(present) == ns, f"missing shards {sorted(set(range(ns))-set(present))}")
if a.spot and present:
    key = os.environ["OPENAI_API_KEY"]; random.seed(7)
    idx = [si * S + random.randrange(min(S, N - si * S)) for si in random.sample(present, min(len(present), a.spot))]
    body = json.dumps({"model": "text-embedding-3-small", "input": [rows[i]["text"] for i in idx]}).encode()
    d = json.loads(urllib.request.urlopen(urllib.request.Request("https://api.openai.com/v1/embeddings", data=body, headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"}), timeout=120).read())
    for i, e in zip(idx, d["data"]):
        X = np.load(os.path.join(a.emb, f"emb_{i//S:05d}.npy"), mmap_mode="r"); v = np.asarray(X[i % S]); w = np.asarray(e["embedding"], dtype=np.float32)
        cs = float(v @ w / (np.linalg.norm(v) * np.linalg.norm(w))); print(f"spot idx {i} cos={cs:.5f}")
        chk(cs > 0.999, f"spot check idx {i} cos {cs:.4f}")
print("RESULT:", "OK" if not bad else f"{len(bad)} PROBLEMS")
sys.exit(1 if bad else 0)
