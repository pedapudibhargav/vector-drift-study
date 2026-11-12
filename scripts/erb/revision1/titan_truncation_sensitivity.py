#!/usr/bin/env python3
"""Sensitivity to Titan 24k-char truncation on primary-200 gold docs (saved lists only)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np

from equivalence_analysis import (
    B,
    DELTA_PRIMARY,
    DELTA_SENSITIVITY,
    DOC_LENGTH,
    MANIFEST,
    SEED,
    align_hits,
    bootstrap_90,
    compute_equivalence,
    dump_json,
    drop_5k_100k,
    input_fingerprints,
    lift_at_scale,
    load_ladders,
    load_json,
    subset_order,
)

from equivalence_analysis import IDX

ROOT = Path(__file__).resolve().parents[3]
REV1 = ROOT / "artifacts" / "published" / "revision1"

OUT_JSON = REV1 / "titan_truncation_sensitivity.json"
OUT_MD = REV1 / "titan_truncation_sensitivity.md"

REPORT_SCALES = (5000, 50000, 100000)


def titan_truncated_primary200_gold_doc_ids() -> list[str]:
    blob = load_json(DOC_LENGTH)
    inv = blob["truncation"]["ladder_pool"]["chunk_text_only"]["titan_24000_chars"]
    return sorted(inv["truncated_primary200_gold_doc_ids"])


def questions_with_truncated_gold(order: list[str], truncated_docs: set[str]) -> list[str]:
    man = load_json(MANIFEST)
    primary = set(order)
    hit: list[str] = []
    for q in man["questions"]:
        qid = q.get("eval_id") or q.get("question_id")
        if qid not in primary:
            continue
        gold = set(q.get("expected_doc_ids") or [])
        if gold & truncated_docs:
            hit.append(qid)
    return sorted(hit)


def ladder_snapshot(
    ro: dict,
    rt: dict,
    order: list[str],
    idx: np.ndarray,
) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for emb, runs in (("openai", ro), ("titan", rt)):
        out[emb] = {}
        for cond in ("raw", "meta_in"):
            out[emb][cond] = {}
            for scale in REPORT_SCALES:
                hits = align_hits(runs[(cond, scale)], order)
                pt, lo, hi = bootstrap_90(hits, idx)
                out[emb][cond][str(scale)] = {
                    "hit_at_10": round(pt, 3),
                    "ci90_lo": round(lo, 3),
                    "ci90_hi": round(hi, 3),
                }
        drop = drop_5k_100k(runs, "raw", order)
        pt, lo, hi = bootstrap_90(drop, idx)
        out[emb]["raw_drop_5k_100k"] = {
            "estimate": round(pt, 3),
            "ci90_lo": round(lo, 3),
            "ci90_hi": round(hi, 3),
        }
        drop_m = drop_5k_100k(runs, "meta_in", order)
        pt, lo, hi = bootstrap_90(drop_m, idx)
        out[emb]["meta_in_drop_5k_100k"] = {
            "estimate": round(pt, 3),
            "ci90_lo": round(lo, 3),
            "ci90_hi": round(hi, 3),
        }
        lift5 = lift_at_scale(runs, 5000, order)
        lift100 = lift_at_scale(runs, 100000, order)
        pt, lo, hi = bootstrap_90(lift100 - lift5, idx)
        out[emb]["lift_100k_minus_lift_5k"] = {
            "estimate": round(pt, 3),
            "ci90_lo": round(lo, 3),
            "ci90_hi": round(hi, 3),
        }
    drop_o = drop_5k_100k(ro, "raw", order)
    drop_t = drop_5k_100k(rt, "raw", order)
    pt, lo, hi = bootstrap_90(drop_o - drop_t, idx)
    out["paired"] = {
        "openai_minus_titan_raw_drop": {
            "estimate": round(pt, 3),
            "ci90_lo": round(lo, 3),
            "ci90_hi": round(hi, 3),
        }
    }
    drop_om = drop_5k_100k(ro, "meta_in", order)
    drop_tm = drop_5k_100k(rt, "meta_in", order)
    pt, lo, hi = bootstrap_90(drop_om - drop_tm, idx)
    out["paired"]["openai_minus_titan_meta_in_drop"] = {
        "estimate": round(pt, 3),
        "ci90_lo": round(lo, 3),
        "ci90_hi": round(hi, 3),
    }
    return out


def delta_table(full: dict[str, Any], reduced: dict[str, Any]) -> dict[str, Any]:
    changes: dict[str, Any] = {}
    for emb in ("openai", "titan"):
        changes[emb] = {}
        for cond in ("raw", "meta_in"):
            changes[emb][cond] = {}
            for scale in REPORT_SCALES:
                s = str(scale)
                changes[emb][cond][s] = round(
                    reduced[emb][cond][s]["hit_at_10"] - full[emb][cond][s]["hit_at_10"],
                    3,
                )
    changes["paired"] = {}
    for key in ("openai_minus_titan_raw_drop", "openai_minus_titan_meta_in_drop"):
        changes["paired"][key] = round(
            reduced["paired"][key]["estimate"] - full["paired"][key]["estimate"],
            3,
        )
    return changes


def write_md(payload: dict[str, Any]) -> None:
    ex = payload["excluded_questions"]
    full = payload["full_n200"]
    red = payload["reduced"]
    ch = payload["changes_reduced_minus_full"]
    lines = [
        "# Titan truncation sensitivity (primary-200)",
        "",
        "Gold documents with `chunk_text` length > 24,000 characters (Titan truncation rule) "
        "from `doc_length_stats.json`. Questions whose gold set includes any such doc are excluded; "
        "both embedder ladders are recomputed on the same reduced question set.",
        "",
        f"Truncated primary-200 gold doc_ids ({len(payload['truncated_gold_doc_ids'])}): "
        + ", ".join(payload["truncated_gold_doc_ids"]),
        "",
        f"Excluded questions: **{len(ex)}** (of 200)",
        "",
    ]
    if ex:
        lines.append("Excluded eval_ids:")
        for qid in ex:
            lines.append(f"- {qid}")
        lines.append("")

    lines.append("## Hit@10 changes at 5k, 50k, 100k (reduced − full)")
    lines.append("")
    lines.append("| embedder | condition | 5k | 50k | 100k |")
    lines.append("|---|---|---:|---:|---:|")
    for emb in ("openai", "titan"):
        for cond in ("raw", "meta_in"):
            row = ch[emb][cond]
            lines.append(
                f"| {emb} | {cond} | {row['5000']:+.3f} | {row['50000']:+.3f} | {row['100000']:+.3f} |"
            )

    lines.append("")
    lines.append("## Paired drop differences (reduced − full)")
    lines.append("")
    for key in ("openai_minus_titan_raw_drop", "openai_minus_titan_meta_in_drop"):
        lines.append(f"- {key}: {ch['paired'][key]:+.3f}")

    lines.append("")
    lines.append("## Full vs reduced snapshots (Hit@10 means)")
    lines.append("")
    for label, snap in (("Full (n=200)", full), (f"Reduced (n={payload['n_reduced']})", red)):
        lines.append(f"### {label}")
        for emb in ("openai", "titan"):
            for cond in ("raw", "meta_in"):
                parts = [f"{s}={snap[emb][cond][str(s)]['hit_at_10']:.3f}" for s in REPORT_SCALES]
                lines.append(f"- {emb} {cond}: " + ", ".join(parts))
        lines.append("")

    eq = payload.get("equivalence_reduced")
    if eq:
        lines.append("## Equivalence on reduced set (selected)")
        lines.append("")
        a = eq["a_openai_minus_titan_raw_drop_5k_100k"]
        b = eq["b_openai_minus_titan_meta_in_drop_5k_100k"]
        lines.append(
            f"- (a) raw drop diff: {a['estimate']:+.3f} [{a['ci90_lo']:+.3f}, {a['ci90_hi']:+.3f}] "
            f"equiv@0.05={'YES' if a['equivalent_delta_0.05'] else 'NO'}"
        )
        if not a["equivalent_delta_0.05"]:
            lines.append("  - **Equivalence is NOT shown at δ=0.05 for (a) on the reduced set.**")
        lines.append(
            f"- (b) meta_in drop diff: {b['estimate']:+.3f} [{b['ci90_lo']:+.3f}, {b['ci90_hi']:+.3f}] "
            f"equiv@0.05={'YES' if b['equivalent_delta_0.05'] else 'NO'}"
        )
        if not b["equivalent_delta_0.05"]:
            lines.append("  - **Equivalence is NOT shown at δ=0.05 for (b) on the reduced set.**")

    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    order, ro, rt, idx_full = load_ladders()
    truncated_docs = set(titan_truncated_primary200_gold_doc_ids())
    excluded = questions_with_truncated_gold(order, truncated_docs)
    reduced_order = subset_order(order, set(excluded))
    idx_reduced = IDX.get(len(reduced_order))

    full_snap = ladder_snapshot(ro, rt, order, idx_full)
    red_snap = ladder_snapshot(ro, rt, reduced_order, idx_reduced)
    changes = delta_table(full_snap, red_snap)
    eq_reduced = compute_equivalence(reduced_order, idx_reduced, ro, rt)

    payload = {
        "meta": {
            "B": B,
            "seed": SEED,
            "delta_primary": DELTA_PRIMARY,
            "delta_sensitivity": DELTA_SENSITIVITY,
            "titan_truncate_rule": "chunk_text chars > 24000",
            "char_field": "chunk_text_only",
            "inputs": input_fingerprints(),
            "numpy_version": np.__version__,
        },
        "truncated_gold_doc_ids": sorted(truncated_docs),
        "excluded_questions": excluded,
        "n_reduced": len(reduced_order),
        "full_n200": full_snap,
        "reduced": red_snap,
        "changes_reduced_minus_full": changes,
        "equivalence_reduced": eq_reduced,
    }

    REV1.mkdir(parents=True, exist_ok=True)
    dump_json(OUT_JSON, payload)
    write_md(payload)
    print(f"wrote {OUT_JSON}")
    print(f"wrote {OUT_MD}")
    print(f"excluded {len(excluded)} questions; n_reduced={len(reduced_order)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
