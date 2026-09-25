#!/usr/bin/env python3
"""
Audit document_chunks for unrendered dynamic content / boilerplate, re-crawl with
Playwright, sanitize DOM text, refresh chunks, and regenerate embeddings.

Usage:
  python fix_chunk_quality.py --dry-run
  python fix_chunk_quality.py --limit 10
  python fix_chunk_quality.py --url "https://aws.amazon.com/bedrock/pricing"
  python fix_chunk_quality.py --no-embed   # skip OpenAI embedding refresh
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import re
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "apps" / "api"))

from sqlalchemy import text  # noqa: E402

from app.db.session import SessionLocal  # noqa: E402
from app.services.embedding import embed_url_chunks  # noqa: E402
from app.services.quality_gates import count_tokens, run_text_pipeline  # noqa: E402

logger = logging.getLogger(__name__)

CONTENT_SELECTORS = ("main", "#aws-page-content", "[role='main']", "article")
REMOVE_SELECTORS = (
    "header",
    "footer",
    "nav",
    ".feedback-container",
    "[class*='cookie']",
    "[id*='cookie']",
    "[class*='banner']",
    "[aria-label*='cookie' i]",
    "script",
    "style",
    "noscript",
    "iframe",
)

DEFECT_CHECKS: list[tuple[str, re.Pattern[str]]] = [
    ("loading_spinner", re.compile(r"(Loading\s*){2,}", re.I)),
    ("pagination_placeholder", re.compile(r"Displaying\s+\d+-\d+", re.I)),
    ("feedback_boilerplate", re.compile(r"Did you find what you were looking for today\?", re.I)),
    ("yes_no_feedback", re.compile(r"\bYes\s+No\b")),
    ("empty_placeholder", re.compile(r"^\s*(Loading|\.{3,})\s*$", re.I | re.M)),
]

TEXT_STRIP_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("loading_repeat", re.compile(r"(Loading\s*){2,}", re.I)),
    ("pagination", re.compile(r"Displaying\s+\d+-\d+", re.I)),
    ("yes_no", re.compile(r"\bYes\s+No\b")),
    ("feedback", re.compile(r"Did you find what you were looking for today\?", re.I)),
    ("extra_blank", re.compile(r"\n{3,}")),
]


@dataclass
class AuditStats:
    chunks_inspected: int = 0
    chunks_flagged: int = 0
    urls_flagged: int = 0
    urls_recrawled: int = 0
    urls_updated: int = 0
    urls_failed: int = 0
    chunks_updated: int = 0
    embeddings_refreshed: int = 0
    defects_by_type: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    flagged_urls: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "chunks_inspected": self.chunks_inspected,
            "chunks_flagged": self.chunks_flagged,
            "urls_flagged": self.urls_flagged,
            "urls_recrawled": self.urls_recrawled,
            "urls_updated": self.urls_updated,
            "urls_failed": self.urls_failed,
            "chunks_updated": self.chunks_updated,
            "embeddings_refreshed": self.embeddings_refreshed,
            "defects_by_type": dict(self.defects_by_type),
            "flagged_urls": self.flagged_urls,
        }


def chunk_defects(chunk_text: str) -> list[str]:
    if not chunk_text or not chunk_text.strip():
        return ["empty_chunk"]
    hits: list[str] = []
    for name, pattern in DEFECT_CHECKS:
        if pattern.search(chunk_text):
            hits.append(name)
    if len(chunk_text.strip()) < 80 and re.search(r"\bLoading\b", chunk_text, re.I):
        if "loading_short" not in hits:
            hits.append("loading_short")
    return hits


def sanitize_extracted_text(text: str) -> str:
    cleaned = text
    for _, pattern in TEXT_STRIP_PATTERNS:
        cleaned = pattern.sub("\n\n" if pattern.pattern == r"\n{3,}" else " ", cleaned)
    cleaned = re.sub(r"[ \t]+\n", "\n", cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


def sanitize_html_dom(html: str) -> str:
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, "lxml")
    for selector in REMOVE_SELECTORS:
        for element in soup.select(selector):
            element.decompose()

    root = None
    for selector in CONTENT_SELECTORS:
        root = soup.select_one(selector)
        if root and len(root.get_text(" ", strip=True)) >= 100:
            break
    if root is None:
        root = soup.body or soup

    import html2text

    converter = html2text.HTML2Text()
    converter.ignore_links = True
    converter.ignore_images = True
    converter.body_width = 0
    markdown = converter.handle(str(root)).strip()
    return sanitize_extracted_text(markdown)


async def fetch_rendered_html(url: str, *, timeout_ms: int = 60_000) -> str:
    try:
        from playwright.async_api import async_playwright
    except ImportError as exc:
        raise RuntimeError(
            "Playwright not installed. Run: pip install playwright && playwright install chromium"
        ) from exc

    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1440, "height": 900})
        try:
            await page.goto(url, wait_until="networkidle", timeout=timeout_ms)
            for selector in CONTENT_SELECTORS:
                try:
                    await page.wait_for_selector(selector, timeout=15_000, state="visible")
                    break
                except Exception:
                    continue
            await page.wait_for_timeout(1_500)
            return await page.content()
        finally:
            await browser.close()


async def fetch_stored_html(db, url: str) -> str | None:
    row = await db.execute(
        text("SELECT html_content FROM dataset_urls WHERE url = :url"),
        {"url": url},
    )
    record = row.mappings().first()
    if not record or not record["html_content"]:
        return None
    return record["html_content"]


async def fetch_page_html(
    db,
    url: str,
    *,
    timeout_ms: int,
    use_playwright: bool,
) -> str:
    if use_playwright:
        try:
            return await fetch_rendered_html(url, timeout_ms=timeout_ms)
        except Exception as exc:
            logger.warning("Playwright fetch failed for %s: %s — trying stored HTML", url, exc)
    stored = await fetch_stored_html(db, url)
    if stored:
        return stored
    raise RuntimeError("No Playwright HTML and no stored html_content in dataset_urls")


async def mark_url_stage(db, url_id: int, status: str, error: str | None = None) -> None:
    await db.execute(
        text("""
            UPDATE dataset_urls
            SET ingestion_status = :status,
                last_error = :error,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = :id
        """),
        {"id": url_id, "status": status, "error": error},
    )


def assess_text_document(url: str, text: str, chunks: list[str]) -> dict:
    """Heuristic quality assessment for manual-review style reporting."""
    issues: list[str] = []
    combined = text or "\n\n".join(chunks)
    if not combined or len(combined.strip()) < 200:
        issues.append("too_short")
    for name, pattern in DEFECT_CHECKS:
        if pattern.search(combined):
            issues.append(name)
    words = combined.split()
    if len(words) < 50:
        issues.append("low_word_count")
    alpha = sum(ch.isalpha() for ch in combined if not ch.isspace())
    total = len([ch for ch in combined if not ch.isspace()]) or 1
    if alpha / total < 0.5:
        issues.append("low_alpha_ratio")
    nav_lines = sum(1 for ln in combined.splitlines() if ln.strip().startswith("* ["))
    if nav_lines > 8:
        issues.append("nav_heavy")
    verdict = "pass" if not issues else ("warn" if len(issues) <= 1 and issues[0] in ("low_word_count",) else "fail")
    return {
        "url": url,
        "word_count": len(words),
        "chunk_count": len(chunks),
        "issues": issues,
        "verdict": verdict,
        "preview": combined[:400].replace("\n", " "),
    }


async def sample_review_urls(n: int = 20) -> list[dict]:
    async with SessionLocal() as db:
        rows = await db.execute(
            text("""
                SELECT du.url, du.text_content, du.ingestion_status,
                       COALESCE(json_agg(dc.chunk_text ORDER BY dc.chunk_index)
                                FILTER (WHERE dc.chunk_text IS NOT NULL), '[]') AS chunks
                FROM dataset_urls du
                LEFT JOIN document_chunks dc ON dc.url = du.url
                WHERE du.text_content IS NOT NULL
                GROUP BY du.url, du.text_content, du.ingestion_status
                ORDER BY random()
                LIMIT :n
            """),
            {"n": n},
        )
        results = []
        for row in rows.mappings():
            chunks = row["chunks"]
            if isinstance(chunks, str):
                chunks = json.loads(chunks)
            assessment = assess_text_document(row["url"], row["text_content"] or "", chunks)
            assessment["ingestion_status"] = row["ingestion_status"]
            results.append(assessment)
        return results


async def load_chunks(url: str | None = None) -> list[dict]:
    async with SessionLocal() as db:
        if url:
            rows = await db.execute(
                text("""
                    SELECT dc.url, dc.chunk_index, dc.chunk_text, dc.token_count,
                           du.id, du.title, du.service_category, du.page_type,
                           du.is_primary_candidate, du.html_content
                    FROM document_chunks dc
                    JOIN dataset_urls du ON du.url = dc.url
                    WHERE dc.url = :url
                    ORDER BY dc.chunk_index
                """),
                {"url": url},
            )
        else:
            rows = await db.execute(
                text("""
                    SELECT dc.url, dc.chunk_index, dc.chunk_text, dc.token_count,
                           du.id, du.title, du.service_category, du.page_type,
                           du.is_primary_candidate, du.html_content
                    FROM document_chunks dc
                    JOIN dataset_urls du ON du.url = dc.url
                    WHERE dc.chunk_text ~* '(Loading[[:space:]]*){2,}'
                       OR dc.chunk_text ~* 'Displaying[[:space:]]+[0-9]+-[0-9]+'
                       OR dc.chunk_text ILIKE '%Did you find what you were looking for today?%'
                       OR dc.chunk_text ~* 'Yes[[:space:]]+No'
                       OR (length(trim(dc.chunk_text)) < 80 AND dc.chunk_text ~* 'Loading')
                    ORDER BY dc.url, dc.chunk_index
                """)
            )
        return [dict(r) for r in rows.mappings()]


async def count_all_chunks() -> int:
    async with SessionLocal() as db:
        row = await db.execute(text("SELECT COUNT(*) FROM document_chunks"))
        return int(row.scalar_one() or 0)


def audit_chunks(rows: list[dict]) -> tuple[AuditStats, dict[str, list[dict]], dict[str, dict]]:
    stats = AuditStats()
    flagged_by_url: dict[str, list[dict]] = defaultdict(list)
    url_meta: dict[str, dict] = {}

    for row in rows:
        stats.chunks_inspected += 1
        url = row["url"]
        url_meta.setdefault(
            url,
            {
                "id": row["id"],
                "url": url,
                "title": row.get("title"),
                "service_category": row.get("service_category"),
                "page_type": row.get("page_type"),
                "is_primary_candidate": row.get("is_primary_candidate"),
                "html_content": row.get("html_content"),
            },
        )
        defects = chunk_defects(row["chunk_text"] or "")
        if defects:
            stats.chunks_flagged += 1
            flagged_by_url[url].append({**row, "defects": defects})
            for defect in defects:
                stats.defects_by_type[defect] += 1

    stats.urls_flagged = len(flagged_by_url)
    stats.flagged_urls = sorted(flagged_by_url.keys())
    return stats, flagged_by_url, url_meta


async def refresh_url_chunks(
    db,
    row: dict,
    html: str,
    *,
    embed: bool,
) -> dict:
    from app.services.quality_gates import chunk_text, validate_chunks, validate_markdown_text

    sanitized = sanitize_html_dom(html)
    report: dict | None = None

    if sanitized:
        ok, text_gate = validate_markdown_text(sanitized)
        if ok:
            chunks = chunk_text(sanitized)
            ok_chunks, chunk_gate = validate_chunks(chunks)
            if ok_chunks:
                report = {
                    "passed": True,
                    "text": sanitized,
                    "chunks": chunks,
                    "gates": {
                        "html": {"passed": True, "source": "sanitized_dom"},
                        "text": text_gate,
                        "chunks": chunk_gate,
                    },
                }

    if report is None:
        pipeline = await asyncio.to_thread(run_text_pipeline, html, page_url=row["url"])
        if pipeline["passed"]:
            report = pipeline

    if not report or not report.get("passed"):
        await mark_url_stage(
            db,
            row["id"],
            "text_failed",
            error="fix_chunk_quality:pipeline_failed",
        )
        await db.commit()
        return {
            "url": row["url"],
            "passed": False,
            "gates": (report or {}).get("gates", {}),
        }

    chunks = report["chunks"]
    text_content = report["text"]
    quality = {**report["gates"], "chunk_count": len(chunks), "refresh_source": "fix_chunk_quality"}

    await db.execute(text("DELETE FROM document_chunks WHERE url = :url"), {"url": row["url"]})
    await db.execute(
        text("""
            UPDATE dataset_urls SET
                ingestion_status = 'text_ok',
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
                    "refreshed_by": "fix_chunk_quality",
                }),
            },
        )

    embedded_count = 0
    if embed:
        embedded_count = await embed_url_chunks(db, row["url"])
        status = "embedded" if embedded_count else "chunked"
    else:
        status = "chunked"

    await mark_url_stage(db, row["id"], status)
    await db.commit()

    return {
        "url": row["url"],
        "passed": True,
        "gates": report["gates"],
        "chunk_count": len(chunks),
        "embedded_count": embedded_count,
    }


