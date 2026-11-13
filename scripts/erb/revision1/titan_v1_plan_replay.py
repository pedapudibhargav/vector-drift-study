#!/usr/bin/env python3
"""Why the v1 Titan "HNSW" lists equal exact search (R3-B follow-up).

The v1 Titan sweep (scripts/erb/run_scale_sweep_titan.py) used psycopg 3,
which sends the size bound and LIMIT as server-side parameters and prepares a
statement after five executions; PostgreSQL may then reuse a generic plan.
This script replays the v1 query text and order (sizes ascending; raw then
first-type filter per size; ef_search=200, iterative_scan=relaxed_order) on
the frozen original database copy, twice:
  prepared   - psycopg 3 defaults, as in v1;
  unprepared - prepare_threshold=None (every statement planned with its values).
For each cell it counts lists identical to the exact reference lists and, in
the prepared run, reads pg_prepared_statements (generic_plans, custom_plans).
Writes titan_v1_plan_replay.json.
Environment: PGPASSWORD for port 5434 (user/db vector_drift).
"""
import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import explain_audit as ea  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
SIZES = (5000, 10000, 15000, 20000, 25000, 40000, 50000, 75000, 100000)


def run(mode, qs, cache, exact):
    import psycopg
    conn = psycopg.connect(host="localhost", port=5434, user="vector_drift", password=os.environ["PGPASSWORD"],
                           dbname="vector_drift", autocommit=True)
    if mode == "unprepared":
        conn.prepare_threshold = None
    cells = []
    for n in SIZES:
        for cond in ("raw", "meta"):
            conn.execute("SET hnsw.ef_search = 200")
            conn.execute("SET hnsw.iterative_scan = relaxed_order")
            same = 0
            for q in qs:
                lit = ea.vector_literal(cache[q["eval_id"]])
                where = "embedding IS NOT NULL AND scale_rank IS NOT NULL AND scale_rank < %s"
                params = [lit, n]
                if cond == "meta":
                    where += " AND source_type = %s"
                    params.append(str(q["source_types"][0]))
                params += [lit, 10]
                sql = (f"\n            SELECT doc_id, 1 - (embedding <=> %s::vector) AS score\n            FROM document_chunks_titan\n"
                       f"            WHERE {where}\n            ORDER BY embedding <=> %s::vector\n            LIMIT %s\n        ")
                ids = [r[0] for r in conn.execute(sql, params).fetchall()]
                same += ids == exact[("raw" if cond == "raw" else "meta_first", n, q["eval_id"])]
            ps = conn.execute("SELECT left(statement, 60), generic_plans, custom_plans FROM pg_prepared_statements").fetchall()
            cells.append({"scale": n, "condition": cond, "n": len(qs), "identical_to_exact": same,
                          "prepared_statements": [{"statement": s, "generic_plans": g, "custom_plans": c} for s, g, c in ps]})
            print(mode, n, cond, same, [(g, c) for _, g, c in ps], flush=True)
    conn.close()
    return cells


def main():
    qs = ea.load_questions()
    eids = [q["eval_id"] for q in qs]
    spec = [t for t in ea.TABLES if t["embedder"] == "titan"][0]
    cache = ea.load_query_cache(spec["cache_style"], spec["cache_path"], eids)
    ex = json.loads((ROOT / "artifacts/published/revision1/exact_ladder_titan_primary200.json").read_text())
    exact = {(r["condition"], r["scale"], p["question_id"]): p["retrieved_doc_ids"] for r in ex["runs"] for p in r["per_question"]}
    out = {"meta": {"created": time.strftime("%FT%TZ", time.gmtime()), "database": "frozen original copy (port 5434)",
                    "v1_script": "scripts/erb/run_scale_sweep_titan.py", "driver": "psycopg 3 (prepare_threshold default 5)"}}
    for mode in ("prepared", "unprepared"):
        out[mode] = run(mode, qs, cache, exact)
    (ROOT / "artifacts/published/revision1/titan_v1_plan_replay.json").write_text(json.dumps(out, indent=1))
    print("wrote")


if __name__ == "__main__":
    main()
