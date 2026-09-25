#!/usr/bin/env python3
"""Sync document_chunks.scale_rank / source_type / is_gold_anchor from current manifest.

Safe to run while ingest continues: updates metadata only (no re-embed).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from paths import ERB_MANIFEST  # noqa: E402


def main() -> int:
    import psycopg

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=ERB_MANIFEST)
    parser.add_argument("--batch-size", type=int, default=2000)
    args = parser.parse_args()

    url = os.environ.get(
        "DATABASE_URL",
        "postgresql://vector_drift:vector_drift@localhost:5432/vector_drift",
    ).replace("postgresql+asyncpg://", "postgresql://")

    docs = json.loads(args.manifest.read_text(encoding="utf-8"))["documents"]
    by_id = {
        d["doc_id"]: (
            int(d["scale_rank"]),
            str(d.get("source_type") or ""),
            bool(d.get("is_gold_anchor")),
        )
        for d in docs
    }
    print(f"manifest docs={len(by_id)}")

    conn = psycopg.connect(url)
    updated = 0
    mismatched = 0
    try:
        rows = conn.execute(
            "SELECT doc_id, scale_rank FROM document_chunks WHERE doc_id IS NOT NULL"
        ).fetchall()
        print(f"db rows={len(rows)}")
        batch: list[tuple] = []
        for doc_id, cur_rank in rows:
            meta = by_id.get(doc_id)
            if not meta:
                continue
            rank, source_type, is_gold = meta
            if cur_rank != rank:
                mismatched += 1
            batch.append((rank, source_type, is_gold, doc_id))
            if len(batch) >= args.batch_size:
                with conn.cursor() as cur:
                    cur.executemany(
                        """
                        UPDATE document_chunks
                        SET scale_rank = %s,
                            source_type = %s,
                            is_gold_anchor = %s,
                            metadata = metadata || jsonb_build_object(
                              'scale_rank', %s::int,
                              'source_type', %s::text,
                              'is_gold_anchor', %s::boolean
                            )
                        WHERE doc_id = %s
                        """,
                        [(r, s, g, r, s, g, did) for (r, s, g, did) in batch],
                    )
                conn.commit()
                updated += len(batch)
                print(f"synced {updated}/{len(rows)}")
                batch = []
        if batch:
            with conn.cursor() as cur:
                cur.executemany(
                    """
                    UPDATE document_chunks
                    SET scale_rank = %s,
                        source_type = %s,
                        is_gold_anchor = %s,
                        metadata = metadata || jsonb_build_object(
                          'scale_rank', %s::int,
                          'source_type', %s::text,
                          'is_gold_anchor', %s::boolean
                        )
                    WHERE doc_id = %s
                    """,
                    [(r, s, g, r, s, g, did) for (r, s, g, did) in batch],
                )
            conn.commit()
            updated += len(batch)

        stats = conn.execute(
            """
            SELECT COUNT(*) AS n,
                   COUNT(DISTINCT scale_rank) AS distinct_ranks,
                   MIN(scale_rank) AS min_r,
                   MAX(scale_rank) AS max_r
            FROM document_chunks
            WHERE embedding IS NOT NULL
            """
        ).fetchone()
        print(
            json.dumps(
                {
                    "updated_rows": updated,
                    "rank_mismatches_before": mismatched,
                    "embedded_n": stats[0],
                    "distinct_ranks": stats[1],
                    "min_rank": stats[2],
                    "max_rank": stats[3],
                },
                indent=2,
            )
        )
    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
