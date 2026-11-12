#!/usr/bin/env python3
"""Analysis for uniform / rr_s0 exact ladders (JSON inputs only)."""

from __future__ import annotations

import argparse
import json
import math
from collections import Counter
from itertools import combinations
from pathlib import Path
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / "data"
PUB = ROOT / "artifacts" / "published"
REV1 = PUB / "revision1"
MANIFEST_PATH = DATA / "erb_scale_manifest.json"
OUT_JSON = REV1 / "analysis_uniform.json"
OUT_MD = REV1 / "analysis_uniform.md"

SCALES = (5000, 10000, 15000, 20000, 25000, 40000, 50000, 75000, 100000)
B = 10_000
BOOT_SEED = 42
SCORE_EPS = 1e-12
META_COND = ("meta_first", "meta_in")
REFERENCE_100K = {
    ("openai", "raw"): 0.585,
    ("openai", "meta_first"): 0.670,
    ("titan", "raw"): 0.610,
    ("titan", "meta_first"): 0.690,
}
FILTER_FROM_COND = {"meta_first": "first", "meta_in": "in", "meta_gold": "gold"}


def load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def build_doc_source(manifest: dict) -> dict[str, str]:
    out: dict[str, str] = {}
    for doc in manifest.get("documents") or []:
        did = str(doc.get("doc_id") or "")
        if did and did not in out:
            out[did] = str(doc.get("source_type") or "unknown")
    return out


def rr_composition(manifest: dict, scale: int) -> dict[str, int]:
    """Round-robin ladder: manifest scale_rank (dedupe: min rank per doc_id)."""
    best: dict[str, tuple[int, str]] = {}
    for doc in manifest.get("documents") or []:
        did = str(doc.get("doc_id") or "")
        sr = doc.get("scale_rank")
        if not did or sr is None:
            continue
        sr = int(sr)
        st = str(doc.get("source_type") or "unknown")
        prev = best.get(did)
        if prev is None or sr < prev[0]:
            best[did] = (sr, st)
    counts: Counter[str] = Counter()
    for did, (sr, st) in best.items():
        if sr < scale:
            counts[st] += 1
    return dict(sorted(counts.items()))


def pool_source_counts(manifest: dict) -> dict[str, int]:
    comp = rr_composition(manifest, 100000)
    return comp


def uniform_expected_shares(
    manifest: dict,
    scale: int,
    *,
    n_anchors: int = 627,
) -> dict[str, float]:
    """Expected source shares at scale N for uniform-random ladder (fixed anchor prefix)."""
    best: dict[str, tuple[int, str, bool]] = {}
    for doc in manifest.get("documents") or []:
        did = str(doc.get("doc_id") or "")
        sr = doc.get("scale_rank")
        if not did or sr is None or int(sr) >= 100000:
            continue
        sr = int(sr)
        st = str(doc.get("source_type") or "unknown")
        is_g = bool(doc.get("is_gold_anchor"))
        prev = best.get(did)
        if prev is None or sr < prev[0]:
            best[did] = (sr, st, is_g)
    anchors: Counter[str] = Counter()
    non: Counter[str] = Counter()
    for _did, (_sr, st, is_g) in best.items():
        if is_g:
            anchors[st] += 1
        else:
            non[st] += 1
    n_non = sum(non.values()) or 1
    non_sh = {k: v / n_non for k, v in non.items()}
    exp: Counter[str] = Counter()
    take_a = min(scale, n_anchors)
    # approximate: first take_a anchors follow manifest anchor order by rank — use full anchor counts scaled only if scale < n_anchors
    if scale <= n_anchors:
        for st, c in anchors.items():
            exp[st] += c * scale / n_anchors
    else:
        for st, c in anchors.items():
            exp[st] += c
        extra = scale - n_anchors
        for st, p in non_sh.items():
            exp[st] += extra * p
    total = sum(exp.values()) or 1
    return {k: v / total for k, v in sorted(exp.items())}


