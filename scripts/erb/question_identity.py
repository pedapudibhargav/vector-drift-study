"""Canonical evaluation identity for ERB questions.

EnterpriseRAG-Bench ships *extra* metadata-filter questions that reuse the same
``question_id`` as a basic question but have different text, gold docs, and
source_types. Treating ``question_id`` alone as unique caused:

  - duplicate rows in primary-200 / sweep JSON (200 rows, 183 unique IDs)
  - opposite Hit@10 on identical retrieval lists (different gold sets)
  - polluted aggregates and human-audit worksheets

Canonical key: ``{question_id}::{question_type}`` (unique across base+extra).
"""

from __future__ import annotations

from typing import Any


def question_type_of(row: dict[str, Any]) -> str:
    return str(row.get("question_type") or "unknown").lower().strip() or "unknown"


def make_eval_id(question_id: str, question_type: str | None = None, *, row: dict[str, Any] | None = None) -> str:
    qid = str(question_id).strip()
    qtype = question_type_of(row) if row is not None else str(question_type or "unknown").lower().strip()
    if "::" in qid:
        return qid  # already canonical
    return f"{qid}::{qtype}"


def attach_eval_identity(row: dict[str, Any]) -> dict[str, Any]:
    """Return a shallow copy with eval_id + normalized question_type."""
    out = dict(row)
    qtype = question_type_of(out)
    out["question_type"] = qtype
    out["erb_question_id"] = str(out.get("erb_question_id") or out.get("question_id") or "")
    out["eval_id"] = make_eval_id(out["erb_question_id"], qtype)
    # Downstream sweep/DB historically key on question_id — use eval_id there.
    out["question_id"] = out["eval_id"]
    return out


def stratified_unique(
    questions: list[dict[str, Any]],
    n: int,
    *,
    seed: int = 42,
) -> list[dict[str, Any]]:
    """Stratify by question_type without replacement on eval_id."""
    import random
    from collections import defaultdict

    by_id: dict[str, dict[str, Any]] = {}
    for q in questions:
        row = attach_eval_identity(q)
        # First wins; collisions on eval_id should not happen after attach
        by_id.setdefault(row["eval_id"], row)
    unique = list(by_id.values())
    if n <= 0 or n >= len(unique):
        return unique

    by_type: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for q in unique:
        by_type[question_type_of(q)].append(q)

    rng = random.Random(seed)
    total = len(unique) or 1
    picked: list[dict[str, Any]] = []
    seen: set[str] = set()
    for qtype, bucket in sorted(by_type.items()):
        rng.shuffle(bucket)
        take = max(1, round(n * len(bucket) / total))
        for row in bucket[:take]:
            if row["eval_id"] in seen:
                continue
            seen.add(row["eval_id"])
            picked.append(row)

    rng.shuffle(picked)
    if len(picked) > n:
        picked = picked[:n]
    elif len(picked) < n:
        rest = [q for q in unique if q["eval_id"] not in seen]
        rng.shuffle(rest)
        for row in rest:
            if len(picked) >= n:
                break
            picked.append(row)
            seen.add(row["eval_id"])
    return picked
