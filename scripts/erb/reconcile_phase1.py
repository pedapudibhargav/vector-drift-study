#!/usr/bin/env python3
"""Quality gate: reconcile Phase-1 sweep JSON vs DB for this sweep's run IDs only."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path


def _db_url() -> str:
    return os.environ.get(
        "DATABASE_URL",
        "postgresql://vector_drift:vector_drift@localhost:5432/vector_drift",
    ).replace("postgresql+asyncpg://", "postgresql://")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("results_json", type=Path)
    parser.add_argument("--tol", type=float, default=1e-9)
    args = parser.parse_args()

    payload = json.loads(args.results_json.read_text(encoding="utf-8"))
    runs = payload.get("runs") or []
    errors: list[str] = []
    warnings: list[str] = []

    try:
        import psycopg
    except ImportError:
        print("FAIL: psycopg not installed")
        return 2

    with psycopg.connect(_db_url()) as conn:
        for r in runs:
            run_id = r.get("experiment_run_id")
            cond = r.get("condition")
            n = r.get("corpus_scale_size")
            pq = r.get("per_question") or []
            if not run_id:
                errors.append(f"{cond} N={n}: missing experiment_run_id")
                continue
            if len(pq) != int(r.get("questions_evaluated") or 0):
                errors.append(
                    f"{cond} N={n}: per_question len {len(pq)} != questions_evaluated {r.get('questions_evaluated')}"
                )

            # Internal JSON consistency
            if pq:
                h10 = sum(1 for q in pq if q.get("hit_at_10")) / len(pq)
                h1 = sum(1 for q in pq if q.get("hit_at_1")) / len(pq)
                mrr = sum(float(q.get("mrr") or 0) for q in pq) / len(pq)
                if abs(h10 - float(r["hit_at_10"])) > 1e-9:
                    errors.append(f"{cond} N={n}: hit_at_10 JSON {r['hit_at_10']} != per_q {h10}")
                if abs(h1 - float(r["hit_at_1"])) > 1e-9:
                    errors.append(f"{cond} N={n}: hit_at_1 JSON {r['hit_at_1']} != per_q {h1}")
                if abs(mrr - float(r["mrr"])) > 1e-4:
                    errors.append(f"{cond} N={n}: mrr JSON {r['mrr']} != per_q {mrr:.4f}")

            row = conn.execute(
                """
                SELECT COUNT(*),
                       AVG(recall_at_10::int)::float,
                       AVG(COALESCE(mrr_score,0))::float,
                       COUNT(DISTINCT question_id)
                FROM vector_drift_results
                WHERE experiment_run_id = %s::uuid
                """,
                (run_id,),
            ).fetchone()
            db_n, db_h10, db_mrr, db_uq = row
            if int(db_n) != len(pq) and len(pq):
                # allow if DB has extras from re-insert, but distinct must match
                if int(db_uq) != len(pq):
                    errors.append(
                        f"{cond} N={n} run={run_id}: DB distinct q={db_uq} rows={db_n} vs JSON {len(pq)}"
                    )
                else:
                    warnings.append(
                        f"{cond} N={n}: DB rows={db_n} > distinct={db_uq} (dup inserts?)"
                    )
            if db_h10 is None:
                errors.append(f"{cond} N={n}: no DB rows for run {run_id}")
                continue
            if abs(float(db_h10) - float(r["hit_at_10"])) > 1e-6:
                errors.append(
                    f"{cond} N={n}: DB hit@10 {db_h10:.4f} != JSON {r['hit_at_10']}"
                )
            if abs(float(db_mrr) - float(r["mrr"])) > 1e-3:
                warnings.append(
                    f"{cond} N={n}: DB mrr {db_mrr:.4f} vs JSON {r['mrr']} (check schema)"
                )

            er = conn.execute(
                """
                SELECT condition, corpus_scale_size, run_name
                FROM experiment_runs WHERE id = %s::uuid
                """,
                (run_id,),
            ).fetchone()
            if not er:
                errors.append(f"{cond} N={n}: experiment_runs missing {run_id}")
            else:
                if er[0] != cond or int(er[1]) != int(n):
                    errors.append(
                        f"{cond} N={n}: experiment_runs mismatch {er} for {run_id}"
                    )

    # Delta sanity
    by = {(r["condition"], r["corpus_scale_size"]): r for r in runs}
    for d in payload.get("deltas") or []:
        n = d["corpus_scale_size"]
        raw = by.get(("raw", n))
        meta = by.get(("meta", n))
        if not raw or not meta:
            errors.append(f"delta N={n}: missing raw/meta run")
            continue
        expect = round(meta["hit_at_10"] - raw["hit_at_10"], 4)
        if abs(expect - float(d["delta_hit_at_10"])) > 1e-6:
            errors.append(f"delta N={n}: {d['delta_hit_at_10']} != {expect}")

    print(json.dumps({"errors": errors, "warnings": warnings, "n_runs": len(runs)}, indent=2))
    if errors:
        print(f"RECONCILE[FAIL] errors={len(errors)} warnings={len(warnings)}", file=sys.stderr)
        return 1
    print(f"RECONCILE[OK] warnings={len(warnings)}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
