#!/usr/bin/env python3
"""
Post-process document_chunks: dedupe boundaries, merge tail chunks, strip review noise.

Usage:
  python sanitize_chunks.py --reset-all-pending
  python sanitize_chunks.py --urls-file data/reports/validation_sample_20.md --apply
  python sanitize_chunks.py --url "https://..." --dry-run
"""

from __future__ import annotations

import argparse
import asyncio
import json
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
from app.services.chunking import dedupe_adjacent_seams  # noqa: E402
from app.services.dynamic_crawl import sanitize_extracted_text  # noqa: E402
from app.services.quality_gates import count_tokens  # noqa: E402

TAIL_MIN_TOKENS = 150
MAX_MERGED_TOKENS = 600
JACCARD_THRESHOLD = 0.70
REFRESH_SOURCE = "sanitize_chunks"

NOISE_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("feedback_footer", re.compile(
        r"How can we make this page better\?.*?(?=\n\n|\Z)", re.I | re.S
    )),
    ("feedback_report", re.compile(
        r"Give us feedback\s*Report a problem.*?(?=\n\n|\Z)", re.I | re.S
    )),
    ("vendor_disclaimer", re.compile(
        r"Content disclaimer\s*Vendors are responsible.*?(?=\n\n|\Z)", re.I | re.S
    )),
    ("g2_review", re.compile(
        r"What do you like best about the product\?.*?(?=\n\n##|\Z)", re.I | re.S
    )),
    ("g2_dislike", re.compile(
        r"What do you dislike about the product\?.*?(?=\n\n##|\Z)", re.I | re.S
    )),
    ("peer_spot", re.compile(r"PeerSpot\s+reviews?.*?(?=\n\n|\Z)", re.I | re.S)),
    ("star_matrix", re.compile(r"(?:★|⭐|\b[1-5]/5\b).{0,200}(?:rating|reviews)", re.I | re.S)),
    ("try_agent", re.compile(r"_\s*Try agent mode\s*_?", re.I)),
    ("ask_question_ui", re.compile(r"^Ask question\s*$", re.I | re.M)),
    ("create_proposal", re.compile(r"^Create proposal\s*$", re.I | re.M)),
    ("concepts_hub", re.compile(
        r"Browse all cloud computing concepts.*?(?=\n\n|\Z)", re.I | re.S
    )),
]

_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")

NAV_ONLY_RE = re.compile(
    r"^(?:\*?\s*(?:Overview|Pricing|Legal|Support|Info)\s*)+$",
    re.I | re.M,
)
TABLE_ARTIFACT_RE = re.compile(r"^\s*\|(?:\s*\|)+\s*$|^-{3,}\s*$", re.M)


@dataclass
class SanitizeStats:
    urls_processed: int = 0
    chunks_in: int = 0
    chunks_out: int = 0
    duplicate_blocks_removed: int = 0
    tails_merged: int = 0
    tails_pruned: int = 0
    noise_strips: int = 0
    urls_updated: int = 0

    def to_dict(self) -> dict:
        return {
            "urls_processed": self.urls_processed,
            "chunks_in": self.chunks_in,
            "chunks_out": self.chunks_out,
            "duplicate_blocks_removed": self.duplicate_blocks_removed,
            "tails_merged": self.tails_merged,
            "tails_pruned": self.tails_pruned,
            "noise_strips": self.noise_strips,
            "urls_updated": self.urls_updated,
        }


def parse_urls_from_markdown(path: Path) -> list[str]:
    content = path.read_text(encoding="utf-8")
    return re.findall(r"- \*\*URL:\*\* (https://[^\s]+)", content)


def tokenize_words(text: str) -> set[str]:
    return {w.lower() for w in re.findall(r"\b\w+\b", text) if len(w) > 2}


def jaccard(a: set[str], b: set[str]) -> float:
    if not a and not b:
        return 1.0
    union = a | b
    if not union:
        return 0.0
    return len(a & b) / len(union)


def paragraphs(text: str) -> list[str]:
    return [p.strip() for p in re.split(r"\n\n+", text) if p.strip()]


