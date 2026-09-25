#!/usr/bin/env python3
"""Export L4 audit report from study_evaluations → artifacts/published/."""

from __future__ import annotations

import csv
import json
import os
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "artifacts" / "published"


def main() -> int:
    import psycopg

    url = os.environ.get(
        "DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/vector_drift_db",
    ).replace("postgresql+asyncpg://", "postgresql://")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with psycopg.connect(url) as conn:
        rows = conn.execute(
            """
            SELECT s.question_id, s.corpus_scale_size, s.condition,
                   s.hit_at_10, s.rank, s.document_recall,
                   s.expected_doc_ids, s.retrieved_doc_ids,
                   e.evaluator_kind, e.auditor_id, e.label_correct, e.failure_mode,
                   e.notes, e.status, e.relevance_score, e.reasoning_summary,
                   e.model, e.cost_usd, e.updated_at
            FROM audit_samples s
            LEFT JOIN study_evaluations e
              ON e.eval_scope = 'retrieval_row'
             AND e.question_id = s.question_id
             AND e.corpus_scale_size = s.corpus_scale_size
             AND e.condition = s.condition
             AND e.auditor_id <> '_template'
            ORDER BY s.corpus_scale_size, s.question_id, e.evaluator_kind, e.auditor_id
            """
        ).fetchall()
        cols = [
            "question_id",
            "corpus_scale_size",
            "condition",
            "hit_at_10",
            "rank",
            "document_recall",
            "expected_doc_ids",
            "retrieved_doc_ids",
            "evaluator_kind",
            "auditor_id",
            "label_correct",
            "failure_mode",
            "notes",
            "status",
            "relevance_score",
            "reasoning_summary",
            "model",
            "cost_usd",
            "updated_at",
        ]
        records = []
        for tup in rows:
            d = dict(zip(cols, tup, strict=True))
            for k in ("expected_doc_ids", "retrieved_doc_ids"):
                v = d.get(k)
                if isinstance(v, list):
                    d[k] = "|".join(str(x) for x in v)
                elif v is not None and not isinstance(v, str):
                    d[k] = json.dumps(v)
            if d.get("updated_at") is not None:
                d["updated_at"] = d["updated_at"].isoformat()
            if d.get("cost_usd") is not None:
                d["cost_usd"] = float(d["cost_usd"])
            records.append(d)

        spent = conn.execute("SELECT COALESCE(SUM(cost_usd), 0) FROM audit_cost_ledger").fetchone()
        llm_spent = float(spent[0] if spent else 0)

    human = [r for r in records if r.get("evaluator_kind") == "human" and r.get("label_correct")]
    by_scale: dict[str, dict[str, int]] = {}
    for r in human:
        scale = str(r.get("corpus_scale_size"))
        fm = r.get("failure_mode") or "(none)"
        by_scale.setdefault(scale, {})
        by_scale[scale][fm] = by_scale[scale].get(fm, 0) + 1
    confirmed = sum(1 for r in human if r.get("label_correct") == "y")
    paper_blurb = (
        f"On a stratified audit of {len(human)} labeled retrieval rows "
        f"({confirmed}/{len(human)} confirmed automated Hit@10 labels as fair). "
        f"Failure-mode counts by scale: {json.dumps(by_scale)}."
    )
    summary = {
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "n_human_labels": len(human),
        "n_rows": len(records),
        "by_scale_failure_modes": by_scale,
        "llm_spent_usd": llm_spent,
        "paper_paragraph_draft": paper_blurb,
    }

    csv_path = OUT_DIR / "human_audit_labeled_export.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for r in records:
            w.writerow(r)

    (OUT_DIR / "human_audit_export_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    (OUT_DIR / "human_audit_export.md").write_text(
        "# L4 Human Audit Export\n\n"
        f"_Exported {summary['exported_at']}_\n\n"
        "## Draft paper paragraph\n\n"
        f"{paper_blurb}\n\n"
        f"LLM audit spend: ${llm_spent:.4f}\n",
        encoding="utf-8",
    )
    print(f"wrote {csv_path}")
    print(f"human_labels={len(human)} llm_spent_usd={llm_spent:.4f}")
    print(paper_blurb)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
