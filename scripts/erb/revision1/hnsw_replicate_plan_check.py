#!/usr/bin/env python3
"""Plan verification for the HNSW build replicates (seed 1, all nine sizes).
The original replicate runs recorded hnsw_index_used=false because their plan check searched the plan text for 'hnsw',
but the auto-named indexes (<table>_embedding_idx) do not contain that word. Here each seed-1 table is rebuilt exactly as
in hnsw_build_replicates.py, the first question's EXPLAIN is stored, the index access method is read from pg_index/pg_am,
and Hit@10 / recall@10 are compared with the stored cells."""
import json, os, time
from pathlib import Path
import psycopg2
ROOT = Path(__file__).resolve().parents[3]; REV1 = ROOT / "artifacts/published/revision1"
SCALES = [5000, 10000, 15000, 20000, 25000, 40000, 50000, 75000, 100000]
vec = lambda v: "[" + ",".join(f"{x:.9g}" for x in v) + "]"
conn = psycopg2.connect(host="localhost", port=int(os.environ.get("PGPORT", 5433)), user=os.environ["PGUSER"], password=os.environ["PGPASSWORD"], dbname=os.environ["PGDATABASE"])
conn.autocommit = True; cur = conn.cursor()
man = json.loads((ROOT / "data/erb_scale_manifest.json").read_text()); qs = {q["eval_id"]: q for q in man["questions"]}
P = json.loads((ROOT / "artifacts/published/primary_questions_200.json").read_text())["question_ids"]
cache = json.loads((ROOT / "data/erb_query_embed_cache_rev1.json").read_text())
lad = json.loads((REV1 / "exact_ladder_openai_primary200.json").read_text())
stored = {(c["seed"], c["scale"]): c for c in json.loads((REV1 / "hnsw_build_replicates_openai.json").read_text())["cells"]}
cur.execute("SELECT version()"); pg = cur.fetchone()[0]
cur.execute("SELECT extversion FROM pg_extension WHERE extname='vector'"); pv = cur.fetchone()[0]
out = {"postgresql": pg, "pgvector": pv, "seed": 1, "ef_search": 200, "cells": []}
cur.execute("SET maintenance_work_mem='1GB'")
for N in SCALES:
    run = next(r for r in lad["runs"] if r["condition"] == "raw" and int(r["scale"]) == N)
    exact = {pq["question_id"]: pq["retrieved_doc_ids"] for pq in run["per_question"]}
    tbl = f"rev1.nbchk_openai_s1_{N}"
    cur.execute(f"DROP TABLE IF EXISTS {tbl}")
    cur.execute(f"CREATE TABLE {tbl} AS SELECT doc_id, embedding FROM document_chunks WHERE scale_rank < {N} ORDER BY md5(doc_id || '1')")
    t = time.time(); cur.execute(f"CREATE INDEX ON {tbl} USING hnsw (embedding vector_cosine_ops) WITH (m=16, ef_construction=64)"); build = time.time() - t
    cur.execute(f"ANALYZE {tbl}")
    cur.execute("SELECT i.indexname, am.amname FROM pg_indexes i JOIN pg_class c ON c.relname=i.indexname JOIN pg_am am ON am.oid=c.relam WHERE i.schemaname='rev1' AND i.tablename=%s", (f"nbchk_openai_s1_{N}",))
    idx = cur.fetchall()
    cur.execute("SET enable_seqscan=off"); cur.execute("SET hnsw.ef_search=200")
    plan = None; hits = 0; rec = 0.0
    for q in P:
        v = cache[q] if q in cache else cache["openai"][q]; lit = vec(v)
        if plan is None:
            cur.execute(f"EXPLAIN SELECT doc_id FROM {tbl} ORDER BY embedding <=> %s::vector LIMIT 10", (lit,)); plan = [r[0] for r in cur.fetchall()]
        cur.execute(f"SELECT doc_id FROM {tbl} ORDER BY embedding <=> %s::vector LIMIT 10", (lit,)); got = [r[0] for r in cur.fetchall()]
        hits += bool(set(got) & set(qs[q]["expected_doc_ids"])); rec += len(set(got) & set(exact[q])) / 10.0
    s = stored[(1, N)]
    cell = {"scale": N, "index_access_method": [a for _, a in idx], "plan_first_line": plan[0], "index_scan_used": any("Index Scan" in l and "embedding_idx" in l for l in plan),
            "hit10": hits / len(P), "recall10": rec / len(P), "stored_hit10": s["hit10"], "stored_recall10": s["recall10"],
            "matches_stored": abs(hits / len(P) - s["hit10"]) < 1e-9 and abs(rec / len(P) - s["recall10"]) < 1e-9}
    out["cells"].append(cell); print(cell, flush=True)
    cur.execute("RESET enable_seqscan"); cur.execute(f"DROP TABLE {tbl}")
(REV1 / "hnsw_replicate_plan_check.json").write_text(json.dumps(out, indent=1))
print("DONE all_index_scan", all(c["index_scan_used"] for c in out["cells"]), "all_match", all(c["matches_stored"] for c in out["cells"]))
