#!/usr/bin/env python3
"""Rebuild Hit@k metrics from published sweep: unique question_id + ID membership.

Does NOT re-run retrieval. Corrects aggregation bugs (duplicate padding + bad flags).
Writes:
  artifacts/published/erb_full_primary_corrected.json
  artifacts/published/erb_full_primary_corrected_fit.json
  artifacts/published/integrity_hit10_recompute.json (summary)
"""

from __future__ import annotations

import argparse
import json
import math
from collections import defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
PUB = ROOT / "artifacts" / "published"
ERB_DIR = ROOT / "data" / "enterprise_rag_bench"
SRC = PUB / "erb_full_primary200_to100k.json"


def load_expected() -> dict[str, list[str]]:
    """Map both raw question_id and eval_id (qid::type) → gold doc ids."""
    import sys

    sys.path.insert(0, str(ROOT / "scripts" / "erb"))
    from question_identity import attach_eval_identity  # noqa: WPS433

    out: dict[str, list[str]] = {}
    for name in ("questions.jsonl", "extra_questions.jsonl"):
        path = ERB_DIR / name
        if not path.exists():
            continue
        with path.open(encoding="utf-8") as fh:
            for line in fh:
                if not line.strip():
                    continue
                row = attach_eval_identity(json.loads(line))
                gold = [str(x) for x in (row.get("expected_doc_ids") or []) if x]
                if not gold:
                    continue
                out[str(row["eval_id"])] = gold
                # Raw id only if unique; otherwise leave eval_id as the key
                raw = str(row.get("erb_question_id") or "")
                if raw and raw not in out:
                    out[raw] = gold
    return out


def hit_at_k(expected: list[str], retrieved: list[str], k: int) -> bool:
    top = set(retrieved[:k])
    return bool(set(expected) & top)


def mrr(expected: list[str], retrieved: list[str]) -> float:
    gold = set(expected)
    for i, did in enumerate(retrieved, start=1):
        if did in gold:
            return 1.0 / i
    return 0.0


