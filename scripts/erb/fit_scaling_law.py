#!/usr/bin/env python3
"""Fit empirical scaling laws + bootstrap 95% CIs from sweep JSON and/or DB.

Canonical definitions (IEEE protocol):
  Δ_meta(N) = Hit@10_meta(N) − Hit@10_raw(N)
  N★(τ)     = min{ N : Δ_meta(N') < τ  ∀ N' ≥ N }   # sustained collapse (paper Eq. 5)
  Also report n_star_last_ge = max{ N : Δ_meta(N) ≥ τ } when it exists.

CI policy: prefer per_question flags from the sweep JSON (same run that produced
point estimates). Else load vector_drift_results for that run's experiment_run_id
only — never mix older scale/condition rows.
"""

from __future__ import annotations

import argparse
import json
import math
import random
import sys
from pathlib import Path


def _fit_log_linear(xs: list[float], ys: list[float]) -> tuple[float, float]:
    if len(xs) < 2:
        raise ValueError("need at least 2 points")
    n = len(xs)
    sx = sum(math.log(x) for x in xs)
    sy = sum(ys)
    sxx = sum(math.log(x) ** 2 for x in xs)
    sxy = sum(math.log(x) * y for x, y in zip(xs, ys))
    denom = n * sxx - sx * sx
    if abs(denom) < 1e-12:
        raise ValueError("degenerate fit")
    c = (n * sxy - sx * sy) / denom
    a = (sy - c * sx) / n
    b = -c
    return a, b


def _wilson_ci(p: float, n: int, z: float = 1.96) -> list[float | None]:
    """95% Wilson score interval for a binomial proportion."""
    if n <= 0 or p is None:
        return [None, None]
    p = max(0.0, min(1.0, float(p)))
    z2 = z * z
    denom = 1.0 + z2 / n
    center = (p + z2 / (2.0 * n)) / denom
    margin = (z * math.sqrt((p * (1.0 - p) + z2 / (4.0 * n)) / n)) / denom
    return [round(max(0.0, center - margin), 4), round(min(1.0, center + margin), 4)]


def _bootstrap_mean(values: list[float], *, n_boot: int = 1000, seed: int = 42) -> dict:
    if not values:
        return {"mean": None, "ci95": [None, None], "n": 0, "method": "empty"}
    rng = random.Random(seed)
    means: list[float] = []
    n = len(values)
    for _ in range(n_boot):
        sample = [values[rng.randrange(n)] for _ in range(n)]
        means.append(sum(sample) / n)
    means.sort()
    lo = means[int(0.025 * (n_boot - 1))]
    hi = means[int(0.975 * (n_boot - 1))]
    return {
        "mean": round(sum(values) / n, 4),
        "ci95": [round(lo, 4), round(hi, 4)],
        "n": n,
        "method": "bootstrap",
    }


def load_per_query_flags_from_db(experiment_run_id: str) -> dict[str, list[float]]:
    """Return hit/recall flags for one experiment_run_id only."""
    import os

    try:
        import psycopg
    except ImportError:
        return {}

    url = os.environ.get(
        "DATABASE_URL",
        "postgresql://vector_drift:vector_drift@localhost:5432/vector_drift",
    ).replace("postgresql+asyncpg://", "postgresql://")
    try:
        with psycopg.connect(url) as conn:
            rows = conn.execute(
                """
                SELECT recall_at_10::int,
                       COALESCE(document_recall, 0.0)::float,
                       COALESCE(mrr_score, 0.0)::float
                FROM vector_drift_results
                WHERE experiment_run_id = %s::uuid
                ORDER BY question_id
                """,
                (experiment_run_id,),
            ).fetchall()
        return {
            "hit_at_10": [float(r[0]) for r in rows if r[0] is not None],
            "document_recall": [float(r[1]) for r in rows],
            "mrr": [float(r[2]) for r in rows],
        }
    except Exception:
        return {}


