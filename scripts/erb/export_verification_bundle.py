#!/usr/bin/env python3
"""Build Option-B verification bundle for GitHub Pages (no embeddings).

Outputs under artifacts/verification/ and docs/data/verification/:
  - per_query.jsonl   — every primary-200 × scale × condition row
  - questions.json    — question_id → text + expected_doc_ids
  - chunks_by_id.json — doc_id → truncated text for gold∪retrieved only
  - manifest.json     — sizes, counts, build metadata

Sources (in order):
  1) artifacts/published/erb_full_primary200_to100k.json  (metrics + retrieved ids)
  2) data/enterprise_rag_bench/questions.jsonl            (question text + gold ids)
  3) data/enterprise_rag_bench/documents/*.txt             (chunk text; local ERB data)
  4) optional DATABASE_URL / document_chunks if Postgres is up

Embeddings are never written.
"""

from __future__ import annotations

import argparse
import json
import os
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PUBLISHED = ROOT / "artifacts" / "published" / "erb_full_primary200_to100k.json"
QUESTIONS_JSONL = ROOT / "data" / "enterprise_rag_bench" / "questions.jsonl"
DOCS_DIR = ROOT / "data" / "enterprise_rag_bench" / "documents"
OUT_ART = ROOT / "artifacts" / "verification"
OUT_DOCS = ROOT / "docs" / "data" / "verification"
MAX_CHARS = 8_000
_DOC_INDEX: dict[str, Path] | None = None


def build_doc_index() -> dict[str, Path]:
    global _DOC_INDEX
    if _DOC_INDEX is not None:
        return _DOC_INDEX
    index: dict[str, Path] = {}
    if DOCS_DIR.exists():
        for p in DOCS_DIR.glob("*.txt"):
            name = p.name
            if name.startswith("dsid_") and "__" in name:
                index.setdefault(name.split("__", 1)[0], p)
    _DOC_INDEX = index
    return index


def load_questions(primary_ids: set[str]) -> dict[str, dict]:
    out: dict[str, dict] = {}
    if not QUESTIONS_JSONL.exists():
        return out
    with QUESTIONS_JSONL.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            qid = row.get("question_id") or row.get("id")
            if qid not in primary_ids:
                continue
            gold = row.get("expected_doc_ids") or row.get("gold_doc_ids") or []
            if isinstance(gold, str):
                gold = [g for g in gold.split("|") if g]
            out[qid] = {
                "question_id": qid,
                "question_text": row.get("question") or row.get("question_text") or row.get("text") or "",
                "question_type": row.get("question_type"),
                "expected_doc_ids": list(gold),
            }
    return out


def resolve_doc_text(doc_id: str, max_chars: int = MAX_CHARS) -> str | None:
    path = build_doc_index().get(doc_id)
    if path is None:
        return None
    text = path.read_text(encoding="utf-8", errors="replace")
    if len(text) > max_chars:
        return text[:max_chars] + "\n…[truncated for Pages bundle]"
    return text


