#!/usr/bin/env python3
"""Embed and upsert EnterpriseRAG documents into pgvector (one vector per doc)."""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from paths import ERB_DOCS, ERB_INGEST_CHECKPOINT, ERB_MANIFEST, api_pythonpath  # noqa: E402

sys.path.insert(0, str(api_pythonpath()))


def _load_env() -> None:
    for env_path in (Path("/app/.env"), Path(__file__).resolve().parents[2] / ".env"):
        if not env_path.exists():
            continue
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
        break


def _resolve_doc_path(raw: str) -> Path:
    p = Path(raw)
    if p.is_file():
        return p
    candidate = ERB_DOCS / p.name
    if candidate.is_file():
        return candidate
    raise FileNotFoundError(raw)

def _db_url() -> str:
    url = os.environ.get("DATABASE_URL") or os.environ.get(
        "ERB_DATABASE_URL",
        "postgresql://vector_drift:vector_drift@localhost:5432/vector_drift",
    )
    return url.replace("postgresql+asyncpg://", "postgresql://")


def _read_body(path: Path, title: str) -> str:
    text = path.read_text(encoding="utf-8", errors="replace").replace("\x00", "")
    lines = text.splitlines()
    if lines and lines[0].strip() == title:
        body = "\n".join(lines[1:]).strip()
        return f"{title}\n\n{body}" if body else title
    return text


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=ERB_MANIFEST)
    parser.add_argument("--batch-size", type=int, default=50)
    parser.add_argument("--limit", type=int, default=0, help="Max docs to ingest (0=all)")
    parser.add_argument("--checkpoint", type=Path, default=ERB_INGEST_CHECKPOINT)
    parser.add_argument("--reset-checkpoint", action="store_true")
    parser.add_argument(
        "--max-rank",
        type=int,
        default=100_000,
        help="Only docs with scale_rank < max-rank (default 100k ladder)",
    )
    args = parser.parse_args()

    _load_env()

    # Optional local TLS-intercept CA (corp-proxy.pem) before OpenAI HTTPS.
    from app import ssl_bundle  # noqa: WPS433

    ssl_bundle.apply_corporate_ssl_bundle()

    import psycopg
    from app.services.embedding import (  # noqa: WPS433
        EMBEDDING_MODEL,
        embed_texts_sync,
        truncate_for_embedding,
        validate_embedding,
        vector_literal,
    )

    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    docs = [d for d in manifest["documents"] if int(d["scale_rank"]) < args.max_rank]
    docs.sort(key=lambda d: int(d["scale_rank"]))
    if args.limit and args.limit > 0:
        docs = docs[: args.limit]

    done: set[str] = set()
    if args.checkpoint.exists() and not args.reset_checkpoint:
        done = set(json.loads(args.checkpoint.read_text(encoding="utf-8")).get("done_doc_ids", []))

    pending = [d for d in docs if d["doc_id"] not in done]
    print(f"ingest pending={len(pending)} already={len(done)} model={EMBEDDING_MODEL}")

    conn = psycopg.connect(_db_url())
    try:
        for start in range(0, len(pending), args.batch_size):
            batch = pending[start : start + args.batch_size]
            texts = [
                truncate_for_embedding(
                    _read_body(_resolve_doc_path(d["path"]), d.get("title") or d["doc_id"])
                )
                for d in batch
            ]
            try:
                from cost_tracker import assert_budget  # noqa: WPS433

                assert_budget()
            except RuntimeError as exc:
                print(f"BUDGET HALT: {exc}", flush=True)
                return 2
            vectors = embed_texts_sync(texts)
            if len(vectors) != len(batch):
                raise RuntimeError(
                    f"embed count mismatch: got {len(vectors)} for batch {len(batch)}"
                )
            vectors = [validate_embedding(v) for v in vectors]
            try:
                from cost_tracker import record_embedding  # noqa: WPS433

                try:
                    from app.services.embedding import get_encoding  # noqa: WPS433

                    tok = sum(len(get_encoding().encode(t)) for t in texts)
                except Exception:
                    # Fallback if tiktoken download/SSL fails — approx 4 chars/token.
                    tok = sum(max(1, len(t) // 4) for t in texts)
                record_embedding(tokens=tok, docs=len(batch), note=f"batch@{len(done)}")
            except Exception as exc:
                print(f"cost_tracker warn: {exc}")
            with conn.cursor() as cur:
                for d, vec, text in zip(batch, vectors, texts):
                    meta = {
                        "doc_id": d["doc_id"],
                        "source_type": d["source_type"],
                        "scale_rank": d["scale_rank"],
                        "is_gold_anchor": d["is_gold_anchor"],
                        "title": d.get("title"),
                        "embedding_model": EMBEDDING_MODEL,
                        "study": "enterprise_rag_bench",
                    }
                    cur.execute(
                        """
                        INSERT INTO document_chunks (
                            url, doc_id, title, chunk_index, chunk_text,
                            metadata, embedding, source_type, scale_rank, is_gold_anchor
                        ) VALUES (
                            %(url)s, %(doc_id)s, %(title)s, 0, %(text)s,
                            %(metadata)s::jsonb, %(embedding)s::vector,
                            %(source_type)s, %(scale_rank)s, %(is_gold_anchor)s
                        )
                        ON CONFLICT (url, chunk_index) DO UPDATE SET
                            doc_id = EXCLUDED.doc_id,
                            title = EXCLUDED.title,
                            chunk_text = EXCLUDED.chunk_text,
                            metadata = EXCLUDED.metadata,
                            embedding = EXCLUDED.embedding,
                            source_type = EXCLUDED.source_type,
                            scale_rank = EXCLUDED.scale_rank,
                            is_gold_anchor = EXCLUDED.is_gold_anchor
                        """,
                        {
                            "url": d["doc_id"],
                            "doc_id": d["doc_id"],
                            "title": d.get("title"),
                            "text": text,
                            "metadata": json.dumps(meta),
                            "embedding": vector_literal(vec),
                            "source_type": d["source_type"],
                            "scale_rank": d["scale_rank"],
                            "is_gold_anchor": d["is_gold_anchor"],
                        },
                    )
            conn.commit()
            for d in batch:
                done.add(d["doc_id"])
            args.checkpoint.parent.mkdir(parents=True, exist_ok=True)
            args.checkpoint.write_text(
                json.dumps(
                    {
                        "done_doc_ids": sorted(done),
                        "count": len(done),
                        "updated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    }
                ),
                encoding="utf-8",
            )
            print(f"upserted {len(done)}/{len(docs)}")
    finally:
        conn.close()
    print("ingest complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
