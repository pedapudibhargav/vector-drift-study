#!/usr/bin/env python3
"""Chunk-level top-k retrieval (R1.1): the variant chunked RAG pipelines use.

Retrieve the top 10 CHUNKS by exact cosine (ties by doc_id, then chunk file
order) and count a question as a hit when any of those chunks belongs to a gold
document ("Hit@10 chunks"). Long documents can fill several of the ten slots,
so fewer than ten distinct documents may be returned; the mean number of
distinct documents is reported. Also reports top-20/top-50 chunks.

Same 512-token / 64-overlap chunk embeddings, question vectors and sizes as
chunk_eval.py. Drops are compared with the whole-document exact ladder
(exact_ladder_openai_primary200.json) with a paired bootstrap
(B=10000, seed 42). Writes chunk_topchunks_openai_primary200.json.
"""
import json
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import chunk_eval as ce  # noqa: E402
from run_exact_ladder import OPENAI_CACHE, REV1, load_manifest, load_query_cache, load_questions  # noqa: E402

CFG = "c512_o64"
DEPTHS = (10, 20, 50)
B, SEED = 10000, 42
OUT = REV1 / "chunk_topchunks_openai_primary200.json"


def ci(v, idx):
    b = v[idx].mean(axis=1)
    lo, hi = np.percentile(b, [2.5, 97.5])
    lo9, hi9 = np.percentile(b, [5, 95])
    return {"estimate": round(float(v.mean()), 6), "ci95": [round(float(lo), 6), round(float(hi), 6)],
            "ci90": [round(float(lo9), 6), round(float(hi9), 6)]}


def main():
    import os
    if os.environ.get("CHUNK_STUDY_DIR"):
        ce.CS = Path(os.environ["CHUNK_STUDY_DIR"])
    man = load_manifest()
    qs = load_questions(man, "primary200")
    cache, miss = load_query_cache("openai", [q["eval_id"] for q in qs], OPENAI_CACHE)
    assert not miss
    Q = np.asarray([cache[q["eval_id"]] for q in qs], dtype=np.float32)
    Q /= np.linalg.norm(Q, axis=1, keepdims=True)
    doc_src = {}
    for line in open(ce.CS / "docs.jsonl"):
        r = json.loads(line)
        doc_src[r["doc_id"]] = r["source_type"]
    meta, X = ce.load_emb(CFG)
    X /= np.linalg.norm(X, axis=1, keepdims=True)
    scales = ce.CONFIGS[CFG][2]
    doc_ids = np.array([m["doc_id"] for m in meta])
    ranks = np.fromiter((m["scale_rank"] for m in meta), dtype=np.int64, count=len(meta))
    # tie-break key: doc_id order then chunk file order
    uniq = sorted(set(doc_ids.tolist()))
    dpos = {d: i for i, d in enumerate(uniq)}
    tie = np.fromiter((dpos[d] for d in doc_ids), dtype=np.int64, count=len(meta)) * 10_000_000 + np.arange(len(meta))
    src_arr = np.array([doc_src.get(d, "") for d in doc_ids])
    S = Q @ X.T
    whole = json.loads((REV1 / "exact_ladder_openai_primary200.json").read_text())
    wflags = {(r["condition"], int(r["scale"])): {p["question_id"]: bool(p["hit_at_10"]) for p in r["per_question"]} for r in whole["runs"]}
    flags = {}
    rows = []
    for cond in ("raw", "meta_in"):
        for N in scales:
            keep = ranks < N
            hits = {k: np.zeros(len(qs)) for k in DEPTHS}
            ndist = []
            for qi, q in enumerate(qs):
                m = keep.copy()
                if cond == "meta_in":
                    sts = {str(s) for s in (q.get("source_types") or []) if s}
                    m &= np.isin(src_arr, list(sts))
                cand = np.flatnonzero(m)
                order = cand[np.lexsort((tie[cand], -S[qi, cand]))[: max(DEPTHS)]]
                gold = {str(x) for x in q.get("expected_doc_ids") or []}
                for k in DEPTHS:
                    hits[k][qi] = float(any(d in gold for d in doc_ids[order[:k]]))
                ndist.append(len(set(doc_ids[order[:10]].tolist())))
            flags[(cond, N)] = hits[10]
            rows.append({"condition": cond, "scale": N, **{f"hit_at_{k}_chunks": round(float(hits[k].mean()), 6) for k in DEPTHS},
                         "mean_distinct_docs_in_top10_chunks": round(float(np.mean(ndist)), 3),
                         "whole_doc_hit_at_10": round(float(np.mean([wflags[(cond, N)][q["eval_id"]] for q in qs])), 6)})
            print(rows[-1], flush=True)
    rng = np.random.default_rng(SEED)
    idx = rng.integers(0, len(qs), size=(B, len(qs)))
    comp = {}
    lo_s, hi_s = scales[0], scales[-1]
    for cond in ("raw", "meta_in"):
        c_drop = flags[(cond, lo_s)] - flags[(cond, hi_s)]
        w = {s: np.array([wflags[(cond, s)][q["eval_id"]] for q in qs], float) for s in (lo_s, hi_s)}
        w_drop = w[lo_s] - w[hi_s]
        comp[cond] = {"topchunks_drop": ci(c_drop, idx), "whole_doc_drop": ci(w_drop, idx),
                      "topchunks_minus_whole_drop": ci(c_drop - w_drop, idx),
                      "level_topchunks_minus_whole_100k": ci(flags[(cond, hi_s)] - w[hi_s], idx)}
    rr = {r_["scale"]: r_ for r_ in rows if r_["condition"] == "raw"}
    mi = {r_["scale"]: r_ for r_ in rows if r_["condition"] == "meta_in"}
    lift = {s: round(mi[s]["hit_at_10_chunks"] - rr[s]["hit_at_10_chunks"], 6) for s in scales}
    out = {"meta": {"created": time.strftime("%FT%TZ", time.gmtime()), "config": CFG,
                    "rule": "top-k chunks by exact cosine, ties by doc_id then chunk order; hit if any of the k chunks belongs to a gold document",
                    "n_questions": len(qs), "bootstrap_B": B, "bootstrap_seed": SEED, "scales": scales},
           "runs": rows, "drop_comparison": comp, "lift_by_scale": lift}
    OUT.write_text(json.dumps(out, indent=1))
    print(json.dumps(comp, indent=1))
    print("lift", lift)


if __name__ == "__main__":
    main()