def strip_noise(text: str, stats: SanitizeStats) -> str:
    cleaned = text
    for _, pattern in NOISE_PATTERNS:
        new = pattern.sub("\n\n", cleaned)
        if new != cleaned:
            stats.noise_strips += 1
            cleaned = new
    return sanitize_extracted_text(cleaned)


def is_prunable_tail(chunk: str) -> bool:
    stripped = chunk.strip()
    if not stripped:
        return True
    if NAV_ONLY_RE.search(stripped) and len(stripped.split()) < 80:
        return True
    if TABLE_ARTIFACT_RE.search(stripped) and len(stripped.split()) < 40:
        return True
    lines = [ln.strip() for ln in stripped.splitlines() if ln.strip()]
    link_lines = sum(1 for ln in lines if ln.startswith("* [") or ln.startswith("* "))
    if link_lines >= max(3, len(lines) - 1):
        return True
    return False


def dedupe_paragraphs_within_text(text: str, stats: SanitizeStats) -> str:
    seen: set[str] = set()
    kept: list[str] = []
    for para in paragraphs(text):
        key = re.sub(r"\s+", " ", para.lower()).strip()
        if key in seen:
            stats.duplicate_blocks_removed += 1
            continue
        seen.add(key)
        kept.append(para)
    return "\n\n".join(kept)


def _sentences(text: str) -> list[str]:
    parts = [s.strip() for s in _SENTENCE_SPLIT_RE.split(text) if s.strip()]
    return parts if parts else ([text.strip()] if text.strip() else [])


def _strip_sentence_seam_overlap(prev: str, curr: str) -> str:
    """Remove leading sentences in curr that duplicate trailing sentences in prev."""
    prev_sents = _sentences(prev)
    curr_sents = _sentences(curr)
    if not prev_sents or not curr_sents:
        return curr

    skip = 0
    for n in range(min(4, len(prev_sents)), 0, -1):
        for m in range(1, min(n + 2, len(curr_sents) + 1)):
            tail = " ".join(prev_sents[-n:]).lower()
            head = " ".join(curr_sents[:m]).lower()
            if re.sub(r"\s+", " ", tail).strip() == re.sub(r"\s+", " ", head).strip():
                skip = m
                break
        if skip:
            break

    if skip:
        return " ".join(curr_sents[skip:]).strip()
    return curr


def remove_chunk_duplicates(chunks: list[str], stats: SanitizeStats) -> list[str]:
    if len(chunks) < 2:
        return chunks

    result = [chunks[0]]
    for idx in range(1, len(chunks)):
        prev = result[-1]
        curr = chunks[idx]
        prev_tail = paragraphs(prev)[-3:] if paragraphs(prev) else []
        curr_parts = paragraphs(curr)
        kept: list[str] = []
        for para in curr_parts:
            para_words = tokenize_words(para)
            is_dup = False
            for tail_para in prev_tail:
                if jaccard(para_words, tokenize_words(tail_para)) >= JACCARD_THRESHOLD:
                    stats.duplicate_blocks_removed += 1
                    is_dup = True
                    break
            if not is_dup:
                kept.append(para)
        merged_curr = "\n\n".join(kept).strip()
        merged_curr = _strip_sentence_seam_overlap(prev, merged_curr)
        if merged_curr and merged_curr != prev:
            if len(merged_curr) < len(curr):
                stats.duplicate_blocks_removed += 1
            result.append(merged_curr)
    return dedupe_adjacent_seams(result)


def merge_tail_chunks(chunks: list[str], stats: SanitizeStats) -> list[str]:
    if not chunks:
        return chunks

    while len(chunks) >= 2:
        tail = chunks[-1]
        tail_tokens = count_tokens(tail)
        if tail_tokens >= TAIL_MIN_TOKENS:
            break
        if is_prunable_tail(tail):
            chunks.pop()
            stats.tails_pruned += 1
            continue
        prev = chunks[-2]
        combined_tokens = count_tokens(prev) + tail_tokens
        if combined_tokens <= MAX_MERGED_TOKENS:
            chunks[-2] = f"{prev.rstrip()}\n\n{tail.lstrip()}".strip()
            chunks.pop()
            stats.tails_merged += 1
        else:
            break
    return chunks