def doc_recall(expected: list[str], retrieved: list[str], k: int = 10) -> float:
    if not expected:
        return 0.0
    top = set(retrieved[:k])
    return len(set(expected) & top) / len(set(expected))


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
    # y = a - b * log(x)
    n = len(xs)
    if n < 2:
        return {"a": ys[0] if ys else 0.0, "b": 0.0, "form": "a - b*log(N)"}
    lx = [math.log(x) for x in xs]
    mean_x = sum(lx) / n
    mean_y = sum(ys) / n
    var_x = sum((x - mean_x) ** 2 for x in lx) or 1e-12
    cov = sum((lx[i] - mean_x) * (ys[i] - mean_y) for i in range(n))
    b = -cov / var_x  # because y = a - b*log => slope vs log is -b
    a = mean_y + b * mean_x
    return {"a": a, "b": b, "form": "a - b*log(N)"}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--src", type=Path, default=SRC)
    args = ap.parse_args()
    expected = load_expected()
    src = json.loads(args.src.read_text(encoding="utf-8"))

    corrected_runs: list[dict[str, Any]] = []
    summary_rows: list[dict[str, Any]] = []

    for run in src.get("runs") or []:
        by: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for q in run.get("per_question") or []:
            by[str(q["question_id"])].append(q)

        uniq_rows: list[dict[str, Any]] = []
        dup_disagree = 0
        flag_mismatch = 0
        for qid, copies in sorted(by.items()):
            hits = {bool(c.get("hit_at_10")) for c in copies}
            if len(copies) > 1 and len(hits) > 1:
                dup_disagree += 1
            # Prefer gold already stored on the sweep row (eval_id-aware); else ERB map.
            chosen = copies[0]
            for c in copies:
                row_exp = [str(x) for x in (c.get("expected_doc_ids") or []) if x]
                exp_try = row_exp or expected.get(qid) or []
                ret = [str(x) for x in (c.get("retrieved_doc_ids") or [])]
                mem = hit_at_k(exp_try, ret, 10) if exp_try else bool(c.get("hit_at_10"))
                if bool(c.get("hit_at_10")) == mem:
                    chosen = c
                    break
            exp = [str(x) for x in (chosen.get("expected_doc_ids") or []) if x] or expected.get(qid) or []
            ret = [str(x) for x in (chosen.get("retrieved_doc_ids") or [])]
            true_hit10 = hit_at_k(exp, ret, 10) if exp else bool(chosen.get("hit_at_10"))
            # If ERB map missed eval_id but stored flag exists, keep stored membership
            if not exp and chosen.get("hit_at_10") is not None:
                true_hit10 = bool(chosen.get("hit_at_10"))
            if bool(chosen.get("hit_at_10")) != true_hit10:
                flag_mismatch += 1
            row = {
                "question_id": qid,
                "condition": chosen.get("condition") or run.get("condition"),
                "corpus_scale_size": chosen.get("corpus_scale_size") or run.get("corpus_scale_size"),
                "expected_doc_ids": exp,
                "retrieved_doc_ids": ret,
                "hit_at_1": hit_at_k(exp, ret, 1),
                "hit_at_5": hit_at_k(exp, ret, 5),
                "hit_at_10": true_hit10,
                "mrr": mrr(exp, ret),
                "document_recall": doc_recall(exp, ret, 10),
                "rank": next((i for i, d in enumerate(ret, 1) if d in set(exp)), None),
                "stored_hit_at_10": bool(chosen.get("hit_at_10")),
                "n_duplicate_copies": len(copies),
            }
            uniq_rows.append(row)

        agg = aggregate(uniq_rows)
        stored_n = len(run.get("per_question") or [])
        stored_hit = sum(1 for q in (run.get("per_question") or []) if q.get("hit_at_10")) / max(1, stored_n)
        corrected_runs.append(
            {
                "corpus_scale_size": run.get("corpus_scale_size"),
                "condition": run.get("condition"),
                "experiment_run_id": run.get("experiment_run_id"),
                "n_unique_questions": len(uniq_rows),
                "metrics": agg,
                "per_question": uniq_rows,
            }
        )
        summary_rows.append(
            {
                "corpus_scale_size": run.get("corpus_scale_size"),
                "condition": run.get("condition"),
                "n_rows_published": stored_n,
                "n_unique": len(uniq_rows),
                "stored_hit_at_10": round(stored_hit, 4),
                "recomputed_hit_at_10": round(agg["hit_at_10"], 4),
                "delta": round(agg["hit_at_10"] - stored_hit, 4),
                "duplicate_hit_disagreements": dup_disagree,
                "flag_mismatches_vs_membership": flag_mismatch,
            }
        )

    # Fit raw hit@10
    raw_pts = [
        (r["corpus_scale_size"], r["metrics"]["hit_at_10"])
        for r in corrected_runs
        if r.get("condition") == "raw"
    ]
    meta_pts = [
        (r["corpus_scale_size"], r["metrics"]["hit_at_10"])
        for r in corrected_runs
        if r.get("condition") == "meta"
    ]
    raw_pts.sort()
    meta_pts.sort()
    fit_raw = fit_log([p[0] for p in raw_pts], [p[1] for p in raw_pts])
    # delta meta
    raw_by = {s: h for s, h in raw_pts}
    delta_points = []
    for s, mh in meta_pts:
        rh = raw_by.get(s)
        if rh is None:
            continue
        delta_points.append(
            {
                "corpus_scale_size": s,
                "delta_hit_at_10": mh - rh,
                "raw_hit_at_10": rh,
                "meta_hit_at_10": mh,
            }
        )
    # N*(τ): first N where Δ stays < τ for the rest of the ladder (non-monotonic-safe)
    n_star = None
    for i, p in enumerate(delta_points):
        if p["delta_hit_at_10"] >= 0.10:
            continue
        if all(x["delta_hit_at_10"] < 0.10 for x in delta_points[i:]):
            n_star = p["corpus_scale_size"]
            break
    n_star_last_ge = None
    for p in delta_points:
        if p["delta_hit_at_10"] >= 0.10:
            n_star_last_ge = p["corpus_scale_size"]

    out = {
        "source": str(args.src.name),
        "correction": "unique question_id; Hit@k = |expected ∩ retrieved[:k]| > 0 using ERB questions.jsonl",
        "n_unique_questions": corrected_runs[0]["n_unique_questions"] if corrected_runs else 0,
        "runs": corrected_runs,
    }
    fit_out = {
        "n_unique_questions": out["n_unique_questions"],
        "fit_hit_at_10": fit_raw,
        "fit_delta_meta_hit_at_10": {
            "form": "c*log(N/N0) (points only; see delta_points)",
            "points": delta_points,
        },
        "n_star_tau_0_10": n_star,
        "n_star_last_ge": n_star_last_ge,
        "tau": 0.1,
        "integrity_summary": summary_rows,
    }

    PUB.mkdir(parents=True, exist_ok=True)
    (PUB / "erb_full_primary_corrected.json").write_text(
        json.dumps(out, indent=2), encoding="utf-8"
    )
    (PUB / "erb_full_primary_corrected_fit.json").write_text(
        json.dumps(fit_out, indent=2), encoding="utf-8"
    )
    (PUB / "integrity_hit10_recompute.json").write_text(
        json.dumps(
            {
                "note": out["correction"],
                "n_star_tau_0_10_corrected": n_star,
                "fit_hit_at_10": fit_raw,
                "runs": summary_rows,
                "delta_points": delta_points,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"unique_questions={out['n_unique_questions']}")
    print(f"fit_hit_at_10={fit_raw}")
    print(f"N*(tau=0.10) corrected={n_star}")
    print("wrote erb_full_primary_corrected.json (+ _fit + integrity summary)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
