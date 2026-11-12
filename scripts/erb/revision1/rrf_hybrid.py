#!/usr/bin/env python3
"""Reciprocal rank fusion of exact dense top-100 and BM25 dense-text top-100.

OpenAI primary-200, exact cosine search (seq-scan session). Primary RRF k=60.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))
import run_exact_ladder as ladder  # noqa: E402

ROOT = ladder.ROOT
DATA = ladder.DATA
REV1 = ladder.REV1
CACHE_PATH = ladder.OPENAI_CACHE_REV1
BM25_PATH = REV1 / "bm25_dense_text.json"
LADDER_PATH = REV1 / "exact_ladder_openai_primary200.json"
DENSE_TOP100_OUT = REV1 / "dense_top100_openai_primary200.json"
SCRATCH_CACHE = DATA / "rev1_dense_top100_openai_primary200.json"

PRIMARY_K = 60
SENSITIVITY_KS = (10, 30, 100)
TOP_N = 10
TOP_100 = 100
B_BOOT = 10000
BOOT_SEED = 42
TABLE = "document_chunks"

EXPECTED_DENSE_HIT10 = {5000: 0.795, 50000: 0.640, 100000: 0.585}


def rrf_fuse(rank_lists: list[list[str]], k: int, top_n: int = TOP_N) -> list[str]:
    """RRF: score(d) = sum_s 1/(k + rank_s(d)); missing list contributes 0.

    Rank is 1-based. Ties broken by doc_id ascending. Documents that appear in
    no list are omitted (score 0 and unseen).
    """
    scores: dict[str, float] = {}
    for ranked in rank_lists:
        seen: set[str] = set()
        for i, did in enumerate(ranked):
            if did in seen:
                continue
            seen.add(did)
            scores[did] = scores.get(did, 0.0) + 1.0 / (k + i + 1)
    ordered = sorted(scores, key=lambda d: (-scores[d], d))
    return ordered[:top_n]


def rrf_scores(rank_lists: list[list[str]], k: int) -> dict[str, float]:
    scores: dict[str, float] = {}
    for ranked in rank_lists:
        seen: set[str] = set()
        for i, did in enumerate(ranked):
            if did in seen:
                continue
            seen.add(did)
            scores[did] = scores.get(did, 0.0) + 1.0 / (k + i + 1)
    return scores


def load_scratch_cache() -> dict[str, Any]:
    if not SCRATCH_CACHE.is_file():
        return {"by_scale": {}}
    return json.loads(SCRATCH_CACHE.read_text(encoding="utf-8"))


def save_scratch_cache(blob: dict[str, Any]) -> None:
    SCRATCH_CACHE.parent.mkdir(parents=True, exist_ok=True)
    tmp = SCRATCH_CACHE.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(blob), encoding="utf-8")
    tmp.replace(SCRATCH_CACHE)


def load_bm25_top100(
    eval_ids: list[str],
) -> tuple[dict[int, dict[str, list[str]]], dict, bool]:
    blob = json.loads(BM25_PATH.read_text(encoding="utf-8"))
    out: dict[int, dict[str, list[str]]] = {}
    by_scale = blob.get("per_question_by_scale") or {}
    for sk, rows in by_scale.items():
        scale = int(sk)
        m: dict[str, list[str]] = {}
        for row in rows:
            qid = str(row["question_id"])
            m[qid] = [str(d) for d in (row.get("retrieved_top100") or [])]
        out[scale] = m
    missing_scales = []
    for scale, m in out.items():
        miss = [e for e in eval_ids if e not in m]
        if miss:
            missing_scales.append((scale, miss[:3], len(miss)))
    if missing_scales:
        raise SystemExit(f"BM25 file missing eval_ids: {missing_scales[:3]}")
    has_filtered = False
    for key in blob.keys():
        if "filter" in key.lower() or "meta" in key.lower():
            has_filtered = True
    return out, blob, has_filtered


def bootstrap_mean_ci(values: np.ndarray, idx: np.ndarray) -> tuple[float, float, float]:
    v = np.asarray(values, dtype=np.float64)
    point = float(v.mean()) if v.size else 0.0
    if v.size == 0:
        return point, point, point
    boot = v[idx].mean(axis=1)
    lo, hi = np.percentile(boot, [2.5, 97.5])
    return point, float(lo), float(hi)


def ci_obj(point: float, lo: float, hi: float) -> dict[str, float]:
    return {"estimate": round(point, 6), "ci_lo": round(lo, 6), "ci_hi": round(hi, 6)}


def metrics_from_lists(
    questions: list[dict], lists: dict[str, list[str]]
) -> tuple[dict[str, float], list[dict]]:
    per_q: list[dict] = []
    for q in questions:
        eid = q["eval_id"]
        expected = {str(x) for x in (q.get("expected_doc_ids") or []) if x}
        retrieved = lists.get(eid) or []
        m = ladder.per_question_metrics(expected, retrieved, [0.0] * len(retrieved), TOP_N)
        per_q.append({"question_id": eid, **m})
    return ladder.aggregate_metrics(per_q), per_q


def run_unit_tests() -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []

    # (c) hand-computed example
    a = ["x", "y"]
    b = ["z", "x"]
    k = 60
    scores = rrf_scores([a, b], k)
    want = {
        "x": 1.0 / 61 + 1.0 / 62,
        "y": 1.0 / 62,
        "z": 1.0 / 61,
    }
    ok_scores = all(abs(scores[d] - want[d]) < 1e-15 for d in want)
    fused = rrf_fuse([a, b], k, top_n=10)
    # x highest, then z (1/61 > 1/62), then y
    ok_order = fused == ["x", "z", "y"]
    # tie example: a vs b swap ranks -> equal scores, doc_id asc
    left = ["doc_a", "doc_b"]
    right = ["doc_b", "doc_a"]
    tie_scores = rrf_scores([left, right], k)
    tie_ok = abs(tie_scores["doc_a"] - tie_scores["doc_b"]) < 1e-15
    tie_order = rrf_fuse([left, right], k, top_n=2)
    tie_order_ok = tie_order == ["doc_a", "doc_b"]
    hand_pass = ok_scores and ok_order and tie_ok and tie_order_ok
    results.append(
        {
            "name": "hand_computed_rrf",
            "status": "PASS" if hand_pass else "FAIL",
            "example": {
                "lists": {"A": a, "B": b},
                "k": k,
                "scores": {d: scores[d] for d in ("x", "y", "z")},
                "expected_scores": want,
                "fused": fused,
                "expected_fused": ["x", "z", "y"],
                "tie_lists": {"A": left, "B": right},
                "tie_fused": tie_order,
            },
        }
    )

    # (a) single-list reproduces input top-10 for both systems
    dense_list = [f"d{i:03d}" for i in range(100)]
    bm25_list = [f"b{i:03d}" for i in range(99, -1, -1)]
    dense_only = rrf_fuse([dense_list], PRIMARY_K, top_n=10)
    bm25_only = rrf_fuse([bm25_list], PRIMARY_K, top_n=10)
    a_ok = dense_only == dense_list[:10] and bm25_only == bm25_list[:10]
    # also k-sensitivity must preserve single-list order
    a_ok = a_ok and all(
        rrf_fuse([dense_list], kk, top_n=10) == dense_list[:10] for kk in SENSITIVITY_KS
    )
    results.append(
        {
            "name": "single_list_reproduces_top10",
            "status": "PASS" if a_ok else "FAIL",
            "dense_only": dense_only,
            "bm25_only": bm25_only,
        }
    )
    return results


def fetch_dense_top100(
    cur,
    questions: list[dict],
    qvecs: dict[str, list[float]],
    scales: list[int],
) -> dict[str, dict[str, dict[str, list]]]:
    scratch = load_scratch_cache()
    by_scale: dict[str, dict[str, dict[str, list]]] = dict(scratch.get("by_scale") or {})
    for scale in scales:
        sk = str(scale)
        slot = dict(by_scale.get(sk) or {})
        need = [q for q in questions if q["eval_id"] not in slot]
        t0 = time.time()
        for q in need:
            eid = q["eval_id"]
            rows = ladder.exact_search(cur, TABLE, qvecs[eid], scale, "", (), TOP_100)
            slot[eid] = {
                "retrieved_top100": [d for d, _ in rows],
                "scores": [s for _, s in rows],
            }
            if len(slot) % 25 == 0:
                by_scale[sk] = slot
                save_scratch_cache({"by_scale": by_scale})
        by_scale[sk] = slot
        save_scratch_cache({"by_scale": by_scale})
        n_new = len(need)
        print(
            f"dense top-100 N={scale} cached={len(slot) - n_new} new={n_new} "
            f"({time.time() - t0:.1f}s)",
            flush=True,
        )
    return by_scale


def write_markdown(path: Path, payload: dict) -> None:
    lines = [
        "# RRF hybrid (OpenAI primary-200, exact dense + BM25 dense-text)",
        "",
        f"RRF k = {PRIMARY_K} (Cormack et al. 2009). Sensitivity k in {list(SENSITIVITY_KS)}.",
        "Bootstrap: paired percentile over question indices, "
        f"B={B_BOOT}, numpy default_rng({BOOT_SEED}), 95% CI = 2.5/97.5 percentiles.",
        "",
        payload.get("oracle_metadata_rrf", {}).get("note", ""),
        "",
        "## Hit@10 and MRR by scale",
        "",
        "| scale | dense Hit@10 | dense MRR | BM25 Hit@10 | BM25 MRR | RRF k=60 Hit@10 | RRF k=60 MRR | RRF−dense Hit@10 [CI] | RRF−BM25 Hit@10 [CI] |",
        "|------:|-------------:|----------:|------------:|---------:|----------------:|-------------:|----------------------:|---------------------:|",
    ]
    for row in payload.get("by_scale") or []:
        dd = row["rrf_minus_dense_hit_at_10"]
        db = row["rrf_minus_bm25_hit_at_10"]
        lines.append(
            f"| {row['scale']} | {row['dense']['hit_at_10']:.4f} | {row['dense']['mrr']:.4f} | "
            f"{row['bm25']['hit_at_10']:.4f} | {row['bm25']['mrr']:.4f} | "
            f"{row['rrf_k60']['hit_at_10']:.4f} | {row['rrf_k60']['mrr']:.4f} | "
            f"{dd['estimate']:+.4f} [{dd['ci_lo']:+.4f}, {dd['ci_hi']:+.4f}] | "
            f"{db['estimate']:+.4f} [{db['ci_lo']:+.4f}, {db['ci_hi']:+.4f}] |"
        )
    drop = payload.get("drop_5k_to_100k") or {}
    lines.extend(["", "## 5k → 100k drop (Hit@10)", ""])
    if drop.get("skipped"):
        lines.append(f"Skipped: {drop.get('reason')}")
    else:
        lines.append("| system | drop Hit@10 [CI] |")
        lines.append("|--------|-----------------:|")
        for name in ("dense", "bm25", "rrf_k60"):
            d = drop[name]["hit_at_10"]
            lines.append(
                f"| {name} | {d['estimate']:.4f} [{d['ci_lo']:.4f}, {d['ci_hi']:.4f}] |"
            )
        dv = drop["rrf_minus_dense_drop_hit_at_10"]
        lines.append(
            f"| RRF drop − dense drop | {dv['estimate']:+.4f} "
            f"[{dv['ci_lo']:+.4f}, {dv['ci_hi']:+.4f}] |"
        )
    lines.extend(["", "## Unit tests", ""])
    for t in payload.get("unit_tests") or []:
        lines.append(f"- {t['name']}: **{t['status']}**")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def compare_to_published(
    questions: list[dict],
    by_scale_rows: list[dict],
    bm25_blob: dict,
) -> list[dict]:
    checks: list[dict] = []
    nq = len(questions)
    full = nq == 200
    if LADDER_PATH.is_file():
        ladder_blob = json.loads(LADDER_PATH.read_text(encoding="utf-8"))
        raw = {
            int(r["scale"]): r
            for r in ladder_blob.get("runs") or []
            if r.get("condition") == "raw"
        }
    else:
        raw = {}
        checks.append({"name": "dense_vs_exact_ladder", "status": "FAIL", "detail": "missing ladder file"})

    bm25_runs = {int(r["corpus_scale_size"]): r for r in bm25_blob.get("runs") or []}

    for row in by_scale_rows:
        scale = int(row["scale"])
        if not full:
            # subset: compare per-question hits to ladder on the same eval_ids
            if scale in raw:
                want = {p["question_id"]: bool(p["hit_at_10"]) for p in raw[scale].get("per_question") or []}
                got = {p["question_id"]: bool(p["hit_at_10"]) for p in row["dense_per_question"]}
                n_match = sum(1 for qid, h in got.items() if want.get(qid) == h)
                ok = n_match == len(got) and len(got) == nq
                checks.append(
                    {
                        "name": f"dense_subset_hit10_vs_ladder_N={scale}",
                        "status": "PASS" if ok else "FAIL",
                        "n_match": n_match,
                        "n": nq,
                        "note": "smoke/subset; published 200-q means not comparable",
                    }
                )
            bm_pq = {
                p["question_id"]: bool(p["hit_at_10"])
                for p in (bm25_blob.get("per_question_by_scale") or {}).get(str(scale), [])
            }
            got_b = {p["question_id"]: bool(p["hit_at_10"]) for p in row["bm25_per_question"]}
            n_match_b = sum(1 for qid, h in got_b.items() if bm_pq.get(qid) == h)
            checks.append(
                {
                    "name": f"bm25_subset_hit10_vs_file_N={scale}",
                    "status": "PASS" if n_match_b == len(got_b) else "FAIL",
                    "n_match": n_match_b,
                    "n": nq,
                }
            )
            continue
        exp = EXPECTED_DENSE_HIT10.get(scale)
        got = float(row["dense"]["hit_at_10"])
        if exp is not None:
            checks.append(
                {
                    "name": f"dense_hit10_N={scale}",
                    "status": "PASS" if got == exp else "FAIL",
                    "got": got,
                    "expected": exp,
                }
            )
        if scale in raw:
            lad = float(raw[scale]["metrics"]["hit_at_10"])
            checks.append(
                {
                    "name": f"dense_hit10_equals_ladder_N={scale}",
                    "status": "PASS" if got == lad else "FAIL",
                    "got": got,
                    "ladder": lad,
                }
            )
        if scale in bm25_runs:
            bgot = float(row["bm25"]["hit_at_10"])
            bwant = float(bm25_runs[scale]["hit_at_10"])
            checks.append(
                {
                    "name": f"bm25_hit10_N={scale}",
                    "status": "PASS" if bgot == bwant else "FAIL",
                    "got": bgot,
                    "expected": bwant,
                }
            )
    if full:
        for name, status in [
            (f"dense_hit10_N={s}", None) for s in EXPECTED_DENSE_HIT10
        ]:
            if not any(c["name"] == name for c in checks):
                checks.append({"name": name, "status": "NOT_RUN", "reason": "scale not in this job"})
    else:
        checks.append(
            {
                "name": "dense_hit10_published_200q",
                "status": "NOT_RUN",
                "reason": f"n_questions={nq} (need 200); manager full job required",
            }
        )
    return checks


def run(args: argparse.Namespace) -> int:
    unit = run_unit_tests()
    for t in unit:
        print(f"unit {t['name']}: {t['status']}", flush=True)
        if t["status"] != "PASS":
            print("FAIL unit tests", file=sys.stderr)
            return 1

    if args.unit_test:
        return 0

    manifest = ladder.load_manifest()
    questions = ladder.load_questions(manifest, "primary200")
    if args.limit and args.limit > 0:
        questions = questions[: args.limit]
    eval_ids = [q["eval_id"] for q in questions]
    qvecs, missing = ladder.load_query_cache("openai", eval_ids, CACHE_PATH)
    if missing:
        print(f"FAIL missing query vectors (eval_id keys): {missing[:5]}", file=sys.stderr)
        return 1
    pf = ladder.run_openai_preflight(
        "openai",
        "primary200",
        questions,
        qvecs,
        skip_preflight=False,
        provenance_path=ladder.PROVENANCE_DEFAULT,
    )
    if pf != 0:
        return pf

    scales = [int(x) for x in args.scales.split(",") if x.strip()]
    bm25_by_scale, bm25_blob, bm25_has_filter = load_bm25_top100(eval_ids)

    conn = ladder.pg_connect()
    conn.autocommit = True
    cur = conn.cursor()
    ladder.apply_seqscan_session(cur)
    pg_version, pgvector_version = ladder.session_pg_versions(cur)

    dense_by_scale = fetch_dense_top100(cur, questions, qvecs, scales)
    cur.close()
    conn.close()

    nq = len(questions)
    rng = np.random.default_rng(BOOT_SEED)
    idx = rng.integers(0, nq, size=(B_BOOT, nq), dtype=np.int64)

    by_scale_rows: list[dict] = []
    per_scale_hits: dict[str, dict[int, np.ndarray]] = {
        "dense": {},
        "bm25": {},
        "rrf_k60": {},
    }
    per_scale_mrr: dict[str, dict[int, np.ndarray]] = {
        "dense": {},
        "bm25": {},
        "rrf_k60": {},
    }

    for scale in scales:
        t0 = time.time()
        dense_map = dense_by_scale[str(scale)]
        bm25_map = bm25_by_scale[int(scale)]
        fused_k: dict[int, dict[str, list[str]]] = {kk: {} for kk in (PRIMARY_K, *SENSITIVITY_KS)}
        dense_top10: dict[str, list[str]] = {}
        bm25_top10: dict[str, list[str]] = {}
        for q in questions:
            eid = q["eval_id"]
            dlist = list(dense_map[eid]["retrieved_top100"])
            blist = list(bm25_map[eid])
            dense_top10[eid] = rrf_fuse([dlist], PRIMARY_K, top_n=TOP_N)
            bm25_top10[eid] = rrf_fuse([blist], PRIMARY_K, top_n=TOP_N)
            for kk in fused_k:
                fused_k[kk][eid] = rrf_fuse([dlist, blist], kk, top_n=TOP_N)

        d_metrics, d_pq = metrics_from_lists(questions, dense_top10)
        b_metrics, b_pq = metrics_from_lists(questions, bm25_top10)
        r_metrics, r_pq = metrics_from_lists(questions, fused_k[PRIMARY_K])
        sens = {}
        for kk in SENSITIVITY_KS:
            sm, _ = metrics_from_lists(questions, fused_k[kk])
            sens[str(kk)] = sm

        d_hit = np.array([float(p["hit_at_10"]) for p in d_pq], dtype=np.float64)
        b_hit = np.array([float(p["hit_at_10"]) for p in b_pq], dtype=np.float64)
        r_hit = np.array([float(p["hit_at_10"]) for p in r_pq], dtype=np.float64)
        d_mrr = np.array([float(p["mrr"]) for p in d_pq], dtype=np.float64)
        b_mrr = np.array([float(p["mrr"]) for p in b_pq], dtype=np.float64)
        r_mrr = np.array([float(p["mrr"]) for p in r_pq], dtype=np.float64)
        per_scale_hits["dense"][scale] = d_hit
        per_scale_hits["bm25"][scale] = b_hit
        per_scale_hits["rrf_k60"][scale] = r_hit
        per_scale_mrr["dense"][scale] = d_mrr
        per_scale_mrr["bm25"][scale] = b_mrr
        per_scale_mrr["rrf_k60"][scale] = r_mrr

        row = {
            "scale": scale,
            "n_questions": nq,
            "dense": d_metrics,
            "bm25": b_metrics,
            "rrf_k60": r_metrics,
            "rrf_sensitivity": sens,
            "dense_hit_at_10_ci": ci_obj(*bootstrap_mean_ci(d_hit, idx)),
            "bm25_hit_at_10_ci": ci_obj(*bootstrap_mean_ci(b_hit, idx)),
            "rrf_k60_hit_at_10_ci": ci_obj(*bootstrap_mean_ci(r_hit, idx)),
            "dense_mrr_ci": ci_obj(*bootstrap_mean_ci(d_mrr, idx)),
            "bm25_mrr_ci": ci_obj(*bootstrap_mean_ci(b_mrr, idx)),
            "rrf_k60_mrr_ci": ci_obj(*bootstrap_mean_ci(r_mrr, idx)),
            "rrf_minus_dense_hit_at_10": ci_obj(*bootstrap_mean_ci(r_hit - d_hit, idx)),
            "rrf_minus_bm25_hit_at_10": ci_obj(*bootstrap_mean_ci(r_hit - b_hit, idx)),
            "rrf_minus_dense_mrr": ci_obj(*bootstrap_mean_ci(r_mrr - d_mrr, idx)),
            "rrf_minus_bm25_mrr": ci_obj(*bootstrap_mean_ci(r_mrr - b_mrr, idx)),
            "elapsed_s": round(time.time() - t0, 3),
            "dense_per_question": d_pq,
            "bm25_per_question": b_pq,
            "rrf_per_question": r_pq,
        }
        by_scale_rows.append(row)
        print(
            f"RRF N={scale} dense Hit@10={d_metrics['hit_at_10']:.4f} "
            f"BM25={b_metrics['hit_at_10']:.4f} RRF={r_metrics['hit_at_10']:.4f} "
            f"({row['elapsed_s']}s)",
            flush=True,
        )

    drop: dict[str, Any]
    if 5000 in per_scale_hits["dense"] and 100000 in per_scale_hits["dense"]:
        drop = {"skipped": False}
        for sys_name in ("dense", "bm25", "rrf_k60"):
            h5 = per_scale_hits[sys_name][5000]
            h100 = per_scale_hits[sys_name][100000]
            m5 = per_scale_mrr[sys_name][5000]
            m100 = per_scale_mrr[sys_name][100000]
            drop[sys_name] = {
                "hit_at_10": ci_obj(*bootstrap_mean_ci(h5 - h100, idx)),
                "mrr": ci_obj(*bootstrap_mean_ci(m5 - m100, idx)),
            }
        rrf_drop_h = per_scale_hits["rrf_k60"][5000] - per_scale_hits["rrf_k60"][100000]
        den_drop_h = per_scale_hits["dense"][5000] - per_scale_hits["dense"][100000]
        rrf_drop_m = per_scale_mrr["rrf_k60"][5000] - per_scale_mrr["rrf_k60"][100000]
        den_drop_m = per_scale_mrr["dense"][5000] - per_scale_mrr["dense"][100000]
        drop["rrf_minus_dense_drop_hit_at_10"] = ci_obj(
            *bootstrap_mean_ci(rrf_drop_h - den_drop_h, idx)
        )
        drop["rrf_minus_dense_drop_mrr"] = ci_obj(
            *bootstrap_mean_ci(rrf_drop_m - den_drop_m, idx)
        )
    else:
        drop = {
            "skipped": True,
            "reason": "need scales 5000 and 100000 in this job",
        }

    dense_out = {
        "meta": {
            "embedder": "openai",
            "bank": "primary200",
            "table": TABLE,
            "search_mode": "exact",
            "top_k": TOP_100,
            "n_questions": nq,
            "scales": scales,
            "query_cache_path": str(CACHE_PATH.relative_to(ROOT)),
            "query_vector_key_rule": ladder.QUERY_VECTOR_KEY_RULE,
        },
        "by_scale": {
            sk: {
                eid: dense_by_scale[sk][eid]
                for eid in eval_ids
                if eid in dense_by_scale.get(sk, {})
            }
            for sk in (str(s) for s in scales)
        },
    }
    DENSE_TOP100_OUT.parent.mkdir(parents=True, exist_ok=True)
    DENSE_TOP100_OUT.write_text(json.dumps(dense_out), encoding="utf-8")
    print(f"wrote {DENSE_TOP100_OUT}", flush=True)

    oracle_note = (
        "Oracle-filter RRF skipped: bm25_dense_text.json stores unfiltered "
        "retrieved_top100 only. Filtering that list after the fact would be an "
        "incomplete BM25 ranking under the metadata constraint."
    )
    acceptance = compare_to_published(questions, by_scale_rows, bm25_blob)
    for t in unit:
        acceptance.insert(0, {"name": t["name"], "status": t["status"]})

    # strip bulky per_question from published JSON but keep ids+metrics
    slim_rows = []
    for row in by_scale_rows:
        slim = {k: v for k, v in row.items() if not k.endswith("_per_question")}
        slim["per_question"] = [
            {
                "question_id": p["question_id"],
                "dense": {m: d_pq[m] for m in ("hit_at_1", "hit_at_5", "hit_at_10", "mrr", "document_recall", "rank", "retrieved_doc_ids")},
                "bm25": {m: b_pq[m] for m in ("hit_at_1", "hit_at_5", "hit_at_10", "mrr", "document_recall", "rank", "retrieved_doc_ids")},
                "rrf_k60": {m: r_pq[m] for m in ("hit_at_1", "hit_at_5", "hit_at_10", "mrr", "document_recall", "rank", "retrieved_doc_ids")},
            }
            for d_pq, b_pq, r_pq, p in zip(
                row["dense_per_question"],
                row["bm25_per_question"],
                row["rrf_per_question"],
                row["rrf_per_question"],
            )
        ]
        slim_rows.append(slim)

    payload = {
        "meta": {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "embedder": "openai",
            "bank": "primary200",
            "search_mode": "exact",
            "table": TABLE,
            "rrf_k_primary": PRIMARY_K,
            "rrf_k_sensitivity": list(SENSITIVITY_KS),
            "bootstrap_B": B_BOOT,
            "bootstrap_seed": BOOT_SEED,
            "n_questions": nq,
            "scales": scales,
            "session_settings": {"enable_indexscan": "off", "enable_bitmapscan": "off"},
            "postgresql_version": pg_version,
            "pgvector_version": pgvector_version,
            "query_cache_path": str(CACHE_PATH.relative_to(ROOT)),
            "query_vector_key_rule": ladder.QUERY_VECTOR_KEY_RULE,
            "bm25_path": str(BM25_PATH.relative_to(ROOT)),
            "limit": args.limit,
        },
        "oracle_metadata_rrf": {
            "skipped": True,
            "bm25_has_filtered_top100": bm25_has_filter,
            "note": oracle_note,
        },
        "unit_tests": unit,
        "acceptance": acceptance,
        "by_scale": slim_rows,
        "drop_5k_to_100k": drop,
    }
    out = args.out or (REV1 / "rrf_hybrid_openai_primary200.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    write_markdown(out.with_suffix(".md"), payload)
    print(f"wrote {out}", flush=True)
    print(f"wrote {out.with_suffix('.md')}", flush=True)
    failed = [a for a in acceptance if a.get("status") == "FAIL"]
    return 1 if failed else 0


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--scales", default=",".join(str(s) for s in ladder.DEFAULT_SCALES))
    p.add_argument("--limit", type=int, default=0, help="Use first N questions (0 = all 200)")
    p.add_argument("--out", type=Path, default=None)
    p.add_argument("--unit-test", action="store_true")
    p.add_argument(
        "--smoke",
        action="store_true",
        help="scales 5000,100000 and first 10 questions",
    )
    args = p.parse_args()
    if args.smoke:
        args.scales = "5000,100000"
        args.limit = 10
    return run(args)


if __name__ == "__main__":
    raise SystemExit(main())
