#!/usr/bin/env python3
"""
Audit document_chunks for information density, boilerplate ratio, and CSR hydration.

Usage:
  python validate_chunk_quality.py --dry-run
  python validate_chunk_quality.py --url "https://aws.amazon.com/solutions/ai/chatbots-virtual-assistants"
  python validate_chunk_quality.py --json data/reports/chunk_quality_validation.json
"""

from __future__ import annotations

import argparse
import asyncio
import json
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
from app.services.dynamic_crawl import (  # noqa: E402
    AWS_SERVICE_SIGNALS,
    GENERIC_BOILERPLATE_PHRASES,
    SOLUTION_CARD_SIGNALS,
    chunk_defects,
)

MIN_WORDS = 40
BOILERPLATE_RATIO_THRESHOLD = 0.20

SOLUTIONS_PATH = re.compile(r"/solutions/", re.I)
CHATBOTS_VERIFY_URL = "https://aws.amazon.com/solutions/ai/chatbots-virtual-assistants"


@dataclass
class ChunkIssue:
    url: str
    chunk_index: int
    issues: list[str]
    word_count: int
    boilerplate_ratio: float
    preview: str


@dataclass
class ValidationReport:
    chunks_inspected: int = 0
    chunks_flagged: int = 0
    urls_flagged: int = 0
    issues_by_type: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    flagged: list[ChunkIssue] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "chunks_inspected": self.chunks_inspected,
            "chunks_flagged": self.chunks_flagged,
            "urls_flagged": self.urls_flagged,
            "issues_by_type": dict(self.issues_by_type),
            "flagged": [
                {
                    "url": f.url,
                    "chunk_index": f.chunk_index,
                    "issues": f.issues,
                    "word_count": f.word_count,
                    "boilerplate_ratio": round(f.boilerplate_ratio, 3),
                    "preview": f.preview,
                }
                for f in self.flagged
            ],
        }


def word_count(text: str) -> int:
    return len(re.findall(r"\b\w+\b", text or ""))


def boilerplate_ratio(text: str) -> float:
    if not text:
        return 1.0
    total = len(text)
    overlap = 0
    lower = text.lower()
    for phrase in GENERIC_BOILERPLATE_PHRASES:
        overlap += lower.count(phrase.lower()) * len(phrase)
    return min(1.0, overlap / max(total, 1))


def validate_chunk(url: str, chunk_index: int, chunk_text: str) -> ChunkIssue | None:
    issues: list[str] = []
    wc = word_count(chunk_text)
    bp_ratio = boilerplate_ratio(chunk_text)

    if wc < MIN_WORDS:
        issues.append("low_word_count")
    if bp_ratio > BOILERPLATE_RATIO_THRESHOLD:
        issues.append("high_boilerplate")
    for defect in chunk_defects(chunk_text):
        issues.append(defect)

    if SOLUTIONS_PATH.search(url):
        has_signals = AWS_SERVICE_SIGNALS.search(chunk_text) or SOLUTION_CARD_SIGNALS.search(chunk_text)
        if not has_signals and wc < 80:
            issues.append("missing_solution_signals")

    if not issues:
        return None
    return ChunkIssue(
        url=url,
        chunk_index=chunk_index,
        issues=issues,
        word_count=wc,
        boilerplate_ratio=bp_ratio,
        preview=(chunk_text or "")[:280].replace("\n", " "),
    )


def validate_url_document(url: str, chunks: list[str]) -> list[ChunkIssue]:
    """Document-level gate: hard-fail CSR defects; allow short nav chunks if body is substantive."""
    flagged: list[ChunkIssue] = []
    if not chunks:
        return [
            ChunkIssue(
                url=url,
                chunk_index=0,
                issues=["empty_document"],
                word_count=0,
                boilerplate_ratio=1.0,
                preview="",
            )
        ]

    total_words = sum(word_count(c) for c in chunks)
    combined = "\n\n".join(chunks)

    for idx, chunk in enumerate(chunks):
        defects = chunk_defects(chunk)
        if defects:
            flagged.append(
                ChunkIssue(
                    url=url,
                    chunk_index=idx,
                    issues=defects,
                    word_count=word_count(chunk),
                    boilerplate_ratio=boilerplate_ratio(chunk),
                    preview=(chunk or "")[:280].replace("\n", " "),
                )
            )

    if total_words < 80:
        flagged.append(
            ChunkIssue(
                url=url,
                chunk_index=-1,
                issues=["low_doc_word_count"],
                word_count=total_words,
                boilerplate_ratio=boilerplate_ratio(combined),
                preview=combined[:280].replace("\n", " "),
            )
        )

    if SOLUTIONS_PATH.search(url) and "video" not in url.lower():
        has_signals = AWS_SERVICE_SIGNALS.search(combined) or SOLUTION_CARD_SIGNALS.search(combined)
        if not has_signals and total_words < 300:
            flagged.append(
                ChunkIssue(
                    url=url,
                    chunk_index=-1,
                    issues=["missing_solution_signals"],
                    word_count=total_words,
                    boilerplate_ratio=boilerplate_ratio(combined),
                    preview=combined[:280].replace("\n", " "),
                )
            )

    doc_bp = boilerplate_ratio(combined)
    if doc_bp > BOILERPLATE_RATIO_THRESHOLD and total_words < 400:
        flagged.append(
            ChunkIssue(
                url=url,
                chunk_index=-1,
                issues=["high_boilerplate"],
                word_count=total_words,
                boilerplate_ratio=doc_bp,
                preview=combined[:280].replace("\n", " "),
            )
        )

    return flagged


