#!/usr/bin/env python3
"""Safe multi-seed distractor endpoint runner (P0a).

Temporarily syncs an alternate distractor seed into Postgres, runs OpenAI
endpoint sweeps on the *published* primary-200 questions, writes an artifact,
then **always restores** seed-42 ranks from ``data/erb_scale_manifest.json``.

Uses sync psycopg2 HNSW evaluation (``sync_vector_eval.eval_scale_raw``) — no
SQLAlchemy or Docker required.

Usage (full protocol):
  ./.venv/bin/python scripts/erb/run_multi_seed_endpoints.py --skip-build

Build seed-0 manifest only (dry-run, no DB writes):
  ./.venv/bin/python scripts/erb/run_multi_seed_endpoints.py --build-manifest-only
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from paths import DATA_DIR, ERB_MANIFEST, SCALE_SEED  # noqa: E402
from sync_vector_eval import db_url_sync, load_query_cache, run_endpoint_sweep  # noqa: E402

PUB = ROOT / "artifacts" / "published"
PRIMARY_200 = PUB / "primary_questions_200.json"
PUBLISHED_SWEEP = PUB / "erb_full_primary200_to100k.json"
DEFAULT_ALT_MANIFEST = DATA_DIR / "erb_scale_manifest_seed0.json"
DEFAULT_OUT = PUB / "erb_seed0_endpoints_primary200.json"
DEFAULT_SCALES = (5_000, 50_000, 100_000)
RESTORE_VERIFY_SCALE = 5_000
RESTORE_HIT10_TOLERANCE = 0.01
PUBLISHED_SEED42_HIT10_5K = 0.795
DEFAULT_EF_SEARCH = 200


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
    for host in ("vector-drift-db", "vector-drift-postgres"):
        if host in url:
            os.environ["DATABASE_URL"] = url.replace(f"@{host}:", "@localhost:")


def _manifest_rank_digest(manifest_path: Path) -> str:
    docs = json.loads(manifest_path.read_text(encoding="utf-8"))["documents"]
    pairs = sorted((str(d["doc_id"]), int(d["scale_rank"])) for d in docs)
    payload = json.dumps(pairs, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _build_manifest(seed: int, out: Path) -> None:
    script = Path(__file__).resolve().parent / "build_scale_manifest.py"
    cmd = [sys.executable, str(script), "--seed", str(seed), "--out", str(out)]
    print(f"build manifest: {' '.join(cmd)}", flush=True)
    subprocess.run(cmd, check=True)


def _sync_ranks(manifest_path: Path) -> None:
    script = Path(__file__).resolve().parent / "sync_scale_ranks.py"
    cmd = [sys.executable, str(script), "--manifest", str(manifest_path)]
    print(f"sync ranks: {' '.join(cmd)}", flush=True)
    subprocess.run(cmd, check=True)


def _load_primary_questions(manifest_path: Path) -> list[dict]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    all_q = {q["question_id"]: q for q in manifest.get("questions") or []}
    primary_path = PRIMARY_200 if PRIMARY_200.exists() else PUB / "primary_questions_eval.json"
    primary = json.loads(primary_path.read_text(encoding="utf-8"))
    qids = list(primary["question_ids"])
    questions = [all_q[qid] for qid in qids if qid in all_q]
    if len(questions) != 200:
        raise SystemExit(f"expected 200 primary questions, got {len(questions)}")
    return questions


def _verify_db_ranks_match_manifest(manifest_path: Path) -> dict:
    import psycopg

    docs = json.loads(manifest_path.read_text(encoding="utf-8"))["documents"]
    expected = {str(d["doc_id"]): int(d["scale_rank"]) for d in docs}
    conn = psycopg.connect(db_url_sync())
    try:
        rows = conn.execute(
            "SELECT doc_id, scale_rank FROM document_chunks WHERE doc_id IS NOT NULL"
        ).fetchall()
        mismatches = 0
        checked = 0
        for doc_id, db_rank in rows:
            exp = expected.get(doc_id)
            if exp is None:
                continue
            checked += 1
            if int(db_rank) != exp:
                mismatches += 1
        return {
            "manifest": str(manifest_path),
            "manifest_digest": _manifest_rank_digest(manifest_path),
            "rows_checked": checked,
            "rank_mismatches": mismatches,
            "ok": mismatches == 0,
        }
    finally:
        conn.close()


def _published_baseline(scale: int, condition: str = "raw") -> dict | None:
    if not PUBLISHED_SWEEP.exists():
        if scale == 5000 and condition == "raw":
            return {"hit_at_10": PUBLISHED_SEED42_HIT10_5K}
        return None
    sweep = json.loads(PUBLISHED_SWEEP.read_text(encoding="utf-8"))
    for run in sweep.get("runs") or []:
        if int(run.get("corpus_scale_size") or 0) == scale and run.get("condition") == condition:
            return run
    return None


def _slim_run(run: dict) -> dict:
    return {
        "run_name": run.get("run_name"),
        "condition": run.get("condition"),
        "corpus_scale_size": run.get("corpus_scale_size"),
        "ef_search": run.get("ef_search", DEFAULT_EF_SEARCH),
        "questions_evaluated": run.get("questions_evaluated"),
        "document_recall": run.get("document_recall"),
        "hit_at_1": run.get("hit_at_1"),
        "hit_at_5": run.get("hit_at_5"),
        "hit_at_10": run.get("hit_at_10"),
        "mrr": run.get("mrr"),
        "elapsed_s": run.get("elapsed_s"),
    }


def _print_comparison_table(
    results: list[dict],
    scales: list[int],
    conditions: list[str],
    distractor_seed: int,
) -> None:
    print("\n=== Seed-0 vs published seed-42 (Hit@10, raw) ===")
    header = f"| {'N':>7} | {'seed-0':>8} | {'seed-42':>8} | {'Δ':>8} |"
    print(header)
    print("|" + "-" * 9 + "|" + "-" * 10 + "|" + "-" * 10 + "|" + "-" * 10 + "|")
    for n in scales:
        for cond in conditions:
            alt = next(
                (r for r in results if r["corpus_scale_size"] == n and r["condition"] == cond),
                None,
            )
            base = _published_baseline(n, cond)
            if not alt:
                continue
            h0 = alt["hit_at_10"]
            h42 = float(base["hit_at_10"]) if base else None
            delta = round(h0 - h42, 4) if h42 is not None else None
            h42_s = f"{h42:.4f}" if h42 is not None else "—"
            delta_s = f"{delta:+.4f}" if delta is not None else "—"
            print(f"| {n:>7} | {h0:>8.4f} | {h42_s:>8} | {delta_s:>8} |")
    print()


def _spot_check_hit10_sync(
    conn,
    questions: list[dict],
    qvecs: dict[str, list[float]],
    *,
    scale: int,
    expected_hit10: float,
    tolerance: float,
    ef_search: int,
) -> dict:
    from sync_vector_eval import eval_scale_raw

    summary = eval_scale_raw(
        conn,
        questions,
        scale=scale,
        top_k=10,
        ef_search=ef_search,
        qvecs=qvecs,
        condition="raw",
    )
    observed = float(summary["hit_at_10"])
    delta = abs(observed - expected_hit10)
    return {
        "scale": scale,
        "expected_hit_at_10": expected_hit10,
        "observed_hit_at_10": round(observed, 4),
        "delta": round(delta, 4),
        "tolerance": tolerance,
        "ok": delta <= tolerance,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--seed", type=int, default=0, help="Alternate distractor seed (default: 0)")
    parser.add_argument(
        "--alt-manifest",
        type=Path,
        default=DEFAULT_ALT_MANIFEST,
        help=f"Alternate manifest path (default: {DEFAULT_ALT_MANIFEST})",
    )
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT, help=f"Output artifact (default: {DEFAULT_OUT})")
    parser.add_argument("--scales", default=",".join(str(s) for s in DEFAULT_SCALES))
    parser.add_argument("--conditions", default="raw", help="Comma-separated: raw, meta")
    parser.add_argument("--ef-search", type=int, default=DEFAULT_EF_SEARCH)
    parser.add_argument(
        "--build-manifest-only",
        action="store_true",
        help="Only build alternate manifest; no DB sync or eval",
    )
    parser.add_argument("--skip-build", action="store_true", help="Skip manifest build (use --alt-manifest)")
    parser.add_argument("--skip-sync", action="store_true", help="Skip syncing alternate ranks (debug only)")
    parser.add_argument("--skip-eval", action="store_true", help="Sync only; skip evaluation")
    parser.add_argument("--skip-restore", action="store_true", help="DANGEROUS: do not restore seed-42 ranks")
    parser.add_argument("--skip-spot-check", action="store_true", help="Skip post-restore Hit@10 spot-check")
    args = parser.parse_args()

    _load_env()
    distractor_seed = int(args.seed)
    alt_manifest = Path(args.alt_manifest)
    scales = [int(x) for x in args.scales.split(",") if x.strip()]
    conditions = [c.strip() for c in args.conditions.split(",") if c.strip()]

    if args.build_manifest_only:
        _build_manifest(distractor_seed, alt_manifest)
        digest = _manifest_rank_digest(alt_manifest)
        print(f"manifest-only done: {alt_manifest} digest={digest}")
        return 0

    if not args.skip_build:
        _build_manifest(distractor_seed, alt_manifest)

    seed42_digest = _manifest_rank_digest(ERB_MANIFEST)
    alt_digest = _manifest_rank_digest(alt_manifest)
    if distractor_seed != SCALE_SEED and alt_digest == seed42_digest:
        raise SystemExit(
            f"alternate manifest digest matches seed-{SCALE_SEED}; "
            f"seed {distractor_seed} may not have changed distractor order"
        )
    print(f"seed-{SCALE_SEED} digest={seed42_digest} seed-{distractor_seed} digest={alt_digest}")

    if not args.skip_sync:
        _sync_ranks(alt_manifest)

    results: list[dict] = []
    restore_report: dict = {}
    spot_check: dict | None = None
    comparisons: list[dict] = []

    try:
        import psycopg2
    except ImportError as exc:
        raise SystemExit(f"psycopg2 required: {exc}") from exc

    conn = psycopg2.connect(db_url_sync())
    try:
        if not args.skip_eval:
            questions = _load_primary_questions(ERB_MANIFEST)
            qids = [q["question_id"] for q in questions]
            cache = load_query_cache(qids)
            results = run_endpoint_sweep(
                conn,
                questions,
                cache,
                scales=scales,
                conditions=conditions,
                top_k=10,
                ef_search=args.ef_search,
            )

            for r in results:
                base = _published_baseline(int(r["corpus_scale_size"]), r["condition"])
                row = {
                    "corpus_scale_size": r["corpus_scale_size"],
                    "condition": r["condition"],
                    "distractor_seed": distractor_seed,
                    "hit_at_10_seed_alt": r["hit_at_10"],
                    "hit_at_10_seed42": base.get("hit_at_10") if base else None,
                    "delta_hit_at_10": (
                        round(r["hit_at_10"] - float(base["hit_at_10"]), 4)
                        if base and base.get("hit_at_10") is not None
                        else None
                    ),
                }
                comparisons.append(row)

            _print_comparison_table(results, scales, conditions, distractor_seed)

            payload = {
                "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "protocol": "multi_seed_distractor_endpoints_sync_psycopg2",
                "eval_backend": "sync_vector_eval.eval_scale_raw (HNSW ef_search=200)",
                "distractor_seed": distractor_seed,
                "question_sample_seed": 42,
                "primary_n": 200,
                "primary_questions": str(PRIMARY_200),
                "alt_manifest": str(alt_manifest),
                "baseline_manifest_seed42": str(ERB_MANIFEST),
                "published_baseline_artifact": str(PUBLISHED_SWEEP),
                "scales": scales,
                "conditions": conditions,
                "ef_search": args.ef_search,
                "runs": [_slim_run(r) for r in results],
                "comparisons_vs_seed42": comparisons,
            }
            out = Path(args.out)
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
            print(f"wrote {out}")
    finally:
        conn.close()

        if not args.skip_restore:
            print(f"restoring seed-{SCALE_SEED} ranks from {ERB_MANIFEST} …", flush=True)
            _sync_ranks(ERB_MANIFEST)
            restore_report = _verify_db_ranks_match_manifest(ERB_MANIFEST)
            print(json.dumps(restore_report, indent=2))
            if not restore_report["ok"]:
                raise SystemExit(
                    f"restore verification failed: {restore_report['rank_mismatches']} rank mismatches"
                )

            if not args.skip_eval and not args.skip_spot_check:
                conn2 = psycopg2.connect(db_url_sync())
                try:
                    questions = _load_primary_questions(ERB_MANIFEST)
                    qids = [q["question_id"] for q in questions]
                    cache = load_query_cache(qids)
                    base = _published_baseline(RESTORE_VERIFY_SCALE, "raw")
                    expected = float(base["hit_at_10"]) if base else PUBLISHED_SEED42_HIT10_5K
                    spot_check = _spot_check_hit10_sync(
                        conn2,
                        questions,
                        cache,
                        scale=RESTORE_VERIFY_SCALE,
                        expected_hit10=expected,
                        tolerance=RESTORE_HIT10_TOLERANCE,
                        ef_search=args.ef_search,
                    )
                    print(f"restore spot-check: {json.dumps(spot_check)}")
                    if not spot_check["ok"]:
                        raise SystemExit(
                            f"restore Hit@10 spot-check failed: observed={spot_check['observed_hit_at_10']} "
                            f"expected≈{expected} (tol={RESTORE_HIT10_TOLERANCE})"
                        )
                finally:
                    conn2.close()

    if restore_report or spot_check:
        verify_path = PUB / f"erb_seed{distractor_seed}_restore_verify.json"
        verify_path.write_text(
            json.dumps(
                {
                    "restored_at": datetime.now(timezone.utc).isoformat(),
                    "seed42_manifest": str(ERB_MANIFEST),
                    "seed42_digest": seed42_digest,
                    "rank_check": restore_report,
                    "hit10_spot_check": spot_check,
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        print(f"wrote {verify_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
