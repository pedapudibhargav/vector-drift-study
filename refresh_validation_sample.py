#!/usr/bin/env python3
"""
Pick N new random URLs, Playwright-recrawl, post-process, export validation_sample_20.md.

Pipeline per URL:
  1. recrawl_dynamic_pages (Playwright → HTML → text → chunks)
  2. sanitize_chunks (dedupe boundaries, tail merge, noise strip)
  3. clean_text_artifacts (regex / table skeleton cleanup)
  4. regenerate validation markdown
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "apps" / "api"))

from app import ssl_bundle  # noqa: E402

ssl_bundle.apply_corporate_ssl_bundle()

from sqlalchemy import text  # noqa: E402

from app.db.session import SessionLocal  # noqa: E402
from app.services.dynamic_crawl import PlaywrightBatchFetcher  # noqa: E402
from clean_text_artifacts import run_cleanup  # noqa: E402
from recrawl_dynamic_pages import recrawl_one  # noqa: E402
from sanitize_chunks import (  # noqa: E402
    load_url_rows,
    parse_urls_from_markdown,
    regenerate_validation_md,
    run_sanitize,
)

REPORTS = ROOT / "data" / "reports"


async def verify_playwright() -> None:
    try:
        from playwright.async_api import async_playwright  # noqa: F401
    except ImportError as exc:
        raise RuntimeError(
            "Playwright not installed in container. See docs/INGESTION_PIPELINE.md"
        ) from exc


async def pick_random_urls(n: int, *, exclude: list[str]) -> list[str]:
    exclude_clause = "AND NOT (du.url = ANY(:exclude))" if exclude else ""
    async with SessionLocal() as db:
        rows = await db.execute(
            text(f"""
                SELECT du.url
                FROM dataset_urls du
                WHERE EXISTS (SELECT 1 FROM document_chunks dc WHERE dc.url = du.url)
                  {exclude_clause}
                ORDER BY random()
                LIMIT :n
            """),
            {"n": n, "exclude": exclude or []},
        )
        return [r[0] for r in rows]


async def recrawl_batch(
    urls: list[str],
    *,
    timeout_ms: int,
    concurrency: int,
) -> tuple[list[str], list[dict]]:
    rows = await load_url_rows(urls)
    succeeded: list[str] = []
    failures: list[dict] = []
    total = len(rows)

    async with PlaywrightBatchFetcher(timeout_ms=timeout_ms) as fetcher:
        async with SessionLocal() as db:
            for start in range(0, total, concurrency):
                batch = rows[start : start + concurrency]
                batch_urls = [r["url"] for r in batch]
                print(
                    f"  Fetch batch {start // concurrency + 1}"
                    f" ({len(batch_urls)} pages, concurrency={concurrency})"
                )
                html_map = await fetcher.fetch_many(batch_urls, concurrency=concurrency)

                for i, row in enumerate(batch, start=start + 1):
                    url = row["url"]
                    fetched = html_map.get(url)
                    print(f"  [{i}/{total}] chunk: {url}")
                    try:
                        if not fetched:
                            raise RuntimeError("playwright_fetch_empty")
                        result = await recrawl_one(
                            db,
                            row,
                            timeout_ms=timeout_ms,
                            embed=False,
                            skip_validation=False,
                            html=fetched.html,
                            http_status=fetched.status,
                        )
                    except Exception as exc:
                        failures.append({"url": url, "passed": False, "reason": str(exc)})
                        print(f"    ✗ error: {exc}")
                        continue

                    if result.get("passed"):
                        succeeded.append(url)
                        print(f"    ✓ {result.get('chunk_count', '?')} chunks")
                    else:
                        failures.append(result)
                        print(f"    ✗ {result.get('reason', 'failed')}")

    return succeeded, failures


async def ensure_recrawled(
    count: int,
    *,
    exclude: list[str],
    timeout_ms: int,
    max_attempts: int,
    concurrency: int,
) -> tuple[list[str], list[dict]]:
    attempted: set[str] = set(exclude)
    succeeded: list[str] = []
    all_failures: list[dict] = []

    for attempt in range(1, max_attempts + 1):
        need = count - len(succeeded)
        if need <= 0:
            break

        batch = await pick_random_urls(need, exclude=list(attempted))
        if not batch:
            break

        attempted.update(batch)
        print(f"\nRecrawl attempt {attempt}: {len(batch)} URL(s)")
        ok, fails = await recrawl_batch(
            batch, timeout_ms=timeout_ms, concurrency=concurrency
        )
        succeeded.extend(ok)
        all_failures.extend(fails)

    return succeeded[:count], all_failures


async def main_async(args: argparse.Namespace) -> int:
    await verify_playwright()
    print("Playwright: OK")

    prior_urls: list[str] = []
    if args.output.exists():
        prior_urls = parse_urls_from_markdown(args.output)

    exclude = list(set(prior_urls))
    print(f"Selecting {args.count} new URL(s) (excluding {len(prior_urls)} prior sample URL(s))")
    print("Embedding: DISABLED (text review gate)")

    succeeded, failures = await ensure_recrawled(
        args.count,
        exclude=exclude,
        timeout_ms=args.timeout_ms,
        max_attempts=args.max_attempts,
        concurrency=args.concurrency,
    )

    if len(succeeded) < args.count:
        print(
            f"WARNING: only {len(succeeded)}/{args.count} URLs recrawled successfully",
            file=sys.stderr,
        )
        if not succeeded:
            return 1

    print(f"\nPost-processing {len(succeeded)} URL(s): sanitize_chunks → clean_text_artifacts")
    sanitize_stats, _ = await run_sanitize(succeeded, dry_run=False)
    print(f"  sanitize: {sanitize_stats.to_dict()}")

    rows = await load_url_rows(succeeded)
    artifact_stats = await run_cleanup(rows, dry_run=False)
    print(f"  artifacts: {artifact_stats.to_dict()}")

    await regenerate_validation_md(succeeded, args.output)
    ts = (
        datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        + " (playwright-recrawl + rag-sanitize + post-process)"
    )
    text = args.output.read_text(encoding="utf-8")
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if line.startswith("Generated:"):
            lines[i] = f"Generated: {ts}"
            break
    args.output.write_text("\n".join(lines) + "\n", encoding="utf-8")

    audit = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "pipeline": "playwright → chunk → sanitize → artifact_clean",
        "embedding": False,
        "urls_requested": args.count,
        "urls_succeeded": len(succeeded),
        "urls_failed": len(failures),
        "sanitize": sanitize_stats.to_dict(),
        "artifacts": artifact_stats.to_dict(),
        "succeeded_urls": succeeded,
        "failures": failures,
    }
    audit_path = REPORTS / "validation_recrawl_audit.json"
    audit_path.parent.mkdir(parents=True, exist_ok=True)
    audit_path.write_text(json.dumps(audit, indent=2), encoding="utf-8")

    print(f"\nWrote {args.output} ({len(succeeded)} documents, {len(failures)} recrawl failures)")
    print(f"Audit: {audit_path}")
    if failures:
        for f in failures[:10]:
            print(f"  failed: {f.get('url', '?')} — {f.get('reason', '?')}")
    return 0 if len(succeeded) >= args.count else 1


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Refresh validation sample: Playwright recrawl → sanitize → artifact clean → export",
    )
    parser.add_argument("--count", type=int, default=20)
    parser.add_argument("--timeout-ms", type=int, default=60_000)
    parser.add_argument(
        "--concurrency",
        type=int,
        default=4,
        help="Parallel Playwright pages per process (shared browser)",
    )
    parser.add_argument("--max-attempts", type=int, default=3, help="Extra pick rounds if recrawls fail")
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "data" / "reports" / "validation_sample_20.md",
    )
    return asyncio.run(main_async(parser.parse_args()))


if __name__ == "__main__":
    raise SystemExit(main())
