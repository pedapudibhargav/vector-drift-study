#!/usr/bin/env python3
"""RRF sensitivity: fusion constant k and dense/BM25 weighting (R1.4).

Offline: reads the stored exact dense top-100 lists
(dense_top100_openai_primary200.json) and the BM25 dense_text top-100 lists
(bm25_dense_text.json); no database access. Weighted RRF:
    score(d) = 2 * [ w / (k + r_dense(d)) + (1 - w) / (k + r_bm25(d)) ],
where w = 0.5 gives standard RRF. Ties are broken by doc_id ascending, as in
rrf_hybrid.py. The script checks that (k=60, w=0.5) reproduces the published
rrf_k60 Hit@10 at every size, and that w=1 and w=0 reproduce dense and BM25.
Bootstrap: B=10000 paired over the 200 questions, seed 42 (shared indices).
The grid is evaluated on the test bank itself, so the best cell is an
optimistic (in-sample) choice and is reported as such.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

_SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_SCRIPT_DIR))
import run_exact_ladder as ladder  # noqa: E402

REV1 = ladder.REV1
DENSE = REV1 / "dense_top100_openai_primary200.json"
BM25 = REV1 / "bm25_dense_text.json"
RRF_PUB = REV1 / "rrf_hybrid_openai_primary200.json"
OUT = REV1 / "rrf_sensitivity_openai_primary200.json"
KS = (1, 10, 30, 60, 100, 200)
WS = (0.0, 0.25, 0.4, 0.5, 0.6, 0.75, 1.0)
B, SEED, TOPN = 10000, 42, 10


def fuse(dl, bl, k, w):
    s = {}
    for lst, wt in ((dl, w), (bl, 1.0 - w)):
        if wt == 0.0:
            continue
        seen = set()
        for i, d in enumerate(lst):
            if d in seen:
                continue
            seen.add(d)
            s[d] = s.get(d, 0.0) + 2.0 * wt / (k + i + 1)
    return sorted(s, key=lambda d: (-s[d], d))[:TOPN]


def flags(golds, lists, qids):
    hit = np.zeros(len(qids))
    mrr = np.zeros(len(qids))
    for j, q in enumerate(qids):
        g = golds[q]
        for r, d in enumerate(lists[q][:TOPN]):
            if d in g:
                hit[j] = 1.0
                mrr[j] = 1.0 / (r + 1)
                break
    return hit, mrr


def ci(v, idx):
    b = v[idx].mean(axis=1)
    lo, hi = np.percentile(b, [2.5, 97.5])
    return {"estimate": round(float(v.mean()), 6), "ci_lo": round(float(lo), 6), "ci_hi": round(float(hi), 6)}


def main() -> int:
    manifest = ladder.load_manifest()
    qs = ladder.load_questions(manifest, "primary200")
    qids = [q["eval_id"] for q in qs]
    golds = {q["eval_id"]: {str(x) for x in (q.get("expected_doc_ids") or []) if x} for q in qs}
    dense = json.loads(DENSE.read_text())["by_scale"]
    bm = json.loads(BM25.read_text())["per_question_by_scale"]
    bm = {int(s): {r["question_id"]: [str(d) for d in r.get("retrieved_top100") or []] for r in rows} for s, rows in bm.items()}
    pub = {r["scale"]: r for r in json.loads(RRF_PUB.read_text())["by_scale"]}
    scales = sorted(int(s) for s in dense)
    rng = np.random.default_rng(SEED)
    idx = rng.integers(0, len(qids), size=(B, len(qids)))

    H, M = {}, {}
    for k in KS:
        for w in WS:
            if w in (0.0, 1.0) and k != 60:
                continue
            for s in scales:
                lists = {q: fuse(dense[str(s)][q]["retrieved_top100"], bm[s][q], k, w) for q in qids}
                H[(k, w, s)], M[(k, w, s)] = flags(golds, lists, qids)

    checks = []
    for s in scales:
        for key, (k, w) in (("rrf_k60", (60, 0.5)), ("dense", (60, 1.0)), ("bm25", (60, 0.0))):
            got = round(float(H[(k, w, s)].mean()), 6)
            want = round(float(pub[s][key]["hit_at_10"]), 6)
            checks.append({"scale": s, "series": key, "got": got, "published": want, "ok": abs(got - want) < 1e-9})
    if not all(c["ok"] for c in checks):
        print("FAIL reproduction", [c for c in checks if not c["ok"]][:5], file=sys.stderr)
        return 1

    lo_s, hi_s = scales[0], scales[-1]
    dense_drop = H[(60, 1.0, lo_s)] - H[(60, 1.0, hi_s)]
    dense_mrr_drop = M[(60, 1.0, lo_s)] - M[(60, 1.0, hi_s)]
    cells = []
    for (k, w, s) in sorted({(k, w, lo_s) for (k, w, _) in H}):
        row = {"k": k, "w_dense": w, "hit10_by_scale": {}, "mrr_by_scale": {}}
        for sc in scales:
            row["hit10_by_scale"][sc] = round(float(H[(k, w, sc)].mean()), 6)
            row["mrr_by_scale"][sc] = round(float(M[(k, w, sc)].mean()), 6)
        drop = H[(k, w, lo_s)] - H[(k, w, hi_s)]
        mdrop = M[(k, w, lo_s)] - M[(k, w, hi_s)]
        row["hit10_drop"] = ci(drop, idx)
        row["mrr_drop"] = ci(mdrop, idx)
        row["drop_minus_dense_drop_hit10"] = ci(drop - dense_drop, idx)
        row["drop_minus_dense_drop_mrr"] = ci(mdrop - dense_mrr_drop, idx)
        row["gain_vs_dense_hit10_at_100k"] = ci(H[(k, w, hi_s)] - H[(60, 1.0, hi_s)], idx)
        row["gain_vs_bm25_hit10_at_100k"] = ci(H[(k, w, hi_s)] - H[(60, 0.0, hi_s)], idx)
        gains = [float(H[(k, w, sc)].mean() - H[(60, 1.0, sc)].mean()) for sc in scales]
        row["gain_vs_dense_hit10_min_max"] = [round(min(gains), 6), round(max(gains), 6)]
        cells.append(row)

    out = {
        "meta": {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "purpose": "R1.4 sensitivity of reciprocal rank fusion to k and to the dense/BM25 weight",
            "inputs": [str(DENSE.relative_to(ladder.ROOT)), str(BM25.relative_to(ladder.ROOT))],
            "formula": "score = 2*[w/(k+r_dense) + (1-w)/(k+r_bm25)], ranks 1-based over top-100 lists, ties by doc_id",
            "ks": list(KS), "weights": list(WS), "bootstrap_B": B, "bootstrap_seed": SEED,
            "n_questions": len(qids), "scales": scales,
            "caveat": "grid evaluated on the test bank; best cell is in-sample",
        },
        "reproduction_checks": checks,
        "cells": cells,
    }
    OUT.write_text(json.dumps(out, indent=1))
    print("wrote", OUT)
    for r in cells:
        print(f"k={r['k']:>3} w={r['w_dense']:.2f}  5k={r['hit10_by_scale'][lo_s]:.3f} 100k={r['hit10_by_scale'][hi_s]:.3f} "
              f"drop={r['hit10_drop']['estimate']:.3f} dDrop={r['drop_minus_dense_drop_hit10']['estimate']:+.3f}"
              f"[{r['drop_minus_dense_drop_hit10']['ci_lo']:+.3f},{r['drop_minus_dense_drop_hit10']['ci_hi']:+.3f}] "
              f"gain={r['gain_vs_dense_hit10_min_max']} vsBM25@100k={r['gain_vs_bm25_hit10_at_100k']['estimate']:+.3f}"
              f"[{r['gain_vs_bm25_hit10_at_100k']['ci_lo']:+.3f},{r['gain_vs_bm25_hit10_at_100k']['ci_hi']:+.3f}]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
