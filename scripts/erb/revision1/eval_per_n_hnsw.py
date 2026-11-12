#!/usr/bin/env python3
"""Evaluate per-N HNSW indexes against exact top-10 lists (revision 1, task W9).

Queries rev1.n_<embedder>_<N> with no scale predicate. Resumable: finished cells
are cached under data/ and skipped on rerun. Full grid is intended for nohup;
use --subset / --repeats for smoke tests.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import statistics
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import psycopg2

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))
from harness_lib import percentile_linear  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / "data"
PUB = ROOT / "artifacts" / "published"
REV1 = PUB / "revision1"
MANIFEST_PATH = DATA / "erb_scale_manifest.json"
OPENAI_CACHE = DATA / "erb_query_embed_cache.json"
TITAN_CACHE = DATA / "erb_titan_query_embed_cache.json"
BANK_PATH = PUB / "primary_questions_200.json"
BUILD_JSON = REV1 / "per_n_index_build_openai.json"  # legacy name kept for sha field; see BUILD_JSON_FILES
BUILD_JSON_FILES = {"openai": REV1 / "per_n_index_build_openai.json", "titan": REV1 / "per_n_index_build_titan.json"}
CACHE_DIR_DEFAULT = DATA / "rev1_per_n_hnsw_cache"

DEFAULT_SCALES = (5000, 10000, 15000, 20000, 25000, 40000, 50000, 75000, 100000)
DEFAULT_CONDITIONS = ("raw", "meta_first", "meta_in")
DEFAULT_EF = (40, 100, 200, 400, 800)
DEFAULT_MODES = ("relaxed_order", "strict_order")
TOP_K = 10
METRICS = ("hit_at_1", "hit_at_5", "hit_at_10", "mrr", "document_recall")
QUERY_VECTOR_KEY_RULE = (
    "eval_id only; bare question ids are never used because they collide across question types"
)
DEFAULT_MAX_SCAN_TUPLES = 20000
EXTRA_MST = 100000
EXTRA_MST_N = 100000
EXTRA_MST_EF = 200
EXTRA_MST_CONDS = ("raw", "meta_first")

EMBEDDERS = {
    "openai": {
        "cache_path": OPENAI_CACHE,
        "cache_style": "flat",
        "exact_path": REV1 / "exact_ladder_openai_primary200.json",
        "dim": 1536,
    },
    "titan": {
        "cache_path": TITAN_CACHE,
        "cache_style": "titan_vectors",
        "exact_path": REV1 / "exact_ladder_titan_primary200.json",
        "dim": 1024,
    },
}


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def vector_literal(vec: list[float]) -> str:
    return "[" + ",".join(str(v) for v in vec) + "]"


def table_name(embedder: str, n: int) -> str:
    return f"n_{embedder}_{n}"


def qualified_table(embedder: str, n: int) -> str:
    return f"rev1.{table_name(embedder, n)}"


def hnsw_index_name(embedder: str, n: int) -> str:
    return f"{table_name(embedder, n)}_hnsw"


def cell_id(
    embedder: str,
    n: int,
    condition: str,
    ef: int,
    mode: str,
    max_scan_tuples: int,
    n_questions: int,
    seqscan_off: bool = False,
) -> str:
    flag = "_seqscan_off" if seqscan_off else ""
    return (
        f"{embedder}_{n}_{condition}_ef{ef}_{mode}_mst{max_scan_tuples}_n{n_questions}{flag}"
    )


def loadavg() -> dict[str, Any]:
    out: dict[str, Any] = {"captured_at": utc_now()}
    try:
        out["os_getloadavg"] = list(os.getloadavg())
    except OSError as exc:
        out["os_getloadavg_error"] = str(exc)
    try:
        proc = subprocess.run(["uptime"], check=False, capture_output=True, text=True)
        out["uptime_stdout"] = (proc.stdout or "").strip()
        out["uptime_stderr"] = (proc.stderr or "").strip()
        out["uptime_returncode"] = int(proc.returncode)
    except OSError as exc:
        out["uptime_error"] = str(exc)
    return out


def pg_connect():
    missing = [k for k in ("PGUSER", "PGPASSWORD", "PGDATABASE") if not os.environ.get(k)]
    if missing:
        raise SystemExit(f"missing environment variables: {', '.join(missing)}")
    conn = psycopg2.connect(
        host=os.environ.get("PGHOST", "localhost"),
        port=int(os.environ.get("PGPORT", "5432")),
        user=os.environ["PGUSER"],
        password=os.environ["PGPASSWORD"],
        dbname=os.environ["PGDATABASE"],
        connect_timeout=30,
    )
    conn.autocommit = True
    return conn


def load_questions(subset: int | None) -> list[dict]:
    bank = json.loads(BANK_PATH.read_text(encoding="utf-8"))
    eval_ids = list(bank["question_ids"])
    if subset is not None:
        eval_ids = eval_ids[: int(subset)]
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    by_eval = {q["eval_id"]: q for q in manifest.get("questions") or []}
    missing = [e for e in eval_ids if e not in by_eval]
    if missing:
        raise SystemExit(f"manifest missing {len(missing)} eval_ids (e.g. {missing[:3]})")
    out = []
    for eid in eval_ids:
        q = dict(by_eval[eid])
        q["eval_id"] = eid
        q["question_id"] = eid
        out.append(q)
    return out


def load_query_cache(embedder: str, eval_ids: list[str]) -> dict[str, list[float]]:
    cfg = EMBEDDERS[embedder]
    path = cfg["cache_path"]
    raw = json.loads(path.read_text(encoding="utf-8"))
    cache: dict[str, list[float]] = {}
    if cfg["cache_style"] == "titan_vectors":
        vecs = raw.get("vectors") or {}
        for eid in eval_ids:
            v = vecs.get(eid)
            if isinstance(v, list):
                cache[eid] = v
    else:
        for eid in eval_ids:
            v = raw.get(eid)
            if isinstance(v, list):
                cache[eid] = v
            elif isinstance(v, dict) and "embedding" in v:
                cache[eid] = list(v["embedding"])
    missing = [eid for eid in eval_ids if eid not in cache]
    if missing:
        raise SystemExit(
            f"{path.name} missing {len(missing)} embeddings keyed by eval_id "
            f"(e.g. {missing[:3]})"
        )
    return cache


def condition_filter_sql(condition: str, question: dict) -> tuple[str, tuple]:
    if condition == "raw":
        return "", ()
    if condition == "meta_first":
        st = (question.get("source_types") or [None])[0]
        if not st:
            return "WHERE FALSE", ()
        return "WHERE source_type = %s", (str(st),)
    if condition == "meta_in":
        sts = [str(s) for s in (question.get("source_types") or []) if s]
        if not sts:
            return "WHERE FALSE", ()
        return "WHERE source_type = ANY(%s)", (sts,)
    raise ValueError(f"unknown condition: {condition}")


def build_sql(qtable: str, where_sql: str) -> str:
    where = f" {where_sql}" if where_sql else ""
    return (
        f"SELECT doc_id, 1 - (embedding <=> %s::vector) "
        f"FROM {qtable}{where} "
        f"ORDER BY embedding <=> %s::vector LIMIT {TOP_K}"
    )


def per_question_metrics(expected: set[str], retrieved: list[str], scores: list[float]) -> dict:
    rank: int | None = None
    for i, doc_id in enumerate(retrieved[:TOP_K], start=1):
        if doc_id in expected:
            rank = i
            break
    hit_ids = expected & set(retrieved[:TOP_K])
    return {
        "rank": rank,
        "hit_at_1": bool(rank == 1) if rank else False,
        "hit_at_5": bool(rank is not None and rank <= 5),
        "hit_at_10": bool(rank is not None and rank <= 10),
        "mrr": (1.0 / rank) if rank else 0.0,
        "document_recall": (len(hit_ids) / len(expected)) if expected else 0.0,
        "retrieved_doc_ids": retrieved[:TOP_K],
        "scores": scores[:TOP_K],
        "n_retrieved": len(retrieved),
        "shortfall": len(retrieved) < TOP_K,
    }


def aggregate_metrics(per_question: list[dict]) -> dict[str, float]:
    n = len(per_question)
    if n == 0:
        return {m: 0.0 for m in METRICS}
    return {m: round(sum(float(p[m]) for p in per_question) / n, 4) for m in METRICS}


def list_recall_at_10(hnsw_ids: list[str], exact_ids: list[str]) -> float:
    return len(set(hnsw_ids[:TOP_K]) & set(exact_ids[:TOP_K])) / float(TOP_K)


def walk_plan(node: dict, acc: dict) -> None:
    ntype = str(node.get("Node Type") or "")
    acc["node_types"].append(ntype)
    idx = node.get("Index Name")
    if idx:
        acc["index_names"].append(str(idx))
    for child in node.get("Plans") or []:
        if isinstance(child, dict):
            walk_plan(child, acc)


def sanitize_plan(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {str(k): sanitize_plan(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [sanitize_plan(v) for v in obj]
    if isinstance(obj, str):
        if len(obj) > 80 and ("<=>" in obj or obj.strip().startswith("[")):
            return "[VECTOR_ELIDED]"
        if len(obj) > 400:
            return obj[:160] + "…[truncated]…" + obj[-40:]
        return obj
    if isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
        return obj
    return obj


def summarize_plan(explain_root: dict, expected_hnsw: str) -> dict[str, Any]:
    plan = explain_root.get("Plan") or {}
    acc: dict[str, Any] = {"node_types": [], "index_names": []}
    walk_plan(plan, acc)
    node_types = acc["node_types"]
    index_names = list(dict.fromkeys(acc["index_names"]))
    uses_named = expected_hnsw in index_names
    hnsw_any = uses_named or any("hnsw" in n.lower() for n in index_names)
    seq = "Seq Scan" in node_types
    if uses_named:
        plan_kind = "hnsw_index_scan"
    elif hnsw_any:
        plan_kind = "hnsw_other_index"
    elif seq:
        plan_kind = "seq_scan"
    else:
        plan_kind = "other"
    return {
        "plan_kind": plan_kind,
        "node_types": list(dict.fromkeys(node_types)),
        "index_names": index_names,
        "expected_hnsw_index": expected_hnsw,
        "used_expected_hnsw_index": uses_named,
        "hnsw_index_used": hnsw_any,
        "seq_scan": seq,
        "has_sort": "Sort" in node_types,
        "planning_ms": float(explain_root.get("Planning Time") or 0.0),
        "execution_ms": float(explain_root.get("Execution Time") or 0.0),
        "plan": sanitize_plan(explain_root),
    }


def load_exact_refs(
    embedder: str, questions: list[dict]
) -> tuple[dict[tuple[str, int, str], list[str]], dict[tuple[str, int], dict[str, float]]]:
    path = EMBEDDERS[embedder]["exact_path"]
    blob = json.loads(path.read_text(encoding="utf-8"))
    lists: dict[tuple[str, int, str], list[str]] = {}
    metrics: dict[tuple[str, int], dict[str, float]] = {}
    wanted = {q["eval_id"] for q in questions}
    for run in blob.get("runs") or []:
        cond = str(run["condition"])
        scale = int(run.get("scale", run.get("corpus_scale_size")))
        if "metrics" in run:
            metrics[(cond, scale)] = dict(run["metrics"])
        for pq in run.get("per_question") or []:
            qid = str(pq.get("question_id") or pq.get("eval_id") or "")
            if qid not in wanted:
                continue
            lists[(cond, scale, qid)] = [str(d) for d in (pq.get("retrieved_doc_ids") or [])]
    return lists, metrics


def load_build_meta() -> dict[tuple[str, int], dict[str, Any]]:
    out: dict[tuple[str, int], dict[str, Any]] = {}
    blobs = [json.loads(pth.read_text(encoding="utf-8")) for pth in BUILD_JSON_FILES.values() if pth.is_file()]
    for blob in blobs:
        _load_build_blob(blob, out)
    return out


def _load_build_blob(blob: dict[str, Any], out: dict[tuple[str, int], dict[str, Any]]) -> None:
    for row in blob.get("build_log") or []:
        emb = str(row.get("embedder") or blob.get("embedder") or "")
        n = int(row.get("scale_n") or 0)
        if not emb or not n:
            continue
        out[(emb, n)] = {
            "hnsw_build_seconds": row.get("hnsw_build_seconds"),
            "table_bytes": row.get("table_bytes"),
            "hnsw_index_bytes": row.get("hnsw_index_bytes"),
            "btree_index_bytes": row.get("btree_index_bytes"),
            "total_bytes": row.get("total_bytes"),
            "row_count": row.get("row_count"),
            "source": "per_n_index_build.json:build_log",
        }
    for row in blob.get("tables_built_this_run") or []:
        emb = str(row.get("embedder") or blob.get("embedder") or "")
        n = int(row.get("scale_n") or 0)
        if not emb or not n:
            continue
        sizes = row.get("sizes_bytes") or {}
        rec = out.get((emb, n), {})
        rec.update(
            {
                "hnsw_build_seconds": row.get("hnsw_build_seconds", rec.get("hnsw_build_seconds")),
                "table_bytes": sizes.get("table_bytes", rec.get("table_bytes")),
                "hnsw_index_bytes": sizes.get("hnsw_index_bytes", rec.get("hnsw_index_bytes")),
                "btree_index_bytes": sizes.get("btree_index_bytes", rec.get("btree_index_bytes")),
                "total_bytes": sizes.get("total_bytes", rec.get("total_bytes")),
                "row_count": row.get("row_count", rec.get("row_count")),
                "source": rec.get("source") or "per_n_index_build.json:tables_built_this_run",
            }
        )
        out[(emb, n)] = rec


def fetch_build_log_db(cur, embedder: str) -> dict[int, dict[str, Any]]:
    try:
        cur.execute(
            """
            SELECT scale_n, hnsw_build_seconds, table_bytes, hnsw_index_bytes,
                   btree_index_bytes, total_bytes, row_count
            FROM rev1.build_log
            WHERE embedder = %s AND status = 'complete'
            """,
            (embedder,),
        )
    except Exception:
        return {}
    out: dict[int, dict[str, Any]] = {}
    for row in cur.fetchall():
        n = int(row[0])
        out[n] = {
            "hnsw_build_seconds": None if row[1] is None else float(row[1]),
            "table_bytes": None if row[2] is None else int(row[2]),
            "hnsw_index_bytes": None if row[3] is None else int(row[3]),
            "btree_index_bytes": None if row[4] is None else int(row[4]),
            "total_bytes": None if row[5] is None else int(row[5]),
            "row_count": None if row[6] is None else int(row[6]),
            "source": "rev1.build_log",
        }
    return out


def relation_sizes(cur, embedder: str, n: int) -> dict[str, int]:
    tname = table_name(embedder, n)
    hname = hnsw_index_name(embedder, n)
    cur.execute("SELECT pg_relation_size(%s::regclass)", (f"rev1.{tname}",))
    table_bytes = int(cur.fetchone()[0])
    cur.execute("SELECT pg_relation_size(%s::regclass)", (f"rev1.{hname}",))
    hnsw_bytes = int(cur.fetchone()[0])
    cur.execute("SELECT pg_total_relation_size(%s::regclass)", (f"rev1.{tname}",))
    total_bytes = int(cur.fetchone()[0])
    return {
        "table_bytes": table_bytes,
        "hnsw_index_bytes": hnsw_bytes,
        "total_bytes": total_bytes,
    }


def show_guc(cur, name: str) -> str:
    cur.execute(f"SHOW {name}")
    return str(cur.fetchone()[0])


def set_search_gucs(
    cur,
    *,
    ef_search: int,
    iterative_scan: str,
    max_scan_tuples: int | None,
    seqscan_off: bool,
) -> dict[str, Any]:
    cur.execute("SET enable_indexscan = on")
    cur.execute("SET enable_indexonlyscan = on")
    cur.execute("SET enable_bitmapscan = on")
    cur.execute("SET enable_sort = on")
    if seqscan_off:
        cur.execute("SET enable_seqscan = off")
    else:
        cur.execute("SET enable_seqscan = on")
    mst = DEFAULT_MAX_SCAN_TUPLES if max_scan_tuples is None else int(max_scan_tuples)
    cur.execute(f"SET hnsw.ef_search = {int(ef_search)}")
    cur.execute(f"SET hnsw.iterative_scan = {iterative_scan}")
    cur.execute(f"SET hnsw.max_scan_tuples = {int(mst)}")
    return {
        "ef_search": int(ef_search),
        "iterative_scan": iterative_scan,
        "max_scan_tuples_set": int(mst),
        "max_scan_tuples_show": show_guc(cur, "hnsw.max_scan_tuples"),
        "enable_seqscan": "off" if seqscan_off else "on",
        "hnsw.ef_search": show_guc(cur, "hnsw.ef_search"),
        "hnsw.iterative_scan": show_guc(cur, "hnsw.iterative_scan"),
    }


def run_one_query(
    cur, qtable: str, question: dict, condition: str, qvec: list[float]
) -> tuple[list[str], list[float], float]:
    where_sql, extra = condition_filter_sql(condition, question)
    lit = vector_literal(qvec)
    sql = build_sql(qtable, where_sql)
    params = (lit, *extra, lit)
    t0 = time.perf_counter()
    cur.execute(sql, params)
    rows = cur.fetchall()
    elapsed_ms = (time.perf_counter() - t0) * 1000.0
    ids = [str(r[0]) for r in rows if r[0]]
    scores = [float(r[1]) for r in rows]
    return ids, scores, elapsed_ms


def explain_first(
    cur,
    qtable: str,
    question: dict,
    condition: str,
    qvec: list[float],
    expected_hnsw: str,
) -> dict[str, Any]:
    where_sql, extra = condition_filter_sql(condition, question)
    lit = vector_literal(qvec)
    sql = build_sql(qtable, where_sql)
    params = (lit, *extra, lit)
    cur.execute("EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON)\n" + sql, params)
    raw = cur.fetchone()[0]
    root = raw[0] if isinstance(raw, list) else json.loads(raw)[0]
    return summarize_plan(root, expected_hnsw)


def exact_hit10_on_subset(
    questions: list[dict],
    exact_lists: dict[tuple[str, int, str], list[str]],
    condition: str,
    n: int,
) -> float:
    hits = 0
    for q in questions:
        expected = {str(x) for x in (q.get("expected_doc_ids") or []) if x}
        retrieved = exact_lists.get((condition, n, q["eval_id"])) or []
        rank = None
        for i, doc_id in enumerate(retrieved[:TOP_K], start=1):
            if doc_id in expected:
                rank = i
                break
        if rank is not None and rank <= 10:
            hits += 1
    return round(hits / len(questions), 4) if questions else 0.0


def score_sweep(
    questions: list[dict],
    lists: dict[str, list[str]],
    scores: dict[str, list[float]],
    exact_lists: dict[tuple[str, int, str], list[str]],
    condition: str,
    n: int,
) -> tuple[list[dict], dict[str, float], float, int]:
    per_q: list[dict] = []
    recalls: list[float] = []
    n_short = 0
    for q in questions:
        eid = q["eval_id"]
        expected = {str(x) for x in (q.get("expected_doc_ids") or []) if x}
        retrieved = lists.get(eid) or []
        sc = scores.get(eid) or []
        m = per_question_metrics(expected, retrieved, sc)
        exact_ids = exact_lists.get((condition, n, eid)) or []
        rec10 = list_recall_at_10(retrieved, exact_ids)
        m["question_id"] = eid
        m["eval_id"] = eid
        m["recall_at_10_vs_exact"] = rec10
        per_q.append(m)
        recalls.append(rec10)
        if m["shortfall"]:
            n_short += 1
    agg = aggregate_metrics(per_q)
    mean_rec = round(sum(recalls) / len(recalls), 4) if recalls else 0.0
    return per_q, agg, mean_rec, n_short


def metric_signature(per_q: list[dict]) -> list[tuple]:
    out = []
    for p in per_q:
        out.append(
            (
                p["eval_id"],
                tuple(p.get("retrieved_doc_ids") or []),
                bool(p.get("hit_at_1")),
                bool(p.get("hit_at_5")),
                bool(p.get("hit_at_10")),
                round(float(p.get("mrr") or 0.0), 12),
                round(float(p.get("document_recall") or 0.0), 12),
            )
        )
    return out


def run_cell(
    cur,
    *,
    embedder: str,
    n: int,
    condition: str,
    ef: int,
    mode: str,
    max_scan_tuples: int | None,
    questions: list[dict],
    qvecs: dict[str, list[float]],
    exact_lists: dict[tuple[str, int, str], list[str]],
    exact_metrics: dict[tuple[str, int], dict[str, float]],
    repeats: int,
    seqscan_off: bool,
) -> dict[str, Any]:
    qtable = qualified_table(embedder, n)
    expected_hnsw = hnsw_index_name(embedder, n)
    guc = set_search_gucs(
        cur,
        ef_search=ef,
        iterative_scan=mode,
        max_scan_tuples=max_scan_tuples,
        seqscan_off=seqscan_off,
    )
    first = questions[0]
    plan = explain_first(cur, qtable, first, condition, qvecs[first["eval_id"]], expected_hnsw)

    for q in questions:
        run_one_query(cur, qtable, q, condition, qvecs[q["eval_id"]])

    sweep_seconds: list[float] = []
    per_query_ms: dict[str, list[float]] = {q["eval_id"]: [] for q in questions}
    signatures: list[list[tuple]] = []
    last_per_q: list[dict] = []
    last_agg: dict[str, float] = {}
    last_rec = 0.0
    last_short = 0
    last_lists: dict[str, list[str]] = {}

    for _rep in range(repeats):
        lists: dict[str, list[str]] = {}
        scores: dict[str, list[float]] = {}
        t0 = time.perf_counter()
        for q in questions:
            eid = q["eval_id"]
            ids, sc, ms = run_one_query(cur, qtable, q, condition, qvecs[eid])
            lists[eid] = ids
            scores[eid] = sc
            per_query_ms[eid].append(ms)
        sweep_seconds.append(time.perf_counter() - t0)
        per_q, agg, mean_rec, n_short = score_sweep(
            questions, lists, scores, exact_lists, condition, n
        )
        signatures.append(metric_signature(per_q))
        last_per_q = per_q
        last_agg = agg
        last_rec = mean_rec
        last_short = n_short
        last_lists = lists

    disagree = 0
    if signatures:
        base = signatures[0]
        for sig in signatures[1:]:
            if sig != base:
                disagree += 1

    query_medians = [statistics.median(xs) for xs in per_query_ms.values() if xs]
    p50 = round(percentile_linear(query_medians, 50), 3) if query_medians else None
    p95 = round(percentile_linear(query_medians, 95), 3) if query_medians else None
    exact_hit10 = exact_metrics.get((condition, n), {}).get("hit_at_10")
    subset_exact_hit10 = exact_hit10_on_subset(questions, exact_lists, condition, n)
    if exact_hit10 is None:
        exact_hit10 = subset_exact_hit10

    keep_lists = ef == 200
    per_q_out = last_per_q if keep_lists else None
    if per_q_out is None:
        per_q_out = [
            {
                "question_id": p["question_id"],
                "eval_id": p["eval_id"],
                "rank": p["rank"],
                "hit_at_1": p["hit_at_1"],
                "hit_at_5": p["hit_at_5"],
                "hit_at_10": p["hit_at_10"],
                "mrr": p["mrr"],
                "document_recall": p["document_recall"],
                "n_retrieved": p["n_retrieved"],
                "shortfall": p["shortfall"],
                "recall_at_10_vs_exact": p["recall_at_10_vs_exact"],
            }
            for p in last_per_q
        ]

    return {
        "embedder": embedder,
        "scale_n": n,
        "table": qtable,
        "condition": condition,
        "ef_search": ef,
        "iterative_scan": mode,
        "max_scan_tuples": guc.get("max_scan_tuples_set")
        if guc.get("max_scan_tuples_set") is not None
        else DEFAULT_MAX_SCAN_TUPLES,
        "seqscan_off": seqscan_off,
        "n_questions": len(questions),
        "guc": guc,
        "plan": {
            k: v
            for k, v in plan.items()
            if k != "plan"
        },
        "plan_full": plan.get("plan"),
        "metrics": last_agg,
        "recall_at_10_vs_exact": last_rec,
        "hit_at_10_exact": exact_hit10,
        "hit_at_10_exact_on_evaluated": subset_exact_hit10,
        "hit_at_10_drop": round(float(subset_exact_hit10) - float(last_agg["hit_at_10"]), 4),
        "n_queries_short_of_10": last_short,
        "warmup_passes": 1,
        "timed_repeats": repeats,
        "sweeps_agree": disagree == 0,
        "n_repeat_metric_mismatches": disagree,
        "latency": {
            "p50_query_ms": p50,
            "p95_query_ms": p95,
            "mean_per_sweep_s": round(sum(sweep_seconds) / len(sweep_seconds), 4)
            if sweep_seconds
            else None,
            "per_sweep_s": [round(s, 4) for s in sweep_seconds],
        },
        "per_question": per_q_out if keep_lists else None,
        "per_question_metrics_only": None if keep_lists else per_q_out,
        "retrieved_fingerprint": hashlib.sha256(
            json.dumps(last_lists, sort_keys=True).encode("utf-8")
        ).hexdigest(),
    }


def cache_path(cache_dir: Path, cid: str) -> Path:
    return cache_dir / f"{cid}.json"


def write_json_atomic(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, indent=2, default=str) + "\n", encoding="utf-8")
    tmp.replace(path)


def enumerate_cells(
    embedder: str,
    scales: list[int],
    conditions: list[str],
    efs: list[int],
    modes: list[str],
    n_questions: int,
    extra_mst: bool,
) -> list[dict[str, Any]]:
    cells = []
    for n in scales:
        for cond in conditions:
            for ef in efs:
                for mode in modes:
                    cells.append(
                        {
                            "embedder": embedder,
                            "n": n,
                            "condition": cond,
                            "ef": ef,
                            "mode": mode,
                            "max_scan_tuples": None,
                            "mst_label": DEFAULT_MAX_SCAN_TUPLES,
                            "seqscan_off": False,
                            "id": cell_id(
                                embedder,
                                n,
                                cond,
                                ef,
                                mode,
                                DEFAULT_MAX_SCAN_TUPLES,
                                n_questions,
                                False,
                            ),
                        }
                    )
    if extra_mst:
        for cond in EXTRA_MST_CONDS:
            if cond not in conditions:
                continue
            if EXTRA_MST_N not in scales:
                continue
            if EXTRA_MST_EF not in efs:
                continue
            for mode in modes:
                cells.append(
                    {
                        "embedder": embedder,
                        "n": EXTRA_MST_N,
                        "condition": cond,
                        "ef": EXTRA_MST_EF,
                        "mode": mode,
                        "max_scan_tuples": EXTRA_MST,
                        "mst_label": EXTRA_MST,
                        "seqscan_off": False,
                        "id": cell_id(
                            embedder,
                            EXTRA_MST_N,
                            cond,
                            EXTRA_MST_EF,
                            mode,
                            EXTRA_MST,
                            n_questions,
                            False,
                        ),
                    }
                )
    return cells


def progress_line(cell: dict[str, Any], rec: dict[str, Any], skipped: bool) -> str:
    plan = rec.get("plan") or {}
    lat = rec.get("latency") or {}
    tag = "SKIP" if skipped else "DONE"
    return (
        f"{tag} {rec.get('embedder')} N={rec.get('scale_n')} cond={rec.get('condition')} "
        f"ef={rec.get('ef_search')} mode={rec.get('iterative_scan')} "
        f"mst={rec.get('max_scan_tuples')} seqscan_off={rec.get('seqscan_off')} "
        f"n={rec.get('n_questions')} recall@10={rec.get('recall_at_10_vs_exact')} "
        f"hit@10={ (rec.get('metrics') or {}).get('hit_at_10') } "
        f"short={rec.get('n_queries_short_of_10')} "
        f"p50_ms={lat.get('p50_query_ms')} p95_ms={lat.get('p95_query_ms')} "
        f"plan={plan.get('plan_kind')} hnsw={plan.get('used_expected_hnsw_index')} "
        f"sort={plan.get('has_sort')} agree={rec.get('sweeps_agree')}"
    )


def maybe_seqscan_off_spec(spec: dict[str, Any], rec: dict[str, Any], n_questions: int) -> dict[str, Any] | None:
    plan = rec.get("plan") or {}
    if spec.get("seqscan_off"):
        return None
    if not plan.get("seq_scan"):
        return None
    return {
        "embedder": spec["embedder"],
        "n": spec["n"],
        "condition": spec["condition"],
        "ef": spec["ef"],
        "mode": spec["mode"],
        "max_scan_tuples": spec["max_scan_tuples"],
        "mst_label": spec["mst_label"],
        "seqscan_off": True,
        "id": cell_id(
            spec["embedder"],
            spec["n"],
            spec["condition"],
            spec["ef"],
            spec["mode"],
            spec["mst_label"],
            n_questions,
            True,
        ),
    }


def slim_cell(rec: dict[str, Any], include_per_question: bool) -> dict[str, Any]:
    out = dict(rec)
    out.pop("plan_full", None)
    if include_per_question and rec.get("ef_search") == 200 and not rec.get("seqscan_off"):
        out["per_question"] = rec.get("per_question")
    else:
        out["per_question"] = None
    out.pop("per_question_metrics_only", None)
    return out


def md_table(headers: list[str], rows: list[list[Any]]) -> list[str]:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---:" if h != "mode" and h != "cond" else "---" for h in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join("" if c is None else str(c) for c in row) + " |")
    return lines


def pick_cell(
    cells: list[dict[str, Any]],
    *,
    n: int,
    condition: str,
    ef: int,
    mode: str,
    mst: int,
    seqscan_off: bool = False,
) -> dict[str, Any] | None:
    for c in cells:
        if (
            int(c.get("scale_n")) == n
            and c.get("condition") == condition
            and int(c.get("ef_search")) == ef
            and c.get("iterative_scan") == mode
            and int(c.get("max_scan_tuples")) == mst
            and bool(c.get("seqscan_off")) == seqscan_off
        ):
            return c
    return None


def write_embedder_artifacts(
    embedder: str,
    cells: list[dict[str, Any]],
    meta: dict[str, Any],
    build_by_n: dict[int, dict[str, Any]],
    shared_buffers: str,
    write_published: bool,
) -> tuple[Path, Path]:
    payload = {
        "created_at": utc_now(),
        "script": "scripts/erb/revision1/eval_per_n_hnsw.py",
        "embedder": embedder,
        "meta": meta,
        "cells": [
            slim_cell(c, include_per_question=False)
            for c in cells
        ],
        "per_question_ef200": {},
    }
    for c in cells:
        if int(c.get("ef_search") or 0) != 200 or c.get("seqscan_off"):
            continue
        if c.get("per_question") is None:
            continue
        key = (
            f"N={c['scale_n']}|{c['condition']}|ef={c['ef_search']}|"
            f"{c['iterative_scan']}|mst={c['max_scan_tuples']}"
        )
        payload["per_question_ef200"][key] = c["per_question"]

    dest_json = REV1 / f"per_n_hnsw_eval_{embedder}.json"
    dest_md = REV1 / f"per_n_hnsw_eval_{embedder}.md"
    if not write_published:
        dest_json = DATA / f"rev1_per_n_hnsw_smoke_{embedder}.json"
        dest_md = DATA / f"rev1_per_n_hnsw_smoke_{embedder}.md"

    scales = sorted({int(c["scale_n"]) for c in cells})
    efs = sorted({int(c["ef_search"]) for c in cells})
    modes = sorted({str(c["iterative_scan"]) for c in cells})

    lines = [
        f"# Per-N HNSW vs exact (W9, {embedder})",
        "",
        f"Generated: {payload['created_at']}",
        f"Questions: {meta.get('n_questions')}",
        f"Repeats: {meta.get('repeats')}",
        f"shared_buffers: {shared_buffers}",
        "",
        "## 1. recall@10 vs exact top-10 (raw, /10 set overlap)",
        "",
    ]
    for mode in modes:
        lines.append(f"### iterative_scan = {mode}, max_scan_tuples default {DEFAULT_MAX_SCAN_TUPLES}")
        lines.append("")
        headers = ["N"] + [f"ef={ef}" for ef in efs]
        rows = []
        for n in scales:
            row: list[Any] = [n]
            for ef in efs:
                cell = pick_cell(
                    cells, n=n, condition="raw", ef=ef, mode=mode, mst=DEFAULT_MAX_SCAN_TUPLES
                )
                row.append(None if cell is None else cell.get("recall_at_10_vs_exact"))
            rows.append(row)
        lines.extend(md_table(headers, rows))
        lines.append("")

    lines.extend(["## 2. Hit@10 drop (exact − HNSW), raw", ""])
    for mode in modes:
        lines.append(f"### iterative_scan = {mode}")
        lines.append("")
        headers = ["N"] + [f"ef={ef}" for ef in efs]
        rows = []
        for n in scales:
            row = [n]
            for ef in efs:
                cell = pick_cell(
                    cells, n=n, condition="raw", ef=ef, mode=mode, mst=DEFAULT_MAX_SCAN_TUPLES
                )
                row.append(None if cell is None else cell.get("hit_at_10_drop"))
            rows.append(row)
        lines.extend(md_table(headers, rows))
        lines.append("")

    lines.extend(["## 3. Latency (raw, p50 / p95 ms of per-query medians over repeats)", ""])
    for mode in modes:
        lines.append(f"### iterative_scan = {mode}")
        lines.append("")
        headers = ["N"] + [f"ef={ef} p50" for ef in efs] + [f"ef={ef} p95" for ef in efs]
        rows = []
        for n in scales:
            row = [n]
            for ef in efs:
                cell = pick_cell(
                    cells, n=n, condition="raw", ef=ef, mode=mode, mst=DEFAULT_MAX_SCAN_TUPLES
                )
                lat = (cell or {}).get("latency") or {}
                row.append(lat.get("p50_query_ms"))
            for ef in efs:
                cell = pick_cell(
                    cells, n=n, condition="raw", ef=ef, mode=mode, mst=DEFAULT_MAX_SCAN_TUPLES
                )
                lat = (cell or {}).get("latency") or {}
                row.append(lat.get("p95_query_ms"))
            rows.append(row)
        lines.extend(md_table(headers, rows))
        lines.append("")

    lines.extend(
        [
            "## 4. Capacity (index / table from W8; latency = raw, ef=200, relaxed_order)",
            "",
        ]
    )
    cap_headers = [
        "N",
        "rows",
        "table_MB",
        "hnsw_index_MB",
        "build_s",
        "p50_ms",
        "p95_ms",
        "mean_sweep_s",
    ]
    cap_rows = []
    for n in scales:
        b = build_by_n.get(n) or {}
        cell = pick_cell(
            cells,
            n=n,
            condition="raw",
            ef=200,
            mode="relaxed_order",
            mst=DEFAULT_MAX_SCAN_TUPLES,
        )
        lat = (cell or {}).get("latency") or {}
        table_b = b.get("table_bytes")
        idx_b = b.get("hnsw_index_bytes")
        cap_rows.append(
            [
                n,
                b.get("row_count"),
                None if table_b is None else round(float(table_b) / 1e6, 2),
                None if idx_b is None else round(float(idx_b) / 1e6, 2),
                None
                if b.get("hnsw_build_seconds") is None
                else round(float(b["hnsw_build_seconds"]), 2),
                lat.get("p50_query_ms"),
                lat.get("p95_query_ms"),
                lat.get("mean_per_sweep_s"),
            ]
        )
    lines.extend(md_table(cap_headers, cap_rows))
    lines.append("")

    extra = [
        c
        for c in cells
        if int(c.get("max_scan_tuples") or 0) == EXTRA_MST
    ]
    if extra:
        lines.extend(["## Extra max_scan_tuples=100000 (N=100000, ef=200)", ""])
        headers = ["cond", "mode", "recall@10", "hit@10", "drop", "short", "p50_ms", "p95_ms"]
        rows = []
        for c in extra:
            m = c.get("metrics") or {}
            lat = c.get("latency") or {}
            rows.append(
                [
                    c.get("condition"),
                    c.get("iterative_scan"),
                    c.get("recall_at_10_vs_exact"),
                    m.get("hit_at_10"),
                    c.get("hit_at_10_drop"),
                    c.get("n_queries_short_of_10"),
                    lat.get("p50_query_ms"),
                    lat.get("p95_query_ms"),
                ]
            )
        lines.extend(md_table(headers, rows))
        lines.append("")

    n5k = [c for c in cells if int(c.get("scale_n")) == 5000]
    if n5k:
        lines.extend(["## N=5000 planner (HNSW vs seq scan)", ""])
        headers = [
            "cond",
            "ef",
            "mode",
            "seqscan_off",
            "plan_kind",
            "used_n_*_hnsw",
            "has_sort",
            "recall@10",
        ]
        rows = []
        for c in n5k:
            plan = c.get("plan") or {}
            rows.append(
                [
                    c.get("condition"),
                    c.get("ef_search"),
                    c.get("iterative_scan"),
                    c.get("seqscan_off"),
                    plan.get("plan_kind"),
                    plan.get("used_expected_hnsw_index"),
                    plan.get("has_sort"),
                    c.get("recall_at_10_vs_exact"),
                ]
            )
        lines.extend(md_table(headers, rows))
        lines.append("")

    dest_json.parent.mkdir(parents=True, exist_ok=True)
    write_json_atomic(dest_json, payload)
    dest_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return dest_json, dest_md


def acceptance_report(cells: list[dict[str, Any]], expected_n: int) -> list[dict[str, Any]]:
    tests: list[dict[str, Any]] = []
    raw_default = [
        c
        for c in cells
        if c.get("condition") == "raw"
        and not c.get("seqscan_off")
        and int(c.get("max_scan_tuples") or 0) == DEFAULT_MAX_SCAN_TUPLES
    ]
    violations = []
    grouped: dict[tuple[int, str], dict[int, float]] = {}
    for c in raw_default:
        key = (int(c["scale_n"]), str(c["iterative_scan"]))
        grouped.setdefault(key, {})[int(c["ef_search"])] = float(c.get("recall_at_10_vs_exact") or 0.0)
    compared = 0
    for (n, mode), by_ef in sorted(grouped.items()):
        r200 = by_ef.get(200)
        r800 = by_ef.get(800)
        if r200 is None or r800 is None:
            continue
        compared += 1
        if r800 + 1e-12 < r200:
            violations.append(
                {"N": n, "mode": mode, "recall_ef200": r200, "recall_ef800": r800}
            )
    if compared == 0:
        ef800_status = "SKIP"
    elif violations:
        ef800_status = "FAIL"
    else:
        ef800_status = "PASS"
    tests.append(
        {
            "name": "ef_search 800 raw recall@10 >= ef_search 200 for every N",
            "status": ef800_status,
            "violations": violations,
            "compared_groups": compared,
        }
    )

    nq_ok = all(int(c.get("n_questions") or 0) == expected_n for c in cells)
    tests.append(
        {
            "name": f"every cell has {expected_n} evaluated questions",
            "status": "PASS" if cells and nq_ok else "FAIL",
            "n_cells": len(cells),
            "n_questions_values": sorted({int(c.get("n_questions") or 0) for c in cells}),
        }
    )

    plan_ok = all((c.get("plan") or {}).get("plan_kind") for c in cells)
    tests.append(
        {
            "name": "plan type recorded for every cell",
            "status": "PASS" if cells and plan_ok else "FAIL",
            "missing": [
                c.get("embedder") and cell_id(
                    c["embedder"],
                    int(c["scale_n"]),
                    c["condition"],
                    int(c["ef_search"]),
                    c["iterative_scan"],
                    int(c["max_scan_tuples"]),
                    int(c["n_questions"]),
                    bool(c.get("seqscan_off")),
                )
                for c in cells
                if not (c.get("plan") or {}).get("plan_kind")
            ],
        }
    )

    disagree = [c for c in cells if not c.get("sweeps_agree")]
    tests.append(
        {
            "name": "repeated sweeps agree on metrics exactly",
            "status": "PASS" if not disagree else "FAIL",
            "n_disagree_cells": len(disagree),
            "examples": [
                {
                    "id": cell_id(
                        c["embedder"],
                        int(c["scale_n"]),
                        c["condition"],
                        int(c["ef_search"]),
                        c["iterative_scan"],
                        int(c["max_scan_tuples"]),
                        int(c["n_questions"]),
                        bool(c.get("seqscan_off")),
                    ),
                    "n_repeat_metric_mismatches": c.get("n_repeat_metric_mismatches"),
                }
                for c in disagree[:8]
            ],
        }
    )

    n5 = [c for c in cells if int(c.get("scale_n")) == 5000 and not c.get("seqscan_off")]
    kinds = sorted({(c.get("plan") or {}).get("plan_kind") for c in n5})
    seq_cells = [c for c in n5 if (c.get("plan") or {}).get("seq_scan")]
    off_cells = [c for c in cells if int(c.get("scale_n")) == 5000 and c.get("seqscan_off")]
    tests.append(
        {
            "name": "N=5000 planner used HNSW index or sequential scan (both recorded if seq)",
            "status": "PASS" if n5 and (not seq_cells or off_cells) else ("FAIL" if n5 else "SKIP"),
            "default_plan_kinds": kinds,
            "n_seq_scan_cells": len(seq_cells),
            "n_seqscan_off_cells": len(off_cells),
        }
    )
    return tests


def parse_int_list(s: str | None, default: tuple[int, ...]) -> list[int]:
    if not s:
        return list(default)
    return [int(x.strip()) for x in s.split(",") if x.strip()]


def parse_str_list(s: str | None, default: tuple[str, ...]) -> list[str]:
    if not s:
        return list(default)
    return [x.strip() for x in s.split(",") if x.strip()]


def run_embedder(
    conn,
    embedder: str,
    args: argparse.Namespace,
    questions: list[dict],
    qvecs: dict[str, list[float]],
) -> tuple[list[dict[str, Any]], dict[str, Any], Path, Path]:
    cur = conn.cursor()
    load_start = loadavg()
    exact_lists, exact_metrics = load_exact_refs(embedder, questions)
    missing_exact = []
    for q in questions:
        for n in parse_int_list(args.scales, DEFAULT_SCALES):
            for cond in parse_str_list(args.conditions, DEFAULT_CONDITIONS):
                if (cond, n, q["eval_id"]) not in exact_lists:
                    missing_exact.append((cond, n, q["eval_id"]))
                    if len(missing_exact) > 12:
                        break
    if missing_exact:
        raise SystemExit(
            f"{embedder} exact ladder missing lists e.g. {missing_exact[:3]} "
            f"(count shown {len(missing_exact)})"
        )

    file_build = load_build_meta()
    db_build = fetch_build_log_db(cur, embedder)
    shared_buffers = show_guc(cur, "shared_buffers")
    scales = parse_int_list(args.scales, DEFAULT_SCALES)
    build_by_n: dict[int, dict[str, Any]] = {}
    for n in scales:
        rec = dict(file_build.get((embedder, n)) or {})
        if n in db_build:
            for k, v in db_build[n].items():
                if rec.get(k) is None:
                    rec[k] = v
            if "source" in db_build[n]:
                rec["source"] = (rec.get("source") or "") + "+" + db_build[n]["source"]
        if rec.get("table_bytes") is None or rec.get("hnsw_index_bytes") is None:
            rec.update(relation_sizes(cur, embedder, n))
            rec["size_source"] = (rec.get("source") or "") + "+pg_relation_size"
        build_by_n[n] = rec

    n_questions = len(questions)
    specs = enumerate_cells(
        embedder,
        scales,
        parse_str_list(args.conditions, DEFAULT_CONDITIONS),
        parse_int_list(args.ef_search, DEFAULT_EF),
        parse_str_list(args.iterative_scan, DEFAULT_MODES),
        n_questions,
        extra_mst=not args.skip_extra_mst,
    )
    cache_dir = Path(args.cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)

    results: list[dict[str, Any]] = []
    pending = list(specs)
    i = 0
    while i < len(pending):
        spec = pending[i]
        i += 1
        path = cache_path(cache_dir, spec["id"])
        if path.is_file() and not args.force:
            rec = json.loads(path.read_text(encoding="utf-8"))
            skipped = True
        else:
            rec = run_cell(
                cur,
                embedder=embedder,
                n=spec["n"],
                condition=spec["condition"],
                ef=spec["ef"],
                mode=spec["mode"],
                max_scan_tuples=spec["max_scan_tuples"],
                questions=questions,
                qvecs=qvecs,
                exact_lists=exact_lists,
                exact_metrics=exact_metrics,
                repeats=args.repeats,
                seqscan_off=spec["seqscan_off"],
            )
            rec["cell_id"] = spec["id"]
            rec["capacity"] = build_by_n.get(spec["n"])
            rec["shared_buffers"] = shared_buffers
            write_json_atomic(path, rec)
            skipped = False
        results.append(rec)
        print(progress_line(spec, rec, skipped), flush=True)
        extra = maybe_seqscan_off_spec(spec, rec, n_questions)
        if extra is not None:
            extra_ids = {s["id"] for s in pending}
            if extra["id"] not in extra_ids:
                pending.append(extra)
                print(
                    f"QUEUE seqscan_off for {spec['id']} because plan_kind="
                    f"{(rec.get('plan') or {}).get('plan_kind')}",
                    flush=True,
                )

    load_end = loadavg()
    pg_ver = show_guc(cur, "server_version")
    cur.execute("SELECT extversion FROM pg_extension WHERE extname = 'vector'")
    row = cur.fetchone()
    pgvector = row[0] if row else None
    write_published = args.write_artifacts if args.subset is not None else True
    meta = {
        "created_at": utc_now(),
        "embedder": embedder,
        "query_vector_key_rule": QUERY_VECTOR_KEY_RULE,
        "n_questions": n_questions,
        "repeats": args.repeats,
        "subset": args.subset,
        "scales": scales,
        "conditions": parse_str_list(args.conditions, DEFAULT_CONDITIONS),
        "ef_search": parse_int_list(args.ef_search, DEFAULT_EF),
        "iterative_scan": parse_str_list(args.iterative_scan, DEFAULT_MODES),
        "shared_buffers": shared_buffers,
        "postgresql_version": pg_ver,
        "pgvector_version": pgvector,
        "loadavg_start": load_start,
        "loadavg_end": load_end,
        "manifest_sha256": sha256_file(MANIFEST_PATH),
        "bank_sha256": sha256_file(BANK_PATH),
        "query_cache_sha256": sha256_file(EMBEDDERS[embedder]["cache_path"]),
        "exact_ladder_sha256": sha256_file(EMBEDDERS[embedder]["exact_path"]),
        "build_json_sha256": {k: sha256_file(v) for k, v in BUILD_JSON_FILES.items() if v.is_file()},
        "smoke": args.subset is not None,
        "write_published": write_published,
    }
    tests = acceptance_report(results, 200)
    this_run = {
        "name": f"this-run question count is {n_questions}",
        "status": "PASS" if all(int(c.get("n_questions") or 0) == n_questions for c in results) else "FAIL",
        "n_questions": n_questions,
        "subset": args.subset,
    }
    tests.insert(0, this_run)
    meta["acceptance"] = tests
    json_path, md_path = write_embedder_artifacts(
        embedder, results, meta, build_by_n, shared_buffers, write_published
    )
    meta["output_json"] = str(json_path)
    meta["output_md"] = str(md_path)
    print(f"WROTE {json_path}", flush=True)
    print(f"WROTE {md_path}", flush=True)
    for t in tests:
        print(
            f"ACCEPT {t['status']} {t['name']} { {k: v for k, v in t.items() if k not in ('name', 'status')} }",
            flush=True,
        )
    cur.close()
    return results, meta, json_path, md_path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--embedder", choices=["openai", "titan", "both"], default="both")
    parser.add_argument("--scales", default=None, help="Comma-separated N values")
    parser.add_argument("--conditions", default=None, help="raw,meta_first,meta_in")
    parser.add_argument("--ef-search", default=None, help="Comma-separated ef_search values")
    parser.add_argument(
        "--iterative-scan",
        default=None,
        help="Comma-separated hnsw.iterative_scan values",
    )
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument(
        "--subset",
        type=int,
        default=None,
        help="Use the first N primary-200 questions (smoke)",
    )
    parser.add_argument("--cache-dir", type=Path, default=CACHE_DIR_DEFAULT)
    parser.add_argument(
        "--skip-extra-mst",
        action="store_true",
        help="Skip extra max_scan_tuples=100000 cells",
    )
    parser.add_argument(
        "--write-artifacts",
        action="store_true",
        help="Write artifacts/published/revision1 even with --subset",
    )
    parser.add_argument("--force", action="store_true", help="Ignore cell cache")
    args = parser.parse_args()
    if args.repeats < 1:
        raise SystemExit("--repeats must be >= 1")

    questions = load_questions(args.subset)
    embedders = ["openai", "titan"] if args.embedder == "both" else [args.embedder]
    conn = pg_connect()
    try:
        for emb in embedders:
            eval_ids = [q["eval_id"] for q in questions]
            qvecs = load_query_cache(emb, eval_ids)
            print(
                f"PASS_START embedder={emb} n_questions={len(questions)} "
                f"repeats={args.repeats} loadavg={loadavg()}",
                flush=True,
            )
            run_embedder(conn, emb, args, questions, qvecs)
            print(f"PASS_END embedder={emb} loadavg={loadavg()}", flush=True)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
