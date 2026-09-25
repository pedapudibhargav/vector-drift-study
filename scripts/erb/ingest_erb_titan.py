#!/usr/bin/env python3
"""Embed ERB docs with Amazon Titan Text Embeddings V2 into document_chunks_titan.

Stateless Bedrock InvokeModel only — vectors stored in local Postgres.
Auth via ambient AWS credentials (AWS_PROFILE / AWS_CONFIG_FILE).

Resilience:
  - per-doc embed failures are logged and skipped (not fatal)
  - missing source files are skipped
  - full traceback on unexpected errors
  - heartbeat file for external watchdogs
"""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import os
import sys
import threading
import time
import traceback
from pathlib import Path

import boto3
from botocore.config import Config

sys.path.insert(0, str(Path(__file__).resolve().parent))
from paths import ERB_DOCS, ERB_MANIFEST, DATA_DIR  # noqa: E402

AWS_PROFILE = os.environ.get("AWS_PROFILE", "").strip() or None
AWS_REGION = os.environ.get("BEDROCK_REGION") or os.environ.get("AWS_REGION", "us-east-1")
TITAN_MODEL = os.environ.get("BEDROCK_EMBED_MODEL_ID", "amazon.titan-embed-text-v2:0")
CHECKPOINT = DATA_DIR / "erb_titan_ingest_checkpoint.json"
HEARTBEAT = DATA_DIR / "erb_titan_ingest_heartbeat.json"
SKIPPED = DATA_DIR / "erb_titan_ingest_skipped.jsonl"
DIM = 1024
MAX_CHARS = int(os.environ.get("TITAN_MAX_CHARS", "24000"))

_thread_local = threading.local()


def _db_url() -> str:
    return os.environ.get(
        "DATABASE_URL",
        "postgresql://vector_drift:vector_drift@localhost:5432/vector_drift",
    ).replace("postgresql+asyncpg://", "postgresql://")


def _client():
    if getattr(_thread_local, "client", None) is None:
        session_kwargs: dict = {"region_name": AWS_REGION}
        if AWS_PROFILE:
            session_kwargs["profile_name"] = AWS_PROFILE
        session = boto3.Session(**session_kwargs)
        _thread_local.client = session.client(
            "bedrock-runtime",
            config=Config(
                retries={"max_attempts": 10, "mode": "standard"},
                read_timeout=120,
                connect_timeout=30,
                max_pool_connections=32,
            ),
        )
    return _thread_local.client


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


def _truncate(text: str, max_chars: int = MAX_CHARS) -> str:
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


def titan_embed_one(text: str) -> list[float]:
    body = json.dumps({"inputText": text, "dimensions": DIM, "normalize": True})
    last: Exception | None = None
    for attempt in range(10):
        try:
            resp = _client().invoke_model(
                modelId=TITAN_MODEL,
                body=body,
                contentType="application/json",
                accept="application/json",
            )
            payload = json.loads(resp["body"].read())
            return _validate(payload.get("embedding") or [])
        except Exception as exc:  # noqa: BLE001
            last = exc
            # Back off harder on throttling
            delay = min(2**attempt, 60)
            print(f"embed_retry attempt={attempt+1} sleep={delay}s err={type(exc).__name__}: {exc}", flush=True)
            time.sleep(delay)
    raise RuntimeError(f"titan embed failed: {last}") from last


def titan_embed(texts: list[str], *, workers: int) -> list[list[float] | None]:
    """Embed batch; failed items become None (caller skips)."""
    if not texts:
        return []
    out: list[list[float] | None] = [None] * len(texts)
    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, workers)) as ex:
        futs = {ex.submit(titan_embed_one, t): i for i, t in enumerate(texts)}
        for fut in concurrent.futures.as_completed(futs):
            i = futs[fut]
            try:
                out[i] = fut.result()
            except Exception as exc:  # noqa: BLE001
                print(f"embed_item_failed idx={i} err={exc}", flush=True)
                out[i] = None
    return out


def vector_literal(vec: list[float]) -> str:
    return "[" + ",".join(f"{x:.8f}" for x in vec) + "]"