def _flags_from_per_question(per_q: list[dict]) -> dict[str, list[float]]:
    return {
        "hit_at_1": [1.0 if q.get("hit_at_1") else 0.0 for q in per_q],
        "hit_at_5": [1.0 if q.get("hit_at_5") else 0.0 for q in per_q],
        "hit_at_10": [1.0 if q.get("hit_at_10") else 0.0 for q in per_q],
        # sweep JSON uses "recall"; older rows may use document_recall
        "document_recall": [
            float(q.get("recall") if q.get("recall") is not None else q.get("document_recall") or 0.0)
            for q in per_q
        ],
        "mrr": [float(q.get("mrr") or 0.0) for q in per_q],
    }


def _ci_bundle(
    flags: list[float] | None,
    *,
    point: float,
    n_q: int,
    n_boot: int,
    source: str,
) -> dict:
    if flags:
        out = _bootstrap_mean(flags, n_boot=n_boot)
        out["source"] = source
        return out
    return {
        "mean": round(float(point), 4),
        "ci95": _wilson_ci(float(point), n_q),
        "n": n_q,
        "method": "wilson",
        "source": source or "aggregate",
    }


def compute_n_star(deltas: list[dict], *, tau: float) -> dict:
    """Collapse threshold on an ascending ladder.

    ``n_star`` = min{N : Δ(N) < τ and Δ(N') < τ for all N' > N}
    (requires the lift to *stay* collapsed — avoids false N* on a 5k blip).

    ``n_star_last_ge`` = max{N : Δ(N) ≥ τ}.
    """
    ordered = sorted(deltas, key=lambda x: int(x["corpus_scale_size"]))
    n_star_last_ge = None
    for d in ordered:
        n = int(d["corpus_scale_size"])
        delta = float(d.get("delta_hit_at_10") or 0)
        if delta >= tau:
            n_star_last_ge = n

    n_star = None
    for i, d in enumerate(ordered):
        delta = float(d.get("delta_hit_at_10") or 0)
        if delta >= tau:
            continue
        # Require the rest of the ladder to stay below τ
        if all(float(x.get("delta_hit_at_10") or 0) < tau for x in ordered[i:]):
            n_star = int(d["corpus_scale_size"])
            break

    return {
        "n_star": n_star,
        "n_star_last_ge": n_star_last_ge,
        "n_star_definition": (
            f"min{{N : Δ_meta(N') < {tau} ∀ N'≥N}} — first ladder point where "
            f"metadata Hit@10 lift stays below τ for the remainder of the ladder; "
            f"n_star_last_ge = max{{N : Δ_meta(N) ≥ {tau}}}"
        ),
        "tau": tau,
    }


