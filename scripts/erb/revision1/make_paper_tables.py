#!/usr/bin/env python3
"""Generate LaTeX table fragments for revision-1 manuscript (artifact-driven)."""

from __future__ import annotations

import json
import math
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
REV1 = ROOT / "artifacts" / "published" / "revision1"
PUB = ROOT / "artifacts" / "published"
OUT = REV1 / "paper_tables"

BOOT_B = 10_000
BOOT_SEED = 42
CI95 = (2.5, 97.5)
CI90 = (5.0, 95.0)

BM25_VARIANTS = [
    ("chars4000", r"\texttt{chars4000} (title+chunk)"),
    ("dense_text_chars4000", r"\texttt{dense\_text\_chars4000}"),
    ("chars8191", r"\texttt{chars8191} (title+chunk)"),
    ("tokens8191", r"\texttt{tokens8191} (title+chunk)"),
    ("untruncated", r"\texttt{untruncated} (title+chunk)"),
    ("dense_text", r"\texttt{dense\_text}"),
    ("raw_untruncated", r"\texttt{raw\_untruncated}"),
]

PLAN_EFS = (200, 400, 800)
PLAN_AUDIT_DBS = (
    (5434, "original copy"),
    (5433, "fresh restore"),
)

PER_N_SCALES = [5000, 10000, 15000, 20000, 25000, 40000, 50000, 75000, 100000]
PLAN_AUDIT_SCALES = PER_N_SCALES
PER_N_EFS = [40, 100, 200, 400, 800]
PER_N_META_SCALES = [5000, 25000, 50000, 100000]
ROUTING_P_GRID = [0.0, 0.05, 0.1, 0.2, 0.3, 0.5, 1.0]
ROUTING_SCALES = [5000, 50000, 100000]
RRF_TABLE_SCALES = [5000, 25000, 50000, 100000]

QUESTION_TYPE_ORDER = [
    "basic",
    "semantic",
    "metadata",
    "constrained",
    "project_related",
    "intra_document_reasoning",
    "conflicting_info",
    "completeness",
    "miscellaneous",
]

TYPE_TEX = {
    "basic": "basic",
    "semantic": "semantic",
    "metadata": "metadata",
    "constrained": "constrained",
    "project_related": r"project\_related",
    "intra_document_reasoning": r"intra\_doc.\ reasoning",
    "conflicting_info": r"conflicting\_info",
    "completeness": "completeness",
    "miscellaneous": "miscellaneous",
}

FIT_SPECS = [
    ("OpenAI", "openai", "primary200", "exact_ladder_openai_primary200.json", ("raw", "meta_in")),
    ("Titan", "titan", "primary200", "exact_ladder_titan_primary200.json", ("raw", "meta_in")),
    ("OpenAI", "openai", "primary400", "exact_ladder_openai_primary400.json", ("raw", "meta_in")),
]

FIT_METRICS = ("hit_at_1", "hit_at_10", "mrr")
FIT_METRIC_TEX = {"hit_at_1": "Hit@1", "hit_at_10": "Hit@10", "mrr": "MRR"}

_BOOT_IDX: dict[int, np.ndarray] = {}


@dataclass
class SourceTracker:
    fragments: dict[str, list[dict[str, Any]]] = field(default_factory=dict)

    def add(self, fragment: str, path: Path | str, keys: list[Any]) -> None:
        rel = str(path)
        try:
            rel = str(Path(path).relative_to(ROOT))
        except ValueError:
            pass
        self.fragments.setdefault(fragment, []).append({"file": rel, "keys": keys})


SOURCES = SourceTracker()


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def fmt3(x: float | int | None) -> str:
    if x is None:
        return "---"
    return f"{float(x):.3f}"


def fmtq(x: float | int | None) -> str:
    """n=400 values: print a value on the 1/400 grid that ends in 5 at the
    fourth decimal exactly (0.0775, not 0.077 from round-half-even)."""
    if x is None:
        return "---"
    v = float(x)
    if abs(abs(v * 1000 - math.floor(v * 1000)) - 0.5) < 1e-6 and abs(v * 400 - round(v * 400)) < 1e-6:
        return f"{v:.4f}"
    return f"{v:.3f}"


def ci_bracket_q(lo: float, hi: float) -> str:
    return f"$[{fmtq(lo)}, {fmtq(hi)}]$"


def ci_bracket(lo: float, hi: float) -> str:
    return f"$[{fmt3(lo)}, {fmt3(hi)}]$"


def tex_escape(s: str) -> str:
    return (
        s.replace("\\", "\\textbackslash{}")
        .replace("_", "\\_")
        .replace("%", "\\%")
        .replace("&", "\\&")
        .replace("#", "\\#")
    )


def scale_k(n: int) -> str:
    if n % 1000 == 0:
        return f"{n // 1000}k"
    return f"{n:,}".replace(",", "{,}")


def hit_flag(v: Any) -> int:
    if isinstance(v, bool):
        return int(v)
    return 1 if float(v) != 0.0 else 0


def index_runs(blob: dict[str, Any]) -> dict[tuple[str, int], dict[str, Any]]:
    out: dict[tuple[str, int], dict[str, Any]] = {}
    for run in blob.get("runs") or []:
        scale = int(run.get("scale", run.get("corpus_scale_size")))
        out[(str(run["condition"]), scale)] = run
    return out


def qid_order(run: dict[str, Any]) -> list[str]:
    return [p["question_id"] for p in run.get("per_question") or []]


def canonical_question_ids(run: dict[str, Any]) -> list[str]:
    return sorted(qid_order(run))


def hit10_list(run: dict[str, Any], order: list[str]) -> list[int]:
    by_id = {p["question_id"]: p for p in run.get("per_question") or []}
    return [hit_flag(by_id[q]["hit_at_10"]) for q in order]


def question_type_of(qid: str) -> str:
    if "::" not in qid:
        raise ValueError(f"missing type suffix in question_id: {qid}")
    return qid.split("::", 1)[1]


def boot_idx(n: int) -> np.ndarray:
    if n not in _BOOT_IDX:
        rng = np.random.default_rng(BOOT_SEED)
        _BOOT_IDX[n] = rng.integers(0, n, size=(BOOT_B, n))
    return _BOOT_IDX[n]


def align_metric(run: dict[str, Any], order: list[str], metric: str) -> np.ndarray:
    by_id = {p["question_id"]: p for p in run.get("per_question") or []}
    out = np.empty(len(order), dtype=np.float64)
    for i, q in enumerate(order):
        v = by_id[q][metric]
        if metric.startswith("hit_at_"):
            out[i] = float(hit_flag(v))
        else:
            out[i] = float(v)
    return out


def ols_slope_intercept_r2(x: np.ndarray, y: np.ndarray) -> tuple[float, float, float]:
    x = np.asarray(x, dtype=np.float64)
    y = np.asarray(y, dtype=np.float64)
    design = np.column_stack([x, np.ones_like(x)])
    beta, _, _, _ = np.linalg.lstsq(design, y, rcond=None)
    slope = float(beta[0])
    intercept = float(beta[1])
    yhat = design @ beta
    ss_res = float(np.sum((y - yhat) ** 2))
    ss_tot = float(np.sum((y - y.mean()) ** 2))
    r2 = 1.0 if ss_tot == 0.0 else 1.0 - ss_res / ss_tot
    return slope, intercept, float(r2)


def slope_bootstrap_ladder(
    metric_by_scale: list[np.ndarray],
    scales: list[int],
    *,
    exclude: set[int] | None = None,
) -> dict[str, Any]:
    keep = [i for i, s in enumerate(scales) if exclude is None or s not in exclude]
    sc = np.array([scales[i] for i in keep], dtype=np.float64)
    x = np.log(sc)
    mats = np.stack([metric_by_scale[i] for i in keep], axis=0)
    n_q = mats.shape[1]
    idx = boot_idx(n_q)
    y_point = mats.mean(axis=1)
    slope, intercept, r2 = ols_slope_intercept_r2(x, y_point)
    boot_y = mats[:, idx].mean(axis=2).T
    design = np.column_stack([x, np.ones_like(x)])
    xtx_inv = np.linalg.inv(design.T @ design)
    betas = (xtx_inv @ design.T @ boot_y.T).T
    slope_boot = betas[:, 0]
    lo, hi = np.percentile(slope_boot, [CI95[0], CI95[1]])
    return {
        "slope": slope,
        "intercept": intercept,
        "r2": r2,
        "slope_ci_lo": float(lo),
        "slope_ci_hi": float(hi),
        "scales": [int(s) for s in sc],
        "n_points": int(len(sc)),
    }


def log_linear_from_ladder(blob: dict[str, Any], cond: str) -> dict[str, Any]:
    runs = index_runs(blob)
    scales = [int(s) for s in blob["meta"]["scales"]]
    order = qid_order(runs[(cond, scales[0])])
    out: dict[str, Any] = {}
    for metric in FIT_METRICS:
        series = [align_metric(runs[(cond, s)], order, metric) for s in scales]
        out[metric] = {
            "all_scales": slope_bootstrap_ladder(series, scales),
            "exclude_5k": slope_bootstrap_ladder(series, scales, exclude={5000}),
        }
    return out