def try_db_chunks(doc_ids: set[str]) -> dict[str, str]:
    url = os.environ.get("DATABASE_URL", "")
    if not url:
        return {}
    try:
        import psycopg
    except ImportError:
        return {}
    sync = url.replace("postgresql+asyncpg://", "postgresql://")
    found: dict[str, str] = {}
    try:
        with psycopg.connect(sync) as conn:
            with conn.cursor() as cur:
                for did in doc_ids:
                    cur.execute(
                        "SELECT chunk_text FROM document_chunks WHERE doc_id = %s LIMIT 1",
                        (did,),
                    )
                    row = cur.fetchone()
                    if row and row[0]:
                        t = str(row[0])
                        found[did] = t[:MAX_CHARS] + ("\n…[truncated]" if len(t) > MAX_CHARS else "")
    except Exception as exc:  # noqa: BLE001 — optional path
        print(f"DB chunk lookup skipped: {exc}")
    return found


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--max-chars", type=int, default=8_000)
    args = ap.parse_args()
    max_chars = args.max_chars

    if not PUBLISHED.exists():
        raise SystemExit(f"missing {PUBLISHED}")

    sweep = json.loads(PUBLISHED.read_text(encoding="utf-8"))
    primary_path = ROOT / "artifacts" / "published" / "primary_questions_200.json"
    primary_ids = set(json.loads(primary_path.read_text())["question_ids"])
    questions = load_questions(primary_ids)

    rows: list[dict] = []
    needed_docs: set[str] = set()
    for run in sweep["runs"]:
        for q in run["per_question"]:
            qid = q["question_id"]
            meta_q = questions.get(qid, {})
            expected = list(meta_q.get("expected_doc_ids") or [])
            retrieved = list(q.get("retrieved_doc_ids") or [])
            needed_docs.update(expected)
            needed_docs.update(retrieved)
            rows.append(
                {
                    "question_id": qid,
                    "question_text": meta_q.get("question_text", ""),
                    "question_type": meta_q.get("question_type"),
                    "experiment_run_id": run.get("experiment_run_id"),
                    "condition": q.get("condition") or run.get("condition"),
                    "corpus_scale_size": q.get("corpus_scale_size") or run.get("corpus_scale_size"),
                    "hit_at_1": bool(q.get("hit_at_1")),
                    "hit_at_5": bool(q.get("hit_at_5")),
                    "hit_at_10": bool(q.get("hit_at_10")),
                    "mrr": q.get("mrr"),
                    "document_recall": q.get("recall") or q.get("document_recall"),
                    "best_gold_rank": q.get("rank"),
                    "best_gold_score": q.get("score"),
                    "expected_doc_ids": expected,
                    "retrieved_doc_ids": retrieved,
                }
            )

    chunks = try_db_chunks(needed_docs)
    missing = [d for d in needed_docs if d not in chunks]
    for did in missing:
        text = resolve_doc_text(did, max_chars)
        if text is not None:
            chunks[did] = text

    OUT_ART.mkdir(parents=True, exist_ok=True)
    OUT_DOCS.mkdir(parents=True, exist_ok=True)

    per_query_path = OUT_ART / "per_query.jsonl"
    with per_query_path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    questions_out = {qid: questions.get(qid, {"question_id": qid}) for qid in primary_ids}
    (OUT_ART / "questions.json").write_text(
        json.dumps(questions_out, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    (OUT_ART / "chunks_by_id.json").write_text(
        json.dumps(chunks, ensure_ascii=False), encoding="utf-8"
    )

    manifest = {
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "source_sweep": str(PUBLISHED.relative_to(ROOT)),
        "row_count": len(rows),
        "primary_questions": len(primary_ids),
        "unique_docs_referenced": len(needed_docs),
        "chunks_resolved": len(chunks),
        "chunks_missing": sorted(needed_docs - set(chunks)),
        "max_chars_per_chunk": max_chars,
        "includes_embeddings": False,
        "note": "Option B Pages bundle. Full embeddings dump is Option C on GitHub Releases.",
    }
    (OUT_ART / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    # Mirror into docs/ for Pages deploy
    for name in ("per_query.jsonl", "questions.json", "chunks_by_id.json", "manifest.json"):
        src = OUT_ART / name
        (OUT_DOCS / name).write_bytes(src.read_bytes())

    # Also copy aggregate published JSON (small enough) for summary tables
    pub_dir = ROOT / "docs" / "data" / "published"
    pub_dir.mkdir(parents=True, exist_ok=True)
    for name in (
        "erb_full_primary200_to100k_fit.json",
        "erb_full_primary200_to100k.json",
        "primary_questions_200.json",
    ):
        src = ROOT / "artifacts" / "published" / name
        if src.exists():
            (pub_dir / name).write_bytes(src.read_bytes())

    print(json.dumps(manifest, indent=2))
    missing_n = len(manifest["chunks_missing"])
    if missing_n:
        print(f"WARNING: {missing_n} docs missing text — start DB or ensure ERB documents/ present")
    return 0 if missing_n == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
