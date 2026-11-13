#!/usr/bin/env python3
"""Memory working set of the per-size HNSW indexes (R1-3 follow-up).

For each embedder and ladder size, the fresh-restore container is restarted so
that PostgreSQL's shared buffers start empty; then the 200 primary questions
are run twice against rev1.n_<embedder>_<N> at ef_search=200 with
hnsw.iterative_scan=relaxed_order (the per-size study's setting), and
pg_buffercache counts the 8 kB pages of the HNSW index, the heap and the TOAST
relation that are resident in shared buffers. That count is the memory the
query workload actually touched (its working set); the index size is the
memory needed to hold the whole index. Writes memory_footprint_per_n.json.
Environment: PGHOST/PGUSER/PGDATABASE/PGPASSWORD (port 5433), DOCKER_BIN.
"""
import json
import os
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import explain_audit as ea  # noqa: E402

SIZES = (5000, 10000, 15000, 20000, 25000, 40000, 50000, 75000, 100000)
CONTAINER = "vector-drift-rev"
OUT = Path(__file__).resolve().parents[3] / "artifacts/published/revision1/memory_footprint_per_n.json"


def connect():
    import psycopg2
    for _ in range(60):
        try:
            c = psycopg2.connect(host=os.environ.get("PGHOST", "localhost"), port=5433, user=os.environ["PGUSER"],
                                 password=os.environ["PGPASSWORD"], dbname=os.environ["PGDATABASE"])
            c.autocommit = True
            return c
        except Exception:
            time.sleep(1)
    raise SystemExit("database did not come back")


def restart():
    subprocess.run([os.environ["DOCKER_BIN"], "restart", CONTAINER], check=True, capture_output=True)


def main():
    qs = ea.load_questions()
    eids = [q["eval_id"] for q in qs]
    caches = {t["embedder"]: ea.load_query_cache(t["cache_style"], t["cache_path"], eids) for t in ea.TABLES}
    conn = connect()
    cur = conn.cursor()
    cur.execute("CREATE EXTENSION IF NOT EXISTS pg_buffercache")
    cur.execute("SHOW shared_buffers")
    sb = cur.fetchone()[0]
    conn.close()
    rows = []
    for emb in ("openai", "titan"):
        for n in SIZES:
            restart()
            conn = connect()
            cur = conn.cursor()
            t = f"rev1.n_{emb}_{n}"
            cur.execute("SELECT count(*) FROM pg_buffercache WHERE relfilenode IS NOT NULL")
            before = cur.fetchone()[0]
            ea.set_hnsw_gucs(cur, 200)
            sql = f"SELECT doc_id FROM {t} ORDER BY embedding <=> %s::vector LIMIT 10"
            cur.execute("EXPLAIN (FORMAT JSON) " + sql, (ea.vector_literal(caches[emb][eids[0]]),))
            plan = json.dumps(cur.fetchone()[0])
            t0 = time.time()
            for _ in range(2):
                for e in eids:
                    cur.execute(sql, (ea.vector_literal(caches[emb][e]),))
                    cur.fetchall()
            secs = time.time() - t0
            cur.execute(
                """
                WITH rels AS (
                  SELECT 'index' AS kind, i.indexrelid AS oid FROM pg_index i JOIN pg_class c ON c.oid = i.indexrelid
                    JOIN pg_am a ON a.oid = c.relam WHERE i.indrelid = %s::regclass AND a.amname = 'hnsw'
                  UNION ALL SELECT 'heap', %s::regclass::oid
                  UNION ALL SELECT 'toast', reltoastrelid FROM pg_class WHERE oid = %s::regclass)
                SELECT r.kind, pg_relation_size(r.oid),
                       (SELECT count(*) FROM pg_buffercache b
                         WHERE b.relfilenode = pg_relation_filenode(r.oid)
                           AND b.reldatabase = (SELECT oid FROM pg_database WHERE datname = current_database()))
                FROM rels r
                """, (t, t, t))
            res = {k: {"relation_bytes": int(sz), "resident_pages": int(pg), "resident_mb": round(pg * 8192 / 1e6, 1)}
                   for k, sz, pg in cur.fetchall()}
            row = {"embedder": emb, "scale": n, "table": t, "ef_search": 200, "queries": 2 * len(eids),
                   "sweep_seconds": round(secs, 2), "buffers_in_use_after_restart": before,
                   "uses_hnsw": '"hnsw' in plan.lower() or "_embedding_idx" in plan or "hnsw" in plan, "resident": res}
            idx = res.get("index", {})
            row["index_resident_fraction"] = round(idx.get("resident_pages", 0) * 8192 / max(1, idx.get("relation_bytes", 1)), 4)
            rows.append(row)
            print(emb, n, {k: v["resident_mb"] for k, v in res.items()}, "idx frac", row["index_resident_fraction"], flush=True)
            conn.close()
    OUT.write_text(json.dumps({"meta": {"created": time.strftime("%FT%TZ", time.gmtime()), "shared_buffers": sb,
                                        "method": __doc__.strip().splitlines()[0]}, "rows": rows}, indent=1))
    print("wrote", OUT)


if __name__ == "__main__":
    main()
