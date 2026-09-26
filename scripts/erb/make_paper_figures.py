#!/usr/bin/env python3
"""Regenerate the IEEE Access figures from published artifacts (no plotting deps).

Writes SVG to papers/ieee-vector-drift/figures/, then (if Google Chrome is installed)
renders each SVG to a tightly sized vector PDF and a 600-dpi PNG with headless Chrome.

Sources:
  artifacts/published/erb_full_primary200_to100k_fit.json  (OpenAI raw points, CIs, fits)
  artifacts/published/erb_full_primary200_to100k.json      (OpenAI meta runs)
  artifacts/published/erb_titan_primary200_to100k.json     (Titan runs)

Usage: python3 scripts/erb/make_paper_figures.py
"""

from __future__ import annotations

import json
import math
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PUB = ROOT / "artifacts" / "published"
OUT = ROOT / "papers" / "ieee-vector-drift" / "figures"
CHROME = Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")

# Figure geometry in CSS px (96 px = 1 in); IEEE single column is 3.5 in.
W, H = 336, 228
ML, MR, MT, MB = 40, 10, 10, 34
FONT = "Times New Roman, Times, serif"
BLUE, ORANGE, GREEN, GREY = "#1f5fa8", "#d9730d", "#2e8b57", "#555555"
LADDER = [5000, 10000, 15000, 20000, 25000, 40000, 50000, 75000, 100000]
TICKS = [5000, 10000, 20000, 50000, 100000]


def _load(name: str) -> dict:
    return json.loads((PUB / name).read_text(encoding="utf-8"))


def _runs(payload: dict) -> dict[tuple[str, int], dict]:
    return {(r["condition"], r["corpus_scale_size"]): r for r in payload["runs"]}


class Plot:
    def __init__(self, ylo: float, yhi: float, ystep: float, ylabel: str) -> None:
        self.ylo, self.yhi, self.ystep, self.ylabel = ylo, yhi, ystep, ylabel
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
            p.append(f'<line x1="{ML}" x2="{W - MR}" y1="{yy:.1f}" y2="{yy:.1f}" stroke="#e3e3e3" stroke-width="0.6"/>')
            p.append(f'<text x="{ML - 4}" y="{yy + 3:.1f}" font-size="9" text-anchor="end">{v:.2f}</text>')
            v += self.ystep
        for n in TICKS:
            xx = self.x(n)
            p.append(f'<line x1="{xx:.1f}" x2="{xx:.1f}" y1="{H - MB}" y2="{H - MB + 3}" stroke="#000" stroke-width="0.6"/>')
            p.append(f'<text x="{xx:.1f}" y="{H - MB + 13}" font-size="9" text-anchor="middle">{n // 1000}k</text>')
        p.append(f'<line x1="{ML}" x2="{W - MR}" y1="{H - MB}" y2="{H - MB}" stroke="#000" stroke-width="0.8"/>')
        p.append(f'<line x1="{ML}" x2="{ML}" y1="{MT}" y2="{H - MB}" stroke="#000" stroke-width="0.8"/>')
        p.append(f'<text x="{(ML + W - MR) / 2:.1f}" y="{H - 4}" font-size="9.5" text-anchor="middle">'
                 f'Corpus size N (log scale)</text>')
        cy = (MT + H - MB) / 2
        p.append(f'<text x="11" y="{cy:.1f}" font-size="9.5" text-anchor="middle" '
                 f'transform="rotate(-90 11 {cy:.1f})">{self.ylabel}</text>')

    def band(self, pts: list[tuple[int, float, float]], color: str) -> None:
        up = " ".join(f"{self.x(n):.1f},{self.y(hi):.1f}" for n, _, hi in pts)
        dn = " ".join(f"{self.x(n):.1f},{self.y(lo):.1f}" for n, lo, _ in reversed(pts))
        self.parts.append(f'<polygon points="{up} {dn}" fill="{color}" fill-opacity="0.15" stroke="none"/>')

    def line(self, pts: list[tuple[float, float]], color: str, *, dash: str = "", marker: str = "circle") -> None:
        d = " ".join(f"{self.x(n):.1f},{self.y(v):.1f}" for n, v in pts)
        dash_attr = f' stroke-dasharray="{dash}"' if dash else ""
        self.parts.append(f'<polyline points="{d}" fill="none" stroke="{color}" stroke-width="1.4"{dash_attr}/>')
        for n, v in pts if marker else []:
            xx, yy = self.x(n), self.y(v)
            if marker == "square":
                self.parts.append(f'<rect x="{xx - 2.4:.1f}" y="{yy - 2.4:.1f}" width="4.8" height="4.8" fill="{color}"/>')
            elif marker == "triangle":
                self.parts.append(f'<polygon points="{xx:.1f},{yy - 3:.1f} {xx - 2.8:.1f},{yy + 2.2:.1f} '
                                  f'{xx + 2.8:.1f},{yy + 2.2:.1f}" fill="{color}"/>')
            else:
                self.parts.append(f'<circle cx="{xx:.1f}" cy="{yy:.1f}" r="2.3" fill="{color}"/>')

    def fit(self, a: float, b: float, color: str) -> None:
        pts = [(n, a - b * math.log(n)) for n in (5000, 100000)]
        self.line(pts, color, dash="4 3", marker="")

    def legend(self, items: list[tuple[str, str, str]], *, x: float, y: float) -> None:
        for i, (label, color, dash) in enumerate(items):
            yy = y + i * 12
            dash_attr = f' stroke-dasharray="{dash}"' if dash else ""
            self.parts.append(f'<line x1="{x}" x2="{x + 16}" y1="{yy}" y2="{yy}" stroke="{color}" stroke-width="1.4"{dash_attr}/>')
            self.parts.append(f'<text x="{x + 20}" y="{yy + 3}" font-size="8.5">{label}</text>')

    def svg(self) -> str:
        body = "\n".join(self.parts)
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
                f'font-family="{FONT}">\n<rect width="{W}" height="{H}" fill="#fff"/>\n{body}\n</svg>\n')


