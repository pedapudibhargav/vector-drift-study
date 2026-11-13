#!/usr/bin/env python3
"""Question identifiers behind the v1 OpenAI list violations Reviewer 3 counted (R3-A).

Reads the published v1 OpenAI HNSW lists (raw and first-type filtered, nine sizes)
and lists, per size or size pair:
  containment - a raw top-10 document of the filtered type that is missing from the
                filtered top 10 at the same size (harness_lib.containment_reason;
                the other checks of that function found nothing);
  order swaps - two documents retrieved by the filtered condition at both sizes of a
                consecutive pair whose relative order is reversed.
Writes v1_list_violations_openai.json so the counts can be compared case by case
with the review (16, 10, 9, 11, 1, 1 and 5, 3, 1). No database access.
"""
import itertools
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import analyze_exact as ae  # noqa: E402
from harness_lib import containment_reason  # noqa: E402

OUT = Path(__file__).resolve().parents[3] / "artifacts/published/revision1/v1_list_violations_openai.json"


def main():
    doc_source, questions = ae.load_manifest()
    w = ae.wrap_hnsw_as_ladder(ae.HNSW_OPENAI)
    runs = {(r["condition"], r["scale"]): r for r in w["runs"]}
    scales = sorted({s for _, s in runs})

    def lists(cond, s):
        return {p["question_id"]: [str(x) for x in (p.get("retrieved_doc_ids") or [])] for p in runs[(cond, s)]["per_question"]}

    filt = ae.FILTER_FROM_COND["meta"]
    cont = {}
    for s in scales:
        raw, meta = lists("raw", s), lists("meta", s)
        bad = []
        for q in sorted(raw):
            allowed = ae.filter_source_types(questions[q], filt, doc_source)
            r = containment_reason(raw[q], meta.get(q, []), allowed, doc_source)
            if r:
                bad.append({"question": q, "reason": r})
        cont[str(s)] = bad
    swaps = {}
    for a, b in zip(scales, scales[1:]):
        A, B = lists("meta", a), lists("meta", b)
        qs = []
        for q in sorted(A):
            lb = B.get(q, [])
            common = [d for d in A[q] if d in lb]
            if any(lb.index(x) > lb.index(y) for x, y in itertools.combinations(common, 2)):
                qs.append(q)
        swaps[f"{a}-{b}"] = qs
    out = {"meta": {"created": time.strftime("%FT%TZ", time.gmtime()), "script": "v1_list_violations.py",
                    "source": "v1 OpenAI HNSW lists (analyze_exact.HNSW_OPENAI)", "filter": "first listed source type (v1 meta)"},
           "containment_counts": {k: len(v) for k, v in cont.items()}, "containment": cont,
           "order_swap_counts": {k: len(v) for k, v in swaps.items()}, "order_swaps": swaps}
    OUT.write_text(json.dumps(out, indent=1))
    print(out["containment_counts"], out["order_swap_counts"])


if __name__ == "__main__":
    main()
