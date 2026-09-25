#!/usr/bin/env python3
"""
Re-crawl CSR-heavy AWS pages with Playwright, validate chunks, update PostgreSQL,
re-embed, and refresh vector_drift_results for benchmark-200.

Usage:
  python recrawl_dynamic_pages.py --dry-run
  python recrawl_dynamic_pages.py --limit 50 --no-embed
  python recrawl_dynamic_pages.py --url "https://aws.amazon.com/solutions/ai/chatbots-virtual-assistants"
  python recrawl_dynamic_pages.py --status chunked --embed --drift-eval
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "apps" / "api"))

from sqlalchemy import text  # noqa: E402

from app.db.session import SessionLocal  # noqa: E402
from app.services.dynamic_crawl import (  # noqa: E402
    FetchResult,
    PlaywrightBatchFetcher,
    sanitize_extracted_text,
    sanitize_html_dom,
)
from app.services.page_filters import is_error_page, is_http_error_status, rejection_reason  # noqa: E402
from app.services.embedding import embed_url_chunks  # noqa: E402
from app.services.quality_gates import (  # noqa: E402
    chunk_text,
    count_tokens,
    merge_and_polish_chunks,
    run_text_pipeline,
    validate_chunks,
    validate_markdown_text,
)
from app.services.vector_drift_eval import run_benchmark_vector_drift  # noqa: E402
from validate_chunk_quality import (  # noqa: E402
    CHATBOTS_VERIFY_URL,
    validate_url_document,
    verify_chatbots_url,
)

logger = logging.getLogger(__name__)

def apply_shard(targets: list[dict], shard_id: int, num_shards: int) -> list[dict]:
    if num_shards <= 1:
        return targets
    if shard_id < 0 or shard_id >= num_shards:
        raise ValueError(f"shard_id must be between 0 and {num_shards - 1}")
    return targets[shard_id::num_shards]


DYNAMIC_PATH_HINTS = (
    "/solutions/",
    "/resources",
    "/government-education/",
    "/industries/",
    "/customer-stories/",
    "/case-studies/",
)


@dataclass
class RecrawlStats:
    urls_selected: int = 0
    urls_recrawled: int = 0
    urls_updated: int = 0
    urls_failed: int = 0
    urls_validation_failed: int = 0
    chunks_replaced: int = 0
    embeddings_refreshed: int = 0
    failures: list[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "urls_selected": self.urls_selected,
            "urls_recrawled": self.urls_recrawled,
            "urls_updated": self.urls_updated,
            "urls_failed": self.urls_failed,
            "urls_validation_failed": self.urls_validation_failed,
            "chunks_replaced": self.chunks_replaced,
            "embeddings_refreshed": self.embeddings_refreshed,
            "failures": self.failures,
        }


async def select_target_urls(
    db,
    *,
    url: str | None,
    status: str | None,
    dynamic_only: bool,
    defects_only: bool,
    video_only: bool,
    retry_failed: bool,
    resume: bool,
    limit: int | None,
) -> list[dict]:
    if url:
        rows = await db.execute(
            text("""
                SELECT id, url, title, service_category, page_type, is_primary_candidate,
                       ingestion_status
                FROM dataset_urls WHERE url = :url
            """),
            {"url": url},
        )
        return [dict(r) for r in rows.mappings()]

    conditions = ["1=1"]
    if retry_failed:
        conditions.append("du.ingestion_status = 'text_failed'")
    elif resume:
        conditions.append("""
            du.ingestion_status IN ('chunked', 'text_failed')
            AND (
                du.text_quality IS NULL
                OR du.text_quality::text NOT LIKE '%recrawl_dynamic_pages%'
                OR du.ingestion_status = 'text_failed'
            )
        """)
    elif status:
        conditions.append("du.ingestion_status = :status")
    if dynamic_only:
        path_clauses = " OR ".join(f"du.url ILIKE :p{i}" for i in range(len(DYNAMIC_PATH_HINTS)))
        for i, hint in enumerate(DYNAMIC_PATH_HINTS):
            pass
        conditions.append(f"({path_clauses})")
    if defects_only:
        conditions.append("""
            EXISTS (
                SELECT 1 FROM document_chunks dc
                WHERE dc.url = du.url
                  AND (
                    dc.chunk_text ~* '(Loading[[:space:]]*){2,}'
                    OR dc.chunk_text ~* 'Displaying[[:space:]]+[0-9]+-[0-9]+'
                    OR dc.chunk_text ~* 'Filter[[:space:]]*\\([0-9]+\\)'
                    OR dc.chunk_text ILIKE '%Did you find what you were looking for today?%'
                  )
            )
        """)
    if video_only:
        conditions.append("""
            EXISTS (
                SELECT 1 FROM document_chunks dc
                WHERE dc.url = du.url
                  AND (
                    dc.chunk_text ~* 'Video Player is'
                    OR dc.chunk_text ~* 'Stream Type LIVE'
                    OR dc.chunk_text ~* 'captions settings'
                    OR dc.chunk_text ~* 'Current Time [0-9]+:[0-9]+'
                  )
            )
        """)

    params: dict = {}
    if status:
        params["status"] = status
    if dynamic_only:
        for i, hint in enumerate(DYNAMIC_PATH_HINTS):
            params[f"p{i}"] = f"%{hint}%"

    sql = f"""
        SELECT DISTINCT du.id, du.url, du.title, du.service_category, du.page_type,
               du.is_primary_candidate, du.ingestion_status
        FROM dataset_urls du
        WHERE {" AND ".join(conditions)}
        ORDER BY du.url
    """
    if limit:
        sql += " LIMIT :lim"
        params["lim"] = limit

    rows = await db.execute(text(sql), params)
    return [dict(r) for r in rows.mappings()]


async def persist_url_chunks(
    db,
    row: dict,
    html: str,
    text_content: str,
    chunks: list[str],
    *,
    embed: bool,
) -> dict:
    await db.execute(text("DELETE FROM document_chunks WHERE url = :url"), {"url": row["url"]})
    quality = {
        "chunk_count": len(chunks),
        "refresh_source": "recrawl_dynamic_pages",
        "playwright": True,
    }
    await db.execute(
        text("""
            UPDATE dataset_urls SET
                ingestion_status = 'chunked',
                html_content = :html,
                text_content = :text_content,
                text_quality = :quality,
                chunk_count = :chunk_count,
                last_error = NULL,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = :id
        """),
        {
            "id": row["id"],
            "html": html,
            "text_content": text_content,
            "quality": json.dumps(quality),
            "chunk_count": len(chunks),
        },
    )

    for idx, chunk in enumerate(chunks):
        chunk = sanitize_extracted_text(chunk)
        await db.execute(
            text("""
                INSERT INTO document_chunks (url, title, chunk_index, chunk_text, token_count, metadata, embedding)
                VALUES (:url, :title, :idx, :text, :tokens, :meta, NULL)
            """),
            {
                "url": row["url"],
                "title": row.get("title"),
                "idx": idx,
                "text": chunk,
                "tokens": count_tokens(chunk),
                "meta": json.dumps({
                    "service_category": row.get("service_category"),
                    "page_type": row.get("page_type"),
                    "is_primary": row.get("is_primary_candidate"),
                    "embedded": False,
                    "refreshed_by": "recrawl_dynamic_pages",
                }),
            },
        )

    embedded_count = 0
    status = "chunked"
    if embed:
        embedded_count = await embed_url_chunks(db, row["url"])
        status = "embedded" if embedded_count else "chunked"

    await db.execute(
        text("""
            UPDATE dataset_urls
            SET ingestion_status = :status, updated_at = CURRENT_TIMESTAMP
            WHERE id = :id
        """),
        {"id": row["id"], "status": status},
    )
    await db.commit()
    return {"chunk_count": len(chunks), "embedded_count": embedded_count, "status": status}


def build_chunks_from_html(html: str, page_url: str) -> tuple[str, list[str]] | None:
    sanitized = sanitize_html_dom(html)
    if sanitized:
        ok, _ = validate_markdown_text(sanitized)
        if ok:
            chunks = chunk_text(sanitized)
            ok_chunks, _ = validate_chunks(chunks)
            if ok_chunks:
                return sanitized, chunks

    pipeline = run_text_pipeline(html, page_url=page_url)
    if pipeline.get("passed"):
        return pipeline["text"], pipeline["chunks"]
    return None


async def recrawl_one(
    db,
    row: dict,
    *,
    timeout_ms: int,
    embed: bool,
    skip_validation: bool,
    html: str | None = None,
    http_status: int | None = None,
    fetcher: PlaywrightBatchFetcher | None = None,
) -> dict:
    url = row["url"]
    if html is None:
        fetched: FetchResult | None
        if fetcher is not None:
            fetched = await fetcher.fetch(url)
        else:
            async with PlaywrightBatchFetcher(timeout_ms=timeout_ms) as session:
                fetched = await session.fetch(url)
        if not fetched:
            await db.execute(
                text("""
                    UPDATE dataset_urls
                    SET ingestion_status = 'text_failed',
                        last_error = 'recrawl_dynamic_pages:playwright_fetch_failed',
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = :id
                """),
                {"id": row["id"]},
            )
            await db.commit()
            return {"url": url, "passed": False, "reason": "playwright_fetch_failed"}
        html = fetched.html
        http_status = fetched.status

    if is_http_error_status(http_status):
        reason = rejection_reason("", http_status=http_status)
        await db.execute(
            text("""
                UPDATE dataset_urls SET ingestion_status = 'text_failed',
                    last_error = :err,
                    updated_at = CURRENT_TIMESTAMP WHERE id = :id
            """),
            {"id": row["id"], "err": f"recrawl_dynamic_pages:{reason}"},
        )
        await db.commit()
        return {"url": url, "passed": False, "reason": reason}

    built = build_chunks_from_html(html, url)
    if not built:
        await db.execute(
            text("""
                UPDATE dataset_urls
                SET ingestion_status = 'text_failed',
                    last_error = 'recrawl_dynamic_pages:chunk_pipeline_failed',
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = :id
            """),
            {"id": row["id"]},
        )
        await db.commit()
        return {"url": url, "passed": False, "reason": "pipeline_failed"}

    text_content, chunks = built
    reject = rejection_reason(text_content, http_status=http_status)
    if reject:
        await db.execute(
            text("""
                UPDATE dataset_urls SET ingestion_status = 'text_failed',
                    last_error = :err,
                    updated_at = CURRENT_TIMESTAMP WHERE id = :id
            """),
            {"id": row["id"], "err": f"recrawl_dynamic_pages:{reject}"},
        )
        await db.commit()
        return {"url": url, "passed": False, "reason": reject}

    chunks = merge_and_polish_chunks(chunks)
    ok_polish, _ = validate_chunks(chunks)
    if not ok_polish:
        await db.execute(
            text("""
                UPDATE dataset_urls SET ingestion_status = 'text_failed',
                    last_error = 'recrawl_dynamic_pages:polish_failed',
                    updated_at = CURRENT_TIMESTAMP WHERE id = :id
            """),
            {"id": row["id"]},
        )
        await db.commit()
        return {"url": url, "passed": False, "reason": "polish_failed"}

    text_content = sanitize_extracted_text("\n\n".join(chunks))
    if not skip_validation:
        issues = validate_url_document(url, chunks)
        if issues:
            await db.execute(
                text("""
                    UPDATE dataset_urls
                    SET ingestion_status = 'text_failed',
                        last_error = :err,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = :id
                """),
                {
                    "id": row["id"],
                    "err": f"recrawl_validation:{issues[0].issues}",
                },
            )
            await db.commit()
            return {
                "url": url,
                "passed": False,
                "reason": "validation_failed",
                "issues": [i.issues for i in issues],
            }

    result = await persist_url_chunks(
        db, row, html, text_content, chunks, embed=embed
    )
    return {"url": url, "passed": True, **result}


async def run_recrawl(args: argparse.Namespace) -> RecrawlStats:
    stats = RecrawlStats()

    async with SessionLocal() as db:
        targets = await select_target_urls(
            db,
            url=args.url,
            status=args.status,
            dynamic_only=args.dynamic_only,
            defects_only=args.defects_only,
            video_only=args.video_only,
            retry_failed=args.retry_failed,
            resume=args.resume,
            limit=None if args.num_shards > 1 else args.limit,
        )

    total_before_shard = len(targets)
    if args.num_shards > 1 and not args.url:
        targets = apply_shard(targets, args.shard_id, args.num_shards)
    if args.limit is not None:
        targets = targets[: args.limit]

    stats.urls_selected = len(targets)

    print("\n=== Playwright Re-Crawl Pipeline ===")
    if args.num_shards > 1 and not args.url:
        print(f"Shard:                 {args.shard_id + 1}/{args.num_shards}")
        print(f"URLs in shard:         {stats.urls_selected} (of {total_before_shard} pending)")
    print(f"URLs selected:         {stats.urls_selected}")
    if not args.dry_run:
        print(f"Page concurrency:      {max(1, args.concurrency)}")
    if args.dry_run:
        for t in targets[:25]:
            print(f"  • {t['url']} ({t['ingestion_status']})")
        if len(targets) > 25:
            print(f"  … and {len(targets) - 25} more")
        return stats

    concurrency = max(1, args.concurrency)
    async with PlaywrightBatchFetcher(timeout_ms=args.timeout_ms) as fetcher:
        async with SessionLocal() as db:
            for start in range(0, len(targets), concurrency):
                batch = targets[start : start + concurrency]
                urls = [r["url"] for r in batch]
                html_map = await fetcher.fetch_many(urls, concurrency=concurrency)

                for row in batch:
                    stats.urls_recrawled += 1
                    url = row["url"]
                    fetched = html_map.get(url)
                    try:
                        if not fetched:
                            raise RuntimeError("playwright_fetch_empty")
                        result = await recrawl_one(
                            db,
                            row,
                            timeout_ms=args.timeout_ms,
                            embed=args.embed and not args.no_embed,
                            skip_validation=args.skip_validation,
                            html=fetched.html,
                            http_status=fetched.status,
                        )
                        if result.get("passed"):
                            stats.urls_updated += 1
                            stats.chunks_replaced += result.get("chunk_count", 0)
                            stats.embeddings_refreshed += result.get("embedded_count", 0)
                            print(
                                f"  ✓ {url} — {result.get('chunk_count', 0)} chunks"
                                f" → {result.get('status', 'chunked')}"
                            )
                        else:
                            if result.get("reason") == "validation_failed":
                                stats.urls_validation_failed += 1
                            else:
                                stats.urls_failed += 1
                            stats.failures.append(result)
                            print(f"  ✗ {url} — {result.get('reason')}")
                    except Exception as exc:
                        stats.urls_failed += 1
                        stats.failures.append({"url": url, "error": str(exc)})
                        await db.execute(
                            text("""
                                UPDATE dataset_urls
                                SET ingestion_status = 'text_failed',
                                    last_error = :err,
                                    updated_at = CURRENT_TIMESTAMP
                                WHERE id = :id
                            """),
                            {"id": row["id"], "err": f"recrawl:{exc}"},
                        )
                        await db.commit()
                        print(f"  ✗ {url} — {exc}")
                        logger.exception("Recrawl failed for %s", url)

    return stats


async def print_verification() -> None:
    verify = await verify_chatbots_url()
    print("\n=== Verification: Chatbots Solution Page ===")
    print(f"URL: {CHATBOTS_VERIFY_URL}")
    print(f"chunks={verify['chunk_count']} words={verify['word_count']}")
    print(f"aws_service_signals={verify['has_aws_service_signals']}")
    print(f"loading_artifacts={verify['has_loading_artifacts']}")
    print(f"solution_content={verify['has_solution_content']}")
    print(f"nav_noise={verify['excessive_nav_noise']}")
    print(f"PASSED={verify['passed']}")
    print(f"\nChunk preview:\n{verify['preview'][:800]}")


async def main_async(args: argparse.Namespace) -> int:
    stats = await run_recrawl(args)

    if not args.dry_run:
        print("\n=== Summary ===")
        print(f"URLs selected:           {stats.urls_selected}")
        print(f"URLs re-crawled:         {stats.urls_recrawled}")
        print(f"URLs updated:            {stats.urls_updated}")
        print(f"URLs failed:             {stats.urls_failed}")
        print(f"URLs validation failed:  {stats.urls_validation_failed}")
        print(f"Chunks replaced:         {stats.chunks_replaced}")
        print(f"Embeddings refreshed:    {stats.embeddings_refreshed}")

        if args.verify or args.url == CHATBOTS_VERIFY_URL:
            await print_verification()

        drift_summary = None
        if args.drift_eval and not args.no_embed:
            async with SessionLocal() as db:
                drift_summary = await run_benchmark_vector_drift(
                    db,
                    run_name=args.drift_run_name,
                    corpus_scale_size=200,
                )
            print("\n=== Vector Drift (benchmark-200) ===")
            for k, v in drift_summary.items():
                print(f"  {k}: {v}")

    if args.json:
        payload = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "shard_id": args.shard_id,
            "num_shards": args.num_shards,
            **stats.to_dict(),
        }
        if not args.dry_run and (args.verify or not args.url):
            payload["chatbots_verification"] = await verify_chatbots_url()
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print(f"\nWrote report: {args.json}")

    return 0 if stats.urls_failed == 0 and stats.urls_validation_failed == 0 else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Playwright re-crawl for CSR AWS pages")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--url", help="Single URL to re-crawl")
    parser.add_argument(
        "--status",
        default="chunked",
        help="Filter by ingestion_status (default: chunked)",
    )
    parser.add_argument("--dynamic-only", action="store_true", help="Only CSR-prone path patterns")
    parser.add_argument("--defects-only", action="store_true", help="Only URLs with known defects")
    parser.add_argument("--video-only", action="store_true", help="Only URLs with video player UI in chunks")
    parser.add_argument("--retry-failed", action="store_true", help="Only text_failed URLs")
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Re-crawl chunked/text_failed URLs not yet marked recrawl_dynamic_pages",
    )
    parser.add_argument(
        "--embed",
        action="store_true",
        help="Embed after recrawl (OFF by default — require manual text approval first)",
    )
    parser.add_argument("--no-embed", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--skip-validation", action="store_true")
    parser.add_argument("--drift-eval", action="store_true", help="Refresh vector_drift_results (benchmark-200)")
    parser.add_argument("--drift-run-name", default="post_playwright_recrawl")
    parser.add_argument("--verify", action="store_true", help="Print chatbots page verification")
    parser.add_argument("--timeout-ms", type=int, default=60_000)
    parser.add_argument(
        "--concurrency",
        type=int,
        default=3,
        help="Parallel Playwright page contexts per worker (shared browser)",
    )
    parser.add_argument(
        "--shard-id",
        type=int,
        default=0,
        help="Zero-based shard index for parallel workers (use with --num-shards)",
    )
    parser.add_argument(
        "--num-shards",
        type=int,
        default=1,
        help="Split pending URLs across N parallel Playwright workers",
    )
    parser.add_argument("--json", type=Path, help="Write JSON summary report")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO)
    return asyncio.run(main_async(args))


if __name__ == "__main__":
    raise SystemExit(main())
