#!/usr/bin/env python3
"""Analysis for full-pool exact ladders (JSON inputs only; stdlib + numpy)."""

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
OUT_JSON = REV1 / "analysis_pool_ladders.json"
OUT_MD = REV1 / "analysis_pool_ladders.md"
RR_ORIGINAL = REV1 / "exact_ladder_openai_primary200.json"

B = 10_000
BOOT_SEED = 42
SCORE_EPS = 1e-12
META_COND = ("meta_first", "meta_in")
FILTER_FROM_COND = {"meta_first": "first", "meta_in": "in", "meta_gold": "gold"}
EXPECTED_LADDERS = ("prop_s42", "prop_s0", "rr_full")


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
    for _did, (sr, st) in best.items():
        if sr < scale:
            counts[st] += 1
    return dict(sorted(counts.items()))


def pool_source_counts(manifest: dict) -> dict[str, int]:
    return rr_composition(manifest, 100000)


def run_scale_key(run: dict) -> str:
    lab = run.get("scale_label")
    if lab:
        return str(lab)
    return str(int(run["scale"]))


def index_runs(blob: dict) -> dict[tuple[str, str], dict]:
    out: dict[tuple[str, str], dict] = {}
    for run in blob.get("runs") or []:
        out[(run["condition"], run_scale_key(run))] = run
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
            continue
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


def numeric_scale_keys(runs: dict[tuple[str, str], dict]) -> list[tuple[int, str]]:
    keys: list[tuple[int, str]] = []
    seen: set[str] = set()
    for _c, sk in runs:
        if sk in seen:
            continue
        seen.add(sk)
        if sk == "full":
            continue
        try:
            keys.append((int(sk), sk))
        except ValueError:
            continue
    keys.sort()
    return keys


def nest_scale_pairs(runs: dict[tuple[str, str], dict]) -> list[tuple[str, str]]:
    """Pairs (smaller corpus, larger corpus) using numeric N; full is largest if present."""
    nums = numeric_scale_keys(runs)
    labels = [sk for _n, sk in nums]
    has_full = any(sk == "full" for _c, sk in runs)
    pairs: list[tuple[str, str]] = []
    for a, b in combinations(labels, 2):
        pairs.append((a, b))
    if has_full:
        for _n, sk in nums:
            pairs.append((sk, "full"))
    return pairs


def run_invariants(blob: dict, doc_source: dict, questions: dict) -> dict[str, int]:
    runs = index_runs(blob)
    conditions = sorted({c for c, _s in runs})
    order = blob_order(blob)
    pq_index = {(c, s): runs[(c, s)]["per_question"] for (c, s) in runs}
    counts = {"containment": 0, "nested_corpus": 0, "score_monotonicity": 0}
    filt_cache = {
        (qid, filt): filter_source_types(questions[qid], filt, doc_source)
        for qid in order
        if qid in questions
        for filt in ("first", "in", "gold")
    }
    scales = sorted({s for _c, s in runs})
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
                if qid not in questions:
                    continue
                reason = containment_reason(
                    [str(x) for x in raw_pq[i].get("retrieved_doc_ids") or []],
                    [str(x) for x in meta_pq[i].get("retrieved_doc_ids") or []],
                    filt_cache[(qid, filt)],
                    doc_source,
                )
                if reason:
                    counts["containment"] += 1
    for cond in conditions:
        for s_a, s_b in nest_scale_pairs(runs):
            if (cond, s_a) not in pq_index or (cond, s_b) not in pq_index:
                continue
            na = int(runs[(cond, s_a)]["scale"])
            nb = int(runs[(cond, s_b)]["scale"])
            if s_a != "full" and s_b != "full" and na >= nb:
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
    diff = meta_h - raw_h
    point = float(diff.mean())
    boot = diff[idx].mean(axis=1)
    lo, hi = np.percentile(boot, [2.5, 97.5])
    return point, float(lo), float(hi)


def mean_ci_one(x: np.ndarray, idx: np.ndarray) -> tuple[float, float, float]:
    point = float(x.mean())
    boot = x[idx].mean(axis=1)
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


def aligned_hits(run: dict | None, order: list[str]) -> np.ndarray | None:
    if not run:
        return None
    by_id = {p["question_id"]: p for p in run.get("per_question") or []}
    if any(qid not in by_id for qid in order):
        return None
    arr = np.empty(len(order), dtype=np.float64)
    for i, qid in enumerate(order):
        arr[i] = 1.0 if by_id[qid].get("hit_at_10") else 0.0
    return arr


