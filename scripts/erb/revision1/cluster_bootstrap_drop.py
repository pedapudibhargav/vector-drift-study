#!/usr/bin/env python3
"""Cluster bootstrap of the OpenAI raw Hit@10 drop (5k to 100k) over benchmark identifiers.

The 200 primary questions come from 188 benchmark question identifiers (the part of
the eval id before '::'); questions sharing an identifier are resampled together.
Each replicate draws 188 identifiers with replacement and computes the drop as the
mean Hit@10 at 5k minus the mean at 100k over the questions drawn. 95% percentile
interval (numpy default_rng(42), linear percentiles), B=10000. With --check, compares against the stored artifact
instead of writing it.
"""
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
REV1 = ROOT / "artifacts/published/revision1"
OUT = REV1 / "cluster_bootstrap_drop_openai_primary200.json"


def hits(run):
    return {p["question_id"]: int(p["hit_at_10"]) for p in run["per_question"]}


def main():
    ex = json.loads((REV1 / "exact_ladder_openai_primary200.json").read_text())
    runs = {(r["condition"], r["scale"]): r for r in ex["runs"]}
    a, b = hits(runs[("raw", 5000)]), hits(runs[("raw", 100000)])
    cl = defaultdict(list)
    for q in a:
        cl[q.split("::")[0]].append(q)
    keys = sorted(cl)
    drop = sum(a.values()) / len(a) - sum(b.values()) / len(b)
    import numpy as np
    rng = np.random.default_rng(42)
    boots = []
    for _ in range(10000):
        qs = [q for i in rng.integers(0, len(keys), len(keys)) for q in cl[keys[i]]]
        boots.append(sum(a[q] - b[q] for q in qs) / len(qs))
    lo, hi = (float(x) for x in np.percentile(boots, [2.5, 97.5]))
    res = {"clusters": len(keys), "drop": round(drop, 6), "ci95": [lo, hi], "B": 10000, "seed": 42,
           "note": "cluster bootstrap over benchmark question identifiers (%d clusters)" % len(keys),
           "script": "cluster_bootstrap_drop.py"}
    if "--check" in sys.argv:
        old = json.loads(OUT.read_text())
        print("stored", old)
        print("recomputed", res)
        return
    OUT.write_text(json.dumps(res))
    print(res)


if __name__ == "__main__":
    main()