def sanitize_document_chunks(chunks: list[str], stats: SanitizeStats) -> list[str]:
    cleaned = [strip_noise(c, stats) for c in chunks if (c or "").strip()]
    cleaned = [dedupe_paragraphs_within_text(c, stats) for c in cleaned]
    cleaned = [c for c in cleaned if c.strip()]
    cleaned = remove_chunk_duplicates(cleaned, stats)
    cleaned = dedupe_adjacent_seams(cleaned)
    cleaned = merge_tail_chunks(cleaned, stats)
    return [sanitize_extracted_text(c) for c in cleaned if c.strip()]


async def reset_all_to_pending() -> int:
    async with SessionLocal() as db:
        await db.execute(
            text("""
                UPDATE dataset_urls
                SET ingestion_status = 'pending',
                    last_error = NULL,
                    updated_at = CURRENT_TIMESTAMP
            """)
        )
        await db.execute(text("UPDATE document_chunks SET embedding = NULL"))
        result = await db.execute(text("SELECT COUNT(*) FROM dataset_urls"))
        await db.commit()
        return int(result.scalar_one())


async def load_url_rows(urls: list[str]) -> list[dict]:
    async with SessionLocal() as db:
        rows = await db.execute(
            text("""
                SELECT id, url, title, service_category, page_type, is_primary_candidate
                FROM dataset_urls WHERE url = ANY(:urls) ORDER BY url
            """),
            {"urls": urls},
        )
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
                        'sanitized_at', CAST(:ts AS text),
                        'sanitize_source', CAST(:src AS text)
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


async def run_sanitize(urls: list[str], *, dry_run: bool) -> tuple[SanitizeStats, list[dict]]:
    stats = SanitizeStats()
    samples: list[dict] = []
    rows = await load_url_rows(urls)
    found = {r["url"] for r in rows}
    missing = [u for u in urls if u not in found]
    if missing:
        print(f"WARNING: {len(missing)} URL(s) not in DB", file=sys.stderr)

    async with SessionLocal() as db:
        for row in rows:
            stats.urls_processed += 1
            old_chunks = await load_chunks(db, row["url"])
            stats.chunks_in += len(old_chunks)
            if not old_chunks and row["url"] in missing:
                continue

            new_chunks = sanitize_document_chunks(old_chunks, stats)
            stats.chunks_out += len(new_chunks)

            entry = {
                "url": row["url"],
                "chunks_in": len(old_chunks),
                "chunks_out": len(new_chunks),
                "preview": (new_chunks[0][:400] if new_chunks else ""),
            }
            samples.append(entry)

            if dry_run:
                print(f"  {row['url']}: {len(old_chunks)} → {len(new_chunks)} chunks")
                continue

            await persist_chunks(db, row, new_chunks)
            stats.urls_updated += 1
        if not dry_run:
            await db.commit()
    return stats, samples


def write_audit_report(
    stats: SanitizeStats,
    samples: list[dict],
    *,
    urls: list[str],
    spot_url: str | None,
    out_json: Path,
    out_md: Path,
) -> None:
    spot_sample = next((s for s in samples if spot_url and spot_url in s["url"]), None)
    if not spot_sample:
        spot_sample = next(
            (s for s in samples if "marketplace" in s["url"] and "prodview" in s["url"]),
            samples[0] if samples else None,
        )

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "scope": "validation_sample_20",
        "embedding_run": False,
        **stats.to_dict(),
        "urls": urls,
        "marketplace_verification": spot_sample,
    }
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    lines = [
        "# Sanitize Chunks Audit Report",
        "",
        f"Generated: {payload['generated_at']}",
        f"Scope: **20 validation sample URLs** (no embedding)",
        "",
        "## Summary",
        "",
        f"| Metric | Count |",
        f"|--------|------:|",
        f"| URLs processed | {stats.urls_processed} |",
        f"| Chunks in | {stats.chunks_in} |",
        f"| Chunks out | {stats.chunks_out} |",
        f"| Duplicate blocks removed | {stats.duplicate_blocks_removed} |",
        f"| Tail chunks merged | {stats.tails_merged} |",
        f"| Tail chunks pruned | {stats.tails_pruned} |",
        f"| Noise sections stripped | {stats.noise_strips} |",
        "",
        "## Marketplace verification sample",
        "",
    ]
    if spot_sample:
        lines.append(f"**URL:** {spot_sample['url']}")
        lines.append(f"Chunks: {spot_sample['chunks_in']} → {spot_sample['chunks_out']}")
        lines.append("")
        lines.append("```text")
        lines.append(spot_sample.get("preview", "")[:1200])
        lines.append("```")
    out_md.write_text("\n".join(lines) + "\n", encoding="utf-8")


