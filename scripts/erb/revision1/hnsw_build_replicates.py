#!/usr/bin/env python3
"""HNSW build-to-build variability (reviewer-driven): rebuild per-size indexes with shuffled insert order.

For each seed and size N: table rev1.nb_openai_s<seed>_<N> holds the first N documents in a seed-shuffled physical
order with its own HNSW index (m=16, ef_construction=64). Queries (primary-200 raw, ef_search=200) are run with the
index forced; recall@10 vs the stored exact lists and Hit@10 are recorded.
"""
import argparse, hashlib, json, os, sys, time
from pathlib import Path
import numpy as np, psycopg2

ROOT = Path(__file__).resolve().parents[3]
REV1 = ROOT / "artifacts" / "published" / "revision1"
SCALES = [5000, 10000, 15000, 20000, 25000, 40000, 50000, 75000, 100000]


def vec(v):
    return "[" + ",".join(f"{x:.9g}" for x in v) + "]"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", default="1,2,3,4")
    ap.add_argument("--scales", default=",".join(map(str, SCALES)))
    ap.add_argument("--ef", type=int, default=200)
    a = ap.parse_args()
    conn = psycopg2.connect(host="localhost", port=int(os.environ.get("PGPORT", 5433)), user=os.environ["PGUSER"],
                            password=os.environ["PGPASSWORD"], dbname=os.environ["PGDATABASE"])
    conn.autocommit = True; cur = conn.cursor()
    man = json.loads((ROOT / "data" / "erb_scale_manifest.json").read_text()); qs = {q["eval_id"]: q for q in man["questions"]}
    P = json.loads((ROOT / "artifacts/published/primary_questions_200.json").read_text())["question_ids"]
    cache = json.loads((ROOT / "data/erb_query_embed_cache_rev1.json").read_text())
    lad = json.loads((REV1 / "exact_ladder_openai_primary200.json").read_text())
    out_path = REV1 / "hnsw_build_replicates_openai.json"
    out = json.loads(out_path.read_text()) if out_path.exists() else {"cells": []}
    done = {(c["seed"], c["scale"]) for c in out["cells"]}
    cur.execute("SET maintenance_work_mem='1GB'")
    for seed in [int(s) for s in a.seeds.split(",")]:
        for N in [int(s) for s in a.scales.split(",")]:
            if (seed, N) in done:
                continue
            run = next(r for r in lad["runs"] if r["condition"] == "raw" and int(r["scale"]) == N)
            exact = {pq["question_id"]: pq["retrieved_doc_ids"] for pq in run["per_question"]}
            tbl = f"rev1.nb_openai_s{seed}_{N}"
            cur.execute(f"DROP TABLE IF EXISTS {tbl}")
            cur.execute(f"CREATE TABLE {tbl} AS SELECT doc_id, embedding FROM document_chunks WHERE scale_rank < {N} "
                        f"ORDER BY md5(doc_id || '{seed}')")
            t = time.time()
            cur.execute(f"CREATE INDEX ON {tbl} USING hnsw (embedding vector_cosine_ops) WITH (m=16, ef_construction=64)")
            build_s = time.time() - t
            cur.execute(f"ANALYZE {tbl}")
            cur.execute("SET enable_seqscan=off"); cur.execute(f"SET hnsw.ef_search={a.ef}")
            hits = 0; rec = 0.0; used = None
            for q in P:
                v = cache[q] if q in cache else cache["openai"][q]
                lit = vec(v)
                if used is None:
                    cur.execute(f"EXPLAIN SELECT doc_id FROM {tbl} ORDER BY embedding <=> %s::vector LIMIT 10", (lit,))
                    used = any("hnsw" in r[0].lower() for r in cur.fetchall())
                cur.execute(f"SELECT doc_id FROM {tbl} ORDER BY embedding <=> %s::vector LIMIT 10", (lit,))
                got = [r[0] for r in cur.fetchall()]
                hits += bool(set(got) & set(qs[q]["expected_doc_ids"]))
                rec += len(set(got) & set(exact[q])) / 10.0
            exact_hit = sum(bool(set(exact[q]) & set(qs[q]["expected_doc_ids"])) for q in P) / len(P)
            cell = {"seed": seed, "scale": N, "ef_search": a.ef, "hnsw_index_used": used, "build_seconds": round(build_s, 1),
                    "hit10": hits / len(P), "exact_hit10": exact_hit, "loss": exact_hit - hits / len(P), "recall10": rec / len(P)}
            out["cells"].append(cell); out_path.write_text(json.dumps(out, indent=1))
            print(cell, flush=True)
            cur.execute("RESET enable_seqscan"); cur.execute(f"DROP TABLE {tbl}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
