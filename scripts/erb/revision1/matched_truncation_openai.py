#!/usr/bin/env python3
"""Byte-identical input truncation across embedders (R1.2).

The Titan arm embedded document_chunks_titan.chunk_text, which equals the
OpenAI input truncated to its first 24,000 characters for exactly 90 ladder
documents. This script re-embeds those 90 documents with OpenAI
text-embedding-3-small using the Titan input string byte for byte, so that
both embedders see identical text for every one of the 99,998 ladder
documents, and re-runs the exact OpenAI ladder (raw and meta_in, nine sizes,
primary-200) with the 90 vectors replaced.

Method: for each question, size and condition the exact top-10 is computed in
PostgreSQL over all documents except the 90 (sequential scan, ties by doc_id),
and merged with the 90 documents scored in float64 numpy (cosine). Running the
same merge with the 90 ORIGINAL vectors must reproduce the published OpenAI
lists exactly; that is checked before any result is written (fail closed).

Outputs artifacts/published/revision1/matched_truncation_openai_primary200.json.
Vectors are cached in data/rev1_matched_trunc24k_openai.json (not re-embedded
on re-run).
"""

from __future__ import annotations

import json
import os
import ssl
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

_SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_SCRIPT_DIR))
import embed_pool_extension as emb  # noqa: E402
import run_exact_ladder as ladder  # noqa: E402

REV1 = ladder.REV1
OUT = REV1 / "matched_truncation_openai_primary200.json"
VEC_CACHE = ladder.DATA / "rev1_matched_trunc24k_openai.json"
OPENAI_LADDER = REV1 / "exact_ladder_openai_primary200.json"
TITAN_LADDER = REV1 / "exact_ladder_titan_primary200.json"
CONDS = ("raw", "meta_in")
B, SEED = 10000, 42


def parse_vec(s: str) -> np.ndarray:
    return np.array([float(x) for x in s.strip("[]").split(",")], dtype=np.float64)


def load_ladder_flags(path: Path, cond: str):
    d = json.loads(path.read_text())
    out = {}
    for run in d["runs"]:
        if run["condition"] != cond:
            continue
        out[int(run["scale"])] = {p["question_id"]: p for p in run["per_question"]}
    return out


def ci(v, idx, lo=2.5, hi=97.5):
    b = v[idx].mean(axis=1)
    a, c = np.percentile(b, [lo, hi])
    return {"estimate": round(float(v.mean()), 6), "ci_lo": round(float(a), 6), "ci_hi": round(float(c), 6)}


