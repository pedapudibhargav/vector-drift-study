#!/usr/bin/env python3
"""Export human-audit CSV from Postgres vector_drift_results (+ hit details)."""

from __future__ import annotations

import argparse
import csv
import json
import os
import random
from pathlib import Path


def main() -> int:
    import psycopg

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scale", type=int, required=True)
    parser.add_argument("--condition", default="raw")
    parser.add_argument("--n-hit", type=int, default=20)
    parser.add_argument("--n-miss", type=int, default=20)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args()

    url = os.environ.get(
        "DATABASE_URL",
        "postgresql://vector_drift:vector_drift@localhost:5432/vector_drift",
    ).replace("postgresql+asyncpg://", "postgresql://")

    with psycopg.connect(url) as conn:
        rows = conn.execute(
            """
            SELECT question_id, recall_at_10, retrieved_rank, document_recall,
                   retrieved_doc_ids, expected_doc_ids
            FROM vector_drift_results
            WHERE corpus_scale_size = %s AND condition = %s
            """,
            (args.scale, args.condition),
        ).fetchall()

    if not rows:
        raise SystemExit(f"no rows for scale={args.scale} condition={args.condition}")

    records = []
    for qid, hit10, rank, doc_rec, retrieved, expected in rows:
        records.append(
            {
                "question_id": qid,
                "hit_at_10": bool(hit10),
                "rank": rank,
                "document_recall": doc_rec,
                "retrieved_doc_ids": retrieved if isinstance(retrieved, list) else json.loads(retrieved or "[]"),
                "expected_doc_ids": expected if isinstance(expected, list) else json.loads(expected or "[]"),
            }
        )

    rng = random.Random(args.seed)
    hits = [r for r in records if r["hit_at_10"]]
    misses = [r for r in records if not r["hit_at_10"]]
    rng.shuffle(hits)
    rng.shuffle(misses)
    sample = hits[: args.n_hit] + misses[: args.n_miss]
    rng.shuffle(sample)

    out = args.out or Path(f"data/results/human_audit_n{args.scale}_{args.condition}.csv")
    out.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "question_id",
        "corpus_scale_size",
        "condition",
        "hit_at_10",
        "rank",
        "document_recall",
        "expected_doc_ids",
        "retrieved_doc_ids",
        "auditor",
        "label_correct",
        "failure_mode",
        "notes",
    ]
    with out.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        for r in sample:
            w.writerow(
                {
                    "question_id": r["question_id"],
                    "corpus_scale_size": args.scale,
                    "condition": args.condition,
                    "hit_at_10": r["hit_at_10"],
                    "rank": r["rank"],
                    "document_recall": r["document_recall"],
                    "expected_doc_ids": "|".join(r["expected_doc_ids"]),
                    "retrieved_doc_ids": "|".join(r["retrieved_doc_ids"]),
                    "auditor": "",
                    "label_correct": "",
                    "failure_mode": "",
                    "notes": "",
                }
            )
    print(
        f"wrote {out} rows={len(sample)} "
        f"hits={min(args.n_hit, len(hits))} misses={min(args.n_miss, len(misses))}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
