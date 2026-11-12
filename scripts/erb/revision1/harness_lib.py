#!/usr/bin/env python3
"""Shared revision-1 validation helpers (stdlib only). Do not import analyze_exact."""

from __future__ import annotations

import ast
import hashlib
import json
import math
import random
import re
import struct
from dataclasses import dataclass, field
from itertools import combinations
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / "data"
PUB = ROOT / "artifacts" / "published"
REV1 = PUB / "revision1"
MANIFEST_PATH = DATA / "erb_scale_manifest.json"
COMPACT_MANIFEST_PATH = REV1 / "scale_manifest_compact.json"
CLAIMS_PATH = Path(__file__).resolve().parent / "claims.json"
OLD_OPENAI_SWEEP = PUB / "erb_full_primary200_to100k.json"
ARTIFACT_MANIFEST_PATH = REV1 / "ARTIFACT_MANIFEST.json"
PAPER_TEX_PATH = ROOT / "papers" / "ieee-vector-drift" / "access" / "main.tex"
MANAGER_TEX_PATH = DATA / "main_current.tex"
DEFAULT_TEX_PATH = PAPER_TEX_PATH
QUERY_CACHE_REV1 = DATA / "erb_query_embed_cache_rev1.json"
SHARED_SCORE_EPS = 1e-9
COSINE_PASS = 0.99
COSINE_INFO_BAND = 0.999


def resolve_default_tex() -> Path:
    """Prefer the Access manuscript if it is the Exact-Search Ladder revision."""
    if PAPER_TEX_PATH.is_file():
        try:
            if "Exact-Search Ladder" in PAPER_TEX_PATH.read_text(encoding="utf-8"):
                return PAPER_TEX_PATH
        except OSError:
            pass
    return MANAGER_TEX_PATH
LADDER_NAME_RE = re.compile(
    r"^exact_ladder_(?:(?P<variant>uniform_s42|uniform_s0|rr_s0|"
    r"pool_prop_s42|pool_prop_s0|pool_rr_full)_)?"
    r"(?P<embedder>openai|titan)_(?P<bank>primary\d+)$"
)
EXPECTED_EXACT_LADDERS = (
    "exact_ladder_openai_primary200.json",
    "exact_ladder_openai_primary400.json",
    "exact_ladder_titan_primary200.json",
    "exact_ladder_titan_primary400.json",
    "exact_ladder_uniform_s42_openai_primary200.json",
    "exact_ladder_uniform_s42_titan_primary200.json",
    "exact_ladder_uniform_s0_openai_primary200.json",
    "exact_ladder_uniform_s0_titan_primary200.json",
    "exact_ladder_rr_s0_openai_primary200.json",
    "exact_ladder_rr_s0_titan_primary200.json",
)
EXPECTED_POOL_LADDERS = (
    "exact_ladder_pool_prop_s42_openai_primary200.json",
    "exact_ladder_pool_prop_s0_openai_primary200.json",
    "exact_ladder_pool_rr_full_openai_primary200.json",
)
POOL_RR_FULL_RAW_HIT10 = {5000: 0.795, 100000: 0.585}
POOL_ANALYSIS_KEYS = ("prop_s42", "prop_s0", "rr_full")
DISPLACEMENT_CATEGORIES = (
    "displacer",
    "competitor5k",
    "gold_control",
    "random_control",
)
DISPLACEMENT_TEXT_KEYS = {
    "chunk_text",
    "document_text",
    "retrieved_text",
    "title",
    "question",
    "body",
    "path",
}
EXPECTED_PER_N_EVAL = (
    "per_n_hnsw_eval_openai.json",
    "per_n_hnsw_eval_titan.json",
)
EXPECTED_HNSW_RECALL = (
    "hnsw_recall_by_cell_5433.json",
    "hnsw_recall_by_cell_5434.json",
)

