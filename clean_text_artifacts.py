#!/usr/bin/env python3
"""
Final text artifact cleanup, tail-chunk merge, and corpus re-embedding.

Usage:
  python clean_text_artifacts.py --all --dry-run
  python clean_text_artifacts.py --all --embed
  python clean_text_artifacts.py --urls-file data/reports/validation_sample_20.md --embed
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "apps" / "api"))

from app import ssl_bundle  # noqa: E402

ssl_bundle.apply_corporate_ssl_bundle()

from sqlalchemy import text  # noqa: E402

from app.db.session import SessionLocal  # noqa: E402
from app.services.embedding import (  # noqa: E402
    EMBEDDING_DIMENSIONS,
    EMBEDDING_MODEL,
    EMBED_BATCH_PAUSE_S,
    EMBED_BATCH_SIZE,
    embed_texts_async,
    vector_literal,
)
from app.services.quality_gates import count_tokens  # noqa: E402
from app.services.rag_text_sanitizer import sanitize_for_rag  # noqa: E402
from sanitize_chunks import (  # noqa: E402
    is_prunable_tail,
    merge_tail_chunks,
    parse_urls_from_markdown,
)

logger = logging.getLogger("clean_text_artifacts")

REFRESH_SOURCE = "clean_text_artifacts"
TAIL_MIN_TOKENS = 150
MAX_MERGED_TOKENS = 600

EMPTY_HEADER_RE = re.compile(r"^\s*#{1,6}\s*$\n?", re.M)
EMPTY_TABLE_ROW_RE = re.compile(r"\|\s*\|\s*\n")
TABLE_SEPARATOR_RE = re.compile(r"^(?:\|\s*:?-+:?\s*)+\|\s*$\n?", re.M)
TRAILING_ORPHAN_RE = re.compile(
    r"\n+(?:catalog\.|cloud\.|reporting tools|/unit|content|\*\*\*\*)\s*$",
    re.I,
)
TRAILING_ASTERISKS_RE = re.compile(r"\*+$")


@dataclass
class CleanStats:
    urls_processed: int = 0
    urls_updated: int = 0
    chunks_before: int = 0
    chunks_after: int = 0
    empty_headers_removed: int = 0
    empty_table_rows_removed: int = 0
    table_separators_removed: int = 0
    trailing_orphans_removed: int = 0
    trailing_asterisks_trimmed: int = 0
    tails_merged: int = 0
    tails_pruned: int = 0
    chunks_embedded: int = 0
    urls_marked_embedded: int = 0

    def to_dict(self) -> dict:
        return {
            "urls_processed": self.urls_processed,
            "urls_updated": self.urls_updated,
            "chunks_before": self.chunks_before,
            "chunks_after": self.chunks_after,
            "empty_headers_removed": self.empty_headers_removed,
            "empty_table_rows_removed": self.empty_table_rows_removed,
            "table_separators_removed": self.table_separators_removed,
            "trailing_orphans_removed": self.trailing_orphans_removed,
            "trailing_asterisks_trimmed": self.trailing_asterisks_trimmed,
            "tails_merged": self.tails_merged,
            "tails_pruned": self.tails_pruned,
            "chunks_embedded": self.chunks_embedded,
            "urls_marked_embedded": self.urls_marked_embedded,
        }


def _count_and_sub(pattern: re.Pattern[str], text: str) -> tuple[str, int]:
    matches = pattern.findall(text)
    if not matches:
        return text, 0
    return pattern.sub("", text), len(matches)


def clean_chunk_text(text: str, stats: CleanStats) -> str:
    cleaned = text or ""

    cleaned, n = _count_and_sub(EMPTY_HEADER_RE, cleaned)
    stats.empty_headers_removed += n

    cleaned, n = _count_and_sub(EMPTY_TABLE_ROW_RE, cleaned)
    stats.empty_table_rows_removed += n

    cleaned, n = _count_and_sub(TABLE_SEPARATOR_RE, cleaned)
    stats.table_separators_removed += n

    if TRAILING_ORPHAN_RE.search(cleaned):
        new = TRAILING_ORPHAN_RE.sub("", cleaned)
        if new != cleaned:
            stats.trailing_orphans_removed += 1
            cleaned = new

    stripped = cleaned.rstrip()
    if TRAILING_ASTERISKS_RE.search(stripped):
        new = TRAILING_ASTERISKS_RE.sub("", stripped).rstrip()
        if new != stripped:
            stats.trailing_asterisks_trimmed += 1
            cleaned = new

    return sanitize_for_rag(cleaned)


def clean_document_chunks(chunks: list[str], stats: CleanStats) -> list[str]:
    cleaned = [clean_chunk_text(c, stats) for c in chunks if (c or "").strip()]
    cleaned = [c for c in cleaned if c.strip()]
    if not cleaned:
        return cleaned

    merged = merge_tail_chunks(cleaned, stats)  # type: ignore[arg-type]
    return [c for c in merged if c.strip()]


async def load_target_urls(
    *,
    all_urls: bool,
    urls: list[str],
    limit_urls: int | None,
) -> list[dict]:
    async with SessionLocal() as db:
        if urls:
            rows = await db.execute(
                text("""
                    SELECT id, url, title, service_category, page_type, is_primary_candidate
                    FROM dataset_urls
                    WHERE url = ANY(:urls)
                    ORDER BY url
                """),
                {"urls": urls},
            )
        elif all_urls:
            sql = """
                SELECT du.id, du.url, du.title, du.service_category, du.page_type, du.is_primary_candidate
                FROM dataset_urls du
                WHERE EXISTS (SELECT 1 FROM document_chunks dc WHERE dc.url = du.url)
                ORDER BY du.url
            """
            if limit_urls:
                sql += " LIMIT :limit"
                rows = await db.execute(text(sql), {"limit": limit_urls})
            else:
                rows = await db.execute(text(sql))
        else:
            return []
        return [dict(r) for r in rows.mappings()]


async def load_chunks(db, url: str) -> list[str]:
    rows = await db.execute(
        text("SELECT chunk_text FROM document_chunks WHERE url = :url ORDER BY chunk_index"),
        {"url": url},
    )
    return [r["chunk_text"] or "" for r in rows.mappings()]


async def persist_chunks(db, row: dict, chunks: list[str]) -> None:
    url = row["url"]
    await db.execute(text("DELETE FROM document_chunks WHERE url = :url"), {"url": url})
    for idx, chunk in enumerate(chunks):
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
    full_text = "\n\n".join(chunks)
    await db.execute(
        text("""
            UPDATE dataset_urls SET
                ingestion_status = 'chunked',
                text_content = :text_content,
                chunk_count = :chunk_count,
                last_error = NULL,
                text_quality = COALESCE(text_quality, '{}'::jsonb)
                    || jsonb_build_object(
                        'artifact_cleaned_at', CAST(:ts AS text),
                        'artifact_clean_source', CAST(:src AS text)
                    ),
                updated_at = CURRENT_TIMESTAMP
            WHERE id = :id
        """),
        {
            "id": row["id"],
            "text_content": full_text,
            "chunk_count": len(chunks),
            "ts": datetime.now(timezone.utc).isoformat(),
            "src": REFRESH_SOURCE,
        },
    )


async def run_cleanup(
    rows: list[dict],
    *,
    dry_run: bool,
) -> CleanStats:
    stats = CleanStats()
    async with SessionLocal() as db:
        for row in rows:
            stats.urls_processed += 1
            old_chunks = await load_chunks(db, row["url"])
            stats.chunks_before += len(old_chunks)
            if not old_chunks:
                continue

            new_chunks = clean_document_chunks(old_chunks, stats)
            stats.chunks_after += len(new_chunks)

            changed = (
                len(new_chunks) != len(old_chunks)
                or any(a != b for a, b in zip(new_chunks, old_chunks))
            )
            if not changed:
                continue

            if dry_run:
                print(f"  {row['url']}: {len(old_chunks)} → {len(new_chunks)} chunks")
                continue

            await persist_chunks(db, row, new_chunks)
            stats.urls_updated += 1

        if not dry_run:
            await db.commit()
    return stats


async def fetch_pending_chunks(db) -> list[dict]:
    row = await db.execute(
        text("""
            SELECT id, url, chunk_index, chunk_text
            FROM document_chunks
            WHERE embedding IS NULL
            ORDER BY id
        """)
    )
    return [dict(r) for r in row.mappings()]


async def persist_embedding_batch(db, chunks: list[dict], vectors: list[list[float]]) -> None:
    for chunk, vector in zip(chunks, vectors):
        await db.execute(
            text("""
                UPDATE document_chunks
                SET embedding = CAST(:vec AS vector),
                    token_count = :tokens,
                    metadata = COALESCE(metadata, '{}'::jsonb)
                        || jsonb_build_object('embedded', true, 'embedding_model', CAST(:model AS text))
                WHERE id = :id
            """),
            {
                "vec": vector_literal(vector),
                "id": chunk["id"],
                "tokens": count_tokens(chunk["chunk_text"]),
                "model": EMBEDDING_MODEL,
            },
        )


async def mark_urls_embedded(db, urls: list[str]) -> int:
    if not urls:
        return 0
    result = await db.execute(
        text("""
            UPDATE dataset_urls du
            SET ingestion_status = 'embedded',
                updated_at = CURRENT_TIMESTAMP
            WHERE du.url = ANY(:urls)
              AND NOT EXISTS (
                  SELECT 1 FROM document_chunks dc
                  WHERE dc.url = du.url AND dc.embedding IS NULL
              )
        """),
        {"urls": urls},
    )
    return result.rowcount or 0


async def run_embedding(stats: CleanStats) -> None:
    async with SessionLocal() as db:
        pending = await fetch_pending_chunks(db)
        if not pending:
            logger.info("No chunks pending embedding")
            return

        total = len(pending)
        affected_urls: set[str] = set()
        logger.info("Embedding %s chunks (%s)", total, EMBEDDING_MODEL)

        for start in range(0, total, EMBED_BATCH_SIZE):
            batch = pending[start : start + EMBED_BATCH_SIZE]
            vectors = await embed_texts_async([c["chunk_text"] for c in batch])
            if len(vectors) != len(batch):
                raise RuntimeError(f"embedding count mismatch: got {len(vectors)} expected {len(batch)}")
            if any(len(v) != EMBEDDING_DIMENSIONS for v in vectors):
                raise RuntimeError("unexpected embedding dimension from OpenAI")

            await persist_embedding_batch(db, batch, vectors)
            affected_urls.update(c["url"] for c in batch)
            stats.chunks_embedded += len(batch)
            stats.urls_marked_embedded = await mark_urls_embedded(db, list(affected_urls))
            await db.commit()
            logger.info("Embedded %s/%s chunks (%.1f%%)", stats.chunks_embedded, total, 100.0 * stats.chunks_embedded / total)
            if start + EMBED_BATCH_SIZE < total:
                await asyncio.sleep(EMBED_BATCH_PAUSE_S)


async def vector_store_readiness() -> dict:
    async with SessionLocal() as db:
        row = await db.execute(
            text("""
                SELECT
                    (SELECT COUNT(*) FROM document_chunks) AS total_chunks,
                    (SELECT COUNT(*) FROM document_chunks WHERE embedding IS NOT NULL) AS embedded_chunks,
                    (SELECT COUNT(DISTINCT url) FROM document_chunks) AS urls_with_chunks,
                    (SELECT COUNT(*) FROM dataset_urls WHERE ingestion_status = 'embedded') AS urls_embedded,
                    (SELECT COUNT(*) FROM dataset_urls WHERE ingestion_status = 'chunked') AS urls_chunked,
                    (SELECT COUNT(*) FROM dataset_urls WHERE ingestion_status = 'pending') AS urls_pending
            """)
        )
        metrics = dict(row.mappings().first())
        total = int(metrics["total_chunks"] or 0)
        embedded = int(metrics["embedded_chunks"] or 0)
        metrics["vector_store_ready"] = total > 0 and embedded == total
        metrics["embedding_coverage_pct"] = round(100.0 * embedded / total, 2) if total else 0.0
        return metrics


def write_audit_report(
    stats: CleanStats,
    readiness: dict,
    *,
    scope: str,
    out_json: Path,
    out_md: Path,
) -> None:
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "scope": scope,
        "embedding_model": EMBEDDING_MODEL,
        "embedding_dimensions": EMBEDDING_DIMENSIONS,
        **stats.to_dict(),
        "vector_store": readiness,
    }
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    ready = readiness.get("vector_store_ready", False)
    status = "READY" if ready else "INCOMPLETE"
    lines = [
        "# Text Artifact Cleanup & Re-Embedding Audit",
        "",
        f"Generated: {payload['generated_at']}",
        f"Scope: **{scope}**",
        f"Embedding model: `{EMBEDDING_MODEL}` ({EMBEDDING_DIMENSIONS}d)",
        "",
        "## Regex & artifact cleanup",
        "",
        "| Metric | Count |",
        "|--------|------:|",
        f"| Empty markdown headers (`###`) removed | {stats.empty_headers_removed} |",
        f"| Empty markdown table rows stripped | {stats.empty_table_rows_removed} |",
        f"| Table separator skeletons stripped | {stats.table_separators_removed} |",
        f"| Trailing orphan token fragments removed | {stats.trailing_orphans_removed} |",
        f"| Trailing unescaped asterisks trimmed | {stats.trailing_asterisks_trimmed} |",
        "",
        "## Tail chunk merge / prune",
        "",
        "| Metric | Count |",
        "|--------|------:|",
        f"| Tail chunks merged (< {TAIL_MIN_TOKENS} tokens) | {stats.tails_merged} |",
        f"| Tail chunks pruned (footer/nav/table noise) | {stats.tails_pruned} |",
        "",
        "## Corpus delta",
        "",
        "| Metric | Count |",
        "|--------|------:|",
        f"| URLs processed | {stats.urls_processed} |",
        f"| URLs updated | {stats.urls_updated} |",
        f"| Chunks before | {stats.chunks_before} |",
        f"| Chunks after | {stats.chunks_after} |",
        f"| Net chunk delta | {stats.chunks_after - stats.chunks_before} |",
        "",
        "## Embedding pass",
        "",
        f"| Metric | Count |",
        f"|--------|------:|",
        f"| Chunks embedded | {stats.chunks_embedded} |",
        f"| URLs marked embedded | {stats.urls_marked_embedded} |",
        "",
        "## Vector store readiness",
        "",
        f"**Status: {status}**",
        "",
        f"| Metric | Value |",
        f"|--------|------:|",
        f"| Total chunks | {readiness.get('total_chunks', 0)} |",
        f"| Embedded chunks | {readiness.get('embedded_chunks', 0)} |",
        f"| Coverage | {readiness.get('embedding_coverage_pct', 0)}% |",
        f"| URLs embedded | {readiness.get('urls_embedded', 0)} |",
        f"| URLs chunked (no vectors) | {readiness.get('urls_chunked', 0)} |",
        f"| URLs pending | {readiness.get('urls_pending', 0)} |",
        "",
    ]
    out_md.write_text("\n".join(lines), encoding="utf-8")


async def main_async(args: argparse.Namespace) -> int:
    urls: list[str] = []
    if args.urls_file:
        urls = parse_urls_from_markdown(args.urls_file)
    if args.url:
        urls.append(args.url)

    if not args.all and not urls:
        print("Specify --all or --urls-file / --url", file=sys.stderr)
        return 1

    scope = "full_corpus" if args.all and not urls else f"{len(urls)}_urls"
    rows = await load_target_urls(all_urls=args.all, urls=urls, limit_urls=args.limit_urls)
    if not rows:
        print("No URLs to process", file=sys.stderr)
        return 1

    print(f"Cleaning {len(rows)} URL(s) dry_run={args.dry_run}")
    stats = await run_cleanup(rows, dry_run=args.dry_run)

    if args.embed and not args.dry_run:
        await run_embedding(stats)
    elif args.embed and args.dry_run:
        print("Skipping embedding (dry-run)")

    readiness = await vector_store_readiness()
    if not args.dry_run:
        stats.chunks_after = int(readiness.get("total_chunks") or stats.chunks_after)

    out_json = args.json or ROOT / "data" / "reports" / "artifact_cleanup_audit.json"
    out_md = args.audit_md or ROOT / "data" / "reports" / "artifact_cleanup_audit.md"
    write_audit_report(stats, readiness, scope=scope, out_json=out_json, out_md=out_md)

    print(json.dumps({**stats.to_dict(), "vector_store": readiness}, indent=2))
    print(f"\nAudit: {out_md}")
    return 0


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    parser = argparse.ArgumentParser(description="Clean text artifacts, merge tails, re-embed corpus")
    parser.add_argument("--all", action="store_true", help="Process every URL with document_chunks")
    parser.add_argument("--urls-file", type=Path)
    parser.add_argument("--url")
    parser.add_argument("--limit-urls", type=int, help="Cap URLs when using --all")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--embed",
        action="store_true",
        help="Re-embed chunks after cleanup (off by default — run only after text verification)",
    )
    parser.add_argument("--json", type=Path)
    parser.add_argument("--audit-md", type=Path)
    args = parser.parse_args()
    return asyncio.run(main_async(args))


if __name__ == "__main__":
    raise SystemExit(main())
