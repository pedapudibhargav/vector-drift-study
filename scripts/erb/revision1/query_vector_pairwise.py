#!/usr/bin/env python3
"""Cosine similarity between the cached query vectors of different primary questions.

Supports the statement that a cached vector is far closer to a fresh embedding of
its own question (cosine >= 0.9968, query_vector_provenance_openai.json) than to
the vector of any other question. Reads the cached OpenAI query vectors of the
200 primary questions and writes the maximum, the 99th percentile and the most
similar pair to query_vector_pairwise_openai.json. No database or API access.
"""
import json
import math
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import explain_audit as ea  # noqa: E402

OUT = Path(__file__).resolve().parents[3] / "artifacts/published/revision1/query_vector_pairwise_openai.json"


def main():
    qs = ea.load_questions()
    eids = [q["eval_id"] for q in qs]
    spec = [t for t in ea.TABLES if t["embedder"] == "openai"][0]
    cache = ea.load_query_cache(spec["cache_style"], spec["cache_path"], eids)
    vecs = []
    for e in eids:
        v = [float(x) for x in cache[e]]
        n = math.sqrt(sum(x * x for x in v))
        vecs.append([x / n for x in v])
    sims = []
    for i in range(len(vecs)):
        for j in range(i + 1, len(vecs)):
            sims.append((sum(a * b for a, b in zip(vecs[i], vecs[j])), eids[i], eids[j]))
    sims.sort()
    vals = [s for s, _, _ in sims]
    top = sims[-1]
    out = {"meta": {"created": time.strftime("%FT%TZ", time.gmtime()), "script": "query_vector_pairwise.py",
                    "bank": "primary200", "embedder": "openai text-embedding-3-small (cached query vectors)"},
           "n_questions": len(eids), "n_pairs": len(sims), "max_pairwise_cosine": round(top[0], 6),
           "max_pair": [top[1], top[2]], "p99_pairwise_cosine": round(vals[int(0.99 * (len(vals) - 1))], 6),
           "mean_pairwise_cosine": round(sum(vals) / len(vals), 6)}
    OUT.write_text(json.dumps(out, indent=1))
    print(out)


if __name__ == "__main__":
    main()