SCORE_EPS = 1e-12
META_FILTERS = ("first", "in", "gold")
FILTER_FROM_COND = {
    "meta_first": "first",
    "meta_in": "in",
    "meta_gold": "gold",
    "meta": "first",
}
BANK_N = {"primary200": 200, "primary400": 400}
HNSW_LABELS = {"hnsw", "approximate", "approx", "ann"}
EXACT_LABELS = {"exact", "seq", "sequential"}
BARE_QID_RE = re.compile(r"erb_question_id")
CACHE_LOOKUP_RE = re.compile(
    r"""(?:cache|raw|vecs|vectors|embeddings|qvecs)\s*(?:\[|\.get\()\s*(?:[^\n]{0,40}erb_question_id)"""
)


@dataclass
class CheckResult:
    name: str
    status: str
    n_pass: int = 0
    n_fail: int = 0
    n_skip: int = 0
    n_warn: int = 0
    n_unverified: int = 0
    messages: list[str] = field(default_factory=list)

    def add(self, status: str, msg: str) -> None:
        self.messages.append(f"{status}: {msg}")
        if status == "PASS":
            self.n_pass += 1
        elif status == "FAIL":
            self.n_fail += 1
        elif status == "SKIP":
            self.n_skip += 1
        elif status == "WARN":
            self.n_warn += 1
        elif status == "UNVERIFIED":
            self.n_unverified += 1

    def finalize(self) -> "CheckResult":
        if self.n_fail:
            self.status = "FAIL"
        elif self.status == "SKIP" or (self.n_skip and not self.n_pass and not self.n_unverified):
            self.status = "SKIP"
        elif self.n_unverified and not self.n_pass:
            self.status = "UNVERIFIED"
        elif self.n_warn and not self.n_pass:
            self.status = "WARN"
        else:
            self.status = "PASS"
        return self


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_text(text: str) -> str:
    return sha256_bytes(text.encode("utf-8"))


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_vector(vec: list[float]) -> str:
    """SHA-256 of float32 little-endian components (matches run_exact_ladder preflight)."""
    return hashlib.sha256(struct.pack(f"{len(vec)}f", *vec)).hexdigest()


def cache_vector_for_eval(cache: dict[str, Any], eval_id: str) -> list[float] | None:
    v = cache.get(eval_id)
    if isinstance(v, list):
        return v
    if isinstance(v, dict) and isinstance(v.get("embedding"), list):
        return list(v["embedding"])
    vecs = cache.get("vectors")
    if isinstance(vecs, dict):
        v2 = vecs.get(eval_id)
        if isinstance(v2, list):
            return v2
    return None


def parse_ladder_name(path: Path) -> tuple[str, str, str] | None:
    """Return (embedder, bank, variant). variant is '' for the original round-robin ladder."""
    m = LADDER_NAME_RE.match(path.stem)
    if not m:
        return None
    return m.group("embedder"), m.group("bank"), m.group("variant") or ""


def is_canonical_ladder(parsed: tuple[str, str, str] | None) -> bool:
    return parsed is not None and parsed[2] == ""


def discover_ladders(rev1: Path = REV1) -> list[Path]:
    if not rev1.is_dir():
        return []
    return sorted(rev1.glob("exact_ladder_*_*.json"))


def blob_skipped(blob: dict[str, Any]) -> bool:
    meta = blob.get("meta") or {}
    return bool(meta.get("skipped"))


def run_scale(run: dict[str, Any]) -> int:
    return int(run.get("scale", run.get("corpus_scale_size")))


def index_runs(blob: dict[str, Any]) -> dict[tuple[str, int], dict[str, Any]]:
    out: dict[tuple[str, int], dict[str, Any]] = {}
    for run in blob.get("runs") or []:
        out[(run["condition"], run_scale(run))] = run
    return out


def retrieved_ids(pq: dict[str, Any]) -> list[str]:
    return [str(d) for d in (pq.get("retrieved_doc_ids") or [])]


def retrieved_scores(pq: dict[str, Any]) -> list[Any] | None:
    if "scores" not in pq:
        return None
    return list(pq.get("scores") or [])


def is_nan(x: Any) -> bool:
    try:
        return math.isnan(float(x))
    except (TypeError, ValueError):
        return False


