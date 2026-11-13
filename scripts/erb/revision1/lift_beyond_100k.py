#!/usr/bin/env python3
"""Does the oracle lift change beyond 100k, and why? (audit follow-up, R3-A/R3-D)

Offline, from the stored full-pool exact ladders (OpenAI, primary-200):
- lift = Hit@10(meta_in) - Hit@10(raw) at 5k, 100k, 150k and the full pool
  for every schedule, with paired bootstrap 95% intervals for
  lift(full)-lift(100k), lift(full)-lift(5k), lift(100k)-lift(5k);
- the filter's partition share: for each question, the fraction of the
  corpus whose source_type is in its filter set, from the schedule's own
  composition_at_scales; mean over questions;
- the round-robin change from 100k to the full pool by source group
  (small = only Confluence/Jira/GitHub/Fireflies; large = only the other five).
Writes lift_beyond_100k_openai_primary200.json.
"""
import glob
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from run_exact_ladder import REV1, load_manifest, load_questions  # noqa: E402

B, SEED = 10000, 42
SMALL = {"confluence", "jira", "github", "fireflies"}
OUT = REV1 / "lift_beyond_100k_openai_primary200.json"


def flags(d, cond):
    out = {}
    for r in d["runs"]:
        if r["condition"] == cond:
            out[int(r["scale"])] = {p["question_id"]: float(p["hit_at_10"]) for p in r["per_question"]}
    return out


def ci(v, idx):
    b = v[idx].mean(axis=1)
    lo, hi = np.percentile(b, [2.5, 97.5])
    return {"estimate": round(float(v.mean()), 6), "ci_lo": round(float(lo), 6), "ci_hi": round(float(hi), 6)}


def main():
    qs = load_questions(load_manifest(), "primary200")
    qids = [q["eval_id"] for q in qs]
    types = {q["eval_id"]: {str(s) for s in (q.get("source_types") or []) if s} for q in qs}
    rng = np.random.default_rng(SEED)
    idx = rng.integers(0, len(qids), size=(B, len(qids)))
    files = sorted(glob.glob(str(REV1 / "exact_ladder_pool_*_openai_primary200.json")))
    res = {}
    for f in files:
        d = json.loads(Path(f).read_text())
        name = Path(f).name.replace("exact_ladder_pool_", "").replace("_openai_primary200.json", "")
        raw, meta = flags(d, "raw"), flags(d, "meta_in")
        full = max(raw)
        comp = d["meta"].get("composition_at_scales") or {}
        L = {s: np.array([meta[s][e] - raw[s][e] for e in qids]) for s in raw}
        share = {}
        for s in (5000, 100000, full):
            c = comp.get(str(s))
            if c:
                tot = sum(c.values())
                share[s] = round(float(np.mean([sum(c.get(t, 0) for t in types[e]) / tot for e in qids])), 4)
        res[name] = {
            "lift": {s: round(float(L[s].mean()), 6) for s in sorted(L)},
            "full_n": full,
            "full_minus_100k": ci(L[full] - L[100000], idx),
            "full_minus_5k": ci(L[full] - L[5000], idx),
            "100k_minus_5k": ci(L[100000] - L[5000], idx),
            "mean_partition_share": share,
        }
        if name == "rr_full":
            grp = {}
            for g in ("small", "large"):
                sel = [i for i, e in enumerate(qids) if (types[e] <= SMALL if g == "small" else not (types[e] & SMALL))]
                grp[g] = {"n": len(sel)}
                for cond, fl in (("raw", raw), ("meta_in", meta)):
                    grp[g][cond] = {s: round(float(np.mean([fl[s][qids[i]] for i in sel])), 4) for s in (5000, 100000, full)}
            res[name]["by_group"] = grp
    out = {"meta": {"bootstrap_B": B, "bootstrap_seed": SEED, "n_questions": len(qids), "files": [Path(f).name for f in files]}, "schedules": res}
    OUT.write_text(json.dumps(out, indent=1))
    for k, v in res.items():
        print(k, v["lift"].get(5000), v["lift"].get(100000), v["lift"].get(v["full_n"]), "full-100k", v["full_minus_100k"], "full-5k", v["full_minus_5k"], "100k-5k", v["100k_minus_5k"], "share", v["mean_partition_share"])
    print(json.dumps(res["rr_full"]["by_group"], indent=0))


if __name__ == "__main__":
    main()
