#!/usr/bin/env python3
"""Exhaustive plan-choice coverage (audit follow-up to R3-B).

plan_audit_{5433,5434} recorded EXPLAIN (ANALYZE, BUFFERS) for all 200
questions at ef_search=200 but for a 40-question sample at 400 and 800, and
the per-size study recorded one probe plan per cell. Here every one of the 200
primary questions is planned (plain EXPLAIN, FORMAT JSON: the planner's
choice, without executing) in:
  (a) the single-table design on both databases: embedder x condition
      (raw, first-type filter) x 9 sizes x ef_search {200,400,800};
  (b) the per-size tables rev1.n_{openai,titan}_N on the fresh restore:
      raw x 9 sizes x ef_search {40,100,200,400,800}, default planner settings.
Session settings mirror explain_audit.py / eval_per_n_hnsw.py
(hnsw.iterative_scan = relaxed_order). Also records each table's
last (auto)analyze/vacuum times. Writes plan_coverage_full.json.
Connection: PGHOST/PGUSER/PGDATABASE from the environment, password per port
in PGPASSWORD_5433 / PGPASSWORD_5434.
"""
import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import explain_audit as ea  # noqa: E402

OUT = ea.REV1 / "plan_coverage_full.json" if hasattr(ea, "REV1") else None
SIZES = (5000, 10000, 15000, 20000, 25000, 40000, 50000, 75000, 100000)


def connect(port):
    import psycopg2
    c = psycopg2.connect(host=os.environ.get("PGHOST", "localhost"), port=port, user=os.environ["PGUSER"],
                         password=os.environ[f"PGPASSWORD_{port}"], dbname=os.environ["PGDATABASE"])
    c.autocommit = True
    return c


def hnsw_names(cur):
    cur.execute("SELECT indexname FROM pg_indexes WHERE indexdef ILIKE '%USING hnsw%'")
    return {r[0] for r in cur.fetchall()}


def uses(node, names):
    if node.get("Index Name") in names:
        return True
    return any(uses(ch, names) for ch in node.get("Plans") or [])


def signature(node):
    s = node.get("Node Type", "")
    kids = node.get("Plans") or []
    return s + (" > " + signature(kids[0]) if kids else "")


def plan(cur, sql, params):
    cur.execute("EXPLAIN (FORMAT JSON) " + sql, params)
    raw = cur.fetchone()[0]
    return (raw if isinstance(raw, list) else json.loads(raw))[0]["Plan"]


def table_state(cur, tables):
    cur.execute(
        "SELECT relname, last_vacuum, last_autovacuum, last_analyze, last_autoanalyze, n_dead_tup, n_mod_since_analyze "
        "FROM pg_stat_user_tables WHERE relname = ANY(%s)", (list(tables),))
    return {r[0]: {"last_vacuum": str(r[1]), "last_autovacuum": str(r[2]), "last_analyze": str(r[3]),
                   "last_autoanalyze": str(r[4]), "n_dead_tup": r[5], "n_mod_since_analyze": r[6]} for r in cur.fetchall()}


def main():
    qs = ea.load_questions()
    eids = [q["eval_id"] for q in qs]
    caches = {t["embedder"]: ea.load_query_cache(t["cache_style"], t["cache_path"], eids) for t in ea.TABLES}
    out = {"meta": {"created": time.strftime("%FT%TZ", time.gmtime()), "method": "plain EXPLAIN (FORMAT JSON), all 200 primary questions per cell",
                    "iterative_scan": "relaxed_order"}, "single_table": [], "per_size": [], "table_state": {}}
    for port in (5434, 5433):
        conn = connect(port)
        cur = conn.cursor()
        names = hnsw_names(cur)
        tabs = [t["table"] for t in ea.TABLES] + [f"n_{e}_{n}" for e in ("openai", "titan") for n in SIZES]
        out["table_state"][str(port)] = table_state(cur, tabs)
        cur.execute("SELECT name, setting FROM pg_settings WHERE name IN ('shared_buffers','work_mem','effective_cache_size','random_page_cost')")
        out["meta"][f"settings_{port}"] = dict(cur.fetchall())
        for spec in ea.TABLES:
            for cond in ("raw", "meta"):
                sql = ea.build_sql(spec["table"], cond)
                for n in SIZES:
                    for ef in (200, 400, 800):
                        ea.set_hnsw_gucs(cur, ef)
                        used, sigs = 0, {}
                        for q in qs:
                            lit = ea.vector_literal(caches[spec["embedder"]][q["eval_id"]])
                            params = (lit, n, str(q["source_types"][0]), lit) if cond == "meta" else (lit, n, lit)
                            p = plan(cur, sql, params)
                            u = uses(p, names)
                            used += u
                            sg = signature(p)
                            sigs[sg] = sigs.get(sg, 0) + 1
                        out["single_table"].append({"port": port, "embedder": spec["embedder"], "condition": cond, "scale": n,
                                                    "ef_search": ef, "n": len(qs), "n_hnsw": used, "frac_hnsw": used / len(qs), "signatures": sigs})
                print(port, spec["embedder"], cond, "done", flush=True)
        if port == 5433:
            for emb in ("openai", "titan"):
                for n in SIZES:
                    t = f"n_{emb}_{n}"
                    sql = f"SELECT doc_id, 1 - (embedding <=> %s::vector) FROM rev1.{t} ORDER BY embedding <=> %s::vector LIMIT 10"
                    for ef in (40, 100, 200, 400, 800):
                        ea.set_hnsw_gucs(cur, ef)
                        used, sigs = 0, {}
                        for q in qs:
                            lit = ea.vector_literal(caches[emb][q["eval_id"]]); p = plan(cur, sql, (lit, lit))
                            u = uses(p, names)
                            used += u
                            sg = signature(p)
                            sigs[sg] = sigs.get(sg, 0) + 1
                        out["per_size"].append({"embedder": emb, "table": t, "scale": n, "ef_search": ef, "n": len(qs),
                                                "n_hnsw": used, "frac_hnsw": used / len(qs), "signatures": sigs})
                print("per-size", emb, "done", flush=True)
        conn.close()
    path = Path(__file__).resolve().parents[3] / "artifacts/published/revision1/plan_coverage_full.json"
    path.write_text(json.dumps(out, indent=1))
    print("wrote", path)


if __name__ == "__main__":
    main()