async def load_chunks_from_db(url: str | None = None) -> list[dict]:
    async with SessionLocal() as db:
        if url:
            rows = await db.execute(
                text("""
                    SELECT url, chunk_index, chunk_text
                    FROM document_chunks
                    WHERE url = :url
                    ORDER BY chunk_index
                """),
                {"url": url},
            )
        else:
            rows = await db.execute(
                text("""
                    SELECT url, chunk_index, chunk_text
                    FROM document_chunks
                    ORDER BY url, chunk_index
                """)
            )
        return [dict(r) for r in rows.mappings()]


async def run_validation(url: str | None = None, *, document_level: bool = False) -> ValidationReport:
    rows = await load_chunks_from_db(url)
    report = ValidationReport()
    urls_seen: set[str] = set()

    if document_level:
        by_url: dict[str, list[str]] = {}
        for row in rows:
            report.chunks_inspected += 1
            by_url.setdefault(row["url"], []).append(row["chunk_text"] or "")
        for page_url, chunks in sorted(by_url.items()):
            doc_issues = validate_url_document(page_url, chunks)
            if doc_issues:
                urls_seen.add(page_url)
                report.chunks_flagged += len(doc_issues)
                report.flagged.extend(doc_issues)
                for item in doc_issues:
                    for name in item.issues:
                        report.issues_by_type[name] += 1
        report.urls_flagged = len(urls_seen)
        return report

    for row in rows:
        report.chunks_inspected += 1
        issue = validate_chunk(row["url"], row["chunk_index"], row["chunk_text"] or "")
        if issue:
            report.chunks_flagged += 1
            urls_seen.add(row["url"])
            report.flagged.append(issue)
            for name in issue.issues:
                report.issues_by_type[name] += 1

    report.urls_flagged = len(urls_seen)
    return report


def print_report(report: ValidationReport) -> None:
    print("\n=== Chunk Quality Validation ===")
    print(f"Chunks inspected:  {report.chunks_inspected}")
    print(f"Chunks flagged:    {report.chunks_flagged}")
    print(f"URLs flagged:      {report.urls_flagged}")
    if report.issues_by_type:
        print("Issue breakdown:")
        for name, count in sorted(report.issues_by_type.items(), key=lambda x: -x[1]):
            print(f"  - {name}: {count}")
    for item in report.flagged[:15]:
        print(f"\n  • {item.url} [chunk {item.chunk_index}]")
        print(f"    issues={item.issues} words={item.word_count} boilerplate={item.boilerplate_ratio:.2f}")
        print(f"    preview: {item.preview[:200]}…")
    if len(report.flagged) > 15:
        print(f"\n  … and {len(report.flagged) - 15} more flagged chunks")


async def verify_chatbots_url() -> dict:
    url = CHATBOTS_VERIFY_URL
    rows = await load_chunks_from_db(url)
    combined = "\n\n".join(r["chunk_text"] or "" for r in rows)
    wc = word_count(combined)
    has_services = bool(AWS_SERVICE_SIGNALS.search(combined))
    has_loading = bool(re.search(r"(?:Loading\s*){2,}", combined, re.I))
    has_nav_noise = combined.count("Become a Partner") > 2
    solution_titles = bool(
        SOLUTION_CARD_SIGNALS.search(combined)
        or re.search(r"(chatbot|virtual assistant|conversational|Lex|Bedrock)", combined, re.I)
    )
    return {
        "url": url,
        "chunk_count": len(rows),
        "word_count": wc,
        "has_aws_service_signals": has_services,
        "has_loading_artifacts": has_loading,
        "excessive_nav_noise": has_nav_noise,
        "has_solution_content": solution_titles,
        "passed": (
            wc >= 200
            and has_services
            and not has_loading
            and solution_titles
        ),
        "preview": combined[:600].replace("\n", " "),
    }


async def main_async(args: argparse.Namespace) -> int:
    report = await run_validation(args.url, document_level=args.document_level)
    print_report(report)

    if args.verify_chatbots or not args.url:
        verify = await verify_chatbots_url()
        print("\n=== Chatbots Solution Page Verification ===")
        print(f"URL: {verify['url']}")
        print(f"chunks={verify['chunk_count']} words={verify['word_count']}")
        print(f"service_signals={verify['has_aws_service_signals']}")
        print(f"loading_artifacts={verify['has_loading_artifacts']}")
        print(f"solution_content={verify['has_solution_content']}")
        print(f"PASSED={verify['passed']}")
        print(f"preview: {verify['preview'][:400]}…")

    if args.json:
        payload = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            **report.to_dict(),
        }
        if args.verify_chatbots or not args.url:
            payload["chatbots_verification"] = await verify_chatbots_url()
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print(f"\nWrote: {args.json}")

    return 0 if report.chunks_flagged == 0 else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate document_chunks quality")
    parser.add_argument("--url", help="Validate a single URL")
    parser.add_argument("--verify-chatbots", action="store_true")
    parser.add_argument("--json", type=Path, help="Write JSON report")
    parser.add_argument("--document-level", action="store_true", help="Validate per URL document")
    args = parser.parse_args()
    return asyncio.run(main_async(args))


if __name__ == "__main__":
    raise SystemExit(main())