def fit_payload(payload: dict, *, tau: float = 0.10, n_boot: int = 1000) -> dict:
    runs = payload.get("runs") or []
    raw = sorted(
        (r for r in runs if r.get("condition") == "raw"),
        key=lambda r: r["corpus_scale_size"],
    )
    meta = sorted(
        (r for r in runs if r.get("condition") == "meta"),
        key=lambda r: r["corpus_scale_size"],
    )
    if len(raw) < 2:
        raise SystemExit("need >=2 raw scale points")

    xs = [float(r["corpus_scale_size"]) for r in raw]
    y_hit = [float(r["hit_at_10"]) for r in raw]
    y_hit1 = [float(r["hit_at_1"]) for r in raw]
    y_mrr = [float(r["mrr"]) for r in raw]
    y_rec = [float(r["document_recall"]) for r in raw]
    a_hit, b_hit = _fit_log_linear(xs, y_hit)
    a_hit1, b_hit1 = _fit_log_linear(xs, y_hit1)
    a_mrr, b_mrr = _fit_log_linear(xs, y_mrr)
    a_rec, b_rec = _fit_log_linear(xs, y_rec)

    deltas = payload.get("deltas") or []
    if not deltas and meta:
        by_n = {r["corpus_scale_size"]: r for r in raw}
        deltas = []
        for m in meta:
            n = m["corpus_scale_size"]
            r = by_n.get(n)
            if not r:
                continue
            deltas.append(
                {
                    "corpus_scale_size": n,
                    "delta_hit_at_10": m["hit_at_10"] - r["hit_at_10"],
                    "delta_document_recall": m["document_recall"] - r["document_recall"],
                    "delta_mrr": m["mrr"] - r["mrr"],
                    "raw_hit_at_10": r["hit_at_10"],
                    "meta_hit_at_10": m["hit_at_10"],
                }
            )

    n0 = xs[0]
    c_meta = None
    if len(deltas) >= 2:
        dx = [float(d["corpus_scale_size"]) for d in deltas]
        dy = [float(d["delta_hit_at_10"]) for d in deltas]
        _a_d, b_d = _fit_log_linear(dx, dy)
        c_meta = -b_d

    n_star_info = compute_n_star(deltas, tau=tau)

    ci_points = []
    for r in raw:
        n_q = int(r.get("questions_evaluated") or 0)
        run_id = r.get("experiment_run_id")
        source = "none"
        flag_map: dict[str, list[float]] = {}

        per_q = r.get("per_question") or []
        if per_q:
            flag_map = _flags_from_per_question(per_q)
            source = "sweep_json_per_question"
            n_q = n_q or len(per_q)
        elif run_id:
            flag_map = load_per_query_flags_from_db(str(run_id))
            source = f"db_experiment_run_id:{run_id}"
            n_q = n_q or len(flag_map.get("hit_at_10") or [])
        # Intentionally no unscoped scale/condition DB fallback (pollution risk).

        ci_points.append(
            {
                "N": r["corpus_scale_size"],
                "experiment_run_id": run_id,
                "hit_at_1": r["hit_at_1"],
                "hit_at_5": r.get("hit_at_5"),
                "hit_at_10": r["hit_at_10"],
                "document_recall": r["document_recall"],
                "mrr": r["mrr"],
                "hit_at_1_ci95": _ci_bundle(
                    flag_map.get("hit_at_1"),
                    point=float(r["hit_at_1"]),
                    n_q=n_q,
                    n_boot=n_boot,
                    source=source,
                ),
                "hit_at_10_ci95": _ci_bundle(
                    flag_map.get("hit_at_10"),
                    point=float(r["hit_at_10"]),
                    n_q=n_q,
                    n_boot=n_boot,
                    source=source,
                ),
                "document_recall_ci95": _ci_bundle(
                    flag_map.get("document_recall"),
                    point=float(r["document_recall"]),
                    n_q=n_q,
                    n_boot=n_boot,
                    source=source,
                ),
                "mrr_ci95": _ci_bundle(
                    flag_map.get("mrr"),
                    point=float(r["mrr"]),
                    n_q=n_q,
                    n_boot=n_boot,
                    source=source,
                ),
            }
        )

    return {
        "n0": n0,
        "tau": tau,
        "fit_hit_at_10": {"a": a_hit, "b": b_hit, "form": "a - b*log(N)"},
        "fit_hit_at_1": {"a": a_hit1, "b": b_hit1, "form": "a - b*log(N)"},
        "fit_mrr": {"a": a_mrr, "b": b_mrr, "form": "a - b*log(N)"},
        "fit_document_recall": {"a": a_rec, "b": b_rec, "form": "a - b*log(N)"},
        "fit_delta_meta_hit_at_10": {
            "c": c_meta,
            "form": "c*log(N/N0)",
            "points": deltas,
        },
        **n_star_info,
        "raw_points": ci_points,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("results_json", type=Path)
    parser.add_argument("--tau", type=float, default=0.10)
    parser.add_argument("--bootstrap", type=int, default=1000)
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args()

    payload = json.loads(args.results_json.read_text(encoding="utf-8"))
    fitted = fit_payload(payload, tau=args.tau, n_boot=args.bootstrap)
    text = json.dumps(fitted, indent=2)
    print(text)
    out = args.out or args.results_json.with_name(args.results_json.stem + "_fit.json")
    out.write_text(text, encoding="utf-8")
    print(f"wrote {out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
