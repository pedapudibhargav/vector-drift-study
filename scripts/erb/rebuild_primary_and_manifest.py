#!/usr/bin/env python3
"""Rebuild ERB manifest + unique primary set; assert no question_id collisions.

Run after fixing question_identity (eval_id = question_id::question_type).
"""

from __future__ import annotations

import json
import subprocess
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))

from paths import ERB_MANIFEST, ERB_RESULTS_DIR  # noqa: E402
from question_identity import stratified_unique  # noqa: E402


def main() -> int:
    # Rebuild manifest via existing builder
    rc = subprocess.call([sys.executable, str(Path(__file__).parent / "build_scale_manifest.py")])
    if rc != 0:
        return rc

    man = json.loads(ERB_MANIFEST.read_text(encoding="utf-8"))
    questions = list(man.get("questions") or [])
    ids = [q["question_id"] for q in questions]
    dups = [k for k, v in Counter(ids).items() if v > 1]
    if dups:
        print(f"FAIL: manifest still has duplicate question_id/eval_id: {dups[:10]}", file=sys.stderr)
        return 2
    print(f"manifest ok: {len(questions)} unique eval_ids")

    primary = stratified_unique(questions, 200, seed=42)
    pub = ROOT / "artifacts" / "published"
    pub.mkdir(parents=True, exist_ok=True)
    payload = {
        "seed": 42,
        "count": len(primary),
        "unique_eval_ids": True,
        "source": "stratified_unique(eval_id=question_id::question_type)",
        "question_ids": [q["question_id"] for q in primary],
        "erb_question_ids": [q.get("erb_question_id") for q in primary],
        "question_types": [q.get("question_type") for q in primary],
    }
    out = pub / "primary_questions_200.json"
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    # Keep explicit eval copy too
    (pub / "primary_questions_eval.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"wrote {out} count={len(primary)} unique={len(set(payload['question_ids']))}")

    ERB_RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