def index_runs(blob: dict) -> dict[tuple[str, int], dict]:
    out: dict[tuple[str, int], dict] = {}
    for run in blob.get("runs") or []:
        out[(run["condition"], int(run["scale"]))] = run
    return out


def hit10(run: dict | None) -> float | None:
    if not run:
        return None
    return float(run["metrics"]["hit_at_10"])


def blob_order(blob: dict) -> list[str]:
    for run in blob.get("runs") or []:
        pq = run.get("per_question") or []
        if pq:
            return [p["question_id"] for p in pq]
    return []


def filter_source_types(q: dict, which: str, doc_source: dict[str, str]) -> set[str]:
    if which == "first":
        st = q.get("source_types") or []
        return {str(st[0])} if st else set()
    if which == "in":
        return {str(s) for s in (q.get("source_types") or []) if s}
    gold: set[str] = set()
    for did in q.get("expected_doc_ids") or []:
        st = doc_source.get(str(did))
        if st:
            gold.add(st)
    return gold


def is_nan(x: Any) -> bool:
    try:
        return math.isnan(float(x))
    except (TypeError, ValueError):
        return False


def containment_reason(
    raw_ids: list[str],
    meta_ids: list[str],
    allowed: set[str],
    doc_source: dict[str, str],
) -> str | None:
    if not raw_ids or not meta_ids:
        return "empty_list"
    meta_set = set(meta_ids)
    for doc in raw_ids:
        st = doc_source.get(doc)
        if st is not None and st in allowed and doc not in meta_set:
            return "raw_allowed_doc_missing_from_meta"
    for doc in meta_ids:
        st = doc_source.get(doc)
        if st is None:
            return "missing_from_manifest"
        if st not in allowed:
            return "meta_doc_not_in_allowed_set"
    return None


def nested_reason(
    ids_a: list[str],
    scores_a: list[Any] | None,
    ids_b: list[str],
    scores_b: list[Any] | None,
) -> str | None:
    if len(ids_a) != len(set(ids_a)) or len(ids_b) != len(set(ids_b)):
        return "duplicate_doc_ids"
    pos_b = {d: j for j, d in enumerate(ids_b)}
    set_b = set(ids_b)
    last = -1
    for d in ids_a:
        j = pos_b.get(d)
        if j is None:
            continue
        if j < last:
            return "relative_order"
        last = j
    for k, d in enumerate(ids_a):
        if d in set_b:
            for prev in ids_a[:k]:
                if prev not in set_b:
                    return "prefix"
    dropped = [d for d in ids_a if d not in set_b]
    if not dropped:
        return None
    if len(ids_b) != 10:
        return "truncated_list_b"
    scores_ok = (
        scores_a is not None
        and scores_b is not None
        and len(scores_a) == len(ids_a) > 0
        and len(scores_b) == len(ids_b) > 0
        and not any(is_nan(s) for s in scores_a)
        and not any(is_nan(s) for s in scores_b)
    )
    if not scores_ok:
        return "unverifiable"
    score_a = {d: float(s) for d, s in zip(ids_a, scores_a)}
    min_b = min(float(s) for s in scores_b)
    for d in dropped:
        if min_b < score_a[d] - SCORE_EPS:
            return "dropped_doc_score"
    return None


def score_reason(ids: list[str], scores: list[Any] | None) -> str | None:
    if scores is None or len(scores) != len(ids):
        return "length_mismatch"
    floats = [float(s) for s in scores]
    for i in range(len(floats) - 1):
        if floats[i + 1] > floats[i]:
            return "increasing"
    return None


