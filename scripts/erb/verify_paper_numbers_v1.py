#!/usr/bin/env python3
"""Verify Access main.tex headline numbers match the integrity-clean sweep."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SWEEP = ROOT / "artifacts" / "published" / "erb_full_primary200_to100k.json"
CANON = ROOT / "artifacts" / "published" / "CANONICAL_METRICS.json"
TEX = ROOT / "papers" / "ieee-vector-drift" / "access" / "main.tex"
TITAN_SWEEP = ROOT / "artifacts" / "published" / "erb_titan_primary200_to100k.json"
TITAN_EXACT = ROOT / "artifacts" / "published" / "exact_control_titan.json"
TITAN_BOOT = ROOT / "artifacts" / "published" / "openai_vs_titan_bootstrap.json"


def _agg_raw(sweep: dict) -> dict[int, dict[str, float]]:
    out: dict[int, dict[str, float]] = {}
    for run in sweep["runs"]:
        if run.get("condition") != "raw":
            continue
        n = int(run["corpus_scale_size"])
        pqs = run.get("per_question") or []
        if not pqs:
            continue
        out[n] = {
            "hit_at_10": sum(1 for p in pqs if p.get("hit_at_10")) / len(pqs),
            "hit_at_1": sum(1 for p in pqs if p.get("hit_at_1")) / len(pqs),
            "mrr": sum(float(p.get("mrr") or 0) for p in pqs) / len(pqs),
            "n": float(len(pqs)),
        }
    return out


def _check_titan(tex: str) -> list[str]:
    """Titan arm: recompute from per-question rows; exact control; bootstrap tokens."""
    errors: list[str] = []
    sweep = json.loads(TITAN_SWEEP.read_text(encoding="utf-8"))
    runs = sweep.get("runs_with_per_question") or []
    if len(runs) != 18:
        errors.append(f"titan: expected 18 runs with per_question, got {len(runs)}")
    agg = _agg_raw({"runs": runs})
    for run in runs:
        pqs = run["per_question"]
        ids = [p["question_id"] for p in pqs]
        if len(ids) != 200 or len(set(ids)) != 200:
            errors.append(f"titan N={run['corpus_scale_size']} {run['condition']}: unique={len(set(ids))}")
        for p in pqs:
            member = bool(set(p["expected_doc_ids"]) & set(p["retrieved_doc_ids"][:10]))
            if member != bool(p["hit_at_10"]) or len(p["retrieved_doc_ids"]) < 10:
                errors.append(f"titan membership/underfill {p['question_id']} N={run['corpus_scale_size']}")
                break
    for n, metric, expected in (
        (5000, "hit_at_10", 0.785), (100000, "hit_at_10", 0.610),
        (5000, "hit_at_1", 0.620), (100000, "hit_at_1", 0.385),
        (5000, "mrr", 0.671), (100000, "mrr", 0.465),
    ):
        got = round(agg[n][metric], 3)
        if abs(got - expected) > 0.001:
            errors.append(f"titan N={n} {metric}: sweep={got} expected≈{expected}")
        if f"{expected:.3f}" not in tex:
            errors.append(f"main.tex missing titan token {expected:.3f}")

    exact = json.loads(TITAN_EXACT.read_text(encoding="utf-8"))
    for c in exact["comparisons"]:
        if c["hit10_disagreements"] != 0 or c["delta_hit_at_10_exact_minus_hnsw"] != 0:
            errors.append(f"titan exact vs HNSW differs at N={c['corpus_scale_size']}; update Sec. exact")

    boot = json.loads(TITAN_BOOT.read_text(encoding="utf-8"))
    d10 = boot["endpoint"]["hit_at_10"]["exact_titan_minus_openai_drop"]
    lo, hi = d10["ci95"]
    if not (lo < 0 < hi):
        errors.append(f"exact Hit@10 diff-in-drop CI {d10['ci95']} no longer includes 0; revise RQ4")
    if f"{d10['estimate']:+.3f}" not in tex:
        errors.append(f"main.tex missing exact diff-in-drop {d10['estimate']:+.3f}")
    if boot["delta_meta"]["titan"]["n_star_sustained"] != 100000:
        errors.append(f"titan N* = {boot['delta_meta']['titan']['n_star_sustained']}, paper says 100k")
    return errors


def main() -> int:
    sweep = json.loads(SWEEP.read_text(encoding="utf-8"))
    canon = json.loads(CANON.read_text(encoding="utf-8"))
    tex = TEX.read_text(encoding="utf-8")
    agg = _agg_raw(sweep)
    errors: list[str] = []

    if canon.get("integrity") != "OK":
        errors.append(f"CANONICAL integrity={canon.get('integrity')!r} expected OK")
    if canon.get("empty_retrieved_cells", 1) != 0:
        errors.append(f"empty_retrieved_cells={canon.get('empty_retrieved_cells')}")

    checks = [
        (5000, "hit_at_10", 0.795, "0.795"),
        (100000, "hit_at_10", 0.510, "0.510"),
        (5000, "hit_at_1", 0.600, "0.600"),
        (100000, "hit_at_1", 0.305, "0.305"),
        (5000, "mrr", 0.658, "0.658"),
        (100000, "mrr", 0.365, "0.365"),
    ]
    for n, metric, expected, tex_token in checks:
        got = round(agg[n][metric], 3)
        if abs(got - expected) > 0.001:
            errors.append(f"N={n} {metric}: sweep={got} expected≈{expected}")
        if tex_token not in tex:
            errors.append(f"main.tex missing token {tex_token} for N={n} {metric}")

    # unique 200
    for run in sweep["runs"]:
        ids = [p["question_id"] for p in run.get("per_question") or []]
        if len(ids) != 200 or len(set(ids)) != 200:
            errors.append(
                f"N={run['corpus_scale_size']} {run['condition']}: "
                f"n={len(ids)} unique={len(set(ids))}"
            )

    fit = canon.get("fit_hit_at_10") or {}
    if abs(float(fit.get("a", 0)) - 1.474) > 0.01:
        errors.append(f"fit a={fit.get('a')} expected≈1.474")
    if abs(float(fit.get("b", 0)) - 0.086) > 0.01:
        errors.append(f"fit b={fit.get('b')} expected≈0.086")

    errors += _check_titan(tex)

    if errors:
        print("VERIFY FAIL")
        for e in errors:
            print(" -", e)
        return 1
    print("VERIFY OK — L1 headline numbers match sweep + CANONICAL + main.tex tokens")
    print(f"  raw Hit@10 {agg[5000]['hit_at_10']:.3f}→{agg[100000]['hit_at_10']:.3f}")
    print(f"  integrity={canon['integrity']} empties={canon['empty_retrieved_cells']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