def per_question_drop(run_a: dict, run_b: dict, order: list[str]) -> np.ndarray | None:
    ha = aligned_hits(run_a, order)
    hb = aligned_hits(run_b, order)
    if ha is None or hb is None:
        return None
    return ha - hb


def discover_pool_json() -> list[Path]:
    return sorted(REV1.glob("exact_ladder_pool_*_openai_primary200.json"))


def ladder_name(blob: dict, path: Path) -> str:
    meta = blob.get("meta") or {}
    return str(meta.get("ladder") or path.stem)


def available_scale_labels(runs: dict[tuple[str, str], dict]) -> list[str]:
    labels: list[str] = []
    seen: set[str] = set()
    nums = numeric_scale_keys(runs)
    for _n, sk in nums:
        if sk not in seen:
            labels.append(sk)
            seen.add(sk)
    if any(s == "full" for _c, s in runs) and "full" not in seen:
        labels.append("full")
    return labels


def x_for_label(blob: dict, run: dict | None, label: str) -> int | None:
    if not run:
        return None
    if label == "full":
        meta = blob.get("meta") or {}
        n = meta.get("full_n") or meta.get("union_document_count") or run.get("scale")
        return int(n) if n is not None else int(run["scale"])
    return int(run["scale"])


def analyze(paths: list[Path]) -> dict[str, Any]:
    manifest = load_json(MANIFEST_PATH)
    doc_source = build_doc_source(manifest)
    bank = load_json(PUB / "primary_questions_200.json")
    bank_ids = list(bank["question_ids"])
    conf_q = confluence_first_questions(manifest, bank_ids)
    extracted_pool = pool_source_counts(manifest)
    questions = {q["eval_id"]: q for q in manifest.get("questions") or []}

    rr_blob = load_json(RR_ORIGINAL) if RR_ORIGINAL.is_file() else None

    ladders: dict[str, dict] = {}
    for p in paths:
        blob = load_json(p)
        ladders[ladder_name(blob, p)] = {"path": str(p), "blob": blob}

    skipped = [name for name in EXPECTED_LADDERS if name not in ladders]

    order_from = None
    for rec in ladders.values():
        order_from = blob_order(rec["blob"])
        if order_from:
            break
    if not order_from and rr_blob:
        order_from = blob_order(rr_blob)
    order = sorted(order_from or bank_ids)
    n_q = len(order)
    rng = np.random.default_rng(BOOT_SEED)
    boot_idx = rng.integers(0, n_q, size=(B, n_q), dtype=np.int64) if n_q else np.zeros((B, 0), dtype=np.int64)

    composition: dict[str, Any] = {
        "extracted_pool_source_counts": extracted_pool,
        "extracted_pool_source_shares": share_table(extracted_pool),
        "extracted_pool_source_shares_exact": share_fractions(extracted_pool),
        "round_robin_manifest": {str(s): rr_composition(manifest, s) for s in (5000, 10000, 100000)},
        "note": (
            "extracted_pool_* is the original 100k-schedule unique-doc source mix. "
            "union composition (when pool_ext is present) is under each ladder's by_scale full row."
        ),
    }

    for name, rec in ladders.items():
        meta = rec["blob"].get("meta") or {}
        comp_scales = meta.get("composition_at_scales") or {}
        by_scale: dict[str, Any] = {}
        for sc, comp in comp_scales.items():
            obs = share_fractions(comp)
            by_scale[str(sc)] = {
                "counts": comp,
                "n_docs": sum(comp.values()),
                "shares_rounded": share_table(comp),
                "shares": obs,
            }
        composition[name] = {
            "by_scale": by_scale,
            "union_document_count": meta.get("union_document_count"),
            "pool_filter": meta.get("pool_filter"),
            "table": meta.get("table"),
            "rank_table": meta.get("rank_table"),
        }

    hit_ladders: dict[str, dict[str, dict[str, float | None]]] = {}
    invariants: dict[str, dict[str, int]] = {}
    conf_by_scale: dict[str, dict[str, dict[str, float | None]]] = {}
    conf_set = set(conf_q)

    for name, rec in ladders.items():
        blob = rec["blob"]
        runs = index_runs(blob)
        labels = available_scale_labels(runs)
        hit_ladders[name] = {}
        conf_by_scale[name] = {c: {} for c in ("raw", "meta_first", "meta_in")}
        invariants[name] = run_invariants(blob, doc_source, questions)
        for cond in ("raw", "meta_first", "meta_in"):
            hit_ladders[name][cond] = {lab: hit10(runs.get((cond, lab))) for lab in labels}
            for lab in labels:
                conf_by_scale[name][cond][lab] = per_question_hit10(
                    runs.get((cond, lab), {}), conf_set
                )

    lifts: list[dict] = []
    for name, rec in ladders.items():
        runs = index_runs(rec["blob"])
        labels = available_scale_labels(runs)
        for mcond in META_COND:
            for lab in labels:
                raw_run = runs.get(("raw", lab))
                meta_run = runs.get((mcond, lab))
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
                        "condition": mcond,
                        "scale": lab,
                        "n_docs": raw_run.get("corpus_n") or raw_run.get("scale"),
                        "lift": point,
                        "ci_lo": lo,
                        "ci_hi": hi,
                        "n": n_q,
                    }
                )

    slopes: dict[str, Any] = {}
    for name, rec in ladders.items():
        blob = rec["blob"]
        runs = index_runs(blob)
        for cond in ("raw", "meta_first", "meta_in"):
            pts_100k: list[tuple[int, float]] = []
            pts_all: list[tuple[int, float]] = []
            for lab in available_scale_labels(runs):
                run = runs.get((cond, lab))
                y = hit10(run)
                x = x_for_label(blob, run, lab)
                if y is None or x is None or x <= 0:
                    continue
                pts_all.append((x, y))
                if lab != "full" and x <= 100000:
                    pts_100k.append((x, y))
            def fit(pts: list[tuple[int, float]]) -> dict[str, Any] | None:
                if len(pts) < 2:
                    return None
                pts = sorted(pts)
                sl, ic = slope_fit([p[0] for p in pts], [p[1] for p in pts])
                return {
                    "slope": sl,
                    "intercept": ic,
                    "n_points": len(pts),
                    "x": [p[0] for p in pts],
                    "y": [p[1] for p in pts],
                }
            slopes[f"{name}|{cond}"] = {
                "up_to_100k": fit(pts_100k),
                "including_150k_and_full": fit(pts_all),
            }

    drop_block: dict[str, Any] = {}

    def orig_run(cond: str, scale: int) -> dict | None:
        if not rr_blob:
            return None
        for run in rr_blob.get("runs") or []:
            if run["condition"] == cond and int(run["scale"]) == scale:
                return run
        return None

    for name, rec in ladders.items():
        runs = index_runs(rec["blob"])
        alt_out: dict[str, Any] = {}
        for cond in ("raw", "meta_first", "meta_in"):
            a5 = runs.get((cond, "5000"))
            a100 = runs.get((cond, "100000"))
            afull = runs.get((cond, "full"))
            cond_out: dict[str, Any] = {}
            if a5 and a100:
                drop = per_question_drop(a5, a100, order)
                if drop is not None:
                    d_est, d_lo, d_hi = mean_ci_one(drop, boot_idx)
                    cond_out["drop_5k_to_100k"] = {
                        "estimate": d_est,
                        "ci_lo": d_lo,
                        "ci_hi": d_hi,
                    }
                    r5 = orig_run(cond, 5000)
                    r100 = orig_run(cond, 100000)
                    if r5 and r100:
                        rr_drop = per_question_drop(r5, r100, order)
                        if rr_drop is not None:
                            e, lo, hi = mean_ci_diff(drop, rr_drop, boot_idx)
                            cond_out["drop_5k_to_100k_minus_original_rr"] = {
                                "estimate": e,
                                "ci_lo": lo,
                                "ci_hi": hi,
                                "original_rr_drop": float(rr_drop.mean()),
                            }
            if a5 and afull:
                dropf = per_question_drop(a5, afull, order)
                if dropf is not None:
                    d_est, d_lo, d_hi = mean_ci_one(dropf, boot_idx)
                    cond_out["drop_5k_to_full"] = {
                        "estimate": d_est,
                        "ci_lo": d_lo,
                        "ci_hi": d_hi,
                        "full_n": afull.get("corpus_n") or afull.get("scale"),
                    }
                    r5 = orig_run(cond, 5000)
                    r100 = orig_run(cond, 100000)
                    if r5 and r100:
                        rr_drop = per_question_drop(r5, r100, order)
                        if rr_drop is not None:
                            e, lo, hi = mean_ci_diff(dropf, rr_drop, boot_idx)
                            cond_out["drop_5k_to_full_minus_original_rr"] = {
                                "estimate": e,
                                "ci_lo": lo,
                                "ci_hi": hi,
                                "original_rr_drop": float(rr_drop.mean()),
                            }
            if cond_out:
                alt_out[cond] = cond_out
        if alt_out:
            drop_block[name] = alt_out

    acceptance: list[dict] = []
    for miss in skipped:
        acceptance.append(
            {
                "name": f"ladder_present_{miss}",
                "pass": None,
                "status": "SKIP",
                "reason": "missing input JSON",
            }
        )
    for name, inv in invariants.items():
        ok = all(v == 0 for v in inv.values())
        acceptance.append({"name": f"invariants_zero_{name}", "pass": ok, "values": inv})
    if rr_blob is None:
        acceptance.append(
            {
                "name": "original_rr_present",
                "pass": None,
                "status": "SKIP",
                "path": str(RR_ORIGINAL),
            }
        )

    return {
        "confluence_first_n": len(conf_q),
        "confluence_first_question_ids": conf_q,
        "n_questions_aligned": n_q,
        "bootstrap": {"B": B, "seed": BOOT_SEED},
        "skipped_ladders": skipped,
        "composition": composition,
        "hit_at_10_ladders": hit_ladders,
        "confluence_hit_at_10": conf_by_scale,
        "slopes": slopes,
        "metadata_lift": lifts,
        "drop": drop_block,
        "invariants": invariants,
        "acceptance": acceptance,
        "inputs": [str(p) for p in paths],
    }


