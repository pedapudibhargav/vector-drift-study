#!/usr/bin/env python3
"""Write artifacts/published/revision1/ARTIFACT_MANIFEST.json (stdlib only)."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from harness_lib import REV1, ROOT, sha256_file  # noqa: E402

SCRIPT_MAP: list[tuple[str, str]] = [
    ("exact_ladder_openai_", "run_exact_ladder.py"),
    ("exact_ladder_titan_", "run_exact_ladder.py"),
    ("exact_ladder_uniform_", "run_exact_ladder_uniform.py"),
    ("exact_ladder_rr_s0_", "run_exact_ladder_uniform.py"),
    ("analysis_exact.", "analyze_exact.py"),
    ("analysis_uniform.", "analyze_uniform.py"),
    ("analysis_equivalence.", "equivalence_analysis.py"),
    ("analysis_delta_meta.", "analyze_exact.py"),
    ("rrf_hybrid_", "rrf_hybrid.py"),
    ("dense_top100_", "rrf_hybrid.py"),
    ("routing_simulation_", "routing_simulation.py"),
    ("per_n_hnsw_eval_", "eval_per_n_hnsw.py"),
    ("per_n_index_build_", "build_per_n_indexes.py"),
    ("hnsw_recall_by_cell_", "search_mode_diagnosis.py"),
    ("search_mode_diagnosis_", "search_mode_diagnosis.py"),
    ("plan_audit_", "explain_audit.py"),
    ("bm25_", "run_bm25_variants.py"),
    ("doc_length_stats.", "doc_token_stats.py"),
    ("doc_token_cuts_", "doc_token_stats.py"),
    ("titan_truncation_sensitivity.", "titan_truncation_sensitivity.py"),
    ("query_vector_provenance_", "run_exact_ladder.py"),
    ("duplicate_doc_ids.", "write_duplicate_doc_ids.py"),
    ("n400_lift_slope.", "write_duplicate_doc_ids.py"),
    ("scale_manifest_compact.", "write_compact_manifest.py"),
    ("plan_coverage_full.", "full_plan_coverage.py"),
    ("planner_cost_probe.", "planner_cost_probe.py"),
    ("memory_footprint_per_n.", "memory_footprint.py"),
    ("build_parallel_probe.", "build_parallel_probe.sql"),
    ("titan_v1_plan_replay.", "titan_v1_plan_replay.py"),
    ("query_vector_pairwise_", "query_vector_pairwise.py"),
    ("v1_list_violations_", "v1_list_violations.py"),
    ("lift_beyond_100k_", "lift_beyond_100k.py"),
    ("matched_truncation_", "matched_truncation_openai.py"),
    ("chunk_topchunks_", "chunk_topchunks_eval.py"),
    ("rrf_sensitivity_", "rrf_sensitivity.py"),
    ("source_group_split.", "source_group_split.py"),
    ("rank_depth_", "rank_depth.py"),
    ("hnsw_build_replicates", "hnsw_build_replicates.py"),
    ("hnsw_replicate_plan_check.", "hnsw_replicate_plan_check.py"),
    ("pool_counts_by_source.", "make_pool_counts_table.py"),
    ("analysis_pool_ladders.", "analyze_pool_ladders.py"),
    ("audit_v3/", "llm_audit_v3.py"),
    ("llm_audit_panel.", "llm_audit_panel.py"),
    ("llm_audit_top10.", "llm_audit_top10.py"),
    ("llm_displacement_audit", "llm_displacement_audit.py"),
    ("cluster_bootstrap_drop_", "cluster_bootstrap_drop.py"),
    ("chunk_control_", "chunk_eval.py"),
    ("exact_ladder_pool_", "run_exact_ladder_pool.py"),
    ("exact_ladder_origdb5434_", "run_exact_ladder.py"),
    ("pool_schedule_uncertainty.", "make_pool_table.py"),
    ("PREREGISTRATION.md", "llm_audit_v3.py (protocol, written before judge calls)"),
    ("items.json", "llm_audit_v3.py"),
    ("analysis.json", "llm_audit_v3.py"),
    ("tab_", "make_paper_tables.py"),
    ("_stats.", "make_paper_tables.py"),
    ("_sources.", "make_paper_tables.py"),
    ("fig", "make_paper_figures_rev1.py"),
]


def script_for(name: str) -> str | None:
    for prefix, script in SCRIPT_MAP:
        if name.startswith(prefix) or prefix in name:
            return script
    return None


def created_at_from_blob(blob: Any, path: Path) -> tuple[str, str]:
    if isinstance(blob, dict):
        meta = blob.get("meta") if isinstance(blob.get("meta"), dict) else {}
        for key in ("created_at", "generated_at", "created"):
            val = (meta or {}).get(key) or blob.get(key)
            if val:
                return str(val), "file_meta"
    mtime = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).isoformat()
    return mtime, "file_mtime"


def input_artifacts(blob: Any) -> list[str]:
    out: list[str] = []
    if not isinstance(blob, dict):
        return out
    meta = blob.get("meta") if isinstance(blob.get("meta"), dict) else {}
    src = meta or {}
    for key in (
        "bm25_path",
        "query_cache_path",
        "exact_ladder_path",
        "hnsw_recall_by_cell_file",
    ):
        val = src.get(key) or blob.get(key)
        if isinstance(val, str) and val:
            out.append(val)
    inputs = src.get("inputs") or blob.get("inputs")
    if isinstance(inputs, dict):
        items = inputs.values()
    elif isinstance(inputs, list):
        items = inputs
    else:
        items = []
    for v in items:
        if isinstance(v, str):
            out.append(v)
        elif isinstance(v, dict) and v.get("path"):
            out.append(str(v["path"]))
    return sorted(set(out))


def collect_files(rev1: Path) -> list[Path]:
    files: list[Path] = []
    if not rev1.is_dir():
        return files
    for path in sorted(rev1.rglob("*")):
        if not path.is_file():
            continue
        if path.name == "ARTIFACT_MANIFEST.json":
            continue
        if path.suffix.lower() in {".json", ".md", ".csv", ".tex", ".png", ".pdf", ".svg"}:
            files.append(path)
        elif path.name == "README.md":
            files.append(path)
    return files


def build_manifest(rev1: Path = REV1) -> dict[str, Any]:
    files_out: dict[str, Any] = {}
    for path in collect_files(rev1):
        rel = str(path.relative_to(ROOT))
        blob: Any = None
        if path.suffix == ".json":
            try:
                blob = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                blob = None
        created, created_src = created_at_from_blob(blob, path)
        rec = {
            "path": rel,
            "sha256": sha256_file(path),
            "script": script_for(path.name),
            "created_at": created,
            "created_at_source": created_src,
            "input_artifact_files": input_artifacts(blob),
        }
        files_out[rel] = rec
    return {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "script": "write_artifact_manifest.py",
        "files": files_out,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rev1", type=Path, default=REV1)
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="default artifacts/published/revision1/ARTIFACT_MANIFEST.json",
    )
    args = parser.parse_args(argv)
    out = args.out or (args.rev1 / "ARTIFACT_MANIFEST.json")
    payload = build_manifest(args.rev1)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {out} n_files={len(payload['files'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
