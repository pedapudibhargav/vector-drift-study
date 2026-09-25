#!/usr/bin/env python3
"""Okapi BM25 lexical control on the primary-200 bank (full scale ladder).

Answers the IEEE-review RQ2 gap: Postgres FTS is a weak negative control;
this script runs classic Okapi BM25 (rank_bm25) over the same gold-pinned
scale_rank < N document sets as the dense ladder.

Usage:
  DATABASE_URL=postgresql://vector_drift:vector_drift@localhost:5432/vector_drift \\
    ./.venv/bin/python scripts/erb/run_bm25_baseline.py

  ./.venv/bin/python scripts/erb/run_bm25_baseline.py --scales 5000,10000,50000,100000
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

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from paths import DEFAULT_SCALES, ERB_MANIFEST, api_pythonpath  # noqa: E402

PUB = ROOT / "artifacts" / "published"
PRIMARY = PUB / "primary_questions_eval.json"
TOKEN_RE = re.compile(r"[a-z0-9]+")


def _load_env() -> None:
    for env_path in (ROOT / ".env", Path("/app/.env")):
        if not env_path.exists():
            continue
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
        break
    url = os.environ.get("DATABASE_URL", "")
    if "vector-drift-db" in url:
        os.environ["DATABASE_URL"] = url.replace("vector-drift-db", "localhost")


def _db_url() -> str:
    url = os.environ.get(
        "DATABASE_URL",
        "postgresql://vector_drift:vector_drift@localhost:5432/vector_drift",
    )
    return url.replace("postgresql+asyncpg://", "postgresql://")


def tokenize(text: str) -> list[str]:
    return TOKEN_RE.findall((text or "").lower())


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--scales",
        default=",".join(str(s) for s in DEFAULT_SCALES),
        help="Comma-separated N values",
    )
    parser.add_argument("--top-k", type=int, default=10)
    parser.add_argument("--max-chars", type=int, default=4000, help="Truncate doc text for BM25")
    args = parser.parse_args()
    _load_env()

    try:
        import psycopg2
        from rank_bm25 import BM25Okapi
    except ImportError as exc:
        raise SystemExit(
            f"Missing dependency: {exc}. Install with: "
            "pip install rank_bm25 psycopg2-binary"
        ) from exc

    scales = [int(x) for x in args.scales.split(",") if x.strip()]
    max_n = max(scales)

    primary = json.loads(PRIMARY.read_text(encoding="utf-8"))
    qids = list(primary["question_ids"])
    man = json.loads(ERB_MANIFEST.read_text(encoding="utf-8"))
    qmap = {q["question_id"]: q for q in man["questions"]}
    questions = [qmap[qid] for qid in qids if qid in qmap]
    if len(questions) != 200:
        raise SystemExit(f"expected 200 primary questions, got {len(questions)}")

    print(f"loading docs scale_rank < {max_n} …", flush=True)
    t0 = time.time()
    conn = psycopg2.connect(_db_url())
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
        rows = cur.fetchall()
    finally:
        conn.close()
    print(f"loaded {len(rows)} docs in {time.time()-t0:.1f}s", flush=True)

    # Pre-tokenize once; slice by scale_rank for each N
    ranks: list[int] = []
    doc_ids: list[str] = []
    corpus_tokens: list[list[str]] = []
    for scale_rank, doc_id, text in rows:
        ranks.append(int(scale_rank))
        doc_ids.append(str(doc_id))
        corpus_tokens.append(tokenize(str(text)[: args.max_chars]))

    # End index exclusive for each scale (first position where rank >= N)
    def end_idx(n: int) -> int:
        # ranks are sorted ascending
        lo, hi = 0, len(ranks)
        while lo < hi:
            mid = (lo + hi) // 2
            if ranks[mid] < n:
                lo = mid + 1
            else:
                hi = mid
        return lo

    runs: list[dict] = []
    for n in scales:
        e = end_idx(n)
        toks = corpus_tokens[:e]
        ids = doc_ids[:e]
        if e == 0:
            raise SystemExit(f"no docs for N={n}")
        print(f"BM25 N={n} docs={e} …", flush=True)
        t1 = time.time()
        bm25 = BM25Okapi(toks)
        hit1 = hit5 = hit10 = 0
        recall_sum = mrr_sum = 0.0
        per_q: list[dict] = []
        for q in questions:
            expected = {str(x) for x in (q.get("expected_doc_ids") or []) if x}
            if not expected:
                continue
            scores = bm25.get_scores(tokenize(q["question"]))
            # top-k indices
            if len(scores) <= args.top_k:
                top_idx = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)
            else:
                # partial select
                import numpy as np

                arr = np.asarray(scores)
                top_idx = np.argpartition(arr, -args.top_k)[-args.top_k :]
                top_idx = top_idx[np.argsort(arr[top_idx])[::-1]].tolist()
            retrieved = [ids[i] for i in top_idx]
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
                }
            )
        nq = len(per_q) or 1
        summary = {
            "condition": "bm25_okapi",
            "method": "rank_bm25.BM25Okapi",
            "corpus_scale_size": n,
            "n_docs": e,
            "questions_evaluated": len(per_q),
            "hit_at_1": round(hit1 / nq, 4),
            "hit_at_5": round(hit5 / nq, 4),
            "hit_at_10": round(hit10 / nq, 4),
            "document_recall": round(recall_sum / nq, 4),
            "mrr": round(mrr_sum / nq, 4),
            "elapsed_s": round(time.time() - t1, 1),
            "per_question": per_q,
        }
        print(
            f"  Hit@10={summary['hit_at_10']:.3f} Hit@1={summary['hit_at_1']:.3f} "
            f"MRR={summary['mrr']:.3f} ({summary['elapsed_s']}s)",
            flush=True,
        )
        runs.append(summary)

    report = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "method": "Okapi BM25 (rank_bm25.BM25Okapi) on title+chunk_text truncated",
        "max_chars": args.max_chars,
        "primary_n": 200,
        "scales": scales,
        "runs": [{k: v for k, v in r.items() if k != "per_question"} for r in runs],
        "per_question_by_scale": {
            str(r["corpus_scale_size"]): r["per_question"] for r in runs
        },
        "paper_note": (
            "RQ2 control: classic Okapi BM25 on the same gold-pinned ladder as dense HNSW. "
            "Compare Hit@10 decline vs dense; if BM25 stays flat/near-floor while dense falls "
            "from a high baseline, the measured drift curve is dense-stack-specific on this bank."
        ),
    }
    PUB.mkdir(parents=True, exist_ok=True)
    out = PUB / "erb_bm25_baseline_primary200.json"
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    md = [
        "# Okapi BM25 baseline (primary-200)",
        "",
        report["paper_note"],
        "",
        "| N | docs | Hit@1 | Hit@5 | Hit@10 | MRR |",
        "|---|------|-------|-------|--------|-----|",
    ]
    for r in runs:
        md.append(
            f"| {r['corpus_scale_size']} | {r['n_docs']} | {r['hit_at_1']} | "
            f"{r['hit_at_5']} | {r['hit_at_10']} | {r['mrr']} |"
        )
    md_path = PUB / "erb_bm25_baseline_primary200.md"
    md_path.write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"wrote {out}")
    print(f"wrote {md_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
