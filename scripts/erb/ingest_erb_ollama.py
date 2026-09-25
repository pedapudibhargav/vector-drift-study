#!/usr/bin/env python3
"""Embed ERB docs with Ollama nomic-embed-text into document_chunks_ollama.

Parallel arm — does not touch OpenAI document_chunks.

Speed: prefers /api/embed batch; falls back to concurrent /api/embeddings.
Quality: dim/finite/norm checks on every vector; optional --smoke-every.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from paths import ERB_DOCS, ERB_MANIFEST, DATA_DIR  # noqa: E402

OLLAMA_MODEL = os.environ.get("OLLAMA_EMBED_MODEL", "nomic-embed-text")
OLLAMA_URL = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434").rstrip("/")
CHECKPOINT = DATA_DIR / "erb_ollama_ingest_checkpoint.json"
DIM = 768
DEFAULT_WORKERS = max(4, min(12, (os.cpu_count() or 8) - 2))


def _db_url() -> str:
    return os.environ.get(
        "DATABASE_URL",
        "postgresql://vector_drift:vector_drift@localhost:5432/vector_drift",
    ).replace("postgresql+asyncpg://", "postgresql://")


def _resolve_doc_path(raw: str) -> Path:
    p = Path(raw)
    if p.is_file():
        return p
    candidate = ERB_DOCS / p.name
    if candidate.is_file():
        return candidate
    raise FileNotFoundError(raw)


def _read_body(path: Path, title: str) -> str:
    text = path.read_text(encoding="utf-8", errors="replace").replace("\x00", "")
    lines = text.splitlines()
    if lines and lines[0].strip() == title:
        body = "\n".join(lines[1:]).strip()
        return f"{title}\n\n{body}" if body else title
    return text


def _truncate(text: str, max_chars: int = 6_000) -> str:
    """nomic-embed-text context is 2048 tokens — keep inputs small for speed/stability."""
    if len(text) <= max_chars:
        return text
    return text[:max_chars]


def _validate(emb: list[float]) -> list[float]:
    if not emb or len(emb) != DIM:
        raise RuntimeError(f"bad embedding dim={len(emb) if emb else None} want={DIM}")
    norm_sq = 0.0
    for x in emb:
        if x != x or x in (float("inf"), float("-inf")):
            raise RuntimeError("embedding non-finite")
        norm_sq += float(x) * float(x)
    if norm_sq < 1e-12:
        raise RuntimeError("embedding near-zero")
    return emb


def _post_json(path: str, payload: dict, timeout: int = 300) -> dict:
    data = json.dumps(payload).encode()
    last_err: Exception | None = None
    for attempt in range(8):
        req = urllib.request.Request(
            f"{OLLAMA_URL}{path}",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode())
        except Exception as exc:  # noqa: BLE001
            last_err = exc
            time.sleep(min(2**attempt, 20))
    raise RuntimeError(f"ollama {path} failed: {last_err}") from last_err


def _embed_one(text: str) -> list[float]:
    data = _post_json("/api/embeddings", {"model": OLLAMA_MODEL, "prompt": text}, timeout=180)
    return _validate(data.get("embedding") or [])


def ollama_embed(texts: list[str], *, workers: int, prefer_batch: bool = False) -> list[list[float]]:
    """Concurrent /api/embeddings by default (stable on Metal). Optional /api/embed batch."""
    if not texts:
        return []
    if prefer_batch and len(texts) <= 8:
        try:
            data = _post_json("/api/embed", {"model": OLLAMA_MODEL, "input": texts}, timeout=180)
            embs = data.get("embeddings")
            if isinstance(embs, list) and len(embs) == len(texts):
                return [_validate(e) for e in embs]
        except Exception as exc:  # noqa: BLE001
            print(f"batch /api/embed fallback ({exc})", flush=True)

    out: list[list[float] | None] = [None] * len(texts)
    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, workers)) as ex:
        futs = {ex.submit(_embed_one, t): i for i, t in enumerate(texts)}
        for fut in concurrent.futures.as_completed(futs):
            out[futs[fut]] = fut.result()
    if any(e is None for e in out):
        raise RuntimeError("incomplete embed results")
    return out  # type: ignore[return-value]


def vector_literal(vec: list[float]) -> str:
    return "[" + ",".join(f"{x:.8f}" for x in vec) + "]"


def _smoke_db(conn, *, expect_min: int = 1) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT COUNT(*), COUNT(DISTINCT doc_id),
                   COUNT(*) FILTER (WHERE embedding IS NULL),
                   COUNT(*) FILTER (WHERE length(trim(chunk_text))=0)
            FROM document_chunks_ollama
            """
        )
        rows, distinct, null_emb, empty = cur.fetchone()
        cur.execute("SELECT vector_dims(embedding) FROM document_chunks_ollama LIMIT 1")
        dim_row = cur.fetchone()
    if rows != distinct:
        raise RuntimeError(f"ollama dup rows={rows} distinct={distinct}")
    if null_emb or empty:
        raise RuntimeError(f"ollama null_emb={null_emb} empty_text={empty}")
    if rows >= expect_min and dim_row and int(dim_row[0]) != DIM:
        raise RuntimeError(f"ollama dim={dim_row[0]} want={DIM}")
    print(
        f"SMOKE_OLLAMA rows={rows} distinct={distinct} null_emb={null_emb} empty={empty}",
        flush=True,
    )


