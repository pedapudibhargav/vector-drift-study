#!/usr/bin/env python3
"""Gold-rank depth analysis from the stored exact dense top-100 lists (reviewer-driven)."""
import json, statistics
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
REV1 = ROOT / "artifacts" / "published" / "revision1"
d = json.loads((REV1 / "dense_top100_openai_primary200.json").read_text())
man = json.loads((ROOT / "data" / "erb_scale_manifest.json").read_text())
qs = {q["eval_id"]: q for q in man["questions"]}
all_gold = {g for q in man["questions"] for g in q["expected_doc_ids"]}
by = d["by_scale"]

def best_rank(sc, e):
    gold = set(qs[e]["expected_doc_ids"])
    for i, did in enumerate(by[sc][e]["retrieved_top100"], 1):
        if did in gold:
            return i
    return None  # beyond 100

out = {"hit_at_k": {}, "displaced": {}}
for sc in by:
    n = len(by[sc])
    out["hit_at_k"][sc] = {k: sum(1 for e in by[sc] if (best_rank(sc, e) or 10**9) <= k) / n for k in (1, 5, 10, 20, 50, 100)}
disp = [e for e in by["5000"] if (best_rank("5000", e) or 10**9) <= 10 and (best_rank("100000", e) or 10**9) > 10]
ranks = [best_rank("100000", e) for e in disp]
rk = [r for r in ranks if r]
out["displaced"] = {
    "n": len(disp),
    "within_20": sum(1 for r in ranks if r and r <= 20), "within_50": sum(1 for r in ranks if r and r <= 50),
    "within_100": sum(1 for r in ranks if r), "beyond_100": sum(1 for r in ranks if not r),
    "median_best_rank_among_within_100": statistics.median(rk) if rk else None,
    "p90_best_rank_among_within_100": sorted(rk)[int(0.9 * (len(rk) - 1))] if rk else None,
}
# who displaces: non-gold top-10 docs at 100k for displaced questions that are other questions' gold anchors
tot = anchors = 0
for e in disp:
    g = set(qs[e]["expected_doc_ids"])
    for did in by["100000"][e]["retrieved_top100"][:10]:
        if did in g:
            continue
        tot += 1
        anchors += did in all_gold
out["displaced"]["nongold_top10_docs"] = tot
out["displaced"]["nongold_top10_that_are_other_questions_gold_anchors"] = anchors
(REV1 / "rank_depth_openai_primary200.json").write_text(json.dumps(out, indent=1))
print(json.dumps(out, indent=1))
