"""Shared paths for the EnterpriseRAG-Bench study."""

from __future__ import annotations

import os
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent  # .../scripts/erb
_REPO_ROOT = _SCRIPT_DIR.parents[1]  # .../<repo>
_CANDIDATE_ROOTS = [
    Path(os.environ["ERB_ROOT"]) if os.environ.get("ERB_ROOT") else None,
    _REPO_ROOT,
    Path("/app"),
]
ROOT = next(
    (
        p
        for p in _CANDIDATE_ROOTS
        if p is not None and ((p / "data").exists() or (p / "apps" / "api").exists() or (p / "app").exists())
    ),
    _REPO_ROOT,
)
DATA_DIR = Path(os.environ.get("ERB_DATA_DIR", str(ROOT / "data")))
if not DATA_DIR.exists() and Path("/app/data").exists():
    DATA_DIR = Path("/app/data")

ERB_DIR = DATA_DIR / "enterprise_rag_bench"
ERB_ZIPS = ERB_DIR / "zips"
ERB_DOCS = ERB_DIR / "documents"
ERB_QUESTIONS = ERB_DIR / "questions.jsonl"
ERB_EXTRA_QUESTIONS = ERB_DIR / "extra_questions.jsonl"
ERB_MANIFEST = DATA_DIR / "erb_scale_manifest.json"
ERB_INGEST_CHECKPOINT = DATA_DIR / "erb_ingest_checkpoint.json"
ERB_RESULTS_DIR = DATA_DIR / "results"
QUERY_EMBED_CACHE = DATA_DIR / "erb_query_embed_cache.json"

SCALE_SEED = 42
# Denser ladder for IEEE curve stability (log-fit + N*). Preliminary 20k kept.
DEFAULT_SCALES = (
    5_000,
    10_000,
    15_000,
    20_000,
    25_000,
    40_000,
    50_000,
    75_000,
    100_000,
)
SMOKE_SCALES = (1_000, 5_000)
TOP_KS = (1, 5, 10)
UI_TOP_K = 3
EVAL_TOP_K = 10
EXCLUDED_QUESTION_TYPES = frozenset({"high_level", "info_not_found"})

HF_DATASET = "onyx-dot-app/EnterpriseRAG-Bench"
GITHUB_RAW = "https://raw.githubusercontent.com/onyx-dot-app/EnterpriseRAG-Bench/main"
GITHUB_RELEASES_API = "https://api.github.com/repos/onyx-dot-app/EnterpriseRAG-Bench/releases/latest"


def api_pythonpath() -> Path:
    """Return directory that contains the `app` package."""
    for candidate in (
        ROOT / "apps" / "api",
        Path("/app"),
        ROOT,
    ):
        if (candidate / "app" / "services" / "embedding.py").exists():
            return candidate
    return Path("/app")