async def count_loading_artifacts() -> int:
    async with SessionLocal() as db:
        row = await db.execute(
            text("""
                SELECT COUNT(*) FROM document_chunks
                WHERE chunk_text ~* '(Loading[[:space:]]*){2,}'
                   OR chunk_text ~* 'Displaying[[:space:]]+[0-9]+-[0-9]+'
                   OR chunk_text ILIKE '%Did you find what you were looking for today?%'
                   OR chunk_text ~* 'Yes\s+No'
            """)
        )
        return int(row.scalar_one() or 0)


async def run_fix(
    *,
    dry_run: bool,
    limit: int | None,
    url: str | None,
    embed: bool,
    timeout_ms: int,
    use_playwright: bool,
    mark_flagged: bool,
) -> AuditStats:
    rows = await load_chunks(url)
    total_chunks = await count_all_chunks() if not url else len(rows)
    if not rows and not url:
        print("No defective document_chunks found in PostgreSQL.")
        stats = AuditStats()
        stats.chunks_inspected = total_chunks
        return stats

    stats, flagged_by_url, url_meta = audit_chunks(rows)
    if not url:
        stats.chunks_inspected = total_chunks
    target_urls = stats.flagged_urls
    if limit is not None:
        target_urls = target_urls[:limit]

    print("\n=== Chunk Quality Audit ===")
    print(f"Chunks inspected:     {stats.chunks_inspected}")
    print(f"Chunks flagged:       {stats.chunks_flagged}")
    print(f"URLs flagged:         {stats.urls_flagged}")
    if stats.defects_by_type:
        print("Defect breakdown:")
        for name, count in sorted(stats.defects_by_type.items(), key=lambda x: -x[1]):
            print(f"  - {name}: {count}")

    if dry_run:
        print("\nDry run — no re-crawl performed.")
        for flagged_url in target_urls[:20]:
            sample = flagged_by_url[flagged_url][0]
            print(f"  • {flagged_url} ({sample['defects']})")
        if len(target_urls) > 20:
            print(f"  … and {len(target_urls) - 20} more URLs")
        remaining = await count_loading_artifacts()
        print(f"\nLoading/boilerplate artifacts in DB: {remaining}")
        return stats

    if not target_urls:
        print("\nNo defective chunks — nothing to re-process.")
        remaining = await count_loading_artifacts()
        print(f"Loading/boilerplate artifacts in DB: {remaining}")
        return stats

    source = "Playwright + stored HTML fallback" if use_playwright else "stored HTML (sanitized re-chunk)"
    print(f"\nRe-processing {len(target_urls)} flagged URL(s) via {source}…")

    async with SessionLocal() as db:
        if mark_flagged:
            for flagged_url in target_urls:
                await mark_url_stage(
                    db,
                    url_meta[flagged_url]["id"],
                    "text_failed",
                    error="fix_chunk_quality:flagged_for_rechunk",
                )
            await db.commit()
            print(f"Marked {len(target_urls)} URL(s) as text_failed (needs re-chunk / re-embed review)")

        for flagged_url in target_urls:
            row = url_meta[flagged_url]
            stats.urls_recrawled += 1
            try:
                html = await fetch_page_html(
                    db,
                    flagged_url,
                    timeout_ms=timeout_ms,
                    use_playwright=use_playwright,
                )
                result = await refresh_url_chunks(db, row, html, embed=embed)
                if result.get("passed"):
                    stats.urls_updated += 1
                    stats.chunks_updated += result.get("chunk_count", 0)
                    stats.embeddings_refreshed += result.get("embedded_count", 0)
                    print(f"  ✓ {flagged_url} — {result.get('chunk_count', 0)} chunks → chunked (no embed)")
                else:
                    stats.urls_failed += 1
                    gate = next(
                        (g for g, v in (result.get("gates") or {}).items() if not v.get("passed")),
                        "unknown",
                    )
                    print(f"  ✗ {flagged_url} — pipeline failed ({gate}) → text_failed")
            except Exception as exc:
                stats.urls_failed += 1
                await mark_url_stage(
                    db,
                    row["id"],
                    "text_failed",
                    error=f"fix_chunk_quality:{exc}",
                )
                await db.commit()
                print(f"  ✗ {flagged_url} — {exc}")
                logger.exception("Re-process failed for %s", flagged_url)

    remaining = await count_loading_artifacts()
    print("\n=== Final Summary ===")
    print(f"URLs re-crawled:              {stats.urls_recrawled}")
    print(f"URLs updated:                 {stats.urls_updated}")
    print(f"URLs failed:                  {stats.urls_failed}")
    print(f"Chunks written:               {stats.chunks_updated}")
    print(f"Embeddings refreshed:         {stats.embeddings_refreshed}")
    print(f"Remaining loading artifacts:  {remaining}")
    return stats


