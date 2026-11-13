#!/usr/bin/env python3
"""Drift by source group (revision 1, added after submission).

Groups the 200 primary questions by their listed source types: 'small' = all listed types are among the four
sources that are exhausted before 100k in the round-robin schedule (confluence, jira, github, fireflies);
'large' = no listed type is one of them; 'mixed' = both kinds. Writes artifacts/published/revision1/source_group_split.json.
Bootstrap: percentile, B = 10000, seed 42, questions resampled within each group.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import analyze_exact as A  # noqa: E402

ROOT = HERE.parents[2]
REV1 = ROOT / "artifacts" / "published" / "revision1"
SMALL = {"confluence", "jira", "github", "fireflies"}


def flags(blob, cond, scale):
    r = [x for x in blob["runs"] if x["condition"] == cond and x["scale"] == scale][0]
    return {p["question_id"]: int(p["hit_at_10"]) for p in r["per_question"]}


def main() -> None:
    _, questions = A.load_manifest()
    ladder = json.loads((REV1 / "exact_ladder_openai_primary200.json").read_text())
    pool = json.loads((REV1 / "exact_ladder_pool_rr_full_openai_primary200.json").read_text())
    ids = sorted(flags(ladder, "raw", 5000))
    group = {}
    for q in ids:
        st = set(questions[q].get("source_types") or [])
        group[q] = "small" if st and st <= SMALL else ("large" if st and not (st & SMALL) else "mixed")
    out: dict = {"definition": "small = all listed source types in {confluence, jira, github, fireflies}; large = none of them; mixed = both",
                 "bootstrap": {"B": 10000, "seed": 42, "level": 0.95}, "groups": {}}
    cache = {}
    for cond in ("raw", "meta_in"):
        for scale in (5000, 100000):
            cache[(cond, scale)] = flags(ladder, cond, scale)
        for scale in (100000, 184963):
            cache[("pool", cond, scale)] = flags(pool, cond, scale)
    for g in ("small", "large", "mixed"):
        qs = [q for q in ids if group[q] == g]
        rec = {"n": len(qs)}
        for cond in ("raw", "meta_in"):
            rec[cond] = {
                "hit10_5k": float(np.mean([cache[(cond, 5000)][q] for q in qs])),
                "hit10_100k": float(np.mean([cache[(cond, 100000)][q] for q in qs])),
                "hit10_full_pool": float(np.mean([cache[("pool", cond, 184963)][q] for q in qs])),
            }
            rec[cond]["drop_5k_100k"] = rec[cond]["hit10_5k"] - rec[cond]["hit10_100k"]
        out["groups"][g] = rec
    rng = np.random.default_rng(42)
    S = [q for q in ids if group[q] == "small"]
    L = [q for q in ids if group[q] == "large"]
    drop = {q: cache[("raw", 5000)][q] - cache[("raw", 100000)][q] for q in ids}
    diffs = []
    for _ in range(10000):
        a = rng.choice(S, len(S))
        b = rng.choice(L, len(L))
        diffs.append(np.mean([drop[q] for q in b]) - np.mean([drop[q] for q in a]))
    lo, hi = np.percentile(diffs, [2.5, 97.5])
    out["large_minus_small_drop"] = {
        "estimate": out["groups"]["large"]["raw"]["drop_5k_100k"] - out["groups"]["small"]["raw"]["drop_5k_100k"],
        "ci_lo": float(lo), "ci_hi": float(hi)}
    # the same split on every other exact ladder of the primary-200 bank (raw Hit@10, 5k -> 100k)
    import glob
    gaps = {}
    for path in sorted(glob.glob(str(REV1 / "exact_ladder_*primary200.json"))):
        name = Path(path).name.replace("exact_ladder_", "").replace("_primary200.json", "")
        if name.startswith("origdb"):
            continue
        blob = json.loads(Path(path).read_text())
        try:
            a5 = flags(blob, "raw", 5000)
            a100 = flags(blob, "raw", 100000)
        except IndexError:
            continue
        dd = {q: a5[q] - a100[q] for q in ids}
        sm = float(np.mean([dd[q] for q in S]))
        lg = float(np.mean([dd[q] for q in L]))
        r2 = np.random.default_rng(42)
        bb = []
        for _ in range(10000):
            x = r2.choice(S, len(S))
            y = r2.choice(L, len(L))
            bb.append(np.mean([dd[q] for q in y]) - np.mean([dd[q] for q in x]))
        l2, h2 = np.percentile(bb, [2.5, 97.5])
        gaps[name] = {"small_drop": sm, "large_drop": lg, "large_minus_small": lg - sm, "ci_lo": float(l2), "ci_hi": float(h2)}
    out["gap_by_ladder"] = gaps
    (REV1 / "source_group_split.json").write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
    print(json.dumps({k: out[k] for k in ("large_minus_small_drop",)}, indent=1))
    for g, r in out["groups"].items():
        print(g, r["n"], {c: {k: round(v, 3) for k, v in r[c].items()} for c in ("raw", "meta_in")})


if __name__ == "__main__":
    main()
