#!/usr/bin/env python3
"""Why the planner's HNSW cost estimate is not monotone in ef_search (R3-B follow-up).

For OpenAI raw at 100k on both databases, records the planner's chosen plan and
the cost of the plan with the HNSW index (sequential and bitmap scans disabled)
for ef_search 100..1000, the heap and index page counts, and the ratio of
pgvector 0.8.6's hnswcostestimate (src/hnsw.c):

  ratio = (entryLevel*m + 2m*ef_search*layer0Selectivity) / tuples
  layer0Selectivity = 0.55*ln(tuples) / (ln(m)*(1+ln(ef_search)))

pgvector subtracts a TOAST discount from the index startup cost when
numIndexPages*ratio > heap pages and ratio < 0.5, so the index cost drops at
the ef_search where numIndexPages*ratio first exceeds the heap pages. The heap
page count differs between the databases (in-place updates on the original), so
the crossing point differs. Writes planner_cost_probe.json.
Connection: PGHOST/PGUSER/PGDATABASE; PGPASSWORD_5433 / PGPASSWORD_5434.
"""
import json
import math
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import explain_audit as ea  # noqa: E402

EFS = (100, 200, 300, 400, 500, 600, 700, 750, 800, 900, 1000)
M = 16


def connect(port):
    import psycopg2
    c = psycopg2.connect(host=os.environ.get("PGHOST", "localhost"), port=port, user=os.environ["PGUSER"],
                         password=os.environ[f"PGPASSWORD_{port}"], dbname=os.environ["PGDATABASE"])
    c.autocommit = True
    return c


def chain(p):
    out = []

    def w(n):
        out.append(n.get("Index Name") or n["Node Type"])
        for k in n.get("Plans") or []:
            w(k)
    w(p)
    return " > ".join(out)


def pgv_ratio(tuples, ef):
    entry = int(math.log(tuples) * (1 / math.log(M)))
    sel = 0.55 * math.log(tuples) / (math.log(M) * (1 + math.log(ef)))
    return min(1.0, (entry * M + 2 * M * ef * sel) / tuples)


def main():
    qs = ea.load_questions()
    spec = [t for t in ea.TABLES if t["embedder"] == "openai"][0]
    eid = qs[0]["eval_id"]
    lit = ea.vector_literal(ea.load_query_cache(spec["cache_style"], spec["cache_path"], [eid])[eid])
    sql = ea.build_sql(spec["table"], "raw")
    out = {"meta": {"created": time.strftime("%FT%TZ", time.gmtime()), "query": eid, "scale": 100000,
                    "pgvector_source": "https://github.com/pgvector/pgvector/blob/v0.8.6/src/hnsw.c (hnswcostestimate)"},
           "databases": {}}
    for port in (5434, 5433):
        cur = connect(port).cursor()
        cur.execute("SELECT relname, relpages, reltuples FROM pg_class WHERE relname IN ('document_chunks','idx_chunks_embedding_hnsw')")
        rel = {r[0]: {"relpages": int(r[1]), "reltuples": float(r[2])} for r in cur.fetchall()}
        heap = rel["document_chunks"]["relpages"]
        ipages = rel["idx_chunks_embedding_hnsw"]["relpages"]
        itup = rel["idx_chunks_embedding_hnsw"]["reltuples"]
        rows = []
        for ef in EFS:
            ea.set_hnsw_gucs(cur, ef)
            cur.execute("EXPLAIN (FORMAT JSON) " + sql, (lit, 100000, lit))
            p = cur.fetchone()[0][0]["Plan"]
            cur.execute("SET enable_seqscan = off")
            cur.execute("SET enable_bitmapscan = off")
            cur.execute("EXPLAIN (FORMAT JSON) " + sql, (lit, 100000, lit))
            f = cur.fetchone()[0][0]["Plan"]
            cur.execute("RESET enable_seqscan")
            cur.execute("RESET enable_bitmapscan")
            r = pgv_ratio(itup, ef)
            rows.append({"ef_search": ef, "chosen_plan": chain(p), "chosen_cost": p["Total Cost"],
                         "index_plan": chain(f), "index_cost": f["Total Cost"], "pgvector_ratio": round(r, 5),
                         "startup_pages": round(ipages * r, 1), "toast_discount_applies": bool(ipages * r > heap and r < 0.5)})
        out["databases"][str(port)] = {"heap_pages": heap, "index_pages": ipages, "index_tuples": itup,
                                       "threshold_ratio": round(heap / ipages, 5), "rows": rows}
        for x in rows:
            print(port, x["ef_search"], x["chosen_plan"][:45], round(x["chosen_cost"], 1), round(x["index_cost"], 1), x["pgvector_ratio"], x["toast_discount_applies"])
    path = Path(__file__).resolve().parents[3] / "artifacts/published/revision1/planner_cost_probe.json"
    path.write_text(json.dumps(out, indent=1))
    print("wrote", path)


if __name__ == "__main__":
    main()
