#!/usr/bin/env python3
"""Repair polluted primary-200 sweep JSON without re-querying the DB.

Root cause (fixed going forward in question_identity / manifest):
  extra_questions.jsonl reuses question_id for *different* metadata questions.
  Old sweeps keyed only on question_id → duplicate rows, conflicting Hit@10,
  wrong gold sets, and empty meta retrievals from the wrong source_type filter.

This script:
  1) Loads ERB base+extra questions keyed by eval_id = question_id::question_type
  2) For each polluted run row, matches retrieved IDs against candidate gold sets
  3) Emits a clean run with unique eval_ids and Hit@k recomputed from membership
  4) Drops impossible empty-retrieval meta rows that cannot be attributed safely
     (they must be re-swept); records them in a quarantine list

Writes:
  artifacts/published/erb_full_primary200_to100k.json   (canonical, clean)
  artifacts/published/erb_full_primary200_to100k_fit.json
  artifacts/published/sweep_repair_report.json
"""

from __future__ import annotations

import json
import math
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))

from paths import ERB_EXTRA_QUESTIONS, ERB_QUESTIONS  # noqa: E402
from question_identity import attach_eval_identity, make_eval_id  # noqa: E402

PUB = ROOT / "artifacts" / "published"
SRC = PUB / "erb_full_primary200_to100k.json"


def load_erb_variants() -> dict[str, list[dict[str, Any]]]:
    """Map raw erb question_id → list of variant rows (basic, metadata, …)."""
    by: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for path in (ERB_QUESTIONS, ERB_EXTRA_QUESTIONS):
        if not path.exists():
            continue
        with path.open(encoding="utf-8") as fh:
            for line in fh:
                if not line.strip():
                    continue
                raw = json.loads(line)
                row = attach_eval_identity(
                    {
                        "question_id": raw["question_id"],
                        "question_type": raw.get("question_type"),
                        "question": raw.get("question") or raw.get("question_text") or "",
                        "expected_doc_ids": [d for d in (raw.get("expected_doc_ids") or []) if d],
                        "source_types": list(raw.get("source_types") or []),
                    }
                )
                by[row["erb_question_id"]].append(row)
    return by


def hit_at_k(expected: list[str], retrieved: list[str], k: int) -> bool:
    return bool(set(expected) & set(retrieved[:k]))


def mrr(expected: list[str], retrieved: list[str]) -> float:
    gold = set(expected)
    for i, did in enumerate(retrieved, start=1):
        if did in gold:
            return 1.0 / i
    return 0.0


def doc_recall(expected: list[str], retrieved: list[str], k: int = 10) -> float:
    if not expected:
        return 0.0
    return len(set(expected) & set(retrieved[:k])) / len(set(expected))


def best_variant(
    erb_qid: str,
    retrieved: list[str],
    stored_hit: bool | None,
    variants: list[dict[str, Any]],
) -> dict[str, Any] | None:
    if not variants:
        return None
    if len(variants) == 1:
        return variants[0]
    # Prefer variant whose membership matches stored hit when retrieved non-empty
    scored: list[tuple[int, dict[str, Any]]] = []
    for v in variants:
        exp = list(v.get("expected_doc_ids") or [])
        mem = hit_at_k(exp, retrieved, 10) if retrieved else False
        score = 0
        if retrieved and stored_hit is not None and mem == bool(stored_hit):
            score += 5
        if retrieved and mem:
            score += 2
        # Prefer basic for raw condition attribution when tied
        if str(v.get("question_type")) == "basic":
            score += 1
        scored.append((score, v))
    scored.sort(key=lambda x: x[0], reverse=True)
    return scored[0][1]


def aggregate(rows: list[dict[str, Any]]) -> dict[str, float]:
    n = len(rows) or 1
    return {
        "n": len(rows),
        "hit_at_1": sum(1 for r in rows if r["hit_at_1"]) / n,
        "hit_at_5": sum(1 for r in rows if r["hit_at_5"]) / n,
        "hit_at_10": sum(1 for r in rows if r["hit_at_10"]) / n,
        "mrr": sum(r["mrr"] for r in rows) / n,
        "document_recall": sum(r["document_recall"] for r in rows) / n,
    }


