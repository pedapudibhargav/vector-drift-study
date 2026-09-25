#!/usr/bin/env python3
"""Parse EnterpriseRAG documents and build a deterministic scale manifest."""

from __future__ import annotations

import argparse
import json
import random
import re
import sys
from collections import defaultdict
from pathlib import Path

from paths import (
    ERB_DOCS,
    ERB_EXTRA_QUESTIONS,
    ERB_MANIFEST,
    ERB_QUESTIONS,
    EXCLUDED_QUESTION_TYPES,
    SCALE_SEED,
)
from question_identity import attach_eval_identity

DOC_ID_RE = re.compile(r"^(dsid_[0-9a-f]+)", re.I)


def load_jsonl(path: Path) -> list[dict]:
    rows: list[dict] = []
    if not path.exists():
        return rows
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def retrieval_questions(include_extra: bool = True) -> list[dict]:
    """Load base + optional extra questions with *unique* eval_id keys.

    Extra metadata questions reuse ERB ``question_id`` values but are different
    items (different text/gold/source_types). We expose them as
    ``{question_id}::{question_type}`` so sweeps never collide.
    """
    rows = load_jsonl(ERB_QUESTIONS)
    if include_extra:
        rows.extend(load_jsonl(ERB_EXTRA_QUESTIONS))
    out: list[dict] = []
    seen: set[str] = set()
    for q in rows:
        qtype = str(q.get("question_type") or "").lower()
        expected = [d for d in (q.get("expected_doc_ids") or []) if d]
        if qtype in EXCLUDED_QUESTION_TYPES or not expected:
            continue
        row = attach_eval_identity(
            {
                "question_id": q["question_id"],
                "question_type": qtype,
                "question": q.get("question") or q.get("question_text") or "",
                "expected_doc_ids": expected,
                "source_types": list(q.get("source_types") or []),
            }
        )
        if row["eval_id"] in seen:
            raise SystemExit(f"duplicate eval_id after attach: {row['eval_id']}")
        seen.add(row["eval_id"])
        out.append(row)
    return out


def parse_doc_id(filename: str) -> str | None:
    m = DOC_ID_RE.match(Path(filename).name)
    return m.group(1).lower() if m else None


def read_document(path: Path) -> dict:
    doc_id = parse_doc_id(path.name)
    if not doc_id:
        raise ValueError(f"bad doc name: {path}")
    source_side = path.with_suffix(".source")
    source_type = "unknown"
    if source_side.exists():
        source_type = source_side.read_text(encoding="utf-8").strip() or "unknown"
    else:
        # try parent folder name if docs kept nested
        parent = path.parent.name.lower().replace("-", "_")
        if parent not in {"documents", "enterprise_rag_bench"}:
            source_type = parent

    text = path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    title = lines[0].strip() if lines else doc_id
    body = "\n".join(lines[1:]).strip() if len(lines) > 1 else text
    return {
        "doc_id": doc_id,
        "source_type": source_type,
        "title": title,
        "text": body or text,
        "path": str(path),
    }


def iter_documents(docs_dir: Path) -> list[dict]:
    docs: list[dict] = []
    for path in sorted(docs_dir.rglob("*.txt")):
        try:
            docs.append(read_document(path))
        except Exception as exc:
            print(f"skip {path}: {exc}", file=sys.stderr)
    return docs


def build_manifest(
    docs: list[dict],
    questions: list[dict],
    *,
    seed: int = SCALE_SEED,
) -> dict:
    present_ids = {d["doc_id"] for d in docs}
    usable_questions: list[dict] = []
    skipped_incomplete = 0
    for q in questions:
        expected = [d for d in q["expected_doc_ids"] if d]
        if expected and all(doc_id in present_ids for doc_id in expected):
            usable_questions.append(q)
        else:
            skipped_incomplete += 1
    questions = usable_questions

    gold: set[str] = set()
    for q in questions:
        gold.update(q["expected_doc_ids"])

    by_id = {d["doc_id"]: d for d in docs}
    missing_gold = sorted(g for g in gold if g not in by_id)
    present_gold = sorted(g for g in gold if g in by_id)

    rng = random.Random(seed)
    # Stratified distractors: shuffle within each source, then round-robin
    distractors_by_source: dict[str, list[str]] = defaultdict(list)
    for doc in docs:
        if doc["doc_id"] in gold:
            continue
        distractors_by_source[doc["source_type"]].append(doc["doc_id"])
    for source in distractors_by_source:
        rng.shuffle(distractors_by_source[source])

    sources = sorted(distractors_by_source.keys())
    distractor_order: list[str] = []
    while any(distractors_by_source[s] for s in sources):
        for source in sources:
            bucket = distractors_by_source[source]
            if bucket:
                distractor_order.append(bucket.pop(0))

    # Anchors first (stable sorted), then stratified distractors
    ranked: list[dict] = []
    for rank, doc_id in enumerate(present_gold):
        d = by_id[doc_id]
        ranked.append(
            {
                "doc_id": doc_id,
                "source_type": d["source_type"],
                "title": d["title"],
                "path": str(Path(d["path"]).name) if "path" in d else "",
                "scale_rank": rank,
                "is_gold_anchor": True,
            }
        )
    base = len(ranked)
    for i, doc_id in enumerate(distractor_order):
        d = by_id[doc_id]
        ranked.append(
            {
                "doc_id": doc_id,
                "source_type": d["source_type"],
                "title": d["title"],
                "path": str(Path(d["path"]).name),
                "scale_rank": base + i,
                "is_gold_anchor": False,
            }
        )

    source_counts: dict[str, int] = defaultdict(int)
    for row in ranked:
        source_counts[row["source_type"]] += 1

    return {
        "seed": seed,
        "document_count": len(ranked),
        "gold_anchor_count": len(present_gold),
        "missing_gold_doc_ids": missing_gold,
        "questions_skipped_incomplete_gold": skipped_incomplete,
        "source_counts": dict(sorted(source_counts.items())),
        "questions": questions,
        "documents": ranked,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--docs-dir", type=Path, default=ERB_DOCS)
    parser.add_argument("--out", type=Path, default=ERB_MANIFEST)
    parser.add_argument("--seed", type=int, default=SCALE_SEED)
    parser.add_argument("--no-extra-questions", action="store_true")
    args = parser.parse_args()

    if not args.docs_dir.exists():
        raise SystemExit(f"docs dir missing: {args.docs_dir}")

    questions = retrieval_questions(include_extra=not args.no_extra_questions)
    docs = iter_documents(args.docs_dir)
    if not docs:
        raise SystemExit(f"no .txt documents under {args.docs_dir}")

    manifest = build_manifest(docs, questions, seed=args.seed)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(
        f"wrote {args.out} docs={manifest['document_count']} "
        f"anchors={manifest['gold_anchor_count']} "
        f"questions={len(manifest['questions'])} "
        f"missing_gold={len(manifest['missing_gold_doc_ids'])}"
    )
    return 0


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    raise SystemExit(main())
