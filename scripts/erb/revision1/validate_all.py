#!/usr/bin/env python3
"""Revision-1 validation harness. Stdlib only. Non-zero exit if any check FAILs."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any, Callable

sys.path.insert(0, str(Path(__file__).resolve().parent))

from harness_lib import (  # noqa: E402
    ARTIFACT_MANIFEST_PATH,
    BANK_N,
    CLAIMS_PATH,
    COMPACT_MANIFEST_PATH,
    COSINE_INFO_BAND,
    COSINE_PASS,
    DEFAULT_TEX_PATH,
    DISPLACEMENT_CATEGORIES,
    DISPLACEMENT_TEXT_KEYS,
    EXACT_LABELS,
    EXPECTED_EXACT_LADDERS,
    EXPECTED_HNSW_RECALL,
    EXPECTED_PER_N_EVAL,
    EXPECTED_POOL_LADDERS,
    HNSW_LABELS,
    MANIFEST_PATH,
    POOL_ANALYSIS_KEYS,
    POOL_RR_FULL_RAW_HIT10,
    OLD_OPENAI_SWEEP,
    PUB,
    QUERY_CACHE_REV1,
    REV1,
    ROOT,
    CheckResult,
    bank_question_ids,
    bare_erb_cache_lookups,
    blob_skipped,
    cache_vector_for_eval,
    cell_hnsw_index_used,
    claimed_search_mode,
    discover_ladders,
    elapsed_recorded,
    exact_plan_ok,
    forced_hnsw_plan_evidence,
    hnsw_frac,
    iter_forced_hnsw_rows,
    iter_manifest_documents,
    load_json,
    load_manifest,
    match_plan_cells,
    mean,
    numbers_close,
    parse_ladder_name,
    provenance_entries,
    resolve_default_tex,
    resolve_path,
    resolve_scale_manifest,
    result_eval_ids,
    retrieved_ids,
    run_invariants,
    sha256_file,
    sha256_text,
    sha256_vector,
)
from crosscheck_stats import (  # noqa: E402
    compare_with_analysis,
    extra_cross_mismatches,
    load_canonical_ladders,
    n400_lift_slope_from_ladder,
    recompute,
)

PROVENANCE_PATH = REV1 / "query_vector_provenance_openai.json"
ANALYSIS_PATH = REV1 / "analysis_exact.json"


def print_result(res: CheckResult) -> None:
    print(
        f"{res.name} {res.status} pass={res.n_pass} fail={res.n_fail} "
        f"skip={res.n_skip} warn={res.n_warn} unverified={res.n_unverified}"
    )
    shown = res.messages[:40]
    for msg in shown:
        print(f"  {msg}")
    for msg in res.messages[40:]:
        if "FAIL" in msg[:8]:
            print(f"  {msg}")
    if len(res.messages) > 40:
        print(f"  ... {len(res.messages) - 40} more (failures above are always shown)")


def load_ladder_blobs(
    ladders: dict[str, dict[str, Any]] | None = None,
    rev1: Path = REV1,
) -> dict[str, dict[str, Any]]:
    if ladders is not None:
        return ladders
    out: dict[str, dict[str, Any]] = {}
    for path in discover_ladders(rev1):
        out[str(path)] = load_json(path)
    return out


def expected_n_questions(bank: str, pub: Path = PUB) -> int:
    bank_file = pub / f"primary_questions_{bank.replace('primary', '')}.json"
    # primary200 -> primary_questions_200.json
    mapped = {
        "primary200": pub / "primary_questions_200.json",
        "primary400": pub / "primary_questions_400.json",
    }
    path = mapped.get(bank)
    if path and path.is_file():
        blob = load_json(path)
        return int(blob.get("count") or len(blob.get("question_ids") or []))
    return BANK_N.get(bank, 0)


def check_schema(
    ladders: dict[str, dict[str, Any]] | None = None,
    rev1: Path = REV1,
    pub: Path = PUB,
) -> CheckResult:
    res = CheckResult("SCHEMA", "PASS")
    blobs = load_ladder_blobs(ladders, rev1)
    if not blobs:
        res.add("SKIP", f"no exact_ladder_*_*.json under {rev1}")
        return res.finalize()
    for path_s, blob in sorted(blobs.items()):
        name = Path(path_s).name
        meta = blob.get("meta") or {}
        if blob_skipped(blob):
            res.add("SKIP", f"{name} skipped")
            continue
        if not (blob.get("runs") or []):
            res.add("FAIL", f"{name} runs==[] without skipped=true")
            continue
        parsed = parse_ladder_name(Path(path_s))
        bank = parsed[1] if parsed else ""
        want_n = expected_n_questions(bank, pub) if bank else 0
        mode = claimed_search_mode(blob)
        if mode != "exact":
            res.add("FAIL", f"{name} search_mode={mode!r} expected exact")
        ok_plan, plan_msg = exact_plan_ok(meta.get("plan_check"))
        if not ok_plan:
            res.add("FAIL", f"{name} plan_check {plan_msg}")
        else:
            res.add("PASS", f"{name} plan_check {plan_msg}")
        seen_cells: set[tuple[str, int]] = set()
        for run in blob.get("runs") or []:
            cond = run.get("condition")
            scale = int(run.get("scale", run.get("corpus_scale_size")))
            cell = (str(cond), scale)
            if cell in seen_cells:
                res.add("FAIL", f"{name} duplicate cell {cell}")
            seen_cells.add(cell)
            if not elapsed_recorded(run):
                res.add("FAIL", f"{name} {cond} {scale} missing elapsed time")
            pq = run.get("per_question") or []
            ids = [p.get("question_id") for p in pq]
            if want_n and len(pq) != want_n:
                res.add("FAIL", f"{name} {cond} {scale} n={len(pq)} expected {want_n}")
            if len(ids) != len(set(ids)):
                res.add("FAIL", f"{name} {cond} {scale} duplicate question ids")
            for p in pq:
                docs = retrieved_ids(p)
                scores = p.get("scores")
                qid = p.get("question_id")
                if len(docs) != 10:
                    res.add("FAIL", f"{name} {cond} {scale} {qid} retrieved={len(docs)} != 10")
                    break
                if len(docs) != len(set(docs)):
                    res.add("FAIL", f"{name} {cond} {scale} {qid} duplicate doc ids")
                    break
                if not isinstance(scores, list) or len(scores) != 10:
                    res.add("FAIL", f"{name} {cond} {scale} {qid} scores length {0 if scores is None else len(scores)}")
                    break
        want_conds = [str(c) for c in (meta.get("conditions") or [])]
        max_seen = max((sc for _, sc in seen_cells), default=0)
        want_scales = [max_seen if str(s) == "full" else int(s) for s in (meta.get("scales") or [])]
        if want_conds and want_scales:
            expected_cells = {(c, s) for c in want_conds for s in want_scales}
            missing = sorted(expected_cells - seen_cells)
            if missing:
                res.add("FAIL", f"{name} missing cells {missing[:8]}")
        if res.n_fail == 0:
            res.add("PASS", f"{name} {len(blob.get('runs') or [])} runs schema ok")
    if ladders is None:
        for expected in EXPECTED_EXACT_LADDERS:
            path = rev1 / expected
            if not path.is_file():
                res.add("SKIP", f"{expected} missing")
        check_schema_per_n(res, rev1)
        check_schema_future_files(res, rev1, blobs)
    return res.finalize()


def check_schema_per_n(res: CheckResult, rev1: Path) -> None:
    for expected in EXPECTED_PER_N_EVAL:
        path = rev1 / expected
        if not path.is_file():
            res.add("SKIP", f"{expected} missing")
            continue
        blob = load_json(path)
        cells = blob.get("cells") or []
        if not cells:
            res.add("FAIL", f"{expected} has no cells")
            continue
        n_no_plan = 0
        n_no_short = 0
        n_wrong_q = 0
        n_false_hnsw = 0
        n_false_unflagged = 0
        acceptance = (blob.get("meta") or {}).get("acceptance") or blob.get("acceptance") or []
        acc_seq = None
        for t in acceptance:
            if isinstance(t, dict) and "n_seq_scan_cells" in t:
                acc_seq = int(t.get("n_seq_scan_cells") or 0)
        n_seq = 0
        for cell in cells:
            nq = int(cell.get("n_questions") or 0)
            if nq != 200:
                n_wrong_q += 1
            if not cell.get("plan"):
                n_no_plan += 1
            if "n_queries_short_of_10" not in cell:
                n_no_short += 1
            used = cell_hnsw_index_used(cell)
            plan = cell.get("plan") or {}
            if used is False:
                n_false_hnsw += 1
                if plan.get("seq_scan") or plan.get("plan_kind") == "seq_scan":
                    n_seq += 1
                kind = str(plan.get("plan_kind") or "")
                if kind == "hnsw_index_scan":
                    n_false_unflagged += 1
                    res.add(
                        "FAIL",
                        f"{expected} {cell.get('cell_id')} hnsw_index_used=false but plan_kind=hnsw_index_scan",
                    )
        if n_wrong_q:
            res.add("FAIL", f"{expected} {n_wrong_q} cells without 200 evaluated questions")
        else:
            res.add("PASS", f"{expected} {len(cells)} cells have 200 questions")
        if n_no_plan:
            res.add("FAIL", f"{expected} {n_no_plan} cells missing plan record")
        else:
            res.add("PASS", f"{expected} every cell has a plan record")
        if n_no_short:
            res.add("FAIL", f"{expected} {n_no_short} cells missing n_queries_short_of_10")
        else:
            res.add("PASS", f"{expected} n_queries_short_of_10 recorded on every cell")
        if n_seq and acc_seq is None:
            res.add(
                "FAIL",
                f"{expected} {n_seq} seq-scan cells (hnsw_index_used=false) but aggregates do not flag them",
            )
        elif n_seq and acc_seq is not None and acc_seq != n_seq:
            # acceptance counts N=5000 default seq cells only; require a flag, not exact match
            res.add(
                "PASS",
                f"{expected} hnsw_index_used=false seq cells={n_seq} acceptance n_seq_scan_cells={acc_seq}",
            )
        elif n_false_hnsw:
            res.add(
                "PASS",
                f"{expected} {n_false_hnsw} cells with hnsw_index_used=false recorded in plan (not counted as HNSW)",
            )
        if n_false_unflagged:
            pass  # already FAIL'd per cell


def _run_hit10(run: dict[str, Any]) -> float | None:
    mets = run.get("metrics") or {}
    if "hit_at_10" in mets and mets["hit_at_10"] is not None:
        return float(mets["hit_at_10"])
    pq = run.get("per_question") or []
    if not pq:
        return None
    return mean([float(p.get("hit_at_10") or 0.0) for p in pq])


def _json_has_doc_text(obj: Any) -> str | None:
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k in DISPLACEMENT_TEXT_KEYS and isinstance(v, str) and v.strip():
                return k
            hit = _json_has_doc_text(v)
            if hit:
                return hit
    elif isinstance(obj, list):
        for x in obj:
            hit = _json_has_doc_text(x)
            if hit:
                return hit
    return None


def _category_count(rec: Any) -> int | None:
    if isinstance(rec, int) and not isinstance(rec, bool):
        return int(rec)
    if isinstance(rec, dict):
        for key in ("count", "n"):
            if rec.get(key) is not None:
                return int(rec[key])
    return None


def _displacement_categories(blob: dict[str, Any]) -> dict[str, Any]:
    for key in ("categories", "category_summaries"):
        rec = blob.get(key)
        if isinstance(rec, dict):
            return rec
    planned = (blob.get("meta") or {}).get("category_counts_planned")
    if isinstance(planned, dict):
        return planned
    return blob


def _displacement_n_items(blob: dict[str, Any]) -> int | None:
    if blob.get("n_items") is not None:
        return int(blob["n_items"])
    meta = blob.get("meta") if isinstance(blob.get("meta"), dict) else {}
    if meta.get("n_items") is not None:
        return int(meta["n_items"])
    for key in ("judgments", "items"):
        rec = blob.get(key)
        if isinstance(rec, list) and rec:
            return len(rec)
    planned = meta.get("category_counts_planned") if isinstance(meta, dict) else None
    if isinstance(planned, dict) and planned.get("total") is not None:
        return int(planned["total"])
    return None


def _displacement_meta_str(blob: dict[str, Any], key: str) -> str:
    if blob.get(key):
        return str(blob.get(key))
    meta = blob.get("meta") if isinstance(blob.get("meta"), dict) else {}
    return str(meta.get(key) or "")


def check_schema_future_files(
    res: CheckResult,
    rev1: Path,
    blobs: dict[str, dict[str, Any]],
) -> None:
    blobs_by_name = {Path(p).name: b for p, b in blobs.items()}
    for expected in EXPECTED_POOL_LADDERS:
        path = rev1 / expected
        if not path.is_file():
            res.add("SKIP", f"{expected} missing")
            continue
        blob = blobs_by_name.get(expected) or load_json(path)
        if expected == "exact_ladder_pool_rr_full_openai_primary200.json":
            by = {(r.get("condition"), int(r.get("scale", r.get("corpus_scale_size")))): r for r in (blob.get("runs") or [])}
            for scale, want in POOL_RR_FULL_RAW_HIT10.items():
                run = by.get(("raw", scale))
                got = _run_hit10(run) if run else None
                if got is None:
                    res.add("FAIL", f"{expected} missing raw N={scale} Hit@10")
                elif abs(float(got) - float(want)) > 1e-9:
                    res.add("FAIL", f"{expected} raw N={scale} Hit@10={got} expected {want}")
                else:
                    res.add("PASS", f"{expected} raw N={scale} Hit@10={got}")

    pool_analysis = rev1 / "analysis_pool_ladders.json"
    if not pool_analysis.is_file():
        res.add("SKIP", "analysis_pool_ladders.json missing")
    else:
        blob = load_json(pool_analysis)
        if not isinstance(blob, dict):
            res.add("FAIL", "analysis_pool_ladders.json is not an object")
        else:
            pool_keys = set(blob) | set(blob.get("hit_at_10_ladders") or {})
            missing = [k for k in POOL_ANALYSIS_KEYS if k not in pool_keys]
            if missing:
                res.add("FAIL", f"analysis_pool_ladders.json missing keys {missing}")
            else:
                res.add("PASS", "analysis_pool_ladders.json has prop_s42, prop_s0, rr_full")

    disp = rev1 / "llm_displacement_audit.json"
    if not disp.is_file():
        res.add("SKIP", "llm_displacement_audit.json missing")
        return
    blob = load_json(disp)
    if not isinstance(blob, dict):
        res.add("FAIL", "llm_displacement_audit.json is not an object")
        return
    cats = _displacement_categories(blob)
    counts: list[int] = []
    for name in DISPLACEMENT_CATEGORIES:
        if name not in cats:
            res.add("FAIL", f"llm_displacement_audit.json missing category {name}")
            continue
        n = _category_count(cats[name])
        if n is None:
            res.add("FAIL", f"llm_displacement_audit.json category {name} has no count")
        else:
            counts.append(n)
    n_items = _displacement_n_items(blob)
    if n_items is None:
        res.add("FAIL", "llm_displacement_audit.json missing n_items")
    elif len(counts) == len(DISPLACEMENT_CATEGORIES) and int(n_items) != sum(counts):
        res.add(
            "FAIL",
            f"llm_displacement_audit.json n_items={n_items} != sum(counts)={sum(counts)}",
        )
    elif len(counts) == len(DISPLACEMENT_CATEGORIES):
        res.add("PASS", f"llm_displacement_audit.json counts sum to n_items={n_items}")
    provider = _displacement_meta_str(blob, "provider")
    model = _displacement_meta_str(blob, "model")
    if not provider:
        res.add("FAIL", "llm_displacement_audit.json missing provider")
    if not model:
        res.add("FAIL", "llm_displacement_audit.json missing model")
    text_key = _json_has_doc_text(blob)
    if text_key:
        res.add("FAIL", f"llm_displacement_audit.json stores document text key={text_key}")
    elif provider and model and len(counts) == len(DISPLACEMENT_CATEGORIES):
        res.add("PASS", "llm_displacement_audit.json schema ok (no document text)")


def check_invariants(
    ladders: dict[str, dict[str, Any]] | None = None,
    rev1: Path = REV1,
    manifest_path: Path = MANIFEST_PATH,
) -> CheckResult:
    res = CheckResult("INVARIANTS", "PASS")
    resolved = resolve_scale_manifest(manifest_path)
    if resolved is None:
        res.add("SKIP", f"manifest missing ({manifest_path}); cannot check source-type invariants")
        return res.finalize()
    manifest_path = resolved
    blobs = load_ladder_blobs(ladders, rev1)
    packed: dict[tuple[str, str, str], dict[str, Any]] = {}
    for path_s, blob in blobs.items():
        parsed = parse_ladder_name(Path(path_s))
        if parsed is None or blob_skipped(blob):
            continue
        packed[parsed] = blob
    if not packed:
        res.add("SKIP", "no non-skipped exact ladders")
        return res.finalize()
    doc_source, questions = load_manifest(manifest_path)
    try:
        inv = run_invariants(packed, doc_source, questions)
    except ValueError as exc:
        res.add("FAIL", f"qid alignment: {exc}")
        return res.finalize()
    for kind in ("containment", "nested_corpus", "score_monotonicity"):
        rec = inv[kind]
        if rec["n_violations"] or rec["n_unverifiable"]:
            res.add(
                "FAIL",
                f"{kind} checked={rec['n_checked']} violations={rec['n_violations']} "
                f"unverifiable={rec['n_unverifiable']}",
            )
        else:
            res.add("PASS", f"{kind} checked={rec['n_checked']} violations=0")
    return res.finalize()


def _plan_seq_scan(cell: dict[str, Any]) -> bool:
    plan = cell.get("plan") or {}
    if plan.get("seq_scan") is True:
        return True
    return str(plan.get("plan_kind") or "") == "seq_scan"


def _per_n_twin_key(cell: dict[str, Any]) -> tuple[Any, ...]:
    return (
        int(cell.get("scale_n") or cell.get("scale") or -1),
        str(cell.get("condition") or ""),
        int(cell.get("ef_search") or -1),
        str(cell.get("iterative_scan") or ""),
        int(cell.get("max_scan_tuples") or -1),
    )


def _check_per_n_search_mode(res: CheckResult, name: str, blob: dict[str, Any]) -> None:
    cells = list(blob.get("cells") or [])
    twins_hnsw = {
        _per_n_twin_key(c)
        for c in cells
        if c.get("seqscan_off") is True and cell_hnsw_index_used(c) is True
    }
    n_hnsw = 0
    n_raw_non_seq = 0
    n_raw_non_seq_hnsw = 0
    n_fail = 0
    for cell in cells:
        used = cell_hnsw_index_used(cell)
        plan = cell.get("plan") or {}
        seqscan_off = bool(cell.get("seqscan_off"))
        cond = str(cell.get("condition") or "")
        label = cell.get("cell_id") or f"{cond}/N={cell.get('scale_n')}/ef={cell.get('ef_search')}"
        if cond == "raw" and not _plan_seq_scan(cell):
            n_raw_non_seq += 1
            if used is True:
                n_raw_non_seq_hnsw += 1
        if used is True:
            n_hnsw += 1
        if (not seqscan_off) and cond == "raw" and used is False:
            seq_ok = _plan_seq_scan(cell) or plan.get("seq_scan") is True
            twin_ok = _per_n_twin_key(cell) in twins_hnsw
            if not (seq_ok and twin_ok):
                n_fail += 1
                res.add(
                    "FAIL",
                    f"{name} {label} seqscan_off=false raw hnsw_index_used=false "
                    f"seq_scan={plan.get('seq_scan')} twin_hnsw={twin_ok}",
                )
    if n_raw_non_seq:
        frac = n_raw_non_seq_hnsw / n_raw_non_seq
        if frac < 0.95:
            res.add(
                "FAIL",
                f"{name} HNSW frac among non-seq raw cells={frac:.3f} < 0.95 "
                f"({n_raw_non_seq_hnsw}/{n_raw_non_seq})",
            )
        else:
            res.add(
                "PASS",
                f"{name} HNSW frac among non-seq raw cells={frac:.3f} "
                f"({n_raw_non_seq_hnsw}/{n_raw_non_seq})",
            )
    elif cells:
        res.add("FAIL", f"{name} no non-seq raw cells with HNSW evidence")
    if n_fail == 0 and n_raw_non_seq and (n_raw_non_seq_hnsw / n_raw_non_seq) >= 0.95:
        res.add("PASS", f"{name} per-cell plans hnsw_index_used true={n_hnsw} cells={len(cells)}")


def _load_plan_audits(rev1: Path) -> list[tuple[Path, dict[str, Any]]]:
    out = []
    if not rev1.is_dir():
        return out
    for path in sorted(rev1.glob("plan_audit_*.json")):
        out.append((path, load_json(path)))
    return out


def check_search_mode_truth(
    artifacts: list[tuple[str, dict[str, Any]]] | None = None,
    rev1: Path = REV1,
    pub: Path = PUB,
) -> CheckResult:
    res = CheckResult("SEARCH_MODE_TRUTH", "PASS")
    audits = [blob for _, blob in _load_plan_audits(rev1)]
    from_disk = artifacts is None
    if artifacts is None:
        items: list[tuple[str, dict[str, Any]]] = []
        for path in discover_ladders(rev1):
            items.append((path.name, load_json(path)))
        if rev1.is_dir():
            for path in sorted(rev1.glob("per_n_hnsw_eval_*.json")):
                items.append((path.name, load_json(path)))
        if OLD_OPENAI_SWEEP.is_file():
            items.append((OLD_OPENAI_SWEEP.name, load_json(OLD_OPENAI_SWEEP)))
        artifacts = items
    if not artifacts:
        res.add("SKIP", "no search-result artifacts")
        return res.finalize()

    for name, blob in artifacts:
        mode = claimed_search_mode(blob)
        meta = blob.get("meta") or {}
        if name.startswith("erb_full_primary200_to100k") or (
            mode in HNSW_LABELS
            and not meta.get("plan_check")
            and not audits
            and not (name.startswith("per_n_hnsw_eval_") and (blob.get("cells") or []))
        ):
            res.add("UNVERIFIED", f"{name} claims approximate/HNSW or is the old OpenAI sweep but carries no plan evidence")
            continue
        if blob_skipped(blob) and (mode in EXACT_LABELS or name.startswith("exact_ladder_")):
            res.add("SKIP", f"{name} skipped exact ladder")
            continue
        if mode in EXACT_LABELS or (mode is None and name.startswith("exact_ladder_")):
            ok, msg = exact_plan_ok(meta.get("plan_check"))
            if not ok:
                res.add("FAIL", f"{name} labelled exact: {msg}")
            else:
                res.add("PASS", f"{name} exact {msg}")
            continue
        if name.startswith("per_n_hnsw_eval_") and (blob.get("cells") or []):
            _check_per_n_search_mode(res, name, blob)
            continue
        if mode in HNSW_LABELS or name.startswith("per_n_hnsw_eval_"):
            plan_check = meta.get("plan_check")
            if plan_check:
                n_hnsw = sum(1 for e in plan_check if isinstance(e, dict) and (
                    e.get("hnsw_index_scan") is True or "hnsw" in str(e.get("innermost_scan_node_type") or "").lower()
                ))
                frac = n_hnsw / max(len(plan_check), 1)
                if frac < 0.95:
                    res.add("FAIL", f"{name} labelled HNSW but plan_check HNSW frac={frac:.3f}")
                else:
                    res.add("PASS", f"{name} HNSW frac={frac:.3f}")
                continue
            cells = match_plan_cells(
                audits,
                embedder=meta.get("embedder"),
                condition=None,
                scale=None,
                ef_search=meta.get("ef_search"),
            )
            if not cells:
                res.add("UNVERIFIED", f"{name} labelled HNSW, no matching plan_audit cell")
                continue
            bad = [c for c in cells if (hnsw_frac(c) or 0.0) < 0.95]
            if bad:
                res.add("FAIL", f"{name} labelled HNSW but {len(bad)} cells have frac_hnsw<0.95")
            else:
                res.add("PASS", f"{name} HNSW evidence on {len(cells)} cells")
            continue
        if name.startswith("erb_full_primary200") or "hnsw" in name.lower():
            res.add("UNVERIFIED", f"{name} no plan evidence")
        else:
            res.add("PASS", f"{name} no search_mode claim")

    if from_disk:
        for expected in EXPECTED_HNSW_RECALL:
            path = rev1 / expected
            blob = load_json(path) if path.is_file() else None
            name = expected
            if blob is None:
                res.add("SKIP", f"{expected} missing")
                continue
            rows = iter_forced_hnsw_rows(blob)
            if not rows:
                res.add("FAIL", f"{name} has no forced_hnsw rows")
                continue
            n_ok = 0
            for label, row in rows:
                ok, msg = forced_hnsw_plan_evidence(row)
                if not ok:
                    res.add("FAIL", f"{name} {label} {msg}")
                else:
                    n_ok += 1
            if n_ok:
                res.add("PASS", f"{name} {n_ok} forced_hnsw rows have HNSW plan evidence")

    for path, audit in _load_plan_audits(rev1):
        n = len(audit.get("cells") or [])
        res.add("PASS", f"{path.name} loaded {n} plan cells as evidence")
        for cell in audit.get("cells") or []:
            if (
                cell.get("embedder") == "openai"
                and cell.get("condition") == "raw"
                and int(cell.get("ef_search") or -1) == 200
                and int(cell.get("scale") or 0) in (5000, 10000)
                and cell.get("pass") == "forward"
            ):
                frac = hnsw_frac(cell) or 0.0
                n_h = int(round(frac * int(cell.get("n_plans") or 0)))
                res.add(
                    "PASS",
                    f"{path.name} openai raw ef=200 N={cell['scale']} HNSW={n_h}/{cell.get('n_plans')}",
                )
    return res.finalize()


def check_query_vector_provenance(
    ladders: dict[str, dict[str, Any]] | None = None,
    provenance: dict[str, Any] | list | None = None,
    rev1: Path = REV1,
    pub: Path = PUB,
    manifest_path: Path = MANIFEST_PATH,
    script_dir: Path | None = None,
) -> CheckResult:
    res = CheckResult("QUERY_VECTOR_PROVENANCE", "PASS")
    prov_path = rev1 / "query_vector_provenance_openai.json"
    if provenance is None and not prov_path.is_file():
        res.add("SKIP", f"provenance file missing: {prov_path}")
        return res.finalize()
    if not manifest_path.is_file():
        res.add("SKIP", "manifest missing; cannot hash current question text")
        return res.finalize()
    blob = provenance if provenance is not None else load_json(prov_path)
    entries = {e["eval_id"]: e for e in provenance_entries(blob)}
    _, questions = load_manifest(manifest_path)
    blobs = load_ladder_blobs(ladders, rev1)
    banks = bank_question_ids(pub)
    claimed: set[str] = set()
    for path_s, result in blobs.items():
        claimed |= result_eval_ids(result)
    if not claimed:
        for ids in banks.values():
            claimed.update(ids)
    for qid in sorted(claimed):
        if "::" not in str(qid):
            res.add("FAIL", f"result cache/eval key {qid!r} lacks '::'")
            continue
        ent = entries.get(qid)
        if ent is None:
            res.add("FAIL", f"no provenance entry for {qid}")
            continue
        q = questions.get(qid)
        if q is None:
            res.add("FAIL", f"manifest missing {qid}")
            continue
        want = sha256_text(q.get("question") or "")
        if ent.get("question_sha256") != want:
            res.add("FAIL", f"{qid} question_sha256 mismatch")
            continue
        cos = float(ent.get("cosine_to_fresh_embedding") or 0.0)
        if cos < COSINE_PASS:
            res.add("FAIL", f"{qid} cosine_to_fresh_embedding={cos} < {COSINE_PASS}")
            continue
        res.n_pass += 1
    band = [
        (qid, float(ent.get("cosine_to_fresh_embedding") or 0.0))
        for qid, ent in sorted(entries.items())
        if COSINE_PASS <= float(ent.get("cosine_to_fresh_embedding") or 0.0) < COSINE_INFO_BAND
    ]
    if band:
        ids = ",".join(qid for qid, _ in band)
        print(
            f"INFO: QUERY_VECTOR_PROVENANCE cosine in [{COSINE_PASS}, {COSINE_INFO_BAND}): "
            f"n={len(band)} ids={ids}"
        )
        res.add(
            "WARN",
            f"cosine in [{COSINE_PASS}, {COSINE_INFO_BAND}): n={len(band)} ids={ids}",
        )
    cache_path = QUERY_CACHE_REV1
    if not cache_path.is_file():
        res.add("SKIP", f"vector_sha256 vs cache skipped ({cache_path.name} not in checkout)")
    else:
        cache = load_json(cache_path)
        n_sha = 0
        for qid in sorted(entries):
            ent = entries[qid]
            vec = cache_vector_for_eval(cache, qid)
            if vec is None:
                res.add("FAIL", f"{qid} vector missing from {cache_path.name}")
                continue
            want_v = sha256_vector(vec)
            got_v = ent.get("vector_sha256")
            if got_v != want_v:
                res.add("FAIL", f"{qid} vector_sha256 mismatch")
                continue
            n_sha += 1
        if n_sha:
            res.add("PASS", f"vector_sha256 matches cache for {n_sha} entries")
    lookups = bare_erb_cache_lookups(script_dir)
    if lookups:
        for h in lookups:
            res.add("FAIL", h)
    else:
        res.add("PASS", "no revision1 cache lookup by erb_question_id")
    if res.n_fail == 0:
        res.add("PASS", f"provenance ok for {len(claimed)} claimed eval ids")
    return res.finalize()


def _load_artifact_manifest(rev1: Path) -> dict[str, dict[str, Any]]:
    path = rev1 / "ARTIFACT_MANIFEST.json"
    if not path.is_file():
        return {}
    blob = load_json(path)
    files = blob.get("files") if isinstance(blob, dict) else None
    if isinstance(files, dict):
        return files
    if isinstance(files, list):
        out = {}
        for rec in files:
            name = rec.get("path") or rec.get("name") or rec.get("file")
            if name:
                out[Path(str(name)).name] = rec
        return out
    return {}


def check_artifact_provenance(rev1: Path = REV1) -> CheckResult:
    res = CheckResult("ARTIFACT_PROVENANCE", "PASS")
    if not rev1.is_dir():
        res.add("SKIP", f"{rev1} missing")
        return res.finalize()
    input_keys = ("manifest_sha256", "query_cache_sha256")
    listed = _load_artifact_manifest(rev1)
    json_paths = list(sorted(rev1.glob("*.json")))
    tables = rev1 / "paper_tables"
    if tables.is_dir():
        json_paths.extend(sorted(tables.glob("*.json")))
    for path in json_paths:
        if path.name == "ARTIFACT_MANIFEST.json":
            res.add("PASS", "ARTIFACT_MANIFEST.json present")
            continue
        rel = str(path.relative_to(ROOT)) if ROOT in path.parents or path.parent == ROOT else path.name
        rec = listed.get(rel) or listed.get(path.name) or listed.get(str(path))
        if rec and rec.get("script") and rec.get("sha256"):
            try:
                actual = sha256_file(path)
            except OSError:
                actual = ""
            if actual and actual == rec.get("sha256"):
                res.add("PASS", f"{path.name} provenance-complete via ARTIFACT_MANIFEST")
                continue
            res.add("WARN", f"{path.name} listed in manifest but sha256 mismatch")
            continue
        blob = load_json(path)
        if not isinstance(blob, dict):
            res.add("WARN", f"{path.name} not an object")
            continue
        meta = blob.get("meta") if isinstance(blob.get("meta"), dict) else {}
        created = (meta or {}).get("created_at") or blob.get("created_at") or blob.get("generated_at") or blob.get("created")
        script = (meta or {}).get("script") or (meta or {}).get("script_name") or blob.get("script") or blob.get("task")
        missing = []
        if not created:
            missing.append("created_at")
        if not script:
            missing.append("script")
        has_inputs = all((meta or {}).get(k) or blob.get(k) for k in input_keys)
        from_db = any(
            k in (meta or {}) or k in blob
            for k in ("postgresql_version", "postgres_version", "pgvector_version")
        )
        if missing or not has_inputs:
            res.add(
                "WARN",
                f"{path.name} incomplete provenance (missing {missing or 'input sha256s'}; "
                f"pre-harness files are warnings)",
            )
        else:
            res.add("PASS", f"{path.name} meta created_at+script+input hashes")
        if from_db:
            pg = (meta or {}).get("postgresql_version") or blob.get("postgresql_version") or blob.get("postgres_version")
            pv = (meta or {}).get("pgvector_version") or blob.get("pgvector_version")
            if not pg or not pv:
                res.add("WARN", f"{path.name} db output missing postgres/pgvector version")
    if res.n_fail == 0 and res.n_pass == 0 and res.n_warn:
        res.status = "WARN"
        return res
    return res.finalize()


def check_cross_implementation(
    ladders: dict[tuple[str, ...], dict[str, Any]] | None = None,
    analysis: dict[str, Any] | None = None,
    rev1: Path = REV1,
    extra_kwargs: dict[str, Any] | None = None,
) -> CheckResult:
    res = CheckResult("CROSS_IMPLEMENTATION", "PASS")
    analysis_path = rev1 / "analysis_exact.json"
    if analysis is None and not analysis_path.is_file():
        res.add("SKIP", f"missing {analysis_path}")
        return res.finalize()
    from crosscheck_stats import load_ladders

    computed = recompute(ladders if ladders is not None else load_canonical_ladders(rev1))
    analysis_blob = analysis if analysis is not None else load_json(analysis_path)
    mismatches = compare_with_analysis(computed, analysis_blob)
    if mismatches:
        for m in mismatches:
            res.add("FAIL", m)
    else:
        n_cells = sum(
            len(scales)
            for banks in computed["hit_at_10"].values()
            for conds in banks.values()
            for scales in conds.values()
        )
        res.add("PASS", f"Hit@10 cells agree ({n_cells}); lift hits/delta exact; CI within 0.01")
    extra = extra_cross_mismatches(rev1=rev1, **(extra_kwargs or {}))
    for m in extra:
        if m.startswith("SKIP:"):
            res.add("SKIP", m[5:].strip())
        elif m.startswith("FAIL:"):
            res.add("FAIL", m[5:].strip())
        else:
            res.add("FAIL", m)
    if not any(m.startswith("FAIL:") for m in extra):
        res.add("PASS", "extra RRF/routing/per-size/uniform cross-checks have no FAILs")
    return res.finalize()


def known_duplicate_ids(claims: list[dict[str, Any]]) -> list[str] | None:
    for c in claims:
        if c.get("id") == "hygiene.known_duplicate_doc_ids":
            exp = c.get("expected")
            if isinstance(exp, list):
                return [str(x) for x in exp]
    return None


def check_data_hygiene(
    manifest_path: Path = MANIFEST_PATH,
    claims_path: Path = CLAIMS_PATH,
) -> CheckResult:
    res = CheckResult("DATA_HYGIENE", "PASS")
    resolved = resolve_scale_manifest(manifest_path)
    if resolved is None:
        res.add("SKIP", f"manifest not committed/present at {manifest_path}")
        return res.finalize()
    manifest_path = resolved
    if manifest_path == COMPACT_MANIFEST_PATH:
        res.add("PASS", f"using compact manifest {manifest_path.name}")
    man = load_json(manifest_path)
    docs = iter_manifest_documents(man)
    counts: dict[str, int] = {}
    for d in docs:
        did = d.get("doc_id")
        counts[did] = counts.get(did, 0) + 1
    dups = sorted(did for did, n in counts.items() if n > 1)
    claims = load_json(claims_path) if claims_path.is_file() else []
    if isinstance(claims, dict):
        claims = claims.get("claims") or []
    dup_art = REV1 / "duplicate_doc_ids.json"
    if dup_art.is_file():
        art = load_json(dup_art)
        art_ids = [str(x) for x in (art.get("duplicate_doc_ids") or [])]
        if set(dups) != set(art_ids):
            res.add(
                "FAIL",
                f"duplicate_doc_ids.json {sorted(art_ids)} != manifest {dups}",
            )
        else:
            res.add("PASS", f"duplicate_doc_ids.json matches manifest: {dups}")
    expected = known_duplicate_ids(claims)
    if expected is None:
        res.add("FAIL", "claims.json missing hygiene.known_duplicate_doc_ids")
        expected = []
    if set(dups) != set(expected):
        res.add("FAIL", f"duplicate doc_ids changed: got {dups} expected {sorted(expected)}")
    else:
        res.add("PASS", f"exactly 3 known duplicated doc_ids: {dups}")
    under = [d for d in docs if d.get("scale_rank") is not None and int(d["scale_rank"]) < 100000]
    n_under = len(under)
    n_distinct = len({d["doc_id"] for d in under})
    print(f"DATA_HYGIENE scale_rank<100000 count={n_under} distinct_ids={n_distinct}")
    if n_under != 100000:
        res.add("FAIL", f"scale_rank<100000 count={n_under} expected 100000")
    elif n_distinct not in (99997, 99998):
        res.add("FAIL", f"distinct ids at scale_rank<100000 = {n_distinct} (want 99997 or 99998)")
    else:
        res.add("PASS", f"scale_rank<100000 n={n_under} distinct={n_distinct}")
    return res.finalize()


def load_claims(path: Path = CLAIMS_PATH) -> list[dict[str, Any]]:
    raw = load_json(path)
    if isinstance(raw, list):
        return raw
    return list(raw.get("claims") or [])


def check_claim_registry(
    claims: list[dict[str, Any]] | None = None,
    root: Path = ROOT,
    claims_path: Path = CLAIMS_PATH,
    tex_path: Path | None = None,
    tex_text: str | None = None,
    skip_tex: bool = False,
) -> CheckResult:
    res = CheckResult("CLAIM_REGISTRY", "PASS")
    from_file = claims is None
    items = claims if claims is not None else (load_claims(claims_path) if claims_path.is_file() else None)
    if not items:
        res.add("FAIL", "claims.json missing or empty")
        return res.finalize()
    if from_file and len(items) < 25:
        res.add("FAIL", f"claims.json has {len(items)} entries, need >= 25")
    cache: dict[str, Any] = {}
    tex = tex_text
    tex_src = tex_path if tex_path is not None else DEFAULT_TEX_PATH
    if skip_tex:
        tex = None
        tex_checked = False
    elif tex is not None:
        tex_checked = True
    elif tex_src.is_file():
        tex = tex_src.read_text(encoding="utf-8")
        tex_checked = True
    else:
        tex = None
        tex_checked = False
        res.add("SKIP", f"tex checking skipped ({tex_src} not in checkout)")
    for claim in items:
        cid = claim.get("id")
        rel = claim.get("artifact")
        if rel and Path(str(rel)).name == "n400_lift_slope.json":
            res.add("FAIL", f"{cid}: circular artifact n400_lift_slope.json (compute from ladder)")
            continue
        path = root / rel
        if not path.is_file():
            res.add("SKIP", f"{cid}: artifact not present ({rel})")
            continue
        if claim.get("compute") == "n400_lift_slope":
            try:
                actual = n400_lift_slope_from_ladder(load_json(path))
            except (ValueError, KeyError, TypeError) as exc:
                res.add("FAIL", f"{cid}: n400_lift_slope {exc}")
                continue
        else:
            if str(path) not in cache:
                cache[str(path)] = load_json(path)
            try:
                actual = resolve_path(cache[str(path)], claim.get("json_path") or [])
            except (KeyError, IndexError, TypeError) as exc:
                res.add("FAIL", f"{cid}: path {claim.get('json_path')} {exc}")
                continue
        tol = float(claim.get("tolerance") or 0.0)
        value_ok = numbers_close(actual, claim.get("expected"), tol)
        if value_ok:
            res.add("PASS", f"{cid}")
        else:
            res.add("FAIL", f"{cid}: actual={actual!r} expected={claim.get('expected')!r} tol={tol}")
        strings = claim.get("tex_strings") or []
        extra_files = [root / p for p in (claim.get("tex_files") or [])]
        extra_ok: dict[str, str] = {}
        for ep in extra_files:
            if ep.is_file():
                extra_ok[str(ep)] = ep.read_text(encoding="utf-8")
            else:
                res.add("SKIP", f"{cid}: tex_file missing {ep}")
        if not strings:
            continue
        if skip_tex or not tex_checked:
            res.add("SKIP", f"{cid}: tex_strings not checked")
            continue
        haystacks = [tex] + list(extra_ok.values())
        for s in strings:
            if not any(s in h for h in haystacks):
                res.add("FAIL", f"{cid}: tex_string absent {s!r}")
    return res.finalize()


CHECKS: dict[str, Callable[..., CheckResult]] = {
    "SCHEMA": check_schema,
    "INVARIANTS": check_invariants,
    "SEARCH_MODE_TRUTH": check_search_mode_truth,
    "QUERY_VECTOR_PROVENANCE": check_query_vector_provenance,
    "ARTIFACT_PROVENANCE": check_artifact_provenance,
    "CROSS_IMPLEMENTATION": check_cross_implementation,
    "DATA_HYGIENE": check_data_hygiene,
    "CLAIM_REGISTRY": check_claim_registry,
}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--checks",
        default=",".join(CHECKS),
        help="comma-separated check names",
    )
    parser.add_argument(
        "--tex",
        type=Path,
        default=None,
        help=(
            "manuscript path for CLAIM_REGISTRY tex_strings "
            "(default: papers/.../main.tex if it contains 'Exact-Search Ladder', else data/main_current.tex)"
        ),
    )
    parser.add_argument(
        "--skip-tex",
        action="store_true",
        help="do not check tex_strings (CI subset)",
    )
    args = parser.parse_args(argv)
    names = [x.strip() for x in args.checks.split(",") if x.strip()]
    results: list[CheckResult] = []
    for name in names:
        fn = CHECKS.get(name)
        if fn is None:
            print(f"unknown check {name}", file=sys.stderr)
            return 2
        if name == "CLAIM_REGISTRY":
            tex_path = args.tex if args.tex is not None else resolve_default_tex()
            res = fn(tex_path=tex_path, skip_tex=args.skip_tex)
        else:
            res = fn()
        print_result(res)
        results.append(res)
    failed = [r for r in results if r.status == "FAIL"]
    print("---")
    for r in results:
        print(f"{r.status}\t{r.name}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
