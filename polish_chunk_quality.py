#!/usr/bin/env python3
"""
In-DB chunk polish: sanitize text, merge micro-chunks, re-split — no Playwright.

Usage:
  python polish_chunk_quality.py --all
  python polish_chunk_quality.py --url "https://aws.amazon.com/..."
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "apps" / "api"))

from app import ssl_bundle  # noqa: E402

ssl_bundle.apply_corporate_ssl_bundle()

from sqlalchemy import text  # noqa: E402

from app.db.session import SessionLocal  # noqa: E402
from app.services.dynamic_crawl import chunk_defects, sanitize_extracted_text  # noqa: E402
from app.services.quality_gates import (  # noqa: E402
    count_tokens,
    merge_and_polish_chunks,
    validate_chunks,
)

REFRESH_SOURCE = "polish_chunk_quality"


async def load_urls(url: str | None) -> list[dict]:
    async with SessionLocal() as db:
        if url:
            rows = await db.execute(
                text("""
                    SELECT id, url, title, service_category, page_type, is_primary_candidate
                    FROM dataset_urls WHERE url = :url
                """),
                {"url": url},
            )
        else:
            rows = await db.execute(
                text("""
                    SELECT id, url, title, service_category, page_type, is_primary_candidate
                    FROM dataset_urls
                    WHERE ingestion_status IN ('chunked', 'embedded', 'text_failed')
                    ORDER BY url
                """)
            )
        return [dict(r) for r in rows.mappings()]


async def load_chunks_for_url(db, url: str) -> list[str]:
    rows = await db.execute(
        text("""
            SELECT chunk_text FROM document_chunks
            WHERE url = :url ORDER BY chunk_index
        """),
        {"url": url},
    )
    return [r["chunk_text"] or "" for r in rows.mappings()]


async def polish_url(db, row: dict) -> dict:
    url = row["url"]
    old_chunks = await load_chunks_for_url(db, url)
    if not old_chunks:
        return {"url": url, "skipped": True, "reason": "no_chunks"}

    new_chunks = merge_and_polish_chunks(old_chunks)
    ok, gate = validate_chunks(new_chunks)
    if not ok:
        return {"url": url, "skipped": True, "reason": gate.get("reason", "validate_failed")}

    full_text = sanitize_extracted_text("\n\n".join(new_chunks))
    await db.execute(text("DELETE FROM document_chunks WHERE url = :url"), {"url": url})
    for idx, chunk in enumerate(new_chunks):
        await db.execute(
            text("""
                INSERT INTO document_chunks (url, title, chunk_index, chunk_text, token_count, metadata, embedding)
                VALUES (:url, :title, :idx, :text, :tokens, :meta, NULL)
            """),
            {
                "url": url,
                "title": row.get("title"),
                "idx": idx,
                "text": chunk,
                "tokens": count_tokens(chunk),
                "meta": json.dumps({
                    "service_category": row.get("service_category"),
                    "page_type": row.get("page_type"),
                    "is_primary": row.get("is_primary_candidate"),
                    "embedded": False,
                    "refreshed_by": REFRESH_SOURCE,
                }),
            },
        )

    status_row = await db.execute(
        text("SELECT ingestion_status FROM dataset_urls WHERE id = :id"),
        {"id": row["id"]},
    )
    current = status_row.scalar_one()
    new_status = "chunked" if current == "embedded" else current
    if current == "text_failed":
        new_status = "chunked"

    await db.execute(
        text("""
            UPDATE dataset_urls SET
                text_content = :text_content,
                chunk_count = :chunk_count,
                ingestion_status = :status,
                last_error = NULL,
                text_quality = COALESCE(text_quality, '{}'::jsonb)
                    || jsonb_build_object(
                        'polished_at', CAST(:ts AS text),
                        'polish_source', CAST(:src AS text)
                    ),
                updated_at = CURRENT_TIMESTAMP
            WHERE id = :id
        """),
        {
            "id": row["id"],
            "text_content": full_text,
            "chunk_count": len(new_chunks),
            "status": new_status,
            "ts": datetime.now(timezone.utc).isoformat(),
            "src": REFRESH_SOURCE,
        },
    )
    await db.commit()
    return {
        "url": url,
        "old_chunks": len(old_chunks),
        "new_chunks": len(new_chunks),
        "updated": True,
    }


async def run_polish(url: str | None) -> dict:
    urls = await load_urls(url)
    stats = {"urls": len(urls), "updated": 0, "skipped": 0, "errors": 0}
    async with SessionLocal() as db:
        for row in urls:
            try:
                result = await polish_url(db, row)
                if result.get("updated"):
                    stats["updated"] += 1
                else:
                    stats["skipped"] += 1
            except Exception as exc:
                stats["errors"] += 1
                await db.rollback()
                print(f"  ✗ {row['url']}: {exc}")
    return stats


def main() -> int:
    parser = argparse.ArgumentParser(description="Polish chunks in PostgreSQL")
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--url")
    args = parser.parse_args()
    if not args.all and not args.url:
        parser.error("use --all or --url")
    stats = asyncio.run(run_polish(args.url))
    print(json.dumps(stats, indent=2))
    return 0 if stats["errors"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