def run_invariants(blob: dict, doc_source: dict, questions: dict) -> dict[str, int]:
    runs = index_runs(blob)
    scales = sorted({int(s) for _c, s in runs})
    conditions = sorted({c for c, _s in runs})
    order = blob_order(blob)
    pq_index = {(c, s): runs[(c, s)]["per_question"] for (c, s) in runs}
    counts = {"containment": 0, "nested_corpus": 0, "score_monotonicity": 0}
    filt_cache = {
        (qid, filt): filter_source_types(questions[qid], filt, doc_source)
        for qid in order
        for filt in ("first", "in", "gold")
    }
    for cond in conditions:
        if cond == "raw":
            continue
        filt = FILTER_FROM_COND.get(cond)
        if not filt:
            continue
        for s in scales:
            raw_pq = pq_index.get(("raw", s))
            meta_pq = pq_index.get((cond, s))
            if not raw_pq or not meta_pq:
                continue
            for i, qid in enumerate(order):
                reason = containment_reason(
                    [str(x) for x in raw_pq[i].get("retrieved_doc_ids") or []],
                    [str(x) for x in meta_pq[i].get("retrieved_doc_ids") or []],
                    filt_cache[(qid, filt)],
                    doc_source,
                )
                if reason:
                    counts["containment"] += 1
    for cond in conditions:
        for s_a, s_b in combinations(scales, 2):
            if (cond, s_a) not in pq_index or (cond, s_b) not in pq_index:
                continue
            pq_a = pq_index[(cond, s_a)]
            pq_b = pq_index[(cond, s_b)]
            for i in range(len(order)):
                reason = nested_reason(
                    [str(x) for x in pq_a[i].get("retrieved_doc_ids") or []],
                    pq_a[i].get("scores"),
                    [str(x) for x in pq_b[i].get("retrieved_doc_ids") or []],
                    pq_b[i].get("scores"),
                )
                if reason and reason != "unverifiable":
                    counts["nested_corpus"] += 1
    for cond in conditions:
        for s in scales:
            for pq in pq_index.get((cond, s), []):
                reason = score_reason(
                    [str(x) for x in pq.get("retrieved_doc_ids") or []],
                    pq.get("scores"),
                )
                if reason:
                    counts["score_monotonicity"] += 1
    return counts


def mean_ci(meta_h: np.ndarray, raw_h: np.ndarray, idx: np.ndarray) -> tuple[float, float, float]:
    """Paired bootstrap CI for meta minus raw (lift)."""
    diff = meta_h - raw_h
    point = float(diff.mean())
    boot = diff[idx].mean(axis=1)
    lo, hi = np.percentile(boot, [2.5, 97.5])
    return point, float(lo), float(hi)


def mean_ci_diff(a: np.ndarray, b: np.ndarray, idx: np.ndarray) -> tuple[float, float, float]:
    diff = a - b
    point = float(diff.mean())
    boot = diff[idx].mean(axis=1)
    lo, hi = np.percentile(boot, [2.5, 97.5])
    return point, float(lo), float(hi)


def slope_fit(scales: list[int], values: list[float]) -> tuple[float, float]:
    x = np.log(np.array(scales, dtype=np.float64))
    y = np.array(values, dtype=np.float64)
    X = np.column_stack([x, np.ones_like(x)])
    beta, _, _, _ = np.linalg.lstsq(X, y, rcond=None)
    return float(beta[0]), float(beta[1])


def confluence_first_questions(manifest: dict, bank_ids: list[str]) -> list[str]:
    by_eval = {q["eval_id"]: q for q in manifest.get("questions") or []}
    out = []
    for eid in bank_ids:
        q = by_eval.get(eid)
        if not q:
            continue
        sts = q.get("source_types") or []
        if sts and str(sts[0]) == "confluence":
            out.append(eid)
    return out


def per_question_hit10(run: dict, qids: set[str]) -> float | None:
    hits = []
    for p in run.get("per_question") or []:
        if p["question_id"] not in qids:
            continue
        hits.append(1.0 if p.get("hit_at_10") else 0.0)
    if not hits:
        return None
    return float(sum(hits) / len(hits))


def share_fractions(comp: dict[str, int]) -> dict[str, float]:
    total = sum(comp.values()) or 1
    return {k: v / total for k, v in sorted(comp.items())}


def share_table(comp: dict[str, int]) -> dict[str, float]:
    return {k: round(v, 4) for k, v in share_fractions(comp).items()}


