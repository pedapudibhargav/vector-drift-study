#!/usr/bin/env python3
"""BM25 truncation variants (revision W5): like-for-like lexical controls.

Runs rank_bm25.BM25Okapi on the primary-200 gold-pinned scale ladder with four
document-length rules matched to dense OpenAI indexing semantics.

Usage:
  /path/to/.venv/bin/python scripts/erb/revision1/run_bm25_variants.py --variant chars4000
  /path/to/.venv/bin/python scripts/erb/revision1/run_bm25_variants.py --variant tokens8191
  /path/to/.venv/bin/python scripts/erb/revision1/run_bm25_variants.py --variant dense_text
  /path/to/.venv/bin/python scripts/erb/revision1/run_bm25_variants.py --variant raw_untruncated
  /path/to/.venv/bin/python scripts/erb/revision1/run_bm25_variants.py --variant dense_text_chars4000
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts" / "erb"))
from paths import DEFAULT_SCALES, ERB_MANIFEST  # noqa: E402

PUB = ROOT / "artifacts" / "published"
REV1 = PUB / "revision1"
PRIMARY = PUB / "primary_questions_200.json"
TOKEN_CUTS = REV1 / "doc_token_cuts_openai.json"
DOC_LENGTH_STATS = REV1 / "doc_length_stats.json"
RAW_DOCS = Path(__file__).resolve().parents[3] / "data" / "enterprise_rag_bench" / "documents"

TOKEN_RE = re.compile(r"[a-z0-9]+")
BM25_PARAMS = {"k1": 1.5, "b": 0.75, "epsilon": 0.25}
TOP_K = 10
TOP_100 = 100

LEGACY_TITLE_PLUS = frozenset(
    {"chars4000", "chars8191", "tokens8191", "untruncated"}
)

VARIANT_RULES = {
    "chars4000": "truncate title+chunk_text to 4000 characters",
    "chars8191": "truncate title+chunk_text to 8191 characters",
    "tokens8191": (
        "truncate at cut_char_8191 from doc_token_cuts_openai.json "
        "(cl100k_base 8191-token boundary)"
    ),
    "untruncated": "no truncation on title+chunk_text",
    "dense_text": "chunk_text from document_chunks only (matches OpenAI embed input; no extra title)",
    "raw_untruncated": (
        "chunk_text from DB; for 11 ingest-capped docs only, full raw benchmark body "
        "via ingest _read_body (title + body, no truncation)"
    ),
    "dense_text_chars4000": "chunk_text only, truncated to 4000 characters",
    "titan_text": "raw_untruncated text capped at 24000 characters (the Titan client-side cap)",
}

VARIANT_METHOD = {
    "chars4000": "Okapi BM25 (rank_bm25.BM25Okapi) on title+chunk_text",
    "chars8191": "Okapi BM25 (rank_bm25.BM25Okapi) on title+chunk_text",
    "tokens8191": "Okapi BM25 (rank_bm25.BM25Okapi) on title+chunk_text",
    "untruncated": "Okapi BM25 (rank_bm25.BM25Okapi) on title+chunk_text",
    "dense_text": "Okapi BM25 (rank_bm25.BM25Okapi) on chunk_text (dense embed text)",
    "raw_untruncated": "Okapi BM25 (rank_bm25.BM25Okapi) on chunk_text or raw ingest body (11 capped)",
    "dense_text_chars4000": "Okapi BM25 (rank_bm25.BM25Okapi) on chunk_text truncated to 4000 chars",
    "titan_text": "Okapi BM25 (rank_bm25.BM25Okapi) on the text Titan embedded (24000-char cap)",
}

SUMMARY_VARIANT_ORDER = (
    "chars4000",
    "dense_text_chars4000",
    "chars8191",
    "tokens8191",
    "untruncated",
    "dense_text",
    "raw_untruncated",
)


def pg_connect():
    import psycopg2

    return psycopg2.connect(
        host=os.environ.get("PGHOST", "localhost"),
        port=os.environ.get("PGPORT", "5432"),
        user=os.environ["PGUSER"],
        password=os.environ["PGPASSWORD"],
        dbname=os.environ["PGDATABASE"],
    )


def tokenize(text: str) -> list[str]:
    return TOKEN_RE.findall((text or "").lower())


def ingest_read_body(path: Path, title: str) -> str:
    text = path.read_text(encoding="utf-8", errors="replace").replace("\x00", "")
    lines = text.splitlines()
    if lines and lines[0].strip() == title:
        body = "\n".join(lines[1:]).strip()
        return f"{title}\n\n{body}" if body else title
    return text


def load_capped_doc_ids() -> frozenset[str]:
    if not DOC_LENGTH_STATS.is_file():
        raise SystemExit(f"missing dependency: {DOC_LENGTH_STATS}")
    data = json.loads(DOC_LENGTH_STATS.read_text(encoding="utf-8"))
    ids = data.get("raw_pretruncation_chars", {}).get("capped_doc_ids") or []
    if len(ids) != 11:
        raise SystemExit(f"expected 11 capped_doc_ids, got {len(ids)}")
    return frozenset(str(x) for x in ids)


def index_raw_paths(needed: frozenset[str]) -> dict[str, Path]:
    found: dict[str, Path] = {}
    if not RAW_DOCS.is_dir():
        raise SystemExit(f"raw document directory missing: {RAW_DOCS}")
    with os.scandir(RAW_DOCS) as it:
        for ent in it:
            if not ent.name.endswith(".txt") or "__" not in ent.name:
                continue
            did = ent.name.split("__", 1)[0]
            if did in needed and did not in found:
                found[did] = Path(ent.path)
    missing = sorted(needed - set(found))
    if missing:
        raise SystemExit(f"missing raw files for capped docs: {missing[:5]}")
    return found


def truncate_text(
    full_text: str, doc_id: str, variant: str, token_cuts: dict[str, dict]
) -> tuple[str, bool]:
    if variant in ("untruncated", "dense_text", "raw_untruncated"):
        return full_text, False
    if variant == "titan_text":
        out = full_text[:24000]
        return out, len(out) < len(full_text)
    if variant in ("chars4000", "dense_text_chars4000"):
        out = full_text[:4000]
        return out, len(out) < len(full_text)
    if variant == "chars8191":
        out = full_text[:8191]
        return out, len(out) < len(full_text)
    if variant == "tokens8191":
        info = token_cuts.get(doc_id)
        if info is None:
            return full_text, False
        cut = int(info["cut_char_8191"])
        out = full_text[:cut]
        return out, len(out) < len(full_text)
    raise ValueError(f"unknown variant: {variant}")


def top_indices(scores, k: int) -> list[int]:
    import numpy as np

    n = len(scores)
    if n <= k:
        return sorted(range(n), key=lambda i: scores[i], reverse=True)
    arr = np.asarray(scores)
    top_idx = np.argpartition(arr, -k)[-k:]
    return top_idx[np.argsort(arr[top_idx])[::-1]].tolist()


def load_questions() -> list[dict]:
    qids = json.loads(PRIMARY.read_text(encoding="utf-8"))["question_ids"]
    man = json.loads(ERB_MANIFEST.read_text(encoding="utf-8"))
    qmap = {q["question_id"]: q for q in man["questions"]}
    questions = [qmap[qid] for qid in qids if qid in qmap]
    if len(questions) != 200:
        raise SystemExit(f"expected 200 primary questions, got {len(questions)}")
    return questions


def load_corpus_legacy(max_n: int) -> list[tuple[int, str, str]]:
    conn = pg_connect()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT scale_rank, doc_id,
                   coalesce(title,'') || ' ' || coalesce(chunk_text,'')
            FROM document_chunks
            WHERE embedding IS NOT NULL
              AND scale_rank IS NOT NULL
              AND scale_rank < %s
            ORDER BY scale_rank ASC, doc_id ASC
            """,
            (max_n,),
        )
        return [
            (int(scale_rank), str(doc_id), str(text or ""))
            for scale_rank, doc_id, text in cur.fetchall()
        ]
    finally:
        conn.close()


