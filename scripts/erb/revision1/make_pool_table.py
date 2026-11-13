#!/usr/bin/env python3
"""LaTeX table of full-pool ladders (raw / meta_in Hit@10) plus schedule-uncertainty summary."""
import json, statistics
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
REV1 = ROOT / "artifacts" / "published" / "revision1"
OUT = REV1 / "paper_tables" / "tab_pool_ladders.tex"
LAD = [("rr\\_full", "round-robin"), ("prop_s42", "proportional, seed 42"), ("prop_s0", "proportional, seed 0"),
       ("prop_evalgold_s42", "proportional, evaluated-bank gold pinned only")]
SIZES = [5000, 50000, 100000, 150000, 184963]


def load(name):
    key = name.replace("\\_", "_")
    d = json.loads((REV1 / f"exact_ladder_pool_{key}_openai_primary200.json").read_text())
    t = {}
    for r in d["runs"]:
        sc = r.get("scale") or r.get("corpus_scale_size")
        t[(r["condition"], int(sc))] = r["metrics"]["hit_at_10"]
    return t


rows = []
summary = {}
for key, label in LAD:
    t = load(key)
    cells = " & ".join(f"{t[('raw', s)]:.3f} / {t[('meta_in', s)]:.3f}" for s in SIZES)
    lift = " & ".join(f"{t[('meta_in', s)] - t[('raw', s)]:+.3f}" for s in (5000, 100000, 184963))
    rows.append(f"{label} & {cells} & {lift} \\\\")
    summary[key] = {s: (t[("raw", s)], t[("meta_in", s)]) for s in SIZES}
tex = (
    "\\begin{table*}[!t]\n\\caption{Full-pool exact ladders (OpenAI, primary-200): raw / \\texttt{meta\\_in} Hit@10 at selected sizes "
    "and the lift in Hit@10 at $5\\text{k}$, $100\\text{k}$, and the full pool ($184{,}963$ documents).}\n\\label{tab:poolladders}\n"
    "\\fittext{\\begin{tabular}{@{}lccccccccc@{}}\n\\toprule\nSchedule & $5\\text{k}$ & $50\\text{k}$ & $100\\text{k}$ & $150\\text{k}$ & Full & "
    "$\\Delta_{5\\text{k}}$ & $\\Delta_{100\\text{k}}$ & $\\Delta_{\\text{full}}$ \\\\\n\\midrule\n" + "\n".join(rows) + "\n\\bottomrule\n\\end{tabular}}\n\\end{table*}\n"
)
# one row has 9 data columns; fix the header count: sizes (5) + lifts (3) = 8 numeric columns
tex = tex.replace("{@{}lccccccccc@{}}", "{@{}lcccccccc@{}}")
OUT.write_text(tex)
# schedule-uncertainty summary over seeds
seeds = {}
for s in range(1, 9):
    p = REV1 / f"exact_ladder_pool_prop_s{s}_openai_primary200.json"
    if not p.exists():
        continue
    d = json.loads(p.read_text())
    t = {(r["condition"], int(r.get("scale") or r.get("corpus_scale_size"))): r["metrics"]["hit_at_10"] for r in d["runs"]}
    seeds[s] = t
for s, d in ((42, "prop_s42"), (0, "prop_s0")):
    seeds[s] = {(c, sc): v for (c, sc), v in ((("raw", k), summary[d][k][0]) for k in summary[d])} | \
               {("meta_in", k): summary[d][k][1] for k in summary[d]}
drops = [t[("raw", 5000)] - t[("raw", 100000)] for t in seeds.values() if ("raw", 100000) in t]
lifts100 = [t[("meta_in", 100000)] - t[("raw", 100000)] for t in seeds.values() if ("meta_in", 100000) in t]
liftsF = [t[("meta_in", 184963)] - t[("raw", 184963)] for t in seeds.values() if ("meta_in", 184963) in t]
lifts5 = [t[("meta_in", 5000)] - t[("raw", 5000)] for t in seeds.values() if ("meta_in", 5000) in t]
rep = {"n_proportional_seeds": len(drops), "drop_5k_100k": {"mean": statistics.mean(drops), "sd": statistics.stdev(drops) if len(drops) > 1 else None, "min": min(drops), "max": max(drops)},
       "lift_5k": [min(lifts5), max(lifts5)], "lift_100k": [min(lifts100), max(lifts100)], "lift_full": [min(liftsF), max(liftsF)] if liftsF else None,
       "per_seed": {str(k): {"raw5k": v.get(("raw", 5000)), "raw100k": v.get(("raw", 100000)), "rawfull": v.get(("raw", 184963))} for k, v in seeds.items()}}
(REV1 / "pool_schedule_uncertainty.json").write_text(json.dumps(rep, indent=1))
print(OUT.read_text()); print(json.dumps(rep, indent=1))