def _write_heartbeat(*, count: int, status: str, detail: str = "") -> None:
    HEARTBEAT.parent.mkdir(parents=True, exist_ok=True)
    HEARTBEAT.write_text(
        json.dumps(
            {
                "pid": os.getpid(),
                "count": count,
                "status": status,
                "detail": detail,
                "updated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            }
        ),
        encoding="utf-8",
    )


def _save_checkpoint(done: set[str]) -> None:
    CHECKPOINT.parent.mkdir(parents=True, exist_ok=True)
    CHECKPOINT.write_text(
        json.dumps(
            {
                "done_doc_ids": sorted(done),
                "count": len(done),
                "model": TITAN_MODEL,
                "updated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            }
        ),
        encoding="utf-8",
    )


def _log_skip(doc_id: str, reason: str) -> None:
    SKIPPED.parent.mkdir(parents=True, exist_ok=True)
    with SKIPPED.open("a", encoding="utf-8") as f:
        f.write(json.dumps({"doc_id": doc_id, "reason": reason, "ts": time.time()}) + "\n")


def _smoke_db(conn, *, expect_min: int = 1) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT COUNT(*), COUNT(DISTINCT doc_id),
                   COUNT(*) FILTER (WHERE embedding IS NULL),
                   COUNT(*) FILTER (WHERE length(trim(chunk_text))=0)
            FROM document_chunks_titan
            """
        )
        rows, distinct, null_emb, empty = cur.fetchone()
        cur.execute("SELECT vector_dims(embedding) FROM document_chunks_titan LIMIT 1")
        dim_row = cur.fetchone()
    if rows != distinct:
        raise RuntimeError(f"titan dup rows={rows} distinct={distinct}")
    if null_emb or empty:
        raise RuntimeError(f"titan null_emb={null_emb} empty_text={empty}")
    if rows >= expect_min and dim_row and int(dim_row[0]) != DIM:
        raise RuntimeError(f"titan dim={dim_row[0]} want={DIM}")
    print(
        f"SMOKE_TITAN rows={rows} distinct={distinct} null_emb={null_emb} empty={empty}",
        flush=True,
    )


def main() -> int:
    import psycopg

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=ERB_MANIFEST)
    parser.add_argument("--limit", type=int, default=100_000)
    parser.add_argument("--batch-size", type=int, default=24)
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--checkpoint", type=Path, default=CHECKPOINT)
    parser.add_argument("--reset-checkpoint", action="store_true")
    parser.add_argument("--max-rank", type=int, default=100_000)
    parser.add_argument("--smoke-every", type=int, default=500)
    args = parser.parse_args()

    try:
        probe = titan_embed_one("titan ingest probe")
        assert len(probe) == DIM
        print(f"probe_ok model={TITAN_MODEL} region={AWS_REGION} dim={DIM}", flush=True)

        manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
        docs = [d for d in manifest["documents"] if int(d["scale_rank"]) < args.max_rank]
        docs.sort(key=lambda d: int(d["scale_rank"]))
        if args.limit and args.limit > 0:
            docs = docs[: args.limit]

        done: set[str] = set()
        if args.checkpoint.exists() and not args.reset_checkpoint:
            done = set(
                json.loads(args.checkpoint.read_text(encoding="utf-8")).get("done_doc_ids", [])
            )

        pending = [d for d in docs if d["doc_id"] not in done]
        print(
            f"titan ingest pending={len(pending)} already={len(done)} "
            f"batch={args.batch_size} workers={args.workers} pid={os.getpid()}",
            flush=True,
        )
        _write_heartbeat(count=len(done), status="start")

        conn = psycopg.connect(_db_url())
        last_smoke = len(done)
        t0 = time.time()
        try:
            for start in range(0, len(pending), args.batch_size):
                batch = pending[start : start + args.batch_size]
                texts: list[str | None] = []
                for d in batch:
                    try:
                        texts.append(
                            _truncate(
                                _read_body(
                                    _resolve_doc_path(d["path"]),
                                    d.get("title") or d["doc_id"],
                                )
                            )
                        )
                    except Exception as exc:  # noqa: BLE001
                        print(f"skip_read doc={d['doc_id']} err={exc}", flush=True)
                        _log_skip(d["doc_id"], f"read:{exc}")
                        texts.append(None)

                embed_inputs = [t if t is not None else "" for t in texts]
                # Only embed real texts; map results back
                real_idx = [i for i, t in enumerate(texts) if t is not None]
                real_texts = [texts[i] for i in real_idx]  # type: ignore[misc]
                real_vecs = titan_embed(real_texts, workers=args.workers) if real_texts else []
                vec_by_i: dict[int, list[float] | None] = {
                    i: v for i, v in zip(real_idx, real_vecs)
                }

                upserted = 0
                with conn.cursor() as cur:
                    for i, d in enumerate(batch):
                        if texts[i] is None:
                            continue
                        vec = vec_by_i.get(i)
                        if vec is None:
                            _log_skip(d["doc_id"], "embed_failed")
                            continue
                        meta = {
                            "doc_id": d["doc_id"],
                            "source_type": d["source_type"],
                            "scale_rank": d["scale_rank"],
                            "is_gold_anchor": d["is_gold_anchor"],
                            "title": d.get("title"),
                            "embedding_model": TITAN_MODEL,
                            "study": "enterprise_rag_bench",
                            "arm": "titan_v2",
                        }
                        cur.execute(
                            """
                            INSERT INTO document_chunks_titan (
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
                                "text": texts[i],
                                "metadata": json.dumps(meta),
                                "embedding": vector_literal(vec),
                                "source_type": d["source_type"],
                                "scale_rank": d["scale_rank"],
                                "is_gold_anchor": d["is_gold_anchor"],
                            },
                        )
                        done.add(d["doc_id"])
                        upserted += 1
                conn.commit()
                _save_checkpoint(done)
                elapsed = max(time.time() - t0, 1e-6)
                rate = (len(done) - (len(docs) - len(pending))) / elapsed * 60
                print(
                    f"titan upserted {len(done)}/{len(docs)} "
                    f"(+{upserted}) rate~{rate:.0f}/min",
                    flush=True,
                )
                _write_heartbeat(count=len(done), status="running")
                if len(done) - last_smoke >= args.smoke_every:
                    _smoke_db(conn)
                    last_smoke = len(done)
            _smoke_db(conn)
            _write_heartbeat(count=len(done), status="complete")
        finally:
            conn.close()
        print("titan ingest complete", flush=True)
        return 0
    except Exception:
        traceback.print_exc()
        _write_heartbeat(count=-1, status="crashed", detail=traceback.format_exc()[-500:])
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
