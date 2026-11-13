#!/usr/bin/env python3
"""Regenerate revision-1 paper figures from exact-search ladder artifacts (no plotting deps).

Writes SVG to artifacts/published/revision1/paper_figures/. PDF/PNG via headless Chrome
is optional (skipped when SKIP_CHROME_RENDER=1).

Usage:
  <repo>/.venv/bin/python \
    scripts/erb/revision1/make_paper_figures_rev1.py
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

try:
    import numpy as np
except ImportError:  # pragma: no cover
    np = None  # type: ignore

ROOT = Path(__file__).resolve().parents[3]
REV1 = ROOT / "artifacts" / "published" / "revision1"
OUT = REV1 / "paper_figures"
CHROME = Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")

W, H = 262, 188
ML, MR, MT, MB = 40, 10, 10, 34
FONT = "Times New Roman, Times, serif"
BLUE, ORANGE, GREEN, GREY, PURPLE = "#1f5fa8", "#d9730d", "#2e8b57", "#555555", "#6a3d9a"
LADDER = [5000, 10000, 15000, 20000, 25000, 40000, 50000, 75000, 100000]
TICKS = [5000, 10000, 20000, 50000, 100000]
BOOT_B = 10_000
BOOT_SEED = 42
TAU = 0.10
_BOOT_IDX: dict[int, Any] = {}


def _boot_idx(n: int):
    if n not in _BOOT_IDX:
        if np is None:
            raise RuntimeError("numpy required for bootstrap indices")
        rng = np.random.default_rng(BOOT_SEED)
        _BOOT_IDX[n] = rng.integers(0, n, size=(BOOT_B, n))
    return _BOOT_IDX[n]


def _sorted_hit_flags(run: dict) -> list[bool]:
    pq = sorted(run["per_question"], key=lambda p: p["question_id"])
    return [bool(p["hit_at_10"]) for p in pq]


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _runs_by_key(payload: dict) -> dict[tuple[str, int], dict]:
    return {(r["condition"], r["scale"]): r for r in payload["runs"]}


def _bm25_by_scale(payload: dict) -> dict[int, dict]:
    return {r["corpus_scale_size"]: r for r in payload["runs"]}


def _metric(run: dict, key: str = "hit_at_10") -> float:
    return float(run["metrics"][key])


def _hit_flags(run: dict) -> list[bool]:
    return [bool(q["hit_at_10"]) for q in run["per_question"]]


def _bootstrap_mean_ci(flags: list[bool], *, seed: int = BOOT_SEED) -> tuple[float, float, float]:
    arr = [1.0 if f else 0.0 for f in flags]
    n = len(arr)
    if np is not None:
        idx = _boot_idx(n) if seed == BOOT_SEED else np.random.default_rng(seed).integers(0, n, size=(BOOT_B, n))
        samples = arr_np_mean(idx, arr)
        lo, hi = np.percentile(samples, [2.5, 97.5])
        return float(sum(arr) / n), float(lo), float(hi)
    import random

    rng = random.Random(seed)
    samples: list[float] = []
    for _ in range(BOOT_B):
        tot = sum(arr[rng.randrange(n)] for _ in range(n))
        samples.append(tot / n)
    samples.sort()
    lo = samples[int(0.025 * BOOT_B)]
    hi = samples[int(0.975 * BOOT_B) - 1]
    return sum(arr) / n, lo, hi


def arr_np_mean(idx, arr):
    a = np.asarray(arr, dtype=np.float64)
    return a[idx].mean(axis=1)


def _paired_lift_ci(
    meta_flags: list[bool],
    raw_flags: list[bool],
    *,
    seed: int = BOOT_SEED,
) -> tuple[float, float, float]:
    if len(meta_flags) != len(raw_flags):
        raise ValueError("paired lift: mismatched question counts")
    n = len(meta_flags)
    meta = [1.0 if f else 0.0 for f in meta_flags]
    raw = [1.0 if f else 0.0 for f in raw_flags]
    point = sum(m - r for m, r in zip(meta, raw)) / n
    if np is not None:
        idx = _boot_idx(n) if seed == BOOT_SEED else np.random.default_rng(seed).integers(0, n, size=(BOOT_B, n))
        m_s = meta_np(idx, meta)
        r_s = raw_np(idx, raw)
        deltas = m_s - r_s
        lo, hi = np.percentile(deltas, [2.5, 97.5])
        return point, float(lo), float(hi)
    import random

    rng = random.Random(seed)
    samples: list[float] = []
    for _ in range(BOOT_B):
        dm = dr = 0.0
        for _ in range(n):
            j = rng.randrange(n)
            dm += meta[j]
            dr += raw[j]
        samples.append(dm / n - dr / n)
    samples.sort()
    lo = samples[int(0.025 * BOOT_B)]
    hi = samples[int(0.975 * BOOT_B) - 1]
    return point, lo, hi


def meta_np(idx, meta):
    a = np.asarray(meta, dtype=np.float64)
    return a[idx].mean(axis=1)


def raw_np(idx, raw):
    a = np.asarray(raw, dtype=np.float64)
    return a[idx].mean(axis=1)


class Plot:
    def __init__(
        self,
        ylo: float,
        yhi: float,
        ystep: float,
        ylabel: str,
        *,
        xlabel: str = "Corpus size N",
    ) -> None:
        self.ylo, self.yhi, self.ystep, self.ylabel = ylo, yhi, ystep, ylabel
        self.xlabel = xlabel
        self.xlo, self.xhi = math.log(4500), math.log(110000)
        self.parts: list[str] = []

    def x(self, n: float) -> float:
        return ML + (math.log(n) - self.xlo) / (self.xhi - self.xlo) * (W - ML - MR)

    def y(self, v: float) -> float:
        return MT + (self.yhi - v) / (self.yhi - self.ylo) * (H - MT - MB)

    def axes(self) -> None:
        p = self.parts
        v = self.ylo
        while v <= self.yhi + 1e-9:
            yy = self.y(v)
            p.append(
                f'<line x1="{ML}" x2="{W - MR}" y1="{yy:.1f}" y2="{yy:.1f}" '
                f'stroke="#e3e3e3" stroke-width="0.6"/>'
            )
            p.append(f'<text x="{ML - 4}" y="{yy + 3:.1f}" font-size="9" text-anchor="end">{v:.2f}</text>')
            v += self.ystep
        for n in TICKS:
            xx = self.x(n)
            p.append(
                f'<line x1="{xx:.1f}" x2="{xx:.1f}" y1="{H - MB}" y2="{H - MB + 3}" '
                f'stroke="#000" stroke-width="0.6"/>'
            )
            p.append(f'<text x="{xx:.1f}" y="{H - MB + 13}" font-size="9" text-anchor="middle">{n // 1000}k</text>')
        p.append(f'<line x1="{ML}" x2="{W - MR}" y1="{H - MB}" y2="{H - MB}" stroke="#000" stroke-width="0.8"/>')
        p.append(f'<line x1="{ML}" x2="{ML}" y1="{MT}" y2="{H - MB}" stroke="#000" stroke-width="0.8"/>')
        p.append(
            f'<text x="{(ML + W - MR) / 2:.1f}" y="{H - 4}" font-size="9.5" text-anchor="middle">{self.xlabel}</text>'
        )
        cy = (MT + H - MB) / 2
        p.append(
            f'<text x="11" y="{cy:.1f}" font-size="9.5" text-anchor="middle" '
            f'transform="rotate(-90 11 {cy:.1f})">{self.ylabel}</text>'
        )

    def band(self, pts: list[tuple[int, float, float]], color: str) -> None:
        up = " ".join(f"{self.x(n):.1f},{self.y(hi):.1f}" for n, _, hi in pts)
        dn = " ".join(f"{self.x(n):.1f},{self.y(lo):.1f}" for n, lo, _ in reversed(pts))
        self.parts.append(f'<polygon points="{up} {dn}" fill="{color}" fill-opacity="0.15" stroke="none"/>')

    def line(
        self,
        pts: list[tuple[float, float]],
        color: str,
        *,
        dash: str = "",
        marker: str = "circle",
        xoff: float = 0.0,
    ) -> None:
        d = " ".join(f"{self.x(n) + xoff:.1f},{self.y(v):.1f}" for n, v in pts)
        dash_attr = f' stroke-dasharray="{dash}"' if dash else ""
        self.parts.append(f'<polyline points="{d}" fill="none" stroke="{color}" stroke-width="1.4"{dash_attr}/>')
        for n, v in pts if marker else []:
            xx, yy = self.x(n) + xoff, self.y(v)
            if marker == "square":
                self.parts.append(f'<rect x="{xx - 2.4:.1f}" y="{yy - 2.4:.1f}" width="4.8" height="4.8" fill="{color}"/>')
            elif marker == "triangle":
                self.parts.append(
                    f'<polygon points="{xx:.1f},{yy - 3:.1f} {xx - 2.8:.1f},{yy + 2.2:.1f} '
                    f'{xx + 2.8:.1f},{yy + 2.2:.1f}" fill="{color}"/>'
                )
            else:
                self.parts.append(f'<circle cx="{xx:.1f}" cy="{yy:.1f}" r="2.3" fill="{color}"/>')

    def errorbar(
        self,
        n: int,
        v: float,
        lo: float,
        hi: float,
        color: str,
        *,
        xoff: float = 0.0,
        marker: str = "circle",
    ) -> None:
        xx = self.x(n) + xoff
        yc, ylo, yhi = self.y(v), self.y(lo), self.y(hi)
        cap = 3.0
        self.parts.append(f'<line x1="{xx:.1f}" x2="{xx:.1f}" y1="{ylo:.1f}" y2="{yhi:.1f}" stroke="{color}" stroke-width="1.1"/>')
        self.parts.append(
            f'<line x1="{xx - cap:.1f}" x2="{xx + cap:.1f}" y1="{ylo:.1f}" y2="{ylo:.1f}" '
            f'stroke="{color}" stroke-width="1.1"/>'
        )
        self.parts.append(
            f'<line x1="{xx - cap:.1f}" x2="{xx + cap:.1f}" y1="{yhi:.1f}" y2="{yhi:.1f}" '
            f'stroke="{color}" stroke-width="1.1"/>'
        )
        if marker == "square":
            self.parts.append(f'<rect x="{xx - 2.4:.1f}" y="{yc - 2.4:.1f}" width="4.8" height="4.8" fill="{color}"/>')
        elif marker == "triangle":
            self.parts.append(
                f'<polygon points="{xx:.1f},{yc - 3:.1f} {xx - 2.8:.1f},{yc + 2.2:.1f} '
                f'{xx + 2.8:.1f},{yc + 2.2:.1f}" fill="{color}"/>'
            )
        else:
            self.parts.append(f'<circle cx="{xx:.1f}" cy="{yc:.1f}" r="2.3" fill="{color}"/>')

    def hline(self, v: float, color: str, *, dash: str = "", width: float = 0.9) -> None:
        yy = self.y(v)
        dash_attr = f' stroke-dasharray="{dash}"' if dash else ""
        self.parts.append(
            f'<line x1="{ML}" x2="{W - MR}" y1="{yy:.1f}" y2="{yy:.1f}" stroke="{color}" '
            f'stroke-width="{width}"{dash_attr}/>'
        )

    def fit_log_linear(self, intercept: float, slope: float, color: str) -> None:
        pts = [(n, intercept + slope * math.log(n)) for n in (5000, 100000)]
        self.line(pts, color, dash="4 3", marker="")

    def legend(self, items: list[tuple], *, x: float, y: float) -> None:
        for i, item in enumerate(items):
            label, color, dash = item[0], item[1], item[2]
            marker = item[3] if len(item) > 3 else ""
            yy = y + i * 11
            dash_attr = f' stroke-dasharray="{dash}"' if dash else ""
            self.parts.append(
                f'<line x1="{x}" x2="{x + 16}" y1="{yy}" y2="{yy}" stroke="{color}" '
                f'stroke-width="1.4"{dash_attr}/>'
            )
            mx = x + 8
            if marker == "square":
                self.parts.append(f'<rect x="{mx - 2.4}" y="{yy - 2.4}" width="4.8" height="4.8" fill="{color}"/>')
            elif marker == "triangle":
                self.parts.append(f'<polygon points="{mx},{yy - 3} {mx - 3},{yy + 2.4} {mx + 3},{yy + 2.4}" fill="{color}"/>')
            self.parts.append(f'<text x="{x + 20}" y="{yy + 3}" font-size="9">{label}</text>')

    def svg(self) -> str:
        body = "\n".join(self.parts)
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
            f'font-family="{FONT}">\n<rect width="{W}" height="{H}" fill="#fff"/>\n{body}\n</svg>\n'
        )


def fig1_exact_hit_vs_logN(openai200: dict, analysis: dict) -> tuple[str, list[dict]]:
    runs = _runs_by_key(openai200)
    coef = analysis["log_linear"]["openai"]["primary200"]["raw"]["hit_at_10"]["all_scales"]
    intercept, slope = float(coef["intercept"]), float(coef["slope"])

    band_pts: list[tuple[int, float, float]] = []
    plotted: list[dict] = []
    for n in LADDER:
        raw_run = runs[("raw", n)]
        mean, lo, hi = _bootstrap_mean_ci(_sorted_hit_flags(raw_run), seed=BOOT_SEED)
        band_pts.append((n, lo, hi))
        raw_h10 = _metric(raw_run)
        meta_h10 = _metric(runs[("meta_in", n)])
        raw_h1 = _metric(raw_run, "hit_at_1")
        plotted.append(
            {
                "N": n,
                "raw_hit_at_10": raw_h10,
                "meta_in_hit_at_10": meta_h10,
                "raw_hit_at_1": raw_h1,
                "bootstrap_hit_at_10_lo": lo,
                "bootstrap_hit_at_10_hi": hi,
            }
        )

    p = Plot(0.25, 1.05, 0.10, "Hit@k")
    p.axes()
    p.band(band_pts, BLUE)
    p.line([(n, d["meta_in_hit_at_10"]) for n, d in zip(LADDER, plotted)], ORANGE, marker="square")
    p.line([(n, d["raw_hit_at_10"]) for n, d in zip(LADDER, plotted)], BLUE)
    p.fit_log_linear(intercept, slope, BLUE)
    p.line([(n, d["raw_hit_at_1"]) for n, d in zip(LADDER, plotted)], GREEN, marker="triangle")
    p.legend([("meta_in Hit@10", ORANGE, "", "square"), ("raw Hit@1", GREEN, "", "triangle")], x=ML + 8, y=MT + 8)
    p.legend([("raw Hit@10", BLUE, ""), ("log-linear fit", BLUE, "4 3")], x=ML + 112, y=MT + 8)
    return p.svg(), plotted


def _lift_series(payload: dict) -> list[dict]:
    runs = _runs_by_key(payload)
    out: list[dict] = []
    for n in LADDER:
        meta = runs[("meta_in", n)]
        raw = runs[("raw", n)]
        delta, lo, hi = _paired_lift_ci(_sorted_hit_flags(meta), _sorted_hit_flags(raw), seed=BOOT_SEED)
        out.append({"N": n, "lift": delta, "ci_lo": lo, "ci_hi": hi})
    return out


def fig2_exact_lift(openai200: dict, titan200: dict, openai400: dict) -> tuple[str, list[dict]]:
    series = [
        ("OpenAI primary200", _lift_series(openai200), BLUE, -5.0, "circle"),
        ("Titan primary200", _lift_series(titan200), ORANGE, 0.0, "square"),
        ("OpenAI primary400", _lift_series(openai400), GREEN, 5.0, "triangle"),
    ]
    p = Plot(-0.05, 0.25, 0.05, "Δmeta (Hit@10)")
    p.axes()
    p.hline(0.0, "#000", width=0.8)
    p.hline(TAU, GREY, dash="2 2")
    yy = p.y(TAU)
    p.parts.append(
        f'<text x="{W - MR - 2}" y="{yy - 3:.1f}" font-size="8.5" text-anchor="end" fill="{GREY}">τ = {TAU:.2f}</text>'
    )
    plotted: list[dict] = []
    for label, pts, color, xoff, marker in series:
        for row in pts:
            p.errorbar(row["N"], row["lift"], row["ci_lo"], row["ci_hi"], color, xoff=xoff, marker=marker)
            plotted.append({"series": label, **row})
        d = " ".join(f"{p.x(r['N']) + xoff:.1f},{p.y(r['lift']):.1f}" for r in pts)
        p.parts.append(f'<polyline points="{d}" fill="none" stroke="{color}" stroke-width="1.4"/>')
    p.legend(
        [
            ("OpenAI, n=200", BLUE, ""),
            ("Titan V2, n=200", ORANGE, ""),
            ("OpenAI, n=400", GREEN, ""),
        ],
        x=ML + 8,
        y=p.y(0.245),
    )
    return p.svg(), plotted


def fig3_bm25_vs_dense(openai200: dict, titan200: dict, bm25_dense: dict, bm25_4k: dict) -> tuple[str, list[dict]]:
    oa = _runs_by_key(openai200)
    ti = _runs_by_key(titan200)
    b_dense = _bm25_by_scale(bm25_dense)
    b_4k = _bm25_by_scale(bm25_4k)

    plotted: list[dict] = []
    for n in LADDER:
        plotted.append(
            {
                "N": n,
                "openai_exact": _metric(oa[("raw", n)]),
                "titan_exact": _metric(ti[("raw", n)]),
                "bm25_dense_text": float(b_dense[n]["hit_at_10"]),
                "bm25_chars4000": float(b_4k[n]["hit_at_10"]),
            }
        )

    p = Plot(0.35, 0.90, 0.05, "Hit@10")
    p.axes()
    p.line([(r["N"], r["openai_exact"]) for r in plotted], BLUE)
    p.line([(r["N"], r["titan_exact"]) for r in plotted], ORANGE, marker="square")
    p.line([(r["N"], r["bm25_dense_text"]) for r in plotted], GREEN, marker="triangle")
    p.line([(r["N"], r["bm25_chars4000"]) for r in plotted], GREY, dash="3 2", marker="")
    p.legend(
        [
            ("dense exact OpenAI", BLUE, ""),
            ("dense exact Titan", ORANGE, ""),
            ("BM25 (dense_text)", GREEN, ""),
            ("BM25 legacy 4000 chars", GREY, "3 2"),
        ],
        x=ML + 118,
        y=MT + 18,
    )
    return p.svg(), plotted


def _per_n_loss_series(eval_json: dict[str, Any], *, ef: int) -> list[tuple[int, float]]:
    as_planned: dict[int, dict[str, Any]] = {}
    twins: dict[int, dict[str, Any]] = {}
    for c in eval_json.get("cells") or []:
        if c.get("condition") != "raw":
            continue
        if int(c.get("max_scan_tuples") or 20000) != 20000:
            continue
        if int(c["ef_search"]) != ef:
            continue
        if c.get("iterative_scan") != "relaxed_order":
            continue
        scale = int(c["scale_n"])
        if c.get("seqscan_off"):
            twins[scale] = c
        else:
            as_planned[scale] = c
    pts: list[tuple[int, float]] = []
    for scale in sorted(as_planned):
        cell = as_planned[scale]
        plan = cell.get("plan") or {}
        if plan.get("seq_scan"):
            cell = twins.get(scale)
            if cell is None:
                raise ValueError(f"fig4: missing seqscan_off twin N={scale} ef={ef}")
        pts.append((scale, float(cell["hit_at_10_drop"])))
    return pts


def _legacy_single_index_loss(hnsw_cell_json: dict[str, Any]) -> tuple[list[tuple[int, float]], list[str]]:
    """document_chunks raw ef=200; modes as_planned/forced_hnsw with all_probes_hnsw."""
    pts: list[tuple[int, float]] = []
    notes: list[str] = []
    for cell in hnsw_cell_json.get("cells") or []:
        if cell.get("condition") != "raw" or int(cell.get("ef_search", -1)) != 200:
            continue
        if cell.get("table") != "document_chunks":
            continue
        modes = {m["mode"]: m for m in cell.get("modes") or []}
        picked = None
        for mode in ("as_planned", "forced_hnsw"):
            if mode not in modes:
                continue
            m = modes[mode]
            if m.get("plan_error"):
                notes.append(f"scale={cell.get('scale')} mode={mode}: plan_error")
                continue
            pc = m.get("plan_check") or {}
            if not pc.get("all_probes_hnsw"):
                notes.append(f"scale={cell.get('scale')} mode={mode}: not all_probes_hnsw")
                continue
            loss = m.get("hit_at_10_loss")
            if loss is None:
                notes.append(f"scale={cell.get('scale')} mode={mode}: missing loss")
                continue
            picked = (int(cell["scale"]), float(loss), mode)
            break
        if picked:
            pts.append((picked[0], picked[1]))
        else:
            notes.append(f"scale={cell.get('scale')}: no qualifying mode row")
    have = {n for n, _ in pts}
    for n in LADDER:
        if n not in have:
            notes.append(f"legacy single-index @ef200: no HNSW row for N={n} in hnsw_recall_by_cell_5434.json (skipped)")
    return sorted(pts), notes


def fig4_perN_hit_loss(eval_openai: dict[str, Any], legacy_cells: dict[str, Any]) -> tuple[str, list[dict], list[str]]:
    colors = {100: BLUE, 200: ORANGE, 400: GREEN, 800: PURPLE}
    p = Plot(-0.02, 0.12, 0.02, "Hit@10 loss (exact − HNSW)")
    p.axes()
    plotted: list[dict] = []
    for ef, color in colors.items():
        series = _per_n_loss_series(eval_openai, ef=ef)
        p.line(series, color)
        for n, loss in series:
            plotted.append({"ef_search": ef, "N": n, "hit_at_10_loss": loss})
    legacy, notes = _legacy_single_index_loss(legacy_cells)
    if legacy:
        p.line(legacy, GREY, dash="4 3", marker="circle")
        for n, loss in legacy:
            plotted.append({"ef_search": "legacy_single_index", "N": n, "hit_at_10_loss": loss})
    p.legend(
        [
            ("ef=100", BLUE, ""),
            ("ef=200", ORANGE, ""),
            ("ef=400", GREEN, ""),
            ("ef=800", PURPLE, ""),
            ("first version, single index, ef=200", GREY, "4 3"),
        ],
        x=ML + 6,
        y=H - MB - 58,
    )
    return p.svg(), plotted, notes


class PlotLinearP:
    """Expected routing error rate p on the x-axis (linear 0--1)."""

    def __init__(self, ylo: float, yhi: float, ystep: float, ylabel: str) -> None:
        self.ylo, self.yhi, self.ystep, self.ylabel = ylo, yhi, ystep, ylabel
        self.xlo, self.xhi = 0.0, 1.0
        self.parts: list[str] = []

    def x(self, p: float) -> float:
        return ML + (p - self.xlo) / (self.xhi - self.xlo) * (W - ML - MR)

    def y(self, v: float) -> float:
        return MT + (self.yhi - v) / (self.yhi - self.ylo) * (H - MT - MB)

    def axes(self) -> None:
        part = self.parts
        v = self.ylo
        while v <= self.yhi + 1e-9:
            yy = self.y(v)
            part.append(
                f'<line x1="{ML}" x2="{W - MR}" y1="{yy:.1f}" y2="{yy:.1f}" '
                f'stroke="#e3e3e3" stroke-width="0.6"/>'
            )
            part.append(f'<text x="{ML - 4}" y="{yy + 3:.1f}" font-size="9" text-anchor="end">{v:.2f}</text>')
            v += self.ystep
        for p in (0.0, 0.2, 0.4, 0.6, 0.8, 1.0):
            xx = self.x(p)
            part.append(
                f'<line x1="{xx:.1f}" x2="{xx:.1f}" y1="{H - MB}" y2="{H - MB + 3}" '
                f'stroke="#000" stroke-width="0.6"/>'
            )
            part.append(f'<text x="{xx:.1f}" y="{H - MB + 13}" font-size="9" text-anchor="middle">{p:g}</text>')
        part.append(f'<line x1="{ML}" x2="{W - MR}" y1="{H - MB}" y2="{H - MB}" stroke="#000" stroke-width="0.8"/>')
        part.append(f'<line x1="{ML}" x2="{ML}" y1="{MT}" y2="{H - MB}" stroke="#000" stroke-width="0.8"/>')
        part.append(
            f'<text x="{(ML + W - MR) / 2:.1f}" y="{H - 4}" font-size="9.5" text-anchor="middle">'
            "Router error rate p"
            "</text>"
        )
        cy = (MT + H - MB) / 2
        part.append(
            f'<text x="11" y="{cy:.1f}" font-size="9.5" text-anchor="middle" '
            f'transform="rotate(-90 11 {cy:.1f})">{self.ylabel}</text>'
        )

    def line(self, pts: list[tuple[float, float]], color: str, *, dash: str = "") -> None:
        d = " ".join(f"{self.x(a):.1f},{self.y(b):.1f}" for a, b in pts)
        dash_attr = f' stroke-dasharray="{dash}"' if dash else ""
        self.parts.append(f'<polyline points="{d}" fill="none" stroke="{color}" stroke-width="1.4"{dash_attr}/>')
        for a, b in pts:
            xx, yy = self.x(a), self.y(b)
            self.parts.append(f'<circle cx="{xx:.1f}" cy="{yy:.1f}" r="2.3" fill="{color}"/>')

    def hline(self, v: float, color: str, *, dash: str = "") -> None:
        yy = self.y(v)
        dash_attr = f' stroke-dasharray="{dash}"' if dash else ""
        self.parts.append(
            f'<line x1="{ML}" x2="{W - MR}" y1="{yy:.1f}" y2="{yy:.1f}" stroke="{color}" '
            f'stroke-width="0.9"{dash_attr}/>'
        )

    def legend(self, items: list[tuple[str, str, str]], *, x: float, y: float) -> None:
        for i, (label, color, dash) in enumerate(items):
            yy = y + i * 12
            dash_attr = f' stroke-dasharray="{dash}"' if dash else ""
            self.parts.append(
                f'<line x1="{x}" x2="{x + 16}" y1="{yy}" y2="{yy}" stroke="{color}" '
                f'stroke-width="1.4"{dash_attr}/>'
            )
            self.parts.append(f'<text x="{x + 20}" y="{yy + 3}" font-size="8.5">{label}</text>')

    def svg(self) -> str:
        body = "\n".join(self.parts)
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
            f'font-family="{FONT}">\n<rect width="{W}" height="{H}" fill="#fff"/>\n{body}\n</svg>\n'
        )


def fig5_routing(routing: dict[str, Any]) -> tuple[str, list[dict]]:
    scale = 100000
    p_grid = list((routing.get("meta") or {}).get("p_grid") or [0.0, 0.05, 0.1, 0.2, 0.3, 0.5, 1.0])
    modes = ["wrong_type", "wrong_dropgold", "superset", "abstain"]
    colors = {
        "wrong_type": BLUE,
        "wrong_dropgold": ORANGE,
        "superset": GREEN,
        "abstain": PURPLE,
    }
    compact = routing.get("table_compact") or []
    raw = float((routing.get("raw_hit_at_10") or {}).get(str(scale), 0.585))

    def series(mode: str) -> list[tuple[float, float]]:
        key = "hit_at_10_100000"
        out: list[tuple[float, float]] = []
        for p in p_grid:
            for row in compact:
                if row.get("mode") == mode and abs(float(row["p"]) - p) < 1e-12:
                    out.append((p, float(row[key])))
                    break
        return out

    p = PlotLinearP(0.0, 1.0, 0.2, "Expected Hit@10")
    p.axes()
    p.hline(raw, GREY, dash="3 2")
    plotted: list[dict] = []
    oracle = series("wrong_type")[0][1] if series("wrong_type") else None
    if oracle is not None:
        p.hline(oracle, "#000", dash="2 2")
    for mode in modes:
        pts = series(mode)
        p.line(pts, colors[mode])
        for pv, hit in pts:
            plotted.append({"mode": mode, "p": pv, "hit_at_10": hit})
    p.legend(
        [
            ("wrong_type", BLUE, ""),
            ("wrong_dropgold", ORANGE, ""),
            ("superset", GREEN, ""),
            ("abstain", PURPLE, ""),
            ("raw Hit@10 (unfiltered)", GREY, "3 2"),
            ("oracle (p = 0)", "#000", "2 2"),
        ],
        x=ML + 8,
        y=H - MB - 78,
    )
    return p.svg(), plotted


def render(svg_path: Path) -> None:
    html = (
        f"<!doctype html><html><head><title>{svg_path.stem}</title>"
        f"<style>@page{{size:{W}px {H}px;margin:0}}html,body{{margin:0;padding:0}}"
        f"svg{{display:block}}</style></head>"
        f"<body>{svg_path.read_text(encoding='utf-8')}</body></html>"
    )
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        page = Path(tmp) / "fig.html"
        page.write_text(html, encoding="utf-8")
        common = [str(CHROME), "--headless", "--disable-gpu", "--no-pdf-header-footer", "--hide-scrollbars"]
        subprocess.run(
            common + [f"--print-to-pdf={svg_path.with_suffix('.pdf')}", page.as_uri()],
            check=True,
            capture_output=True,
        )
        scale = 600 / 96
        subprocess.run(
            common
            + [
                f"--force-device-scale-factor={scale}",
                f"--window-size={W},{H}",
                f"--screenshot={svg_path.with_suffix('.png')}",
                page.as_uri(),
            ],
            check=True,
            capture_output=True,
        )


def _print_table(title: str, rows: list[dict], cols: list[str]) -> None:
    print(f"\n=== {title} ===")
    hdr = " ".join(f"{c:>16}" for c in cols)
    print(hdr)
    for row in rows:
        print(" ".join(f"{row[c]:>16}" for c in cols))


def _validate_xml(svg_path: Path) -> tuple[bool, str]:
    try:
        ET.parse(svg_path)
        return True, "ok"
    except ET.ParseError as exc:
        return False, str(exc)


def main() -> int:
    openai200 = _load(REV1 / "exact_ladder_openai_primary200.json")
    openai400 = _load(REV1 / "exact_ladder_openai_primary400.json")
    titan200 = _load(REV1 / "exact_ladder_titan_primary200.json")
    bm25_dense = _load(REV1 / "bm25_dense_text.json")
    bm25_4k = _load(REV1 / "bm25_chars4000.json")
    analysis = _load(REV1 / "analysis_exact.json")

    fig1_svg, fig1_pts = fig1_exact_hit_vs_logN(openai200, analysis)
    fig2_svg, fig2_pts = fig2_exact_lift(openai200, titan200, openai400)
    fig3_svg, fig3_pts = fig3_bm25_vs_dense(openai200, titan200, bm25_dense, bm25_4k)
    per_n_openai = _load(REV1 / "per_n_hnsw_eval_openai.json")
    legacy_hnsw = _load(REV1 / "hnsw_recall_by_cell_5434.json")
    routing = _load(REV1 / "routing_simulation_openai_primary200.json")
    fig4_svg, fig4_pts, fig4_notes = fig4_perN_hit_loss(per_n_openai, legacy_hnsw)
    fig5_svg, fig5_pts = fig5_routing(routing)

    figures = {
        "fig1_exact_hit_vs_logN.svg": fig1_svg,
        "fig2_exact_lift.svg": fig2_svg,
        "fig3_bm25_vs_dense.svg": fig3_svg,
        "fig4_perN_hit_loss.svg": fig4_svg,
        "fig5_routing.svg": fig5_svg,
    }
    OUT.mkdir(parents=True, exist_ok=True)
    for name, svg in figures.items():
        (OUT / name).write_text(svg, encoding="utf-8")

    _print_table(
        "fig1 OpenAI primary200 exact (raw / meta_in Hit@10, raw Hit@1)",
        fig1_pts,
        ["N", "raw_hit_at_10", "meta_in_hit_at_10", "raw_hit_at_1", "bootstrap_hit_at_10_lo", "bootstrap_hit_at_10_hi"],
    )
    _print_table("fig2 metadata lift (meta_in − raw Hit@10)", fig2_pts, ["series", "N", "lift", "ci_lo", "ci_hi"])
    _print_table(
        "fig3 Hit@10 vs N",
        fig3_pts,
        ["N", "openai_exact", "titan_exact", "bm25_dense_text", "bm25_chars4000"],
    )
    _print_table(
        "fig4 per-N Hit@10 loss",
        fig4_pts,
        ["ef_search", "N", "hit_at_10_loss"],
    )
    if fig4_notes:
        print("\nfig4 legacy single-index notes:")
        for note in fig4_notes:
            print(f"  {note}")
    _print_table("fig5 routing @100k", fig5_pts, ["mode", "p", "hit_at_10"])

    skip_chrome = os.environ.get("SKIP_CHROME_RENDER", "1") == "1"
    chrome_ok = False
    if not skip_chrome and CHROME.exists():
        for path in figures:
            svg = OUT / path
            try:
                render(svg)
                chrome_ok = True
            except (subprocess.CalledProcessError, OSError) as exc:
                print(f"Chrome render failed for {svg.name}: {exc}", file=sys.stderr)
                chrome_ok = False
                break
    if skip_chrome:
        print("\nSVG written; PDF/PNG skipped (SKIP_CHROME_RENDER=1).", file=sys.stderr)
    elif not chrome_ok:
        print("\nSVG written; PDF/PNG not rendered (Chrome missing or blocked). Example conversion:", file=sys.stderr)
        for path in figures:
            svg = OUT / path
            print(
                f'  "{CHROME}" --headless --disable-gpu --no-pdf-header-footer '
                f'--print-to-pdf="{svg.with_suffix(".pdf")}" "<wrap {svg.name} in a local file:// HTML page>"',
                file=sys.stderr,
            )
            print(
                f'  "{CHROME}" --headless --disable-gpu --force-device-scale-factor={600 / 96:.4f} '
                f'--window-size={W},{H} --screenshot="{svg.with_suffix(".png")}" "<same file:// HTML page>"',
                file=sys.stderr,
            )

    print("\n=== SVG XML validation ===")
    for path in figures:
        ok, msg = _validate_xml(OUT / path)
        print(f"{path}: {'PASS' if ok else 'FAIL'} ({msg})")

    print("\n=== plotted vs ladder JSON (fig1 raw Hit@10) ===")
    runs = _runs_by_key(openai200)
    all_match = True
    for row in fig1_pts:
        src = _metric(runs[("raw", row["N"])])
        match = abs(src - row["raw_hit_at_10"]) < 1e-12
        all_match = all_match and match
        print(
            f"N={row['N']:>6} ladder={src:.6f} plotted={row['raw_hit_at_10']:.6f} "
            f"{'PASS' if match else 'FAIL'}"
        )
    print(f"fig1 values match ladder: {'PASS' if all_match else 'FAIL'}")

    hashes = {name: hashlib.sha256((OUT / name).read_bytes()).hexdigest() for name in figures}
    print("\n=== output SHA-256 (determinism check) ===")
    for name, digest in hashes.items():
        print(f"{name}: {digest}")

    for name, svg in figures.items():
        rel = (OUT / name).relative_to(ROOT)
        if chrome_ok:
            print(f"wrote {rel}, .pdf, .png")
        else:
            print(f"wrote {rel}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