def resolve_scale_manifest(preferred: Path | None = None) -> Path | None:
    """Full manifest if present, else committed compact rows (clean-clone fallback).

    An explicit missing path other than MANIFEST_PATH does not fall back (tests).
    """
    if preferred is not None:
        if preferred.is_file():
            return preferred
        try:
            if preferred.resolve() != MANIFEST_PATH.resolve():
                return None
        except OSError:
            return None
    if MANIFEST_PATH.is_file():
        return MANIFEST_PATH
    if COMPACT_MANIFEST_PATH.is_file():
        return COMPACT_MANIFEST_PATH
    return None


def iter_manifest_documents(man: dict[str, Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for d in man.get("documents") or []:
        if isinstance(d, (list, tuple)):
            if len(d) < 3:
                continue
            out.append(
                {
                    "doc_id": d[0],
                    "source_type": d[1],
                    "scale_rank": d[2],
                    "is_gold_anchor": bool(d[3]) if len(d) > 3 else False,
                }
            )
        elif isinstance(d, dict):
            out.append(d)
    return out


def load_manifest(path: Path = MANIFEST_PATH) -> tuple[dict[str, str], dict[str, dict[str, Any]]]:
    man = load_json(path)
    doc_source: dict[str, str] = {}
    for d in iter_manifest_documents(man):
        did = d.get("doc_id")
        st = d.get("source_type")
        if did and did not in doc_source and st is not None:
            doc_source[did] = st
    questions: dict[str, dict[str, Any]] = {}
    for q in man.get("questions") or []:
        qid = q.get("eval_id") or q.get("question_id")
        questions[qid] = q
        if q.get("question_id") and q["question_id"] != qid:
            questions[q["question_id"]] = q
    return doc_source, questions


def filter_source_types(q: dict[str, Any], which: str, doc_source: dict[str, str]) -> set[str]:
    if which == "first":
        st = q.get("source_types") or []
        return {st[0]} if st else set()
    if which == "in":
        return set(q.get("source_types") or [])
    gold_types = set()
    for did in q.get("expected_doc_ids") or []:
        st = doc_source.get(did)
        if st is not None:
            gold_types.add(st)
    return gold_types


def containment_reason(
    raw_ids: list[str],
    meta_ids: list[str],
    allowed: set[str],
    doc_source: dict[str, str],
) -> str | None:
    if not raw_ids or not meta_ids:
        return "empty_list"
    if len(raw_ids) < 10 or len(meta_ids) < 10:
        return "truncated_list"
    if len(raw_ids) != len(set(raw_ids)) or len(meta_ids) != len(set(meta_ids)):
        return "duplicate_doc_ids"
    for doc in raw_ids:
        if doc not in doc_source:
            return "missing_from_manifest"
    for doc in meta_ids:
        if doc not in doc_source:
            return "missing_from_manifest"
        if doc_source[doc] not in allowed:
            return "meta_doc_not_in_allowed_set"
    meta_set = set(meta_ids)
    for doc in raw_ids:
        st = doc_source.get(doc)
        if st is not None and st in allowed and doc not in meta_set:
            return "raw_allowed_doc_missing_from_meta"
    return None


def nested_reason(
    ids_a: list[str],
    scores_a: list[Any] | None,
    ids_b: list[str],
    scores_b: list[Any] | None,
) -> str | None:
    if not ids_a or not ids_b:
        return "empty_list"
    if len(ids_a) < 10:
        return "truncated_list_a"
    if len(ids_b) < 10:
        return "truncated_list_b"
    if len(ids_a) != len(set(ids_a)) or len(ids_b) != len(set(ids_b)):
        return "duplicate_doc_ids"
    pos_b = {d: j for j, d in enumerate(ids_b)}
    set_b = set(ids_b)
    last = -1
    for d in ids_a:
        j = pos_b.get(d)
        if j is None:
            continue
        if j < last:
            return "relative_order"
        last = j
    for k, d in enumerate(ids_a):
        if d in set_b:
            for prev in ids_a[:k]:
                if prev not in set_b:
                    return "prefix"
    scores_ok = (
        scores_a is not None
        and scores_b is not None
        and len(scores_a) == len(ids_a) > 0
        and len(scores_b) == len(ids_b) > 0
        and not any(is_nan(s) for s in scores_a)
        and not any(is_nan(s) for s in scores_b)
    )
    if scores_ok:
        score_a_map = {d: float(s) for d, s in zip(ids_a, scores_a)}
        score_b_map = {d: float(s) for d, s in zip(ids_b, scores_b)}
        for d in set(ids_a) & set_b:
            if abs(score_a_map[d] - score_b_map[d]) > SHARED_SCORE_EPS:
                return "shared_score_mismatch"
    dropped = [d for d in ids_a if d not in set_b]
    if not dropped:
        return None
    if len(ids_b) != 10:
        return "truncated_list_b"
    if not scores_ok:
        return "unverifiable"
    score_a = {d: float(s) for d, s in zip(ids_a, scores_a)}
    min_b = min(float(s) for s in scores_b)
    for d in dropped:
        if min_b < score_a[d] - SCORE_EPS:
            return "dropped_doc_score"
    return None


def score_reason(ids: list[str], scores: list[Any] | None) -> str | None:
    if scores is None:
        return "missing_scores"
    if not ids or not scores:
        return "empty"
    if len(scores) != len(ids):
        return "length_mismatch"
    if any(is_nan(s) for s in scores):
        return "nan"
    floats = [float(s) for s in scores]
    for i in range(len(floats) - 1):
        if floats[i + 1] > floats[i]:
            return "increasing"
        if floats[i + 1] == floats[i] and not (ids[i] < ids[i + 1]):
            return "tie_not_ascending"
    return None


def empty_kind() -> dict[str, Any]:
    return {
        "n_checked": 0,
        "n_violations": 0,
        "n_unverifiable": 0,
        "by_key": {},
        "examples": [],
        "pass": True,
    }


def _note(
    summary: dict[str, Any],
    kind: str,
    key: str,
    example: dict[str, Any],
    *,
    violated: bool = False,
    unverifiable: bool = False,
) -> None:
    bucket = summary[kind]
    rec = bucket["by_key"].setdefault(
        key, {"n_checked": 0, "n_violations": 0, "n_unverifiable": 0}
    )
    rec["n_checked"] += 1
    bucket["n_checked"] += 1
    if unverifiable:
        rec["n_unverifiable"] += 1
        bucket["n_unverifiable"] += 1
        if len(bucket["examples"]) < 8:
            bucket["examples"].append(example)
        return
    if violated:
        rec["n_violations"] += 1
        bucket["n_violations"] += 1
        if len(bucket["examples"]) < 8:
            bucket["examples"].append(example)


def qid_order(run: dict[str, Any]) -> list[str]:
    return sorted(str(p["question_id"]) for p in run.get("per_question") or [])


def assert_qid_set(run: dict[str, Any], order: list[str], *, label: str = "") -> None:
    got = {str(p["question_id"]) for p in run.get("per_question") or []}
    want = set(order)
    if got != want:
        missing = sorted(want - got)[:8]
        extra = sorted(got - want)[:8]
        prefix = f"{label}: " if label else ""
        raise ValueError(f"{prefix}question_id set mismatch missing={missing} extra={extra}")


def align_pq(run: dict[str, Any], order: list[str]) -> list[dict[str, Any]]:
    by_id = {str(p["question_id"]): p for p in run.get("per_question") or []}
    assert_qid_set(run, order)
    return [by_id[q] for q in order]


def run_invariants(
    ladders: dict[tuple[str, ...], dict[str, Any]],
    doc_source: dict[str, str],
    questions: dict[str, dict[str, Any]],
    cond_filter_map: dict[str, str] | None = None,
) -> dict[str, Any]:
    summary: dict[str, Any] = {
        "containment": empty_kind(),
        "nested_corpus": empty_kind(),
        "score_monotonicity": empty_kind(),
    }
    fmap = cond_filter_map if cond_filter_map is not None else FILTER_FROM_COND
    for key, blob in sorted(ladders.items()):
        emb, bank = key[0], key[1]
        runs = index_runs(blob)
        if not runs:
            continue
        meta = blob.get("meta") or {}
        scales = sorted({k[1] for k in runs})
        conditions = list(meta.get("conditions") or sorted({k[0] for k in runs}))
        first_run = next(iter(runs.values()))
        order = qid_order(first_run)
        pq_index = {}
        for cond in conditions:
            for s in scales:
                run = runs[(cond, s)]
                assert_qid_set(run, order, label=f"{emb}|{bank}|{cond}|{s}")
                pq_index[(cond, s)] = align_pq(run, order)

        filt_cache: dict[tuple[str, str], set[str]] = {}
        for qid in order:
            q = questions[qid]
            for filt in META_FILTERS:
                filt_cache[(qid, filt)] = filter_source_types(q, filt, doc_source)

        for cond in conditions:
            if cond == "raw":
                for s in scales:
                    key = f"{emb}|{bank}|{cond}|{s}"
                    raw_pq = pq_index[("raw", s)]
                    for i, qid in enumerate(order):
                        ids = retrieved_ids(raw_pq[i])
                        reason = None
                        if not ids:
                            reason = "empty_list"
                        elif len(ids) != len(set(ids)):
                            reason = "duplicate_doc_ids"
                        else:
                            for doc in ids:
                                if doc not in doc_source:
                                    reason = "missing_from_manifest"
                                    break
                        _note(
                            summary,
                            "containment",
                            key,
                            {"embedder": emb, "condition": cond, "scale": s, "question": qid, "reason": reason},
                            violated=reason is not None,
                        )
                continue
            filt = fmap.get(cond)
            if filt is None:
                continue
            for s in scales:
                raw_pq = pq_index[("raw", s)]
                meta_pq = pq_index[(cond, s)]
                key = f"{emb}|{bank}|{cond}|{s}"
                for i, qid in enumerate(order):
                    reason = containment_reason(
                        retrieved_ids(raw_pq[i]),
                        retrieved_ids(meta_pq[i]),
                        filt_cache[(qid, filt)],
                        doc_source,
                    )
                    _note(
                        summary,
                        "containment",
                        key,
                        {"embedder": emb, "condition": cond, "scale": s, "question": qid, "reason": reason},
                        violated=reason is not None,
                    )

        for cond in conditions:
            for s_a, s_b in combinations(scales, 2):
                pq_a = pq_index[(cond, s_a)]
                pq_b = pq_index[(cond, s_b)]
                key = f"{emb}|{bank}|{cond}|{s_a}-{s_b}"
                for i, qid in enumerate(order):
                    reason = nested_reason(
                        retrieved_ids(pq_a[i]),
                        retrieved_scores(pq_a[i]),
                        retrieved_ids(pq_b[i]),
                        retrieved_scores(pq_b[i]),
                    )
                    _note(
                        summary,
                        "nested_corpus",
                        key,
                        {
                            "embedder": emb,
                            "condition": cond,
                            "scale": f"{s_a}-{s_b}",
                            "question": qid,
                            "reason": reason,
                        },
                        violated=reason is not None and reason != "unverifiable",
                        unverifiable=reason == "unverifiable",
                    )

        for cond in conditions:
            for s in scales:
                key = f"{emb}|{bank}|{cond}|{s}"
                for i, qid in enumerate(order):
                    ids = retrieved_ids(pq_index[(cond, s)][i])
                    scores = retrieved_scores(pq_index[(cond, s)][i])
                    reason = score_reason(ids, scores)
                    _note(
                        summary,
                        "score_monotonicity",
                        key,
                        {"embedder": emb, "condition": cond, "scale": s, "question": qid, "reason": reason},
                        violated=reason is not None,
                    )

    for kind in summary:
        summary[kind]["pass"] = (
            summary[kind]["n_violations"] == 0 and summary[kind]["n_unverifiable"] == 0
        )
    return summary


def claimed_search_mode(blob: dict[str, Any]) -> str | None:
    meta = blob.get("meta") or {}
    mode = meta.get("search_mode") or blob.get("search_mode")
    if mode:
        return str(mode).lower()
    return None


def plan_entry_hnsw(entry: dict[str, Any]) -> bool:
    if entry.get("hnsw_index_scan") is True:
        return True
    if float(entry.get("frac_hnsw") or 0.0) > 0.0:
        return True
    nodes = " ".join(str(x) for x in (entry.get("scan_node_types") or []))
    innermost = str(entry.get("innermost_scan_node_type") or "")
    blob = nodes + " " + innermost + " " + " ".join(str(x) for x in (entry.get("node_types") or []))
    return "hnsw" in blob.lower()


def exact_plan_ok(plan_check: list[Any] | None) -> tuple[bool, str]:
    if plan_check is None:
        return False, "missing_plan_check"
    if not isinstance(plan_check, list) or not plan_check:
        return False, "empty_plan_check"
    executed = [e for e in plan_check if isinstance(e, dict) and not e.get("skipped")]
    if not executed:
        return False, "no_executed_plan_check"
    n_hnsw = sum(1 for e in executed if plan_entry_hnsw(e))
    if n_hnsw:
        return False, f"hnsw_index_scans={n_hnsw}"
    return True, "zero_hnsw"


def hnsw_frac(cell: dict[str, Any]) -> float | None:
    if "frac_hnsw" in cell and cell["frac_hnsw"] is not None:
        return float(cell["frac_hnsw"])
    n = int(cell.get("n_plans") or 0)
    n_h = cell.get("n_hnsw")
    if n and n_h is not None:
        return float(n_h) / float(n)
    queries = cell.get("queries") or []
    if queries:
        hits = 0
        for q in queries:
            nodes = " ".join(str(x) for x in (q.get("node_types") or q.get("node_types_unique") or []))
            if "hnsw" in nodes.lower():
                hits += 1
        return hits / len(queries)
    return None


def match_plan_cells(
    audits: list[dict[str, Any]],
    *,
    embedder: str | None,
    condition: str | None,
    scale: int | None,
    ef_search: int | None = None,
    iterative_scan: str | None = None,
) -> list[dict[str, Any]]:
    out = []
    for audit in audits:
        for cell in audit.get("cells") or []:
            if embedder and cell.get("embedder") != embedder:
                continue
            if condition and cell.get("condition") != condition:
                continue
            if scale is not None and int(cell.get("scale") or -1) != int(scale):
                continue
            if ef_search is not None and int(cell.get("ef_search") or -1) != int(ef_search):
                continue
            if iterative_scan is not None:
                guc = cell.get("guc") or {}
                mode = cell.get("iterative_scan") or guc.get("iterative_scan") or guc.get("iterative_scan_set")
                if str(mode) != str(iterative_scan):
                    continue
            out.append(cell)
    return out


def percentile_linear(values: list[float], p: float) -> float:
    xs = sorted(float(v) for v in values)
    if not xs:
        raise ValueError("empty")
    if len(xs) == 1:
        return xs[0]
    k = (len(xs) - 1) * (p / 100.0)
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return xs[int(k)]
    return xs[f] * (c - k) + xs[c] * (k - f)


def paired_bootstrap_ci(
    diffs: list[float],
    *,
    seed: int = 42,
    b: int = 2000,
) -> tuple[float, float, float]:
    n = len(diffs)
    if n == 0:
        raise ValueError("no diffs")
    point = sum(diffs) / n
    rng = random.Random(seed)
    boots: list[float] = []
    for _ in range(b):
        acc = 0.0
        for _i in range(n):
            acc += diffs[rng.randrange(n)]
        boots.append(acc / n)
    return point, percentile_linear(boots, 2.5), percentile_linear(boots, 97.5)


def hit10_list(run: dict[str, Any], order: list[str]) -> list[int]:
    assert_qid_set(run, order)
    by_id = {str(p["question_id"]): p for p in run["per_question"]}
    out = []
    for qid in order:
        v = by_id[qid]["hit_at_10"]
        if isinstance(v, bool):
            out.append(int(v))
        else:
            out.append(1 if float(v) != 0.0 else 0)
    return out


def mean(xs: list[float]) -> float:
    return sum(xs) / len(xs) if xs else 0.0


def resolve_path(obj: Any, path: list[Any]) -> Any:
    cur = obj
    for step in path:
        if isinstance(step, dict) and "where" in step:
            where = step["where"]
            matches = [
                x
                for x in cur
                if isinstance(x, dict) and all(x.get(k) == v for k, v in where.items())
            ]
            if len(matches) != 1:
                raise KeyError(f"where {where} matched {len(matches)}")
            cur = matches[0]
        elif isinstance(step, int) or (isinstance(step, str) and step.isdigit() and isinstance(cur, list)):
            cur = cur[int(step)]
        else:
            cur = cur[step]
    return cur


def numbers_close(actual: Any, expected: Any, tolerance: float) -> bool:
    if isinstance(expected, list) and isinstance(actual, list):
        if len(actual) != len(expected):
            return False
        return all(numbers_close(a, e, tolerance) for a, e in zip(actual, expected))
    if isinstance(expected, dict) and isinstance(actual, dict):
        return all(k in actual and numbers_close(actual[k], expected[k], tolerance) for k in expected)
    if isinstance(expected, (int, float)) and not isinstance(expected, bool):
        try:
            return abs(float(actual) - float(expected)) <= float(tolerance)
        except (TypeError, ValueError):
            return False
    return actual == expected


def provenance_entries(blob: Any) -> list[dict[str, Any]]:
    if isinstance(blob, list):
        return blob
    if isinstance(blob, dict):
        if isinstance(blob.get("entries"), list):
            return blob["entries"]
        if isinstance(blob.get("questions"), list):
            return blob["questions"]
    raise ValueError("unrecognized provenance schema")


def revision1_py_files(script_dir: Path | None = None) -> list[Path]:
    d = script_dir or Path(__file__).resolve().parent
    return sorted(p for p in d.glob("*.py") if p.is_file())


def bare_erb_cache_lookups(script_dir: Path | None = None) -> list[str]:
    hits: list[str] = []
    skip_names = {"validate_all.py", "harness_lib.py", "test_harness_mutations.py"}
    for path in revision1_py_files(script_dir):
        if path.name in skip_names:
            continue
        text = path.read_text(encoding="utf-8")
        if not BARE_QID_RE.search(text):
            continue
        if CACHE_LOOKUP_RE.search(text):
            hits.append(f"{path.name}: cache lookup uses erb_question_id")
            continue
        try:
            tree = ast.parse(text)
        except SyntaxError:
            hits.append(f"{path.name}: mentions erb_question_id")
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and node.value == "erb_question_id":
                hits.append(f"{path.name}: string erb_question_id")
            if isinstance(node, ast.Name) and node.id == "erb_question_id":
                hits.append(f"{path.name}: name erb_question_id")
    return hits


def bank_question_ids(pub: Path = PUB) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for path in sorted(pub.glob("primary_questions_*.json")):
        blob = load_json(path)
        out[path.name] = list(blob.get("question_ids") or [])
    return out


def result_eval_ids(blob: dict[str, Any]) -> set[str]:
    ids: set[str] = set()
    for run in blob.get("runs") or []:
        for p in run.get("per_question") or []:
            qid = p.get("question_id") or p.get("eval_id")
            if qid:
                ids.add(str(qid))
    pqs = blob.get("per_question_by_scale") or {}
    if isinstance(pqs, dict):
        for rows in pqs.values():
            for p in rows or []:
                qid = p.get("question_id") or p.get("eval_id")
                if qid:
                    ids.add(str(qid))
    return ids


def elapsed_recorded(run: dict[str, Any]) -> bool:
    for key in ("elapsed_s", "elapsed_ms", "elapsed", "wall_clock_s"):
        if run.get(key) is not None:
            return True
    return False


def first_hit_rank(expected: set[str], retrieved: list[str]) -> int | None:
    gold = {str(x) for x in expected}
    for i, did in enumerate(retrieved):
        if str(did) in gold:
            return i + 1
    return None


def question_metrics(expected: list[str] | set[str], retrieved: list[str]) -> dict[str, float]:
    rank = first_hit_rank(set(str(x) for x in expected), [str(d) for d in retrieved])
    e = {str(x) for x in expected}
    r = [str(d) for d in retrieved[:10]]
    rec = (len(e & set(r)) / len(e)) if e else 0.0
    return {
        "rank": rank,
        "hit_at_1": float(rank is not None and rank <= 1),
        "hit_at_5": float(rank is not None and rank <= 5),
        "hit_at_10": float(rank is not None and rank <= 10),
        "mrr": (1.0 / rank) if rank else 0.0,
        "document_recall": rec,
    }


def rrf_fuse(rank_lists: list[list[str]], k: int, top_n: int = 10) -> list[str]:
    scores: dict[str, float] = {}
    for ranked in rank_lists:
        seen: set[str] = set()
        for i, did in enumerate(ranked):
            s = str(did)
            if s in seen:
                continue
            seen.add(s)
            scores[s] = scores.get(s, 0.0) + 1.0 / (k + i + 1)
    return sorted(scores, key=lambda d: (-scores[d], d))[:top_n]


def list_recall_at_k(approx: list[str], exact: list[str], k: int = 10) -> float:
    a = [str(x) for x in approx[:k]]
    e = [str(x) for x in exact[:k]]
    if not e:
        return 0.0
    return len(set(a) & set(e)) / len(set(e))


def cell_hnsw_index_used(cell: dict[str, Any]) -> bool | None:
    if cell.get("hnsw_index_used") is not None:
        return bool(cell.get("hnsw_index_used"))
    plan = cell.get("plan")
    if isinstance(plan, dict) and plan.get("hnsw_index_used") is not None:
        return bool(plan.get("hnsw_index_used"))
    return None


def forced_hnsw_plan_evidence(mode_row: dict[str, Any]) -> tuple[bool, str]:
    """forced_hnsw rows must carry plan evidence that HNSW was used."""
    pc = mode_row.get("plan_check")
    if not pc:
        return False, "missing_plan_check"
    if isinstance(pc, dict):
        if pc.get("all_probes_hnsw") is True:
            return True, "all_probes_hnsw"
        probes = pc.get("probes") or []
        if probes and all(isinstance(p, dict) and p.get("hnsw_used") is True for p in probes):
            return True, "all_probes_hnsw_used"
        if probes and any(isinstance(p, dict) and p.get("hnsw_used") is not True for p in probes):
            n_ok = sum(1 for p in probes if isinstance(p, dict) and p.get("hnsw_used") is True)
            return False, f"probes_hnsw={n_ok}/{len(probes)}"
        if pc.get("hnsw_used") is True or pc.get("hnsw_index_scan") is True:
            return True, "hnsw_used"
        return False, "plan_check_without_hnsw"
    if isinstance(pc, list):
        n_h = sum(1 for e in pc if isinstance(e, dict) and plan_entry_hnsw(e))
        if n_h == 0:
            return False, "plan_check_zero_hnsw"
        return True, f"hnsw_entries={n_h}"
    return False, "unrecognized_plan_check"


def iter_forced_hnsw_rows(blob: dict[str, Any]) -> list[tuple[str, dict[str, Any]]]:
    rows: list[tuple[str, dict[str, Any]]] = []
    for cell in blob.get("cells") or []:
        scale = cell.get("scale") or cell.get("scale_n")
        cond = cell.get("condition")
        ef = cell.get("ef_search")
        for mode in cell.get("modes") or []:
            if str(mode.get("mode") or "").lower() == "forced_hnsw":
                label = f"{cond}/N={scale}/ef={ef}/forced_hnsw"
                rows.append((label, mode))
        if str(cell.get("mode") or cell.get("label") or "").lower() == "forced_hnsw":
            rows.append((f"{cond}/N={scale}/ef={ef}/forced_hnsw", cell))
    return rows
