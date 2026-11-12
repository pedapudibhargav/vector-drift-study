#!/usr/bin/env python3
"""Write scale_manifest_compact.json from data/erb_scale_manifest.json (stdlib only)."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from harness_lib import COMPACT_MANIFEST_PATH, MANIFEST_PATH, ROOT  # noqa: E402


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def compact_documents(docs: list[Any]) -> list[list[Any]]:
    rows: list[list[Any]] = []
    for d in docs:
        if not isinstance(d, dict):
            raise SystemExit(f"unexpected document record: {type(d)}")
        rows.append(
            [
                d["doc_id"],
                d["source_type"],
                int(d["scale_rank"]),
                1 if d.get("is_gold_anchor") else 0,
            ]
        )
    rows.sort(key=lambda r: (int(r[2]), str(r[0]), str(r[1])))
    return rows


def compact_questions(questions: list[Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for q in questions:
        if not isinstance(q, dict):
            raise SystemExit(f"unexpected question record: {type(q)}")
        eval_id = q.get("eval_id") or q.get("question_id")
        out.append(
            {
                "eval_id": eval_id,
                "question_type": q.get("question_type"),
                "source_types": list(q.get("source_types") or []),
                "expected_doc_ids": list(q.get("expected_doc_ids") or []),
            }
        )
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=MANIFEST_PATH)
    parser.add_argument("--out", type=Path, default=COMPACT_MANIFEST_PATH)
    args = parser.parse_args(argv)
    if not args.source.is_file():
        print(f"missing source manifest {args.source}", file=sys.stderr)
        return 1
    digest = sha256_file(args.source)
    man = json.loads(args.source.read_text(encoding="utf-8"))
    docs = compact_documents(list(man.get("documents") or []))
    questions = compact_questions(list(man.get("questions") or []))
    payload = {
        "sha256_of_source": digest,
        "n_documents": len(docs),
        "documents": docs,
        "questions": questions,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, separators=(",", ":")) + "\n", encoding="utf-8")
    rel_src = str(args.source.relative_to(ROOT)) if ROOT in args.source.parents else str(args.source)
    print(f"wrote {args.out} n_documents={len(docs)} n_questions={len(questions)} source={rel_src}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