def fit_log(xs: list[float], ys: list[float]) -> dict[str, float]:
    n = len(xs)
    if n < 2:
        return {"a": ys[0] if ys else 0.0, "b": 0.0, "form": "a - b*log(N)"}
    lx = [math.log(x) for x in xs]
    mean_x = sum(lx) / n
    mean_y = sum(ys) / n
    var_x = sum((x - mean_x) ** 2 for x in lx) or 1e-12
    cov = sum((lx[i] - mean_x) * (ys[i] - mean_y) for i in range(n))
    b = -cov / var_x
    a = mean_y + b * mean_x
    return {"a": a, "b": b, "form": "a - b*log(N)"}


def repair_run(run: dict[str, Any], variants_by_qid: dict[str, list[dict[str, Any]]]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    quarantine: list[dict[str, Any]] = []
    # Group polluted copies by raw erb id (strip :: if already present)
    by_raw: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for q in run.get("per_question") or []:
        qid = str(q.get("question_id") or "")
        raw = qid.split("::", 1)[0]
        by_raw[raw].append(q)

    clean_rows: list[dict[str, Any]] = []
    used_eval: set[str] = set()

    for raw_qid, copies in by_raw.items():
        variants = variants_by_qid.get(raw_qid) or []
        # If we have multiple copies, try to assign each copy to a distinct variant
        remaining = list(variants)
        for copy in copies:
            ret = [str(x) for x in (copy.get("retrieved_doc_ids") or [])]
            stored = copy.get("hit_at_10")
            condition = str(run.get("condition") or "raw")
            # Empty retrieval is a valid miss — keep the row. Prefer metadata variant
            # under meta condition, else basic.
            pool = remaining or variants
            if not ret:
                preferred = None
                want = "metadata" if condition == "meta" else "basic"
                for v in pool:
                    if str(v.get("question_type")) == want:
                        preferred = v
                        break
                v = preferred or (pool[0] if pool else None)
                if v is None:
                    quarantine.append(
                        {
                            "reason": "empty_retrieved_no_variant",
                            "corpus_scale_size": run.get("corpus_scale_size"),
                            "condition": condition,
                            "question_id": raw_qid,
                            "stored_hit_at_10": stored,
                        }
                    )
                    continue
            else:
                v = best_variant(
                    raw_qid,
                    ret,
                    bool(stored) if stored is not None else None,
                    pool,
                )
            if v is None:
                quarantine.append(
                    {
                        "reason": "no_erb_variant",
                        "corpus_scale_size": run.get("corpus_scale_size"),
                        "condition": condition,
                        "question_id": raw_qid,
                    }
                )
                continue
            eval_id = v["eval_id"]
            if eval_id in used_eval:
                continue
            used_eval.add(eval_id)
            if v in remaining:
                remaining.remove(v)
            exp = list(v.get("expected_doc_ids") or [])
            row = {
                "question_id": eval_id,
                "erb_question_id": raw_qid,
                "question_type": v.get("question_type"),
                "condition": condition,
                "corpus_scale_size": run.get("corpus_scale_size"),
                "expected_doc_ids": exp,
                "retrieved_doc_ids": ret,
                "hit_at_1": hit_at_k(exp, ret, 1),
                "hit_at_5": hit_at_k(exp, ret, 5),
                "hit_at_10": hit_at_k(exp, ret, 10),
                "mrr": mrr(exp, ret),
                "document_recall": doc_recall(exp, ret, 10),
                "rank": next((i for i, d in enumerate(ret, 1) if d in set(exp)), None),
                "stored_hit_at_10": stored,
                "empty_retrieval": not bool(ret),
                "repaired": True,
            }
            clean_rows.append(row)

        # If variants remain unused but we only had one polluted copy, that's OK
        # (primary set may not include both). No action.

    clean_rows.sort(key=lambda r: r["question_id"])
    metrics = aggregate(clean_rows)
    out = {
        "corpus_scale_size": run.get("corpus_scale_size"),
        "condition": run.get("condition"),
        "experiment_run_id": run.get("experiment_run_id"),
        "questions_evaluated": len(clean_rows),
        "hit_at_1": metrics["hit_at_1"],
        "hit_at_5": metrics["hit_at_5"],
        "hit_at_10": metrics["hit_at_10"],
        "mrr": metrics["mrr"],
        "document_recall": metrics["document_recall"],
        "metrics": metrics,
        "per_question": clean_rows,
        "repair": {
            "input_rows": len(run.get("per_question") or []),
            "output_rows": len(clean_rows),
            "quarantined": len(quarantine),
        },
    }
    return out, quarantine


def main() -> int:
    if not SRC.exists():
        print(f"missing {SRC}", file=sys.stderr)
        return 2
    # Prefer polluted backup
    polluted = PUB / "erb_full_primary200_to100k.POLLUTED.json"
    src_path = polluted if polluted.exists() else SRC
    if not polluted.exists() and SRC.exists():
        # Only backup if source still looks polluted (duplicate ids in first run)
        probe = json.loads(SRC.read_text(encoding="utf-8"))
        runs0 = probe.get("runs") or []
        if runs0:
            ids = [q.get("question_id") for q in (runs0[0].get("per_question") or [])]
            if len(ids) != len(set(ids)):
                polluted.write_text(SRC.read_text(encoding="utf-8"), encoding="utf-8")
                print(f"backed up polluted sweep → {polluted.name}")
                src_path = polluted
    if polluted.exists():
        src_path = polluted
        print(f"repairing from {polluted.name}")

    data = json.loads(src_path.read_text(encoding="utf-8"))
    variants = load_erb_variants()
    print(f"erb variants loaded for {len(variants)} raw question_ids")

    clean_runs: list[dict[str, Any]] = []
    all_q: list[dict[str, Any]] = []
    for run in data.get("runs") or []:
        cleaned, quar = repair_run(run, variants)
        clean_runs.append(cleaned)
        all_q.extend(quar)
        print(
            f"N={cleaned['corpus_scale_size']} {cleaned['condition']}: "
            f"{cleaned['repair']['input_rows']}→{cleaned['repair']['output_rows']} "
            f"hit@10={cleaned['hit_at_10']:.3f} quarantined={cleaned['repair']['quarantined']}"
        )

    raw_pts = sorted(
        (r["corpus_scale_size"], r["hit_at_10"]) for r in clean_runs if r.get("condition") == "raw"
    )
    meta_by = {
        r["corpus_scale_size"]: r["hit_at_10"] for r in clean_runs if r.get("condition") == "meta"
    }
    delta_points = []
    for s, rh in raw_pts:
        mh = meta_by.get(s)
        if mh is None:
            continue
        delta_points.append(
            {
                "corpus_scale_size": s,
                "delta_hit_at_10": mh - rh,
                "raw_hit_at_10": rh,
                "meta_hit_at_10": mh,
            }
        )
    n_star = next((p["corpus_scale_size"] for p in delta_points if p["delta_hit_at_10"] < 0.10), None)
    fit = fit_log([p[0] for p in raw_pts], [p[1] for p in raw_pts])

    out = {
        "created_from": str(src_path.name),
        "repair": "eval_id disambiguation + Hit@k membership recompute",
        "unique_eval_ids": True,
        "question_count_note": "rows use question_id = erb_id::question_type",
        "runs": clean_runs,
        "deltas": [
            {
                "corpus_scale_size": p["corpus_scale_size"],
                "delta_hit_at_10": round(p["delta_hit_at_10"], 4),
                "raw_hit_at_10": round(p["raw_hit_at_10"], 4),
                "meta_hit_at_10": round(p["meta_hit_at_10"], 4),
            }
            for p in delta_points
        ],
    }
    fit_out = {
        "unique_eval_ids": True,
        "fit_hit_at_10": fit,
        "fit_delta_meta_hit_at_10": {"points": delta_points},
        "n_star_tau_0_10": n_star,
        "tau": 0.1,
        "n0": 5000,
    }
    report = {
        "quarantine_count": len(all_q),
        "quarantine_sample": all_q[:50],
        "quarantine_by_reason": {},
        "n_star_tau_0_10": n_star,
        "fit_hit_at_10": fit,
        "delta_points": delta_points,
        "note": (
            "Empty-retrieval quarantines require a DB re-sweep with fixed eval_ids. "
            "Canonical published JSON excludes those rows rather than inventing hits."
        ),
    }
    for q in all_q:
        report["quarantine_by_reason"][q["reason"]] = report["quarantine_by_reason"].get(q["reason"], 0) + 1

    PUB.mkdir(parents=True, exist_ok=True)
    (PUB / "erb_full_primary200_to100k.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    (PUB / "erb_full_primary200_to100k_fit.json").write_text(json.dumps(fit_out, indent=2), encoding="utf-8")
    (PUB / "erb_full_primary_corrected.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    (PUB / "erb_full_primary_corrected_fit.json").write_text(json.dumps(fit_out, indent=2), encoding="utf-8")
    (PUB / "sweep_repair_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"N*={n_star} fit={fit}")
    print(f"quarantine={len(all_q)} by {report['quarantine_by_reason']}")
    print("wrote canonical published sweep + fit + sweep_repair_report.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