def load_corpus_chunk_rows(max_n: int) -> list[tuple[int, str, str, str]]:
    conn = pg_connect()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT scale_rank, doc_id,
                   coalesce(title,''), coalesce(chunk_text,'')
            FROM document_chunks
            WHERE embedding IS NOT NULL
              AND scale_rank IS NOT NULL
              AND scale_rank < %s
            ORDER BY scale_rank ASC, doc_id ASC
            """,
            (max_n,),
        )
        return [
            (int(scale_rank), str(doc_id), str(title or ""), str(chunk or ""))
            for scale_rank, doc_id, title, chunk in cur.fetchall()
        ]
    finally:
        conn.close()


def corpus_text_for_variant(
    variant: str,
    scale_rank: int,
    doc_id: str,
    title: str,
    chunk_text: str,
    capped_ids: frozenset[str],
    raw_paths: dict[str, Path],
) -> str:
    if variant in LEGACY_TITLE_PLUS:
        return f"{title} {chunk_text}".strip() if title else chunk_text
    if variant in ("raw_untruncated", "titan_text"):
        if doc_id in capped_ids:
            return ingest_read_body(raw_paths[doc_id], title or doc_id)
        return chunk_text
    if variant in ("dense_text", "dense_text_chars4000"):
        return chunk_text
    raise ValueError(f"unknown variant: {variant}")


def load_corpus(variant: str, max_n: int) -> list[tuple[int, str, str]]:
    if variant in LEGACY_TITLE_PLUS:
        return load_corpus_legacy(max_n)
    rows = load_corpus_chunk_rows(max_n)
    capped_ids: frozenset[str] = frozenset()
    raw_paths: dict[str, Path] = {}
    if variant in ("raw_untruncated", "titan_text"):
        capped_ids = load_capped_doc_ids()
        raw_paths = index_raw_paths(capped_ids)
    out: list[tuple[int, str, str]] = []
    for scale_rank, doc_id, title, chunk_text in rows:
        text = corpus_text_for_variant(
            variant, scale_rank, doc_id, title, chunk_text, capped_ids, raw_paths
        )
        out.append((scale_rank, doc_id, text))
    return out


def end_idx(ranks: list[int], n: int) -> int:
    lo, hi = 0, len(ranks)
    while lo < hi:
        mid = (lo + hi) // 2
        if ranks[mid] < n:
            lo = mid + 1
        else:
            hi = mid
    return lo


def run_variant(variant: str, scales: list[int]) -> tuple[dict, float]:
    from rank_bm25 import BM25Okapi

    if variant == "tokens8191" and not TOKEN_CUTS.is_file():
        raise SystemExit(
            f"missing dependency: {TOKEN_CUTS} (run doc_token_stats first)"
        )
    token_cuts: dict[str, dict] = {}
    if variant == "tokens8191":
        token_cuts = json.loads(TOKEN_CUTS.read_text(encoding="utf-8"))

    questions = load_questions()
    max_n = max(scales)
    print(f"[{variant}] loading docs scale_rank < {max_n} …", flush=True)
    t_load = time.time()
    rows = load_corpus(variant, max_n)
    print(f"[{variant}] loaded {len(rows)} docs in {time.time() - t_load:.1f}s", flush=True)

    ranks: list[int] = []
    doc_ids: list[str] = []
    corpus_tokens: list[list[str]] = []
    truncated_flags: list[bool] = []

    for scale_rank, doc_id, text in rows:
        truncated, was_trunc = truncate_text(text, doc_id, variant, token_cuts)
        ranks.append(scale_rank)
        doc_ids.append(doc_id)
        corpus_tokens.append(tokenize(truncated))
        truncated_flags.append(was_trunc)

    query_tokens = [tokenize(q["question"]) for q in questions]

    t_wall = time.time()
    runs: list[dict] = []
    per_question_by_scale: dict[str, list[dict]] = {}

    for n in scales:
        e = end_idx(ranks, n)
        if e == 0:
            raise SystemExit(f"no docs for N={n}")
        n_trunc = sum(1 for i in range(e) if truncated_flags[i])
        toks = corpus_tokens[:e]
        ids = doc_ids[:e]
        print(f"[{variant}] BM25 N={n} docs={e} truncated={n_trunc} …", flush=True)
        t1 = time.time()
        bm25 = BM25Okapi(toks)
        hit1 = hit5 = hit10 = 0
        recall_sum = mrr_sum = 0.0
        per_q: list[dict] = []
        for q, qtok in zip(questions, query_tokens):
            expected = {str(x) for x in (q.get("expected_doc_ids") or []) if x}
            if not expected:
                continue
            scores = bm25.get_scores(qtok)
            top100_idx = top_indices(scores, min(TOP_100, len(scores)))
            top10_idx = top100_idx[:TOP_K]
            retrieved = [ids[i] for i in top10_idx]
            retrieved_top100 = [ids[i] for i in top100_idx]
            rank = None
            for i, did in enumerate(retrieved, start=1):
                if did in expected:
                    rank = i
                    break
            hit_ids = expected & set(retrieved)
            recall = len(hit_ids) / max(len(expected), 1)
            mrr = 1.0 / rank if rank else 0.0
            r1 = rank == 1 if rank else False
            r5 = rank is not None and rank <= 5
            r10 = rank is not None and rank <= 10
            hit1 += int(r1)
            hit5 += int(r5)
            hit10 += int(r10)
            recall_sum += recall
            mrr_sum += mrr
            per_q.append(
                {
                    "question_id": q["question_id"],
                    "rank": rank,
                    "hit_at_1": r1,
                    "hit_at_5": r5,
                    "hit_at_10": r10,
                    "mrr": mrr,
                    "document_recall": recall,
                    "retrieved_doc_ids": retrieved,
                    "retrieved_top100": retrieved_top100,
                }
            )
        nq = len(per_q) or 1
        summary = {
            "condition": "bm25_okapi",
            "method": "rank_bm25.BM25Okapi",
            "corpus_scale_size": n,
            "n_docs": e,
            "n_truncated_documents": n_trunc,
            "questions_evaluated": len(per_q),
            "hit_at_1": round(hit1 / nq, 4),
            "hit_at_5": round(hit5 / nq, 4),
            "hit_at_10": round(hit10 / nq, 4),
            "document_recall": round(recall_sum / nq, 4),
            "mrr": round(mrr_sum / nq, 4),
            "elapsed_s": round(time.time() - t1, 1),
        }
        print(
            f"  Hit@10={summary['hit_at_10']:.3f} truncated={n_trunc} ({summary['elapsed_s']}s)",
            flush=True,
        )
        runs.append(summary)
        per_question_by_scale[str(n)] = per_q

    wall_s = time.time() - t_wall
    max_chars = None
    if variant in ("chars4000", "dense_text_chars4000"):
        max_chars = 4000
    elif variant == "chars8191":
        max_chars = 8191

    report = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "variant": variant,
        "method": VARIANT_METHOD[variant],
        "truncation_rule": VARIANT_RULES[variant],
        "bm25_params": BM25_PARAMS,
        "custom_implementation": False,
        "max_chars": max_chars,
        "primary_n": 200,
        "scales": scales,
        "wall_clock_s": round(wall_s, 1),
        "runs": runs,
        "per_question_by_scale": per_question_by_scale,
    }
    return report, wall_s


def write_variant_outputs(report: dict) -> Path:
    REV1.mkdir(parents=True, exist_ok=True)
    variant = report["variant"]
    out = REV1 / f"bm25_{variant}.json"
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    md_lines = [
        f"# BM25 variant `{variant}` (primary-200)",
        "",
        report["truncation_rule"],
        "",
        f"Wall-clock: {report['wall_clock_s']}s",
        "",
        "| N | docs | truncated | Hit@1 | Hit@5 | Hit@10 | MRR |",
        "|---|------|-----------|-------|-------|--------|-----|",
    ]
    for r in report["runs"]:
        md_lines.append(
            f"| {r['corpus_scale_size']} | {r['n_docs']} | {r['n_truncated_documents']} | "
            f"{r['hit_at_1']} | {r['hit_at_5']} | {r['hit_at_10']} | {r['mrr']} |"
        )
    out.with_suffix(".md").write_text("\n".join(md_lines) + "\n", encoding="utf-8")
    print(f"wrote {out}")
    return out


def update_summary_md() -> None:
    variants = [v for v in SUMMARY_VARIANT_ORDER if (REV1 / f"bm25_{v}.json").is_file()]
    if not variants:
        variants = list(SUMMARY_VARIANT_ORDER)
    series: dict[str, dict[int, float]] = {}
    trunc_100k: dict[str, int] = {}
    for v in variants:
        path = REV1 / f"bm25_{v}.json"
        if not path.is_file():
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        series[v] = {r["corpus_scale_size"]: r["hit_at_10"] for r in data["runs"]}
        for r in data["runs"]:
            if r["corpus_scale_size"] == 100000:
                trunc_100k[v] = r["n_truncated_documents"]

    scales = list(DEFAULT_SCALES)
    header = "| N | " + " | ".join(variants) + " |"
    sep = "|---|" + "|".join(["---"] * len(variants)) + "|"
    lines = [
        "# BM25 truncation variants — Hit@10 by scale (primary-200)",
        "",
        header,
        sep,
    ]
    for n in scales:
        cells = []
        for v in variants:
            val = series.get(v, {}).get(n)
            cells.append(f"{val:.3f}" if val is not None else "—")
        lines.append(f"| {n} | " + " | ".join(cells) + " |")
    if trunc_100k:
        lines.extend(["", "Truncated documents at N=100000:"])
        for v in variants:
            if v in trunc_100k:
                lines.append(f"- `{v}`: {trunc_100k[v]}")
    dense = REV1 / "bm25_dense_text.json"
    raw = REV1 / "bm25_raw_untruncated.json"
    if dense.is_file() and raw.is_file():
        d_data = json.loads(dense.read_text(encoding="utf-8"))
        r_data = json.loads(raw.read_text(encoding="utf-8"))
        diff_pairs = 0
        for scale in d_data.get("scales", []):
            key = str(scale)
            d_q = {x["question_id"]: x for x in d_data["per_question_by_scale"][key]}
            r_q = {x["question_id"]: x for x in r_data["per_question_by_scale"][key]}
            for qid, dq in d_q.items():
                if dq.get("retrieved_top100") != r_q[qid].get("retrieved_top100"):
                    diff_pairs += 1
        lines.extend(
            [
                "",
                "## dense_text vs raw_untruncated",
                "",
                f"Question×scale pairs with differing top-100 (expect only queries touched by 11 capped docs): "
                f"{diff_pairs}",
            ]
        )
    baseline = REV1 / "bm25_chars4000.json"
    dt4 = REV1 / "bm25_dense_text_chars4000.json"
    if baseline.is_file() and dt4.is_file():
        b_data = json.loads(baseline.read_text(encoding="utf-8"))
        n_data = json.loads(dt4.read_text(encoding="utf-8"))
        lines.extend(["", "## chars4000 (title+chunk) vs dense_text_chars4000", ""])
        lines.append("| N | baseline Hit@10 | dense_text_chars4000 | Δ |")
        lines.append("|---|-----------------|----------------------|---|")
        b_map = {r["corpus_scale_size"]: r["hit_at_10"] for r in b_data["runs"]}
        n_map = {r["corpus_scale_size"]: r["hit_at_10"] for r in n_data["runs"]}
        for n in b_data.get("scales", []):
            b = b_map[n]
            nv = n_map[n]
            lines.append(f"| {n} | {b:.3f} | {nv:.3f} | {nv - b:+.3f} |")
    (REV1 / "bm25_variants_summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {REV1 / 'bm25_variants_summary.md'}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--variant",
        required=True,
        choices=sorted(VARIANT_RULES),
        help="Truncation variant to run",
    )
    parser.add_argument(
        "--scales",
        default=",".join(str(s) for s in DEFAULT_SCALES),
        help="Comma-separated N values",
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Regenerate bm25_variants_summary.md from existing JSON artifacts",
    )
    args = parser.parse_args()

    if args.summary:
        update_summary_md()
        return 0

    scales = [int(x) for x in args.scales.split(",") if x.strip()]
    report, wall_s = run_variant(args.variant, scales)
    write_variant_outputs(report)
    update_summary_md()
    print(f"[{args.variant}] total wall-clock {wall_s:.1f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
