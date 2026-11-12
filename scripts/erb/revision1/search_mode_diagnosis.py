#!/usr/bin/env python3
"""Diagnose pgvector latency, planner choices, and iterative_scan ordering (revision 1, W2)."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from itertools import combinations
from pathlib import Path
from typing import Any

_REV1_DIR = Path(__file__).resolve().parent
if str(_REV1_DIR) not in sys.path:
    sys.path.insert(0, str(_REV1_DIR))
from explain_audit import SCAN_NODE_TYPES, TABLE_SCAN_TYPES, summarize_plan

import numpy as np
import psycopg2

ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / "data"
PUB = ROOT / "artifacts" / "published"
REV1 = PUB / "revision1"
MANIFEST_PATH = DATA / "erb_scale_manifest.json"
BANK_PATH = PUB / "primary_questions_200.json"
OPENAI_CACHE = DATA / "erb_query_embed_cache.json"
TITAN_CACHE = DATA / "erb_titan_query_embed_cache.json"
PLAN_AUDIT_TEMPLATE = REV1 / "plan_audit_{port}.json"

TOP_K = 10
HNSW_INDEX_OPENAI = "idx_chunks_embedding_hnsw"
HNSW_INDEX_TITAN = "idx_chunks_titan_embedding_hnsw"
BTREE_INDEXES = {
    "idx_chunks_scale_rank",
    "idx_chunks_source_type",
    "idx_chunks_titan_scale_rank",
    "idx_chunks_titan_source_type",
}
VEC_IN_BRACKETS = re.compile(r"\[[-+0-9eE.,\s]{80,}\]")

TIMING_SCALES = (5000, 50000, 100000)
TIMING_EFS = (200, 400, 800)
E2_EFS = (100, 200, 300, 400, 500, 600, 800)
E3_SCALES = (5000, 25000, 100000)
E3_MODES = ("off", "strict_order", "relaxed_order")
E4_SCALES = (25000, 40000, 50000, 75000)
E4_PAIRS = ((25000, 40000), (40000, 50000), (50000, 75000), (75000, 100000))
HNSW_RECALL_SCALES_OPENAI_RAW = (
    10000,
    15000,
    20000,
    25000,
    40000,
    50000,
    75000,
    100000,
)
META_MIXED_SCALES = (40000, 50000, 75000, 100000)


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def vector_literal(vec: list[float]) -> str:
    return "[" + ",".join(str(v) for v in vec) + "]"


def median(xs: list[float]) -> float:
    if not xs:
        return float("nan")
    return float(np.median(np.asarray(xs, dtype=np.float64)))


def percentile(xs: list[float], p: float) -> float:
    if not xs:
        return float("nan")
    return float(np.percentile(np.asarray(xs, dtype=np.float64), p))


def json_sanitize(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {k: json_sanitize(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [json_sanitize(v) for v in obj]
    if isinstance(obj, float) and (obj != obj or obj in (float("inf"), float("-inf"))):
        return None
    return obj


def write_json_atomic(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(
        json.dumps(json_sanitize(obj), indent=2, ensure_ascii=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    tmp.replace(path)


def pg_connect(port: int):
    conn = psycopg2.connect(
        host=os.environ.get("PGHOST", "localhost"),
        port=int(port),
        user=os.environ["PGUSER"],
        password=os.environ["PGPASSWORD"],
        dbname=os.environ["PGDATABASE"],
        connect_timeout=15,
    )
    conn.autocommit = True
    return conn


def load_questions() -> list[dict]:
    bank = json.loads(BANK_PATH.read_text(encoding="utf-8"))
    eval_ids = list(bank["question_ids"])
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    by_eval = {q["eval_id"]: q for q in manifest.get("questions") or []}
    missing = [e for e in eval_ids if e not in by_eval]
    if missing:
        raise SystemExit(f"manifest missing {len(missing)} eval_ids")
    out = []
    for e in eval_ids:
        q = dict(by_eval[e])
        q["eval_id"] = e
        q["question_id"] = e
        out.append(q)
    return out


def load_openai_cache(eval_ids: list[str]) -> dict[str, list[float]]:
    raw = json.loads(OPENAI_CACHE.read_text(encoding="utf-8"))
    cache: dict[str, list[float]] = {}
    for eid in eval_ids:
        v = raw.get(eid)
        if isinstance(v, list):
            cache[eid] = v
        elif isinstance(v, dict) and "embedding" in v:
            cache[eid] = list(v["embedding"])
    missing = [e for e in eval_ids if e not in cache]
    if missing:
        raise SystemExit(f"OpenAI cache missing {len(missing)} embeddings")
    return cache


def load_titan_cache(eval_ids: list[str]) -> dict[str, list[float]]:
    raw = json.loads(TITAN_CACHE.read_text(encoding="utf-8"))
    vecs = raw.get("vectors") or {}
    cache: dict[str, list[float]] = {}
    for eid in eval_ids:
        v = vecs.get(eid)
        if isinstance(v, list):
            cache[eid] = v
    missing = [e for e in eval_ids if e not in cache]
    if missing:
        raise SystemExit(f"Titan cache missing {len(missing)} embeddings")
    return cache


def meta_filter(question: dict) -> tuple[str, tuple]:
    sts = question.get("source_types") or []
    if not sts:
        return "", ()
    return " AND source_type = %s", (str(sts[0]),)


def condition_extra(question: dict, condition: str) -> tuple[str, tuple]:
    if condition == "raw":
        return "", ()
    if condition in ("meta", "meta_first"):
        extra, params = meta_filter(question)
        if not params:
            return " AND 1=0", ()
        return extra, params
    if condition == "meta_in":
        sts = [str(s) for s in (question.get("source_types") or []) if s]
        if not sts:
            return " AND 1=0", ()
        return " AND source_type = ANY(%s)", (sts,)
    raise ValueError(f"unknown condition: {condition}")


def build_sql(table: str, condition: str, *, exact_tiebreak: bool = False) -> str:
    """Approximate eval matches ``eval_scale_raw`` (distance only). Exact ref uses doc_id tie-break."""
    if condition in ("meta", "meta_first"):
        meta_sql = " AND source_type = %s"
    elif condition == "meta_in":
        meta_sql = " AND source_type = ANY(%s)"
    else:
        meta_sql = ""
    order = "ORDER BY embedding <=> %s::vector"
    if exact_tiebreak:
        order += ", doc_id"
    return f"""
            SELECT doc_id, 1 - (embedding <=> %s::vector) AS score
            FROM {table}
            WHERE embedding IS NOT NULL
              AND scale_rank IS NOT NULL
              AND scale_rank < %s
              {meta_sql}
            {order}
            LIMIT %s
        """


def list_recall_against_exact(exact_ids: list[str], approx_ids: list[str]) -> float:
    if not exact_ids:
        return float("nan")
    return len(set(exact_ids) & set(approx_ids)) / len(exact_ids)


def question_hit_at_10(question: dict, retrieved: list[str]) -> bool:
    expected = {str(x) for x in (question.get("expected_doc_ids") or []) if x}
    for i, doc_id in enumerate(retrieved[:TOP_K], start=1):
        if doc_id in expected:
            return i <= TOP_K
    return False


def mean_hit_at_10(questions: list[dict], sweep: dict[str, Any]) -> float:
    by_eid = {r["eval_id"]: r for r in sweep.get("per_question") or []}
    hits: list[float] = []
    for q in questions:
        row = by_eid.get(q["eval_id"]) or {}
        hits.append(1.0 if question_hit_at_10(q, row.get("doc_ids") or []) else 0.0)
    return round(float(np.mean(hits)) if hits else float("nan"), 4)


def mean_hit_at_10_from_exact_map(questions: list[dict], exact_map: dict[str, list[str]]) -> float:
    hits = [1.0 if question_hit_at_10(q, exact_map.get(q["eval_id"]) or []) else 0.0 for q in questions]
    return round(float(np.mean(hits)) if hits else float("nan"), 4)


def compare_to_exact_with_hits(
    questions: list[dict],
    sweep: dict[str, Any],
    exact_map: dict[str, list[str]],
) -> dict[str, Any]:
    base = compare_to_exact(sweep, exact_map)
    base["mean_hit_at_10_approx"] = mean_hit_at_10(questions, sweep)
    base["mean_hit_at_10_exact_ref"] = mean_hit_at_10_from_exact_map(questions, exact_map)
    base["hit_at_10_loss"] = round(
        base["mean_hit_at_10_exact_ref"] - base["mean_hit_at_10_approx"], 4
    )
    return base


def scores_non_increasing(scores: list[float]) -> bool:
    for i in range(1, len(scores)):
        if scores[i] > scores[i - 1] + 1e-12:
            return False
    return True


def question_swaps_order(list_lo: list[str], list_hi: list[str]) -> bool:
    common = [d for d in list_lo if d in set(list_hi)]
    if len(common) < 2:
        return False
    pos_lo = {d: i for i, d in enumerate(list_lo)}
    pos_hi = {d: i for i, d in enumerate(list_hi)}
    for a, b in combinations(common, 2):
        d_lo = pos_lo[a] - pos_lo[b]
        d_hi = pos_hi[a] - pos_hi[b]
        if d_lo * d_hi < 0:
            return True
    return False


def walk_plan(node: dict, acc: dict) -> None:
    ntype = str(node.get("Node Type") or "")
    acc["node_types"].append(ntype)
    idx = node.get("Index Name")
    if idx:
        acc["index_names"].append(str(idx))
    for child in node.get("Plans") or []:
        if isinstance(child, dict):
            walk_plan(child, acc)


def summarize_explain_json(root: dict, hnsw_index: str) -> dict[str, Any]:
    plan = root.get("Plan") or {}
    acc: dict[str, Any] = {"node_types": [], "index_names": []}
    walk_plan(plan, acc)
    node_types = acc["node_types"]
    index_names = acc["index_names"]
    hnsw_used = hnsw_index in index_names
    return {
        "node_types_unique": list(dict.fromkeys(node_types)),
        "index_names": list(dict.fromkeys(index_names)),
        "hnsw_used": bool(hnsw_used),
        "seq_scan": "Seq Scan" in node_types,
        "has_sort": "Sort" in node_types,
        "btree_filter": any(n in BTREE_INDEXES for n in index_names),
        "exec_ms": float(root.get("Execution Time") or 0.0),
        "planning_ms": float(root.get("Planning Time") or 0.0),
    }


def sanitize_plan(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {str(k): sanitize_plan(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [sanitize_plan(v) for v in obj]
    if isinstance(obj, str):
        if len(obj) > 120 and ("<=>" in obj or obj.strip().startswith("[")):
            return VEC_IN_BRACKETS.sub("[VECTOR]", obj)
        return obj
    return obj


class Session:
    def __init__(self, cur, table: str, hnsw_index: str):
        self.cur = cur
        self.table = table
        self.hnsw_index = hnsw_index
        self._exact_mode = False

    def reset_planner_defaults(self) -> None:
        self.cur.execute("SET enable_indexscan = on")
        self.cur.execute("SET enable_indexonlyscan = on")
        self.cur.execute("SET enable_bitmapscan = on")
        self.cur.execute("SET enable_seqscan = on")
        self.cur.execute("SET enable_sort = on")
        self.cur.execute("SET hnsw.ef_search = 40")
        self.cur.execute("SET hnsw.iterative_scan = off")
        self.cur.execute("SET hnsw.max_scan_tuples = 20000")
        self.cur.execute("SET hnsw.scan_mem_multiplier = 1")
        self._exact_mode = False

    def set_gucs(
        self,
        *,
        ef_search: int = 200,
        iterative_scan: str = "relaxed_order",
        max_scan_tuples: int | None = None,
        scan_mem_multiplier: int | None = None,
        force_hnsw: bool = False,
        exact_mode: bool = False,
    ) -> dict[str, Any]:
        self._exact_mode = exact_mode
        self.reset_planner_defaults()
        self.cur.execute(f"SET hnsw.ef_search = {int(ef_search)}")
        guc: dict[str, Any] = {"ef_search": int(ef_search), "iterative_scan": iterative_scan}
        if exact_mode:
            self.cur.execute("SET enable_indexscan = off")
            self.cur.execute("SET enable_bitmapscan = off")
            guc["enable_indexscan"] = "off"
            guc["enable_bitmapscan"] = "off"
        elif force_hnsw:
            self.cur.execute("SET enable_seqscan = off")
            self.cur.execute("SET enable_bitmapscan = off")
            self.cur.execute("SET enable_sort = off")
            self.cur.execute("SET enable_indexonlyscan = off")
            guc["force_hnsw"] = True
            guc["enable_seqscan"] = "off"
            guc["enable_sort"] = "off"
            guc["enable_indexonlyscan"] = "off"
        if max_scan_tuples is not None:
            self.cur.execute(f"SET hnsw.max_scan_tuples = {int(max_scan_tuples)}")
            guc["max_scan_tuples"] = int(max_scan_tuples)
        if scan_mem_multiplier is not None:
            self.cur.execute(f"SET hnsw.scan_mem_multiplier = {int(scan_mem_multiplier)}")
            guc["scan_mem_multiplier"] = int(scan_mem_multiplier)
        if iterative_scan == "off":
            try:
                self.cur.execute("SET hnsw.iterative_scan = off")
            except Exception as exc:
                guc["iterative_scan_error"] = str(exc)
        else:
            try:
                self.cur.execute(f"SET hnsw.iterative_scan = {iterative_scan}")
            except Exception as exc:
                guc["iterative_scan_error"] = str(exc)
        return guc

    def fetch_list(
        self,
        question: dict,
        scale: int,
        condition: str,
        qvec: list[float],
    ) -> tuple[list[str], list[float], float]:
        lit = vector_literal(qvec)
        eid = question["eval_id"]
        extra_where, extra_params = condition_extra(question, condition)
        if condition != "raw" and not extra_params and extra_where == " AND 1=0":
            return [], [], 0.0
        sql = build_sql(self.table, condition, exact_tiebreak=self._exact_mode)
        params = (lit, scale, *extra_params, lit, TOP_K)
        t0 = time.perf_counter()
        self.cur.execute(sql, params)
        rows = self.cur.fetchall()
        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        doc_ids = [str(r[0]) for r in rows if r[0]]
        scores = [float(r[1]) for r in rows]
        return doc_ids, scores, elapsed_ms

    def explain_one(
        self,
        question: dict,
        scale: int,
        condition: str,
        qvec: list[float],
        *,
        analyze: bool = True,
    ) -> dict[str, Any]:
        lit = vector_literal(qvec)
        extra_where, extra_params = condition_extra(question, condition)
        sql = build_sql(self.table, condition, exact_tiebreak=False)
        params = (lit, scale, *extra_params, lit, TOP_K)
        fmt = "EXPLAIN (FORMAT JSON)"
        if analyze:
            fmt = "EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON)"
        self.cur.execute(fmt + "\n" + sql, params)
        raw = self.cur.fetchone()[0]
        root = raw[0] if isinstance(raw, list) else json.loads(raw)[0]
        summary = summarize_explain_json(root, self.hnsw_index)
        summary["plan"] = sanitize_plan(root)
        summary["eval_id"] = question["eval_id"]
        summary["scale"] = scale
        summary["condition"] = condition
        return summary


def sweep_questions(
    sess: Session,
    questions: list[dict],
    qvecs: dict[str, list[float]],
    *,
    scale: int,
    condition: str,
    ef_search: int = 200,
    iterative_scan: str = "relaxed_order",
    max_scan_tuples: int | None = None,
    scan_mem_multiplier: int | None = None,
    force_hnsw: bool = False,
    exact_mode: bool = False,
    collect_lists: bool = True,
) -> dict[str, Any]:
    guc = sess.set_gucs(
        ef_search=ef_search,
        iterative_scan=iterative_scan,
        max_scan_tuples=max_scan_tuples,
        scan_mem_multiplier=scan_mem_multiplier,
        force_hnsw=force_hnsw,
        exact_mode=exact_mode,
    )
    times_ms: list[float] = []
    per_q: list[dict] = []
    t_sweep = time.perf_counter()
    for q in questions:
        eid = q["eval_id"]
        if eid not in qvecs:
            continue
        doc_ids, scores, ms = sess.fetch_list(q, scale, condition, qvecs[eid])
        times_ms.append(ms)
        row: dict[str, Any] = {"eval_id": eid, "elapsed_ms": round(ms, 3)}
        if collect_lists:
            row["doc_ids"] = doc_ids
            row["scores"] = scores
            row["scores_non_increasing"] = scores_non_increasing(scores)
        per_q.append(row)
    sweep_s = time.perf_counter() - t_sweep
    return {
        "guc": guc,
        "scale": scale,
        "condition": condition,
        "ef_search": ef_search,
        "iterative_scan": iterative_scan,
        "exact_mode": exact_mode,
        "n_queries": len(times_ms),
        "sweep_elapsed_s": round(sweep_s, 3),
        "sum_query_ms": round(sum(times_ms), 3),
        "median_query_ms": round(median(times_ms), 3),
        "p50_query_ms": round(percentile(times_ms, 50), 3),
        "p90_query_ms": round(percentile(times_ms, 90), 3),
        "p95_query_ms": round(percentile(times_ms, 95), 3),
        "p99_query_ms": round(percentile(times_ms, 99), 3),
        "per_question": per_q,
    }


def exact_refs_scratch(port: int, scratch_suffix: str | None = None) -> Path:
    if scratch_suffix:
        return DATA / f"rev1_search_mode_exact_refs_{scratch_suffix}.json"
    return DATA / f"rev1_search_mode_exact_refs_{port}.json"


def build_exact_refs(
    sess: Session,
    questions: list[dict],
    qvecs: dict[str, list[float]],
    scales: tuple[int, ...],
    conditions: tuple[str, ...],
    *,
    port: int,
    scratch_suffix: str | None = None,
) -> dict[str, dict[str, list[str]]]:
    scratch = exact_refs_scratch(port, scratch_suffix)
    refs: dict[str, dict[str, list[str]]] = {}
    if scratch.exists():
        refs = json.loads(scratch.read_text(encoding="utf-8"))
    needed = [f"{c}|{s}" for s in scales for c in conditions if f"{c}|{s}" not in refs]
    for key in needed:
        condition, scale_s = key.split("|", 1)
        scale = int(scale_s)
        print(f"exact reference {key} …", flush=True)
        sw = sweep_questions(
            sess,
            questions,
            qvecs,
            scale=int(scale),
            condition=condition,
            exact_mode=True,
            collect_lists=True,
        )
        refs[key] = {r["eval_id"]: r["doc_ids"] for r in sw["per_question"]}
        write_json_atomic(scratch, refs)
    sess.reset_planner_defaults()
    return {k: refs[k] for k in (f"{c}|{s}" for s in scales for c in conditions) if k in refs}


def verify_exact_refs_independent(
    sess: Session,
    questions: list[dict],
    qvecs: dict[str, list[float]],
    stored_refs: dict[str, dict[str, list[str]]],
) -> dict[str, Any]:
    """Second exact pass; compare lists to stored reference maps."""
    n_lists = 0
    n_identical = 0
    mismatches: list[str] = []
    for key, stored_map in stored_refs.items():
        condition, scale_s = key.split("|", 1)
        scale = int(scale_s)
        sess.reset_planner_defaults()
        sw = sweep_questions(
            sess,
            questions,
            qvecs,
            scale=scale,
            condition=condition,
            exact_mode=True,
            iterative_scan="off",
            collect_lists=True,
        )
        for q in questions:
            eid = q["eval_id"]
            fresh = next((r["doc_ids"] for r in sw["per_question"] if r["eval_id"] == eid), [])
            stored = stored_map.get(eid) or []
            n_lists += 1
            if fresh == stored:
                n_identical += 1
            elif len(mismatches) < 5:
                mismatches.append(f"{key}:{eid}")
    sess.reset_planner_defaults()
    frac = round(n_identical / n_lists, 6) if n_lists else float("nan")
    return {
        "n_lists_compared": n_lists,
        "n_identical": n_identical,
        "frac_identical": frac,
        "status": "PASS" if n_lists and n_identical == n_lists else "FAIL",
        "sample_mismatches": mismatches,
    }


def tie_handling_check(
    sess: Session,
    questions: list[dict],
    qvecs: dict[str, list[float]],
    scales: tuple[int, ...],
    conditions: tuple[str, ...],
) -> dict[str, Any]:
    """Exact top-11 pass: score tie at ranks 10/11 and duplicate scores in top 10."""
    sess.reset_planner_defaults()
    tie_10_11: list[dict] = []
    dup_in_top10 = 0
    lists_checked = 0

    def fetch_n(
        question: dict,
        scale: int,
        condition: str,
        qvec: list[float],
        limit: int,
    ) -> tuple[list[str], list[float]]:
        lit = vector_literal(qvec)
        extra_sql, extra_params = condition_extra(question, condition)
        if condition != "raw" and not extra_params and extra_sql == " AND 1=0":
            return [], []
        meta_sql = extra_sql
        sql = f"""
            SELECT doc_id, 1 - (embedding <=> %s::vector) AS score
            FROM {sess.table}
            WHERE embedding IS NOT NULL
              AND scale_rank IS NOT NULL
              AND scale_rank < %s
              {meta_sql}
            ORDER BY embedding <=> %s::vector, doc_id
            LIMIT %s
        """
        params = (lit, scale, *extra_params, lit, limit)
        sess.set_gucs(exact_mode=True, iterative_scan="off")
        sess.cur.execute(sql, params)
        rows = sess.cur.fetchall()
        return [str(r[0]) for r in rows if r[0]], [float(r[1]) for r in rows]

    for key in (f"{c}|{s}" for s in scales for c in conditions):
        condition, scale_s = key.split("|", 1)
        scale = int(scale_s)
        for q in questions:
            eid = q["eval_id"]
            if eid not in qvecs:
                continue
            doc_ids, scores = fetch_n(q, scale, condition, qvecs[eid], 11)
            lists_checked += 1
            if len(scores) >= 11:
                tied = abs(scores[9] - scores[10]) <= 1e-12
                if tied:
                    tie_10_11.append({"key": key, "eval_id": eid, "score_10": scores[9], "score_11": scores[10]})
            if len(scores) >= 2:
                top = scores[: min(10, len(scores))]
                if len(top) != len(set(round(x, 15) for x in top)):
                    dup_in_top10 += 1
    sess.reset_planner_defaults()
    return {
        "n_lists_checked": lists_checked,
        "n_rank10_11_score_ties": len(tie_10_11),
        "rank10_11_tie_samples": tie_10_11[:10],
        "n_lists_duplicate_scores_in_top10": dup_in_top10,
        "hit_at_10_impact_note": (
            "Ties at rank 10/11 can change which doc occupies rank 10 under doc_id tie-break; "
            "Hit@10 uses set membership of top-10 ids, not rank-11."
        ),
    }


def deepest_table_scan_node(plan: dict) -> dict[str, str] | None:
    found: list[tuple[str, str | None]] = []

    def walk(node: dict) -> None:
        ntype = str(node.get("Node Type") or "")
        if ntype in TABLE_SCAN_TYPES:
            idx = node.get("Index Name")
            found.append((ntype, str(idx) if idx else None))
        for child in node.get("Plans") or []:
            if isinstance(child, dict):
                walk(child)

    walk(plan)
    if not found:
        return None
    ntype, idx = found[-1]
    return {"node_type": ntype, "index_name": idx or ""}


def first_multi_source_question(questions: list[dict]) -> dict | None:
    for q in questions:
        if len(q.get("source_types") or []) > 1:
            return q
    return None


def hnsw_plan_probe_questions(questions: list[dict]) -> list[dict]:
    probes: list[dict] = [questions[0]]
    multi = first_multi_source_question(questions)
    if multi and multi["eval_id"] != probes[0]["eval_id"]:
        probes.append(multi)
    last = questions[-1]
    if last["eval_id"] not in {p["eval_id"] for p in probes}:
        probes.append(last)
    return probes


def verify_cell_hnsw_plans(
    sess: Session,
    questions: list[dict],
    qvecs: dict[str, list[float]],
    *,
    scale: int,
    condition: str,
    ef_search: int,
    force_hnsw: bool,
) -> dict[str, Any]:
    probes = hnsw_plan_probe_questions(questions)
    sess.set_gucs(
        ef_search=ef_search,
        iterative_scan="relaxed_order",
        force_hnsw=force_hnsw,
    )
    probe_rows: list[dict[str, Any]] = []
    failing_plan: dict[str, Any] | None = None
    for q in probes:
        eid = q["eval_id"]
        if eid not in qvecs:
            probe_rows.append({"eval_id": eid, "skipped": True, "reason": "missing_query_vector"})
            continue
        plan = sess.explain_one(q, scale, condition, qvecs[eid], analyze=False)
        idx_names = list(plan.get("index_names") or [])
        hnsw_name = next((n for n in idx_names if "hnsw" in n.lower()), None)
        row = {
            "eval_id": eid,
            "hnsw_used": bool(plan.get("hnsw_used")),
            "hnsw_index_name": hnsw_name,
            "index_names": idx_names,
            "node_types_unique": plan.get("node_types_unique"),
        }
        probe_rows.append(row)
        if force_hnsw and not row["hnsw_used"] and failing_plan is None:
            failing_plan = {
                "eval_id": eid,
                "plan": plan.get("plan"),
                "index_names": idx_names,
                "node_types_unique": plan.get("node_types_unique"),
            }
    sess.reset_planner_defaults()
    executed = [p for p in probe_rows if not p.get("skipped")]
    all_hnsw = bool(executed) and all(p["hnsw_used"] for p in executed)
    out: dict[str, Any] = {"probes": probe_rows, "all_probes_hnsw": all_hnsw}
    if force_hnsw and not all_hnsw:
        out["plan_error"] = (
            "forced_hnsw probes did not all use an HNSW index scan "
            f"(scale={scale}, condition={condition}, ef={ef_search})"
        )
        if failing_plan:
            out["plan_error_detail"] = failing_plan
    return out


def compare_to_exact(
  sweep: dict[str, Any],
  exact_map: dict[str, list[str]],
) -> dict[str, Any]:
    recalls: list[float] = []
    identical = 0
    n = 0
    for row in sweep["per_question"]:
        eid = row["eval_id"]
        approx = row.get("doc_ids") or []
        exact = exact_map.get(eid) or []
        lr = list_recall_against_exact(exact, approx)
        recalls.append(lr)
        if approx == exact:
            identical += 1
        n += 1
    return {
        "mean_list_recall_at_10": round(float(np.mean(recalls)) if recalls else float("nan"), 4),
        "frac_lists_identical_to_exact": round(identical / n, 4) if n else float("nan"),
        "n_questions": n,
    }


_AUDIT_CACHE: dict[int, list[dict]] = {}


def load_audit_cells(port: int) -> list[dict]:
    if port in _AUDIT_CACHE:
        return _AUDIT_CACHE[port]
    path = PLAN_AUDIT_TEMPLATE.with_name(PLAN_AUDIT_TEMPLATE.name.format(port=port))
    if not path.exists():
        _AUDIT_CACHE[port] = []
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    cells = list(data.get("cells") or [])
    _AUDIT_CACHE[port] = cells
    return cells


def load_audit_timing(port: int, table: str, condition: str, scale: int, ef: int) -> dict[str, Any] | None:
    cell = None
    for c in load_audit_cells(port):
        if (
            c.get("pass") == "forward"
            and c.get("table") == table
            and c.get("condition") == condition
            and int(c.get("scale") or -1) == int(scale)
            and int(c.get("ef_search") or -1) == int(ef)
        ):
            cell = c
            break
    if not cell:
        return None
    queries = cell.get("queries") or []
    exec_sum = sum(float(q.get("exec_ms") or 0.0) for q in queries)
    n_audit = len(queries)
    mean_audit_ms = (exec_sum / n_audit) if n_audit else float("nan")
    return {
        "n_plans": n_audit,
        "n_queries_sample": n_audit,
        "median_exec_ms": cell.get("median_exec_ms"),
        "mean_exec_ms": round(mean_audit_ms, 4),
        "sum_exec_ms": round(exec_sum, 3),
        "sum_exec_s": round(exec_sum / 1000.0, 3),
        "frac_hnsw": cell.get("frac_hnsw"),
    }


def explain_cost_matrix(
    sess: Session,
    questions: list[dict],
    qvecs: dict[str, list[float]],
    scale: int,
    condition: str,
    exact_map: dict[str, list[str]],
    ef_values: tuple[int, ...] = E2_EFS,
) -> list[dict[str, Any]]:
    sql = build_sql(sess.table, condition, exact_tiebreak=False)
    rows: list[dict] = []
    for ef in ef_values:
        default_costs: list[float] = []
        forced_costs: list[float] = []
        scan_types: set[str] = set()
        for q in questions:
            eid = q["eval_id"]
            if eid not in qvecs:
                continue
            lit = vector_literal(qvecs[eid])
            extra_params: tuple = ()
            _, extra_params = condition_extra(q, condition)
            if condition != "raw" and not extra_params:
                continue
            params = (lit, scale, *extra_params, lit, TOP_K)
            sess.set_gucs(ef_search=ef, iterative_scan="relaxed_order")
            sess.cur.execute("EXPLAIN (FORMAT JSON)\n" + sql, params)
            def_cost = sess.cur.fetchone()[0]
            def_root = def_cost[0] if isinstance(def_cost, list) else json.loads(def_cost)[0]
            default_costs.append(float((def_root.get("Plan") or {}).get("Total Cost") or 0.0))
            sess.cur.execute("SET enable_seqscan = off")
            sess.cur.execute("SET enable_bitmapscan = off")
            sess.cur.execute("EXPLAIN (FORMAT JSON)\n" + sql, params)
            hnsw_cost = sess.cur.fetchone()[0]
            hnsw_root = hnsw_cost[0] if isinstance(hnsw_cost, list) else json.loads(hnsw_cost)[0]
            forced_costs.append(float((hnsw_root.get("Plan") or {}).get("Total Cost") or 0.0))
            st = deepest_table_scan_node(hnsw_root.get("Plan") or {})
            if st:
                label = st["node_type"]
                if st.get("index_name"):
                    label = f"{label} using {st['index_name']}"
                scan_types.add(label)
            sess.reset_planner_defaults()
        sw_forced = sweep_questions(
            sess,
            questions,
            qvecs,
            scale=scale,
            condition=condition,
            ef_search=ef,
            iterative_scan="relaxed_order",
            force_hnsw=True,
            collect_lists=True,
        )
        sess.reset_planner_defaults()
        vs = compare_to_exact_with_hits(questions, sw_forced, exact_map)
        rows.append(
            {
                "ef_search": ef,
                "n_queries_cost_explained": len(default_costs),
                "median_default_total_cost": round(median(default_costs), 3),
                "median_forced_hnsw_total_cost": round(median(forced_costs), 3),
                "forced_hnsw_table_scan_node_types": sorted(scan_types),
                "forced_hnsw_vs_exact": vs,
            }
        )
    return rows


def plan_audit_loops_check_rows(port: int) -> list[dict[str, Any]]:
    path = PLAN_AUDIT_TEMPLATE.with_name(PLAN_AUDIT_TEMPLATE.name.format(port=port))
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    rows: list[dict] = []
    for cell in data.get("cells") or []:
        ex = cell.get("example_plan")
        if not ex or not isinstance(ex, dict) or "Plan" not in ex:
            continue
        root = {
            "Plan": ex["Plan"],
            "Execution Time": ex.get("Execution Time", 0),
            "Planning Time": ex.get("Planning Time", 0),
        }
        fixed = summarize_plan(root)
        qs = cell.get("queries") or []
        old = qs[0].get("scan_actual_rows") if qs else None
        rows.append(
            {
                "port": port,
                "pass": cell.get("pass"),
                "table": cell.get("table"),
                "condition": cell.get("condition"),
                "scale": cell.get("scale"),
                "ef_search": cell.get("ef_search"),
                "old_scan_actual_rows": old,
                "corrected_scan_actual_rows": fixed.get("scan_actual_rows"),
                "scan_actual_rows_per_loop": fixed.get("scan_actual_rows_per_loop"),
                "delta": (
                    (fixed.get("scan_actual_rows") or 0) - (old or 0)
                    if old is not None and fixed.get("scan_actual_rows") is not None
                    else None
                ),
            }
        )
    return rows


def write_plan_audit_loops_check() -> Path:
    rows = plan_audit_loops_check_rows(5434) + plan_audit_loops_check_rows(5433)
    out = REV1 / "plan_audit_loops_check.json"
    obj = {"generated_at": utc_now(), "n_cells": len(rows), "cells": rows}
    write_json_atomic(out, obj)
    return out


def hnsw_recall_cells_from_audit(port: int) -> list[dict]:
    cells = []
    for c in load_audit_cells(port):
        if c.get("pass") != "forward":
            continue
        if int(c.get("ef_search") or -1) not in (200, 400, 800):
            continue
        cells.append(c)
    return cells


def hnsw_recall_work_cells(
    port: int,
    scales: tuple[int, ...] | None = None,
) -> list[dict[str, Any]]:
    """Audit cells plus meta_in duplicates (plan audit labels meta as meta_first)."""
    out: list[dict[str, Any]] = []
    for c in hnsw_recall_cells_from_audit(port):
        scale = int(c.get("scale") or 0)
        if scales is not None and scale not in scales:
            continue
        cond = str(c.get("condition") or "raw")
        if cond == "meta":
            for mc in ("meta_first", "meta_in"):
                out.append(
                    {
                        **c,
                        "condition": mc,
                        "frac_hnsw_audit": float(c.get("frac_hnsw") or 0.0),
                    }
                )
        else:
            out.append({**c, "condition": cond, "frac_hnsw_audit": float(c.get("frac_hnsw") or 0.0)})
    return out


def run_hnsw_recall_by_cell(
    port: int,
    questions: list[dict],
    openai: Session,
    titan: Session,
    qvecs_openai: dict[str, list[float]],
    qvecs_titan: dict[str, list[float]],
    openai_refs: dict[str, dict[str, list[str]]],
    titan_refs: dict[str, dict[str, list[str]]],
    *,
    scales: tuple[int, ...] | None = None,
    scratch_suffix: str | None = None,
) -> list[dict[str, Any]]:
    table_map = {
        "document_chunks": (openai, qvecs_openai, openai_refs, None),
        "document_chunks_titan": (titan, qvecs_titan, titan_refs, scratch_suffix),
    }
    out: list[dict] = []
    for cell in hnsw_recall_work_cells(port, scales=scales):
        table = cell.get("table")
        if table not in table_map:
            continue
        sess, qvecs, all_refs, titan_scratch = table_map[table]
        condition = str(cell.get("condition") or "raw")
        scale = int(cell.get("scale") or 0)
        ef = int(cell.get("ef_search") or 200)
        ref_key = f"{condition}|{scale}"
        exact_map = all_refs.get(ref_key)
        if not exact_map:
            suffix = titan_scratch if table == "document_chunks_titan" else None
            exact_map = build_exact_refs(
                sess,
                questions,
                qvecs,
                (scale,),
                (condition,),
                port=port,
                scratch_suffix=suffix,
            ).get(ref_key, {})
        frac_hnsw = float(cell.get("frac_hnsw_audit") or cell.get("frac_hnsw") or 0.0)
        rows_for_cell: list[dict] = []
        if frac_hnsw > 0:
            plan_check = verify_cell_hnsw_plans(
                sess,
                questions,
                qvecs,
                scale=scale,
                condition=condition,
                ef_search=ef,
                force_hnsw=False,
            )
            sw = sweep_questions(
                sess,
                questions,
                qvecs,
                scale=scale,
                condition=condition,
                ef_search=ef,
                iterative_scan="relaxed_order",
            )
            sess.reset_planner_defaults()
            rows_for_cell.append(
                {
                    "mode": "as_planned",
                    "frac_hnsw_audit": frac_hnsw,
                    "plan_check": plan_check,
                    **compare_to_exact_with_hits(questions, sw, exact_map),
                    "sweep_elapsed_s": sw["sweep_elapsed_s"],
                }
            )
        if frac_hnsw < 1.0:
            plan_check = verify_cell_hnsw_plans(
                sess,
                questions,
                qvecs,
                scale=scale,
                condition=condition,
                ef_search=ef,
                force_hnsw=True,
            )
            if plan_check.get("all_probes_hnsw"):
                sw = sweep_questions(
                    sess,
                    questions,
                    qvecs,
                    scale=scale,
                    condition=condition,
                    ef_search=ef,
                    iterative_scan="relaxed_order",
                    force_hnsw=True,
                )
                sess.reset_planner_defaults()
                rows_for_cell.append(
                    {
                        "mode": "forced_hnsw",
                        "frac_hnsw_audit": frac_hnsw,
                        "plan_check": plan_check,
                        **compare_to_exact_with_hits(questions, sw, exact_map),
                        "sweep_elapsed_s": sw["sweep_elapsed_s"],
                    }
                )
            else:
                sess.reset_planner_defaults()
                rows_for_cell.append(
                    {
                        "mode": "forced_hnsw",
                        "frac_hnsw_audit": frac_hnsw,
                        "plan_check": plan_check,
                        "plan_error": plan_check.get("plan_error"),
                        "plan_error_detail": plan_check.get("plan_error_detail"),
                        "recall_excluded": True,
                    }
                )
        out.append(
            {
                "table": table,
                "condition": condition,
                "scale": scale,
                "ef_search": ef,
                "frac_hnsw_audit": frac_hnsw,
                "modes": rows_for_cell,
            }
        )
    return out


def write_hnsw_recall_artifacts(port: int, rows: list[dict]) -> tuple[Path, Path]:
    out_json = REV1 / f"hnsw_recall_by_cell_{port}.json"
    obj = {"port": port, "generated_at": utc_now(), "cells": rows}
    write_json_atomic(out_json, obj)
    lines = [
        f"# HNSW recall by plan-audit cell (port {port})",
        "",
        f"Generated: {obj['generated_at']}",
        "",
        "| table | cond | scale | ef | mode | frac_hnsw | recall@10 | frac_identical | Hit@10 approx | Hit@10 exact | Hit@10 loss |",
        "|---|---|---:|---:|---|---:|---:|---:|---:|---:|---:|",
    ]
    for cell in rows:
        for m in cell.get("modes") or []:
            if m.get("recall_excluded"):
                lines.append(
                    f"| {cell['table']} | {cell['condition']} | {cell['scale']} | {cell['ef_search']} | "
                    f"{m['mode']} | {m.get('frac_hnsw_audit')} | — | — | — | — | — | plan_error |"
                )
                continue
            lines.append(
                f"| {cell['table']} | {cell['condition']} | {cell['scale']} | {cell['ef_search']} | "
                f"{m['mode']} | {m.get('frac_hnsw_audit')} | {m.get('mean_list_recall_at_10')} | "
                f"{m.get('frac_lists_identical_to_exact')} | {m.get('mean_hit_at_10_approx')} | "
                f"{m.get('mean_hit_at_10_exact_ref')} | {m.get('hit_at_10_loss')} |"
            )
    md = out_json.with_suffix(".md")
    md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out_json, md


def run_diagnosis(port: int, out_json: Path, scratch_suffix: str | None = None) -> dict[str, Any]:
    questions = load_questions()
    eval_ids = [q["eval_id"] for q in questions]
    qvecs_openai = load_openai_cache(eval_ids)
    qvecs_titan = load_titan_cache(eval_ids)

    conn = pg_connect(port)
    cur = conn.cursor()
    cur.execute("SELECT version()")
    pg_version = cur.fetchone()[0]
    cur.execute("SELECT extversion FROM pg_extension WHERE extname = 'vector'")
    row = cur.fetchone()
    pgvector = row[0] if row else None
    cur.execute(
        "SELECT name, setting FROM pg_settings WHERE name LIKE 'hnsw%' OR name IN "
        "('shared_buffers','work_mem') ORDER BY 1"
    )
    settings = {a: b for a, b in cur.fetchall()}

    openai = Session(cur, "document_chunks", HNSW_INDEX_OPENAI)
    titan = Session(cur, "document_chunks_titan", HNSW_INDEX_TITAN)

    payload: dict[str, Any] = {
        "task": "W2_search_mode_diagnosis",
        "port": port,
        "generated_at": utc_now(),
        "postgres_version": pg_version,
        "pgvector_version": pgvector,
        "settings": settings,
        "experiments": {},
        "acceptance": {},
        "observations": {},
        "open_questions": [],
    }

    # Exact references (shared across experiments)
    ref_scales = sorted(
        set(
            list(TIMING_SCALES)
            + list(E3_SCALES)
            + list(E4_SCALES)
            + [100000]
            + list(HNSW_RECALL_SCALES_OPENAI_RAW)
            + list(META_MIXED_SCALES)
        )
    )
    ref_conditions = ("raw", "meta", "meta_in")
    print("Building exact reference lists …", flush=True)
    exact_refs = build_exact_refs(
        openai, questions, qvecs_openai, tuple(ref_scales), ref_conditions, port=port
    )
    payload["acceptance"]["exact_self_recall"] = verify_exact_refs_independent(
        openai, questions, qvecs_openai, exact_refs
    )
    payload["experiments"]["tie_handling"] = {
        "openai": tie_handling_check(
            openai, questions, qvecs_openai, tuple(ref_scales), ref_conditions
        ),
    }

    # (1) Timing first pass after reference builds and warm — OpenAI raw
    timing_rows: list[dict] = []
    for pass_name in ("first_pass_after_reference_scans", "warm"):
        for ef in TIMING_EFS:
            for scale in TIMING_SCALES:
                print(f"timing {pass_name} raw N={scale} ef={ef}", flush=True)
                sw = sweep_questions(
                    openai,
                    questions,
                    qvecs_openai,
                    scale=scale,
                    condition="raw",
                    ef_search=ef,
                    iterative_scan="relaxed_order",
                )
                cmp = compare_to_exact_with_hits(questions, sw, exact_refs[f"raw|{scale}"])
                audit = load_audit_timing(port, "document_chunks", "raw", scale, ef)
                mean_sweep_ms = sw["sum_query_ms"] / max(sw["n_queries"], 1)
                row = {
                    "pass": pass_name,
                    "table": "document_chunks",
                    "condition": "raw",
                    "scale": scale,
                    "ef_search": ef,
                    **sw,
                    "vs_exact": cmp,
                    "plan_audit_forward": audit,
                }
                if audit and sw["n_queries"]:
                    row["sweep_vs_audit_mean_ms_ratio"] = round(
                        mean_sweep_ms / max(float(audit.get("mean_exec_ms") or 0.0), 1e-9),
                        4,
                    )
                    row["sweep_n_queries"] = sw["n_queries"]
                    row["audit_n_queries_sample"] = audit.get("n_queries_sample")
                timing_rows.append(row)
                openai.reset_planner_defaults()
    payload["experiments"]["timing_openai_raw"] = timing_rows

    first_5k = next(
        r
        for r in timing_rows
        if r["pass"] == "first_pass_after_reference_scans" and r["scale"] == 5000 and r["ef_search"] == 200
    )
    first_50k = next(
        r
        for r in timing_rows
        if r["pass"] == "first_pass_after_reference_scans" and r["scale"] == 50000 and r["ef_search"] == 200
    )
    sum_ratio = first_5k["sum_query_ms"] / max(first_50k["sum_query_ms"], 1e-9)
    mean_ratio = (first_5k["sum_query_ms"] / max(first_5k["n_queries"], 1)) / max(
        first_50k["sum_query_ms"] / max(first_50k["n_queries"], 1), 1e-9
    )
    payload["acceptance"]["latency_5k_vs_50k_ef200_raw"] = {
        "port": port,
        "timing_pass": "first_pass_after_reference_scans",
        "sweep_s_5k": first_5k["sweep_elapsed_s"],
        "sweep_s_50k": first_50k["sweep_elapsed_s"],
        "sum_ms_5k": first_5k["sum_query_ms"],
        "sum_ms_50k": first_50k["sum_query_ms"],
        "mean_ms_ratio_5k_over_50k": round(mean_ratio, 3),
        "sum_ms_ratio_5k_over_50k": round(sum_ratio, 3),
        "audit_mean_ms_ratio_5k_over_50k": round(
            float((first_5k.get("plan_audit_forward") or {}).get("mean_exec_ms") or 0)
            / max(float((first_50k.get("plan_audit_forward") or {}).get("mean_exec_ms") or 1), 1e-9),
            3,
        ),
        "reproduces_3x_band": bool(mean_ratio >= 2.0),
        "note": "Pass runs after exact-reference scans; not a cold-cache measurement.",
    }

    ef400_100k = next(
        r
        for r in timing_rows
        if r["pass"] == "first_pass_after_reference_scans" and r["scale"] == 100000 and r["ef_search"] == 400
    )
    ef800_100k = next(
        r
        for r in timing_rows
        if r["pass"] == "first_pass_after_reference_scans" and r["scale"] == 100000 and r["ef_search"] == 800
    )
    payload["acceptance"]["ef400_800_identical_to_exact_100k_raw"] = {
        "ef400_frac_identical": ef400_100k["vs_exact"]["frac_lists_identical_to_exact"],
        "ef800_frac_identical": ef800_100k["vs_exact"]["frac_lists_identical_to_exact"],
        "ef400_status": "PASS" if ef400_100k["vs_exact"]["frac_lists_identical_to_exact"] == 1.0 else "FAIL",
        "ef800_status": "PASS" if ef800_100k["vs_exact"]["frac_lists_identical_to_exact"] == 1.0 else "FAIL",
    }

    # E2 ef sweep @ 100k raw (OpenAI)
    e2_rows: list[dict] = []
    for ef in E2_EFS:
        print(f"E2 OpenAI 100k ef={ef}", flush=True)
        sw = sweep_questions(
            openai,
            questions,
            qvecs_openai,
            scale=100000,
            condition="raw",
            ef_search=ef,
            iterative_scan="relaxed_order",
        )
        cmp = compare_to_exact_with_hits(questions, sw, exact_refs["raw|100000"])
        plan = openai.explain_one(questions[0], 100000, "raw", qvecs_openai[questions[0]["eval_id"]], analyze=False)
        e2_rows.append(
            {
                "ef_search": ef,
                "sweep_elapsed_s": sw["sweep_elapsed_s"],
                "sum_query_ms": sw["sum_query_ms"],
                "vs_exact": cmp,
                "example_plan_summary": {
                    "ef_search": ef,
                    "hnsw_used": plan["hnsw_used"],
                    "node_types_unique": plan["node_types_unique"],
                    "index_names": plan["index_names"],
                },
            }
        )
        openai.reset_planner_defaults()
    payload["experiments"]["e2_ef_sweep_100k_openai_raw"] = e2_rows

    # E2 hnsw guc variants @ 400/800 (restore defaults after each combo)
    guc_variants: list[dict] = []
    for ef in (400, 800):
        for mst in (20000, 100000, 1000000):
            for smm in (1, 4):
                sw = sweep_questions(
                    openai,
                    questions,
                    qvecs_openai,
                    scale=100000,
                    condition="raw",
                    ef_search=ef,
                    iterative_scan="relaxed_order",
                    max_scan_tuples=mst,
                    scan_mem_multiplier=smm,
                )
                cmp = compare_to_exact_with_hits(questions, sw, exact_refs["raw|100000"])
                guc_variants.append(
                    {
                        "ef_search": ef,
                        "max_scan_tuples": mst,
                        "scan_mem_multiplier": smm,
                        "sweep_elapsed_s": sw["sweep_elapsed_s"],
                        "vs_exact": cmp,
                    }
                )
                openai.reset_planner_defaults()
    payload["experiments"]["e2_guc_variants_100k_openai_raw"] = guc_variants
    openai.reset_planner_defaults()

    # HNSW recall cells — OpenAI raw ef200
    hnsw_recall: list[dict] = []
    for scale in HNSW_RECALL_SCALES_OPENAI_RAW:
        sw = sweep_questions(
            openai,
            questions,
            qvecs_openai,
            scale=scale,
            condition="raw",
            ef_search=200,
            iterative_scan="relaxed_order",
        )
        cmp = compare_to_exact_with_hits(questions, sw, exact_refs[f"raw|{scale}"])
        plan = openai.explain_one(questions[0], scale, "raw", qvecs_openai[questions[0]["eval_id"]])
        openai.reset_planner_defaults()
        hnsw_recall.append(
            {
                "scale": scale,
                "example_hnsw_used": plan["hnsw_used"],
                "vs_exact": cmp,
                "sweep_elapsed_s": sw["sweep_elapsed_s"],
            }
        )
    payload["experiments"]["hnsw_recall_openai_raw_ef200"] = hnsw_recall

    # E3 iterative_scan modes
    e3_rows: list[dict] = []
    for scale in E3_SCALES:
        for condition in ("raw", "meta"):
            for mode in E3_MODES:
                sw = sweep_questions(
                    openai,
                    questions,
                    qvecs_openai,
                    scale=scale,
                    condition=condition,
                    ef_search=200,
                    iterative_scan=mode,
                )
                cmp = compare_to_exact_with_hits(questions, sw, exact_refs[f"{condition}|{scale}"])
                noninc = sum(1 for r in sw["per_question"] if r.get("scores_non_increasing"))
                openai.reset_planner_defaults()
                e3_rows.append(
                    {
                        "scale": scale,
                        "condition": condition,
                        "iterative_scan": mode,
                        "frac_scores_non_increasing": round(noninc / max(sw["n_queries"], 1), 4),
                        "vs_exact": cmp,
                        "sweep_elapsed_s": sw["sweep_elapsed_s"],
                    }
                )
    payload["experiments"]["e3_iterative_scan_openai"] = e3_rows

    # E4 cross-scale meta order swaps
    e4: dict[str, Any] = {}
    for mode in ("relaxed_order", "strict_order"):
        lists_by_scale: dict[int, dict[str, list[str]]] = {}
        for scale in E4_SCALES + (100000,):
            sw = sweep_questions(
                openai,
                questions,
                qvecs_openai,
                scale=scale,
                condition="meta",
                ef_search=200,
                iterative_scan=mode,
            )
            lists_by_scale[scale] = {r["eval_id"]: r["doc_ids"] for r in sw["per_question"]}
        pair_stats: list[dict] = []
        for lo, hi in E4_PAIRS:
            swap_q = 0
            for q in questions:
                eid = q["eval_id"]
                if question_swaps_order(lists_by_scale[lo].get(eid, []), lists_by_scale[hi].get(eid, [])):
                    swap_q += 1
            pair_stats.append(
                {
                    "scale_lo": lo,
                    "scale_hi": hi,
                    "n_questions_with_pair_swap": swap_q,
                    "frac": round(swap_q / len(questions), 4),
                }
            )
        e4[mode] = pair_stats
    payload["experiments"]["e4_cross_scale_meta_swaps"] = e4

    # OpenAI meta mixed plans 40k–100k
    mixed: list[dict] = []
    for scale in META_MIXED_SCALES:
        sw = sweep_questions(
            openai,
            questions,
            qvecs_openai,
            scale=scale,
            condition="meta",
            ef_search=200,
            iterative_scan="relaxed_order",
        )
        by_eid = {r["eval_id"]: r for r in sw["per_question"]}
        hnsw_plans: list[dict] = []
        exact_plans: list[dict] = []
        for q in questions:
            eid = q["eval_id"]
            if eid not in qvecs_openai:
                continue
            plan = openai.explain_one(q, scale, "meta", qvecs_openai[eid], analyze=False)
            row = by_eid.get(eid) or {}
            exact = exact_refs[f"meta|{scale}"].get(eid, [])
            approx = row.get("doc_ids") or []
            rec = {
                "eval_id": eid,
                "hnsw_used": plan["hnsw_used"],
                "list_identical_to_exact": approx == exact,
                "list_recall_at_10": round(list_recall_against_exact(exact, approx), 4),
            }
            if plan["hnsw_used"]:
                hnsw_plans.append(rec)
            else:
                exact_plans.append(rec)
        def mean_recall(rows: list[dict]) -> float | None:
            if not rows:
                return None
            return round(float(np.mean([r["list_recall_at_10"] for r in rows])), 4)
        mixed.append(
            {
                "scale": scale,
                "n_hnsw_plans": len(hnsw_plans),
                "n_exact_plans": len(exact_plans),
                "mean_recall_hnsw_plans": mean_recall(hnsw_plans),
                "mean_recall_exact_plans": mean_recall(exact_plans),
                "frac_hnsw_lists_identical": round(
                    sum(1 for r in hnsw_plans if r["list_identical_to_exact"]) / max(len(hnsw_plans), 1), 4
                ),
                "per_question_sample": (hnsw_plans + exact_plans)[:5],
            }
        )
        openai.reset_planner_defaults()
    payload["experiments"]["openai_meta_mixed_plans"] = mixed

    # Cost explain matrix (200 queries, 100k raw)
    cost_rows = explain_cost_matrix(
        openai,
        questions,
        qvecs_openai,
        100000,
        "raw",
        exact_refs["raw|100000"],
        E2_EFS,
    )
    payload["experiments"]["planner_cost_explain_100k_raw"] = cost_rows
    openai.reset_planner_defaults()

    titan_suffix = scratch_suffix or f"titan_{port}"
    titan_scales: set[int] = {100000}
    titan_conds: set[str] = {"raw"}
    for cell in hnsw_recall_work_cells(port):
        if cell.get("table") == "document_chunks_titan":
            titan_scales.add(int(cell.get("scale") or 0))
            titan_conds.add(str(cell.get("condition") or "raw"))
    titan_refs = build_exact_refs(
        titan,
        questions,
        qvecs_titan,
        tuple(sorted(titan_scales)),
        tuple(sorted(titan_conds)),
        port=port,
        scratch_suffix=titan_suffix,
    )
    payload["acceptance"]["exact_self_recall_titan"] = verify_exact_refs_independent(
        titan, questions, qvecs_titan, titan_refs
    )
    payload["experiments"]["tie_handling"]["titan"] = tie_handling_check(
        titan,
        questions,
        qvecs_titan,
        tuple(sorted(titan_scales)),
        tuple(sorted(titan_conds)),
    )
    titan_exact_100k = titan_refs
    hnsw_cell_rows = run_hnsw_recall_by_cell(
        port,
        questions,
        openai,
        titan,
        qvecs_openai,
        qvecs_titan,
        exact_refs,
        titan_refs,
        scratch_suffix=titan_suffix,
    )
    write_hnsw_recall_artifacts(port, hnsw_cell_rows)
    payload["hnsw_recall_by_cell_file"] = str(REV1 / f"hnsw_recall_by_cell_{port}.json")

    # Titan: E2 subset + E3 relaxed vs strict @ 100k raw
    titan_e2: list[dict] = []
    for ef in (200, 400, 800):
        sw = sweep_questions(
            titan,
            questions,
            qvecs_titan,
            scale=100000,
            condition="raw",
            ef_search=ef,
            iterative_scan="relaxed_order",
        )
        cmp = compare_to_exact_with_hits(questions, sw, titan_exact_100k["raw|100000"])
        plan = titan.explain_one(questions[0], 100000, "raw", qvecs_titan[questions[0]["eval_id"]])
        titan_e2.append(
            {
                "ef_search": ef,
                "vs_exact": cmp,
                "example_hnsw_used": plan["hnsw_used"],
                "sweep_elapsed_s": sw["sweep_elapsed_s"],
                "sum_query_ms": sw["sum_query_ms"],
            }
        )
        titan.reset_planner_defaults()
    payload["experiments"]["titan_e2_100k_raw"] = titan_e2

    titan_e3: list[dict] = []
    for mode in ("relaxed_order", "strict_order"):
        sw = sweep_questions(
            titan,
            questions,
            qvecs_titan,
            scale=100000,
            condition="raw",
            ef_search=200,
            iterative_scan=mode,
        )
        noninc = sum(1 for r in sw["per_question"] if r.get("scores_non_increasing"))
        frac_noninc = round(noninc / max(sw["n_queries"], 1), 4)
        cmp = compare_to_exact_with_hits(questions, sw, titan_exact_100k["raw|100000"])
        titan_e3.append(
            {
                "iterative_scan": mode,
                "frac_scores_non_increasing": frac_noninc,
                "vs_exact": cmp,
                "sweep_elapsed_s": sw["sweep_elapsed_s"],
                "sum_query_ms": sw["sum_query_ms"],
            }
        )
        titan.reset_planner_defaults()
    payload["experiments"]["titan_e3_100k_raw"] = titan_e3

    conn.close()

    titan_e3_monotonicity = {
        r["iterative_scan"]: r["frac_scores_non_increasing"] for r in titan_e3
    }
    payload["observations"] = {
        "port": port,
        "timing_first_pass_mean_ms_ratio_5k_over_50k_ef200": payload["acceptance"]["latency_5k_vs_50k_ef200_raw"][
            "mean_ms_ratio_5k_over_50k"
        ],
        "ef400_800_frac_identical_exact_100k_raw": {
            "ef400": ef400_100k["vs_exact"]["frac_lists_identical_to_exact"],
            "ef800": ef800_100k["vs_exact"]["frac_lists_identical_to_exact"],
        },
        "e3_openai_relaxed_frac_non_increasing_min": min(
            (
                r["frac_scores_non_increasing"]
                for r in e3_rows
                if r["iterative_scan"] == "relaxed_order"
            ),
            default=None,
        ),
        "e4_relaxed_total_pair_swaps": sum(p["n_questions_with_pair_swap"] for p in e4.get("relaxed_order") or []),
        "e4_strict_total_pair_swaps": sum(p["n_questions_with_pair_swap"] for p in e4.get("strict_order") or []),
        "titan_e3_frac_scores_non_increasing": titan_e3_monotonicity,
        "tie_handling_openai": (payload["experiments"].get("tie_handling") or {}).get("openai"),
        "tie_handling_titan": (payload["experiments"].get("tie_handling") or {}).get("titan"),
    }

    def drop_per_question(obj: Any) -> None:
        if isinstance(obj, dict):
            obj.pop("per_question", None)
            for v in obj.values():
                drop_per_question(v)
        elif isinstance(obj, list):
            for item in obj:
                drop_per_question(item)

    drop_per_question(payload["experiments"])

    md_path = out_json.with_suffix(".md")
    write_json_atomic(out_json, payload)
    md_path.write_text(render_md(payload), encoding="utf-8")
    return payload


def audit_hnsw_usage_rows(port: int) -> list[list[str]]:
    rows: list[list[str]] = []
    for c in load_audit_cells(port):
        if c.get("pass") != "forward":
            continue
        ef = int(c.get("ef_search") or -1)
        if ef not in (200, 400, 800):
            continue
        table = str(c.get("table") or "")
        embedder = "openai" if table == "document_chunks" else "titan" if table == "document_chunks_titan" else table
        cond = str(c.get("condition") or "raw")
        if cond == "meta":
            cond = "meta_first"
        rows.append([embedder, cond, str(c.get("scale")), str(ef), str(c.get("frac_hnsw"))])
    rows.sort(key=lambda r: (r[0], r[1], int(r[2]), int(r[3])))
    return rows


def run_only_recall_by_cell(
    port: int,
    *,
    scales: tuple[int, ...] | None = None,
    scratch_suffix: str | None = None,
) -> tuple[Path, Path]:
    questions = load_questions()
    eval_ids = [q["eval_id"] for q in questions]
    qvecs_openai = load_openai_cache(eval_ids)
    qvecs_titan = load_titan_cache(eval_ids)

    conn = pg_connect(port)
    cur = conn.cursor()
    openai = Session(cur, "document_chunks", HNSW_INDEX_OPENAI)
    titan = Session(cur, "document_chunks_titan", HNSW_INDEX_TITAN)

    openai_scales: set[int] = set()
    openai_conds: set[str] = set()
    titan_scales: set[int] = set()
    titan_conds: set[str] = set()
    for cell in hnsw_recall_work_cells(port, scales=scales):
        scale = int(cell.get("scale") or 0)
        cond = str(cell.get("condition") or "raw")
        if cell.get("table") == "document_chunks_titan":
            titan_scales.add(scale)
            titan_conds.add(cond)
        else:
            openai_scales.add(scale)
            openai_conds.add(cond)

    titan_suffix = scratch_suffix or f"titan_{port}"
    print("Building exact reference lists (recall-by-cell only) …", flush=True)
    openai_refs = build_exact_refs(
        openai,
        questions,
        qvecs_openai,
        tuple(sorted(openai_scales)),
        tuple(sorted(openai_conds)),
        port=port,
    )
    titan_refs = build_exact_refs(
        titan,
        questions,
        qvecs_titan,
        tuple(sorted(titan_scales)),
        tuple(sorted(titan_conds)),
        port=port,
        scratch_suffix=titan_suffix,
    )

    rows = run_hnsw_recall_by_cell(
        port,
        questions,
        openai,
        titan,
        qvecs_openai,
        qvecs_titan,
        openai_refs,
        titan_refs,
        scales=scales,
        scratch_suffix=titan_suffix,
    )
    conn.close()
    return write_hnsw_recall_artifacts(port, rows)


def render_md(payload: dict[str, Any]) -> str:
    lines: list[str] = []
    port = payload["port"]
    lines.append(f"# Search mode diagnosis (port {port})")
    lines.append("")
    lines.append(f"Generated: {payload['generated_at']}")
    ex = payload.get("experiments") or {}

    def section_table(title: str, headers: list[str], rows: list[list[str]]) -> None:
        lines.append(f"## {title}")
        lines.append("")
        lines.append("| " + " | ".join(headers) + " |")
        lines.append("|" + "|".join(["---"] * len(headers)) + "|")
        for row in rows:
            lines.append("| " + " | ".join(str(c) for c in row) + " |")
        lines.append("")

    timing_rows = []
    for r in ex.get("timing_openai_raw") or []:
        audit = r.get("plan_audit_forward") or {}
        timing_rows.append(
            [
                r["pass"],
                r["scale"],
                r["ef_search"],
                r.get("sweep_n_queries", r.get("n_queries", "n/a")),
                (r.get("plan_audit_forward") or {}).get("n_queries_sample", "n/a"),
                r["sweep_elapsed_s"],
                r.get("sweep_vs_audit_mean_ms_ratio", "n/a"),
                r["vs_exact"]["frac_lists_identical_to_exact"],
                r["vs_exact"].get("mean_hit_at_10_approx", "n/a"),
            ]
        )
    section_table(
        "Timing (OpenAI raw)",
        [
            "pass",
            "scale",
            "ef",
            "sweep_n_queries",
            "audit_n_queries_sample",
            "sweep_s",
            "mean_ms_ratio_vs_audit",
            "frac_identical",
            "Hit@10 approx",
        ],
        timing_rows,
    )

    e2_rows = [
        [
            r["ef_search"],
            r["sweep_elapsed_s"],
            r["vs_exact"]["mean_list_recall_at_10"],
            r["vs_exact"]["frac_lists_identical_to_exact"],
            r["vs_exact"].get("mean_hit_at_10_approx"),
            r["vs_exact"].get("mean_hit_at_10_exact_ref"),
            (r.get("example_plan_summary") or {}).get("hnsw_used"),
        ]
        for r in ex.get("e2_ef_sweep_100k_openai_raw") or []
    ]
    section_table(
        "E2 ef sweep @ 100k raw (OpenAI)",
        ["ef", "sweep_s", "recall@10", "frac_identical", "Hit@10 approx", "Hit@10 exact", "plan_hnsw"],
        e2_rows,
    )

    hnsw_r2 = [
        [
            r["scale"],
            (r.get("example_hnsw_used")),
            r["vs_exact"]["mean_list_recall_at_10"],
            r["vs_exact"]["frac_lists_identical_to_exact"],
            r["sweep_elapsed_s"],
        ]
        for r in ex.get("hnsw_recall_openai_raw_ef200") or []
    ]
    section_table(
        "OpenAI raw HNSW recall @ ef 200 (by scale)",
        ["scale", "plan_hnsw", "recall@10", "frac_identical", "sweep_s"],
        hnsw_r2,
    )

    guc_rows = [
        [
            r["ef_search"],
            r["max_scan_tuples"],
            r["scan_mem_multiplier"],
            r["sweep_elapsed_s"],
            r["vs_exact"]["frac_lists_identical_to_exact"],
        ]
        for r in ex.get("e2_guc_variants_100k_openai_raw") or []
    ]
    section_table(
        "E2 GUC variants @ 100k raw",
        ["ef", "max_scan_tuples", "scan_mem_mult", "sweep_s", "frac_identical"],
        guc_rows,
    )

    e3_rows = [
        [
            r["scale"],
            r["condition"],
            r["iterative_scan"],
            r["frac_scores_non_increasing"],
            r["vs_exact"]["mean_list_recall_at_10"],
            r["vs_exact"]["frac_lists_identical_to_exact"],
            r["sweep_elapsed_s"],
        ]
        for r in ex.get("e3_iterative_scan_openai") or []
    ]
    section_table(
        "E3 iterative_scan (OpenAI)",
        ["scale", "cond", "mode", "frac_non_increasing", "recall@10", "frac_identical", "sweep_s"],
        e3_rows,
    )

    for mode in ("relaxed_order", "strict_order"):
        pair_rows = [
            [p["scale_lo"], p["scale_hi"], p["n_questions_with_pair_swap"], p["frac"]]
            for p in (ex.get("e4_cross_scale_meta_swaps") or {}).get(mode) or []
        ]
        section_table(f"E4 cross-scale meta swaps ({mode})", ["scale_lo", "scale_hi", "n_swap_q", "frac"], pair_rows)

    cost_rows = [
        [
            r["ef_search"],
            r["median_default_total_cost"],
            r["median_forced_hnsw_total_cost"],
            r["forced_hnsw_vs_exact"].get("mean_list_recall_at_10"),
            r["forced_hnsw_vs_exact"].get("mean_hit_at_10_approx"),
            ",".join(r.get("forced_hnsw_table_scan_node_types") or []),
        ]
        for r in ex.get("planner_cost_explain_100k_raw") or []
    ]
    section_table(
        "Planner cost matrix @ 100k raw (median over 200 queries)",
        ["ef", "cost_default", "cost_forced_hnsw", "forced recall@10", "forced Hit@10", "scan_node"],
        cost_rows,
    )

    titan_e2 = [
        [r["ef_search"], r["sweep_elapsed_s"], r["vs_exact"]["frac_lists_identical_to_exact"], r["example_hnsw_used"]]
        for r in ex.get("titan_e2_100k_raw") or []
    ]
    section_table("Titan E2 @ 100k raw", ["ef", "sweep_s", "frac_identical", "plan_hnsw"], titan_e2)

    titan_e3 = [
        [
            r["iterative_scan"],
            r.get("frac_scores_non_increasing"),
            r["vs_exact"]["frac_lists_identical_to_exact"],
            r["sweep_elapsed_s"],
        ]
        for r in ex.get("titan_e3_100k_raw") or []
    ]
    section_table("Titan E3 @ 100k raw", ["mode", "frac_non_increasing", "frac_identical", "sweep_s"], titan_e3)

    mixed_rows = []
    for m in ex.get("openai_meta_mixed_plans") or []:
        mixed_rows.append(
            [
                m["scale"],
                m["n_hnsw_plans"],
                m["n_exact_plans"],
                m.get("mean_recall_hnsw_plans"),
                m.get("mean_recall_exact_plans"),
                m.get("frac_hnsw_lists_identical"),
            ]
        )
    section_table(
        "OpenAI meta mixed plans (ef 200)",
        ["scale", "n_hnsw", "n_exact", "mean_recall_hnsw", "mean_recall_exact", "frac_hnsw_identical"],
        mixed_rows,
    )

    tie_block = ex.get("tie_handling") or {}
    lines.append("## Tie handling (exact top-11)")
    lines.append("")
    for label, tie in (("openai", tie_block.get("openai") or tie_block), ("titan", tie_block.get("titan") or {})):
        if not tie:
            continue
        lines.append(f"### {label}")
        lines.append("")
        lines.append(f"- lists checked: {tie.get('n_lists_checked')}")
        lines.append(f"- rank 10/11 score ties (≤1e-12): {tie.get('n_rank10_11_score_ties')}")
        lines.append(f"- duplicate scores in top 10: {tie.get('n_lists_duplicate_scores_in_top10')}")
        if label == "openai":
            lines.append(f"- note: {tie.get('hit_at_10_impact_note')}")
        lines.append("")

    lines.append("## Observations")
    lines.append("")
    lines.append("HNSW plan-audit usage (fraction of sampled queries with HNSW index in plan):")
    lines.append("")
    section_table(
        "Plan audit forward (HNSW fraction)",
        ["embedder", "condition", "scale", "ef_search", "frac_hnsw"],
        audit_hnsw_usage_rows(port),
    )

    lines.append("## Acceptance")
    lines.append("")
    for name, rec in (payload.get("acceptance") or {}).items():
        if isinstance(rec, dict) and "status" in rec:
            lines.append(f"- `{name}`: **{rec['status']}** — {json.dumps(rec, ensure_ascii=True)}")
        else:
            lines.append(f"- `{name}`: {rec}")
    lines.append("")
    if payload.get("hnsw_recall_by_cell_file"):
        lines.append(f"HNSW recall table: `{payload['hnsw_recall_by_cell_file']}`")
        lines.append("")
    oq = payload.get("open_questions") or []
    if oq:
        lines.append("## Open questions")
        lines.append("")
        for q in oq:
            lines.append(f"- {q}")
    return "\n".join(lines) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=None)
    ap.add_argument("--out", type=Path, default=None)
    ap.add_argument(
        "--scratch-suffix",
        type=str,
        default=None,
        help="Suffix for Titan exact-reference scratch file under data/",
    )
    ap.add_argument(
        "--loops-check-only",
        action="store_true",
        help="Only recompute plan_audit_loops_check.json from existing plan audits",
    )
    ap.add_argument(
        "--only-recall-by-cell",
        action="store_true",
        help="Only build exact refs and run hnsw_recall_by_cell (does not touch search_mode_diagnosis output)",
    )
    ap.add_argument(
        "--scales",
        type=str,
        default=None,
        help="Comma-separated corpus sizes for --only-recall-by-cell (default: all audit scales)",
    )
    args = ap.parse_args()
    if args.loops_check_only:
        path = write_plan_audit_loops_check()
        print(f"Wrote {path}", flush=True)
        return
    if args.port is None:
        ap.error("--port is required unless --loops-check-only")
    if args.only_recall_by_cell:
        scale_tuple: tuple[int, ...] | None = None
        if args.scales:
            scale_tuple = tuple(int(x.strip()) for x in args.scales.split(",") if x.strip())
        t0 = time.time()
        out_json, out_md = run_only_recall_by_cell(
            args.port,
            scales=scale_tuple,
            scratch_suffix=args.scratch_suffix,
        )
        print(f"Wrote {out_json} and {out_md} in {time.time() - t0:.1f}s", flush=True)
        return
    out = args.out or (REV1 / f"search_mode_diagnosis_{args.port}.json")
    write_plan_audit_loops_check()
    print(f"W2 diagnosis port={args.port} -> {out}", flush=True)
    t0 = time.time()
    payload = run_diagnosis(args.port, out, scratch_suffix=args.scratch_suffix)
    print(f"Done in {time.time() - t0:.1f}s", flush=True)
    acc = payload.get("acceptance") or {}
    for k, v in acc.items():
        print(f"acceptance {k}: {v}", flush=True)


if __name__ == "__main__":
    main()
