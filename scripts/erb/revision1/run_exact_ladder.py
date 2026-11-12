#!/usr/bin/env python3
"""Exact cosine scale-ladder evaluation (revision 1): full per-query retrieval lists.

Disables index/bitmap scans so Postgres orders by exact cosine distance over the
filtered corpus at each scale point.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import struct
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))
from harness_lib import provenance_entries, run_invariants, sha256_text  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / "data"
PUB = ROOT / "artifacts" / "published"
REV1 = PUB / "revision1"
MANIFEST_PATH = DATA / "erb_scale_manifest.json"
OPENAI_CACHE = DATA / "erb_query_embed_cache.json"
OPENAI_CACHE_REV1 = DATA / "erb_query_embed_cache_rev1.json"
TITAN_CACHE = DATA / "erb_titan_query_embed_cache.json"
PROVENANCE_DEFAULT = REV1 / "query_vector_provenance_openai.json"

DEFAULT_SCALES = (5000, 10000, 15000, 20000, 25000, 40000, 50000, 75000, 100000)
DEFAULT_CONDITIONS = ("raw", "meta_first", "meta_in", "meta_gold")
PLAN_CHECK_SCALES = (5000, 50000, 100000)
TOP_K = 10
METRICS = ("hit_at_1", "hit_at_5", "hit_at_10", "mrr", "document_recall")
QUERY_VECTOR_KEY_RULE = (
    "eval_id only; bare question ids are never used because they collide across question types"
)
FILTER_FROM_COND = {"meta_first": "first", "meta_in": "in", "meta_gold": "gold"}
_PLAN_SCAN_KIND = (
    r"Parallel Index Scan"
    r"|Index Scan Backward"
    r"|Index Only Scan"
    r"|Index Scan"
    r"|Bitmap Index Scan"
    r"|Bitmap Heap Scan"
    r"|Seq Scan"
    r"|Tid Scan"
    r"|Subquery Scan"
)
SCAN_LINE_RE = re.compile(
    rf"(?:->\s+)?(?P<kind>{_PLAN_SCAN_KIND})"
    r"(?:\s+using\s+(?P<idx_using>[^\s(]+))?"
    r"(?:\s+on\s+(?P<on_name>[^\s(]+))?"
)
INDEX_NAME_SCAN_KINDS = frozenset(
    {
        "Index Scan",
        "Index Scan Backward",
        "Index Only Scan",
        "Bitmap Index Scan",
        "Parallel Index Scan",
    }
)

BANK_FILES = {
    "primary200": PUB / "primary_questions_200.json",
    "primary400": PUB / "primary_questions_400.json",
}

EMBEDDER_CONFIG = {
    "openai": {
        "table": "document_chunks",
        "cache_path": OPENAI_CACHE,
        "cache_style": "flat",
    },
    "titan": {
        "table": "document_chunks_titan",
        "cache_path": TITAN_CACHE,
        "cache_style": "titan_vectors",
    },
}


def vector_literal(vec: list[float]) -> str:
    return "[" + ",".join(str(v) for v in vec) + "]"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_vector(vec: list[float]) -> str:
    """SHA-256 of float32 little-endian components (matches provenance artifacts)."""
    return hashlib.sha256(struct.pack(f"{len(vec)}f", *vec)).hexdigest()


def resolve_cache_path(embedder: str, bank: str, explicit: Path | None) -> Path:
    if explicit is not None:
        return explicit
    if embedder == "openai" and bank == "primary400":
        return OPENAI_CACHE_REV1
    return EMBEDDER_CONFIG[embedder]["cache_path"]


def pg_connect():
    import psycopg2

    return psycopg2.connect(
        host=os.environ.get("PGHOST", "localhost"),
        port=os.environ.get("PGPORT", "5432"),
        user=os.environ["PGUSER"],
        password=os.environ["PGPASSWORD"],
        dbname=os.environ["PGDATABASE"],
    )


def load_manifest() -> dict:
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def build_doc_source_map(manifest: dict) -> dict[str, str]:
    out: dict[str, str] = {}
    for doc in manifest.get("documents") or []:
        did = str(doc.get("doc_id") or "")
        if did and did not in out:
            out[did] = str(doc.get("source_type") or "")
    return out


def load_questions(manifest: dict, bank: str) -> list[dict]:
    bank_path = BANK_FILES[bank]
    bank_data = json.loads(bank_path.read_text(encoding="utf-8"))
    eval_ids = list(bank_data["question_ids"])
    by_eval = {q["eval_id"]: q for q in manifest.get("questions") or []}
    missing = [e for e in eval_ids if e not in by_eval]
    if missing:
        raise SystemExit(f"manifest missing {len(missing)} eval_ids from {bank} (e.g. {missing[:3]})")
    return [by_eval[e] for e in eval_ids]


def load_query_cache(
    embedder: str, eval_ids: list[str], cache_path: Path
) -> tuple[dict[str, list[float]], list[str]]:
    cfg = EMBEDDER_CONFIG[embedder]
    raw = json.loads(cache_path.read_text(encoding="utf-8"))
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
    return cache, missing


def gold_source_types(question: dict, doc_source: dict[str, str]) -> list[str]:
    types: set[str] = set()
    for did in question.get("expected_doc_ids") or []:
        st = doc_source.get(str(did))
        if st:
            types.add(st)
    return sorted(types)


def condition_filter_sql(
    condition: str, question: dict, doc_source: dict[str, str]
) -> tuple[str, tuple]:
    if condition == "raw":
        return "", ()
    if condition == "meta_first":
        st = (question.get("source_types") or [None])[0]
        if not st:
            return " AND 1=0", ()
        return " AND source_type = %s", (str(st),)
    if condition == "meta_in":
        sts = [str(s) for s in (question.get("source_types") or []) if s]
        if not sts:
            return " AND 1=0", ()
        return " AND source_type = ANY(%s)", (sts,)
    if condition == "meta_gold":
        sts = gold_source_types(question, doc_source)
        if not sts:
            return " AND 1=0", ()
        return " AND source_type = ANY(%s)", (sts,)
    raise ValueError(f"unknown condition: {condition}")


def per_question_metrics(expected: set[str], retrieved: list[str], scores: list[float], top_k: int) -> dict:
    rank: int | None = None
    for i, doc_id in enumerate(retrieved[:top_k], start=1):
        if doc_id in expected:
            rank = i
            break
    hit_ids = expected & set(retrieved[:top_k])
    return {
        "rank": rank,
        "hit_at_1": rank == 1 if rank else False,
        "hit_at_5": rank is not None and rank <= 5,
        "hit_at_10": rank is not None and rank <= 10,
        "mrr": 1.0 / rank if rank else 0.0,
        "document_recall": len(hit_ids) / max(len(expected), 1),
        "retrieved_doc_ids": retrieved[:top_k],
        "scores": scores[:top_k],
    }


def aggregate_metrics(per_question: list[dict]) -> dict[str, float]:
    n = len(per_question)
    if n == 0:
        return {m: 0.0 for m in METRICS}
    return {
        m: round(sum(float(p[m]) for p in per_question) / n, 4)
        for m in METRICS
    }


def exact_search(
    cur,
    table: str,
    vec: list[float],
    scale: int,
    extra_where: str,
    extra_params: tuple,
    top_k: int,
) -> list[tuple[str, float]]:
    lit = vector_literal(vec)
    sql = f"""
        SELECT doc_id, 1 - (embedding <=> %s::vector) AS score
        FROM {table}
        WHERE embedding IS NOT NULL
          AND scale_rank IS NOT NULL
          AND scale_rank < %s
          {extra_where}
        ORDER BY embedding <=> %s::vector, doc_id
        LIMIT %s
    """
    params = (lit, scale, *extra_params, lit, top_k)
    cur.execute(sql, params)
    return [(str(r[0]), float(r[1])) for r in cur.fetchall() if r[0]]


def parse_plan_scans(plan_lines: list[str]) -> tuple[list[str], bool, str]:
    scan_node_types: list[str] = []
    innermost_scan_node_type = ""
    hnsw_index_scan = False
    for line in plan_lines:
        m = SCAN_LINE_RE.search(line)
        if not m:
            continue
        kind = m.group("kind")
        idx_using = m.group("idx_using") or ""
        on_name = m.group("on_name") or ""
        if kind in INDEX_NAME_SCAN_KINDS:
            index_name = idx_using or (on_name if kind == "Bitmap Index Scan" else "")
            if index_name:
                if idx_using:
                    label = f"{kind} using {index_name}"
                else:
                    label = f"{kind} on {index_name}"
            else:
                label = kind
        elif on_name:
            label = f"{kind} on {on_name}"
        else:
            label = kind
        scan_node_types.append(label)
        innermost_scan_node_type = label
        if kind in INDEX_NAME_SCAN_KINDS:
            index_name = idx_using or (on_name if kind == "Bitmap Index Scan" else "")
            if index_name and "hnsw" in index_name.lower():
                hnsw_index_scan = True
    return scan_node_types, hnsw_index_scan, innermost_scan_node_type


def first_multi_source_question(questions: list[dict]) -> dict | None:
    for q in questions:
        if len(q.get("source_types") or []) > 1:
            return q
    return None


def plan_probe_questions(
    questions: list[dict],
    qvecs: dict[str, list[float]] | None = None,
) -> list[dict]:
    pool = [q for q in questions if qvecs is None or q.get("eval_id") in qvecs]
    if not pool:
        return []
    probes: list[dict] = [pool[0]]
    multi = first_multi_source_question(pool)
    if multi and multi["eval_id"] != probes[0]["eval_id"]:
        probes.append(multi)
    return probes


def session_pg_versions(cur) -> tuple[str, str | None]:
    cur.execute("SELECT version()")
    pg_version = cur.fetchone()[0]
    cur.execute("SELECT extversion FROM pg_extension WHERE extname = 'vector'")
    row = cur.fetchone()
    pgvector_version = row[0] if row else None
    return pg_version, pgvector_version


def apply_seqscan_session(cur) -> None:
    cur.execute("SET enable_indexscan = off")
    cur.execute("SET enable_bitmapscan = off")


def plan_probe_errors(checks: list[dict], qvecs: dict[str, list[float]]) -> list[str]:
    errors: list[str] = []
    executed = [c for c in checks if not c.get("skipped")]
    cached_skipped = [
        c for c in checks if c.get("skipped") and c.get("eval_id") in qvecs
    ]
    if checks and not executed:
        if cached_skipped or any(c.get("eval_id") in qvecs for c in checks):
            errors.append("all plan probes skipped")
        # else: probes have no cached vectors (skipped-bank path); do not abort
    for c in cached_skipped:
        errors.append(f"plan probe {c['eval_id']} skipped but query vector exists")
    return errors


def run_plan_checks(
    cur,
    table: str,
    conditions: list[str],
    probe_questions: list[dict],
    qvecs: dict[str, list[float]],
    doc_source: dict,
    scales: tuple[int, ...] = PLAN_CHECK_SCALES,
) -> list[dict]:
    checks: list[dict] = []
    for question in probe_questions:
        eid = question["eval_id"]
        vec = qvecs.get(eid)
        if vec is None:
            checks.append(
                {
                    "table": table,
                    "eval_id": eid,
                    "skipped": True,
                    "skip_reason": "missing_query_vector",
                }
            )
            continue
        for scale in scales:
            for cond in conditions:
                extra, params = condition_filter_sql(cond, question, doc_source)
                lit = vector_literal(vec)
                sql = f"""
                    EXPLAIN
                    SELECT doc_id, 1 - (embedding <=> %s::vector) AS score
                    FROM {table}
                    WHERE embedding IS NOT NULL
                      AND scale_rank IS NOT NULL
                      AND scale_rank < %s
                      {extra}
                    ORDER BY embedding <=> %s::vector, doc_id
                    LIMIT %s
                """
                cur.execute(sql, (lit, scale, *params, lit, TOP_K))
                plan_lines = [r[0] for r in cur.fetchall()]
                scan_node_types, hnsw_index_scan, innermost = parse_plan_scans(plan_lines)
                checks.append(
                    {
                        "table": table,
                        "condition": cond,
                        "scale": scale,
                        "eval_id": eid,
                        "innermost_scan_node_type": innermost,
                        "scan_node_types": scan_node_types,
                        "hnsw_index_scan": hnsw_index_scan,
                        "plan": plan_lines,
                    }
                )
    return checks


def plan_checks_failed(checks: list[dict]) -> bool:
    return any(bool(c.get("hnsw_index_scan")) for c in checks)


def missing_vectors_by_question_type(missing: list[str], by_eval: dict[str, dict]) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for eid in missing:
        q = by_eval.get(eid) or {}
        counts[str(q.get("question_type") or "unknown")] += 1
    return dict(sorted(counts.items()))


def filter_source_types(q: dict, which: str, doc_source: dict[str, str]) -> set[str]:
    if which == "first":
        st = q.get("source_types") or []
        return {str(st[0])} if st else set()
    if which == "in":
        return {str(s) for s in (q.get("source_types") or []) if s}
    gold_types: set[str] = set()
    for did in q.get("expected_doc_ids") or []:
        st = doc_source.get(str(did))
        if st is not None:
            gold_types.add(st)
    return gold_types


def index_runs(data: dict) -> dict[tuple[str, int], dict]:
    return {(r["condition"], int(r["scale"])): r for r in data.get("runs") or []}


def question_order(data: dict, by_eval: dict[str, dict]) -> list[str]:
    runs = index_runs(data)
    if not runs:
        return []
    first = next(iter(runs.values()))
    order = [p["question_id"] for p in first.get("per_question") or []]
    return order


def align_per_question(run: dict, order: list[str]) -> list[dict]:
    from harness_lib import align_pq

    return align_pq(run, order)


def verify_invariants(
    data: dict,
    doc_source: dict[str, str],
    by_eval: dict[str, dict],
) -> dict[str, int]:
    meta = data.get("meta") or {}
    emb = str(meta.get("embedder") or "unknown")
    bank = str(meta.get("bank") or "unknown")
    if not (data.get("runs") or []):
        return {"containment": 0, "order_preservation": 0, "score_monotonicity": 0}
    summary = run_invariants({(emb, bank, ""): data}, doc_source, by_eval)
    return {
        "containment": int(summary["containment"]["n_violations"]),
        "order_preservation": int(summary["nested_corpus"]["n_violations"]),
        "score_monotonicity": int(summary["score_monotonicity"]["n_violations"]),
    }


def preflight_openai_vectors(
    questions: list[dict],
    qvecs: dict[str, list[float]],
    provenance_path: Path,
) -> int:
    if not provenance_path.is_file():
        print(f"preflight FAIL: missing {provenance_path}", file=sys.stderr)
        return 3
    blob = json.loads(provenance_path.read_text(encoding="utf-8"))
    entries = {e["eval_id"]: e for e in provenance_entries(blob)}
    checked = 0
    for q in questions:
        eid = q["eval_id"]
        ent = entries.get(eid)
        if ent is None:
            print(f"preflight FAIL: no provenance entry for {eid}", file=sys.stderr)
            return 3
        want_q = sha256_text(q.get("question") or "")
        if ent.get("question_sha256") != want_q:
            print(f"preflight FAIL: {eid} question_sha256 mismatch", file=sys.stderr)
            return 3
        vec = qvecs.get(eid)
        if vec is None:
            print(f"preflight FAIL: {eid} missing query vector in cache", file=sys.stderr)
            return 3
        want_v = sha256_vector(vec)
        if ent.get("vector_sha256") != want_v:
            print(f"preflight FAIL: {eid} vector_sha256 mismatch", file=sys.stderr)
            return 3
        checked += 1
    print(f"preflight: checked {checked} query-vector provenance entries")
    return 0


def run_openai_preflight(
    embedder: str,
    bank: str,
    questions: list[dict],
    qvecs: dict[str, list[float]],
    *,
    skip_preflight: bool,
    provenance_path: Path,
) -> int:
    if embedder != "openai":
        return 0
    if skip_preflight:
        print("note: --skip-preflight ignored for openai embedder", file=sys.stderr)
    return preflight_openai_vectors(questions, qvecs, provenance_path)


def write_markdown_summary(path: Path, data: dict) -> None:
    runs = data.get("runs") or []
    if not runs:
        path.write_text("# Exact ladder\n\n(no runs — skipped)\n", encoding="utf-8")
        return
    scales = sorted({r["scale"] for r in runs})
    conditions = sorted({r["condition"] for r in runs}, key=lambda c: DEFAULT_CONDITIONS.index(c) if c in DEFAULT_CONDITIONS else 99)
    idx = {(r["condition"], r["scale"]): r for r in runs}
    lines = [
        f"# Exact ladder Hit@10 ({data['meta']['embedder']}, {data['meta']['bank']})",
        "",
        "| scale | " + " | ".join(conditions) + " |",
        "|------:|" + "|".join(["---:"] * len(conditions)) + "|",
    ]
    for sc in scales:
        cells = []
        for cond in conditions:
            run = idx.get((cond, sc))
            cells.append(f"{run['metrics']['hit_at_10']:.3f}" if run else "—")
        lines.append(f"| {sc} | " + " | ".join(cells) + " |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_ladder(args: argparse.Namespace) -> int:
    embedder = args.embedder
    bank = args.bank
    cfg = EMBEDDER_CONFIG[embedder]
    out_path = args.out or (REV1 / f"exact_ladder_{embedder}_{bank}.json")
    md_path = out_path.with_suffix(".md")
    cache_path = resolve_cache_path(embedder, bank, args.cache)

    manifest = load_manifest()
    doc_source = build_doc_source_map(manifest)
    questions = load_questions(manifest, bank)
    eval_ids = [q["eval_id"] for q in questions]
    qvecs, missing = load_query_cache(embedder, eval_ids, cache_path)

    pf = run_openai_preflight(
        embedder,
        bank,
        questions,
        qvecs,
        skip_preflight=args.skip_preflight,
        provenance_path=args.provenance,
    )
    if pf != 0:
        return pf

    scales = [int(x) for x in args.scales.split(",") if x.strip()]
    conditions = [c.strip() for c in args.conditions.split(",") if c.strip()]

    created_at = datetime.now(timezone.utc).isoformat()
    session_settings = {
        "enable_indexscan": "off",
        "enable_bitmapscan": "off",
    }

    by_eval = {q["eval_id"]: q for q in manifest.get("questions") or []}
    queries_meta = {
        "query_vector_key_rule": QUERY_VECTOR_KEY_RULE,
        "missing_query_vectors_by_question_type": missing_vectors_by_question_type(missing, by_eval),
    }

    conn = pg_connect()
    conn.autocommit = True
    cur = conn.cursor()
    apply_seqscan_session(cur)
    pg_version, pgvector_version = session_pg_versions(cur)
    probes = plan_probe_questions(questions, qvecs)
    plan_checks = run_plan_checks(cur, cfg["table"], conditions, probes, qvecs, doc_source)
    probe_errs = plan_probe_errors(plan_checks, qvecs)
    if probe_errs:
        for e in probe_errs:
            print(f"FAIL: {e}", file=sys.stderr)
        cur.close()
        conn.close()
        return 1

    if missing:
        payload = {
            "meta": {
                "created_at": created_at,
                "embedder": embedder,
                "bank": bank,
                "search_mode": "exact",
                "skipped": True,
                "skip_reason": "missing_query_vectors",
                "missing_query_vectors": len(missing),
                "missing_query_vector_ids_sample": missing[:10],
                **queries_meta,
                "session_settings": session_settings,
                "postgresql_version": pg_version,
                "pgvector_version": pgvector_version,
                "plan_check": plan_checks,
                "top_k": TOP_K,
                "manifest_sha256": sha256_file(MANIFEST_PATH),
                "query_cache_path": str(cache_path.relative_to(ROOT)),
                "query_cache_sha256": sha256_file(cache_path),
            },
            "runs": [],
        }
        cur.close()
        conn.close()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        write_markdown_summary(md_path, payload)
        print(f"skipped {embedder}/{bank}: {len(missing)} missing vectors -> {out_path}")
        if plan_checks_failed(plan_checks):
            print("FAIL: plan check reports HNSW index scan", file=sys.stderr)
            return 1
        return 0

    runs: list[dict] = []
    for cond in conditions:
        for scale in scales:
            t0 = time.time()
            per_q: list[dict] = []
            for q in questions:
                eid = q["eval_id"]
                expected = {str(x) for x in (q.get("expected_doc_ids") or []) if x}
                if not expected:
                    continue
                extra, params = condition_filter_sql(cond, q, doc_source)
                rows = exact_search(cur, cfg["table"], qvecs[eid], scale, extra, params, TOP_K)
                retrieved = [d for d, _ in rows]
                scores = [s for _, s in rows]
                m = per_question_metrics(expected, retrieved, scores, TOP_K)
                per_q.append({"question_id": eid, **m})
            elapsed = round(time.time() - t0, 3)
            metrics = aggregate_metrics(per_q)
            runs.append(
                {
                    "condition": cond,
                    "scale": scale,
                    "n_questions": len(per_q),
                    "elapsed_s": elapsed,
                    "metrics": metrics,
                    "per_question": per_q,
                }
            )
            print(
                f"{embedder} {bank} {cond} N={scale} Hit@10={metrics['hit_at_10']:.4f} ({elapsed}s)",
                flush=True,
            )

    cur.close()
    conn.close()

    payload = {
        "meta": {
            "created_at": created_at,
            "embedder": embedder,
            "bank": bank,
            "search_mode": "exact",
            "session_settings": session_settings,
            "postgresql_version": pg_version,
            "pgvector_version": pgvector_version,
            "query_vector_key_rule": QUERY_VECTOR_KEY_RULE,
            "top_k": TOP_K,
            "scales": scales,
            "conditions": conditions,
            "table": cfg["table"],
            "manifest_sha256": sha256_file(MANIFEST_PATH),
            "query_cache_path": str(cache_path.relative_to(ROOT)),
            "query_cache_sha256": sha256_file(cache_path),
            "plan_check": plan_checks,
        },
        "runs": runs,
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    write_markdown_summary(md_path, payload)
    print(f"wrote {out_path}")
    print(f"wrote {md_path}")
    if plan_checks_failed(plan_checks):
        print("FAIL: plan check reports HNSW index scan", file=sys.stderr)
        return 1
    return 0


def verify_skipped_meta(meta: dict) -> list[str]:
    errors: list[str] = []
    if not meta.get("skipped"):
        errors.append("skipped meta missing skipped=true")
    if not meta.get("skip_reason"):
        errors.append("skipped meta missing skip_reason")
    for key in ("postgresql_version", "pgvector_version", "session_settings", "plan_check"):
        if key not in meta:
            errors.append(f"skipped meta missing {key}")
    if meta.get("plan_check") is not None and plan_checks_failed(meta.get("plan_check") or []):
        errors.append("skipped file plan_check reports HNSW index scan")
    return errors


def verify_file(path: Path, manifest: dict | None = None, *, tol: float = 1e-9) -> tuple[list[str], dict[str, int]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    meta = data.get("meta") or {}
    if manifest is None:
        manifest = load_manifest()
    by_eval = {q["eval_id"]: q for q in manifest.get("questions") or []}
    doc_source = build_doc_source_map(manifest)
    errors: list[str] = []
    invariant_counts = {"containment": 0, "order_preservation": 0, "score_monotonicity": 0}

    if meta.get("skipped"):
        errors.extend(verify_skipped_meta(meta))
        return errors, invariant_counts

    if meta.get("plan_check") is not None and plan_checks_failed(meta.get("plan_check") or []):
        errors.append("plan_check reports HNSW index scan")

    for run in data.get("runs") or []:
        per_q_rebuilt: list[dict] = []
        for p in run.get("per_question") or []:
            qid = p["question_id"]
            q = by_eval.get(qid)
            if not q:
                errors.append(f"missing manifest question {qid}")
                continue
            expected = {str(x) for x in (q.get("expected_doc_ids") or []) if x}
            scores = p.get("scores") or [0.0] * len(p.get("retrieved_doc_ids") or [])
            rebuilt = per_question_metrics(
                expected, list(p.get("retrieved_doc_ids") or []), scores, TOP_K
            )
            per_q_rebuilt.append(rebuilt)
            for key in ("rank", "hit_at_1", "hit_at_5", "hit_at_10", "mrr", "document_recall"):
                if key in ("hit_at_1", "hit_at_5", "hit_at_10"):
                    if bool(p.get(key)) != bool(rebuilt[key]):
                        errors.append(f"{qid} {run['condition']} N={run['scale']}: {key} mismatch")
                elif key == "rank":
                    if p.get(key) != rebuilt[key]:
                        errors.append(f"{qid} {run['condition']} N={run['scale']}: rank mismatch")
                elif abs(float(p.get(key) or 0) - float(rebuilt[key])) > tol:
                    errors.append(f"{qid} {run['condition']} N={run['scale']}: {key} mismatch")
        recomputed = aggregate_metrics(per_q_rebuilt)
        for m in METRICS:
            stored = float(run["metrics"][m])
            calc = recomputed[m]
            if abs(stored - calc) > tol:
                errors.append(
                    f"{path.name} {run['condition']} scale={run['scale']} {m}: stored={stored} recomputed={calc}"
                )

    invariant_counts = verify_invariants(data, doc_source, by_eval)
    for kind, n in invariant_counts.items():
        if n:
            errors.append(f"invariant {kind}: {n} violation(s)")
    return errors, invariant_counts


def _plan_sample(line: str, expect_hnsw: bool) -> None:
    _, hnsw, _ = parse_plan_scans([line])
    assert hnsw is expect_hnsw, f"line={line!r} expected hnsw={expect_hnsw} got {hnsw}"


def run_unit_tests() -> int:
    print("unit: parse_plan_scans")
    _plan_sample("  ->  Index Scan using document_chunks_embedding_hnsw_idx on document_chunks", True)
    _plan_sample("  ->  Index Scan Backward using document_chunks_embedding_hnsw_idx on document_chunks", True)
    _plan_sample("  ->  Index Only Scan using idx_foo_hnsw_bar on t", True)
    _plan_sample("  ->  Bitmap Index Scan on document_chunks_embedding_hnsw_idx", True)
    _plan_sample("  ->  Parallel Index Scan using document_chunks_embedding_hnsw_idx on document_chunks", True)
    _plan_sample("  ->  Seq Scan on document_chunks", False)
    _plan_sample("  ->  Bitmap Heap Scan on document_chunks", False)
    _plan_sample("  ->  Index Scan using document_chunks_scale_rank_idx on document_chunks", False)
    print("  PASS plan parser (8 cases)")

    print("unit: meta containment reverse direction")
    data = {
        "meta": {"scales": [5000], "conditions": ["raw", "meta_in"]},
        "runs": [
            {
                "condition": "raw",
                "scale": 5000,
                "per_question": [
                    {"question_id": "q1", "retrieved_doc_ids": ["d1", "d2"], "scores": [0.9, 0.8]}
                ],
            },
            {
                "condition": "meta_in",
                "scale": 5000,
                "per_question": [
                    {"question_id": "q1", "retrieved_doc_ids": ["d1", "bad"], "scores": [0.9, 0.8]}
                ],
            },
        ],
    }
    by_eval = {
        "q1": {"eval_id": "q1", "source_types": ["confluence"], "expected_doc_ids": ["g1"]},
    }
    doc_source = {"d1": "confluence", "d2": "jira", "bad": "slack", "g1": "confluence"}
    counts = verify_invariants(data, doc_source, by_eval)
    assert counts["containment"] >= 1, counts
    print("  PASS containment counts violations for disallowed meta doc")

    print("unit: sha256_vector round-trip vs provenance sample")
    cache = json.loads(OPENAI_CACHE_REV1.read_text(encoding="utf-8"))
    prov = json.loads(PROVENANCE_DEFAULT.read_text(encoding="utf-8"))
    eid = prov["entries"][0]["eval_id"]
    assert sha256_vector(cache[eid]) == prov["entries"][0]["vector_sha256"]
    print("  PASS vector_sha256 definition")

    print("ALL unit tests PASS")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--embedder", choices=("openai", "titan"))
    parser.add_argument("--bank", choices=("primary200", "primary400"))
    parser.add_argument("--scales", default=",".join(str(s) for s in DEFAULT_SCALES))
    parser.add_argument("--conditions", default=",".join(DEFAULT_CONDITIONS))
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument("--cache", type=Path, default=None, help="Query embedding cache JSON")
    parser.add_argument(
        "--provenance",
        type=Path,
        default=PROVENANCE_DEFAULT,
        help=argparse.SUPPRESS,
    )
    parser.add_argument(
        "--skip-preflight",
        action="store_true",
        help="No-op for Titan only; OpenAI always preflights",
    )
    parser.add_argument("--unit-test", action="store_true", help="Run built-in unit tests")
    parser.add_argument("--verify", action="store_true", help="Verify metrics in --out file(s)")
    args = parser.parse_args()

    if args.unit_test:
        return run_unit_tests()

    if args.verify:
        paths = [args.out] if args.out else sorted(REV1.glob("exact_ladder_*.json"))
        if not paths:
            print("no files to verify", file=sys.stderr)
            return 1
        failed = False
        totals = {"containment": 0, "order_preservation": 0, "score_monotonicity": 0}
        for p in paths:
            errs, inv = verify_file(p)
            for k in totals:
                totals[k] += inv[k]
            if errs:
                failed = True
                print(f"FAIL {p}: {len(errs)} error(s)")
                for e in errs[:20]:
                    print(f"  {e}")
            else:
                print(f"PASS {p}")
            print(
                f"  invariants: containment={inv['containment']} "
                f"order_preservation={inv['order_preservation']} "
                f"score_monotonicity={inv['score_monotonicity']}"
            )
        print(
            f"verify invariant totals: containment={totals['containment']} "
            f"order_preservation={totals['order_preservation']} "
            f"score_monotonicity={totals['score_monotonicity']}"
        )
        return 1 if failed else 0

    if not args.embedder or not args.bank:
        parser.error("--embedder and --bank required unless --verify")
    return run_ladder(args)


if __name__ == "__main__":
    raise SystemExit(main())