async def regenerate_validation_md(urls: list[str], out_path: Path) -> None:
    from generate_validation_sample import render_markdown

    async with SessionLocal() as db:
        docs = []
        for url in urls:
            row = await db.execute(
                text("""
                    SELECT du.url, du.title, du.ingestion_status, du.chunk_count,
                           COALESCE(json_agg(
                               json_build_object(
                                   'chunk_index', dc.chunk_index,
                                   'chunk_text', dc.chunk_text,
                                   'token_count', dc.token_count
                               ) ORDER BY dc.chunk_index
                           ) FILTER (WHERE dc.chunk_text IS NOT NULL), '[]') AS chunks
                    FROM dataset_urls du
                    LEFT JOIN document_chunks dc ON dc.url = du.url
                    WHERE du.url = :url
                    GROUP BY du.url, du.title, du.ingestion_status, du.chunk_count
                """),
                {"url": url},
            )
            docs.append(dict(row.mappings().first()))

    md = render_markdown(
        docs,
        generated_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC") + " (post-sanitize)",
    )
    out_path.write_text(md, encoding="utf-8")


async def main_async(args: argparse.Namespace) -> int:
    if args.reset_all_pending:
        n = await reset_all_to_pending()
        print(f"Reset {n} URLs to ingestion_status='pending' (embeddings cleared)")

    urls: list[str] = []
    if args.urls_file:
        urls = parse_urls_from_markdown(args.urls_file)
    if args.url:
        urls = [args.url]
    if not urls and not args.reset_all_pending:
        print("No URLs specified", file=sys.stderr)
        return 1

    if not urls:
        return 0

    print(f"\nSanitizing {len(urls)} URL(s) dry_run={args.dry_run}")
    stats, samples = await run_sanitize(urls, dry_run=args.dry_run)

    if not args.dry_run:
        out_md = args.output_md or ROOT / "data" / "reports" / "validation_sample_20.md"
        await regenerate_validation_md(urls, out_md)
        print(f"Regenerated {out_md}")

    write_audit_report(
        stats,
        samples,
        urls=urls,
        spot_url=args.spot_url,
        out_json=args.json or ROOT / "data" / "reports" / "sanitize_audit.json",
        out_md=args.audit_md or ROOT / "data" / "reports" / "sanitize_audit.md",
    )
    print(json.dumps(stats.to_dict(), indent=2))
    print(f"\nAudit: {args.json or ROOT / 'data/reports/sanitize_audit.json'}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Sanitize document chunks in PostgreSQL")
    parser.add_argument("--reset-all-pending", action="store_true")
    parser.add_argument("--urls-file", type=Path)
    parser.add_argument("--url")
    parser.add_argument("--apply", action="store_true", help="Write changes (default with --urls-file)")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--json", type=Path)
    parser.add_argument("--audit-md", type=Path)
    parser.add_argument("--output-md", type=Path, help="Regenerated validation markdown")
    parser.add_argument("--spot-url", help="Marketplace doc for verification sample")
    args = parser.parse_args()
    if args.urls_file and not args.dry_run:
        args.dry_run = False
    return asyncio.run(main_async(args))


if __name__ == "__main__":
    raise SystemExit(main())