def main() -> int:
    conn = ladder.pg_connect()
    conn.autocommit = True
    cur = conn.cursor()
    ladder.apply_seqscan_session(cur)
    pg_version, pgv = ladder.session_pg_versions(cur)
    cur.execute(
        """SELECT o.doc_id, t.chunk_text, o.embedding::text, o.scale_rank, o.source_type, o.is_gold_anchor
           FROM document_chunks o JOIN document_chunks_titan t USING (doc_id)
           WHERE o.chunk_text <> t.chunk_text ORDER BY o.doc_id"""
    )
    rows = cur.fetchall()
    ids = [r[0] for r in rows]
    texts = {r[0]: r[1] for r in rows}
    orig = {r[0]: parse_vec(r[2]) for r in rows}
    rank = {r[0]: int(r[3]) for r in rows}
    src = {r[0]: r[4] for r in rows}
    n_gold = sum(1 for r in rows if r[5])
    if len(ids) != 90 or any(len(texts[i]) != 24000 for i in ids):
        print(f"FAIL expected 90 documents with 24,000-character Titan text, got {len(ids)}", file=sys.stderr)
        return 1
    cur.execute(
        "SELECT count(*) FROM document_chunks o JOIN document_chunks_titan t USING (doc_id) "
        "WHERE left(o.chunk_text, 24000) = t.chunk_text AND o.chunk_text <> t.chunk_text"
    )
    if cur.fetchone()[0] != 90:
        print("FAIL Titan text is not a prefix of the OpenAI text for all 90", file=sys.stderr)
        return 1

    cache = json.loads(VEC_CACHE.read_text()) if VEC_CACHE.is_file() else {}
    todo = [i for i in ids if i not in cache]
    tokens = 0
    if todo:
        key = os.environ.get("OPENAI_API_KEY") or ""
        if not key:
            print("OPENAI_API_KEY not set", file=sys.stderr)
            return 2
        ctx = ssl.create_default_context()
        for s in range(0, len(todo), 16):
            batch = todo[s : s + 16]
            vecs, tk = emb.embed_batch([texts[i] for i in batch], base_url="https://api.openai.com", api_key=key, ssl_ctx=ctx)
            tokens += tk
            for i, v in zip(batch, vecs):
                cache[i] = v
            VEC_CACHE.write_text(json.dumps(cache))
        print(f"embedded {len(todo)} documents, {tokens} tokens", flush=True)
    new = {i: np.array(cache[i], dtype=np.float64) for i in ids}
    cos_orig_new = {i: float(orig[i] @ new[i] / (np.linalg.norm(orig[i]) * np.linalg.norm(new[i]))) for i in ids}

    manifest = ladder.load_manifest()
    qs = ladder.load_questions(manifest, "primary200")
    qvecs, missing = ladder.load_query_cache("openai", [q["eval_id"] for q in qs], ladder.OPENAI_CACHE)
    if missing:
        print("FAIL missing query vectors", file=sys.stderr)
        return 1
    doc_source = ladder.build_doc_source_map(manifest)
    pub = {c: load_ladder_flags(OPENAI_LADDER, c) for c in CONDS}
    tit = {c: load_ladder_flags(TITAN_LADDER, c) for c in CONDS}
    scales = sorted(pub["raw"])
    idarr = list(ids)

    def unit(v):
        return v / np.linalg.norm(v)

    O = np.stack([unit(orig[i]) for i in idarr])
    Nw = np.stack([unit(new[i]) for i in idarr])
    res = {c: {s: {} for s in scales} for c in CONDS}
    mismatches = 0
    for q in qs:
        eid = q["eval_id"]
        qv = np.array(qvecs[eid], dtype=np.float64)
        qu = unit(qv)
        so, sn = O @ qu, Nw @ qu
        for c in CONDS:
            where, params = ladder.condition_filter_sql(c, q, doc_source)
            allowed_types = None if c == "raw" else set(params[0])
            for s in scales:
                base = ladder.exact_search(cur, "document_chunks", qvecs[eid], s,
                                           where + " AND doc_id <> ALL(%s)", (*params, idarr), 10)
                cand_o = list(base)
                cand_n = list(base)
                for j, d in enumerate(idarr):
                    if rank[d] >= s or (allowed_types is not None and src[d] not in allowed_types):
                        continue
                    cand_o.append((d, float(so[j])))
                    cand_n.append((d, float(sn[j])))
                lo = [d for d, _ in sorted(cand_o, key=lambda x: (-x[1], x[0]))[:10]]
                ln = [d for d, _ in sorted(cand_n, key=lambda x: (-x[1], x[0]))[:10]]
                if lo != pub[c][s][eid]["retrieved_doc_ids"]:
                    mismatches += 1
                gold = {str(x) for x in q.get("expected_doc_ids") or []}
                res[c][s][eid] = {"orig_list_reproduced": lo == pub[c][s][eid]["retrieved_doc_ids"],
                                  "matched_list": ln,
                                  "hit_at_10": any(d in gold for d in ln),
                                  "hit_at_1": bool(ln) and ln[0] in gold,
                                  "changed": ln != lo}
    cur.close()
    conn.close()
    if mismatches:
        print(f"FAIL merge with original vectors does not reproduce {mismatches} published lists", file=sys.stderr)
        return 1

    qids = [q["eval_id"] for q in qs]
    rng = np.random.default_rng(SEED)
    idx = rng.integers(0, len(qids), size=(B, len(qids)))
    summary = {}
    for c in CONDS:
        lo_s, hi_s = scales[0], scales[-1]
        m = {s: np.array([res[c][s][e]["hit_at_10"] for e in qids], float) for s in scales}
        p = {s: np.array([pub[c][s][e]["hit_at_10"] for e in qids], float) for s in scales}
        t = {s: np.array([tit[c][s][e]["hit_at_10"] for e in qids], float) for s in scales}
        dm, dp, dt = m[lo_s] - m[hi_s], p[lo_s] - p[hi_s], t[lo_s] - t[hi_s]
        summary[c] = {
            "hit10_matched": {s: round(float(m[s].mean()), 6) for s in scales},
            "hit10_published": {s: round(float(p[s].mean()), 6) for s in scales},
            "hit1_matched": {s: round(float(np.mean([res[c][s][e]["hit_at_1"] for e in qids])), 6) for s in scales},
            "questions_with_changed_list": {s: int(sum(res[c][s][e]["changed"] for e in qids)) for s in scales},
            "questions_with_changed_hit10": {s: int((m[s] != p[s]).sum()) for s in scales},
            "drop_matched_95": ci(dm, idx),
            "drop_matched_minus_published_95": ci(dm - dp, idx),
            "openai_matched_minus_titan_drop_90": ci(dm - dt, idx, 5, 95),
            "openai_published_minus_titan_drop_90": ci(dp - dt, idx, 5, 95),
            "openai_matched_minus_titan_level100k_90": ci(m[hi_s] - t[hi_s], idx, 5, 95),
        }
    out = {
        "meta": {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "purpose": "R1.2 byte-identical input truncation for both embedders",
            "n_documents_reembedded": len(ids), "n_gold_anchors_among_them": n_gold,
            "input_rule": "OpenAI input := Titan chunk_text (first 24,000 characters) for the 90 documents; all other 99,908 inputs were already identical",
            "model": emb.EMBEDDING_MODEL, "tokens_used_this_run": tokens,
            "cosine_original_vs_matched_vector": {"min": round(min(cos_orig_new.values()), 6), "median": round(float(np.median(list(cos_orig_new.values()))), 6)},
            "postgresql_version": pg_version, "pgvector_version": pgv,
            "reproduction": "merge with the original 90 vectors reproduced all published raw and meta_in lists (fail closed)",
            "bootstrap_B": B, "bootstrap_seed": SEED, "scales": scales, "conditions": list(CONDS),
        },
        "summary": summary,
        "doc_ids": idarr,
    }
    OUT.write_text(json.dumps(out, indent=1))
    print(json.dumps({c: {k: v for k, v in summary[c].items() if k != "hit10_published"} for c in CONDS}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
