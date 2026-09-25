#!/usr/bin/env python3
"""Integrity gate: fail if published sweep has ID collisions or Hit@10 ≠ membership."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def check_run(run: dict) -> list[str]:
    errors: list[str] = []
    per_q = list(run.get("per_question") or [])
    ids = [q.get("question_id") for q in per_q]
    dups = [k for k, v in Counter(ids).items() if v > 1]
    scale = run.get("corpus_scale_size")
    cond = run.get("condition")
    if dups:
        errors.append(f"{cond} N={scale}: duplicate question_id x{len(dups)} e.g. {dups[:3]}")

    by = defaultdict(list)
    for q in per_q:
        by[q.get("question_id")].append(q)
    for qid, copies in by.items():
        if len(copies) < 2:
            continue
        hits = {bool(c.get("hit_at_10")) for c in copies}
        if len(hits) > 1:
            errors.append(f"{cond} N={scale}: conflicting Hit@10 for {qid}")

    empty = 0
    mismatch = 0
    checked = 0
    for q in per_q:
        ret = list(q.get("retrieved_doc_ids") or [])
        exp = list(q.get("expected_doc_ids") or [])
        if not ret:
            empty += 1
            continue
        if exp:
            checked += 1
            mem = bool(set(map(str, exp)) & set(map(str, ret[:10])))
            if mem != bool(q.get("hit_at_10")):
                mismatch += 1
    n = max(len(per_q), 1)
    empty_rate = empty / n
    # Hard-fail empty retrievals only when severe on raw (meta can be sparse filters,
    # but >25% empty still indicates broken retrieval / wrong source_type).
    limit = 0.05 if cond == "raw" else 0.25
    if empty_rate > limit:
        errors.append(
            f"{cond} N={scale}: empty retrieved_doc_ids on {empty}/{n} rows "
            f"({empty_rate:.0%} > {limit:.0%} threshold)"
        )
    if mismatch:
        errors.append(f"{cond} N={scale}: Hit@10 ≠ gold∈top-10 on {mismatch}/{checked} non-empty rows")
    return errors


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--sweep",
        type=Path,
        default=ROOT / "artifacts" / "published" / "erb_full_primary_corrected.json",
    )
    ap.add_argument("--allow-missing-expected", action="store_true")
    args = ap.parse_args()
    if not args.sweep.exists():
        print(f"FAIL: missing {args.sweep}", file=sys.stderr)
        return 2
    data = json.loads(args.sweep.read_text(encoding="utf-8"))
    runs = data.get("runs") or []
    all_errs: list[str] = []
    for run in runs:
        all_errs.extend(check_run(run))
    # Primary file uniqueness
    primary = ROOT / "artifacts" / "published" / "primary_questions_200.json"
    if primary.exists():
        p = json.loads(primary.read_text(encoding="utf-8"))
        ids = p.get("question_ids") or []
        dups = [k for k, v in Counter(ids).items() if v > 1]
        if dups:
            all_errs.append(f"primary_questions_200.json has duplicate ids: {dups[:5]}")
        if not p.get("unique_eval_ids"):
            all_errs.append("primary_questions_200.json missing unique_eval_ids=true flag")

    if all_errs:
        print("INTEGRITY FAIL:")
        for e in all_errs[:40]:
            print(f"  - {e}")
        if len(all_errs) > 40:
            print(f"  … +{len(all_errs) - 40} more")
        return 1
    print(f"INTEGRITY OK: {args.sweep.name} runs={len(runs)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
