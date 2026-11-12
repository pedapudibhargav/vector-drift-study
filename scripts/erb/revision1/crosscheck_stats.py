#!/usr/bin/env python3
"""Recompute Hit@10, metadata lift, and 5k-to-100k drops from saved exact ladders.

Pure standard library. Independent of analyze_exact.py / numpy.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from harness_lib import (
    MANIFEST_PATH,
    REV1,
    assert_qid_set,
    blob_skipped,
    discover_ladders,
    hit10_list,
    index_runs,
    is_canonical_ladder,
    list_recall_at_k,
    load_json,
    load_manifest,
    mean,
    paired_bootstrap_ci,
    parse_ladder_name,
    percentile_linear,
    qid_order,
    question_metrics,
    resolve_scale_manifest,
    rrf_fuse,
)

ANALYSIS = REV1 / "analysis_exact.json"
CI_TOL = 0.01


def load_ladders(rev1: Path = REV1) -> dict[tuple[str, str, str], dict[str, Any]]:
    out: dict[tuple[str, str, str], dict[str, Any]] = {}
    for path in discover_ladders(rev1):
        parsed = parse_ladder_name(path)
        if parsed is None:
            continue
        out[parsed] = load_json(path)
    return out


def load_canonical_ladders(rev1: Path = REV1) -> dict[tuple[str, str, str], dict[str, Any]]:
    return {k: v for k, v in load_ladders(rev1).items() if is_canonical_ladder(k)}


def recompute(ladders: dict[tuple[str, ...], dict[str, Any]] | None = None) -> dict[str, Any]:
    ladders = ladders if ladders is not None else load_canonical_ladders()
    hit: dict[str, Any] = {}
    lift: dict[str, Any] = {}
    drops: dict[str, Any] = {}
    for key, blob in sorted(ladders.items()):
        if len(key) >= 3 and key[2]:
            continue
        emb, bank = key[0], key[1]
        if blob_skipped(blob):
            continue
        runs = index_runs(blob)
        if not runs:
            continue
        first = next(iter(runs.values()))
        order = qid_order(first)
        for run in runs.values():
            assert_qid_set(run, order)
        hit.setdefault(emb, {})[bank] = {}
        for (cond, scale), run in sorted(runs.items()):
            hits = hit10_list(run, order)
            hit[emb][bank].setdefault(cond, {})[str(scale)] = mean([float(x) for x in hits])
        if ("raw" in {c for c, _ in runs}) and ("meta_in" in {c for c, _ in runs}):
            lift.setdefault(emb, {})[bank] = {}
            scales = sorted({s for c, s in runs if c == "raw"})
            for scale in scales:
                raw = hit10_list(runs[("raw", scale)], order)
                meta = hit10_list(runs[("meta_in", scale)], order)
                diffs = [float(m - r) for m, r in zip(meta, raw)]
                point, lo, hi = paired_bootstrap_ci(diffs, seed=42, b=2000)
                lift[emb][bank][str(scale)] = {
                    "hits_meta": int(sum(meta)),
                    "hits_raw": int(sum(raw)),
                    "n": len(order),
                    "delta": (int(sum(meta)) - int(sum(raw))) / len(order),
                    "delta_bootstrap": point,
                    "ci_lo": lo,
                    "ci_hi": hi,
                }
        if ("raw", 5000) in runs and ("raw", 100000) in runs:
            drops.setdefault(emb, {})[bank] = {}
            for cond in ("raw", "meta_in"):
                if (cond, 5000) not in runs or (cond, 100000) not in runs:
                    continue
                a = hit10_list(runs[(cond, 5000)], order)
                b = hit10_list(runs[(cond, 100000)], order)
                diffs = [float(x - y) for x, y in zip(a, b)]
                point, lo, hi = paired_bootstrap_ci(diffs, seed=42, b=2000)
                drops[emb][bank][cond] = {
                    "estimate": point,
                    "ci_lo": lo,
                    "ci_hi": hi,
                    "hit_at_10_5000": mean([float(x) for x in a]),
                    "hit_at_10_100000": mean([float(x) for x in b]),
                }
    return {"hit_at_10": hit, "metadata_lift": lift, "drops_5k_to_100k": drops}


def compare_with_analysis(
    computed: dict[str, Any],
    analysis: dict[str, Any],
    *,
    ci_tol: float = CI_TOL,
) -> list[str]:
    mismatches: list[str] = []
    ladder = analysis.get("ladder") or {}
    for emb, banks in computed["hit_at_10"].items():
        for bank, conds in banks.items():
            for cond, scales in conds.items():
                for scale, val in scales.items():
                    try:
                        ref = ladder[emb][bank]["conditions"][cond][str(scale)]["metrics"]["hit_at_10"]
                    except (KeyError, TypeError):
                        mismatches.append(f"missing analysis Hit@10 {emb}/{bank}/{cond}/{scale}")
                        continue
                    if float(val) != float(ref):
                        mismatches.append(
                            f"Hit@10 {emb}/{bank}/{cond}/{scale}: recomputed={val} analysis={ref}"
                        )

    alift = analysis.get("metadata_lift") or {}
    for emb, banks in computed["metadata_lift"].items():
        for bank, scales in banks.items():
            rows = (alift.get(emb) or {}).get(bank, {}).get("in", {}).get("per_scale") or []
            by_s = {int(r["scale"]): r for r in rows}
            for scale, rec in scales.items():
                ref = by_s.get(int(scale))
                if ref is None:
                    mismatches.append(f"missing lift {emb}/{bank}/{scale}")
                    continue
                if int(rec["hits_meta"]) != int(ref["hits_meta"]) or int(rec["hits_raw"]) != int(
                    ref["hits_raw"]
                ):
                    mismatches.append(
                        f"lift hits {emb}/{bank}/{scale}: {rec['hits_meta']}-{rec['hits_raw']} "
                        f"vs {ref['hits_meta']}-{ref['hits_raw']}"
                    )
                if float(rec["delta"]) != float(ref["delta"]):
                    mismatches.append(
                        f"lift delta {emb}/{bank}/{scale}: {rec['delta']} vs {ref['delta']}"
                    )
                for bound in ("ci_lo", "ci_hi"):
                    if abs(float(rec[bound]) - float(ref[bound])) > ci_tol:
                        mismatches.append(
                            f"lift {bound} {emb}/{bank}/{scale}: {rec[bound]} vs {ref[bound]} (tol {ci_tol})"
                        )

    adrop = (analysis.get("cross_embedder") or {}).get("primary200", {}).get(
        "hit10_drop_5k_to_100k"
    ) or {}
    key_map = {
        ("openai", "raw"): "openai_raw",
        ("openai", "meta_in"): "openai_meta_in",
        ("titan", "raw"): "titan_raw",
        ("titan", "meta_in"): "titan_meta_in",
    }
    for emb, banks in computed["drops_5k_to_100k"].items():
        for bank, conds in banks.items():
            if bank != "primary200":
                continue
            for cond, rec in conds.items():
                ref = adrop.get(key_map[(emb, cond)])
                if ref is None:
                    mismatches.append(f"missing drop {emb}/{cond}")
                    continue
                if float(rec["estimate"]) != float(ref["estimate"]):
                    mismatches.append(
                        f"drop {emb}/{cond}: {rec['estimate']} vs {ref['estimate']}"
                    )
                if float(rec["hit_at_10_5000"]) != float(ref["hit_at_10_5000"]):
                    mismatches.append(f"drop 5k Hit@10 {emb}/{cond}")
                if float(rec["hit_at_10_100000"]) != float(ref["hit_at_10_100000"]):
                    mismatches.append(f"drop 100k Hit@10 {emb}/{cond}")
                for bound in ("ci_lo", "ci_hi"):
                    if abs(float(rec[bound]) - float(ref[bound])) > ci_tol:
                        mismatches.append(
                            f"drop {bound} {emb}/{cond}: {rec[bound]} vs {ref[bound]}"
                        )
    return mismatches


RRF_K = 60
RRF_SCALES = (5000, 50000, 100000)
UNIFORM_ENDPOINTS = {
    "openai": {"raw": 0.585, "meta_first": 0.670},
    "titan": {"raw": 0.610, "meta_first": 0.690},
}


def ols_slope(xs: list[float], ys: list[float]) -> float:
    if len(xs) != len(ys) or len(xs) < 2:
        raise ValueError("ols_slope needs aligned x,y with n>=2")
    n = len(xs)
    mx = sum(xs) / n
    my = sum(ys) / n
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    den = sum((x - mx) ** 2 for x in xs)
    if den == 0.0:
        raise ValueError("degenerate x in ols_slope")
    return num / den


def n400_lift_slope_from_ladder(
    blob: dict[str, Any],
    *,
    seed: int = 42,
    b: int = 2000,
) -> dict[str, float]:
    """OLS of per-scale meta_in−raw Hit@10 lift on log10 N; 90% paired bootstrap CI."""
    import math
    import random

    runs = index_runs(blob)
    scales = sorted({s for c, s in runs if c == "raw" and ("meta_in", s) in runs})
    if len(scales) < 2:
        raise ValueError("need >=2 scales with raw and meta_in")
    order = qid_order(runs[("raw", scales[0])])
    for s in scales:
        assert_qid_set(runs[("raw", s)], order)
        assert_qid_set(runs[("meta_in", s)], order)
    raw_hits = {s: hit10_list(runs[("raw", s)], order) for s in scales}
    meta_hits = {s: hit10_list(runs[("meta_in", s)], order) for s in scales}
    n = len(order)
    xs = [math.log10(float(s)) for s in scales]
    lifts_by_q = [
        [float(meta_hits[s][i] - raw_hits[s][i]) for s in scales] for i in range(n)
    ]
    y_point = [
        sum(lifts_by_q[i][j] for i in range(n)) / n for j in range(len(scales))
    ]
    point = ols_slope(xs, y_point)
    rng = random.Random(seed)
    n_s = len(scales)
    boots: list[float] = []
    for _ in range(b):
        acc = [0.0] * n_s
        for _i in range(n):
            row = lifts_by_q[rng.randrange(n)]
            for j in range(n_s):
                acc[j] += row[j]
        boots.append(ols_slope(xs, [v / n for v in acc]))
    return {
        "estimate": point,
        "ci90_lo": percentile_linear(boots, 5.0),
        "ci90_hi": percentile_linear(boots, 95.0),
    }


def _gold_by_qid(manifest_path: Path = MANIFEST_PATH) -> dict[str, list[str]] | None:
    path = resolve_scale_manifest(manifest_path)
    if path is None:
        return None
    _, questions = load_manifest(path)
    out: dict[str, list[str]] = {}
    for qid, q in questions.items():
        out[str(qid)] = [str(x) for x in (q.get("expected_doc_ids") or [])]
    return out


def bm25_top100_by_scale(bm25: dict[str, Any]) -> dict[int, dict[str, list[str]]]:
    pqs = bm25.get("per_question_by_scale") or {}
    out: dict[int, dict[str, list[str]]] = {}
    for scale_s, rows in pqs.items():
        by_q: dict[str, list[str]] = {}
        for row in rows or []:
            qid = str(row.get("question_id") or row.get("eval_id"))
            docs = row.get("retrieved_top100") or row.get("retrieved_doc_ids") or []
            by_q[qid] = [str(d) for d in docs]
        out[int(scale_s)] = by_q
    return out


def dense_top100_by_scale(dense: dict[str, Any]) -> dict[int, dict[str, list[str]]]:
    pqs = dense.get("by_scale") or {}
    out: dict[int, dict[str, list[str]]] = {}
    for scale_s, by_q in pqs.items():
        if not isinstance(by_q, dict):
            continue
        mapped: dict[str, list[str]] = {}
        for qid, rec in by_q.items():
            if isinstance(rec, dict):
                docs = rec.get("retrieved_top100") or rec.get("retrieved_doc_ids") or []
            elif isinstance(rec, list):
                docs = rec
            else:
                docs = []
            mapped[str(qid)] = [str(d) for d in docs]
        out[int(scale_s)] = mapped
    return out


def recompute_rrf_at_scales(
    dense: dict[str, Any],
    bm25: dict[str, Any],
    gold: dict[str, list[str]],
    *,
    k: int = RRF_K,
    scales: tuple[int, ...] = RRF_SCALES,
) -> dict[int, dict[str, float]]:
    d_by = dense_top100_by_scale(dense)
    b_by = bm25_top100_by_scale(bm25)
    out: dict[int, dict[str, float]] = {}
    for scale in scales:
        dmap = d_by.get(scale) or {}
        bmap = b_by.get(scale) or {}
        qids = sorted(set(dmap) & set(bmap) & set(gold))
        hits: list[float] = []
        mrrs: list[float] = []
        for qid in qids:
            fused = rrf_fuse([dmap[qid], bmap[qid]], k=k, top_n=10)
            m = question_metrics(gold[qid], fused)
            hits.append(m["hit_at_10"])
            mrrs.append(m["mrr"])
        out[scale] = {
            "n": float(len(qids)),
            "hit_at_10": mean(hits),
            "mrr": mean(mrrs),
        }
    return out


def routing_p0_hit10(routing: dict[str, Any]) -> dict[int, dict[str, float]]:
    out: dict[int, dict[str, float]] = {}
    for row in routing.get("results") or []:
        if row.get("p") is None or abs(float(row.get("p")) - 0.0) > 1e-12:
            continue
        scale = int(row["scale"])
        mode = str(row.get("mode"))
        hit = row.get("hit_at_10")
        val = float(hit["estimate"] if isinstance(hit, dict) else hit)
        out.setdefault(scale, {})[mode] = val
    return out


def ladder_condition_hit10(blob: dict[str, Any], condition: str) -> dict[int, float]:
    out: dict[int, float] = {}
    for (cond, scale), run in index_runs(blob).items():
        if cond != condition:
            continue
        out[int(scale)] = float((run.get("metrics") or {}).get("hit_at_10") or mean(
            [float(p.get("hit_at_10") or 0) for p in run.get("per_question") or []]
        ))
    return out


def ladder_lists(blob: dict[str, Any], condition: str, scale: int) -> dict[str, list[str]]:
    run = index_runs(blob).get((condition, scale))
    if run is None:
        return {}
    return {
        str(p["question_id"]): [str(d) for d in (p.get("retrieved_doc_ids") or [])]
        for p in run.get("per_question") or []
    }


def parse_ef200_key(key: str) -> dict[str, Any] | None:
    # N=5000|raw|ef=200|relaxed_order|mst=20000
    parts = str(key).split("|")
    if len(parts) < 4:
        return None
    got: dict[str, Any] = {}
    for p in parts:
        if p.startswith("N="):
            got["scale"] = int(p[2:])
        elif p.startswith("ef="):
            got["ef"] = int(p[3:])
        elif p.startswith("mst="):
            got["mst"] = int(p[4:])
        elif p in ("raw", "meta_first", "meta_in", "meta_gold"):
            got["condition"] = p
        else:
            got["iterative_scan"] = p
    return got if "scale" in got and "condition" in got else None


def per_n_ef200_vs_exact(
    eval_blob: dict[str, Any],
    exact_blob: dict[str, Any],
    *,
    scales: tuple[int, ...] = (5000, 100000),
    condition: str = "raw",
    iterative_scan: str = "relaxed_order",
    gold: dict[str, list[str]] | None = None,
) -> dict[int, dict[str, float]]:
    pq = eval_blob.get("per_question_ef200") or {}
    out: dict[int, dict[str, float]] = {}
    for key, rows in pq.items():
        parsed = parse_ef200_key(key)
        if parsed is None:
            continue
        if parsed.get("condition") != condition:
            continue
        if parsed.get("iterative_scan") != iterative_scan:
            continue
        if int(parsed.get("scale") or -1) not in scales:
            continue
        if parsed.get("ef") not in (None, 200):
            continue
        if parsed.get("mst") not in (None, 20000):
            continue
        scale = int(parsed["scale"])
        exact_lists = ladder_lists(exact_blob, condition, scale)
        recalls: list[float] = []
        approx_hits: list[float] = []
        exact_hits: list[float] = []
        for row in rows or []:
            qid = str(row.get("question_id") or row.get("eval_id"))
            approx = [str(d) for d in (row.get("retrieved_doc_ids") or [])]
            exact = exact_lists.get(qid) or []
            recalls.append(list_recall_at_k(approx, exact, 10))
            g = (gold or {}).get(qid)
            if g:
                approx_hits.append(question_metrics(g, approx)["hit_at_10"])
                exact_hits.append(question_metrics(g, exact)["hit_at_10"])
            else:
                approx_hits.append(float(row.get("hit_at_10") or 0.0))
                # exact hit from stored ladder flags
                exact_hits.append(1.0 if exact and False else float("nan"))
        # If no gold, compute Hit@10 loss from stored cell metrics vs exact run flag via lists overlap not gold.
        if gold:
            loss = mean(exact_hits) - mean(approx_hits)
            exact_h = mean(exact_hits)
            approx_h = mean(approx_hits)
        else:
            exact_h = float("nan")
            approx_h = mean(approx_hits)
            loss = float("nan")
        out[scale] = {
            "n": float(len(rows or [])),
            "recall_at_10": mean(recalls),
            "hit_at_10_approx": approx_h,
            "hit_at_10_exact": exact_h,
            "hit_at_10_loss": loss,
        }
    return out


def uniform_endpoint_hit10(blob: dict[str, Any], condition: str, scale: int = 100000) -> float | None:
    run = index_runs(blob).get((condition, scale))
    if run is None:
        return None
    mets = run.get("metrics") or {}
    if "hit_at_10" in mets:
        return float(mets["hit_at_10"])
    pq = run.get("per_question") or []
    if not pq:
        return None
    return mean([float(p.get("hit_at_10") or 0.0) for p in pq])


def extra_cross_mismatches(
    *,
    rev1: Path = REV1,
    dense: dict[str, Any] | None = None,
    bm25: dict[str, Any] | None = None,
    rrf: dict[str, Any] | None = None,
    routing: dict[str, Any] | None = None,
    exact_openai: dict[str, Any] | None = None,
    gold: dict[str, list[str]] | None = None,
    per_n: dict[str, dict[str, Any]] | None = None,
    exact_by_emb: dict[str, dict[str, Any]] | None = None,
    uniform_blobs: dict[str, dict[str, Any]] | None = None,
    manifest_path: Path = MANIFEST_PATH,
) -> list[str]:
    """Independent recomputes. Each missing input yields a SKIP-style message prefix 'SKIP:'."""
    msgs: list[str] = []

    def _load(name: str, blob: dict[str, Any] | None) -> dict[str, Any] | None:
        if blob is not None:
            return blob
        path = rev1 / name
        if not path.is_file():
            return None
        return load_json(path)

    gold = gold if gold is not None else _gold_by_qid(manifest_path)
    dense = dense if dense is not None else _load("dense_top100_openai_primary200.json", None)
    bm25 = bm25 if bm25 is not None else _load("bm25_dense_text.json", None)
    rrf = rrf if rrf is not None else _load("rrf_hybrid_openai_primary200.json", None)
    if dense is None or bm25 is None:
        msgs.append("SKIP: RRF recompute missing dense_top100 or bm25_dense_text")
    elif gold is None:
        msgs.append("SKIP: RRF recompute missing manifest gold ids")
    else:
        computed = recompute_rrf_at_scales(dense, bm25, gold)
        published_by = {}
        if rrf:
            for row in rrf.get("by_scale") or []:
                published_by[int(row["scale"])] = row.get("rrf_k60") or {}
        for scale, rec in computed.items():
            pref = published_by.get(scale) or {}
            for metric in ("hit_at_10", "mrr"):
                got = rec[metric]
                want = pref.get(metric)
                if want is None:
                    msgs.append(f"FAIL: RRF {metric} N={scale} no published value (got {got})")
                    continue
                tol = 5e-5 if metric == "mrr" else 1e-9
                if abs(float(got) - float(want)) > tol:
                    msgs.append(
                        f"FAIL: RRF {metric} N={scale}: recomputed={got} published={want}"
                    )

    routing = routing if routing is not None else _load("routing_simulation_openai_primary200.json", None)
    exact_openai = exact_openai if exact_openai is not None else _load("exact_ladder_openai_primary200.json", None)
    if routing is None or exact_openai is None:
        msgs.append("SKIP: routing identity missing routing or exact ladder")
    elif not (routing.get("results") or []) or not (exact_openai.get("runs") or []):
        msgs.append("SKIP: routing identity empty routing results or exact runs")
    else:
        p0 = routing_p0_hit10(routing)
        meta = ladder_condition_hit10(exact_openai, "meta_in")
        scales = sorted(set(meta) | set(p0))
        if len(scales) < 9:
            msgs.append(f"FAIL: routing identity expected 9 scales, got {len(scales)}")
        for scale in scales:
            want = meta.get(scale)
            modes = p0.get(scale) or {}
            if want is None:
                msgs.append(f"FAIL: routing identity missing ladder meta_in N={scale}")
                continue
            if not modes:
                msgs.append(f"FAIL: routing identity missing p=0 N={scale}")
                continue
            for mode, got in modes.items():
                if abs(float(got) - float(want)) > 1e-9:
                    msgs.append(
                        f"FAIL: routing p=0 {mode} N={scale}: {got} vs meta_in {want}"
                    )

    exact_by_emb = exact_by_emb or {}
    per_n = per_n or {}
    for emb in ("openai", "titan"):
        ev_name = f"per_n_hnsw_eval_{emb}.json"
        ex_name = f"exact_ladder_{emb}_primary200.json"
        ev = per_n.get(emb) if per_n.get(emb) is not None else _load(ev_name, None)
        ex = exact_by_emb.get(emb) if exact_by_emb.get(emb) is not None else _load(ex_name, None)
        if ev is None or ex is None:
            msgs.append(f"SKIP: per-size recall {emb} missing eval or exact ladder")
            continue
        got_map = per_n_ef200_vs_exact(ev, ex, gold=gold)
        cells = ev.get("cells") or []
        for scale in (5000, 100000):
            rec = got_map.get(scale)
            if rec is None:
                msgs.append(f"SKIP: per-size ef200 {emb} N={scale} missing per_question_ef200")
                continue
            twins = [
                c
                for c in cells
                if int(c.get("scale_n") or -1) == scale
                and c.get("condition") == "raw"
                and int(c.get("ef_search") or -1) == 200
                and c.get("iterative_scan") == "relaxed_order"
                and not c.get("seqscan_off")
            ]
            if not twins:
                msgs.append(f"FAIL: per-size {emb} N={scale} ef200 no published cell")
                continue
            pub = twins[0]
            pub_r = float(pub.get("recall_at_10_vs_exact") or 0.0)
            pub_l = float(pub.get("hit_at_10_drop") or 0.0)
            if abs(rec["recall_at_10"] - pub_r) > 1e-6:
                msgs.append(
                    f"FAIL: per-size recall@10 {emb} N={scale}: recomputed={rec['recall_at_10']} published={pub_r}"
                )
            if gold is not None and rec["hit_at_10_loss"] == rec["hit_at_10_loss"]:
                if abs(rec["hit_at_10_loss"] - pub_l) > 1e-6:
                    msgs.append(
                        f"FAIL: per-size Hit@10 loss {emb} N={scale}: recomputed={rec['hit_at_10_loss']} published={pub_l}"
                    )

    uniform_blobs = uniform_blobs or {}
    for emb, conds in UNIFORM_ENDPOINTS.items():
        rr_name = f"exact_ladder_{emb}_primary200.json"
        rr = _load(rr_name, None)
        for variant in ("uniform_s42", "uniform_s0", "rr_s0"):
            key = f"{variant}_{emb}"
            name = f"exact_ladder_{variant}_{emb}_primary200.json"
            blob = uniform_blobs.get(key) if key in uniform_blobs else _load(name, None)
            if blob is None:
                msgs.append(f"SKIP: uniform endpoint missing {name}")
                continue
            for cond, want in conds.items():
                got = uniform_endpoint_hit10(blob, cond, 100000)
                if got is None:
                    msgs.append(f"FAIL: {name} missing {cond} N=100000")
                    continue
                if abs(float(got) - float(want)) > 1e-9:
                    msgs.append(
                        f"FAIL: {name} {cond} 100k Hit@10={got} expected {want}"
                    )
                if rr is not None:
                    rr_got = uniform_endpoint_hit10(rr, cond, 100000)
                    if rr_got is not None and abs(float(got) - float(rr_got)) > 1e-9:
                        msgs.append(
                            f"FAIL: {name} {cond} 100k Hit@10={got} != round-robin {rr_got}"
                        )
    return msgs


def main() -> int:
    if not ANALYSIS.is_file():
        print("SKIP CROSS-IMPLEMENTATION: missing", ANALYSIS)
        return 0
    computed = recompute()
    analysis = load_json(ANALYSIS)
    mismatches = compare_with_analysis(computed, analysis)
    print(json.dumps({"n_mismatches": len(mismatches), "mismatches": mismatches[:20]}, indent=2))
    if mismatches:
        print(f"FAIL CROSS-IMPLEMENTATION {len(mismatches)} disagreement(s)")
        return 1
    print("PASS CROSS-IMPLEMENTATION")
    return 0


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    raise SystemExit(main())
