#!/usr/bin/env python3
"""Extra rank tables for schedule-uncertainty and evaluated-gold-only pinning (reviewer-driven)."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_pool_union import (  # noqa: E402
    build_prop_ranks, fetch_chunk_rows, fetch_union_ids, gold_ordered_ids, pg_connect, write_rank_table,
)
from run_exact_ladder import load_manifest  # noqa: E402
from run_exact_ladder_pool import load_questions  # noqa: E402

SEEDS = list(range(1, 9))


def main() -> int:
    conn = pg_connect(); conn.autocommit = True; cur = conn.cursor()
    union = fetch_union_ids(cur)
    gold_all = gold_ordered_ids(fetch_chunk_rows(cur))
    for s in SEEDS:
        rows = build_prop_ranks(union, gold_all, s)
        print(f"rev1.prop_rank_s{s}", write_rank_table(cur, f"rev1.prop_rank_s{s}", rows))
    manifest = load_manifest()
    qs = load_questions(manifest, "primary200", None)
    evalg = {d for q in qs for d in q["expected_doc_ids"]}
    anchors = [g for g in gold_all if g in evalg]
    print("evaluated gold docs:", len(evalg), "anchors used:", len(anchors))
    rows = build_prop_ranks(union, anchors, 42)  # non-evaluated gold become ordinary shuffled docs
    print("rev1.prop_evalgold_s42", write_rank_table(cur, "rev1.prop_evalgold_s42", rows))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
