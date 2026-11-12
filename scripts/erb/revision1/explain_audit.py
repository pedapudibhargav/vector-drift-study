#!/usr/bin/env python3
"""Query-plan audit of the original pgvector HNSW eval shape (revision 1, task W1).

Copies the SQL and session GUCs from scripts/erb/sync_vector_eval.py:eval_scale_raw
(table name parameterized for the Titan arm). Does not change recall code or tables.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

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

SCALES = (5000, 10000, 15000, 20000, 25000, 40000, 50000, 75000, 100000)
CONDITIONS = ("raw", "meta")
EF_VALUES = (200, 400, 800)
TOP_K = 10
SAMPLE_EF = (400, 800)
SAMPLE_N = 40
SAMPLE_SEED = 42

TABLES = (
    {
        "embedder": "openai",
        "table": "document_chunks",
        "hnsw_index": "idx_chunks_embedding_hnsw",
        "cache_path": OPENAI_CACHE,
        "cache_style": "flat",
    },
    {
        "embedder": "titan",
        "table": "document_chunks_titan",
        "hnsw_index": "idx_chunks_titan_embedding_hnsw",
        "cache_path": TITAN_CACHE,
        "cache_style": "titan_vectors",
    },
)

HNSW_INDEXES = {t["hnsw_index"] for t in TABLES}
BTREE_FILTER_INDEXES = {
    "idx_chunks_scale_rank",
    "idx_chunks_source_type",
    "idx_chunks_titan_scale_rank",
    "idx_chunks_titan_source_type",
}
SCAN_NODE_TYPES = {
    "Seq Scan",
    "Index Scan",
    "Index Only Scan",
    "Bitmap Heap Scan",
    "Bitmap Index Scan",
    "Tid Scan",
    "Sample Scan",
    "Foreign Scan",
    "Custom Scan",
    "Function Scan",
    "Values Scan",
    "CTE Scan",
    "Named Tuplestore Scan",
    "WorkTable Scan",
    "Subquery Scan",
}
TABLE_SCAN_TYPES = {
    "Seq Scan",
    "Index Scan",
    "Index Only Scan",
    "Bitmap Heap Scan",
    "Tid Scan",
    "Custom Scan",
}
VEC_IN_BRACKETS = re.compile(r"\[[-+0-9eE.,\s]{80,}\]")


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def vector_literal(vec: list[float]) -> str:
    return "[" + ",".join(str(v) for v in vec) + "]"


def loadavg() -> dict[str, Any]:
    out: dict[str, Any] = {"captured_at": utc_now()}
    try:
        out["os_getloadavg"] = list(os.getloadavg())
    except OSError as exc:
        out["os_getloadavg_error"] = str(exc)
    try:
        proc = subprocess.run(
            ["uptime"],
            check=False,
            capture_output=True,
            text=True,
        )
        out["uptime_stdout"] = (proc.stdout or "").strip()
        out["uptime_stderr"] = (proc.stderr or "").strip()
        out["uptime_returncode"] = int(proc.returncode)
    except OSError as exc:
        out["uptime_error"] = str(exc)
    return out


def pg_connect(port: int):
    conn = psycopg2.connect(
        host=os.environ.get("PGHOST", "localhost"),
        port=int(port),
        user=os.environ["PGUSER"],
        password=os.environ["PGPASSWORD"],
        dbname=os.environ["PGDATABASE"],
        connect_timeout=10,
    )
    conn.autocommit = True
    return conn


def load_questions() -> list[dict]:
    bank = json.loads(BANK_PATH.read_text(encoding="utf-8"))
    eval_ids = list(bank["question_ids"])
    if len(eval_ids) != 200:
        raise SystemExit(f"primary-200 bank has {len(eval_ids)} ids, expected 200")
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    by_eval = {q["eval_id"]: q for q in manifest.get("questions") or []}
    missing = [e for e in eval_ids if e not in by_eval]
    if missing:
        raise SystemExit(f"manifest missing {len(missing)} eval_ids (e.g. {missing[:3]})")
    return [by_eval[e] for e in eval_ids]


def load_query_cache(style: str, path: Path, eval_ids: list[str]) -> dict[str, list[float]]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    cache: dict[str, list[float]] = {}
    if style == "titan_vectors":
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
        raise SystemExit(f"{path.name} missing {len(missing)} embeddings (e.g. {missing[:3]})")
    return cache


def sample40(questions: list[dict]) -> list[dict]:
    rng = np.random.default_rng(SAMPLE_SEED)
    idx = rng.choice(len(questions), size=SAMPLE_N, replace=False)
    return [questions[int(i)] for i in idx]


def build_sql(table: str, condition: str) -> str:
    metadata_filter = " AND source_type = %s" if condition == "meta" else ""
    return f"""
            SELECT doc_id, 1 - (embedding <=> %s::vector) AS score
            FROM {table}
            WHERE embedding IS NOT NULL
              AND scale_rank IS NOT NULL
              AND scale_rank < %s
              {metadata_filter}
            ORDER BY embedding <=> %s::vector
            LIMIT {TOP_K}
        """


def explain_sql(table: str, condition: str) -> str:
    return "EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON)\n" + build_sql(table, condition)


def sanitize_plan(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {str(k): sanitize_plan(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [sanitize_plan(v) for v in obj]
    if isinstance(obj, str):
        if len(obj) > 120 and ("<=>" in obj or obj.strip().startswith("[")):
            return VEC_IN_BRACKETS.sub("[VECTOR]", obj)
        if len(obj) > 400:
            return obj[:200] + "…[truncated]…" + obj[-40:]
        return obj
    return obj


def walk_plan(node: dict, acc: dict, ancestors: list[str]) -> None:
    ntype = str(node.get("Node Type") or "")
    acc["node_types"].append(ntype)
    idx = node.get("Index Name")
    if idx:
        acc["index_names"].append(str(idx))
    if ntype == "Limit":
        acc["limit_actual_rows"] = node.get("Actual Rows")
    if ntype in SCAN_NODE_TYPES:
        actual_rows = node.get("Actual Rows")
        actual_loops = node.get("Actual Loops")
        loops_i = 1
        try:
            if actual_loops is not None:
                loops_i = int(actual_loops)
        except (TypeError, ValueError):
            loops_i = 1
        per_loop = actual_rows
        total_rows = actual_rows
        try:
            if actual_rows is not None:
                per_loop_i = int(actual_rows)
                total_rows = per_loop_i * loops_i
        except (TypeError, ValueError):
            total_rows = actual_rows
        rec = {
            "node_type": ntype,
            "index_name": str(idx) if idx else None,
            "actual_rows_per_loop": per_loop,
            "actual_rows_total": total_rows,
            "actual_loops": loops_i,
            "ancestors": list(ancestors),
        }
        acc["scans"].append(rec)
        if ntype in TABLE_SCAN_TYPES:
            acc["table_scans"].append(rec)
        if "Sort" in ancestors:
            acc["sort_above_scan"] = True
    for child in node.get("Plans") or []:
        if isinstance(child, dict):
            walk_plan(child, acc, ancestors + [ntype])


def summarize_plan(explain_root: dict) -> dict[str, Any]:
    plan = explain_root["Plan"]
    acc: dict[str, Any] = {
        "node_types": [],
        "index_names": [],
        "scans": [],
        "table_scans": [],
        "sort_above_scan": False,
        "limit_actual_rows": plan.get("Actual Rows"),
    }
    walk_plan(plan, acc, [])
    node_types = acc["node_types"]
    index_names = acc["index_names"]
    hnsw_used = any(name in HNSW_INDEXES for name in index_names)
    btree_used = any(name in BTREE_FILTER_INDEXES for name in index_names)
    scan_rows = None
    scan_rows_per_loop = None
    if acc["table_scans"]:
        scan_rows = acc["table_scans"][0].get("actual_rows_total")
        scan_rows_per_loop = acc["table_scans"][0].get("actual_rows_per_loop")
    elif acc["scans"]:
        scan_rows = acc["scans"][0].get("actual_rows_total")
        scan_rows_per_loop = acc["scans"][0].get("actual_rows_per_loop")
    limit_rows = acc["limit_actual_rows"]
    try:
        limit_rows_i = int(limit_rows) if limit_rows is not None else None
    except (TypeError, ValueError):
        limit_rows_i = None
    try:
        scan_rows_i = int(scan_rows) if scan_rows is not None else None
    except (TypeError, ValueError):
        scan_rows_i = None
    try:
        scan_rows_per_loop_i = int(scan_rows_per_loop) if scan_rows_per_loop is not None else None
    except (TypeError, ValueError):
        scan_rows_per_loop_i = None
    return {
        "node_types": node_types,
        "node_types_unique": list(dict.fromkeys(node_types)),
        "index_names": list(dict.fromkeys(index_names)),
        "hnsw_used": bool(hnsw_used),
        "seq_scan": "Seq Scan" in node_types,
        "btree_scale_or_source": bool(btree_used),
        "has_sort": "Sort" in node_types,
        "sort_above_scan": bool(acc["sort_above_scan"]),
        "scan_actual_rows": scan_rows_i,
        "scan_actual_rows_per_loop": scan_rows_per_loop_i,
        "limit_actual_rows": limit_rows_i,
        "would_exact_fallback": bool(limit_rows_i is not None and limit_rows_i < TOP_K),
        "exec_ms": float(explain_root.get("Execution Time")),
        "planning_ms": float(explain_root.get("Planning Time")),
        "shared_hit": int(plan.get("Shared Hit Blocks") or 0),
        "shared_read": int(plan.get("Shared Read Blocks") or 0),
    }


def median(xs: list[float]) -> float:
    if not xs:
        return float("nan")
    return float(np.median(np.asarray(xs, dtype=np.float64)))


def p95(xs: list[float]) -> float:
    if not xs:
        return float("nan")
    return float(np.percentile(np.asarray(xs, dtype=np.float64), 95))


def collect_inventory(cur) -> dict[str, Any]:
    cur.execute("SELECT version()")
    pg_version = cur.fetchone()[0]
    cur.execute("SELECT extversion FROM pg_extension WHERE extname = 'vector'")
    row = cur.fetchone()
    pgvector = row[0] if row else None
    cur.execute(
        """
        SELECT tablename, indexname, indexdef
        FROM pg_indexes
        WHERE tablename IN ('document_chunks', 'document_chunks_titan')
        ORDER BY 1, 2
        """
    )
    indexes = [
        {"tablename": a, "indexname": b, "indexdef": c} for a, b, c in cur.fetchall()
    ]
    hnsw_present = [
        ix
        for ix in indexes
        if " using hnsw " in ix["indexdef"].lower() or " USING hnsw " in ix["indexdef"]
    ]
    cur.execute(
        """
        SELECT c.relname,
               pg_relation_size(c.oid) AS bytes,
               pg_size_pretty(pg_relation_size(c.oid)) AS pretty
        FROM pg_class c
        JOIN pg_namespace n ON n.oid = c.relnamespace
        WHERE n.nspname = 'public'
          AND c.relname IN (
            'document_chunks', 'document_chunks_titan',
            'idx_chunks_embedding_hnsw', 'idx_chunks_titan_embedding_hnsw',
            'idx_chunks_scale_rank', 'idx_chunks_titan_scale_rank',
            'idx_chunks_source_type', 'idx_chunks_titan_source_type'
          )
        ORDER BY 1
        """
    )
    sizes = [
        {"relname": a, "bytes": int(b), "pretty": c} for a, b, c in cur.fetchall()
    ]
    wanted = [
        "shared_buffers",
        "work_mem",
        "effective_cache_size",
        "max_parallel_workers_per_gather",
        "random_page_cost",
        "seq_page_cost",
        "enable_indexscan",
        "enable_bitmapscan",
        "enable_seqscan",
    ]
    settings: dict[str, str] = {}
    for name in wanted:
        cur.execute("SELECT current_setting(%s)", (name,))
        settings[name] = cur.fetchone()[0]
    cur.execute(
        "SELECT name, setting FROM pg_settings WHERE name LIKE 'hnsw%' ORDER BY 1"
    )
    hnsw_settings = {a: b for a, b in cur.fetchall()}
    settings.update(hnsw_settings)
    return {
        "postgres_version": pg_version,
        "pgvector_version": pgvector,
        "indexes": indexes,
        "hnsw_indexes": hnsw_present,
        "relation_sizes": sizes,
        "settings": settings,
    }


def set_hnsw_gucs(cur, ef_search: int) -> dict[str, Any]:
    cur.execute(f"SET hnsw.ef_search = {int(ef_search)}")
    iterative_ok = True
    iterative_error = None
    try:
        cur.execute("SET hnsw.iterative_scan = relaxed_order")
    except Exception as exc:
        iterative_ok = False
        iterative_error = str(exc)
    return {"iterative_scan_set": iterative_ok, "iterative_scan_error": iterative_error}


def cell_key(pass_name: str, table: str, condition: str, scale: int, ef: int) -> str:
    return f"{pass_name}|{table}|{condition}|{scale}|{ef}"


def aggregate_cell(
    *,
    pass_name: str,
    embedder: str,
    table: str,
    condition: str,
    scale: int,
    ef: int,
    rows: list[dict],
    example_plan: Any,
    guc: dict[str, Any],
) -> dict[str, Any]:
    n = len(rows)
    return {
        "pass": pass_name,
        "embedder": embedder,
        "table": table,
        "condition": condition,
        "scale": int(scale),
        "ef_search": int(ef),
        "n_plans": n,
        "frac_hnsw": (sum(1 for r in rows if r["hnsw_used"]) / n) if n else float("nan"),
        "frac_seq": (sum(1 for r in rows if r["seq_scan"]) / n) if n else float("nan"),
        "frac_btree_scale_or_source": (
            sum(1 for r in rows if r["btree_scale_or_source"]) / n if n else float("nan")
        ),
        "frac_sort": (sum(1 for r in rows if r["has_sort"]) / n) if n else float("nan"),
        "frac_sort_above_scan": (
            sum(1 for r in rows if r["sort_above_scan"]) / n if n else float("nan")
        ),
        "median_exec_ms": median([r["exec_ms"] for r in rows]),
        "p95_exec_ms": p95([r["exec_ms"] for r in rows]),
        "median_shared_read": median([float(r["shared_read"]) for r in rows]),
        "median_shared_hit": median([float(r["shared_hit"]) for r in rows]),
        "median_planning_ms": median([r["planning_ms"] for r in rows]),
        "n_lt_10_rows": sum(1 for r in rows if r["would_exact_fallback"]),
        "node_type_counter": dict(
            Counter(" > ".join(r["node_types"]) for r in rows)
        ),
        "guc": guc,
        "queries": rows,
        "example_plan": example_plan,
    }


def write_json_atomic(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    text = json.dumps(obj, indent=2, ensure_ascii=True, allow_nan=False) + "\n"
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(path)


def fmt_frac(x: float) -> str:
    if x != x:
        return "nan"
    return f"{x:.3f}"


def fmt_num(x: float) -> str:
    if x != x:
        return "nan"
    if abs(x) >= 100:
        return f"{x:.1f}"
    return f"{x:.3f}"


def plan_signature(cell: dict) -> str:
    counts = cell.get("node_type_counter") or {}
    if not counts:
        return "empty"
    return max(counts.items(), key=lambda kv: kv[1])[0]


def anomalies(cells: list[dict]) -> list[str]:
    notes: list[str] = []
    groups: dict[tuple, list[dict]] = {}
    for c in cells:
        key = (c["pass"], c["table"], c["condition"], c["ef_search"])
        groups.setdefault(key, []).append(c)
    for key, rows in groups.items():
        rows = sorted(rows, key=lambda r: r["scale"])
        prev = None
        for r in rows:
            sig = plan_signature(r)
            h = r["frac_hnsw"]
            if prev is not None:
                if sig != prev["sig"] or abs(h - prev["h"]) > 1e-9:
                    notes.append(
                        f"{key[0]} {key[1]} {key[2]} ef={key[3]}: "
                        f"scale {prev['scale']} sig={prev['sig']} frac_hnsw={prev['h']:.3f} "
                        f"then scale {r['scale']} sig={sig} frac_hnsw={h:.3f}"
                    )
            prev = {"scale": r["scale"], "sig": sig, "h": h}
    return notes


def render_md(payload: dict) -> str:
    lines: list[str] = []
    port = payload["port"]
    lines.append(f"# pgvector plan audit (port {port})")
    lines.append("")
    lines.append(f"Generated: {payload['generated_at']}")
    lines.append("")
    lines.append("## Server")
    lines.append("")
    lines.append(f"- PostgreSQL: `{payload['postgres_version']}`")
    lines.append(f"- pgvector: `{payload['pgvector_version']}`")
    lines.append("- Settings:")
    for k in (
        "shared_buffers",
        "work_mem",
        "effective_cache_size",
        "max_parallel_workers_per_gather",
        "hnsw.ef_search",
        "hnsw.iterative_scan",
        "hnsw.max_scan_tuples",
        "hnsw.scan_mem_multiplier",
    ):
        if k in payload["settings"]:
            lines.append(f"  - `{k}` = `{payload['settings'][k]}`")
    lines.append("")
    lines.append("## HNSW indexes and relation sizes")
    lines.append("")
    lines.append("| relname | bytes | pretty |")
    lines.append("|---|---:|---|")
    for r in payload["relation_sizes"]:
        lines.append(f"| `{r['relname']}` | {r['bytes']} | {r['pretty']} |")
    lines.append("")
    lines.append("HNSW index defs:")
    lines.append("")
    for ix in payload["hnsw_indexes"]:
        lines.append(f"- `{ix['tablename']}.{ix['indexname']}`: `{ix['indexdef']}`")
    lines.append("")
    lines.append("## Load average")
    lines.append("")
    lines.append(f"- start: `{payload['loadavg_start']}`")
    lines.append(f"- end: `{payload['loadavg_end']}`")
    lines.append("")
    lines.append("Query shape matches `eval_scale_raw`:")
    lines.append("`SET hnsw.ef_search`; `SET hnsw.iterative_scan = relaxed_order`;")
    lines.append(
        "`SELECT doc_id, 1 - (embedding <=> $vec::vector) AS score FROM <table> "
        "WHERE embedding IS NOT NULL AND scale_rank IS NOT NULL AND scale_rank < $N "
        "[AND source_type = $st] ORDER BY embedding <=> $vec::vector LIMIT 10`."
    )
    lines.append("")
    lines.append(
        "Buffers are the **root Plan node** Shared Hit/Read Blocks "
        "(PostgreSQL 16 JSON EXPLAIN includes child buffers there). "
        "Example plans have vector literals replaced with `[VECTOR]`."
    )
    lines.append("")
    lines.append("## Per-cell summary")
    lines.append("")
    lines.append(
        "| pass | table | cond | scale | ef | n | frac_hnsw | frac_seq | "
        "frac_btree | frac_sort | median_ms | p95_ms | median_read | n_lt_10 |"
    )
    lines.append("|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
    for c in payload["cells"]:
        lines.append(
            f"| {c['pass']} | `{c['table']}` | {c['condition']} | {c['scale']} | "
            f"{c['ef_search']} | {c['n_plans']} | {fmt_frac(c['frac_hnsw'])} | "
            f"{fmt_frac(c['frac_seq'])} | {fmt_frac(c['frac_btree_scale_or_source'])} | "
            f"{fmt_frac(c['frac_sort'])} | {fmt_num(c['median_exec_ms'])} | "
            f"{fmt_num(c['p95_exec_ms'])} | {fmt_num(c['median_shared_read'])} | "
            f"{c['n_lt_10_rows']} |"
        )
    lines.append("")
    lines.append("## Did this configuration use the HNSW index?")
    lines.append("")
    lines.append(
        "Values are fractions of queries in that cell. This is a planner audit, not a recall result."
    )
    lines.append("")
    grouped: dict[tuple, list[dict]] = {}
    for c in payload["cells"]:
        grouped.setdefault((c["pass"], c["table"], c["condition"], c["ef_search"]), []).append(c)
    for key in sorted(grouped):
        rows = sorted(grouped[key], key=lambda r: r["scale"])
        bits = ", ".join(
            f"N={r['scale']}:{r['frac_hnsw']:.3f}" for r in rows
        )
        lines.append(
            f"- `{key[0]}` `{key[1]}` `{key[2]}` ef={key[3]} frac_hnsw by scale: {bits}"
        )
    lines.append("")
    lines.append("## Plan-type changes vs neighbouring scales")
    lines.append("")
    notes = payload.get("anomalies") or []
    if not notes:
        lines.append("No neighbouring-scale plan signature changes.")
    else:
        for n in notes:
            lines.append(f"- {n}")
    lines.append("")
    lines.append("## Acceptance")
    lines.append("")
    acc = payload.get("acceptance") or {}
    for name, rec in acc.items():
        status = rec.get("status")
        lines.append(f"- `{name}`: **{status}** — {rec.get('detail')}")
    lines.append("")
    return "\n".join(lines) + "\n"


def load_completed(scratch: Path) -> dict[str, dict]:
    done: dict[str, dict] = {}
    if not scratch.exists():
        return done
    with scratch.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            cell = json.loads(line)
            done[cell_key(cell["pass"], cell["table"], cell["condition"], cell["scale"], cell["ef_search"])] = cell
    return done


def append_cell(scratch: Path, cell: dict) -> None:
    scratch.parent.mkdir(parents=True, exist_ok=True)
    with scratch.open("a", encoding="utf-8") as f:
        f.write(json.dumps(cell, ensure_ascii=True, allow_nan=False) + "\n")


def cells_in_order(done: dict[str, dict], pass_name: str) -> list[dict]:
    ordered: list[dict] = []
    scales = SCALES if pass_name == "forward" else tuple(reversed(SCALES))
    for spec in TABLES:
        for condition in CONDITIONS:
            for scale in scales:
                for ef in EF_VALUES:
                    k = cell_key(pass_name, spec["table"], condition, scale, ef)
                    if k in done:
                        ordered.append(done[k])
    return ordered


def hand_explain_check(cur, questions: list[dict], qvecs: dict[str, list[float]]) -> dict[str, Any]:
    q = questions[0]
    lit = vector_literal(qvecs[q["eval_id"]])
    sql = explain_sql("document_chunks", "raw")
    cur.execute(f"SET hnsw.ef_search = 200")
    try:
        cur.execute("SET hnsw.iterative_scan = relaxed_order")
    except Exception:
        pass
    cur.execute(sql, (lit, 5000, lit))
    raw = cur.fetchone()[0]
    root = raw[0] if isinstance(raw, list) else json.loads(raw)[0]
    summary = summarize_plan(root)
    return {
        "eval_id": q["eval_id"],
        "table": "document_chunks",
        "condition": "raw",
        "scale": 5000,
        "ef_search": 200,
        "node_types": summary["node_types"],
        "index_names": summary["index_names"],
        "hnsw_used": summary["hnsw_used"],
        "exec_ms": summary["exec_ms"],
    }


def run_audit(port: int, out_path: Path) -> dict[str, Any]:
    questions = load_questions()
    eval_ids = [q["eval_id"] for q in questions]
    q40 = sample40(questions)
    caches = {
        spec["embedder"]: load_query_cache(spec["cache_style"], spec["cache_path"], eval_ids)
        for spec in TABLES
    }
    scratch = DATA / f"rev1_plan_audit_{port}.jsonl"
    md_path = out_path.with_suffix(".md")

    t_connect = time.time()
    conn = pg_connect(port)
    connected_in_s = round(time.time() - t_connect, 3)
    cur = conn.cursor()
    inventory = collect_inventory(cur)
    load_start = loadavg()
    guc0 = set_hnsw_gucs(cur, 200)
    hand = hand_explain_check(cur, questions, caches["openai"])

    done = load_completed(scratch)
    passes = ("forward", "reverse")
    total_cells = 2 * len(TABLES) * len(CONDITIONS) * len(SCALES) * len(EF_VALUES)
    started = utc_now()
    t0 = time.time()

    print(
        f"port={port} inventory hnsw={len(inventory['hnsw_indexes'])} "
        f"shared_buffers={inventory['settings'].get('shared_buffers')} "
        f"resume_cells={len(done)}/{total_cells}",
        flush=True,
    )

    n_run = 0
    for pass_name in passes:
        scales = SCALES if pass_name == "forward" else tuple(reversed(SCALES))
        for spec in TABLES:
            table = spec["table"]
            embedder = spec["embedder"]
            qvecs = caches[embedder]
            for condition in CONDITIONS:
                sql = explain_sql(table, condition)
                for scale in scales:
                    for ef in EF_VALUES:
                        key = cell_key(pass_name, table, condition, scale, ef)
                        qs = questions if ef == 200 else q40
                        expected_n = 200 if ef == 200 else SAMPLE_N
                        if key in done and done[key].get("n_plans") == expected_n:
                            print(f"skip {key}", flush=True)
                            continue
                        guc = set_hnsw_gucs(cur, ef)
                        rows: list[dict] = []
                        example_plan = None
                        t_cell = time.time()
                        for q in qs:
                            eid = q["eval_id"]
                            lit = vector_literal(qvecs[eid])
                            if condition == "meta":
                                st = (q.get("source_types") or [None])[0]
                                if not st:
                                    raise SystemExit(f"missing source_types[0] for {eid}")
                                params = (lit, scale, str(st), lit)
                            else:
                                params = (lit, scale, lit)
                            cur.execute(sql, params)
                            raw = cur.fetchone()[0]
                            root = raw[0] if isinstance(raw, list) else json.loads(raw)[0]
                            summary = summarize_plan(root)
                            rec = {"eval_id": eid, **summary}
                            rows.append(rec)
                            if example_plan is None:
                                example_plan = sanitize_plan(root)
                        cell = aggregate_cell(
                            pass_name=pass_name,
                            embedder=embedder,
                            table=table,
                            condition=condition,
                            scale=scale,
                            ef=ef,
                            rows=rows,
                            example_plan=example_plan,
                            guc=guc,
                        )
                        append_cell(scratch, cell)
                        done[key] = cell
                        n_run += 1
                        dt = time.time() - t_cell
                        print(
                            f"{key} n={len(rows)} frac_hnsw={cell['frac_hnsw']:.3f} "
                            f"frac_btree={cell['frac_btree_scale_or_source']:.3f} "
                            f"frac_sort={cell['frac_sort']:.3f} "
                            f"n_lt_10={cell['n_lt_10_rows']} "
                            f"median_ms={cell['median_exec_ms']:.1f} cell_s={dt:.1f}",
                            flush=True,
                        )

    load_end = loadavg()
    cells: list[dict] = []
    for pass_name in passes:
        cells.extend(cells_in_order(done, pass_name))

    n_ok_200 = sum(1 for c in cells if c["ef_search"] == 200 and c["n_plans"] == 200)
    n_ok_sample = sum(1 for c in cells if c["ef_search"] in SAMPLE_EF and c["n_plans"] == SAMPLE_N)
    n_cells_200 = sum(1 for c in cells if c["ef_search"] == 200)
    n_cells_sample = sum(1 for c in cells if c["ef_search"] in SAMPLE_EF)
    expected_cells_200 = 2 * len(TABLES) * len(CONDITIONS) * len(SCALES)  # 2 passes
    expected_cells_sample = expected_cells_200 * len(SAMPLE_EF)

    fwd = [c for c in cells if c["pass"] == "forward"]
    target = next(
        (
            c
            for c in fwd
            if c["table"] == "document_chunks"
            and c["condition"] == "raw"
            and c["scale"] == 5000
            and c["ef_search"] == 200
        ),
        None,
    )
    hand_match = False
    hand_detail = "missing forward openai/raw/5000/ef200 cell"
    if target:
        first = target["queries"][0]
        hand_match = first["node_types"] == hand["node_types"]
        hand_detail = (
            f"hand node_types={hand['node_types']} "
            f"summary_first={first['node_types']} "
            f"eval_id_hand={hand['eval_id']} eval_id_first={first['eval_id']}"
        )

    acceptance = {
        "cell_counts": {
            "status": "PASS"
            if n_ok_200 == expected_cells_200 and n_ok_sample == expected_cells_sample
            else "FAIL",
            "detail": (
                f"ef200 cells with n=200: {n_ok_200}/{expected_cells_200} "
                f"(saw {n_cells_200}); ef400/800 cells with n=40: "
                f"{n_ok_sample}/{expected_cells_sample} (saw {n_cells_sample})"
            ),
        },
        "hand_explain_openai_raw_5k_ef200": {
            "status": "PASS" if hand_match else "FAIL",
            "detail": hand_detail,
            "hand": {k: hand[k] for k in ("eval_id", "node_types", "index_names", "hnsw_used", "exec_ms")},
        },
    }

    payload = {
        "task": "W1_explain_audit",
        "port": int(port),
        "generated_at": utc_now(),
        "started_at": started,
        "elapsed_s": round(time.time() - t0, 3),
        "connected_in_s": connected_in_s,
        "postgres_version": inventory["postgres_version"],
        "pgvector_version": inventory["pgvector_version"],
        "settings": inventory["settings"],
        "indexes": inventory["indexes"],
        "hnsw_indexes": inventory["hnsw_indexes"],
        "relation_sizes": inventory["relation_sizes"],
        "iterative_scan_probe": guc0,
        "sample40_eval_ids": [q["eval_id"] for q in q40],
        "sample40_seed": SAMPLE_SEED,
        "query_sql_template": build_sql("<table>", "meta"),
        "loadavg_start": load_start,
        "loadavg_end": load_end,
        "cells": cells,
        "anomalies": anomalies(cells),
        "acceptance": acceptance,
        "cells_run_this_process": n_run,
        "scratch": str(scratch),
    }
    write_json_atomic(out_path, payload)
    md_path.write_text(render_md(payload), encoding="utf-8")
    cur.close()
    conn.close()
    print(f"wrote {out_path} and {md_path}", flush=True)
    print("acceptance", json.dumps(acceptance, indent=2), flush=True)
    return payload


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--port", type=int, default=5433)
    p.add_argument(
        "--out",
        type=Path,
        default=None,
        help="JSON output path (markdown written next to it with .md)",
    )
    return p.parse_args()


def main() -> int:
    args = parse_args()
    out = args.out
    if out is None:
        out = REV1 / f"plan_audit_{args.port}.json"
    run_audit(int(args.port), out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