def fig1(fit: dict, openai: dict) -> str:
    raw = {p["N"]: p for p in fit["raw_points"]}
    p = Plot(0.25, 1.05, 0.10, "Metric value")
    p.axes()
    p.band([(n, *raw[n]["hit_at_10_ci95"]["ci95"]) for n in LADDER], BLUE)
    p.line([(n, openai[("meta", n)]["hit_at_10"]) for n in LADDER], ORANGE, marker="square")
    p.line([(n, raw[n]["hit_at_10"]) for n in LADDER], BLUE)
    p.fit(fit["fit_hit_at_10"]["a"], fit["fit_hit_at_10"]["b"], BLUE)
    p.line([(n, raw[n]["hit_at_1"]) for n in LADDER], GREEN, marker="triangle")
    p.legend([("meta Hit@10", ORANGE, ""), ("raw Hit@1", GREEN, "")], x=ML + 8, y=MT + 8)
    p.legend([("raw Hit@10 (band: 95% CI)", BLUE, ""), ("raw Hit@10 log-linear fit", BLUE, "4 3")],
             x=ML + 128, y=MT + 8)
    return p.svg()


def fig2(openai: dict, titan: dict, tau: float) -> str:
    p = Plot(0.05, 0.20, 0.05, "Δmeta (Hit@10)")
    p.axes()
    yy = p.y(tau)
    p.parts.append(f'<line x1="{ML}" x2="{W - MR}" y1="{yy:.1f}" y2="{yy:.1f}" stroke="{GREY}" '
                   f'stroke-width="0.9" stroke-dasharray="2 2"/>')
    p.parts.append(f'<text x="{W - MR - 2}" y="{yy - 3:.1f}" font-size="8.5" text-anchor="end" fill="{GREY}">'
                   f'τ = {tau:.2f}</text>')

    def delta(runs: dict, n: int) -> float:
        return runs[("meta", n)]["hit_at_10"] - runs[("raw", n)]["hit_at_10"]

    p.line([(n, delta(openai, n)) for n in LADDER], BLUE)
    p.line([(n, delta(titan, n)) for n in LADDER], ORANGE, marker="square")
    p.legend([("OpenAI text-embedding-3-small", BLUE, ""), ("Amazon Titan Text Embeddings V2", ORANGE, "")],
             x=ML + 118, y=p.y(0.0655))
    return p.svg()


def fig3(fit: dict) -> str:
    raw = {p["N"]: p for p in fit["raw_points"]}
    p = Plot(0.25, 0.70, 0.05, "Metric value")
    p.axes()
    p.line([(n, raw[n]["mrr"]) for n in LADDER], ORANGE, marker="square")
    p.fit(fit["fit_mrr"]["a"], fit["fit_mrr"]["b"], ORANGE)
    p.line([(n, raw[n]["hit_at_1"]) for n in LADDER], BLUE)
    p.fit(fit["fit_hit_at_1"]["a"], fit["fit_hit_at_1"]["b"], BLUE)
    p.legend([("raw MRR", ORANGE, ""), ("raw Hit@1", BLUE, ""), ("log-linear fits", GREY, "4 3")],
             x=ML + 150, y=MT + 10)
    return p.svg()


def render(svg_path: Path) -> None:
    """Render SVG to a page-sized vector PDF and a 600-dpi PNG with headless Chrome."""
    html = (f"<!doctype html><html><head><title>{svg_path.stem}</title><style>@page{{size:{W}px {H}px;margin:0}}"
            f"html,body{{margin:0;padding:0}}svg{{display:block}}</style></head>"
            f"<body>{svg_path.read_text(encoding='utf-8')}</body></html>")
    with tempfile.TemporaryDirectory() as tmp:
        page = Path(tmp) / "fig.html"
        page.write_text(html, encoding="utf-8")
        common = [str(CHROME), "--headless", "--disable-gpu", "--no-pdf-header-footer", "--hide-scrollbars"]
        subprocess.run(common + [f"--print-to-pdf={svg_path.with_suffix('.pdf')}", page.as_uri()],
                       check=True, capture_output=True)
        scale = 600 / 96
        subprocess.run(common + [f"--force-device-scale-factor={scale}", f"--window-size={W},{H}",
                                 f"--screenshot={svg_path.with_suffix('.png')}", page.as_uri()],
                       check=True, capture_output=True)


def main() -> int:
    fit = _load("erb_full_primary200_to100k_fit.json")
    openai = _runs(_load("erb_full_primary200_to100k.json"))
    titan = _runs(_load("erb_titan_primary200_to100k.json"))
    figures = {
        "fig1_hit_vs_logN.svg": fig1(fit, openai),
        "fig2_delta_meta.svg": fig2(openai, titan, float(fit.get("tau", 0.10))),
        "fig3_rank_erosion.svg": fig3(fit),
    }
    OUT.mkdir(parents=True, exist_ok=True)
    for name, svg in figures.items():
        path = OUT / name
        path.write_text(svg, encoding="utf-8")
        if CHROME.exists():
            render(path)
            print(f"wrote {path.with_suffix('.pdf').relative_to(ROOT)} and .png")
        else:
            print(f"wrote {path.relative_to(ROOT)} (Chrome not found; PDF/PNG not rendered)")
    if not CHROME.exists():
        print("install Google Chrome or convert the SVGs manually", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
