#!/usr/bin/env python3
"""HNSW ef_search ablation at N=100k (OpenAI primary-200, raw condition).

Compares Hit@10 for ef_search ∈ {200, 400, 800} against the published HNSW
ladder. Override via HNSW_EF_SEARCH (default 200 in vector_search.py).

Usage:
  ./.venv/bin/python scripts/erb/run_ef_search_ablation.py

  ./.venv/bin/python scripts/erb/run_ef_search_ablation.py --ef-values 200,400,800
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from paths import ERB_MANIFEST, QUERY_EMBED_CACHE  # noqa: E402

PUB = ROOT / "artifacts" / "published"
PRIMARY = PUB / "primary_questions_eval.json"
SWEEP = PUB / "erb_full_primary200_to100k.json"
DEFAULT_OUT = PUB / "ef_search_ablation_100k.json"
DEFAULT_EF = (200, 400, 800)
SCALE = 100_000


def _load_env() -> None:
    env_path = ROOT / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
    url = os.environ.get("DATABASE_URL", "")
    if "vector-drift-db" in url:
        os.environ["DATABASE_URL"] = url.replace("vector-drift-db", "localhost")


def _db_url() -> str:
    return os.environ.get(
        "DATABASE_URL",
        "postgresql://vector_drift:vector_drift@localhost:5432/vector_drift",
    ).replace("postgresql+asyncpg://", "postgresql://")


from sync_vector_eval import eval_scale_raw, load_query_cache  # noqa: E402


def _published_hnsw_100k_raw() -> dict | None:
    if not SWEEP.exists():
        return None
    sweep = json.loads(SWEEP.read_text(encoding="utf-8"))
    for run in sweep.get("runs") or []:
        if int(run.get("corpus_scale_size") or 0) == SCALE and run.get("condition") == "raw":
            return run
    return None


def _run(args: argparse.Namespace) -> dict:
    try:
        import psycopg2
    except ImportError as exc:
        raise SystemExit(f"Missing psycopg2: {exc}") from exc

    manifest = json.loads(ERB_MANIFEST.read_text(encoding="utf-8"))
    all_q = {q["question_id"]: q for q in manifest["questions"]}
    primary = json.loads(PRIMARY.read_text(encoding="utf-8"))
    qids = list(primary["question_ids"])
    questions = [all_q[qid] for qid in qids if qid in all_q]
    if len(questions) != 200:
        raise SystemExit(f"expected 200 primary questions, got {len(questions)}")

    cache = load_query_cache(qids)
    published = _published_hnsw_100k_raw()
    pub_h10 = published.get("hit_at_10") if published else None

    ef_values = [int(x) for x in args.ef_values.split(",") if x.strip()]
    conn = psycopg2.connect(_db_url())
    runs: list[dict] = []
    comparisons: list[dict] = []

    try:
        for ef in ef_values:
            os.environ["HNSW_EF_SEARCH"] = str(ef)
            t0 = time.time()
            print(f"ef_search={ef} N={SCALE} raw …", flush=True)
            summary = eval_scale_raw(
                conn,
                questions,
                scale=SCALE,
                top_k=10,
                ef_search=ef,
                qvecs=cache,
            )
            elapsed = round(time.time() - t0, 1)
            row = {
                "ef_search": ef,
                "corpus_scale_size": SCALE,
                "condition": "raw",
                "hit_at_1": summary["hit_at_1"],
                "hit_at_5": summary["hit_at_5"],
                "hit_at_10": summary["hit_at_10"],
                "mrr": summary["mrr"],
                "document_recall": summary["document_recall"],
                "questions_evaluated": summary["questions_evaluated"],
                "exact_fallbacks": summary["exact_fallbacks"],
                "elapsed_s": elapsed,
            }
            if pub_h10 is not None:
                row["published_hit_at_10"] = pub_h10
                row["delta_hit_at_10_vs_published_ef200"] = round(
                    summary["hit_at_10"] - float(pub_h10), 4
                )
            print(
                f"  Hit@10={summary['hit_at_10']:.3f} "
                f"(published ef=200: {pub_h10}) "
                f"Δ={row.get('delta_hit_at_10_vs_published_ef200')} ({elapsed}s)",
                flush=True,
            )
            slim = {k: v for k, v in summary.items() if k != "per_question"}
            slim["elapsed_s"] = elapsed
            runs.append(slim)
            comparisons.append(row)
    finally:
        conn.close()

    report = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "protocol": "OpenAI text-embedding-3-small, primary-200, raw, pgvector HNSW",
        "corpus_scale_size": SCALE,
        "default_ef_search": 200,
        "ef_values": ef_values,
        "published_baseline": (
            {
                "artifact": str(SWEEP.relative_to(ROOT)) if SWEEP.exists() else None,
                "hit_at_10": pub_h10,
            }
            if pub_h10 is not None
            else None
        ),
        "comparisons": comparisons,
        "runs": runs,
        "interpretation_note": (
            "If Hit@10 rises materially as ef_search increases toward exact search, "
            "part of the dense decline at 100k may be ANN recall loss rather than "
            "true semantic drift."
        ),
    }
    out = args.output or DEFAULT_OUT
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    md = [
        "# ef_search ablation @ N=100k (OpenAI raw, primary-200)",
        "",
        report["interpretation_note"],
        "",
        "| ef_search | Hit@1 | Hit@5 | Hit@10 | MRR | Δ vs published ef=200 |",
        "|-----------|-------|-------|--------|-----|------------------------|",
    ]
    for c in comparisons:
        md.append(
            f"| {c['ef_search']} | {c['hit_at_1']} | {c['hit_at_5']} | {c['hit_at_10']} | "
            f"{c['mrr']} | {c.get('delta_hit_at_10_vs_published_ef200', '—')} |"
        )
    md_path = out.with_suffix(".md")
    md_path.write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"wrote {out}")
    print(f"wrote {md_path}")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--ef-values",
        default=",".join(str(v) for v in DEFAULT_EF),
        help="Comma-separated ef_search values",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help=f"JSON output (default: {DEFAULT_OUT.relative_to(ROOT)})",
    )
    args = parser.parse_args()
    _load_env()
    _run(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