def resolve_log_linear_fit(
    ae: dict[str, Any],
    blob: dict[str, Any],
    *,
    emb: str,
    bank: str,
    cond: str,
    metric: str,
    ladder_name: str,
    track: SourceTracker,
    computed_rows: set[tuple[str, str, str]],
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Return (all_scales, exclude_5k) fit dicts."""
    metric_block = (
        ae.get("log_linear", {}).get(emb, {}).get(bank, {}).get(cond, {}).get(metric)
    )
    if isinstance(metric_block, dict) and "all_scales" in metric_block:
        track.add(
            "tab_fits.tex",
            REV1 / "analysis_exact.json",
            ["log_linear", emb, bank, cond, metric],
        )
        return metric_block["all_scales"], metric_block["exclude_5k"]
    fits = log_linear_from_ladder(blob, cond)
    track.add("tab_fits.tex", REV1 / ladder_name, ["runs", cond, "per_question", "computed"])
    computed_rows.add((emb, bank, cond))
    return fits[metric]["all_scales"], fits[metric]["exclude_5k"]


def lift_list(raw_run: dict[str, Any], meta_run: dict[str, Any], order: list[str]) -> list[float]:
    raw_by = {p["question_id"]: p for p in raw_run["per_question"]}
    meta_by = {p["question_id"]: p for p in meta_run["per_question"]}
    return [
        float(hit_flag(meta_by[q]["hit_at_10"]) - hit_flag(raw_by[q]["hit_at_10"]))
        for q in order
    ]


def bootstrap_mean_ci(flags: list[int] | np.ndarray, *, pct: tuple[float, float] = CI95) -> tuple[float, float, float]:
    arr = np.asarray(flags, dtype=np.float64)
    n = arr.size
    if n == 0:
        raise ValueError("empty flags")
    point = float(arr.mean())
    idx = boot_idx(n)
    boots = arr[idx].mean(axis=1)
    lo, hi = np.percentile(boots, pct)
    return point, float(lo), float(hi)


def bootstrap_paired_mean_ci(diffs: list[float] | np.ndarray, *, pct: tuple[float, float] = CI95) -> tuple[float, float, float]:
    arr = np.asarray(diffs, dtype=np.float64)
    n = arr.size
    point = float(arr.mean())
    idx = boot_idx(n)
    boots = arr[idx].mean(axis=1)
    lo, hi = np.percentile(boots, pct)
    return point, float(lo), float(hi)


def equivalent_within_delta(ci_lo: float, ci_hi: float, delta: float) -> bool:
    return ci_lo > -delta and ci_hi < delta


def bootstrap_lift_slope_ci(
    ladders: dict[int, tuple[list[int], list[int]]],
    *,
    pct: tuple[float, float] = CI95,
) -> tuple[float, float, float]:
    """OLS slope of per-question lift vs log10(N); bootstrap over questions."""
    scales = sorted(ladders.keys())
    if len(scales) < 2:
        raise ValueError("need >=2 scales")
    # align question count
    n = len(ladders[scales[0]][0])
    x = np.log10(np.asarray(scales, dtype=np.float64))
    x_mean = x.mean()
    x_center = x - x_mean
    denom = float(np.sum(x_center**2))

    def slope_from_matrix(mat: np.ndarray) -> float:
        y_mean = mat.mean(axis=1, keepdims=True)
        y_center = mat - y_mean
        num = (y_center * x_center).sum(axis=1)
        return float((num / denom).mean())

    lifts = []
    for s in scales:
        raw_h, meta_h = ladders[s]
        lifts.append(np.asarray(meta_h, dtype=np.float64) - np.asarray(raw_h, dtype=np.float64))
    mat = np.stack(lifts, axis=1)  # (n, n_scales)
    point = slope_from_matrix(mat)

    idx = boot_idx(n)
    sampled = mat[idx, :]
    y_mean = sampled.mean(axis=1)
    y_center = y_mean - y_mean.mean(axis=1, keepdims=True)
    num = (y_center * x_center).sum(axis=1)
    boots = num / denom
    lo, hi = np.percentile(boots, pct)
    return point, float(lo), float(hi)


def paired_drop_ci(
    run_lo: dict[str, Any],
    run_hi: dict[str, Any],
    order: list[str],
    *,
    pct: tuple[float, float] = CI95,
) -> dict[str, Any]:
    a = hit10_list(run_lo, order)
    b = hit10_list(run_hi, order)
    diffs = [float(x - y) for x, y in zip(a, b)]
    point, lo, hi = bootstrap_paired_mean_ci(diffs, pct=pct)
    return {
        "hit_at_10_5000": float(np.mean(a)),
        "hit_at_10_100000": float(np.mean(b)),
        "estimate": point,
        "ci_lo": lo,
        "ci_hi": hi,
    }


def latex_table(
    *,
    label: str,
    caption: str,
    tabular: str,
    star: bool = False,
) -> str:
    env = "table*" if star else "table"
    fit = "\\fittext" if star else "\\fitcolumn"
    # true minus signs in table cells; only in text segments (even positions between "$"), never inside math
    _parts = tabular.split("$")
    for _i in range(0, len(_parts), 2):
        _parts[_i] = re.sub(r"(?<=[&\s\[(=,])-(?=\d)", "$-$", _parts[_i])
    tabular = "$".join(_parts)
    end_tag = "\\end{tabular}"
    if end_tag in tabular:
        head, tail = tabular.split(end_tag, 1)
        tabular = f"{fit}{{{head}{end_tag}}}{tail}"
    return (
        f"\\begin{{{env}}}[t]\n"
        f"\\caption{{{caption}}}\n"
        f"\\label{{{label}}}\n"
        f"\\centering\n"
        f"\\small\n"
        f"{tabular}\n"
        f"\\end{{{env}}}\n"
    )


def build_tab_exact_openai(track: SourceTracker) -> str:
    path = REV1 / "exact_ladder_openai_primary200.json"
    blob = load_json(path)
    track.add("tab_exact_openai.tex", path, ["runs", "metrics", "per_question"])
    meta = blob["meta"]
    scales = [int(s) for s in meta["scales"]]
    runs = index_runs(blob)
    rows: list[str] = []
    for cond in ("raw", "meta_in"):
        for scale in scales:
            run = runs[(cond, scale)]
            m = run["metrics"]
            order = canonical_question_ids(run)
            h10 = hit10_list(run, order)
            _, lo, hi = bootstrap_mean_ci(h10)
            rows.append(
                f"\\texttt{{{cond}}} & {scale_k(scale)} & {fmtq(m['hit_at_1'])} & "
                f"{fmtq(m['hit_at_5'])} & {fmtq(m['hit_at_10'])} & {ci_bracket_q(lo, hi)} & "
                f"{fmt3(m['document_recall'])} & {fmt3(m['mrr'])} \\\\"
            )
    tab = (
        "\\begin{tabular}{llrrrrrl}\n"
        "\\toprule\n"
        "Condition & $N$ & Hit@1 & Hit@5 & Hit@10 & Hit@10 95\\% CI & DocR@10 & MRR \\\\\n"
        "\\midrule\n"
        + "\n".join(rows)
        + "\n\\bottomrule\n\\end{tabular}"
    )
    return latex_table(
        label="tab:exact200",
        caption="OpenAI exact vector search (primary-200): raw and \\texttt{meta\\_in} across corpus scales.",
        tabular=tab,
        star=True,
    )


def build_tab_exact_titan(track: SourceTracker) -> str:
    path = REV1 / "exact_ladder_titan_primary200.json"
    blob = load_json(path)
    track.add("tab_exact_titan.tex", path, ["runs", "metrics", "per_question"])
    scales = [int(s) for s in blob["meta"]["scales"]]
    runs = index_runs(blob)
    rows = []
    for cond in ("raw", "meta_in"):
        for scale in scales:
            run = runs[(cond, scale)]
            m = run["metrics"]
            order = canonical_question_ids(run)
            _, lo, hi = bootstrap_mean_ci(hit10_list(run, order))
            rows.append(
                f"\\texttt{{{cond}}} & {scale_k(scale)} & {fmt3(m['hit_at_1'])} & "
                f"{fmt3(m['hit_at_5'])} & {fmt3(m['hit_at_10'])} & {ci_bracket(lo, hi)} & "
                f"{fmt3(m['document_recall'])} & {fmt3(m['mrr'])} \\\\"
            )
    tab = (
        "\\begin{tabular}{llrrrrrl}\n\\toprule\n"
        "Condition & $N$ & Hit@1 & Hit@5 & Hit@10 & Hit@10 95\\% CI & DocR@10 & MRR \\\\\n\\midrule\n"
        + "\n".join(rows)
        + "\n\\bottomrule\n\\end{tabular}"
    )
    return latex_table(
        label="tab:exact_titan",
        caption="Amazon Titan V2 exact search (primary-200): raw and \\texttt{meta\\_in}.",
        tabular=tab,
        star=True,
    )


def _tab_exact_n400_body(blob: dict[str, Any], scales: list[int], track_name: str, track: SourceTracker) -> str:
    path = REV1 / "exact_ladder_openai_primary400.json"
    track.add(track_name, path, ["runs", "metrics", "per_question"])
    runs = index_runs(blob)
    rows = []
    for cond in ("raw", "meta_in"):
        for scale in scales:
            run = runs[(cond, scale)]
            m = run["metrics"]
            order = canonical_question_ids(run)
            _, lo, hi = bootstrap_mean_ci(hit10_list(run, order))
            rows.append(
                f"\\texttt{{{cond}}} & {scale_k(scale)} & {fmtq(m['hit_at_1'])} & "
                f"{fmtq(m['hit_at_5'])} & {fmtq(m['hit_at_10'])} & {ci_bracket_q(lo, hi)} & "
                f"{fmtq(m['document_recall'])} & {fmtq(m['mrr'])} \\\\"
            )
    return (
        "\\begin{tabular}{llrrrrrl}\n\\toprule\n"
        "Condition & $N$ & Hit@1 & Hit@5 & Hit@10 & Hit@10 95\\% CI & DocR@10 & MRR \\\\\n\\midrule\n"
        + "\n".join(rows)
        + "\n\\bottomrule\n\\end{tabular}"
    )


def build_tab_exact_n400(track: SourceTracker) -> str:
    blob = load_json(REV1 / "exact_ladder_openai_primary400.json")
    tab = _tab_exact_n400_body(blob, [5000, 50000, 100000], "tab_exact_n400.tex", track)
    return latex_table(
        label="tab:exact400",
        caption="OpenAI exact search (primary-400) at 5k, 50k, and 100k.",
        tabular=tab,
    )


def build_tab_exact_n400_full(track: SourceTracker) -> str:
    blob = load_json(REV1 / "exact_ladder_openai_primary400.json")
    scales = [int(s) for s in blob["meta"]["scales"]]
    tab = _tab_exact_n400_body(blob, scales, "tab_exact_n400_full.tex", track)
    return latex_table(
        label="tab:exact400full",
        caption="OpenAI exact search (primary-400): all nine corpus scales.",
        tabular=tab,
        star=True,
    )


def build_tab_drift_summary(track: SourceTracker) -> str:
    ae_path = REV1 / "analysis_exact.json"
    ae = load_json(ae_path)
    track.add("tab_drift_summary.tex", ae_path, ["cross_embedder", "primary200", "hit10_drop_5k_to_100k"])

    ladders = {
        ("OpenAI", "primary200"): load_json(REV1 / "exact_ladder_openai_primary200.json"),
        ("Titan", "primary200"): load_json(REV1 / "exact_ladder_titan_primary200.json"),
        ("OpenAI", "primary400"): load_json(REV1 / "exact_ladder_openai_primary400.json"),
    }
    rows = []
    drops_art = ae["cross_embedder"]["primary200"]["hit10_drop_5k_to_100k"]
    key_map = {
        ("OpenAI", "primary200", "raw"): "openai_raw",
        ("OpenAI", "primary200", "meta_in"): "openai_meta_in",
        ("Titan", "primary200", "raw"): "titan_raw",
        ("Titan", "primary200", "meta_in"): "titan_meta_in",
    }
    for (emb, bank), blob in ladders.items():
        runs = index_runs(blob)
        order = canonical_question_ids(runs[("raw", 5000)])
        for cond in ("raw", "meta_in"):
            if bank == "primary400":
                drop = paired_drop_ci(runs[(cond, 5000)], runs[(cond, 100000)], order)
                track.add(
                    "tab_drift_summary.tex",
                    REV1 / f"exact_ladder_{emb.lower()}_primary400.json",
                    ["runs", cond, "per_question"],
                )
            else:
                drop = drops_art[key_map[(emb, bank, cond)]]
                track.add("tab_drift_summary.tex", ae_path, ["cross_embedder", "primary200", "hit10_drop_5k_to_100k", key_map[(emb, bank, cond)]])
            nlabel = f"{emb} $n{{=}}200$" if bank == "primary200" else f"{emb} $n{{=}}400$"
            f = fmtq if bank == "primary400" else fmt3
            cb = ci_bracket_q if bank == "primary400" else ci_bracket
            rows.append(
                f"{nlabel} & \\texttt{{{cond}}} & {f(drop['hit_at_10_5000'])} & "
                f"{f(drop['hit_at_10_100000'])} & {f(drop['estimate'])} & {cb(drop['ci_lo'], drop['ci_hi'])} \\\\"
            )
    tab = (
        "\\begin{tabular}{llrrrl}\n\\toprule\n"
        "Arm & Condition & Hit@10 @5k & Hit@10 @100k & $\\Delta$Hit@10 & 95\\% CI \\\\"
        "\n\\midrule\n" + "\n".join(rows) + "\n\\bottomrule\n\\end{tabular}"
    )
    return latex_table(
        label="tab:drift",
        caption="Corpus-scale drift (5k$\\rightarrow$100k) for Hit@10 under raw and \\texttt{meta\\_in}.",
        tabular=tab,
        star=True,
    )


def build_tab_lift(track: SourceTracker) -> str:
    specs = [
        ("OpenAI", "primary200", REV1 / "exact_ladder_openai_primary200.json"),
        ("Titan", "primary200", REV1 / "exact_ladder_titan_primary200.json"),
        ("OpenAI", "primary400", REV1 / "exact_ladder_openai_primary400.json"),
    ]
    scales_200 = [5000, 10000, 15000, 20000, 25000, 40000, 50000, 75000, 100000]
    col_scales = scales_200
    header = " & ".join([scale_k(s) for s in col_scales])
    arm_labels: list[str] = []
    arm_cells: list[list[str]] = []
    summary_rows: list[str] = []
    meta_first_note: list[str] = []

    for emb, bank, path in specs:
        blob = load_json(path)
        track.add("tab_lift.tex", path, ["runs", "per_question"])
        runs = index_runs(blob)
        scales = [int(s) for s in blob["meta"]["scales"]] if bank == "primary200" else scales_200
        order = canonical_question_ids(runs[("raw", scales[0])])
        lift_by_scale: dict[int, tuple[float, float, float]] = {}
        ladder_mat: dict[int, tuple[list[int], list[int]]] = {}
        for scale in scales:
            raw_h = hit10_list(runs[("raw", scale)], order)
            meta_h = hit10_list(runs[("meta_in", scale)], order)
            ladder_mat[scale] = (raw_h, meta_h)
            lifts = [float(a - b) for a, b in zip(meta_h, raw_h)]
            point, lo, hi = bootstrap_paired_mean_ci(lifts)
            lift_by_scale[scale] = (point, lo, hi)

        cells = []
        for s in col_scales:
            if s in lift_by_scale:
                p, lo, hi = lift_by_scale[s]
                cells.append(f"{(fmtq if bank == 'primary400' else fmt3)(p)} {(ci_bracket_q if bank == 'primary400' else ci_bracket)(lo, hi)}")
            else:
                cells.append("---")
        arm_labels.append(f"{emb} $n{{=}}${bank[-3:]}")
        arm_cells.append(cells)

        d5 = lift_by_scale[5000][0]
        d100 = lift_by_scale[100000][0]
        l5 = lift_list(runs[("raw", 5000)], runs[("meta_in", 5000)], order)
        l100 = lift_list(runs[("raw", 100000)], runs[("meta_in", 100000)], order)
        diffs = [float(b - a) for a, b in zip(l5, l100)]
        chg, lo, hi = bootstrap_paired_mean_ci(diffs)
        slope, slo, shi = bootstrap_lift_slope_ci(ladder_mat)
        summary_rows.append(
            f"\\multicolumn{{{len(arm_labels)+1}}}{{l}}{{{emb} $n{{=}}${bank[-3:]}, $95\\%$ intervals: "
            f"$\\Delta$lift(100k$-$5k)={(fmtq if bank == 'primary400' else fmt3)(chg)} {(ci_bracket_q if bank == 'primary400' else ci_bracket)(lo, hi)}; "
            f"slope/tenfold={fmt3(slope)} {ci_bracket(slo, shi)}}} \\\\"
        )

        if bank == "primary200":
            for s in (5000, 100000):
                mf = runs[("meta_first", s)]["metrics"]["hit_at_10"] - runs[("raw", s)]["metrics"]["hit_at_10"]
                meta_first_note.append(f"{emb} {scale_k(s)} {fmt3(mf)}")

    foot = (
        "\\midrule\n" + "\n".join(summary_rows) + "\n\\bottomrule\n\\end{tabular}\n"
        f"\\par\\smallskip\\footnotesize{{Legacy \\texttt{{meta\\_first}} lift (meta$-$raw): {', '.join(meta_first_note)}.}}"
    )
    n_arms = len(arm_labels)
    body_rows = [
        f"{scale_k(s)} & " + " & ".join(arm_cells[j][i] for j in range(n_arms)) + " \\\\"
        for i, s in enumerate(col_scales)
    ]
    import re as _re

    summary_rows = [_re.sub(r"\\multicolumn\{\d+\}\{l\}", f"\\\\multicolumn{{{n_arms + 1}}}{{l}}", r) for r in summary_rows]
    summary_lines = [r.replace(f"\\multicolumn{{{n_arms + 1}}}{{l}}{{", "", 1).rsplit("}", 1)[0] + " \\\\" for r in summary_rows]
    foot = (
        "\\bottomrule\n\\end{tabular}\n"
        "\\par\\smallskip\n{\\footnotesize\\begin{tabular}{@{}l@{}}\n" + "\n".join(summary_lines) + "\n\\end{tabular}}\n"
        f"\\par\\smallskip\n\\parbox{{0.8\\textwidth}}{{\\footnotesize\\raggedright Legacy \\texttt{{meta\\_first}} lift (meta$-$raw): {', '.join(meta_first_note)}.}}"
    )
    tab = (
        f"\\begin{{tabular}}{{l{'r' * n_arms}}}\n\\toprule\n"
        f"$N$ & " + " & ".join(arm_labels) + " \\\\\n\\midrule\n"
        + "\n".join(body_rows)
        + "\n"
        + foot
    )
    return latex_table(
        label="tab:lift",
        caption="Metadata lift (\\texttt{meta\\_in}$-$raw) with paired 95\\% bootstrap CIs; the text quotes the $90\\%$ intervals of the summary rows from Table~\\ref{tab:equiv}.",
        tabular=tab,
        star=True,
    )


def equiv_verdict(q: dict[str, Any], delta: float) -> str:
    key = "equivalent_delta_0.05" if delta == 0.05 else "equivalent_delta_0.10"
    val = q.get(key)
    if val is True:
        return "yes"
    if val is False:
        return "no"
    return "?"


EQUIV_LABELS = {
    "a_openai_minus_titan_raw_drop_5k_100k": "Raw Hit@10 drop 5k$\\to$100k, OpenAI $-$ Titan",
    "b_openai_minus_titan_meta_in_drop_5k_100k": "Filtered Hit@10 drop 5k$\\to$100k, OpenAI $-$ Titan",
    "d_openai_minus_titan_raw_hit10_level_by_scale@100000": "Raw Hit@10 level at 100k, OpenAI $-$ Titan",
    "c_openai_minus_titan_meta_lift_by_scale@5000": "Metadata lift at 5k, OpenAI $-$ Titan",
    "c_openai_minus_titan_meta_lift_by_scale@50000": "Metadata lift at 50k, OpenAI $-$ Titan",
    "c_openai_minus_titan_meta_lift_by_scale@100000": "Metadata lift at 100k, OpenAI $-$ Titan",
    "e_dense_minus_bm25_drop_difference.openai_raw": "Raw drop, OpenAI $-$ BM25",
    "e_dense_minus_bm25_drop_difference.titan_raw": "Raw drop, Titan $-$ BM25",
    "f_lift_100k_minus_lift_5k_openai": "Lift change 100k$-$5k, OpenAI $n{=}200$",
    "f_lift_100k_minus_lift_5k_titan": "Lift change 100k$-$5k, Titan $n{=}200$",
    "g_lift_100k_minus_lift_5k_openai_primary400 [computed by make_paper_tables.py]": "Lift change 100k$-$5k, OpenAI $n{=}400$",
    "h_lift_slope_per_tenfold_openai_primary400 [computed by make_paper_tables.py]": "Lift slope per tenfold $N$, OpenAI $n{=}400$",
}


def _build_equiv(track: SourceTracker, extra: dict[str, Any], *, compact: bool) -> str:
    path = REV1 / "analysis_equivalence.json"
    eq = load_json(path)
    track.add("tab_equiv.tex" if compact else "tab_equiv_full.tex", path, ["quantities"])
    rows: list[str] = []

    def add_row(name: str, est: float, lo: float, hi: float, q: dict[str, Any]) -> None:
        v05 = equiv_verdict(q, 0.05)
        v10 = equiv_verdict(q, 0.10)
        full_name = f"{name} [{q['note']}]" if q.get("note") else name
        if compact:
            if full_name not in EQUIV_LABELS and name not in EQUIV_LABELS:
                return
            label = EQUIV_LABELS.get(full_name) or EQUIV_LABELS[name]
            rows.append(f"{label} & {fmtq(est)} & {ci_bracket_q(lo, hi)} & {v05} & {v10} \\\\")
        else:
            rows.append(f"\\texttt{{{tex_escape(full_name)}}} & {fmtq(est)} & {ci_bracket_q(lo, hi)} & {v05} & {v10} \\\\")

    quantities = dict(eq["quantities"])
    quantities.update(extra)
    for key in sorted(quantities.keys()):
        val = quantities[key]
        if isinstance(val, dict) and "estimate" in val:
            add_row(key, val["estimate"], val["ci90_lo"], val["ci90_hi"], val)
        elif isinstance(val, list):
            for item in val:
                label = f"{key}@{item.get('scale', '?')}"
                add_row(label, item["estimate"], item["ci90_lo"], item["ci90_hi"], item)
        elif isinstance(val, dict):
            for subk, subv in val.items():
                if isinstance(subv, dict) and "estimate" in subv:
                    add_row(f"{key}.{subk}", subv["estimate"], subv["ci90_lo"], subv["ci90_hi"], subv)
    tab = (
        "\\begin{tabular}{lrlcc}\n\\toprule\n"
        "Quantity & Est. & 90\\% CI & Equivalent, $\\delta{=}0.05$ & Equivalent, $\\delta{=}0.10$ \\\\\n\\midrule\n"
        + "\n".join(rows)
        + "\n\\bottomrule\n\\end{tabular}"
    )
    return latex_table(
        label="tab:equiv" if compact else "tab:equivfull",
        caption=(
            "Equivalence analysis: paired $90\\%$ bootstrap intervals; a quantity is called equivalent when its interval lies strictly inside "
            "$(-\\delta,+\\delta)$."
            if compact
            else "Equivalence analysis, all quantities (paired 90\\% bootstrap intervals)."
        ),
        tabular=tab,
        star=compact,
    )


def build_tab_equiv(track: SourceTracker, extra: dict[str, Any]) -> str:
    return _build_equiv(track, extra, compact=True)


def build_tab_equiv_full(track: SourceTracker, extra: dict[str, Any]) -> str:
    return _build_equiv(track, extra, compact=False)


def build_tab_bm25(track: SourceTracker) -> str:
    eq_path = REV1 / "analysis_equivalence.json"
    eq = load_json(eq_path)
    track.add("tab_bm25.tex", eq_path, ["quantities", "e_dense_minus_bm25_drop_difference"])

    openai = load_json(REV1 / "exact_ladder_openai_primary200.json")
    titan = load_json(REV1 / "exact_ladder_titan_primary200.json")
    track.add("tab_bm25.tex", REV1 / "exact_ladder_openai_primary200.json", ["runs", "raw", "metrics"])
    track.add("tab_bm25.tex", REV1 / "exact_ladder_titan_primary200.json", ["runs", "raw", "metrics"])

    def dense_row(name: str, blob: dict[str, Any]) -> str:
        runs = index_runs(blob)
        cells = []
        for scale in (5000, 50000, 100000):
            h = runs[("raw", scale)]["metrics"]["hit_at_10"]
            cells.append(fmt3(h))
        drop = runs[("raw", 5000)]["metrics"]["hit_at_10"] - runs[("raw", 100000)]["metrics"]["hit_at_10"]
        return f"{name} & " + " & ".join(cells) + f" & {fmt3(drop)} \\\\"

    rows = [
        dense_row("Dense exact OpenAI", openai),
        dense_row("Dense exact Titan", titan),
    ]
    for stem, label in BM25_VARIANTS:
        p = REV1 / f"bm25_{stem}.json"
        data = load_json(p)
        track.add("tab_bm25.tex", p, ["runs", "hit_at_10"])
        by_scale = {int(r["corpus_scale_size"]): r["hit_at_10"] for r in data["runs"]}
        drop = by_scale[5000] - by_scale[100000]
        rows.append(
            f"{label} & {fmt3(by_scale[5000])} & {fmt3(by_scale[50000])} & {fmt3(by_scale[100000])} & {fmt3(drop)} \\\\"
        )

    ae = load_json(REV1 / "analysis_exact.json")
    track.add("tab_bm25.tex", REV1 / "analysis_exact.json", ["rq2_bm25", "openai", "primary200", "bm25_dense_text", "raw"])
    track.add("tab_bm25.tex", REV1 / "analysis_exact.json", ["rq2_bm25", "titan", "primary200", "bm25_dense_text", "raw"])
    o_drop = ae["rq2_bm25"]["openai"]["primary200"]["bm25_dense_text"]["raw"]["dense_drop_minus_bm25_drop"]
    t_drop = ae["rq2_bm25"]["titan"]["primary200"]["bm25_dense_text"]["raw"]["dense_drop_minus_bm25_drop"]
    block2 = (
        "\\midrule\n"
        "\\multicolumn{5}{l}{\\emph{Drop difference 5k$\\to$100k, dense minus BM25 (\\texttt{dense\\_text}): estimate and paired 95\\% interval}} \\\\\n"
        f"OpenAI & {fmt3(o_drop['estimate'])} & \\multicolumn{{3}}{{l}}{{{ci_bracket(o_drop['ci_lo'], o_drop['ci_hi'])}}} \\\\\n"
        f"Titan & {fmt3(t_drop['estimate'])} & \\multicolumn{{3}}{{l}}{{{ci_bracket(t_drop['ci_lo'], t_drop['ci_hi'])}}} \\\\\n"
    )
    tab = (
        "\\begin{tabular}{lrrrr}\n\\toprule\n"
        "Method (Hit@10) & 5k & 50k & 100k & Drop 5k$\\to$100k \\\\\n\\midrule\n"
        + "\n".join(rows)
        + "\n"
        + block2
        + "\\bottomrule\n\\end{tabular}"
    )
    return latex_table(
        label="tab:bm25",
        caption=(
            "Lexical vs dense Hit@10 across scales (primary-200). "
            "The last two rows give the 5k$\\to$100k drop difference (dense minus BM25) and its paired bootstrap 95\\% interval; BM25 variants marked (title+chunk) count the title twice."
        ),
        tabular=tab,
        star=True,
    )


def build_tab_doclen(track: SourceTracker) -> str:
    path = REV1 / "doc_length_stats.json"
    dl = load_json(path)
    track.add("tab_doclen.tex", path, ["ladder_pool", "primary200_gold", "truncation"])

    def pct(frac: float) -> str:
        return f"{100.0 * frac:.1f}"

    def row_for_pop(pop_key: str, title: str) -> str:
        t = dl[pop_key]["chunk_text_only"]
        return (
            f"{title} & {int(t['count']):,} & {int(round(t['median'])):,} & {int(round(t['p90'])):,} & "
            f"{int(t['max']):,} & {pct(t['gt_4000_chars']['fraction'])} & {pct(t['gt_8191_chars']['fraction'])} & "
            f"{int(t['ge_8191_tokens']['count'])} & {int(t['gt_24000_chars']['count'])} \\\\"
        )

    tab = (
        "\\begin{tabular}{lrrrrrrrr}\n\\toprule\n"
        "Population & $n$ & Median & p90 & Max & $>$4k chars (\\%) & $>$8{,}191 chars (\\%) & "
        "$\\geq$8{,}191 tok. & $>$24k chars \\\\\n\\midrule\n"
        + row_for_pop("ladder_pool", "Ladder documents")
        + "\n"
        + row_for_pop("primary200_gold", "Primary-200 gold")
        + "\n\\bottomrule\n\\end{tabular}"
    )
    return latex_table(
        label="tab:doclen",
        caption=(
            "Length in characters of the embedded text (the title is part of it) of the $99{,}998$ ladder documents and of the $272$ gold documents "
            "of the primary bank, the share above the BM25 caps ($4{,}000$ and $8{,}191$ characters; $72.0\\%$ and $21.1\\%$ of the ladder documents for the title-plus-text BM25 input, which repeats the title), and the counts above the "
            "OpenAI cap ($8{,}191$ cl100k tokens; $11$ documents, one a gold anchor, none a primary-bank gold document) and the "
            "Titan cap ($24{,}000$ characters)."
        ),
        tabular=tab,
        star=True,
    )


def build_tab_plan_audit(track: SourceTracker) -> str:
    # Plan choice for all 200 primary questions in every cell (plain EXPLAIN,
    # full_plan_coverage.py). At ef_search=200 these equal the EXPLAIN (ANALYZE,
    # BUFFERS) shares of plan_audit_{port}.json in every cell; at 400/800 the
    # 40-question ANALYZE sample agrees wherever it is all-or-nothing.
    cov = load_json(REV1 / "plan_coverage_full.json")
    track.add("tab_plan_audit.tex", REV1 / "plan_coverage_full.json", ["single_table", "frac_hnsw"])
    audits = {port: {"cells": [dict(r, **{"pass": "forward"}) for r in cov["single_table"] if int(r["port"]) == int(port)]}
              for port, _ in PLAN_AUDIT_DBS}
    # Every arm (embedder) x condition x database x scale x ef_search cell (R3-B).
    groups = [("openai", "raw", "OpenAI raw"), ("openai", "meta", "OpenAI filtered"),
              ("titan", "raw", "Titan raw"), ("titan", "meta", "Titan filtered")]

    def share(v: float) -> str:
        if v == 0.0:
            return "0"
        if v == 1.0:
            return "1"
        from decimal import Decimal, ROUND_HALF_UP
        return str(Decimal(repr(v)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)).lstrip("0")

    rows = []
    for scale in PLAN_AUDIT_SCALES:
        cells = [scale_k(scale)]
        for emb, cond, _ in groups:
            for port, _ in PLAN_AUDIT_DBS:
                vals = []
                for ef in PLAN_EFS:
                    match = [
                        c
                        for c in audits[port]["cells"]
                        if c.get("pass", "forward") == "forward"
                        and c.get("embedder") == emb
                        and c.get("condition") == cond
                        and int(c["scale"]) == scale
                        and int(c["ef_search"]) == ef
                    ]
                    vals.append("--" if not match else share(float(match[0].get("frac_hnsw") or 0.0)))
                cells.append("/".join(vals))
        rows.append(" & ".join(cells) + " \\\\")
    ndb = len(PLAN_AUDIT_DBS)
    top = " & ".join(f"\\multicolumn{{{ndb}}}{{c}}{{{label}}}" for _, _, label in groups)
    cmid = "".join(f"\\cmidrule(lr){{{2 + i * ndb}-{1 + (i + 1) * ndb}}}" for i in range(len(groups)))
    dbs = " & ".join(("orig." if "original" in db else "fresh") for _ in groups for _, db in PLAN_AUDIT_DBS)
    hdr = "& " + top + " \\\\\n" + cmid + "\nScale & " + dbs
    tab = (
        "\\begin{tabular}{l" + "c" * (len(groups) * ndb) + "}\n\\toprule\n"
        + hdr
        + " \\\\\n\\midrule\n"
        + "\n".join(rows)
        + "\n\\bottomrule\n\\end{tabular}"
    )
    return latex_table(
        label="tab:planaudit",
        caption=(
            "Share of the $200$ primary questions whose plan used the HNSW index, "
            "for each embedder, condition (raw; filtered by the first listed source type, the v1 filter whose HNSW runs are audited), database (orig.: frozen original copy; fresh: fresh restore), "
            "and size. Each cell lists the share at $\\texttt{ef\\_search}{=}200/400/800$ (1: every query used HNSW; "
            "0: every query ran an exact scan). Every cell plans all $200$ questions (plain \\texttt{EXPLAIN}); the \\texttt{EXPLAIN (ANALYZE, BUFFERS)} audit gives identical shares at $\\texttt{ef\\_search}{=}200$ and agrees on its $40$-question sample at $400$ and $800$. "
            "All other queries used a B-tree or sequential scan followed by an exact sort."
        ),
        tabular=tab,
        star=True,
    )


def old_per_question_runs(old: dict[str, Any]) -> dict[tuple[str, int], dict[str, Any]]:
    if old.get("runs") and old["runs"][0].get("per_question"):
        return {(r["condition"], int(r["corpus_scale_size"])): r for r in old["runs"]}
    out = {}
    for r in old.get("runs_with_per_question") or []:
        out[(r["condition"], int(r["corpus_scale_size"]))] = r
    return out


def build_tab_old_vs_exact(track: SourceTracker) -> str:
    scales = (5000, 50000, 100000)
    specs = [
        ("OpenAI", PUB / "erb_full_primary200_to100k.json", REV1 / "exact_ladder_openai_primary200.json", "raw"),
        ("Titan", PUB / "erb_titan_primary200_to100k.json", REV1 / "exact_ladder_titan_primary200.json", "raw"),
    ]
    rows = []
    for emb, old_path, exact_path, cond in specs:
        old = load_json(old_path)
        exact = load_json(exact_path)
        track.add("tab_old_vs_exact.tex", old_path, ["runs", "per_question", "hit_at_10"])
        track.add("tab_old_vs_exact.tex", exact_path, ["runs", "per_question", "hit_at_10"])
        old_runs = old_per_question_runs(old)
        exact_runs = index_runs(exact)
        old_cond = cond if (emb, cond) != ("Titan", "raw") else "raw"
        for scale in scales:
            o_run = old_runs[(old_cond, scale)]
            e_run = exact_runs[(cond, scale)]
            order = [p["question_id"] for p in o_run["per_question"]]
            o_h = [hit_flag(p["hit_at_10"]) for p in o_run["per_question"]]
            e_h = hit10_list(e_run, order)
            n_diff = sum(1 for a, b in zip(o_h, e_h) if a != b)
            h_old = float(np.mean(o_h))
            h_ex = e_run["metrics"]["hit_at_10"]
            rows.append(
                f"{emb} & {scale_k(scale)} & {fmt3(h_old)} & {fmt3(h_ex)} & {fmt3(h_old - h_ex)} & {n_diff} \\\\"
            )
    tab = (
        "\\begin{tabular}{llrrrr}\n\\toprule\n"
        "Embedder & $N$ & Hit@10 HNSW & Hit@10 exact & Diff. & \\#Q flag diff. \\\\\n\\midrule\n"
        + "\n".join(rows)
        + "\n\\bottomrule\n\\end{tabular}"
    )
    return latex_table(
        label="tab:oldexact",
        caption="Legacy approximate (HNSW) vs exact search at selected scales.",
        tabular=tab,
    )


def _verified_hnsw_hit_by_ef(hrc: dict[str, Any]) -> dict[int, float]:
    """Verified probe hits at 100k raw (forced HNSW, or as-planned when all probes use HNSW)."""
    out: dict[int, float] = {}
    for cell in hrc.get("cells") or []:
        if cell.get("table") != "document_chunks" or cell.get("condition") != "raw":
            continue
        if int(cell.get("scale", -1)) != 100000:
            continue
        ef = int(cell["ef_search"])
        if ef not in (200, 400, 800):
            continue
        for mode_name in ("forced_hnsw", "as_planned"):
            for mode in cell.get("modes") or []:
                if mode.get("mode") != mode_name:
                    continue
                pc = mode.get("plan_check") or {}
                if not pc.get("all_probes_hnsw"):
                    continue
                out[ef] = float(mode["mean_hit_at_10_approx"])
                break
            if ef in out:
                break
    return out


def _cost_matrix_forced_hit(sm: dict[str, Any], ef: int) -> float | None:
    rows = sm.get("experiments", {}).get("planner_cost_explain_100k_raw") or []
    for row in rows:
        if int(row.get("ef_search", -1)) != ef:
            continue
        for desc in row.get("forced_hnsw_table_scan_node_types") or []:
            if "hnsw" in str(desc).lower():
                vs = row.get("forced_hnsw_vs_exact") or {}
                return float(vs["mean_hit_at_10_approx"])
        return None
    return None


def build_tab_ef_planner(track: SourceTracker) -> str:
    path = REV1 / "search_mode_diagnosis_5434.json"
    sm = load_json(path)
    track.add("tab_ef_planner.tex", path, ["experiments", "e2_ef_sweep_100k_openai_raw"])
    track.add(
        "tab_ef_planner.tex",
        path,
        ["experiments", "planner_cost_explain_100k_raw"],
    )
    hrc_path = REV1 / "hnsw_recall_by_cell_5434.json"
    hrc = load_json(hrc_path)
    track.add("tab_ef_planner.tex", hrc_path, ["cells", "forced_hnsw", "plan_check"])
    verified_hits = _verified_hnsw_hit_by_ef(hrc)
    e2 = {int(r["ef_search"]): r for r in sm["experiments"]["e2_ef_sweep_100k_openai_raw"]}
    efs = [100, 200, 300, 400, 500, 600, 800]
    rows = []
    for ef in efs:
        row = e2[ef]
        vs = row["vs_exact"]
        hnsw = row.get("example_plan_summary", {}).get("hnsw_used")
        plan = "HNSW" if hnsw else "exact"
        if ef in verified_hits:
            forced_col = fmt3(verified_hits[ef])
        elif ef in (500, 600):
            cm_hit = _cost_matrix_forced_hit(sm, ef)
            forced_col = fmt3(cm_hit) if cm_hit is not None else "--"
        else:
            forced_col = "--"
        rows.append(
            f"{ef} & {plan} & {fmt3(vs['mean_list_recall_at_10'])} & {fmt3(vs['mean_hit_at_10_approx'])} & "
            f"{fmt3(vs['mean_hit_at_10_exact_ref'])} & {forced_col} \\\\"
        )
    tab = (
        "\\begin{tabular}{rlrrrr}\n\\toprule\n"
        "\\texttt{ef} & Plan & Recall & Approx. & Exact & Forced \\\\\n\\midrule\n"
        + "\n".join(rows)
        + "\n\\bottomrule\n\\end{tabular}"
    )
    return latex_table(
        label="tab:efplanner",
        caption=(
            "OpenAI raw @100k on the original database copy: planner behavior (Recall is recall@10 against exact search; Approx. and Exact are Hit@10 with approximate and exact search). "
            "Forced is Hit@10 with the HNSW index forced, from \\texttt{hnsw\\_recall\\_by\\_cell\\_5434.json}, "
            "measured at $\\texttt{ef}\\in\\{200,400,800\\}$; a dash means not measured. "
            "At $\\texttt{ef}\\in\\{100,200,300\\}$ the planner used the index, so Approx. is an HNSW result; at $\\texttt{ef}\\ge400$ it chose an exact scan."
        ),
        tabular=tab,
    )


def bytes_to_mb(n: int | float) -> float:
    return float(n) / 1_000_000.0


def index_per_n_cells(blob: dict[str, Any]) -> dict[tuple[Any, ...], dict[str, Any]]:
    out: dict[tuple[Any, ...], dict[str, Any]] = {}
    for c in blob.get("cells") or []:
        key = (
            str(c.get("condition")),
            int(c["scale_n"]),
            int(c["ef_search"]),
            str(c.get("iterative_scan")),
            int(c.get("max_scan_tuples") or 20000),
            bool(c.get("seqscan_off")),
        )
        out[key] = c
    return out


def per_n_cell(
    idx: dict[tuple[Any, ...], dict[str, Any]],
    *,
    condition: str,
    scale_n: int,
    ef_search: int,
    iterative_scan: str = "relaxed_order",
    max_scan_tuples: int = 20000,
    seqscan_off: bool = False,
) -> dict[str, Any] | None:
    return idx.get((condition, scale_n, ef_search, iterative_scan, max_scan_tuples, seqscan_off))


def per_n_cell_needs_dagger(cell: dict[str, Any]) -> bool:
    if str(cell.get("condition")) != "raw":
        return False
    plan = cell.get("plan") or {}
    return bool(plan.get("seq_scan"))


def per_n_latency_cell(
    idx: dict[tuple[Any, ...], dict[str, Any]],
    cell: dict[str, Any],
) -> tuple[dict[str, Any], bool]:
    """Return latency source cell and whether a seqscan_off twin was substituted."""
    if not per_n_cell_needs_dagger(cell):
        return cell, False
    twin = per_n_cell(
        idx,
        condition=str(cell["condition"]),
        scale_n=int(cell["scale_n"]),
        ef_search=int(cell["ef_search"]),
        iterative_scan=str(cell.get("iterative_scan")),
        max_scan_tuples=int(cell.get("max_scan_tuples") or 20000),
        seqscan_off=True,
    )
    if twin is None:
        raise ValueError(
            f"missing seqscan_off twin for latency: "
            f"scale={cell['scale_n']} ef={cell['ef_search']} condition={cell['condition']}"
        )
    return twin, True


def recall_loss_cell(
    cell: dict[str, Any],
    *,
    idx: dict[tuple[Any, ...], dict[str, Any]],
) -> tuple[float, float, bool]:
    """Return (recall, hit_at_10_drop, dagger) using forced-index twin when needed."""
    plan = cell.get("plan") or {}
    dagger = str(cell.get("condition")) == "raw" and bool(plan.get("seq_scan"))
    src = cell
    if dagger:
        twin = per_n_cell(
            idx,
            condition=str(cell["condition"]),
            scale_n=int(cell["scale_n"]),
            ef_search=int(cell["ef_search"]),
            iterative_scan=str(cell.get("iterative_scan")),
            max_scan_tuples=int(cell.get("max_scan_tuples") or 20000),
            seqscan_off=True,
        )
        if twin is None:
            raise ValueError(
                f"missing seqscan_off twin for recall: "
                f"scale={cell['scale_n']} ef={cell['ef_search']} condition={cell['condition']}"
            )
        src = twin
    recall = float(src["recall_at_10_vs_exact"])
    loss = float(src["hit_at_10_drop"])
    return recall, loss, dagger


def plan_kind_tex(plan: dict[str, Any] | None) -> str:
    if not plan:
        return "---"
    pk = str(plan.get("plan_kind") or "")
    if pk == "hnsw_index_scan":
        return "hnsw"
    nodes = plan.get("node_types") or []
    if pk in ("other", "seq_scan") or any("Bitmap" in str(n) for n in nodes):
        return "exact-btree"
    if "Index Scan" in nodes and plan.get("hnsw_index_used"):
        return "hnsw"
    return pk.replace("_", "\\_")


def verify_raw_iterative_modes(openai_eval: dict[str, Any], titan_eval: dict[str, Any]) -> list[str]:
    """Return human-readable lines if strict vs relaxed disagree on raw cells."""
    lines: list[str] = []
    for label, blob in (("OpenAI", openai_eval), ("Titan", titan_eval)):
        cells = [
            c
            for c in blob.get("cells") or []
            if c.get("condition") == "raw" and not c.get("seqscan_off")
        ]
        modes = sorted({str(c.get("iterative_scan")) for c in cells})
        mismatches = 0
        for ef in PER_N_EFS:
            for scale in PER_N_SCALES:
                a = per_n_cell(
                    index_per_n_cells(blob),
                    condition="raw",
                    scale_n=scale,
                    ef_search=ef,
                    iterative_scan="relaxed_order",
                )
                b = per_n_cell(
                    index_per_n_cells(blob),
                    condition="raw",
                    scale_n=scale,
                    ef_search=ef,
                    iterative_scan="strict_order",
                )
                if a is None or b is None:
                    continue
                if (
                    abs(float(a["recall_at_10_vs_exact"]) - float(b["recall_at_10_vs_exact"])) > 1e-12
                    or abs(float(a["hit_at_10_drop"]) - float(b["hit_at_10_drop"])) > 1e-12
                ):
                    mismatches += 1
        if mismatches:
            lines.append(f"{label}: raw strict vs relaxed mismatches={mismatches}")
        else:
            lines.append(f"{label}: raw strict vs relaxed identical ({len(modes)} modes: {', '.join(modes)})")
    return lines


def build_tab_perN_recall(track: SourceTracker, openai: dict[str, Any], titan: dict[str, Any]) -> str:
    track.add("tab_perN_recall.tex", REV1 / "per_n_hnsw_eval_openai.json", ["cells"])
    track.add("tab_perN_recall.tex", REV1 / "per_n_hnsw_eval_titan.json", ["cells"])
    rows: list[str] = []
    dagger_count = 0
    for emb_label, blob in (("OpenAI", openai), ("Titan", titan)):
        idx = index_per_n_cells(blob)
        for scale in PER_N_SCALES:
            cells_ef: list[str] = []
            for ef in PER_N_EFS:
                cell = per_n_cell(idx, condition="raw", scale_n=scale, ef_search=ef)
                if cell is None:
                    cells_ef.append("---")
                    continue
                recall, loss, dagger = recall_loss_cell(cell, idx=idx)
                if dagger:
                    dagger_count += 1
                mark = "$^{\\dagger}$" if dagger else ""
                cells_ef.append(f"{(f'{recall:.4f}' if recall is not None and 0.9995 <= recall < 1 else fmt3(recall))} / {fmt3(loss)}{mark}")
            rows.append(f"{emb_label} & {scale_k(scale)} & " + " & ".join(cells_ef) + " \\\\")
    hdr = " & ".join(str(ef) for ef in PER_N_EFS)
    foot = (
        "\\par\\smallskip\\footnotesize{$^{\\dagger}$Planner chose a sequential scan; "
        "recall and Hit@10 loss shown from the matching \\texttt{seqscan\\_off} cell "
        f"({dagger_count} cells). Recall between $0.9995$ and $1$ is printed to four decimals.}}"
    )
    tab = (
        "\\begin{tabular}{@{}ll" + "r" * len(PER_N_EFS) + "@{}}\n\\toprule\n"
        f"Embedder & $N$ & \\multicolumn{{{len(PER_N_EFS)}}}{{c}}{{"
        f"\\texttt{{ef\\_search}}: recall / Hit@10 loss}} \\\\\n"
        f" &  & {hdr} \\\\\n\\midrule\n"
        + "\n".join(rows)
        + f"\n\\bottomrule\n\\end{{tabular}}\n{foot}"
    )
    return latex_table(
        label="tab:perNrecall",
        caption="Per-size HNSW approximate search (raw, \\texttt{relaxed\\_order}): list recall@10 vs exact and Hit@10 loss.",
        tabular=tab,
        star=True,
    )


def build_tab_perN_capacity(
    track: SourceTracker,
    openai_eval: dict[str, Any],
    titan_eval: dict[str, Any],
    build_openai: dict[str, Any],
    build_titan: dict[str, Any],
) -> str:
    track.add("tab_perN_capacity.tex", REV1 / "per_n_index_build_openai.json", ["build_log"])
    track.add("tab_perN_capacity.tex", REV1 / "per_n_index_build_titan.json", ["build_log"])
    track.add("tab_perN_capacity.tex", REV1 / "per_n_hnsw_eval_openai.json", ["cells", "latency"])
    rows: list[str] = []
    lat_dagger_count = 0
    specs = (
        ("OpenAI", openai_eval, build_openai),
        ("Titan", titan_eval, build_titan),
    )
    build_by_scale: dict[tuple[str, int], dict[str, Any]] = {}
    for emb, bl in (("OpenAI", build_openai), ("Titan", build_titan)):
        for rec in bl.get("build_log") or []:
            build_by_scale[(emb, int(rec["scale_n"]))] = rec

    for emb_label, ev, _ in specs:
        idx = index_per_n_cells(ev)

        def lat_cells(scale: int, ef: int) -> str:
            nonlocal lat_dagger_count
            c = per_n_cell(idx, condition="raw", scale_n=scale, ef_search=ef)
            if c is None:
                return "--- & ---"
            src, dagger = per_n_latency_cell(idx, c)
            if dagger:
                lat_dagger_count += 1
            lat = src.get("latency") or {}
            mark = "$^{\\dagger}$" if dagger else ""
            return f"{fmt3(lat.get('p50_query_ms'))}{mark} & {fmt3(lat.get('p95_query_ms'))}{mark}"

        for scale in PER_N_SCALES:
            bl = build_by_scale.get((emb_label, scale), {})
            cap = (per_n_cell(idx, condition="raw", scale_n=scale, ef_search=40) or {}).get("capacity") or {}
            total_mb = fmt3(
                bytes_to_mb(bl.get("total_bytes") or cap.get("total_bytes") or 0)
            )
            hnsw_mb = fmt3(bytes_to_mb(bl.get("hnsw_index_bytes") or cap.get("hnsw_index_bytes") or 0))
            build_s = fmt3(bl.get("hnsw_build_seconds") or cap.get("hnsw_build_seconds") or 0)
            row_count = bl.get("row_count") or cap.get("row_count") or scale
            rows.append(
                f"{emb_label} & {scale_k(scale)} & {row_count} & {total_mb} & {hnsw_mb} & {build_s} & "
                f"{lat_cells(scale, 200)} & {lat_cells(scale, 800)} \\\\"
            )
    foot = (
        "\\par\\smallskip\\footnotesize{Host shared with other processes; query latency indicative only. "
        "Latencies are the median and 95th percentile over questions of per-question medians "
        f"from three timed 200-question sweeps (\\texttt{{relaxed\\_order}}, "
        f"\\texttt{{max\\_scan\\_tuples}}$=20000$). "
        f"$^{{\\dagger}}$Default plan used sequential scan; latency from matching "
        f"\\texttt{{seqscan\\_off}} twin (the same probes run with \\texttt{{SET enable\\_seqscan=off}}; {lat_dagger_count} cells). "
        "``Total MB'' is on-disk size, \\texttt{total\\_bytes}/$10^6$ (heap, TOAST, and indexes), not memory use; the measured memory working set is given in Sec.~\\ref{sec:perN}. The HNSW size is the same for both embedders because each index entry occupies one 8~kB page at these dimensions. Exact scans are not timed here; the exact scan of the 200 queries at $100$k took $43.7$~s on the original database (artifact \\texttt{exact\\_control\\_mvp}). "
        "The 5k heap is small because vectors are stored out of line. Build time is the primary build (session setting \\texttt{max\\_parallel\\_maintenance\\_workers}$=4$, server default $2$); four further OpenAI builds per size took $2.2$--$2.3$~s at 5k, $50.2$--$56.0$~s at 75k and $25.1$--$29.9$~s at 100k. "
        "The 100k builds are faster because PostgreSQL assigns parallel build workers only when the heap reaches $8$~MB (\\texttt{min\\_parallel\\_table\\_scan\\_size}), which happens between 75k ($881$ pages) and 100k ($1{,}175$); builds up to 75k ran serially (a 75k copy built in $50.6$~s serially and in $12.2$~s with workers allowed; artifact \\texttt{build\\_parallel\\_probe}).}"
    )
    tab = (
        "\\begin{tabular}{@{}llrrrrrrrr@{}}\n\\toprule\n"
        "Embedder & $N$ & Rows & Total MB & HNSW MB & Build s & "
        "p50@200 (ms) & p95@200 (ms) & p50@800 (ms) & p95@800 (ms) \\\\\n\\midrule\n"
        + "\n".join(rows)
        + f"\n\\bottomrule\n\\end{{tabular}}\n{foot}"
    )
    return latex_table(
        label="tab:perNcap",
        caption="Per-$N$ index capacity and query latency (raw), with build times from per-scale HNSW builds.",
        tabular=tab,
        star=True,
    )


def build_tab_perN_meta(track: SourceTracker, openai: dict[str, Any], titan: dict[str, Any]) -> str:
    track.add("tab_perN_meta.tex", REV1 / "per_n_hnsw_eval_openai.json", ["cells", "plan"])
    track.add("tab_perN_meta.tex", REV1 / "per_n_hnsw_eval_titan.json", ["cells", "plan"])
    rows: list[str] = []
    for emb_label, blob in (("OpenAI", openai), ("Titan", titan)):
        idx = index_per_n_cells(blob)
        for cond in ("meta_first", "meta_in"):
            for ef in (200, 800):
                scale_cells: list[str] = []
                plans: list[str] = []
                for scale in PER_N_META_SCALES:
                    cell = per_n_cell(idx, condition=cond, scale_n=scale, ef_search=ef)
                    if cell is None:
                        scale_cells.append("---")
                        plans.append("?")
                        continue
                    recall, loss, _ = recall_loss_cell(cell, idx=idx)
                    scale_cells.append(f"{fmt3(recall)} / {fmt3(loss)}")
                    plans.append(plan_kind_tex(cell.get("plan") or {}))
                plan_col = "/".join(dict.fromkeys(plans))
                rows.append(
                    f"{emb_label} & \\texttt{{{cond}}} & {ef} & "
                    + " & ".join(scale_cells)
                    + f" & {plan_col} \\\\"
                )
    hdr = " & ".join(scale_k(s) for s in PER_N_META_SCALES)
    foot = (
        "\\par\\smallskip\\footnotesize{Plan kind from the first-question probe; "
        "planner choice varies with metadata-filter selectivity (often \\texttt{exact-btree} at these scales).}"
    )
    tab = (
        "\\begin{tabular}{@{}llr" + "r" * len(PER_N_META_SCALES) + "l@{}}\n\\toprule\n"
        f"Embedder & Condition & ef & {hdr} & Plan \\\\\n\\midrule\n"
        + "\n".join(rows)
        + f"\n\\bottomrule\n\\end{{tabular}}\n{foot}"
    )
    return latex_table(
        label="tab:perNmeta",
        caption="Metadata-filtered HNSW cells: recall and Hit@10 loss at selected scales.",
        tabular=tab,
        star=True,
    )


def build_tab_rrf(track: SourceTracker) -> str:
    path = REV1 / "rrf_hybrid_openai_primary200.json"
    rrf = load_json(path)
    track.add("tab_rrf.tex", path, ["by_scale", "drop_5k_to_100k"])
    rows: list[str] = []
    by_scale = {int(r["scale"]): r for r in rrf.get("by_scale") or []}
    for scale in RRF_TABLE_SCALES:
        r = by_scale[scale]
        rd = r["rrf_minus_dense_hit_at_10"]
        rb = r["rrf_minus_bm25_hit_at_10"]
        rows.append(
            f"{scale_k(scale)} & {fmt3(r['dense']['hit_at_10'])} & {fmt3(r['bm25']['hit_at_10'])} & "
            f"{fmt3(r['rrf_k60']['hit_at_10'])} & {fmt3(r['rrf_k60']['mrr'])} & "
            f"{fmt3(rd['estimate'])} {ci_bracket(rd['ci_lo'], rd['ci_hi'])} & "
            f"{fmt3(rb['estimate'])} {ci_bracket(rb['ci_lo'], rb['ci_hi'])} \\\\"
        )
    drop = rrf.get("drop_5k_to_100k") or {}
    drop_rows: list[str] = []
    for name, tex in (("dense", "Dense"), ("bm25", "BM25"), ("rrf_k60", "RRF $k{=}60$")):
        block = drop.get(name) or {}
        h = block.get("hit_at_10") or {}
        m = block.get("mrr") or {}
        drop_rows.append(
            f"{tex} & {fmt3(h.get('estimate'))} {ci_bracket(h.get('ci_lo', 0), h.get('ci_hi', 0))} & "
            f"{fmt3(m.get('estimate'))} {ci_bracket(m.get('ci_lo', 0), m.get('ci_hi', 0))} \\\\"
        )
    rmd = drop.get("rrf_minus_dense_drop_hit_at_10") or {}
    drop_rows.append(
        f"RRF$-$dense drop, Hit@10 & {fmt3(rmd.get('estimate'))} {ci_bracket(rmd.get('ci_lo', 0), rmd.get('ci_hi', 0))} & \\\\"
    )
    tab = (
        "\\begin{tabular}{@{}lrrrrll@{}}\n\\toprule\n"
        "$N$ & Dense H@10 & BM25 H@10 & RRF H@10 & RRF MRR & "
        "RRF$-$dense H@10 & RRF$-$BM25 H@10 \\\\\n\\midrule\n"
        + "\n".join(rows)
        + "\n\\bottomrule\n\\end{tabular}\n"
        "\\par\\medskip\n\\begin{tabular}{lll}\n\\toprule\n"
        "Drop 5k$\\to$100k & Hit@10 [95\\% CI] & MRR@10 [95\\% CI] \\\\\n\\midrule\n"
        + "\n".join(drop_rows)
        + "\n\\bottomrule\n\\end{tabular}"
    )
    return latex_table(
        label="tab:rrf",
        caption="Dense, BM25 (\\texttt{dense\\_text}), and RRF fusion ($k{=}60$) on primary-200; paired bootstrap 95\\% CIs. The lower block gives the 5k$\\to$100k drop in Hit@10 and in MRR@10 with intervals. Over all nine sizes, RRF minus dense Hit@10 ranges from $+0.110$ to $+0.150$. Intervals here come from this analysis's own bootstrap, which resamples the questions in a different order, and can differ by $0.005$ from other artifacts for the same quantity (e.g., the BM25 drop interval is $[0.080,0.170]$ here and $[0.080,0.175]$ in \\texttt{analysis\\_exact}).",
        tabular=tab,
        star=True,
    )


def routing_analytic_breakeven(
    compact: list[dict[str, Any]],
    *,
    mode: str,
    scale: int,
    raw_hit: float,
) -> tuple[str, float | None]:
    """Linear interpolation: p* = (mu(p=0) - raw) / (mu(p=0) - mu(p=1))."""
    key = {5000: "hit_at_10_5000", 50000: "hit_at_10_50000", 100000: "hit_at_10_100000"}[scale]

    def hit_at_p(p: float) -> float | None:
        for row in compact:
            if row.get("mode") == mode and abs(float(row.get("p", -1)) - p) < 1e-12:
                return float(row[key])
        return None

    mu0 = hit_at_p(0.0)
    mu1 = hit_at_p(1.0)
    if mu0 is None or mu1 is None:
        return "---", None
    if mu1 >= raw_hit - 1e-12:
        return "never", None
    denom = mu0 - mu1
    if abs(denom) < 1e-12:
        return "---", None
    p_star = (mu0 - raw_hit) / denom
    return fmt3(p_star), float(p_star)


def build_tab_routing(track: SourceTracker) -> str:
    path = REV1 / "routing_simulation_openai_primary200.json"
    rt = load_json(path)
    track.add("tab_routing.tex", path, ["table_compact", "breakeven", "raw_hit_at_10"])
    compact = rt.get("table_compact") or []
    breakeven = rt.get("breakeven") or {}
    raw_by_scale = {int(k): float(v) for k, v in (rt.get("raw_hit_at_10") or {}).items()}
    meta = rt.get("meta") or {}
    p_cols = list(meta.get("p_grid") or ROUTING_P_GRID)
    modes = ["wrong_type", "wrong_dropgold", "superset", "abstain"]
    rows: list[str] = []
    be_footnotes: list[str] = []

    def hit_at(mode: str, p: float, scale: int) -> float | None:
        key = {5000: "hit_at_10_5000", 50000: "hit_at_10_50000", 100000: "hit_at_10_100000"}[scale]
        for row in compact:
            if row.get("mode") == mode and abs(float(row.get("p", -1)) - p) < 1e-12:
                return float(row[key])
        return None

    def be_val(mode: str, scale: int) -> str:
        raw_hit = raw_by_scale.get(scale)
        if raw_hit is None:
            block = breakeven.get(mode) or {}
            v = block.get(str(scale))
            if v is None:
                return "---"
            if isinstance(v, str):
                return v
            return fmt3(float(v))
        label, p_star = routing_analytic_breakeven(compact, mode=mode, scale=scale, raw_hit=raw_hit)
        mc = (breakeven.get(mode) or {}).get(str(scale))
        if p_star is not None and mc is not None and not isinstance(mc, str):
            if abs(float(mc) - p_star) > 0.003:
                be_footnotes.append(
                    f"\\texttt{{{tex_escape(mode)}}}@{scale_k(scale)}: MC break-even "
                    f"{fmt3(float(mc))} vs analytic {fmt3(p_star)}."
                )
        return label

    for mode in modes:
        for scale in ROUTING_SCALES:
            cells = [fmt3(hit_at(mode, p, scale)) if hit_at(mode, p, scale) is not None else "---" for p in p_cols]
            rows.append(
                f"\\texttt{{{tex_escape(mode)}}} & {scale_k(scale)} & "
                + " & ".join(cells)
                + f" & {be_val(mode, scale)} \\\\"
            )
    hdr = " & ".join(f"{p:g}" for p in p_cols)
    tab = (
        "\\begin{tabular}{@{}ll" + "r" * len(p_cols) + "r@{}}\n\\toprule\n"
        f"Mode & $N$ & \\multicolumn{{{len(p_cols)}}}{{c}}{{Hit@10 at router error $p$}} & "
        f"Break-even $p$ \\\\\n &  & {hdr} &  \\\\\n\\midrule\n"
        + "\n".join(rows)
        + "\n\\bottomrule\n\\end{tabular}"
    )
    if be_footnotes:
        tab += "\n\\par\\smallskip\\footnotesize{" + " ".join(be_footnotes) + "}"
    return latex_table(
        label="tab:routing",
        caption="Simulated metadata routing errors (expected Hit@10; Monte Carlo over per-question oracle lists). Break-even $p$: the error rate at which expected Hit@10 falls to the unfiltered level, interpolated between $p{=}0$ and $p{=}1$ (expected Hit@10 is linear in $p$); \\emph{never}: not below the unfiltered level even at $p{=}1$. The artifact also stores an interpolation over the full $p$ grid, which differs by at most $0.002$.",
        tabular=tab,
        star=True,
    )


def build_per_n_hnsw_tables(track: SourceTracker) -> tuple[dict[str, str], list[str]]:
    openai_eval = load_json(REV1 / "per_n_hnsw_eval_openai.json")
    titan_eval = load_json(REV1 / "per_n_hnsw_eval_titan.json")
    build_openai = load_json(REV1 / "per_n_index_build_openai.json")
    build_titan = load_json(REV1 / "per_n_index_build_titan.json")
    iter_lines = verify_raw_iterative_modes(openai_eval, titan_eval)
    fragments = {
        "tab_perN_recall.tex": build_tab_perN_recall(track, openai_eval, titan_eval),
        "tab_perN_capacity.tex": build_tab_perN_capacity(
            track, openai_eval, titan_eval, build_openai, build_titan
        ),
        "tab_perN_meta.tex": build_tab_perN_meta(track, openai_eval, titan_eval),
        "tab_rrf.tex": build_tab_rrf(track),
        "tab_routing.tex": build_tab_routing(track),
    }
    return fragments, iter_lines


def acceptance_per_n_spot() -> list[tuple[str, bool, str]]:
    blob = load_json(REV1 / "per_n_hnsw_eval_openai.json")
    idx = index_per_n_cells(blob)
    checks = [
        ("raw", 100000, 200, 0.9575, 0.050),
        ("raw", 5000, 200, 0.996, 0.005),
    ]
    out: list[tuple[str, bool, str]] = []
    for cond, scale, ef, exp_r, exp_l in checks:
        cell = per_n_cell(idx, condition=cond, scale_n=scale, ef_search=ef)
        if cell is None:
            out.append((f"perN {scale_k(scale)} ef={ef}", False, "missing cell"))
            continue
        recall, loss, _ = recall_loss_cell(cell, idx=idx)
        ok = abs(recall - exp_r) < 1e-9 and abs(loss - exp_l) < 1e-9
        out.append(
            (
                f"perN OpenAI {cond} @{scale_k(scale)} ef={ef}",
                ok,
                f"recall expected={fmt3(exp_r)} actual={fmt3(recall)}; "
                f"loss expected={fmt3(exp_l)} actual={fmt3(loss)}",
            )
        )
    return out


def acceptance_rrf_routing() -> list[tuple[str, bool, str]]:
    out: list[tuple[str, bool, str]] = []
    rrf = load_json(REV1 / "rrf_hybrid_openai_primary200.json")
    row = [r for r in rrf["by_scale"] if int(r["scale"]) == 100000][0]
    got = float(row["rrf_k60"]["hit_at_10"])
    out.append(
        (
            "RRF 100k Hit@10",
            abs(got - 0.720) < 1e-9,
            f"expected=0.720 actual={fmt3(got)}",
        )
    )
    rt = load_json(REV1 / "routing_simulation_openai_primary200.json")
    compact = rt.get("table_compact") or []
    raw100 = float((rt.get("raw_hit_at_10") or {})["100000"])
    be_s, be = routing_analytic_breakeven(compact, mode="wrong_type", scale=100000, raw_hit=raw100)
    out.append(
        (
            "routing wrong_type break-even @100k (analytic)",
            be is not None and abs(be - 0.120301) < 0.002,
            f"expected~0.120 actual={be_s}",
        )
    )
    return out


def compute_primary400_equiv_extra(track: SourceTracker) -> dict[str, Any]:
    blob = load_json(REV1 / "exact_ladder_openai_primary400.json")
    runs = index_runs(blob)
    order = canonical_question_ids(runs[("raw", 5000)])
    lifts5 = lift_list(runs[("raw", 5000)], runs[("meta_in", 5000)], order)
    lifts100 = lift_list(runs[("raw", 100000)], runs[("meta_in", 100000)], order)
    diffs = [b - a for a, b in zip(lifts5, lifts100)]
    est, lo, hi = bootstrap_paired_mean_ci(diffs, pct=CI90)
    ladder = {
        s: (hit10_list(runs[("raw", s)], order), hit10_list(runs[("meta_in", s)], order))
        for s in [int(x) for x in blob["meta"]["scales"]]
    }
    slope, slo, shi = bootstrap_lift_slope_ci(ladder, pct=CI90)
    track.add("tab_equiv.tex", REV1 / "exact_ladder_openai_primary400.json", ["computed", "lift_change", "slope"])
    return {
        "g_lift_100k_minus_lift_5k_openai_primary400": {
            "estimate": est,
            "ci90_lo": lo,
            "ci90_hi": hi,
            "equivalent_delta_0.05": equivalent_within_delta(lo, hi, 0.05),
            "equivalent_delta_0.10": equivalent_within_delta(lo, hi, 0.10),
            "note": "computed by make_paper_tables.py",
        },
        "h_lift_slope_per_tenfold_openai_primary400": {
            "estimate": slope,
            "ci90_lo": slo,
            "ci90_hi": shi,
            "equivalent_delta_0.05": equivalent_within_delta(slo, shi, 0.05),
            "equivalent_delta_0.10": equivalent_within_delta(slo, shi, 0.10),
            "note": "computed by make_paper_tables.py",
        },
    }


def validate_tex(tex: str, name: str) -> list[str]:
    errs: list[str] = []
    if not re.search(r"\\label\{[^}]+\}", tex):
        errs.append(f"{name}: missing \\label")
    for env in ("table", "table*"):
        n_begin = len(re.findall(rf"\\begin\{{{env}\}}", tex))
        n_end = len(re.findall(rf"\\end\{{{env}\}}", tex))
        if n_begin != n_end:
            errs.append(f"{name}: unbalanced {env} ({n_begin} vs {n_end})")
    return errs


def acceptance_openai_spot() -> list[tuple[str, bool, str]]:
    blob = load_json(REV1 / "exact_ladder_openai_primary200.json")
    runs = index_runs(blob)
    expected = {
        ("raw", 5000): 0.795,
        ("raw", 50000): 0.640,
        ("raw", 100000): 0.585,
        ("meta_in", 5000): 0.875,
        ("meta_in", 50000): 0.715,
        ("meta_in", 100000): 0.665,
    }
    out = []
    for (cond, scale), exp in expected.items():
        got = runs[(cond, scale)]["metrics"]["hit_at_10"]
        ok = abs(got - exp) < 1e-9
        out.append((f"openai {cond} @{scale_k(scale)}", ok, f"expected={fmt3(exp)} actual={fmt3(got)}"))
    return out


def build_tab_fits(track: SourceTracker) -> str:
    ae_path = REV1 / "analysis_exact.json"
    ae = load_json(ae_path)
    computed_rows: set[tuple[str, str, str]] = set()
    rows: list[str] = []
    ladder_cache: dict[str, dict[str, Any]] = {}

    def metric_cells(blob: dict[str, Any], emb: str, bank: str, cond: str, ladder_name: str) -> str:
        fits: dict[str, tuple[dict, dict]] = {}
        for metric in FIT_METRICS:
            fits[metric] = resolve_log_linear_fit(
                ae,
                blob,
                emb=emb,
                bank=bank,
                cond=cond,
                metric=metric,
                ladder_name=ladder_name,
                track=track,
                computed_rows=computed_rows,
            )
        keys = list(FIT_METRICS)
        h1, h10, mrr = keys[0], keys[1], keys[2]
        f1 = fits[h1][0]
        f10, f10n = fits[h10]
        fm = fits[mrr][0]
        return (
            f"{fmt3(f1['slope'])} & {fmt3(f10['slope'])} & {ci_bracket(f10['slope_ci_lo'], f10['slope_ci_hi'])} & "
            f"{fmt3(f10['r2'])} & {fmt3(f10n['slope'])} & {fmt3(fm['slope'])}"
        )

    for arm, emb, bank, ladder_name, conds in FIT_SPECS:
        if ladder_name not in ladder_cache:
            ladder_cache[ladder_name] = load_json(REV1 / ladder_name)
        blob = ladder_cache[ladder_name]
        nlabel = "200" if bank.endswith("200") else "400"
        for cond in conds:
            rows.append(
                f"{arm} $n{{=}}{nlabel}$ & \\texttt{{{cond}}} & "
                f"{metric_cells(blob, emb, bank, cond, ladder_name)} \\\\"
            )

    header = (
        "Arm & Cond. & Hit@1 $b$ & Hit@10 $b$ & Hit@10 95\\% CI & Hit@10 $R^2$ & Hit@10 $b$ w/o 5k & MRR $b$ \\\\"
    )
    foot = ""
    if computed_rows:
        labels = ", ".join(
            f"{e} {b} \\texttt{{{c}}}" for e, b, c in sorted(computed_rows)
        )
        foot = (
            f"\\par\\smallskip\\footnotesize{{Slopes for {labels} "
            f"recomputed in \\texttt{{make\\_paper\\_tables.py}} "
            f"(bootstrap $B{{=}}{BOOT_B}$, seed {BOOT_SEED}).}}"
        )
    tab = (
        "\\begin{tabular}{@{}llrrrrrr@{}}\n\\toprule\n"
        + header
        + "\n\\midrule\n"
        + "\n".join(rows)
        + f"\n\\bottomrule\n\\end{{tabular}}\n{foot}"
    )
    return latex_table(
        label="tab:fits",
        caption=(
            "Log-linear fits $\\mathrm{Hit@}k(N)\\approx a+b\\ln N$ (natural log; negative $b$ is decline). "
            f"Bootstrap 95\\% CIs resample questions ($B{{=}}{BOOT_B}$, seed {BOOT_SEED}). "
            "``w/o 5k'' uses eight scales excluding $N{=}5\\text{k}$. Slopes for Hit@1 and MRR are over all nine sizes."
        ),
        tabular=tab,
        star=True,
    )


def _by_type_hit_rates(blob: dict[str, Any], *, cond: str = "raw") -> dict[str, dict[str, Any]]:
    runs = index_runs(blob)
    by_scale: dict[int, dict[str, list[dict[str, Any]]]] = {}
    for scale in (5000, 100000):
        by_qtype: dict[str, list[dict[str, Any]]] = {}
        for p in runs[(cond, scale)]["per_question"]:
            by_qtype.setdefault(question_type_of(p["question_id"]), []).append(p)
        by_scale[scale] = by_qtype
    counts = {t: len(by_scale[5000].get(t, [])) for t in QUESTION_TYPE_ORDER}
    rows: dict[str, dict[str, Any]] = {}
    for t in QUESTION_TYPE_ORDER:
        p5 = by_scale[5000].get(t, [])
        p100 = by_scale[100000].get(t, [])
        if not p5 and not p100:
            continue
        rows[t] = {
            "n": counts[t],
            "hit_at_1_5k": float(np.mean([hit_flag(x["hit_at_1"]) for x in p5])) if p5 else None,
            "hit_at_10_5k": float(np.mean([hit_flag(x["hit_at_10"]) for x in p5])) if p5 else None,
            "hit_at_1_100k": float(np.mean([hit_flag(x["hit_at_1"]) for x in p100])) if p100 else None,
            "hit_at_10_100k": float(np.mean([hit_flag(x["hit_at_10"]) for x in p100])) if p100 else None,
        }
    return rows


def build_tab_bytype_exact(
    *,
    embedder_label: str,
    ladder_name: str,
    fragment: str,
    label: str,
    track: SourceTracker,
) -> str:
    path = REV1 / ladder_name
    blob = load_json(path)
    track.add(fragment, path, ["runs", "raw", "per_question"])
    data = _by_type_hit_rates(blob, cond="raw")
    body: list[str] = []
    for t in QUESTION_TYPE_ORDER:
        if t not in data:
            continue
        row = data[t]
        name = TYPE_TEX[t]
        if row["n"] < 20:
            name = f"{name}$^{{\\ast}}$"
        body.append(
            f"{name} & {row['n']} & {fmt3(row['hit_at_1_5k'])} & {fmt3(row['hit_at_10_5k'])} & "
            f"{fmt3(row['hit_at_1_100k'])} & {fmt3(row['hit_at_10_100k'])} \\\\"
        )
    tab = (
        "\\begin{tabular}{@{}lrrrrr@{}}\n\\toprule\n"
        "Type & $n$ & H@1$_{5\\mathrm{k}}$ & H@10$_{5\\mathrm{k}}$ & "
        "H@1$_{100\\mathrm{k}}$ & H@10$_{100\\mathrm{k}}$ \\\\\n\\midrule\n"
        + "\n".join(body)
        + "\n\\bottomrule\n\\end{tabular}\n"
        "\\par\\smallskip\\footnotesize{$^{\\ast}$Exploratory ($n{<}20$); not used for primary type-level claims.}"
    )
    return latex_table(
        label=label,
        caption=(
            f"{embedder_label} exact search (primary-200, raw): Hit@$k$ by \\texttt{{question\\_type}} "
            "at ladder endpoints."
        ),
        tabular=tab,
    )


def compute_gold_rank_stats(blob: dict[str, Any], *, cond: str = "raw") -> dict[str, Any]:
    runs = index_runs(blob)
    out: dict[str, Any] = {}
    for scale in (5000, 100000):
        pq = runs[(cond, scale)]["per_question"]
        misses = sum(1 for p in pq if not hit_flag(p["hit_at_10"]))
        ranks = [float(p["rank"]) for p in pq if hit_flag(p["hit_at_10"]) and p.get("rank") is not None]
        out[str(scale)] = {
            "n_miss_hit10": int(misses),
            "mean_gold_rank_among_hit10_successes": float(np.mean(ranks)) if ranks else None,
        }
    m5 = runs[(cond, 5000)]["metrics"]
    m100 = runs[(cond, 100000)]["metrics"]

    def rel_loss(key: str) -> float | None:
        v5 = float(m5[key])
        v100 = float(m100[key])
        if v5 == 0.0:
            return None
        return float((1.0 - v100 / v5) * 100.0)

    out["relative_loss_pct_100k_vs_5k"] = {
        "hit_at_1": rel_loss("hit_at_1"),
        "hit_at_10": rel_loss("hit_at_10"),
        "mrr": rel_loss("mrr"),
    }
    out["metrics_5k"] = {k: float(m5[k]) for k in ("hit_at_1", "hit_at_10", "mrr")}
    out["metrics_100k"] = {k: float(m100[k]) for k in ("hit_at_1", "hit_at_10", "mrr")}
    return out


def acceptance_bytype_openai() -> list[tuple[str, bool, str]]:
    blob = load_json(REV1 / "exact_ladder_openai_primary200.json")
    data = _by_type_hit_rates(blob, cond="raw")
    total_n = sum(data[t]["n"] for t in QUESTION_TYPE_ORDER if t in data)
    ok_n = total_n == 200

    def weighted_hit10(scale_key: str, field: str, expected: float) -> tuple[str, bool, str]:
        num = sum(data[t]["n"] * data[t][field] for t in data)
        den = sum(data[t]["n"] for t in data)
        got = num / den if den else float("nan")
        ok = abs(got - expected) < 1e-9
        return (
            f"bytype weighted {scale_key}",
            ok,
            f"expected={fmt3(expected)} actual={fmt3(got)}",
        )

    out = [
        (
            "bytype count sum",
            ok_n,
            f"expected=200 actual={total_n}",
        ),
        weighted_hit10("5k", "hit_at_10_5k", 0.795),
        weighted_hit10("100k", "hit_at_10_100k", 0.585),
    ]
    return out


def build_tab_pool(track: SourceTracker) -> str:
    """Source composition of the round-robin ladder (counts include gold anchors)."""
    path = ROOT / "data" / "erb_scale_manifest.json"
    manifest = load_json(path)
    docs = manifest["documents"]
    sources = sorted({d["source_type"] for d in docs})
    scales = [5000, 25000, 50000, 75000, 100000]
    pool = {s_: sum(1 for d in docs if d["source_type"] == s_) for s_ in sources}
    cols = {n: {s_: sum(1 for d in docs if d["source_type"] == s_ and d["scale_rank"] < n) for s_ in sources} for n in scales}
    track.add("tab_pool.tex", path, ["documents.source_type", "documents.scale_rank"])
    head = " & ".join(f"{n // 1000}k" for n in scales)
    lines = [
        "\\begin{table}[t]",
        "\\centering",
        "\\small",
        "\\fitcolumn{\\begin{tabular}{@{}lr" + "r" * len(scales) + "@{}}",
        "\\toprule",
        f"Source & Pool & {head} \\\\",
        "\\midrule",
    ]
    for s_ in sources:
        cells = " & ".join(f"{100.0 * cols[n][s_] / n:.1f}" for n in scales)
        name = s_.replace("_", "\\_")
        lines.append(f"\\texttt{{{name}}} & {pool[s_]:,} & {cells} \\\\")
    lines += [
        "\\midrule",
        f"Total & {len(docs):,} & " + " & ".join("100" for _ in scales) + " \\\\",
        "\\bottomrule",
        "\\end{tabular}}",
        (
            "\\caption{Composition (\\% of the corpus, gold anchors included) of the $99{,}998$ embedded "
            "documents at each ladder size under the round-robin schedule; "
            "document counts per source are in Table~\\ref{tab:poolcounts}; the ``Pool'' column is the number of documents extracted per source "
            f"({len(docs):,} in total).}}"
        ),
        "\\label{tab:pool}",
        "\\end{table}",
        "",
    ]
    tex_pool = "\n".join(lines)
    m_cap = re.search(r"(\\caption\{.*?\}\n\\label\{tab:pool\}\n)", tex_pool, re.S)
    if m_cap:  # IEEE convention: table captions above the table
        tex_pool = tex_pool.replace(m_cap.group(1), "")
        tex_pool = tex_pool.replace("\\begin{table}[t]\n", "\\begin{table}[t]\n" + m_cap.group(1), 1)
    return tex_pool


def escape_texttt_underscores(tex: str) -> str:
    """Escape bare underscores inside \\texttt{...} (math-mode errors otherwise)."""
    import re

    def repl(m: "re.Match[str]") -> str:
        inner = re.sub(r"(?<!\\\\)_", r"\\_", m.group(1))
        return "\\texttt{" + inner + "}"

    return re.sub(r"\\texttt\{([^{}]*)\}", repl, tex)


def build_tab_rrf_sens(track: SourceTracker) -> str:
    """R1.4: RRF sensitivity to k and to the dense weight w (rrf_sensitivity.py)."""
    path = REV1 / "rrf_sensitivity_openai_primary200.json"
    data = load_json(path)
    track.add("tab_rrf_sens.tex", path, ["cells"])
    cells = {(int(c["k"]), float(c["w_dense"])): c for c in data["cells"]}
    ks = (1, 10, 60, 200)
    ws = (0.25, 0.4, 0.5, 0.6, 0.75)
    rows = []
    for w in ws:
        out = [f"{w:.2f}"]
        for k in ks:
            c = cells[(k, w)]
            out.append(f"{c['hit10_by_scale']['100000']:.3f} / {c['hit10_drop']['estimate']:.3f}")
        rows.append(" & ".join(out) + " \\\\")
    dense = cells[(60, 1.0)]
    bm25 = cells[(60, 0.0)]
    any_excl = [
        (k, w) for (k, w), c in cells.items()
        if 0.0 < w < 1.0 and (c["drop_minus_dense_drop_hit10"]["ci_lo"] > 0 or c["drop_minus_dense_drop_hit10"]["ci_hi"] < 0)
    ]
    note = ("no fused setting has a drop whose paired 95\\% interval of the difference from the dense drop excludes zero"
            if not any_excl else f"{len(any_excl)} fused settings have a drop difference from dense whose interval excludes zero")
    tab = (
        "\\begin{tabular}{l" + "c" * len(ks) + "}\n\\toprule\n"
        + "Dense weight $w$ & " + " & ".join(f"$k{{=}}{k}$" for k in ks) + " \\\\\n\\midrule\n"
        + "\n".join(rows)
        + "\n\\bottomrule\n\\end{tabular}"
    )
    return latex_table(
        label="tab:rrfsens",
        caption=(
            "Weighted reciprocal rank fusion, $2[w/(k+r_{\\mathrm{dense}})+(1-w)/(k+r_{\\mathrm{BM25}})]$, on primary-200 "
            "(exact dense top-100 and BM25 \\texttt{dense\\_text} top-100). Each cell gives Hit@10 at $100$k / Hit@10 drop "
            f"from $5$k to $100$k. Dense alone: {dense['hit10_by_scale']['100000']:.3f} / {dense['hit10_drop']['estimate']:.3f}; "
            f"BM25 alone: {bm25['hit10_by_scale']['100000']:.3f} / {bm25['hit10_drop']['estimate']:.3f}. "
            f"The grid is evaluated on the test bank itself (in-sample), and {note}."
        ),
        tabular=tab,
        star=False,
    )


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    per_n_fragments, per_n_iter_lines = build_per_n_hnsw_tables(SOURCES)
    extra_equiv = compute_primary400_equiv_extra(SOURCES)

    openai200 = load_json(REV1 / "exact_ladder_openai_primary200.json")
    titan200 = load_json(REV1 / "exact_ladder_titan_primary200.json")
    stats_payload = {
        "openai_primary200_raw": compute_gold_rank_stats(openai200, cond="raw"),
        "titan_primary200_raw": compute_gold_rank_stats(titan200, cond="raw"),
    }

    fragments = {
        "tab_exact_openai.tex": build_tab_exact_openai(SOURCES),
        "tab_exact_titan.tex": build_tab_exact_titan(SOURCES),
        "tab_exact_n400.tex": build_tab_exact_n400(SOURCES),
        "tab_exact_n400_full.tex": build_tab_exact_n400_full(SOURCES),
        "tab_drift_summary.tex": build_tab_drift_summary(SOURCES),
        "tab_lift.tex": build_tab_lift(SOURCES),
        "tab_equiv.tex": build_tab_equiv(SOURCES, extra_equiv),
        "tab_equiv_full.tex": build_tab_equiv_full(SOURCES, extra_equiv),
        "tab_bm25.tex": build_tab_bm25(SOURCES),
        "tab_doclen.tex": build_tab_doclen(SOURCES),
        "tab_pool.tex": build_tab_pool(SOURCES),
        "tab_plan_audit.tex": build_tab_plan_audit(SOURCES),
        "tab_rrf_sens.tex": build_tab_rrf_sens(SOURCES),
        "tab_old_vs_exact.tex": build_tab_old_vs_exact(SOURCES),
        "tab_ef_planner.tex": build_tab_ef_planner(SOURCES),
        "tab_fits.tex": build_tab_fits(SOURCES),
        "tab_bytype_exact.tex": build_tab_bytype_exact(
            embedder_label="OpenAI",
            ladder_name="exact_ladder_openai_primary200.json",
            fragment="tab_bytype_exact.tex",
            label="tab:bytype",
            track=SOURCES,
        ),
        "tab_bytype_exact_titan.tex": build_tab_bytype_exact(
            embedder_label="Titan",
            ladder_name="exact_ladder_titan_primary200.json",
            fragment="tab_bytype_exact_titan.tex",
            label="tab:bytype_titan",
            track=SOURCES,
        ),
        **per_n_fragments,
    }

    validation_errors: list[str] = []
    for name, content in fragments.items():
        path = OUT / name
        content = escape_texttt_underscores(content).replace("\\\\_", "\\_")
        path.write_text(content, encoding="utf-8")
        validation_errors.extend(validate_tex(content, name))

    readme_lines = [
        "| Fragment | Question answered |",
        "|---|---|",
    ]
    descriptions = {
        "tab_exact_openai.tex": "OpenAI exact ladder (n=200) full metric grid.",
        "tab_exact_titan.tex": "Titan exact ladder (n=200) full metric grid.",
        "tab_exact_n400.tex": "OpenAI n=400 exact ladder at 5k/50k/100k.",
        "tab_exact_n400_full.tex": "OpenAI n=400 exact ladder all scales (appendix).",
        "tab_drift_summary.tex": "Hit@10 drift 5k→100k with paired CIs.",
        "tab_lift.tex": "Metadata lift by scale, change, and log-slope.",
        "tab_equiv.tex": "Equivalence quantities (compact, in the paper).",
        "tab_equiv_full.tex": "All equivalence quantities (not in the paper).",
        "tab_bm25.tex": "BM25 truncation variants vs dense exact.",
        "tab_doclen.tex": "Corpus and gold document length stats.",
        "tab_pool.tex": "Pool size and source composition per ladder size (round-robin).",
        "tab_plan_audit.tex": "HNSW plan share by embedder, condition, PG port and ef_search.",
        "tab_rrf_sens.tex": "RRF sensitivity to k and dense weight (R1.4).",
        "tab_old_vs_exact.tex": "Published HNSW vs exact Hit@10.",
        "tab_ef_planner.tex": "ef_search planner sweep at 100k (E2).",
        "tab_fits.tex": "Log-linear scale slopes (raw/meta_in) with bootstrap CIs.",
        "tab_bytype_exact.tex": "Hit@k by question type at 5k/100k (OpenAI raw).",
        "tab_bytype_exact_titan.tex": "Hit@k by question type at 5k/100k (Titan raw).",
        "tab_perN_recall.tex": "Per-N HNSW recall and Hit@10 loss (OpenAI/Titan raw).",
        "tab_perN_capacity.tex": "Per-N table/index size and query latency.",
        "tab_perN_meta.tex": "Metadata-filtered per-N HNSW recall/loss and plans.",
        "tab_rrf.tex": "Dense/BM25/RRF hybrid metrics with CIs.",
        "tab_routing.tex": "Wrong-routing simulation Hit@10 vs error rate.",
    }
    for fn, desc in descriptions.items():
        readme_lines.append(f"| `{fn}` | {desc} |")
    (OUT / "README.md").write_text("\n".join(readme_lines) + "\n", encoding="utf-8")

    sources_path = OUT / "_sources.json"
    sources_path.write_text(
        json.dumps({"fragments": SOURCES.fragments, "generator": "make_paper_tables.py"}, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    stats_path = OUT / "_stats.json"
    stats_path.write_text(json.dumps(stats_payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    # Self-check report to stdout
    print("=== make_paper_tables.py ===")
    for name in sorted(fragments):
        print(f"Wrote {OUT / name}")
    print("\n--- Acceptance (a) determinism ---")
    print("Run script twice and `cmp` fragment files (see reproduction commands).")
    print("\n--- Acceptance (b) OpenAI Hit@10 spot checks ---")
    for label, ok, detail in acceptance_openai_spot():
        print(f"  {'PASS' if ok else 'FAIL'}: {label} — {detail}")
    print("\n--- Acceptance (d) by-type OpenAI (n=200, weighted Hit@10) ---")
    for label, ok, detail in acceptance_bytype_openai():
        print(f"  {'PASS' if ok else 'FAIL'}: {label} — {detail}")
    print("\n--- Per-N HNSW iterative_scan check (raw) ---")
    for line in per_n_iter_lines:
        print(f"  {line}")
    print("\n--- Acceptance (e) per-N / RRF / routing spot checks ---")
    for label, ok, detail in acceptance_per_n_spot() + acceptance_rrf_routing():
        print(f"  {'PASS' if ok else 'FAIL'}: {label} — {detail}")
    print("\n--- Gold-rank / miss stats (primary-200 raw; also in _stats.json) ---")
    for arm, key in (("OpenAI", "openai_primary200_raw"), ("Titan", "titan_primary200_raw")):
        st = stats_payload[key]
        print(
            f"  {arm}: misses Hit@10 5k={st['5000']['n_miss_hit10']} "
            f"100k={st['100000']['n_miss_hit10']}; "
            f"mean gold rank (successes) 5k={fmt3(st['5000']['mean_gold_rank_among_hit10_successes'])} "
            f"100k={fmt3(st['100000']['mean_gold_rank_among_hit10_successes'])}; "
            f"rel. loss % H@1/H@10/MRR="
            f"{fmt3(st['relative_loss_pct_100k_vs_5k']['hit_at_1'])}/"
            f"{fmt3(st['relative_loss_pct_100k_vs_5k']['hit_at_10'])}/"
            f"{fmt3(st['relative_loss_pct_100k_vs_5k']['mrr'])}"
        )
    print("\n--- Acceptance (c) LaTeX self-check ---")
    if validation_errors:
        for e in validation_errors:
            print(f"  FAIL: {e}")
    else:
        print("  PASS: all fragments have balanced table envs and \\label")
    print("\n--- Notes ---")
    print("  primary400 drift row uses bootstrap recomputation (analysis_exact cross_embedder skipped).")
    print("  Titan old ladder uses runs_with_per_question; condition raw vs exact raw.")
    print("  W12d per-N HNSW / RRF / routing tables emitted (tab_perN_*, tab_rrf, tab_routing).")
    return 1 if validation_errors else 0


if __name__ == "__main__":
    sys.exit(main())
