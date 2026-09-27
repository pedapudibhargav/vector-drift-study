#!/usr/bin/env python3
"""Build stratified primary question bank artifacts from the ERB manifest.

Uses ``question_identity.stratified_unique`` on eligible questions in
``data/erb_scale_manifest.json``. Published primary-200 is seed=42, n=200;
primary-400 uses the same question-sample seed with n=400.

Usage:
  ./.venv/bin/python scripts/erb/build_primary_questions.py
  ./.venv/bin/python scripts/erb/build_primary_questions.py --n 400
  ./.venv/bin/python scripts/erb/build_primary_questions.py --n 200 --out artifacts/published/primary_questions_200.json

Endpoint sweep for primary-400 (embeds missing query IDs via API; needs API deps / docker):
  ./.venv/bin/python scripts/erb/run_primary_endpoints.py --primary-n 400

Full ladder:
  docker exec vector-drift-api python /app/scripts/erb/run_primary_endpoints.py \\
    --primary-n 400 --scales 5000 10000 15000 20000 25000 40000 50000 75000 100000 \\
    --out artifacts/published/erb_full_primary400_to100k.json
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))

from paths import ERB_MANIFEST  # noqa: E402
from question_identity import stratified_unique  # noqa: E402


def build_primary_payload(questions: list[dict], n: int, seed: int) -> dict:
    primary = stratified_unique(questions, n, seed=seed)
    ids = [q["question_id"] for q in primary]
    dups = [k for k, v in Counter(ids).items() if v > 1]
    if dups:
        raise SystemExit(f"duplicate eval_ids in sample: {dups[:5]}")
    if len(primary) != n:
        raise SystemExit(f"requested n={n} but stratified_unique returned {len(primary)}")
    return {
        "seed": seed,
        "count": len(primary),
        "unique_eval_ids": True,
        "source": "stratified_unique(eval_id=question_id::question_type)",
        "question_ids": ids,
        "erb_question_ids": [q.get("erb_question_id") for q in primary],
        "question_types": [q.get("question_type") for q in primary],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--manifest", type=Path, default=ERB_MANIFEST)
    parser.add_argument("--n", type=int, default=400, help="Primary bank size (default: 400)")
    parser.add_argument("--seed", type=int, default=42, help="Question-sample seed (default: 42)")
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Output JSON (default: artifacts/published/primary_questions_{n}.json)",
    )
    args = parser.parse_args()

    if not args.manifest.exists():
        raise SystemExit(f"manifest missing: {args.manifest}")

    man = json.loads(args.manifest.read_text(encoding="utf-8"))
    questions = list(man.get("questions") or [])
    eligible = len(questions)
    if args.n > eligible:
        raise SystemExit(f"requested n={args.n} exceeds eligible pool {eligible}")

    payload = build_primary_payload(questions, args.n, args.seed)
    out = args.out or (ROOT / "artifacts" / "published" / f"primary_questions_{args.n}.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"wrote {out} count={payload['count']} eligible_pool={eligible} seed={args.seed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