async def run_sample_review(
    n: int,
    *,
    embed: bool,
    use_playwright: bool,
    fix_failures: bool,
) -> list[dict]:
    print(f"\n=== Random Sample Review ({n} documents) ===")
    samples = await sample_review_urls(n)
    pass_n = warn_n = fail_n = 0
    fixed = 0

    async with SessionLocal() as db:
        for item in samples:
            verdict = item["verdict"]
            if verdict == "pass":
                pass_n += 1
            elif verdict == "warn":
                warn_n += 1
            else:
                fail_n += 1

            status_icon = {"pass": "✓", "warn": "~", "fail": "✗"}[verdict]
            print(f"\n{status_icon} {item['url']}")
            print(f"   stage={item['ingestion_status']} words={item['word_count']} chunks={item['chunk_count']}")
            if item["issues"]:
                print(f"   issues: {', '.join(item['issues'])}")
            print(f"   preview: {item['preview'][:220]}…")

            if fix_failures and verdict == "fail":
                row = await db.execute(
                    text("""
                        SELECT id, url, title, service_category, page_type, is_primary_candidate
                        FROM dataset_urls WHERE url = :url
                    """),
                    {"url": item["url"]},
                )
                meta = dict(row.mappings().first() or {})
                if not meta:
                    continue
                await mark_url_stage(db, meta["id"], "text_failed", "sample_review:quality_fail")
                await db.commit()
                try:
                    html = await fetch_page_html(
                        db,
                        item["url"],
                        timeout_ms=60_000,
                        use_playwright=use_playwright,
                    )
                    result = await refresh_url_chunks(db, meta, html, embed=embed)
                    if result.get("passed"):
                        fixed += 1
                        reassess = assess_text_document(
                            item["url"],
                            "",
                            [],
                        )
                        print(f"   → re-chunked to {result['chunk_count']} chunks (stage=chunked)")
                    else:
                        print("   → re-chunk failed; remains text_failed")
                except Exception as exc:
                    await mark_url_stage(db, meta["id"], "text_failed", f"sample_review:{exc}")
                    await db.commit()
                    print(f"   → fix error: {exc}")

    print(f"\nSample summary: pass={pass_n} warn={warn_n} fail={fail_n} fixed={fixed}")
    return samples


