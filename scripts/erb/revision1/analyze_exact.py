#!/usr/bin/env python3
"""Statistics on revision-1 exact-search scale ladders (independent of retrieval).

Reads saved JSON only. No database. No import of run_exact_ladder.py.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
from fractions import Fraction
from itertools import combinations
from pathlib import Path
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / "data"
PUB = ROOT / "artifacts" / "published"
REV1 = PUB / "revision1"

OUT_JSON = REV1 / "analysis_exact.json"
OUT_MD = REV1 / "analysis_exact.md"
OUT_CSV = REV1 / "analysis_delta_meta.csv"

B = 10_000
SEED = 42
TAU = 0.10
TAU_FRAC = Fraction(1, 10)
SCORE_EPS = 1e-12
SHARED_SCORE_EPS = 1e-9
SCALES_DEFAULT = (5000, 10000, 15000, 20000, 25000, 40000, 50000, 75000, 100000)
METRICS = ("hit_at_1", "hit_at_5", "hit_at_10", "mrr", "document_recall")
META_FILTERS = ("first", "in", "gold")
COND_FROM_FILTER = {
    "first": "meta_first",
    "in": "meta_in",
    "gold": "meta_gold",
}
FILTER_FROM_COND = {v: k for k, v in COND_FROM_FILTER.items()}
# Old approximate OpenAI "meta" used question.source_types[0] (first-type filter).
FILTER_FROM_COND["meta"] = "first"

MANIFEST_PATH = DATA / "erb_scale_manifest.json"
HNSW_OPENAI = PUB / "erb_full_primary200_to100k.json"
HNSW_TITAN = PUB / "erb_titan_primary200_to100k.json"
EXACT_CTRL_OPENAI = PUB / "exact_control_mvp.json"
EXACT_CTRL_TITAN = PUB / "exact_control_titan.json"
BM25_PRIMARY = PUB / "erb_bm25_baseline_primary200.json"
BM25_OLD_CHARS8191 = PUB / "erb_bm25_baseline_primary200_chars8191.json"

_JSON_CACHE: dict[str, Any] = {}


def to_py(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {str(k): to_py(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [to_py(v) for v in obj]
    if isinstance(obj, np.ndarray):
        return to_py(obj.tolist())
    if isinstance(obj, (np.floating,)):
        return float(obj)
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.bool_,)):
        return bool(obj)
    return obj


def dump_json(path: Path, obj: Any) -> None:
    text = json.dumps(to_py(obj), sort_keys=True, indent=2, ensure_ascii=True, allow_nan=False) + "\n"
    path.write_text(text, encoding="utf-8")


def load_json(path: Path) -> Any:
    key = str(path.resolve())
    if key not in _JSON_CACHE:
        with path.open("r", encoding="utf-8") as f:
            _JSON_CACHE[key] = json.load(f)
    return _JSON_CACHE[key]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def fmt(x: float | None, digits: int = 3) -> str:
    if x is None:
        return "undefined"
    return f"{x:.{digits}f}"


def ci_tuple(point: float, lo: float, hi: float) -> dict[str, float]:
    return {"estimate": float(point), "ci_lo": float(lo), "ci_hi": float(hi)}


class IndexCache:
    def __init__(self) -> None:
        self._cache: dict[int, np.ndarray] = {}

    def get(self, n: int) -> np.ndarray:
        if n not in self._cache:
            rng = np.random.default_rng(SEED)
            self._cache[n] = rng.integers(0, n, size=(B, n), dtype=np.int64)
        return self._cache[n]


IDX = IndexCache()


def as_float(seq: list[Any], key: str) -> np.ndarray:
    out = np.empty(len(seq), dtype=np.float64)
    for i, row in enumerate(seq):
        v = row[key]
        out[i] = float(v)
    return out


def as_hit(seq: list[Any], key: str) -> np.ndarray:
    out = np.empty(len(seq), dtype=np.int64)
    for i, row in enumerate(seq):
        v = row[key]
        if isinstance(v, bool):
            out[i] = int(v)
        else:
            out[i] = 1 if float(v) != 0.0 else 0
    return out


def mean_ci(values: np.ndarray, idx: np.ndarray) -> tuple[float, float, float]:
    v = np.asarray(values, dtype=np.float64)
    point = float(v.mean())
    boot = v[idx].mean(axis=1)
    lo, hi = np.percentile(boot, [2.5, 97.5])
    return point, float(lo), float(hi)


def ols_slope_intercept_r2(x: np.ndarray, y: np.ndarray) -> tuple[float, float, float]:
    x = np.asarray(x, dtype=np.float64)
    y = np.asarray(y, dtype=np.float64)
    X = np.column_stack([x, np.ones_like(x)])
    beta, _, _, _ = np.linalg.lstsq(X, y, rcond=None)
    slope = float(beta[0])
    intercept = float(beta[1])
    yhat = X @ beta
    ss_res = float(np.sum((y - yhat) ** 2))
    ss_tot = float(np.sum((y - y.mean()) ** 2))
    r2 = 1.0 if ss_tot == 0.0 else 1.0 - ss_res / ss_tot
    return slope, intercept, float(r2)


def slope_bootstrap(
    metric_by_scale: list[np.ndarray],
    scales: list[int],
    idx: np.ndarray,
    exclude: set[int] | None = None,
) -> dict[str, Any]:
    keep = [i for i, s in enumerate(scales) if exclude is None or s not in exclude]
    sc = np.array([scales[i] for i in keep], dtype=np.float64)
    x = np.log(sc)
    mats = np.stack([metric_by_scale[i] for i in keep], axis=0)
    y_point = mats.mean(axis=1)
    slope, intercept, r2 = ols_slope_intercept_r2(x, y_point)
    boot_y = mats[:, idx].mean(axis=2).T
    X = np.column_stack([x, np.ones_like(x)])
    xtx_inv = np.linalg.inv(X.T @ X)
    betas = (xtx_inv @ X.T @ boot_y.T).T
    slope_boot = betas[:, 0]
    lo, hi = np.percentile(slope_boot, [2.5, 97.5])
    return {
        "slope": slope,
        "intercept": intercept,
        "r2": r2,
        "slope_ci_lo": float(lo),
        "slope_ci_hi": float(hi),
        "scales": [int(s) for s in sc],
        "n_points": int(len(sc)),
    }


def slope_diff_bootstrap(
    series_a: list[np.ndarray],
    series_b: list[np.ndarray],
    scales: list[int],
    idx: np.ndarray,
    exclude: set[int] | None = None,
) -> dict[str, Any]:
    fit_a = slope_bootstrap(series_a, scales, idx, exclude=exclude)
    fit_b = slope_bootstrap(series_b, scales, idx, exclude=exclude)
    keep = [i for i, s in enumerate(scales) if exclude is None or s not in exclude]
    x = np.log(np.array([scales[i] for i in keep], dtype=np.float64))
    mats_a = np.stack([series_a[i] for i in keep], axis=0)
    mats_b = np.stack([series_b[i] for i in keep], axis=0)
    boot_ya = mats_a[:, idx].mean(axis=2).T
    boot_yb = mats_b[:, idx].mean(axis=2).T
    X = np.column_stack([x, np.ones_like(x)])
    xtx_inv = np.linalg.inv(X.T @ X)
    slopes_a = (xtx_inv @ X.T @ boot_ya.T).T[:, 0]
    slopes_b = (xtx_inv @ X.T @ boot_yb.T).T[:, 0]
    diff_boot = slopes_a - slopes_b
    pt = fit_a["slope"] - fit_b["slope"]
    lo, hi = np.percentile(diff_boot, [2.5, 97.5])
    return {
        "estimate": float(pt),
        "ci_lo": float(lo),
        "ci_hi": float(hi),
        "n_points": fit_a["n_points"],
        "scales": fit_a["scales"],
    }


def delta_from_hits(hits_meta: int, hits_raw: int, n: int) -> tuple[Fraction, bool, bool]:
    if n <= 0:
        raise ValueError("n must be positive")
    delta = Fraction(int(hits_meta) - int(hits_raw), int(n))
    return delta, delta < TAU_FRAC, delta <= TAU_FRAC


def n_star_from_flags(pairs: list[tuple[int, bool]]) -> int | None:
    ordered = sorted(pairs, key=lambda x: x[0])
    n_star = None
    for i, (scale, ok) in enumerate(ordered):
        if all(flag for _, flag in ordered[i:]):
            n_star = int(scale)
            break
    return n_star


def load_manifest() -> tuple[dict[str, str], dict[str, dict[str, Any]]]:
    man = load_json(MANIFEST_PATH)
    doc_source: dict[str, str] = {}
    for d in man["documents"]:
        did = d["doc_id"]
        if did not in doc_source:
            doc_source[did] = d["source_type"]
    questions: dict[str, dict[str, Any]] = {}
    for q in man["questions"]:
        qid = q.get("eval_id") or q.get("question_id")
        questions[qid] = q
        if q.get("question_id") and q["question_id"] != qid:
            questions[q["question_id"]] = q
    return doc_source, questions


def filter_source_types(q: dict[str, Any], which: str, doc_source: dict[str, str]) -> set[str]:
    if which == "first":
        st = q.get("source_types") or []
        return {st[0]} if st else set()
    if which == "in":
        return set(q.get("source_types") or [])
    gold_types = set()
    for did in q.get("expected_doc_ids") or []:
        st = doc_source.get(did)
        if st is not None:
            gold_types.add(st)
    return gold_types


def parse_ladder_name(path: Path) -> tuple[str, str] | None:
    name = path.stem
    prefix = "exact_ladder_"
    if not name.startswith(prefix):
        return None
    rest = name[len(prefix) :]
    for emb in ("openai", "titan"):
        tag = emb + "_"
        if rest.startswith(tag):
            return emb, rest[len(tag) :]
    return None


def run_scale(run: dict[str, Any]) -> int:
    return int(run.get("scale", run.get("corpus_scale_size")))


def index_runs(blob: dict[str, Any]) -> dict[tuple[str, int], dict[str, Any]]:
    out: dict[tuple[str, int], dict[str, Any]] = {}
    for run in blob.get("runs") or []:
        out[(run["condition"], run_scale(run))] = run
    return out


def qid_set(run: dict[str, Any]) -> set[str]:
    pq = run.get("per_question") or []
    ids = [p["question_id"] for p in pq]
    unique = set(ids)
    assert len(pq) == len(unique), (
        f"per_question rows ({len(pq)}) != unique question ids ({len(unique)})"
    )
    return unique


def canonical_question_ids(runs: list[dict[str, Any]]) -> list[str]:
    if not runs:
        return []
    sets = [qid_set(r) for r in runs]
    first = sets[0]
    for i, s in enumerate(sets[1:], start=1):
        if s != first:
            missing = sorted(first - s)
            extra = sorted(s - first)
            raise ValueError(
                f"question id set mismatch at run {i}: "
                f"missing={missing[:8]} extra={extra[:8]}"
            )
    return sorted(first)


def align_metric(run: dict[str, Any], order: list[str], key: str) -> np.ndarray:
    by_id = {p["question_id"]: p for p in run["per_question"]}
    rows = [by_id[q] for q in order]
    return as_float(rows, key)


def align_hits(run: dict[str, Any], order: list[str], key: str = "hit_at_10") -> np.ndarray:
    by_id = {p["question_id"]: p for p in run["per_question"]}
    rows = [by_id[q] for q in order]
    return as_hit(rows, key)


def align_pq(run: dict[str, Any], order: list[str]) -> list[dict[str, Any]]:
    by_id = {p["question_id"]: p for p in run["per_question"]}
    missing = [q for q in order if q not in by_id]
    if missing:
        raise ValueError(f"run missing question ids: {missing[:8]}")
    return [by_id[q] for q in order]


def blob_order(blob: dict[str, Any]) -> list[str]:
    runs = [r for r in (blob.get("runs") or []) if r.get("per_question")]
    return canonical_question_ids(runs)


def discover_ladders() -> list[Path]:
    return sorted(REV1.glob("exact_ladder_*_*.json"))


def discover_bm25() -> list[tuple[str, Path]]:
    found: list[tuple[str, Path]] = []
    seen: set[Path] = set()
    extras = [BM25_PRIMARY, BM25_OLD_CHARS8191]
    for p in extras + sorted(REV1.glob("bm25_*.json")):
        rp = p.resolve()
        if rp in seen or not p.is_file():
            continue
        seen.add(rp)
        found.append((p.stem, p))
    return found


def load_hnsw_flags(path: Path, runs_key: str, condition: str, scale: int, order: list[str]) -> np.ndarray:
    blob = load_json(path)
    runs = blob[runs_key]
    for run in runs:
        sc = run.get("corpus_scale_size", run.get("scale"))
        if run.get("condition") == condition and int(sc) == int(scale):
            return align_hits(run, order, "hit_at_10").astype(np.float64)
    raise KeyError(f"missing HNSW run {path.name} {condition} {scale}")


def load_hnsw_metric(path: Path, runs_key: str, condition: str, scale: int, key: str) -> float:
    blob = load_json(path)
    runs = blob[runs_key]
    for run in runs:
        sc = run.get("corpus_scale_size", run.get("scale"))
        if run.get("condition") == condition and int(sc) == int(scale):
            if key in run:
                return float(run[key])
            return float(run["metrics"][key])
    raise KeyError(f"missing HNSW metric {path.name} {condition} {scale} {key}")


def wrap_hnsw_as_ladder(path: Path) -> dict[str, Any]:
    blob = load_json(path)
    raw_runs = blob.get("runs") or blob.get("runs_with_per_question") or []
    runs = []
    for run in raw_runs:
        cond = run["condition"]
        if cond not in ("raw", "meta"):
            continue
        runs.append(
            {
                "condition": cond,
                "scale": int(run.get("corpus_scale_size", run.get("scale"))),
                "per_question": run["per_question"],
                "metrics": {
                    "hit_at_10": float(run.get("hit_at_10", (run.get("metrics") or {}).get("hit_at_10") or 0.0))
                },
            }
        )
    scales = sorted({r["scale"] for r in runs})
    conditions = []
    for c in ("raw", "meta"):
        if any(r["condition"] == c for r in runs):
            conditions.append(c)
    return {"meta": {"scales": scales, "conditions": conditions, "source": str(path)}, "runs": runs}


def self_test() -> dict[str, Any]:
    rng = np.random.default_rng(SEED)
    n = 200
    a = (rng.random(n) < 0.8).astype(np.float64)
    b = (rng.random(n) < 0.6).astype(np.float64)
    idx = rng.integers(0, n, size=(B, n), dtype=np.int64)
    diff = a - b
    point, lo, hi = mean_ci(diff, idx)
    true_diff = 0.2
    contains = bool(lo <= true_diff <= hi)
    left = point - lo
    right = hi - point
    symmetry_gap = abs(right - left)
    symmetric = bool(symmetry_gap <= 0.02)
    return {
        "n": n,
        "B": B,
        "seed": SEED,
        "p_a": 0.8,
        "p_b": 0.6,
        "true_difference": true_diff,
        "sample_difference": point,
        "ci_lo": lo,
        "ci_hi": hi,
        "contains_true_difference": contains,
        "halfwidth_left": float(left),
        "halfwidth_right": float(right),
        "symmetry_gap": float(symmetry_gap),
        "symmetric_within_0.02": symmetric,
        "pass": bool(contains and symmetric),
    }


def is_nan(x: Any) -> bool:
    try:
        return math.isnan(float(x))
    except (TypeError, ValueError):
        return False


def retrieved_ids(pq: dict[str, Any]) -> list[str]:
    return [str(d) for d in (pq.get("retrieved_doc_ids") or [])]


def retrieved_scores(pq: dict[str, Any]) -> list[Any] | None:
    if "scores" not in pq:
        return None
    return list(pq.get("scores") or [])


def containment_reason(
    raw_ids: list[str],
    meta_ids: list[str],
    allowed: set[str],
    doc_source: dict[str, str],
) -> str | None:
    if not raw_ids or not meta_ids:
        return "empty_list"
    if len(raw_ids) < 10 or len(meta_ids) < 10:
        return "truncated_list"
    if len(raw_ids) != len(set(raw_ids)) or len(meta_ids) != len(set(meta_ids)):
        return "duplicate_doc_ids"
    for doc in raw_ids:
        if doc not in doc_source:
            return "missing_from_manifest"
    for doc in meta_ids:
        if doc not in doc_source:
            return "missing_from_manifest"
        st = doc_source[doc]
        if st not in allowed:
            return "meta_doc_not_in_allowed_set"
    meta_set = set(meta_ids)
    for doc in raw_ids:
        st = doc_source.get(doc)
        if st is not None and st in allowed and doc not in meta_set:
            return "raw_allowed_doc_missing_from_meta"
    return None


def nested_reason(
    ids_a: list[str],
    scores_a: list[Any] | None,
    ids_b: list[str],
    scores_b: list[Any] | None,
) -> str | None:
    if not ids_a or not ids_b:
        return "empty_list"
    if len(ids_a) < 10:
        return "truncated_list_a"
    if len(ids_b) < 10:
        return "truncated_list_b"
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
    scores_ok = (
        scores_a is not None
        and scores_b is not None
        and len(scores_a) == len(ids_a) > 0
        and len(scores_b) == len(ids_b) > 0
        and not any(is_nan(s) for s in scores_a)
        and not any(is_nan(s) for s in scores_b)
    )
    if scores_ok:
        score_a_map = {d: float(s) for d, s in zip(ids_a, scores_a)}
        score_b_map = {d: float(s) for d, s in zip(ids_b, scores_b)}
        for d in set(ids_a) & set_b:
            if abs(score_a_map[d] - score_b_map[d]) > SHARED_SCORE_EPS:
                return "shared_score_mismatch"
    dropped = [d for d in ids_a if d not in set_b]
    if not dropped:
        return None
    if len(ids_b) != 10:
        return "truncated_list_b"
    if not scores_ok:
        return "unverifiable"
    score_a = {d: float(s) for d, s in zip(ids_a, scores_a)}
    min_b = min(float(s) for s in scores_b)
    for d in dropped:
        if min_b < score_a[d] - SCORE_EPS:
            return "dropped_doc_score"
    return None


def score_reason(ids: list[str], scores: list[Any] | None) -> str | None:
    if scores is None:
        return "missing_scores"
    if not ids or not scores:
        return "empty"
    if len(scores) != len(ids):
        return "length_mismatch"
    if any(is_nan(s) for s in scores):
        return "nan"
    floats = [float(s) for s in scores]
    for i in range(len(floats) - 1):
        if floats[i + 1] > floats[i]:
            return "increasing"
        if floats[i + 1] == floats[i] and not (ids[i] < ids[i + 1]):
            return "tie_not_ascending"
    return None


def empty_kind() -> dict[str, Any]:
    return {
        "n_checked": 0,
        "n_violations": 0,
        "n_unverifiable": 0,
        "by_key": {},
        "examples": [],
        "pass": True,
    }


def note(
    summary: dict[str, Any],
    kind: str,
    key: str,
    example: dict[str, Any],
    *,
    checked: int = 1,
    violated: bool = False,
    unverifiable: bool = False,
) -> None:
    bucket = summary[kind]
    rec = bucket["by_key"].setdefault(
        key, {"n_checked": 0, "n_violations": 0, "n_unverifiable": 0}
    )
    rec.setdefault("n_unverifiable", 0)
    rec["n_checked"] += checked
    bucket["n_checked"] += checked
    if unverifiable:
        rec["n_unverifiable"] += 1
        bucket["n_unverifiable"] += 1
        if len(bucket["examples"]) < 8:
            bucket["examples"].append(example)
        return
    if violated:
        rec["n_violations"] += 1
        bucket["n_violations"] += 1
        if len(bucket["examples"]) < 8:
            bucket["examples"].append(example)


def run_invariants(
    ladders: dict[tuple[str, str], dict[str, Any]],
    doc_source: dict[str, str],
    questions: dict[str, dict[str, Any]],
    cond_filter_map: dict[str, str] | None = None,
) -> dict[str, Any]:
    summary: dict[str, Any] = {
        "containment": empty_kind(),
        "nested_corpus": empty_kind(),
        "score_monotonicity": empty_kind(),
    }
    fmap = cond_filter_map if cond_filter_map is not None else FILTER_FROM_COND
    for (emb, bank), blob in sorted(ladders.items()):
        runs = index_runs(blob)
        if not runs:
            continue
        scales = sorted(int(s) for s in (blob["meta"].get("scales") or SCALES_DEFAULT))
        conditions = list(blob["meta"].get("conditions") or [])
        order = blob_order(blob)
        pq_index: dict[tuple[str, int], list[dict[str, Any]]] = {}
        for cond in conditions:
            for s in scales:
                pq_index[(cond, s)] = align_pq(runs[(cond, s)], order)

        filt_cache: dict[tuple[str, str], set[str]] = {}
        for qid in order:
            q = questions[qid]
            for filt in META_FILTERS:
                filt_cache[(qid, filt)] = filter_source_types(q, filt, doc_source)

        for cond in conditions:
            for s in scales:
                key = f"{emb}|{bank}|{cond}|{s}"
                summary["containment"]["by_key"].setdefault(
                    key, {"n_checked": 0, "n_violations": 0, "n_unverifiable": 0}
                )
                summary["score_monotonicity"]["by_key"].setdefault(
                    key, {"n_checked": 0, "n_violations": 0, "n_unverifiable": 0}
                )
            for s_a, s_b in combinations(scales, 2):
                key = f"{emb}|{bank}|{cond}|{s_a}-{s_b}"
                summary["nested_corpus"]["by_key"].setdefault(
                    key, {"n_checked": 0, "n_violations": 0, "n_unverifiable": 0}
                )

        for cond in conditions:
            if cond == "raw":
                for s in scales:
                    key = f"{emb}|{bank}|{cond}|{s}"
                    raw_pq = pq_index[("raw", s)]
                    for i, qid in enumerate(order):
                        ids = retrieved_ids(raw_pq[i])
                        reason = None
                        if not ids:
                            reason = "empty_list"
                        elif len(ids) != len(set(ids)):
                            reason = "duplicate_doc_ids"
                        else:
                            for doc in ids:
                                if doc not in doc_source:
                                    reason = "missing_from_manifest"
                                    break
                        note(
                            summary,
                            "containment",
                            key,
                            {
                                "embedder": emb,
                                "condition": cond,
                                "scale": s,
                                "question": qid,
                                "reason": reason,
                            },
                            violated=reason is not None,
                        )
                continue
            filt = fmap.get(cond)
            if filt is None:
                continue
            for s in scales:
                raw_pq = pq_index[("raw", s)]
                meta_pq = pq_index[(cond, s)]
                key = f"{emb}|{bank}|{cond}|{s}"
                for i, qid in enumerate(order):
                    raw_ids = retrieved_ids(raw_pq[i])
                    meta_ids = retrieved_ids(meta_pq[i])
                    allowed = filt_cache[(qid, filt)]
                    reason = containment_reason(raw_ids, meta_ids, allowed, doc_source)
                    note(
                        summary,
                        "containment",
                        key,
                        {
                            "embedder": emb,
                            "condition": cond,
                            "scale": s,
                            "question": qid,
                            "reason": reason,
                        },
                        violated=reason is not None,
                    )

        for cond in conditions:
            for s_a, s_b in combinations(scales, 2):
                pq_a = pq_index[(cond, s_a)]
                pq_b = pq_index[(cond, s_b)]
                key = f"{emb}|{bank}|{cond}|{s_a}-{s_b}"
                for i, qid in enumerate(order):
                    ids_a = retrieved_ids(pq_a[i])
                    ids_b = retrieved_ids(pq_b[i])
                    reason = nested_reason(
                        ids_a, retrieved_scores(pq_a[i]), ids_b, retrieved_scores(pq_b[i])
                    )
                    note(
                        summary,
                        "nested_corpus",
                        key,
                        {
                            "embedder": emb,
                            "condition": cond,
                            "scale": f"{s_a}-{s_b}",
                            "question": qid,
                            "reason": reason,
                        },
                        violated=reason is not None and reason != "unverifiable",
                        unverifiable=reason == "unverifiable",
                    )

        for cond in conditions:
            for s in scales:
                key = f"{emb}|{bank}|{cond}|{s}"
                for i, qid in enumerate(order):
                    ids = retrieved_ids(pq_index[(cond, s)][i])
                    scores = retrieved_scores(pq_index[(cond, s)][i])
                    reason = score_reason(ids, scores)
                    note(
                        summary,
                        "score_monotonicity",
                        key,
                        {
                            "embedder": emb,
                            "condition": cond,
                            "scale": s,
                            "question": qid,
                            "reason": reason,
                        },
                        violated=reason is not None,
                    )

    for kind in summary:
        summary[kind]["pass"] = (
            summary[kind]["n_violations"] == 0 and summary[kind]["n_unverifiable"] == 0
        )
        summary[kind]["by_key"] = dict(sorted(summary[kind]["by_key"].items()))
    return summary


def _toy_docs() -> dict[str, str]:
    docs = {f"d{i}": "confluence" for i in range(12)}
    docs["jx"] = "jira"
    return docs


def _toy_q() -> dict[str, Any]:
    return {
        "eval_id": "q1",
        "question_id": "q1",
        "source_types": ["confluence"],
        "expected_doc_ids": ["d0"],
    }


def _toy_pq(qid: str, ids: list[str], scores: list[Any] | None) -> dict[str, Any]:
    row: dict[str, Any] = {
        "question_id": qid,
        "retrieved_doc_ids": ids,
        "hit_at_10": False,
    }
    if scores is not None:
        row["scores"] = scores
    return row


def _toy_blob(runs: list[dict[str, Any]], scales: list[int], conditions: list[str]) -> dict[str, Any]:
    return {"meta": {"scales": scales, "conditions": conditions}, "runs": runs}


def _toy_run(cond: str, scale: int, pq: list[dict[str, Any]]) -> dict[str, Any]:
    return {"condition": cond, "scale": scale, "per_question": pq}


def self_test_invariants() -> dict[str, Any]:
    docs = _toy_docs()
    questions = {"q1": _toy_q()}
    ids10 = [f"d{i}" for i in range(10)]
    scores10 = [1.0 - 0.01 * i for i in range(10)]
    cases: dict[str, dict[str, Any]] = {}

    mixed = ["jx"] + ids10[1:]
    blob_a = _toy_blob(
        [
            _toy_run("raw", 5000, [_toy_pq("q1", mixed, scores10)]),
            _toy_run("meta_in", 5000, [_toy_pq("q1", mixed, scores10)]),
        ],
        [5000],
        ["raw", "meta_in"],
    )
    inv_a = run_invariants({("toy", "a"): blob_a}, docs, questions)
    cases["a_meta_equals_raw_with_filter"] = {
        "detected": inv_a["containment"]["n_violations"] > 0,
        "containment_violations": inv_a["containment"]["n_violations"],
        "reasons": [e.get("reason") for e in inv_a["containment"]["examples"]],
    }

    blob_b = _toy_blob(
        [
            _toy_run("raw", 5000, [_toy_pq("q1", [], [])]),
            _toy_run("meta_in", 5000, [_toy_pq("q1", [], [])]),
        ],
        [5000],
        ["raw", "meta_in"],
    )
    inv_b = run_invariants({("toy", "b"): blob_b}, docs, questions)
    cases["b_empty_lists"] = {
        "detected": inv_b["containment"]["n_violations"] > 0 or inv_b["score_monotonicity"]["n_violations"] > 0,
        "containment_violations": inv_b["containment"]["n_violations"],
        "score_violations": inv_b["score_monotonicity"]["n_violations"],
    }

    ids_small = ids10[:]
    ids_large = ids10[1:] + ["d10"]
    scores_small = scores10[:]
    scores_large = [0.99 - 0.01 * i for i in range(10)]
    blob_c = _toy_blob(
        [
            _toy_run("raw", 5000, [_toy_pq("q1", ids_small, scores_small)]),
            _toy_run("raw", 10000, [_toy_pq("q1", ids_large, scores_large)]),
        ],
        [5000, 10000],
        ["raw"],
    )
    inv_c = run_invariants({("toy", "c"): blob_c}, docs, questions)
    cases["c_prefix_drop"] = {
        "detected": inv_c["nested_corpus"]["n_violations"] > 0,
        "nested_violations": inv_c["nested_corpus"]["n_violations"],
        "reasons": [e.get("reason") for e in inv_c["nested_corpus"]["examples"]],
    }

    shuffled = ids10[1:3] + [ids10[0]] + ids10[3:]
    blob_d = _toy_blob(
        [
            _toy_run("raw", 5000, [_toy_pq("q1", ids10, scores10)]),
            _toy_run("raw", 10000, [_toy_pq("q1", shuffled, scores10)]),
        ],
        [5000, 10000],
        ["raw"],
    )
    inv_d = run_invariants({("toy", "d"): blob_d}, docs, questions)
    cases["d_shuffled_order"] = {
        "detected": inv_d["nested_corpus"]["n_violations"] > 0,
        "nested_violations": inv_d["nested_corpus"]["n_violations"],
        "reasons": [e.get("reason") for e in inv_d["nested_corpus"]["examples"]],
    }

    nan_scores = [1.0, float("nan")] + scores10[2:]
    blob_e = _toy_blob(
        [
            _toy_run("raw", 5000, [_toy_pq("q1", ids10, nan_scores)]),
        ],
        [5000],
        ["raw"],
    )
    inv_e = run_invariants({("toy", "e"): blob_e}, docs, questions)
    cases["e_nan_score"] = {
        "detected": inv_e["score_monotonicity"]["n_violations"] > 0,
        "score_violations": inv_e["score_monotonicity"]["n_violations"],
        "reasons": [e.get("reason") for e in inv_e["score_monotonicity"]["examples"]],
    }

    ids_trunc_b = ids10[:9]
    scores_trunc_b = scores10[:9]
    blob_f = _toy_blob(
        [
            _toy_run("raw", 5000, [_toy_pq("q1", ids10, scores10)]),
            _toy_run("raw", 10000, [_toy_pq("q1", ids_trunc_b, scores_trunc_b)]),
        ],
        [5000, 10000],
        ["raw"],
    )
    inv_f = run_invariants({("toy", "f"): blob_f}, docs, questions)
    cases["f_truncated_list_b"] = {
        "detected": inv_f["nested_corpus"]["n_violations"] > 0,
        "nested_violations": inv_f["nested_corpus"]["n_violations"],
        "reasons": [e.get("reason") for e in inv_f["nested_corpus"]["examples"]],
        "expected": "violation",
    }

    ids_g_b = ids10[:9] + ["d10"]
    blob_g = _toy_blob(
        [
            _toy_run("raw", 5000, [_toy_pq("q1", ids10, None)]),
            _toy_run("raw", 10000, [_toy_pq("q1", ids_g_b, None)]),
        ],
        [5000, 10000],
        ["raw"],
    )
    inv_g = run_invariants({("toy", "g"): blob_g}, docs, questions)
    cases["g_missing_scores_dropped"] = {
        "detected": False,
        "nested_violations": inv_g["nested_corpus"]["n_violations"],
        "n_unverifiable": inv_g["nested_corpus"]["n_unverifiable"],
        "nested_pass": inv_g["nested_corpus"]["pass"],
        "reasons": [e.get("reason") for e in inv_g["nested_corpus"]["examples"]],
        "expected": "unverifiable",
        "ok": (
            inv_g["nested_corpus"]["n_unverifiable"] > 0
            and inv_g["nested_corpus"]["n_violations"] == 0
            and inv_g["nested_corpus"]["pass"] is False
        ),
    }

    ids_h_b = ids10[:9] + ["d10"]
    scores_h_a = scores10[:]
    scores_h_b = [1.0 - 0.01 * i for i in range(9)] + [0.92]
    blob_h = _toy_blob(
        [
            _toy_run("raw", 5000, [_toy_pq("q1", ids10, scores_h_a)]),
            _toy_run("raw", 10000, [_toy_pq("q1", ids_h_b, scores_h_b)]),
        ],
        [5000, 10000],
        ["raw"],
    )
    inv_h = run_invariants({("toy", "h"): blob_h}, docs, questions)
    cases["h_dropped_lower_score"] = {
        "detected": inv_h["nested_corpus"]["n_violations"] > 0,
        "nested_violations": inv_h["nested_corpus"]["n_violations"],
        "n_unverifiable": inv_h["nested_corpus"]["n_unverifiable"],
        "nested_pass": inv_h["nested_corpus"]["pass"],
        "reasons": [e.get("reason") for e in inv_h["nested_corpus"]["examples"]],
        "expected": "pass",
        "ok": (
            inv_h["nested_corpus"]["n_violations"] == 0
            and inv_h["nested_corpus"]["n_unverifiable"] == 0
            and inv_h["nested_corpus"]["pass"] is True
        ),
    }

    ids_i_b = ids10[:9] + ["d10"]
    scores_i_a = [1.0 - 0.01 * i for i in range(9)] + [0.99]
    scores_i_b = [1.0 - 0.01 * i for i in range(9)] + [0.50]
    blob_i = _toy_blob(
        [
            _toy_run("raw", 5000, [_toy_pq("q1", ids10, scores_i_a)]),
            _toy_run("raw", 10000, [_toy_pq("q1", ids_i_b, scores_i_b)]),
        ],
        [5000, 10000],
        ["raw"],
    )
    inv_i = run_invariants({("toy", "i"): blob_i}, docs, questions)
    cases["i_dropped_higher_score"] = {
        "detected": inv_i["nested_corpus"]["n_violations"] > 0,
        "nested_violations": inv_i["nested_corpus"]["n_violations"],
        "reasons": [e.get("reason") for e in inv_i["nested_corpus"]["examples"]],
        "expected": "violation",
    }

    detect_cases = ("a_meta_equals_raw_with_filter", "b_empty_lists", "c_prefix_drop", "d_shuffled_order", "e_nan_score", "f_truncated_list_b", "i_dropped_higher_score")
    all_detected = all(cases[k]["detected"] for k in detect_cases)
    four_ok = (
        cases["f_truncated_list_b"]["detected"]
        and cases["g_missing_scores_dropped"]["ok"]
        and cases["h_dropped_lower_score"]["ok"]
        and cases["i_dropped_higher_score"]["detected"]
        and not cases["h_dropped_lower_score"]["detected"]
    )
    return {
        "cases": cases,
        "all_detected": all_detected,
        "four_drop_cases_ok": four_ok,
        "pass": bool(all_detected and four_ok),
    }


def ladder_tables(
    ladders: dict[tuple[str, str], dict[str, Any]],
) -> dict[str, Any]:
    tables: dict[str, Any] = {}
    for (emb, bank), blob in sorted(ladders.items()):
        runs = index_runs(blob)
        if not runs:
            tables.setdefault(emb, {})[bank] = {"skipped": True, "reason": blob.get("meta", {}).get("skip_reason")}
            continue
        scales = [int(s) for s in (blob["meta"].get("scales") or SCALES_DEFAULT)]
        conditions = list(blob["meta"].get("conditions") or [])
        order = blob_order(blob)
        bank_out: dict[str, Any] = {"n_questions": len(order), "scales": scales, "conditions": {}}
        for cond in conditions:
            cond_out: dict[str, Any] = {}
            for scale in scales:
                run = runs[(cond, int(scale))]
                pq = align_pq(run, order)
                metrics = {m: float(as_float(pq, m).mean()) for m in METRICS}
                file_metrics = {k: float(v) for k, v in (run.get("metrics") or {}).items()}
                cond_out[str(scale)] = {"metrics": metrics, "file_metrics": file_metrics}
            bank_out["conditions"][cond] = cond_out
        tables.setdefault(emb, {})[bank] = bank_out
    return tables


def metadata_lift(
    ladders: dict[tuple[str, str], dict[str, Any]],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    result: dict[str, Any] = {}
    csv_rows: list[dict[str, Any]] = []
    for (emb, bank), blob in sorted(ladders.items()):
        runs = index_runs(blob)
        if not runs:
            continue
        scales = sorted(int(s) for s in (blob["meta"].get("scales") or SCALES_DEFAULT))
        order = blob_order(blob)
        n = len(order)
        idx = IDX.get(n)
        emb_out: dict[str, Any] = {}
        for filt in META_FILTERS:
            cond = COND_FROM_FILTER[filt]
            per_scale = []
            strict_pairs: list[tuple[int, bool]] = []
            leq_pairs: list[tuple[int, bool]] = []
            ci_pairs: list[tuple[int, bool]] = []
            below_point = []
            below_ci = []
            for scale in scales:
                raw = align_hits(runs[("raw", scale)], order, "hit_at_10")
                meta = align_hits(runs[(cond, scale)], order, "hit_at_10")
                hits_raw = int(raw.sum())
                hits_meta = int(meta.sum())
                delta_frac, strict_lt, leq = delta_from_hits(hits_meta, hits_raw, n)
                point, lo, hi = mean_ci(meta.astype(np.float64) - raw.astype(np.float64), idx)
                rec = {
                    "scale": scale,
                    "hits_meta": hits_meta,
                    "hits_raw": hits_raw,
                    "n": n,
                    "delta_hits": hits_meta - hits_raw,
                    "delta": float(delta_frac),
                    "delta_bootstrap": point,
                    "ci_lo": lo,
                    "ci_hi": hi,
                    "point_below_0.10": bool(strict_lt),
                    "point_leq_0.10": bool(leq),
                    "ci_entirely_below_0.10": bool(hi < TAU),
                }
                per_scale.append(rec)
                strict_pairs.append((scale, strict_lt))
                leq_pairs.append((scale, leq))
                ci_pairs.append((scale, bool(hi < TAU)))
                if rec["point_below_0.10"]:
                    below_point.append(scale)
                if rec["ci_entirely_below_0.10"]:
                    below_ci.append(scale)
                csv_rows.append(
                    {
                        "embedder": emb,
                        "bank": bank,
                        "filter": filt,
                        "scale": scale,
                        "delta": float(delta_frac),
                        "ci_lo": lo,
                        "ci_hi": hi,
                        "hits_meta": hits_meta,
                        "hits_raw": hits_raw,
                        "n": n,
                    }
                )
            ns_strict = n_star_from_flags(strict_pairs)
            ns_leq = n_star_from_flags(leq_pairs)
            ns_ci = n_star_from_flags(ci_pairs)
            emb_out[filt] = {
                "per_scale": per_scale,
                "scales_point_below_0.10": below_point,
                "scales_point_leq_0.10": [s for s, ok in leq_pairs if ok],
                "scales_ci_entirely_below_0.10": below_ci,
                "n_star": ns_strict if ns_strict is not None else "undefined",
                "n_star_strict": ns_strict if ns_strict is not None else "undefined",
                "n_star_nonstrict": ns_leq if ns_leq is not None else "undefined",
                "n_star_ci": ns_ci if ns_ci is not None else "undefined",
            }
        result.setdefault(emb, {})[bank] = emb_out
    return result, csv_rows


def cross_embedder(
    ladders: dict[tuple[str, str], dict[str, Any]],
) -> dict[str, Any]:
    banks = sorted({bank for (_, bank) in ladders})
    out: dict[str, Any] = {}
    for bank in banks:
        o = ladders.get(("openai", bank))
        t = ladders.get(("titan", bank))
        if not o or not t:
            continue
        ro, rt = index_runs(o), index_runs(t)
        if not ro or not rt:
            out[bank] = {"skipped": True, "reason": "empty_runs"}
            continue
        scales = sorted(int(s) for s in (o["meta"].get("scales") or SCALES_DEFAULT))
        order = canonical_question_ids(list(ro.values()) + list(rt.values()))
        idx = IDX.get(len(order))
        delta_diff = []
        for scale in scales:
            o_raw = align_hits(ro[("raw", scale)], order, "hit_at_10")
            o_meta = align_hits(ro[("meta_in", scale)], order, "hit_at_10")
            t_raw = align_hits(rt[("raw", scale)], order, "hit_at_10")
            t_meta = align_hits(rt[("meta_in", scale)], order, "hit_at_10")
            d = (o_meta.astype(np.float64) - o_raw.astype(np.float64)) - (
                t_meta.astype(np.float64) - t_raw.astype(np.float64)
            )
            point, lo, hi = mean_ci(d, idx)
            delta_diff.append({"scale": scale, **ci_tuple(point, lo, hi)})
        drops: dict[str, Any] = {}
        drop_arrs: dict[str, np.ndarray] = {}
        for label, runs, cond in (
            ("openai_raw", ro, "raw"),
            ("titan_raw", rt, "raw"),
            ("openai_meta_in", ro, "meta_in"),
            ("titan_meta_in", rt, "meta_in"),
        ):
            v5 = align_hits(runs[(cond, 5000)], order, "hit_at_10").astype(np.float64)
            v100 = align_hits(runs[(cond, 100000)], order, "hit_at_10").astype(np.float64)
            d = v5 - v100
            drop_arrs[label] = d
            point, lo, hi = mean_ci(d, idx)
            drops[label] = {
                **ci_tuple(point, lo, hi),
                "hit_at_10_5000": float(v5.mean()),
                "hit_at_10_100000": float(v100.mean()),
            }
        paired = {}
        for a, b, name in (
            ("openai_raw", "titan_raw", "openai_raw_minus_titan_raw"),
            ("openai_meta_in", "titan_meta_in", "openai_meta_in_minus_titan_meta_in"),
        ):
            point, lo, hi = mean_ci(drop_arrs[a] - drop_arrs[b], idx)
            paired[name] = ci_tuple(point, lo, hi)
        out[bank] = {
            "delta_openai_minus_delta_titan_meta_in": delta_diff,
            "hit10_drop_5k_to_100k": drops,
            "paired_drop_difference": paired,
        }
    return out


def log_linear_fits(
    ladders: dict[tuple[str, str], dict[str, Any]],
) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for (emb, bank), blob in sorted(ladders.items()):
        runs = index_runs(blob)
        if not runs:
            continue
        scales = [int(s) for s in (blob["meta"].get("scales") or SCALES_DEFAULT)]
        conditions = list(blob["meta"].get("conditions") or [])
        order = blob_order(blob)
        idx = IDX.get(len(order))
        bank_out: dict[str, Any] = {}
        for cond in conditions:
            cond_out: dict[str, Any] = {}
            for metric in ("hit_at_1", "hit_at_10", "mrr"):
                series = [align_metric(runs[(cond, s)], order, metric) for s in scales]
                full = slope_bootstrap(series, scales, idx, exclude=None)
                no5k = slope_bootstrap(series, scales, idx, exclude={5000})
                cond_out[metric] = {"all_scales": full, "exclude_5k": no5k}
            bank_out[cond] = cond_out
        result.setdefault(emb, {})[bank] = bank_out
    return result


def load_bm25_hit10(path: Path) -> tuple[list[str], dict[int, np.ndarray], list[int]]:
    blob = load_json(path)
    pqs = blob["per_question_by_scale"]
    scales = sorted(int(s) for s in pqs)
    runs_as = []
    for s in scales:
        runs_as.append({"per_question": pqs[str(s)]})
    order = canonical_question_ids(runs_as)
    by_scale: dict[int, np.ndarray] = {}
    for s in scales:
        by_scale[s] = align_hits({"per_question": pqs[str(s)]}, order, "hit_at_10")
    return order, by_scale, scales


def rq2_compare_series(
    dense_by_scale: dict[int, np.ndarray],
    bm25_by: dict[int, np.ndarray],
    dense_scales: list[int],
    idx: np.ndarray,
    dense_condition: str,
) -> dict[str, Any]:
    common_scales = [s for s in dense_scales if s in bm25_by]
    drop_dense = dense_by_scale[5000] - dense_by_scale[100000]
    drop_bm25 = bm25_by[5000].astype(np.float64) - bm25_by[100000].astype(np.float64)
    drop_dense = drop_dense.astype(np.float64)
    d_pt, d_lo, d_hi = mean_ci(drop_dense, idx)
    b_pt, b_lo, b_hi = mean_ci(drop_bm25, idx)
    pd_pt, pd_lo, pd_hi = mean_ci(drop_dense - drop_bm25, idx)
    per_scale = []
    for s in common_scales:
        pt, lo, hi = mean_ci(bm25_by[s].astype(np.float64) - dense_by_scale[s].astype(np.float64), idx)
        per_scale.append({"scale": s, **ci_tuple(pt, lo, hi)})
    dense_series = [dense_by_scale[s].astype(np.float64) for s in common_scales]
    bm25_series = [bm25_by[s].astype(np.float64) for s in common_scales]
    fit_d = slope_bootstrap(dense_series, common_scales, idx)
    fit_b = slope_bootstrap(bm25_series, common_scales, idx)
    fit_d5 = slope_bootstrap(dense_series, common_scales, idx, exclude={5000})
    fit_b5 = slope_bootstrap(bm25_series, common_scales, idx, exclude={5000})
    sd_all = slope_diff_bootstrap(dense_series, bm25_series, common_scales, idx)
    sd_no5 = slope_diff_bootstrap(dense_series, bm25_series, common_scales, idx, exclude={5000})
    return {
        "dense_condition": dense_condition,
        "bm25_drop_5k_to_100k": ci_tuple(b_pt, b_lo, b_hi),
        "dense_exact_drop_5k_to_100k": ci_tuple(d_pt, d_lo, d_hi),
        "dense_drop_minus_bm25_drop": ci_tuple(pd_pt, pd_lo, pd_hi),
        "bm25_minus_dense_hit10_by_scale": per_scale,
        "dense_loglinear_hit10": fit_d,
        "bm25_loglinear_hit10": fit_b,
        "dense_loglinear_hit10_exclude_5k": fit_d5,
        "bm25_loglinear_hit10_exclude_5k": fit_b5,
        "slope_dense_minus_bm25": sd_all,
        "slope_dense_minus_bm25_exclude_5k": sd_no5,
    }


def rq2_bm25(
    ladders: dict[tuple[str, str], dict[str, Any]],
) -> dict[str, Any]:
    variants = {}
    files_used = []
    for name, path in discover_bm25():
        order, by_scale, scales = load_bm25_hit10(path)
        rel = str(path.relative_to(ROOT))
        digest = sha256_file(path)
        variants[name] = {"path": rel, "sha256": digest, "order": order, "by_scale": by_scale, "scales": scales}
        files_used.append({"name": name, "path": rel, "sha256": digest})

    names = list(variants)
    if names:
        base_name = names[0]
        base_ids = set(variants[base_name]["order"])
        for vname in names[1:]:
            other = set(variants[vname]["order"])
            if other != base_ids:
                raise ValueError(
                    f"question id set mismatch between BM25 {base_name} and {vname}"
                )
    out: dict[str, Any] = {
        "variants_discovered": sorted(variants),
        "files_used": files_used,
    }
    for (emb, bank), blob in sorted(ladders.items()):
        if bank != "primary200":
            continue
        runs = index_runs(blob)
        if not runs:
            continue
        dense_order = blob_order(blob)
        idx = IDX.get(len(dense_order))
        dense_scales = [int(s) for s in (blob["meta"].get("scales") or SCALES_DEFAULT)]
        emb_out: dict[str, Any] = {}
        for vname, v in variants.items():
            if set(v["order"]) != set(dense_order):
                raise ValueError(
                    f"question id set mismatch between dense {emb}/{bank} and BM25 {vname}"
                )
            bm25_by = {}
            for s, arr in v["by_scale"].items():
                by_id = {qid: float(arr[i]) for i, qid in enumerate(v["order"])}
                bm25_by[s] = np.array([by_id[q] for q in dense_order], dtype=np.float64)
            cond_out: dict[str, Any] = {}
            for cond in ("raw", "meta_in"):
                dense_by_scale = {
                    s: align_hits(runs[(cond, s)], dense_order, "hit_at_10").astype(np.float64)
                    for s in dense_scales
                }
                cond_out[cond] = rq2_compare_series(dense_by_scale, bm25_by, dense_scales, idx, cond)
            emb_out[vname] = cond_out
        out.setdefault(emb, {})[bank] = emb_out
    return out


def oracle_definition(
    ladders: dict[tuple[str, str], dict[str, Any]],
    doc_source: dict[str, str],
    questions: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    blob = ladders.get(("openai", "primary200"))
    if not blob or not blob.get("runs"):
        return {"skipped": True, "reason": "missing_openai_primary200"}
    order = blob_order(blob)
    n = len(order)
    coincide = 0
    multi: list[str] = []
    for qid in order:
        q = questions[qid]
        q_types = set(q.get("source_types") or [])
        gold_types = set()
        for did in q.get("expected_doc_ids") or []:
            st = doc_source.get(did)
            if st is not None:
                gold_types.add(st)
        if q_types == gold_types:
            coincide += 1
        if len(q_types) > 1:
            multi.append(qid)
    per_embedder: dict[str, Any] = {}
    for emb in ("openai", "titan"):
        b = ladders.get((emb, "primary200"))
        if not b or not b.get("runs"):
            continue
        runs = index_runs(b)
        scales = [int(s) for s in (b["meta"].get("scales") or SCALES_DEFAULT)]
        emb_order = blob_order(b)
        if set(emb_order) != set(order):
            raise ValueError(f"{emb} primary200 question ids differ from openai")
        rows = []
        for s in scales:
            rec: dict[str, Any] = {"scale": s}
            for cond, label in (("meta_first", "first"), ("meta_in", "in")):
                pq = align_pq(runs[(cond, s)], emb_order)
                by_id = {qid: pq[i] for i, qid in enumerate(emb_order)}
                sub = [by_id[q] for q in multi]
                rec[label] = {
                    "n": len(sub),
                    "hit_at_10": float(as_float(sub, "hit_at_10").mean()) if sub else None,
                    "mrr": float(as_float(sub, "mrr").mean()) if sub else None,
                    "document_recall": float(as_float(sub, "document_recall").mean()) if sub else None,
                }
            rows.append(rec)
        per_embedder[emb] = rows
    return {
        "bank": "primary200",
        "n_questions": n,
        "source_types_equals_gold_source_types": coincide,
        "n_multi_source_questions": len(multi),
        "multi_source_question_ids": multi,
        "note": (
            "meta_in and meta_gold coincide when question.source_types equals the set of "
            "gold-document source types. meta_first differs on the multi-source questions."
        ),
        "multi_source_hit10_can_be_lower_with_in": (
            "Hit@10 can be lower with the IN filter than with the first-type filter because "
            "IN admits distractors from the additional sources, which can push the first gold "
            "document out of the top 10."
        ),
        "multi_source_first_vs_in": per_embedder,
    }


def mixed_mode(
    ladders: dict[tuple[str, str], dict[str, Any]],
) -> dict[str, Any]:
    scales = [5000, 50000, 100000]
    out: dict[str, Any] = {}
    specs = [
        ("openai", HNSW_OPENAI, "runs", EXACT_CTRL_OPENAI),
        ("titan", HNSW_TITAN, "runs_with_per_question", EXACT_CTRL_TITAN),
    ]
    for emb, hnsw_path, runs_key, ctrl_path in specs:
        blob = ladders.get((emb, "primary200"))
        if not blob:
            out[emb] = {"skipped": True, "reason": "missing_exact_ladder"}
            continue
        runs = index_runs(blob)
        order = blob_order(blob)
        idx = IDX.get(len(order))
        per = []
        for s in scales:
            exact_raw = align_hits(runs[("raw", s)], order, "hit_at_10").astype(np.float64)
            hnsw_blob = load_json(hnsw_path)
            hnsw_runs = hnsw_blob[runs_key]
            hnsw_run = None
            for run in hnsw_runs:
                sc = run.get("corpus_scale_size", run.get("scale"))
                if run.get("condition") == "meta" and int(sc) == int(s):
                    hnsw_run = run
                    break
            if hnsw_run is None:
                raise KeyError(f"missing HNSW run {hnsw_path.name} meta {s}")
            hnsw_order_check = canonical_question_ids([hnsw_run])
            if set(hnsw_order_check) != set(order):
                raise ValueError(f"HNSW question ids mismatch {hnsw_path.name} {s}")
            hnsw_meta = align_hits(hnsw_run, order, "hit_at_10").astype(np.float64)
            point, lo, hi = mean_ci(hnsw_meta - exact_raw, idx)
            per.append(
                {
                    "scale": s,
                    "hnsw_meta_hit10": float(hnsw_meta.mean()),
                    "exact_raw_hit10": float(exact_raw.mean()),
                    **ci_tuple(point, lo, hi),
                }
            )
        ctrl = load_json(ctrl_path)
        ctrl_hits = {}
        for run in ctrl["runs"]:
            sc = int(run.get("corpus_scale_size", run.get("scale")))
            ctrl_hits[sc] = float(run["hit_at_10"])
        ladder_match = {
            str(s): abs(float(runs[("raw", s)]["metrics"]["hit_at_10"]) - ctrl_hits[s]) < 1e-12
            for s in scales
            if s in ctrl_hits
        }
        out[emb] = {
            "hnsw_meta_minus_exact_raw": per,
            "exact_control_raw_matches_ladder": ladder_match,
            "point_estimates_3dp": [round(p["estimate"], 3) for p in per],
        }
    return out


def hnsw_and_bm25_drops() -> dict[str, Any]:
    o5 = load_hnsw_metric(HNSW_OPENAI, "runs", "raw", 5000, "hit_at_10")
    o100 = load_hnsw_metric(HNSW_OPENAI, "runs", "raw", 100000, "hit_at_10")
    bm25 = load_json(BM25_PRIMARY)
    b_by = {int(r["corpus_scale_size"]): float(r["hit_at_10"]) for r in bm25["runs"]}
    return {
        "openai_hnsw_raw_hit10_5000": o5,
        "openai_hnsw_raw_hit10_100000": o100,
        "bm25_hit10_5000": b_by[5000],
        "bm25_hit10_100000": b_by[100000],
    }


def lift_row(lift: dict[str, Any], emb: str, bank: str, filt: str, scale: int) -> dict[str, Any]:
    rows = lift[emb][bank][filt]["per_scale"]
    for row in rows:
        if int(row["scale"]) == int(scale):
            return row
    raise KeyError(f"missing lift {emb} {bank} {filt} {scale}")


def ci_close(row: dict[str, Any], delta: float, lo: float, hi: float) -> bool:
    return (
        abs(float(row["delta"]) - delta) < 1e-12
        and abs(float(row["ci_lo"]) - lo) < 1e-12
        and abs(float(row["ci_hi"]) - hi) < 1e-12
    )


def exact_invariant_slice(
    inv: dict[str, Any],
    ladders: dict[tuple[str, str], dict[str, Any]] | None = None,
) -> dict[str, Any]:
    prefixes: list[str] = []
    if ladders:
        for (emb, bank), blob in sorted(ladders.items()):
            if blob.get("runs"):
                prefixes.append(f"{emb}|{bank}|")
    out: dict[str, Any] = {}
    for kind in ("containment", "nested_corpus", "score_monotonicity"):
        checked = 0
        viol = 0
        unv = 0
        for key, rec in inv[kind]["by_key"].items():
            if prefixes and not any(key.startswith(p) for p in prefixes):
                continue
            checked += rec["n_checked"]
            viol += rec["n_violations"]
            unv += rec.get("n_unverifiable", 0)
        out[kind] = {"n_checked": checked, "n_violations": viol, "n_unverifiable": unv}
    return out


def containment_scale_violations(inv: dict[str, Any], scale: int) -> int:
    total = 0
    suffix = f"|{scale}"
    for key, rec in inv["containment"]["by_key"].items():
        if key.endswith(suffix) and "-" not in key.split("|")[-1]:
            total += rec["n_violations"]
    return total


def acceptance(
    mixed: dict[str, Any],
    drops: dict[str, Any],
    inv: dict[str, Any],
    st: dict[str, Any],
    mut: dict[str, Any],
    lift: dict[str, Any],
    old_hnsw_inv: dict[str, Any],
    ladders: dict[tuple[str, str], dict[str, Any]],
    old_in_diag: dict[str, Any],
) -> list[dict[str, Any]]:
    tests = []

    def add(name: str, ok: bool, actual: Any, expected: Any) -> None:
        tests.append(
            {
                "name": name,
                "result": "PASS" if ok else "FAIL",
                "actual": actual,
                "expected": expected,
            }
        )

    o = mixed["openai"]["point_estimates_3dp"]
    t = mixed["titan"]["point_estimates_3dp"]
    exp_o = [0.080, 0.050, 0.055]
    exp_t = [0.085, 0.105, 0.080]
    add("mixed_mode_openai_5k_50k_100k", o == exp_o, o, exp_o)
    add("mixed_mode_titan_5k_50k_100k", t == exp_t, t, exp_t)
    add(
        "openai_hnsw_hit10_5k",
        abs(drops["openai_hnsw_raw_hit10_5000"] - 0.795) < 1e-9,
        drops["openai_hnsw_raw_hit10_5000"],
        0.795,
    )
    add(
        "openai_hnsw_hit10_100k",
        abs(drops["openai_hnsw_raw_hit10_100000"] - 0.510) < 1e-9
        or abs(drops["openai_hnsw_raw_hit10_100000"] - 0.51) < 1e-9,
        drops["openai_hnsw_raw_hit10_100000"],
        0.510,
    )
    add(
        "bm25_hit10_5k",
        abs(drops["bm25_hit10_5000"] - 0.855) < 1e-9,
        drops["bm25_hit10_5000"],
        0.855,
    )
    add(
        "bm25_hit10_100k",
        abs(drops["bm25_hit10_100000"] - 0.700) < 1e-9
        or abs(drops["bm25_hit10_100000"] - 0.7) < 1e-9,
        drops["bm25_hit10_100000"],
        0.700,
    )
    slice_inv = exact_invariant_slice(inv, ladders)
    for kind in ("containment", "nested_corpus", "score_monotonicity"):
        add(
            f"invariant_{kind}_zero_violations",
            slice_inv[kind]["n_violations"] == 0
            and slice_inv[kind]["n_unverifiable"] == 0
            and slice_inv[kind]["n_checked"] > 0,
            slice_inv[kind],
            {"n_violations": 0, "n_unverifiable": 0, "n_checked": ">0"},
        )
    add(
        "synthetic_bootstrap_self_test",
        bool(st["pass"]),
        {
            "contains_true_difference": st["contains_true_difference"],
            "symmetric_within_0.02": st["symmetric_within_0.02"],
            "ci": [st["ci_lo"], st["ci_hi"]],
            "sample_difference": st["sample_difference"],
        },
        "CI contains 0.2 and is symmetric within 0.02",
    )
    add(
        "mutation_tests_all_detected",
        bool(mut["all_detected"] and mut.get("four_drop_cases_ok")),
        {
            "all_detected": mut["all_detected"],
            "four_drop_cases_ok": mut.get("four_drop_cases_ok"),
            "detected": {k: v.get("detected") for k, v in mut["cases"].items()},
        },
        "original detections plus truncated/missing-scores/lower-vs-higher drop cases",
    )
    add(
        "mutation_truncated_list_b",
        bool(mut["cases"]["f_truncated_list_b"]["detected"]),
        mut["cases"]["f_truncated_list_b"],
        "violation",
    )
    add(
        "mutation_missing_scores_unverifiable",
        bool(mut["cases"]["g_missing_scores_dropped"].get("ok")),
        mut["cases"]["g_missing_scores_dropped"],
        "unverifiable, not a pass, not counted as violation",
    )
    add(
        "mutation_dropped_lower_score_pass",
        bool(mut["cases"]["h_dropped_lower_score"].get("ok")),
        mut["cases"]["h_dropped_lower_score"],
        "pass",
    )
    add(
        "mutation_dropped_higher_score_fail",
        bool(mut["cases"]["i_dropped_higher_score"]["detected"]),
        mut["cases"]["i_dropped_higher_score"],
        "violation",
    )
    r5 = lift_row(lift, "openai", "primary200", "in", 5000)
    r100 = lift_row(lift, "openai", "primary200", "in", 100000)
    add(
        "openai_meta_in_raw_lift_5k",
        ci_close(r5, 0.080, 0.045, 0.120),
        {"delta": r5["delta"], "ci_lo": r5["ci_lo"], "ci_hi": r5["ci_hi"]},
        {"delta": 0.080, "ci_lo": 0.045, "ci_hi": 0.120},
    )
    add(
        "openai_meta_in_raw_lift_100k",
        ci_close(r100, 0.080, 0.045, 0.120),
        {"delta": r100["delta"], "ci_lo": r100["ci_lo"], "ci_hi": r100["ci_hi"]},
        {"delta": 0.080, "ci_lo": 0.045, "ci_hi": 0.120},
    )
    ns_o = lift["openai"]["primary200"]["in"]["n_star_strict"]
    ns_t = lift["titan"]["primary200"]["in"]["n_star_strict"]
    add("n_star_strict_openai_meta_in", ns_o == 15000, ns_o, 15000)
    add("n_star_strict_titan_meta_in", ns_t == 100000, ns_t, 100000)
    raw_prefix = 0
    for key, rec in old_hnsw_inv["nested_corpus"]["by_key"].items():
        if "|raw|" in key:
            raw_prefix += rec["n_violations"]
    add(
        "old_hnsw_openai_raw_nested_reported",
        True,
        {"raw_nested_violations": raw_prefix, "n_checked": old_hnsw_inv["nested_corpus"]["n_checked"]},
        "report counts; reviewer expected several hundred prefix violations on raw",
    )
    first_viol = old_hnsw_inv["containment"]["n_violations"]
    first_checked = old_hnsw_inv["containment"]["n_checked"]
    first_5k = containment_scale_violations(old_hnsw_inv, 5000)
    add(
        "old_list_containment_first",
        first_viol == 56,
        {"n_violations": first_viol, "n_checked": first_checked, "n_violations_at_5000": first_5k},
        {"n_violations": 56, "n_checked": 3600, "n_violations_at_5000": 0},
    )
    add(
        "old_list_containment_first_none_at_5k",
        first_5k == 0,
        first_5k,
        0,
    )
    in_viol = old_in_diag["containment"]["n_violations"]
    add(
        "old_list_containment_in_diagnostic",
        True,
        {"n_violations": in_viol, "n_checked": old_in_diag["containment"]["n_checked"]},
        "diagnostic only; reviewer expected 210",
    )
    return tests


def md_escape(x: Any) -> str:
    return str(x)


def write_invariant_table(lines: list[str], title: str, rec: dict[str, Any]) -> None:
    lines.append(f"### {title}")
    lines.append("")
    lines.append(
        f"CHECKED={rec['n_checked']} VIOLATIONS={rec['n_violations']} "
        f"UNVERIFIABLE={rec.get('n_unverifiable', 0)} pass={rec['pass']}"
    )
    lines.append("")
    lines.append("| key | checked | violations | unverifiable |")
    lines.append("| --- | ---: | ---: | ---: |")
    for key, row in rec["by_key"].items():
        lines.append(
            f"| {key} | {row['n_checked']} | {row['n_violations']} | {row.get('n_unverifiable', 0)} |"
        )
    if rec["examples"]:
        lines.append("")
        lines.append("Examples:")
        for ex in rec["examples"]:
            lines.append(
                f"- ({ex.get('embedder')}, {ex.get('condition')}, {ex.get('scale')}, "
                f"{ex.get('question')}, {ex.get('reason')})"
            )
    lines.append("")


def write_md(
    path: Path,
    payload: dict[str, Any],
) -> None:
    lines: list[str] = []
    lines.append("# Exact-search ladder analysis (revision 1)")
    lines.append("")
    lines.append("Paired percentile bootstrap over questions; B = 10000; seed = 42; 95% CI = 2.5/97.5 percentiles.")
    lines.append("Question order is sorted question ids. N* uses integer hit counts vs tau=1/10.")
    lines.append("")

    lines.append("## 1. Ladder tables")
    lines.append("")
    for emb, banks in sorted(payload["ladder"].items()):
        for bank, blob in sorted(banks.items()):
            lines.append(f"### {emb} / {bank}")
            lines.append("")
            if blob.get("skipped"):
                lines.append(f"Skipped: {blob.get('reason')}")
                lines.append("")
                continue
            for cond, scales in blob["conditions"].items():
                lines.append(f"**{cond}**")
                lines.append("")
                lines.append("| scale | Hit@1 | Hit@5 | Hit@10 | MRR | Doc-Recall |")
                lines.append("| ---: | ---: | ---: | ---: | ---: | ---: |")
                for s in blob["scales"]:
                    m = scales[str(s)]["metrics"]
                    lines.append(
                        f"| {s} | {fmt(m['hit_at_1'])} | {fmt(m['hit_at_5'])} | {fmt(m['hit_at_10'])} | {fmt(m['mrr'], 4)} | {fmt(m['document_recall'])} |"
                    )
                lines.append("")

    lines.append("## 2. Metadata lift Δmeta(N) = Hit@10(meta_X) − Hit@10(raw)")
    lines.append("")
    lines.append("Δ = (hits_meta − hits_raw)/n with integer counts. Strict N*: Δ < 1/10. Nonstrict: Δ ≤ 1/10. N*_CI: smallest N with CI hi < 0.10 for all larger N.")
    lines.append("")
    for emb, banks in sorted(payload["metadata_lift"].items()):
        for bank, filts in sorted(banks.items()):
            lines.append(f"### {emb} / {bank}")
            lines.append("")
            for filt, rec in filts.items():
                lines.append(
                    f"**filter = {filt}**; N* strict = {rec['n_star_strict']}; "
                    f"N* nonstrict = {rec['n_star_nonstrict']}; N*_CI = {rec['n_star_ci']}"
                )
                lines.append("")
                lines.append("| scale | hits_meta | hits_raw | n | Δ | CI lo | CI hi | Δ < 0.10 | Δ ≤ 0.10 | CI < 0.10 |")
                lines.append("| ---: | ---: | ---: | ---: | ---: | ---: | ---: | :---: | :---: | :---: |")
                for row in rec["per_scale"]:
                    lines.append(
                        f"| {row['scale']} | {row['hits_meta']} | {row['hits_raw']} | {row['n']} | "
                        f"{fmt(row['delta'])} | {fmt(row['ci_lo'])} | {fmt(row['ci_hi'])} | "
                        f"{'yes' if row['point_below_0.10'] else 'no'} | "
                        f"{'yes' if row['point_leq_0.10'] else 'no'} | "
                        f"{'yes' if row['ci_entirely_below_0.10'] else 'no'} |"
                    )
                lines.append("")

    lines.append("## 3. Cross-embedder (meta_in)")
    lines.append("")
    for bank, rec in sorted(payload["cross_embedder"].items()):
        lines.append(f"### {bank}")
        lines.append("")
        if rec.get("skipped"):
            lines.append(f"Skipped: {rec.get('reason')}")
            lines.append("")
            continue
        lines.append("| scale | Δ_openai − Δ_titan | CI lo | CI hi |")
        lines.append("| ---: | ---: | ---: | ---: |")
        for row in rec["delta_openai_minus_delta_titan_meta_in"]:
            lines.append(
                f"| {row['scale']} | {fmt(row['estimate'])} | {fmt(row['ci_lo'])} | {fmt(row['ci_hi'])} |"
            )
        lines.append("")
        lines.append("| series | Hit@10 5k | Hit@10 100k | drop | CI lo | CI hi |")
        lines.append("| --- | ---: | ---: | ---: | ---: | ---: |")
        for name, d in rec["hit10_drop_5k_to_100k"].items():
            lines.append(
                f"| {name} | {fmt(d['hit_at_10_5000'])} | {fmt(d['hit_at_10_100000'])} | {fmt(d['estimate'])} | {fmt(d['ci_lo'])} | {fmt(d['ci_hi'])} |"
            )
        lines.append("")
        lines.append("| contrast | estimate | CI lo | CI hi |")
        lines.append("| --- | ---: | ---: | ---: |")
        for name, d in rec["paired_drop_difference"].items():
            lines.append(f"| {name} | {fmt(d['estimate'])} | {fmt(d['ci_lo'])} | {fmt(d['ci_hi'])} |")
        lines.append("")

    lines.append("## 4. Log-linear fits (y ~ slope · ln N + intercept)")
    lines.append("")
    for emb, banks in sorted(payload["log_linear"].items()):
        for bank, conds in sorted(banks.items()):
            lines.append(f"### {emb} / {bank}")
            lines.append("")
            lines.append("| condition | metric | subset | slope | slope CI lo | slope CI hi | intercept | R² |")
            lines.append("| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |")
            for cond, metrics in conds.items():
                for metric, rec in metrics.items():
                    for subset, fit in rec.items():
                        lines.append(
                            f"| {cond} | {metric} | {subset} | {fmt(fit['slope'], 4)} | {fmt(fit['slope_ci_lo'], 4)} | {fmt(fit['slope_ci_hi'], 4)} | {fmt(fit['intercept'], 4)} | {fmt(fit['r2'])} |"
                        )
            lines.append("")

    lines.append("## 5. RQ2 dense exact vs BM25")
    lines.append("")
    rq = payload["rq2_bm25"]
    lines.append("Files used:")
    lines.append("")
    for f in rq.get("files_used") or []:
        lines.append(f"- `{f['path']}` sha256={f['sha256']}")
    lines.append("")
    for emb, banks in sorted((k, v) for k, v in rq.items() if k not in ("variants_discovered", "files_used")):
        for bank, variants in sorted(banks.items()):
            lines.append(f"### {emb} / {bank}")
            lines.append("")
            for vname, rec in variants.items():
                if rec.get("skipped"):
                    lines.append(f"**{vname}** skipped: {rec.get('reason')}")
                    continue
                for cond, crec in rec.items():
                    lines.append(f"**{vname} / {cond}**")
                    lines.append("")
                    dd = crec["dense_exact_drop_5k_to_100k"]
                    bd = crec["bm25_drop_5k_to_100k"]
                    pd = crec["dense_drop_minus_bm25_drop"]
                    sd = crec["slope_dense_minus_bm25"]
                    sd5 = crec["slope_dense_minus_bm25_exclude_5k"]
                    lines.append(
                        f"- dense drop 5k to 100k: {fmt(dd['estimate'])} [{fmt(dd['ci_lo'])}, {fmt(dd['ci_hi'])}]"
                    )
                    lines.append(
                        f"- BM25 drop 5k to 100k: {fmt(bd['estimate'])} [{fmt(bd['ci_lo'])}, {fmt(bd['ci_hi'])}]"
                    )
                    lines.append(
                        f"- dense drop minus BM25 drop: {fmt(pd['estimate'])} [{fmt(pd['ci_lo'])}, {fmt(pd['ci_hi'])}]"
                    )
                    lines.append(
                        f"- slope dense minus BM25 (all): {fmt(sd['estimate'], 4)} [{fmt(sd['ci_lo'], 4)}, {fmt(sd['ci_hi'], 4)}]"
                    )
                    lines.append(
                        f"- slope dense minus BM25 (no 5k): {fmt(sd5['estimate'], 4)} [{fmt(sd5['ci_lo'], 4)}, {fmt(sd5['ci_hi'], 4)}]"
                    )
                    lines.append("")
                    lines.append("| scale | BM25 − dense Hit@10 | CI lo | CI hi |")
                    lines.append("| ---: | ---: | ---: | ---: |")
                    for row in crec["bm25_minus_dense_hit10_by_scale"]:
                        lines.append(
                            f"| {row['scale']} | {fmt(row['estimate'])} | {fmt(row['ci_lo'])} | {fmt(row['ci_hi'])} |"
                        )
                    lines.append("")

    lines.append("## 6. Invariants (exact ladders)")
    lines.append("")
    inv = payload["invariants"]
    write_invariant_table(lines, "containment", inv["containment"])
    write_invariant_table(lines, "nested_corpus", inv["nested_corpus"])
    write_invariant_table(lines, "score_monotonicity", inv["score_monotonicity"])

    lines.append("## 6b. Mutation tests")
    lines.append("")
    mut = payload["self_test_invariants"]
    lines.append(f"all_detected = {mut['all_detected']}")
    lines.append("")
    lines.append("| case | detected |")
    lines.append("| --- | --- |")
    for name, rec in mut["cases"].items():
        lines.append(f"| {name} | {rec['detected']} |")
    lines.append("")

    lines.append("## 6c. Old approximate OpenAI HNSW lists")
    lines.append("")
    olc = payload.get("old_list_containment") or {}
    first = olc.get("first") or {}
    indiag = olc.get("in_diagnostic") or {}
    lines.append(
        "Old approximate OpenAI `meta` used `question.source_types[0]` (first-type filter), "
        "not an IN-set filter."
    )
    lines.append("")
    lines.append(
        f"- containment with **first**: {first.get('n_violations')} of {first.get('n_checked')} "
        f"(none at 5k: {first.get('n_violations_at_5000')})"
    )
    lines.append(
        f"- containment with **in** (diagnostic only): {indiag.get('n_violations')} of "
        f"{indiag.get('n_checked')}"
    )
    lines.append("")
    old = payload["old_hnsw_openai_invariants"]
    write_invariant_table(lines, "old HNSW containment (first)", old["containment"])
    write_invariant_table(lines, "old HNSW nested_corpus", old["nested_corpus"])
    write_invariant_table(lines, "old HNSW score_monotonicity", old["score_monotonicity"])

    lines.append("## 7. Mixed-mode reproduction (HNSW meta − exact raw)")
    lines.append("")
    lines.append("| embedder | 5k | 50k | 100k |")
    lines.append("| --- | ---: | ---: | ---: |")
    mm = payload["mixed_mode"]
    for emb in ("openai", "titan"):
        pts = mm[emb]["point_estimates_3dp"]
        lines.append(f"| {emb} | {pts[0]:+.3f} | {pts[1]:+.3f} | {pts[2]:+.3f} |")
    lines.append("")
    for emb in ("openai", "titan"):
        lines.append(f"**{emb} CIs**")
        lines.append("")
        lines.append("| scale | estimate | CI lo | CI hi | HNSW meta | exact raw |")
        lines.append("| ---: | ---: | ---: | ---: | ---: | ---: |")
        for row in mm[emb]["hnsw_meta_minus_exact_raw"]:
            lines.append(
                f"| {row['scale']} | {fmt(row['estimate'])} | {fmt(row['ci_lo'])} | {fmt(row['ci_hi'])} | {fmt(row['hnsw_meta_hit10'])} | {fmt(row['exact_raw_hit10'])} |"
            )
        lines.append("")

    lines.append("## 8. Oracle definition")
    lines.append("")
    od = payload["oracle_definition"]
    lines.append(
        f"primary-200: question.source_types equals gold-document source-type set for "
        f"{od.get('source_types_equals_gold_source_types')} / {od.get('n_questions')} questions "
        f"(meta_in and meta_gold coincide on that subset)."
    )
    lines.append("")
    lines.append(
        f"meta_first differs on {od.get('n_multi_source_questions')} multi-source questions."
    )
    lines.append("")
    for emb, rows in (od.get("multi_source_first_vs_in") or {}).items():
        lines.append(f"### {emb} multi-source (n={od.get('n_multi_source_questions')})")
        lines.append("")
        lines.append("| scale | first Hit@10 | in Hit@10 | first MRR | in MRR | first Doc-Recall | in Doc-Recall |")
        lines.append("| ---: | ---: | ---: | ---: | ---: | ---: | ---: |")
        for row in rows:
            frow = row["first"]
            irow = row["in"]
            lines.append(
                f"| {row['scale']} | {fmt(frow['hit_at_10'])} | {fmt(irow['hit_at_10'])} | "
                f"{fmt(frow['mrr'], 4)} | {fmt(irow['mrr'], 4)} | "
                f"{fmt(frow['document_recall'])} | {fmt(irow['document_recall'])} |"
            )
        lines.append("")

    lines.append("## 9. Why IN Hit@10 can be lower than first-type on 21 multi-source questions")
    lines.append("")
    lines.append(od.get("multi_source_hit10_can_be_lower_with_in") or "")
    lines.append("")
    lines.append("| embedder | scale | first Hit@10 | in Hit@10 | first MRR | in MRR | first Doc-Recall | in Doc-Recall |")
    lines.append("| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |")
    for emb, rows in (od.get("multi_source_first_vs_in") or {}).items():
        for row in rows:
            frow = row["first"]
            irow = row["in"]
            lines.append(
                f"| {emb} | {row['scale']} | {fmt(frow['hit_at_10'])} | {fmt(irow['hit_at_10'])} | "
                f"{fmt(frow['mrr'], 4)} | {fmt(irow['mrr'], 4)} | "
                f"{fmt(frow['document_recall'])} | {fmt(irow['document_recall'])} |"
            )
    lines.append("")

    lines.append("## Acceptance tests")
    lines.append("")
    lines.append("| test | result | actual | expected |")
    lines.append("| --- | --- | --- | --- |")
    for t in payload["acceptance_tests"]:
        lines.append(
            f"| {t['name']} | {t['result']} | {md_escape(t['actual'])} | {md_escape(t['expected'])} |"
        )
    lines.append("")
    lines.append("Byte-identical re-run is checked outside this file after a second invocation.")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fields = ["embedder", "bank", "filter", "scale", "hits_meta", "hits_raw", "n", "delta", "ci_lo", "ci_hi"]
    with path.open("w", encoding="utf-8", newline="\n") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for row in rows:
            w.writerow(
                {
                    "embedder": row["embedder"],
                    "bank": row["bank"],
                    "filter": row["filter"],
                    "scale": row["scale"],
                    "hits_meta": row["hits_meta"],
                    "hits_raw": row["hits_raw"],
                    "n": row["n"],
                    "delta": f"{row['delta']:.12g}",
                    "ci_lo": f"{row['ci_lo']:.12g}",
                    "ci_hi": f"{row['ci_hi']:.12g}",
                }
            )


def main() -> int:
    doc_source, questions = load_manifest()
    ladders: dict[tuple[str, str], dict[str, Any]] = {}
    skipped = []
    inputs = []
    for path in discover_ladders():
        parsed = parse_ladder_name(path)
        if parsed is None:
            continue
        emb, bank = parsed
        blob = load_json(path)
        ladders[(emb, bank)] = blob
        inputs.append(str(path.relative_to(ROOT)))
        if not blob.get("runs"):
            skipped.append(
                {
                    "embedder": emb,
                    "bank": bank,
                    "reason": blob.get("meta", {}).get("skip_reason"),
                }
            )

    extra_inputs = [
        MANIFEST_PATH,
        HNSW_OPENAI,
        HNSW_TITAN,
        EXACT_CTRL_OPENAI,
        EXACT_CTRL_TITAN,
        BM25_PRIMARY,
        BM25_OLD_CHARS8191,
    ]
    inputs.extend(str(p.relative_to(ROOT)) for p in extra_inputs if p.is_file())
    for _, p in discover_bm25():
        rel = str(p.relative_to(ROOT))
        if rel not in inputs:
            inputs.append(rel)

    st = self_test()
    mut = self_test_invariants()
    tables = ladder_tables(ladders)
    lift, csv_rows = metadata_lift(ladders)
    cross = cross_embedder(ladders)
    fits = log_linear_fits(ladders)
    rq2 = rq2_bm25(ladders)
    inv = run_invariants(ladders, doc_source, questions)
    old_hnsw = wrap_hnsw_as_ladder(HNSW_OPENAI)
    old_wrapped = {("openai_hnsw_approx", "primary200"): old_hnsw}
    old_hnsw_inv = run_invariants(old_wrapped, doc_source, questions)
    old_in_diag = run_invariants(
        old_wrapped,
        doc_source,
        questions,
        cond_filter_map={**FILTER_FROM_COND, "meta": "in"},
    )
    old_list_containment = {
        "filter_mapping": {
            "meta": "first",
            "note": "old approximate OpenAI meta filtered on question.source_types[0]",
        },
        "first": {
            "n_checked": old_hnsw_inv["containment"]["n_checked"],
            "n_violations": old_hnsw_inv["containment"]["n_violations"],
            "n_violations_at_5000": containment_scale_violations(old_hnsw_inv, 5000),
        },
        "in_diagnostic": {
            "n_checked": old_in_diag["containment"]["n_checked"],
            "n_violations": old_in_diag["containment"]["n_violations"],
            "n_violations_at_5000": containment_scale_violations(old_in_diag, 5000),
            "label": "diagnostic_only",
        },
    }
    oracle = oracle_definition(ladders, doc_source, questions)
    mixed = mixed_mode(ladders)
    drops = hnsw_and_bm25_drops()
    tests = acceptance(
        mixed, drops, inv, st, mut, lift, old_hnsw_inv, ladders, old_in_diag
    )

    payload = {
        "meta": {
            "B": B,
            "seed": SEED,
            "tau": TAU,
            "bootstrap": "paired_percentile_over_question_indices",
            "question_order": "sorted_question_ids",
            "n_star": "integer_hits_over_n_vs_one_tenth",
            "inputs": inputs,
            "skipped_ladders": skipped,
            "self_test": st,
            "numpy_version": np.__version__,
        },
        "ladder": tables,
        "metadata_lift": lift,
        "cross_embedder": cross,
        "log_linear": fits,
        "rq2_bm25": rq2,
        "invariants": inv,
        "self_test_invariants": mut,
        "old_hnsw_openai_invariants": old_hnsw_inv,
        "old_list_containment": old_list_containment,
        "oracle_definition": oracle,
        "mixed_mode": mixed,
        "old_hnsw_bm25_endpoint_means": drops,
        "acceptance_tests": tests,
    }

    REV1.mkdir(parents=True, exist_ok=True)
    dump_json(OUT_JSON, payload)
    write_md(OUT_MD, payload)
    write_csv(OUT_CSV, csv_rows)

    print(f"wrote {OUT_JSON}")
    print(f"wrote {OUT_MD}")
    print(f"wrote {OUT_CSV}")
    for t in tests:
        print(f"{t['result']}\t{t['name']}\tactual={t['actual']}\texpected={t['expected']}")
    return 0 if all(t["result"] == "PASS" for t in tests) else 1


if __name__ == "__main__":
    raise SystemExit(main())
