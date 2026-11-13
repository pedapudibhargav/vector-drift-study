#!/usr/bin/env python3
"""Record the plan shape of the v1 Titan statement as a generic and as a custom plan.

Companion to titan_v1_plan_replay.py. On the frozen original copy (port 5434), the
v1 statement is PREPAREd with the parameter types psycopg 3 sends from 40k on
(vector, int4, vector, int2) and EXPLAINed with plan_cache_mode forced to
generic and to custom, at 75k and 100k with the first primary question's
vector. Adds a "plan_shapes" key to titan_v1_plan_replay.json.
Environment: PGPASSWORD for port 5434.
"""
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import explain_audit as ea  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "artifacts/published/revision1/titan_v1_plan_replay.json"


def chain(n):
    out = [n.get("Index Name") or n["Node Type"]]
    for k in n.get("Plans") or []:
        out += chain(k)
    return out


def main():
    import psycopg2
    qs = ea.load_questions()
    spec = [t for t in ea.TABLES if t["embedder"] == "titan"][0]
    eid = qs[0]["eval_id"]
    lit = ea.vector_literal(ea.load_query_cache(spec["cache_style"], spec["cache_path"], [eid])[eid])
    c = psycopg2.connect(host="localhost", port=5434, user="vector_drift", password=os.environ["PGPASSWORD"], dbname="vector_drift")
    c.autocommit = True
    cur = c.cursor()
    cur.execute("SET hnsw.ef_search = 200")
    cur.execute("SET hnsw.iterative_scan = relaxed_order")
    cur.execute("PREPARE q(vector, int4, vector, int2) AS SELECT doc_id, 1 - (embedding <=> $1) AS score "
                "FROM document_chunks_titan WHERE embedding IS NOT NULL AND scale_rank IS NOT NULL AND scale_rank < $2 "
                "ORDER BY embedding <=> $3 LIMIT $4")
    shapes = []
    for n in (75000, 100000):
        for mode in ("force_generic_plan", "force_custom_plan"):
            cur.execute(f"SET plan_cache_mode = {mode}")
            cur.execute("EXPLAIN (FORMAT JSON) EXECUTE q(%s::vector, %s, %s::vector, 10)", (lit, n, lit))
            p = cur.fetchone()[0][0]["Plan"]
            shapes.append({"scale": n, "plan_cache_mode": mode, "plan": " > ".join(chain(p)),
                           "uses_hnsw": any("hnsw" in x for x in chain(p))})
            print(n, mode, shapes[-1]["plan"])
    d = json.loads(OUT.read_text())
    d["plan_shapes"] = {"question": eid, "parameter_types": "vector, int4, vector, int2", "rows": shapes}
    OUT.write_text(json.dumps(d, indent=1))
    print("updated", OUT)


if __name__ == "__main__":
    main()
