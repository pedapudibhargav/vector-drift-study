#!/usr/bin/env python3
"""Per-source document counts at all nine ladder sizes (round-robin ladder, gold anchors included).
Reads the committed artifacts/published/revision1/scale_manifest_compact.json (doc_id, source_type, scale_rank, gold flag)."""
import json, collections
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
SRC = ROOT / "artifacts" / "published" / "revision1" / "scale_manifest_compact.json"
SIZES = [5000, 10000, 15000, 20000, 25000, 40000, 50000, 75000, 100000]
# the database holds one row per doc_id, so a duplicated manifest entry keeps only its lowest rank (rows are sorted by rank)
seen = set()
docs = []
for r in json.load(open(SRC))["documents"]:
    if r[2] < 100000 and r[0] not in seen:
        seen.add(r[0])
        docs.append({"doc_id": r[0], "source_type": r[1], "scale_rank": r[2]})
srcs = sorted({d["source_type"] for d in docs})
counts = {n: collections.Counter(d["source_type"] for d in docs if d["scale_rank"] < n) for n in SIZES}
tot = {n: sum(counts[n].values()) for n in SIZES}
def nm(s): return s.replace("_", "\\_")
lab = lambda n: f"{n//1000}k"
rows = [" & ".join([nm(s)] + [f"{counts[n][s]:,}".replace(",", "{,}") for n in SIZES]) + " \\\\" for s in srcs]
rows.append("\\midrule")
rows.append(" & ".join(["Total"] + [f"{tot[n]:,}".replace(",", "{,}") for n in SIZES]) + " \\\\")
cap = ("\\caption{Documents per source at every ladder size under the round-robin schedule (gold anchors included; sizes count documents with \\texttt{scale\\_rank}${<}N$, so totals from $40\\text{k}$ on are one short, and two short at $100\\text{k}$, because some ranks are unused). A source stops growing once it is exhausted.}\n\\label{tab:poolcounts}\n")
tex = ("\\begin{table*}[t]\n" + cap + "\\centering\n\\small\n\\fittext{\\begin{tabular}{@{}l" + "r" * len(SIZES) + "@{}}\n\\toprule\nSource & "
       + " & ".join(lab(n) for n in SIZES) + " \\\\\n\\midrule\n" + "\n".join(rows)
       + "\n\\bottomrule\n\\end{tabular}}\n\\end{table*}\n")
out = ROOT / "papers" / "ieee-vector-drift" / "access" / "generated" / "tab_pool_counts.tex"
out.write_text(tex)
(ROOT / "artifacts" / "published" / "revision1" / "pool_counts_by_source.json").write_text(json.dumps({"sizes": SIZES, "sources": srcs, "counts": {str(n): dict(counts[n]) for n in SIZES}, "totals": tot}, indent=1))
print("wrote", out); print(tex[:900])
