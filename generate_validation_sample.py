#!/usr/bin/env python3
"""Export N random full-text documents with chunk numbering for manual validation."""

from __future__ import annotations

import argparse
import asyncio
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "apps" / "api"))

from sqlalchemy import text  # noqa: E402

from app.db.session import SessionLocal  # noqa: E402


async def fetch_random_documents(
    n: int,
    *,
    status: str | None = "chunked",
) -> list[dict]:
    status_clause = ""
    params: dict = {"n": n}
    if status:
        status_clause = "AND du.ingestion_status = :status"
        params["status"] = status

    async with SessionLocal() as db:
        rows = await db.execute(
            text(f"""
                SELECT du.url, du.title, du.ingestion_status, du.chunk_count,
                       COALESCE(
                           json_agg(
                               json_build_object(
                                   'chunk_index', dc.chunk_index,
                                   'chunk_text', dc.chunk_text,
                                   'token_count', dc.token_count
                               )
                               ORDER BY dc.chunk_index
                           ) FILTER (WHERE dc.chunk_text IS NOT NULL),
                           '[]'
                       ) AS chunks
                FROM dataset_urls du
                JOIN document_chunks dc ON dc.url = du.url
                WHERE 1=1 {status_clause}
                GROUP BY du.url, du.title, du.ingestion_status, du.chunk_count
                HAVING COUNT(dc.id) > 0
                ORDER BY random()
                LIMIT :n
            """),
            params,
        )
        return [dict(r) for r in rows.mappings()]


def render_markdown(documents: list[dict], *, generated_at: str) -> str:
    lines = [
        "# Chunk Validation Sample",
        "",
        f"Generated: {generated_at}",
        f"Documents: {len(documents)}",
        "",
        "Use this file to manually verify text quality before running vector embedding.",
        "",
        "---",
        "",
    ]

    for doc_idx, doc in enumerate(documents, start=1):
        url = doc["url"]
        title = doc.get("title") or "(no title)"
        status = doc.get("ingestion_status") or "unknown"
        chunks = doc.get("chunks") or []
        if isinstance(chunks, str):
            import json
            chunks = json.loads(chunks)

        lines.append(f"## Document {doc_idx}")
        lines.append("")
        lines.append(f"- **URL:** {url}")
        lines.append(f"- **Title:** {title}")
        lines.append(f"- **Stage:** `{status}`")
        lines.append(f"- **Chunk count:** {len(chunks)}")
        lines.append("")

        for chunk in chunks:
            idx = chunk.get("chunk_index", 0)
            tokens = chunk.get("token_count")
            text_body = (chunk.get("chunk_text") or "").strip()
            lines.append(f"### Chunk {idx}")
            if tokens is not None:
                lines.append(f"*Tokens: {tokens} | Words: ~{len(text_body.split())}*")
            lines.append("")
            lines.append("```text")
            lines.append(text_body)
            lines.append("```")
            lines.append("")

        lines.append("---")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


async def main_async(args: argparse.Namespace) -> int:
    documents = await fetch_random_documents(args.count)
    if not documents:
        print("No documents found.", file=sys.stderr)
        return 1

    md = render_markdown(
        documents,
        generated_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(md, encoding="utf-8")
    print(f"Wrote {len(documents)} documents to {args.output}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate random chunk validation markdown")
    parser.add_argument("--count", type=int, default=20)
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "data" / "reports" / "validation_sample_20.md",
    )
    args = parser.parse_args()
    return asyncio.run(main_async(args))


if __name__ == "__main__":
    raise SystemExit(main())
