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


def test_fit_payload_n_star() -> None:
    payload = {
        "runs": [
            {"condition": "raw", "corpus_scale_size": 1000, "hit_at_10": 0.80, "document_recall": 0.70, "mrr": 0.5},
            {"condition": "meta", "corpus_scale_size": 1000, "hit_at_10": 0.82, "document_recall": 0.72, "mrr": 0.52},
            {"condition": "raw", "corpus_scale_size": 5000, "hit_at_10": 0.60, "document_recall": 0.50, "mrr": 0.4},
            {"condition": "meta", "corpus_scale_size": 5000, "hit_at_10": 0.75, "document_recall": 0.65, "mrr": 0.55},
        ],
        "deltas": [
            {"corpus_scale_size": 1000, "delta_hit_at_10": 0.02, "delta_document_recall": 0.02},
            {"corpus_scale_size": 5000, "delta_hit_at_10": 0.15, "delta_document_recall": 0.15},
        ],
    }
    fitted = fit_payload(payload, tau=0.10)
    assert fitted["n_star"] == 5000
    assert "a" in fitted["fit_hit_at_10"]