def ladder_storage_key(blob: dict) -> str:
    meta = blob.get("meta") or {}
    ladder = str(meta.get("ladder") or "unknown")
    embedder = str(meta.get("embedder") or "openai")
    if embedder == "openai":
        return ladder
    return f"{ladder}_{embedder}"


def aligned_hits(run: dict | None, order: list[str]) -> np.ndarray | None:
    if not run:
        return None
    by_id = {p["question_id"]: p for p in run.get("per_question") or []}
    arr = np.empty(len(order), dtype=np.float64)
    for i, qid in enumerate(order):
        arr[i] = 1.0 if by_id[qid].get("hit_at_10") else 0.0
    return arr


def per_question_drop(run5: dict, run100: dict, order: list[str]) -> np.ndarray:
    h5 = aligned_hits(run5, order)
    h1 = aligned_hits(run100, order)
    if h5 is None or h1 is None:
        raise ValueError("missing run for drop")
    return h5 - h1


def discover_uniform_json() -> list[Path]:
    return sorted(REV1.glob("exact_ladder_uniform_s*_*.json")) + sorted(
        REV1.glob("exact_ladder_rr_s0_*.json")
    )


def analyze(paths: list[Path]) -> dict[str, Any]:
    manifest = load_json(MANIFEST_PATH)
    doc_source = build_doc_source(manifest)
    bank = load_json(PUB / "primary_questions_200.json")
    bank_ids = list(bank["question_ids"])
    conf_q = confluence_first_questions(manifest, bank_ids)
    pool_counts = pool_source_counts(manifest)
    pool_shares_frac = share_fractions(pool_counts)
    pool_shares = share_table(pool_counts)

    rr_by_emb: dict[str, dict] = {}
    for emb, fname in (("openai", "exact_ladder_openai_primary200.json"), ("titan", "exact_ladder_titan_primary200.json")):
        p = REV1 / fname
        if p.is_file():
            rr_by_emb[emb] = load_json(p)

    ladders: dict[str, dict] = {}
    for p in paths:
        blob = load_json(p)
        name = ladder_storage_key(blob)
        ladders[name] = {"path": str(p), "blob": blob}

    order = sorted(bank_ids)
    n_q = len(order)
    rng = np.random.default_rng(BOOT_SEED)
    boot_idx = rng.integers(0, n_q, size=(B, n_q), dtype=np.int64)

    composition: dict[str, Any] = {
        "pool_source_counts": pool_counts,
        "pool_source_shares": pool_shares,
        "pool_source_shares_exact": pool_shares_frac,
        "round_robin_manifest": {str(s): rr_composition(manifest, s) for s in SCALES},
        "note_anchor_prefix": (
            "627 pinned gold anchors are Confluence-heavy; small uniform corpora "
            "are Confluence-heavier than the full pool under any ladder ordering."
        ),
    }
    for name, rec in ladders.items():
        meta = rec["blob"].get("meta") or {}
        comp_scales = meta.get("composition_at_scales") or {}
        by_scale: dict[str, Any] = {}
        for sc, comp in comp_scales.items():
            obs = share_fractions(comp)
            n_docs = sum(comp.values())
            anchor_exp = uniform_expected_shares(manifest, int(sc))
            keys = set(obs) | set(pool_shares_frac) | set(anchor_exp)
            l1_pool = sum(abs(obs.get(k, 0.0) - pool_shares_frac.get(k, 0.0)) for k in keys)
            l1_anchor = sum(abs(obs.get(k, 0.0) - anchor_exp.get(k, 0.0)) for k in keys)
            z_pool = max(
                (
                    abs(obs.get(k, 0.0) - pool_shares_frac.get(k, 0.0))
                    / max(math.sqrt(pool_shares_frac.get(k, 0.0) * (1 - pool_shares_frac.get(k, 0.0)) / max(n_docs, 1)), 1e-9)
                    for k in keys
                ),
                default=0.0,
            )
            z_anchor = max(
                (
                    abs(obs.get(k, 0.0) - anchor_exp.get(k, 0.0))
                    / max(math.sqrt(anchor_exp.get(k, 0.0) * (1 - anchor_exp.get(k, 0.0)) / max(n_docs, 1)), 1e-9)
                    for k in keys
                ),
                default=0.0,
            )
            by_scale[str(sc)] = {
                "counts": comp,
                "shares_rounded": share_table(comp),
                "shares": obs,
                "L1_vs_pool": round(l1_pool, 4),
                "max_z_vs_pool": round(z_pool, 3),
                "L1_vs_anchor_expected": round(l1_anchor, 4),
                "max_z_vs_anchor_expected": round(z_anchor, 3),
            }
        composition[name] = {"by_scale": by_scale}

    hit_ladders: dict[str, dict[str, dict[str, float | None]]] = {}
    invariants: dict[str, dict[str, int]] = {}
    conf_by_scale: dict[str, dict[str, dict[str, float | None]]] = {}
    endpoint_checks: list[dict] = []

    questions = {q["eval_id"]: q for q in manifest.get("questions") or []}
    conf_set = set(conf_q)

    for name, rec in ladders.items():
        blob = rec["blob"]
        emb = blob["meta"]["embedder"]
        runs = index_runs(blob)
        hit_ladders[name] = {}
        conf_by_scale[name] = {"raw": {}, "meta_first": {}, "meta_in": {}}
        invariants[name] = run_invariants(blob, doc_source, questions)
        for cond in ("raw", "meta_first", "meta_in"):
            hit_ladders[name][cond] = {str(s): hit10(runs.get((cond, s))) for s in SCALES}
        for s in SCALES:
            conf_by_scale[name]["raw"][str(s)] = per_question_hit10(
                runs.get(("raw", s), {}), conf_set
            )
            conf_by_scale[name]["meta_first"][str(s)] = per_question_hit10(
                runs.get(("meta_first", s), {}), conf_set
            )
            conf_by_scale[name]["meta_in"][str(s)] = per_question_hit10(
                runs.get(("meta_in", s), {}), conf_set
            )
        if int(blob["meta"].get("max_questions") or 200) == 200:
            for cond in ("raw", "meta_first", "meta_in"):
                run = runs.get((cond, 100000))
                if not run:
                    continue
                got = float(run["metrics"]["hit_at_10"])
                want = REFERENCE_100K.get((emb, cond))
                if want is not None:
                    endpoint_checks.append(
                        {
                            "ladder": name,
                            "embedder": emb,
                            "condition": cond,
                            "got": got,
                            "want": want,
                            "pass": abs(got - want) < 1e-9,
                        }
                    )

    for emb, rr_blob in rr_by_emb.items():
        rr_runs = index_runs(rr_blob)
        rr_key = "round_robin" if emb == "openai" else "round_robin_titan"
        conf_by_scale[rr_key] = {"raw": {}, "meta_first": {}, "meta_in": {}}
        for cond in ("raw", "meta_first", "meta_in"):
            for s in SCALES:
                conf_by_scale[rr_key][cond][str(s)] = per_question_hit10(
                    rr_runs.get((cond, s), {}), conf_set
                )

    lifts: list[dict] = []
    for name, rec in ladders.items():
        runs = index_runs(rec["blob"])
        emb = rec["blob"]["meta"]["embedder"]
        for mcond in META_COND:
            for s in SCALES:
                raw_run = runs.get(("raw", s))
                meta_run = runs.get((mcond, s))
                if not raw_run or not meta_run:
                    continue
                raw_h = aligned_hits(raw_run, order)
                meta_h = aligned_hits(meta_run, order)
                if raw_h is None or meta_h is None:
                    continue
                point, lo, hi = mean_ci(meta_h, raw_h, boot_idx)
                lifts.append(
                    {
                        "ladder": name,
                        "embedder": emb,
                        "condition": mcond,
                        "scale": s,
                        "lift": point,
                        "ci_lo": lo,
                        "ci_hi": hi,
                        "n": n_q,
                    }
                )

    slopes: dict[str, Any] = {}
    for name, rec in ladders.items():
        runs = index_runs(rec["blob"])
        for cond in ("raw", "meta_first", "meta_in"):
            ys = [hit10(runs.get((cond, s))) for s in SCALES]
            if any(y is None for y in ys):
                ys_clean = [y for y in ys if y is not None]
                sc_clean = [s for s, y in zip(SCALES, ys) if y is not None]
            else:
                ys_clean, sc_clean = ys, list(SCALES)
            if len(sc_clean) < 2:
                continue
            sl, ic = slope_fit(sc_clean, ys_clean)
            sc_ex = [s for s in sc_clean if s != 5000]
            ys_ex = [y for s, y in zip(sc_clean, ys_clean) if s != 5000]
            sl_ex, ic_ex = slope_fit(sc_ex, ys_ex) if len(sc_ex) >= 2 else (None, None)
            slopes[f"{name}|{cond}"] = {
                "slope_all": sl,
                "intercept_all": ic,
                "slope_no_5k": sl_ex,
                "intercept_no_5k": ic_ex,
                "scales_used": sc_clean,
            }

    ALT_LADDERS = ("uniform_s42", "uniform_s0", "rr_s0")
    drop_block: dict[str, Any] = {}
    for emb, rr_blob in rr_by_emb.items():
        rr_runs = index_runs(rr_blob)
        emb_block: dict[str, Any] = {}
        for alt in ALT_LADDERS:
            key = alt if emb == "openai" else f"{alt}_{emb}"
            alt_rec = ladders.get(key)
            if not alt_rec:
                continue
            alt_runs = index_runs(alt_rec["blob"])
            alt_out: dict[str, Any] = {}
            for cond in ("raw", "meta_first", "meta_in"):
                r5 = rr_runs.get((cond, 5000))
                r1 = rr_runs.get((cond, 100000))
                a5 = alt_runs.get((cond, 5000))
                a1 = alt_runs.get((cond, 100000))
                if not all((r5, r1, a5, a1)):
                    continue
                alt_drop = per_question_drop(a5, a1, order)
                rr_drop_v = per_question_drop(r5, r1, order)
                d_est, d_lo, d_hi = mean_ci_diff(alt_drop, rr_drop_v, boot_idx)
                alt_out[cond] = {
                    "alt_drop_point": float(alt_drop.mean()),
                    "round_robin_drop_point": float(rr_drop_v.mean()),
                    "drop_difference_alt_minus_rr": {
                        "estimate": d_est,
                        "ci_lo": d_lo,
                        "ci_hi": d_hi,
                    },
                }
            if alt_out:
                emb_block[alt] = alt_out
        if emb_block:
            drop_block[emb] = emb_block
    rr_drop = drop_block.get("openai", {})

    acceptance: list[dict] = []
    for name, inv in invariants.items():
        ok = all(v == 0 for v in inv.values())
        acceptance.append(
            {
                "name": f"invariants_zero_{name}",
                "pass": ok,
                "values": inv,
            }
        )
    for chk in endpoint_checks:
        acceptance.append(
            {
                "name": f"100k_endpoint_{chk['ladder']}_{chk['embedder']}_{chk['condition']}",
                "pass": chk["pass"],
                "got": chk["got"],
                "want": chk["want"],
            }
        )

    for name, rec in ladders.items():
        if not name.startswith("uniform"):
            continue
        comp_meta = composition.get(name, {}).get("by_scale") or {}
        for sc, row in comp_meta.items():
            z_cut = 3.0
            ok = float(row["max_z_vs_anchor_expected"]) <= z_cut
            acceptance.append(
                {
                    "name": f"composition_anchor_noise_{name}_N{sc}",
                    "pass": ok,
                    "L1_vs_anchor_expected": row["L1_vs_anchor_expected"],
                    "max_z_vs_anchor_expected": row["max_z_vs_anchor_expected"],
                    "L1_vs_pool": row["L1_vs_pool"],
                    "max_z_vs_pool": row["max_z_vs_pool"],
                    "n_docs": sum(row["counts"].values()),
                }
            )

    nesting_ok = True
    for name, rec in ladders.items():
        inv = invariants[name]
        if inv["nested_corpus"] != 0:
            nesting_ok = False
    acceptance.append({"name": "nesting_nested_corpus", "pass": nesting_ok, "note": "via nested_corpus violations"})

    return {
        "confluence_first_n": len(conf_q),
        "confluence_first_question_ids": conf_q,
        "composition": composition,
        "hit_at_10_ladders": hit_ladders,
        "confluence_hit_at_10": conf_by_scale,
        "slopes": slopes,
        "metadata_lift": lifts,
        "drop_5k_100k": drop_block,
        "drop_5k_100k_openai": rr_drop,
        "invariants": invariants,
        "endpoint_checks": endpoint_checks,
        "acceptance": acceptance,
        "inputs": [str(p) for p in paths],
    }