def write_md(payload: dict, path: Path) -> None:
    lines = ["# Pool ladder analysis", ""]
    lines.append(f"- Confluence-first questions: **{payload['confluence_first_n']}**")
    lines.append(f"- Aligned questions: **{payload['n_questions_aligned']}**")
    skipped = payload.get("skipped_ladders") or []
    if skipped:
        lines.append(f"- SKIP missing ladders: {', '.join(skipped)}")
    lines.append("")
    lines.append("## Acceptance")
    lines.append("")
    lines.append("| test | pass | detail |")
    lines.append("|------|:----:|--------|")
    for a in payload["acceptance"]:
        detail = {k: v for k, v in a.items() if k not in ("name", "pass")}
        flag = a.get("status") if a.get("pass") is None else a.get("pass")
        lines.append(f"| {a['name']} | {flag} | {detail} |")
    lines.append("")
    lines.append("## Hit@10")
    fmt = lambda x: f"{x:.4f}" if x is not None else "—"
    for ladder, conds in payload["hit_at_10_ladders"].items():
        labels: list[str] = []
        for cond in conds.values():
            for k in cond:
                if k not in labels:
                    labels.append(k)
        lines.append(f"\n### {ladder}")
        lines.append("| scale | raw | meta_first | meta_in |")
        lines.append("|------:|----:|-----------:|--------:|")
        for lab in labels:
            raw = conds.get("raw", {}).get(lab)
            mf = conds.get("meta_first", {}).get(lab)
            mi = conds.get("meta_in", {}).get(lab)
            lines.append(f"| {lab} | {fmt(raw)} | {fmt(mf)} | {fmt(mi)} |")
    lines.append("")
    lines.append("## Composition shares")
    comp = payload.get("composition") or {}
    ep = comp.get("extracted_pool_source_shares") or {}
    lines.append(f"- extracted pool (100k unique): {ep}")
    for name in EXPECTED_LADDERS:
        block = comp.get(name) or {}
        by_scale = block.get("by_scale") or {}
        if not by_scale:
            continue
        lines.append(f"\n### {name}")
        lines.append("| scale | n | shares |")
        lines.append("|------:|--:|--------|")
        for lab, row in by_scale.items():
            lines.append(f"| {lab} | {row.get('n_docs')} | {row.get('shares_rounded')} |")
    lines.append("")
    lines.append("## Drop 5k vs 100k / full (paired bootstrap)")
    for ladder, conds in (payload.get("drop") or {}).items():
        lines.append(f"\n### {ladder}")
        for cond, row in conds.items():
            lines.append(f"- **{cond}**: `{json.dumps(row)}`")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inputs", type=Path, nargs="*", default=None)
    parser.add_argument("--out-json", type=Path, default=OUT_JSON)
    parser.add_argument("--out-md", type=Path, default=OUT_MD)
    args = parser.parse_args()
    paths = args.inputs or discover_pool_json()
    payload = analyze(paths)
    if not paths:
        payload["acceptance"].insert(
            0,
            {"name": "inputs_present", "pass": None, "status": "SKIP", "reason": "no pool JSON"},
        )
    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    write_md(payload, args.out_md)
    print(f"wrote {args.out_json}")
    print(f"wrote {args.out_md}")
    failed = [a for a in payload["acceptance"] if a.get("pass") is False]
    skipped = [a for a in payload["acceptance"] if a.get("status") == "SKIP"]
    print(f"acceptance FAIL={len(failed)} SKIP={len(skipped)}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
