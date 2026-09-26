"""Unit tests for ERB scale-law fitting."""

from __future__ import annotations

import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "scripts" / "erb"))

from fit_scaling_law import _fit_log_linear, fit_payload  # noqa: E402


def test_fit_log_linear_known_curve() -> None:
    xs = [1000.0, 5000.0, 10000.0, 50000.0]
    # y = 0.9 - 0.05 * log(N)
    ys = [0.9 - 0.05 * math.log(x) for x in xs]
    a, b = _fit_log_linear(xs, ys)
    assert abs(a - 0.9) < 1e-6
    assert abs(b - 0.05) < 1e-6


def _payload(lift_1k: float, lift_5k: float) -> dict:
    raw = {1000: 0.80, 5000: 0.60}
    lift = {1000: lift_1k, 5000: lift_5k}
    runs = []
    for n, h10 in raw.items():
        runs.append({"condition": "raw", "corpus_scale_size": n, "hit_at_1": h10 - 0.2,
                     "hit_at_10": h10, "document_recall": h10 - 0.1, "mrr": h10 - 0.3})
        m10 = h10 + lift[n]
        runs.append({"condition": "meta", "corpus_scale_size": n, "hit_at_1": m10 - 0.2,
                     "hit_at_10": m10, "document_recall": m10 - 0.1, "mrr": m10 - 0.3})
    deltas = [{"corpus_scale_size": n, "delta_hit_at_10": lift[n], "delta_document_recall": lift[n]}
              for n in raw]
    return {"runs": runs, "deltas": deltas}


def test_fit_payload_n_star_sustained() -> None:
    # Lift falls below tau at 5k and stays below through the end of the ladder -> N* = 5k.
    fitted = fit_payload(_payload(0.15, 0.02), tau=0.10)
    assert fitted["n_star"] == 5000
    assert "a" in fitted["fit_hit_at_10"]


def test_fit_payload_n_star_undefined_when_lift_recovers() -> None:
    # Below tau only at the first point, then recovers -> no sustained collapse on the ladder.
    fitted = fit_payload(_payload(0.02, 0.15), tau=0.10)
    assert fitted["n_star"] is None