def main() -> int:
    import psycopg

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=ERB_MANIFEST)
    parser.add_argument("--limit", type=int, default=100_000)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--workers", type=int, default=DEFAULT_WORKERS)
    parser.add_argument("--checkpoint", type=Path, default=CHECKPOINT)
    parser.add_argument("--reset-checkpoint", action="store_true")
    parser.add_argument("--max-rank", type=int, default=100_000)
    parser.add_argument("--smoke-every", type=int, default=200, help="DB smoke every N upserts")
    args = parser.parse_args()

    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    docs = [d for d in manifest["documents"] if int(d["scale_rank"]) < args.max_rank]
    docs.sort(key=lambda d: int(d["scale_rank"]))
    if args.limit and args.limit > 0:
        docs = docs[: args.limit]

    done: set[str] = set()
    if args.checkpoint.exists() and not args.reset_checkpoint:
        done = set(json.loads(args.checkpoint.read_text(encoding="utf-8")).get("done_doc_ids", []))

    pending = [d for d in docs if d["doc_id"] not in done]
    print(
        f"ollama ingest model={OLLAMA_MODEL} pending={len(pending)} "
        f"already={len(done)} max_rank={args.max_rank} "
        f"batch={args.batch_size} workers={args.workers}",
        flush=True,
    )

    probe = ollama_embed(["ping"], workers=1)
    assert len(probe[0]) == DIM
    print("probe_ok dim=768", flush=True)

    conn = psycopg.connect(_db_url())
    last_smoke = len(done)
    t0 = time.time()
    try:
        for start in range(0, len(pending), args.batch_size):
            batch = pending[start : start + args.batch_size]
            texts = [
                _truncate(_read_body(_resolve_doc_path(d["path"]), d.get("title") or d["doc_id"]))
                for d in batch
            ]
            vectors = ollama_embed(texts, workers=args.workers)
            if len(vectors) != len(batch):
                raise RuntimeError(f"embed count mismatch {len(vectors)}!={len(batch)}")
            with conn.cursor() as cur:
                for d, vec, text in zip(batch, vectors, texts):
                    meta = {
                        "doc_id": d["doc_id"],
                        "source_type": d["source_type"],
                        "scale_rank": d["scale_rank"],
                        "is_gold_anchor": d["is_gold_anchor"],
                        "title": d.get("title"),
                        "embedding_model": OLLAMA_MODEL,
                        "study": "enterprise_rag_bench",
                        "arm": "ollama",
                    }
                    cur.execute(
                        """
                        INSERT INTO document_chunks_ollama (
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
                        "model": OLLAMA_MODEL,
                        "updated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    }
                ),
                encoding="utf-8",
            )
            elapsed = max(time.time() - t0, 1e-6)
            rate = (len(done) - (len(docs) - len(pending))) / elapsed * 60
            print(
                f"ollama upserted {len(done)}/{len(docs)} rate~{rate:.0f}/min",
                flush=True,
            )
            if len(done) - last_smoke >= args.smoke_every:
                _smoke_db(conn)
                last_smoke = len(done)
        _smoke_db(conn)
    finally:
        conn.close()
    print("ollama ingest complete", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
