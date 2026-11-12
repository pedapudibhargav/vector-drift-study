#!/usr/bin/env python3
"""Chunked-document control: exact MaxP cosine retrieval over chunk embeddings (numpy, brute force),
cross-checked against the published whole-document ladder recomputed from PostgreSQL.
Doc score = max cosine over the document's chunks; ties broken by doc_id (same rule as the SQL ladders)."""
import json, os, sys, argparse, time
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
from run_exact_ladder import MANIFEST_PATH, OPENAI_CACHE, BANK_FILES, load_manifest, load_questions, load_query_cache, per_question_metrics, aggregate_metrics, TOP_K, REV1, ROOT

CS = ROOT / "data" / "chunk_study"
CONFIGS = {  # name: (chunks file, emb dir, scales)
    "c512_o64": ("c512.jsonl", "emb_512", [5000, 10000, 25000, 50000, 75000, 100000]),
    "c256_o32": ("c256.jsonl", "emb_256_25k", [5000, 10000, 25000]),
    "c512_o0": ("c512o0_10k.jsonl", "emb_512o0_10k", [5000, 10000]),
}
DEPTHS = (10, 20, 50)


def load_emb(cfg):
    cf, ed, _ = CONFIGS[cfg]
    meta = [json.loads(l) for l in open(CS / ed / "meta.jsonl")]
    n = len(meta)
    parts = []
    for si in range((n + 9999) // 10000):
        parts.append(np.load(CS / ed / f"emb_{si:05d}.npy"))
    X = np.concatenate(parts).astype(np.float32)
    assert X.shape == (n, 1536), X.shape
    return meta, X


def maxp_topk(Q, X, doc_idx, doc_order, ndocs, mask_docs=None, k=50):
    """Q: nq x d; X: nc x d; doc_idx: chunk -> dense doc index; doc_order: dense index -> tie-break rank.
    mask_docs: nq x ndocs bool allowed. Returns list of ordered doc-index arrays (top k) and scores."""
    S = Q @ X.T  # nq x nc
    out = []
    for qi in range(Q.shape[0]):
        best = np.full(ndocs, -2.0, dtype=np.float32)
        np.maximum.at(best, doc_idx, S[qi])
        if mask_docs is not None:
            best = np.where(mask_docs[qi], best, -3.0)
        valid = best > -2.0 if mask_docs is None else best > -2.5
        cand = np.flatnonzero(valid)
        order = np.lexsort((doc_order[cand], -best[cand]))[:k]
        out.append((cand[order], best[cand[order]]))
    return out


def evaluate(Q, X, meta, N, qs, doc_src, cond):
    """Evaluate at scale N: docs with scale_rank < N."""
    keep = np.fromiter((m["scale_rank"] < N for m in meta), dtype=bool, count=len(meta))
    ids = [m["doc_id"] for m, k in zip(meta, keep) if k]
    uniq = sorted(set(ids))
    pos = {d: i for i, d in enumerate(uniq)}
    doc_idx = np.fromiter((pos[d] for d in ids), dtype=np.int64, count=len(ids))
    doc_order = np.arange(len(uniq))  # uniq is sorted by doc_id => tie-break by doc_id
    mask = None
    if cond == "meta_in":
        mask = np.zeros((len(qs), len(uniq)), dtype=bool)
        for qi, q in enumerate(qs):
            sts = set(str(s) for s in (q.get("source_types") or []) if s)
            mask[qi] = np.array([doc_src.get(d) in sts for d in uniq])
    res = maxp_topk(Q, X[keep], doc_idx, doc_order, len(uniq), mask, k=max(DEPTHS))
    pq = []; deep = {k: 0 for k in DEPTHS}
    for q, (ix, sc) in zip(qs, res):
        retrieved = [uniq[i] for i in ix]
        exp = set(str(x) for x in q.get("expected_doc_ids") or [])
        pq.append(per_question_metrics(exp, retrieved, list(sc), TOP_K))
        for kk in DEPTHS:
            if exp & set(retrieved[:kk]): deep[kk] += 1
    m = aggregate_metrics(pq)
    m.update({f"hit_at_{kk}_depth": deep[kk] / len(qs) for kk in DEPTHS})
    return m, [p["hit_at_10"] for p in pq], dict(docs=len(uniq), chunks=int(keep.sum()), per_question_ranks=[p["rank"] for p in pq])


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--out", default=str(REV1 / "chunk_control_openai_primary200.json"))
    ap.add_argument("--baseline", action="store_true", help="recompute whole-doc baseline from PostgreSQL")
    a = ap.parse_args()
    man = load_manifest(); qs = load_questions(man, "primary200")
    cache, miss = load_query_cache("openai", [q["eval_id"] for q in qs], OPENAI_CACHE); assert not miss
    Q = np.asarray([cache[q["eval_id"]] for q in qs], dtype=np.float32)
    Q /= np.linalg.norm(Q, axis=1, keepdims=True)
    # source types per doc (from the manifest, same map the SQL ladders use for meta filters? SQL uses document_chunks.source_type)
    doc_src = {}
    for l in open(CS / "docs.jsonl"):
        r = json.loads(l); doc_src[r["doc_id"]] = r["source_type"]
    results = {"meta": dict(embedder="text-embedding-3-small", search="exact brute-force cosine, MaxP (max chunk score per document), tie-break doc_id", bank="primary200", n_questions=len(qs), created=time.strftime("%FT%TZ", time.gmtime())), "runs": []}
    # baseline from DB through identical numpy code (whole doc = one 'chunk')
    if a.baseline:
        import psycopg2
        conn = psycopg2.connect(host="localhost", port=5433, user="vector_drift", password=os.environ["PGPASSWORD"], dbname="vector_drift")
        cur = conn.cursor(); cur.execute("SELECT doc_id, scale_rank, embedding::text FROM document_chunks WHERE scale_rank < 100000 ORDER BY doc_id")
        bm = []; bx = []
        for d, r, e in cur:
            bm.append({"doc_id": d, "scale_rank": r}); bx.append(np.fromstring(e.strip("[]"), sep=",", dtype=np.float32))
        BX = np.asarray(bx); BX /= np.linalg.norm(BX, axis=1, keepdims=True)
        for cond in ("raw", "meta_in"):
            for N in (5000, 10000, 25000, 50000, 75000, 100000):
                m, hits, extra = evaluate(Q, BX, bm, N, qs, doc_src, cond)
                results["runs"].append(dict(config="whole_doc_recomputed", condition=cond, scale=N, metrics=m, **extra)); print("whole", cond, N, m["hit_at_10"], flush=True)
    for cfg, (cf, ed, scales) in CONFIGS.items():
        meta, X = load_emb(cfg); X /= np.linalg.norm(X, axis=1, keepdims=True)
        for cond in ("raw", "meta_in"):
            for N in scales:
                m, hits, extra = evaluate(Q, X, meta, N, qs, doc_src, cond)
                results["runs"].append(dict(config=cfg, condition=cond, scale=N, metrics=m, **extra))
                print(cfg, cond, N, "docs", extra["docs"], "chunks", extra["chunks"], "hit@10", m["hit_at_10"], "mrr", m["mrr"], flush=True)
    Path(a.out).write_text(json.dumps(results, indent=1))
    print("wrote", a.out)


if __name__ == "__main__":
    main()