async def main_async(args: argparse.Namespace) -> int:
    use_playwright = not args.stored_html_only

    if args.sample_review:
        await run_sample_review(
            args.sample_review,
            embed=not args.no_embed,
            use_playwright=use_playwright,
            fix_failures=args.fix_sample_failures,
        )

    stats = await run_fix(
        dry_run=args.dry_run,
        limit=args.limit,
        url=args.url,
        embed=not args.no_embed,
        timeout_ms=args.timeout_ms,
        use_playwright=use_playwright,
        mark_flagged=args.mark_flagged,
    )

    if args.sample_review and not args.dry_run:
        await run_sample_review(
            args.sample_review,
            embed=not args.no_embed,
            use_playwright=use_playwright,
            fix_failures=False,
        )
    if args.json:
        payload = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            **stats.to_dict(),
        }
        Path(args.json).parent.mkdir(parents=True, exist_ok=True)
        Path(args.json).write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print(f"\nWrote audit log: {args.json}")
    if not args.dry_run and not args.no_embed:
        print("NOTE: embeddings were refreshed — use --no-embed to skip vector writes")
    return 0 if stats.urls_failed == 0 else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Fix low-quality HTML chunks via Playwright re-crawl")
    parser.add_argument("--dry-run", action="store_true", help="Audit only; do not re-crawl")
    parser.add_argument("--limit", type=int, default=None, help="Max flagged URLs to re-crawl")
    parser.add_argument("--url", help="Single URL to inspect/fix")
    parser.add_argument("--no-embed", action="store_true", help="Skip embedding regeneration")
    parser.add_argument("--stored-html-only", action="store_true", help="Re-chunk from stored HTML (no Playwright)")
    parser.add_argument("--mark-flagged", action="store_true", help="Mark flagged URLs text_failed before re-process")
    parser.add_argument("--sample-review", type=int, default=0, help="Review N random full-text documents")
    parser.add_argument("--fix-sample-failures", action="store_true", help="Re-chunk failed sample docs")
    parser.add_argument("--timeout-ms", type=int, default=60_000, help="Playwright navigation timeout")
    parser.add_argument("--json", type=Path, help="Write audit summary JSON")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO)
    return asyncio.run(main_async(args))


if __name__ == "__main__":
    raise SystemExit(main())
