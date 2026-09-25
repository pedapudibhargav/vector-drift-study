#!/usr/bin/env python3
"""Export human-audit CSV: mix of hits and misses from a scale sweep result."""

from __future__ import annotations

import argparse
import csv
import json
import random
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("sweep_json", type=Path)
    parser.add_argument("--scale", type=int, required=True)
    parser.add_argument("--condition", default="raw")
    parser.add_argument("--n-hit", type=int, default=20)
    parser.add_argument("--n-miss", type=int, default=20)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args()

    payload = json.loads(args.sweep_json.read_text(encoding="utf-8"))
    # Prefer detailed per_question from runs if present; else from DB export shape
    per_q: list[dict] = []
    for run in payload.get("runs") or []:
        if (
            run.get("corpus_scale_size") == args.scale
            and run.get("condition") == args.condition
            and run.get("per_question")
        ):
            per_q = list(run["per_question"])
            break

    if not per_q:
        # try results file that only has aggregates — load from companion if any
        raise SystemExit(
            "No per_question in sweep JSON for that scale/condition. "
            "Re-run sweep with persistence or a results file that includes per_question."
        )

    rng = random.Random(args.seed)
    hits = [q for q in per_q if q.get("hit_at_10")]
    misses = [q for q in per_q if not q.get("hit_at_10")]
    rng.shuffle(hits)
    rng.shuffle(misses)
    sample = hits[: args.n_hit] + misses[: args.n_miss]
    rng.shuffle(sample)

    out = args.out or Path(
        f"data/results/human_audit_n{args.scale}_{args.condition}.csv"
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "question_id",
        "corpus_scale_size",
        "condition",
        "hit_at_10",
        "rank",
        "document_recall",
        "retrieved_doc_ids",
        "auditor",
        "label_correct",  # yes/no/unsure — human fills
        "notes",
    ]
    with out.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        for q in sample:
            w.writerow(
                {
                    "question_id": q.get("question_id"),
                    "corpus_scale_size": args.scale,
                    "condition": args.condition,
                    "hit_at_10": q.get("hit_at_10"),
                    "rank": q.get("rank"),
                    "document_recall": q.get("document_recall"),
                    "retrieved_doc_ids": "|".join(q.get("retrieved_doc_ids") or []),
                    "auditor": "",
                    "label_correct": "",
                    "notes": "",
                }
            )
    print(f"wrote {out} rows={len(sample)} hits={min(args.n_hit,len(hits))} misses={min(args.n_miss,len(misses))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
