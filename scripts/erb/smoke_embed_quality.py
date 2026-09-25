#!/usr/bin/env python3
"""Continuous smoke checks for OpenAI + Ollama ERB embedding arms.

Writes data/erb_smoke_status.json and appends data/results/erb_smoke_log.jsonl.
Exit 0 always when used as a watcher (unless --fail-hard).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from paths import DATA_DIR, ERB_INGEST_CHECKPOINT, ERB_MANIFEST  # noqa: E402

OLLAMA_CKPT = DATA_DIR / "erb_ollama_ingest_checkpoint.json"
STATUS = DATA_DIR / "erb_smoke_status.json"
LOG = DATA_DIR / "results" / "erb_smoke_log.jsonl"


def _db_url() -> str:
    return os.environ.get(
        "DATABASE_URL",
        "postgresql://vector_drift:vector_drift@localhost:5432/vector_drift",
    ).replace("postgresql+asyncpg://", "postgresql://")


def _ckpt_count(path: Path) -> int:
    if not path.exists():
        return 0
    try:
        return int(json.loads(path.read_text()).get("count") or 0)
    except Exception:
        return 0


def check_once() -> dict:
    import psycopg

    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    report: dict = {"ts": now, "ok": True, "errors": [], "openai": {}, "ollama": {}}

    openai_ckpt = _ckpt_count(ERB_INGEST_CHECKPOINT)
    ollama_ckpt = _ckpt_count(OLLAMA_CKPT)

    with psycopg.connect(_db_url()) as conn:
        with conn.cursor() as cur:
            # OpenAI table
            cur.execute(
                """
                SELECT COUNT(*), COUNT(DISTINCT doc_id), COUNT(DISTINCT url),
                       COUNT(*) FILTER (WHERE embedding IS NULL),
                       COUNT(*) FILTER (WHERE chunk_text IS NULL OR length(trim(chunk_text))=0),
                       COUNT(*) FILTER (WHERE is_gold_anchor),
                       COUNT(*) FILTER (WHERE scale_rank < 100000)
                FROM document_chunks
                """
            )
            rows, dist_doc, dist_url, null_e, empty, gold, under = cur.fetchone()
            cur.execute(
                """
                SELECT COUNT(*) FROM (
                  SELECT scale_rank FROM document_chunks
                  WHERE scale_rank IS NOT NULL GROUP BY 1 HAVING COUNT(*)>1
                ) s
                """
            )
            sr_dups = cur.fetchone()[0]
            dim = None
            try:
                cur.execute("SELECT vector_dims(embedding) FROM document_chunks LIMIT 1")
                r = cur.fetchone()
                dim = int(r[0]) if r else None
            except Exception:
                pass

            report["openai"] = {
                "ckpt": openai_ckpt,
                "rows": rows,
                "distinct_doc": dist_doc,
                "null_emb": null_e,
                "empty_text": empty,
                "gold": gold,
                "under_100k": under,
                "scale_rank_dups": sr_dups,
                "dim": dim,
            }
            if rows != dist_doc or rows != dist_url:
                report["ok"] = False
                report["errors"].append(f"openai dup rows={rows} doc={dist_doc} url={dist_url}")
            if null_e or empty:
                report["ok"] = False
                report["errors"].append(f"openai null_emb={null_e} empty={empty}")
            if sr_dups:
                report["ok"] = False
                report["errors"].append(f"openai scale_rank_dups={sr_dups}")
            if dim not in (None, 1536):
                report["ok"] = False
                report["errors"].append(f"openai dim={dim}")

            # Ollama table (may be empty at start)
            cur.execute(
                """
                SELECT EXISTS (
                  SELECT 1 FROM information_schema.tables
                  WHERE table_name='document_chunks_ollama'
                )
                """
            )
            has_ollama = bool(cur.fetchone()[0])
            if has_ollama:
                cur.execute(
                    """
                    SELECT COUNT(*), COUNT(DISTINCT doc_id),
                           COUNT(*) FILTER (WHERE embedding IS NULL),
                           COUNT(*) FILTER (WHERE chunk_text IS NULL OR length(trim(chunk_text))=0)
                    FROM document_chunks_ollama
                    """
                )
                orows, odist, onull, oempty = cur.fetchone()
                odim = None
                if orows:
                    cur.execute(
                        "SELECT vector_dims(embedding) FROM document_chunks_ollama LIMIT 1"
                    )
                    r = cur.fetchone()
                    odim = int(r[0]) if r else None
                report["ollama"] = {
                    "ckpt": ollama_ckpt,
                    "rows": orows,
                    "distinct_doc": odist,
                    "null_emb": onull,
                    "empty_text": oempty,
                    "dim": odim,
                }
                if orows != odist:
                    report["ok"] = False
                    report["errors"].append(f"ollama dup rows={orows} doc={odist}")
                if onull or oempty:
                    report["ok"] = False
                    report["errors"].append(f"ollama null_emb={onull} empty={oempty}")
                if odim not in (None, 768):
                    report["ok"] = False
                    report["errors"].append(f"ollama dim={odim}")
            else:
                report["ollama"] = {"table": False, "ckpt": ollama_ckpt}

            # Gold anchors present for first 5k scale (retrieval safety)
            cur.execute(
                """
                SELECT COUNT(*) FROM document_chunks
                WHERE is_gold_anchor AND scale_rank < 5000
                """
            )
            gold_in_5k = cur.fetchone()[0]
            report["gold_anchors_in_5k"] = gold_in_5k
            if gold_in_5k < 1:
                report["ok"] = False
                report["errors"].append("no gold anchors in scale_rank<5000")

    STATUS.write_text(json.dumps(report, indent=2))
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(report) + "\n")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--interval", type=int, default=120, help="seconds between checks")
    parser.add_argument("--fail-hard", action="store_true")
    args = parser.parse_args()

    while True:
        try:
            report = check_once()
            flag = "OK" if report["ok"] else "FAIL"
            o = report.get("openai", {})
            a = report.get("ollama", {})
            print(
                f"SMOKE[{flag}] openai={o.get('rows')} ollama={a.get('rows')} "
                f"err={report.get('errors')}",
                flush=True,
            )
            if args.fail_hard and not report["ok"]:
                return 1
        except Exception as exc:  # noqa: BLE001
            print(f"SMOKE[ERROR] {exc}", flush=True)
            if args.fail_hard:
                return 1
        if args.once:
            return 0 if report.get("ok", False) or not args.fail_hard else 1
        time.sleep(max(30, args.interval))


if __name__ == "__main__":
    raise SystemExit(main())