def write_md(payload: dict) -> None:
    lines = ["# Uniform ladder analysis", ""]
    lines.append(f"- Confluence-first questions: **{payload['confluence_first_n']}**")
    comp = payload.get("composition") or {}
    if comp.get("note_anchor_prefix"):
        lines.append(f"- Composition note: {comp['note_anchor_prefix']}")
    lines.append("")
    lines.append("## Acceptance")
    lines.append("")
    lines.append("| test | pass | detail |")
    lines.append("|------|:----:|--------|")
    for a in payload["acceptance"]:
        detail = {k: v for k, v in a.items() if k not in ("name", "pass")}
        lines.append(f"| {a['name']} | {a['pass']} | {detail} |")
    lines.append("")
    lines.append("## Confluence-first 41 questions (Hit@10)")
    lines.append("")
    lines.append("| scale | uniform ladders (raw / meta_first) | round-robin (raw / meta_first) |")
    lines.append("|------:|-----------------------------------:|------------------------------:|")
    conf = payload.get("confluence_hit_at_10") or {}
    rr = conf.get("round_robin") or conf.get("round_robin_titan") or {}
    uni_name = "uniform_s42" if "uniform_s42" in conf else next((k for k in conf if k.startswith("uniform")), "")
    uni = conf.get(uni_name, {})
    fmt = lambda x: f"{x:.3f}" if x is not None else "—"
    for s in SCALES:
        sk = str(s)
        lines.append(
            f"| {s} | {fmt(uni.get('raw', {}).get(sk))} / {fmt(uni.get('meta_first', {}).get(sk))} | "
            f"{fmt(rr.get('raw', {}).get(sk))} / {fmt(rr.get('meta_first', {}).get(sk))} |"
        )
    lines.append("")
    lines.append("## Hit@10 (available runs)")
    for ladder, conds in payload["hit_at_10_ladders"].items():
        lines.append(f"\n### {ladder}")
        lines.append("| scale | raw | meta_first | meta_in |")
        lines.append("|------:|----:|-----------:|--------:|")
        for s in SCALES:
            raw = conds.get("raw", {}).get(str(s))
            mf = conds.get("meta_first", {}).get(str(s))
            mi = conds.get("meta_in", {}).get(str(s))
            lines.append(f"| {s} | {fmt(raw)} | {fmt(mf)} | {fmt(mi)} |")
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inputs", type=Path, nargs="*", default=None)
    args = parser.parse_args()
    paths = args.inputs or discover_uniform_json()
    if not paths:
        print("no uniform ladder JSON inputs found", flush=True)
        payload = {"acceptance": [{"name": "inputs_present", "pass": False}]}
        OUT_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        write_md(payload)
        return 1
    payload = analyze(paths)
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    write_md(payload)
    print(f"wrote {OUT_JSON}")
    print(f"wrote {OUT_MD}")
    failed = [a for a in payload["acceptance"] if not a.get("pass")]
    if failed:
        print(f"acceptance: {len(failed)} FAIL", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
