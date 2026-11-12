#!/usr/bin/env python3
"""Embed manifest pool-extension documents (scale_rank >= 100k) into rev1.pool_ext_openai.

Replicates scripts/erb/ingest_erb.py text assembly and apps/api embedding truncation/validation,
using urllib for OpenAI embeddings (no openai package).
"""

from __future__ import annotations

import argparse
import json
import os
import ssl
import sys
import threading
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

import psycopg2
from psycopg2 import sql

ROOT = Path(__file__).resolve().parents[3]
MANIFEST_PATH = ROOT / "data" / "erb_scale_manifest.json"
ERB_DOCS = Path(__file__).resolve().parents[3] / "data" / "enterprise_rag_bench" / "documents"
SPEND_LOG = ROOT / "data" / "pool_embed_spend.jsonl"
TIKTOKEN_CACHE_DIR = ROOT / "data" / "tiktoken_cache"

EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIMENSIONS = 1536
MAX_INPUT_TOKENS = 8191
EMBED_BATCH_SIZE = 100
MAX_REQUEST_TOKENS = 250_000
MAX_RETRIES = 8
INITIAL_BACKOFF_S = 2.0
ENCODING_NAME = "cl100k_base"
USD_PER_M_TOKENS = 0.02
DEFAULT_MAX_USD = 4.0
PROGRESS_EVERY = 1000

_enc = None
_enc_lock = threading.Lock()
_tiktoken_unavailable = False


def _ensure_tiktoken_cache_env() -> None:
    TIKTOKEN_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("TIKTOKEN_CACHE_DIR", str(TIKTOKEN_CACHE_DIR))


def get_encoding():
    global _enc, _tiktoken_unavailable
    with _enc_lock:
        if _enc is not None:
            return _enc
        if _tiktoken_unavailable:
            return None
        _ensure_tiktoken_cache_env()
        try:
            import tiktoken
        except ImportError:
            _tiktoken_unavailable = True
            return None
        _enc = tiktoken.get_encoding(ENCODING_NAME)
        return _enc


def require_tiktoken() -> None:
    if get_encoding() is None:
        raise SystemExit(
            "tiktoken is required for --dry-run. Install tiktoken and set "
            f"TIKTOKEN_CACHE_DIR={TIKTOKEN_CACHE_DIR}"
        )


def read_body(path: Path, title: str) -> str:
    text = path.read_text(encoding="utf-8", errors="replace").replace("\x00", "")
    lines = text.splitlines()
    if lines and lines[0].strip() == title:
        body = "\n".join(lines[1:]).strip()
        return f"{title}\n\n{body}" if body else title
    return text


def truncate_for_embedding(text: str) -> str:
    enc = get_encoding()
    if enc is not None:
        try:
            tokens = enc.encode(text, disallowed_special=())
            if len(tokens) <= MAX_INPUT_TOKENS:
                return text
            return enc.decode(tokens[:MAX_INPUT_TOKENS])
        except Exception:
            pass
    max_chars = MAX_INPUT_TOKENS * 4
    return text if len(text) <= max_chars else text[:max_chars]


def token_count(text: str) -> int:
    enc = get_encoding()
    if enc is not None:
        try:
            return len(enc.encode(text, disallowed_special=()))
        except Exception:
            pass
    return max(1, len(text) // 4)


def vector_literal(vec: list[float]) -> str:
    return "[" + ",".join(str(v) for v in vec) + "]"


def validate_embedding(vec: list[float], *, dims: int = EMBEDDING_DIMENSIONS) -> list[float]:
    if not vec or len(vec) != dims:
        raise ValueError(f"bad embedding length={len(vec) if vec else 0} expected={dims}")
    norm_sq = 0.0
    for x in vec:
        if x != x or x in (float("inf"), float("-inf")):
            raise ValueError("embedding contains non-finite values")
        norm_sq += float(x) * float(x)
    if norm_sq < 1e-12:
        raise ValueError("embedding near-zero norm")
    return vec


def pg_connect():
    return psycopg2.connect(
        host=os.environ.get("PGHOST", "localhost"),
        port=os.environ.get("PGPORT", "5432"),
        user=os.environ["PGUSER"],
        password=os.environ["PGPASSWORD"],
        dbname=os.environ["PGDATABASE"],
    )


def parse_table_name(qualified: str) -> tuple[str, str]:
    if "." not in qualified:
        raise ValueError(f"--table must be schema-qualified (e.g. rev1.pool_ext_openai), got {qualified!r}")
    schema, table = qualified.split(".", 1)
    if not schema or not table:
        raise ValueError(f"invalid --table {qualified!r}")
    return schema, table


def ensure_target_table(conn, qualified: str) -> None:
    schema, table = parse_table_name(qualified)
    with conn.cursor() as cur:
        cur.execute(
            sql.SQL(
                """
                CREATE TABLE IF NOT EXISTS {}.{} (
                    doc_id text PRIMARY KEY,
                    source_type text,
                    manifest_scale_rank int,
                    token_count int,
                    embedding vector(1536),
                    embedded_at timestamptz
                )
                """
            ).format(sql.Identifier(schema), sql.Identifier(table))
        )
    conn.commit()


def load_manifest() -> dict:
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def build_path_index() -> dict[str, list[Path]]:
    index: dict[str, list[Path]] = {}
    for path in ERB_DOCS.rglob("*.txt"):
        index.setdefault(path.name, []).append(path)
    return index


def resolve_doc_path(manifest_path: str, path_index: dict[str, list[Path]]) -> Path:
    name = Path(manifest_path).name
    candidates = path_index.get(name, [])
    if not candidates:
        direct = ERB_DOCS / name
        if direct.is_file():
            return direct
        raise FileNotFoundError(name)
    if len(candidates) == 1:
        return candidates[0]
    preferred = ERB_DOCS / name
    if len(candidates) > 1:
        bodies = {p: p.read_bytes() for p in candidates}
        distinct = len({v for v in bodies.values()})
        if distinct > 1:
            print(
                f"WARN path mismatch for {name}: {len(candidates)} copies differ",
                file=sys.stderr,
                flush=True,
            )
    if preferred in candidates:
        return preferred
    for p in candidates:
        if p.name == name:
            return p
    return candidates[0]


def manifest_by_doc_id(manifest: dict) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for doc in manifest.get("documents") or []:
        did = str(doc.get("doc_id") or "")
        if not did:
            continue
        rank = int(doc.get("scale_rank") or 0)
        prev = out.get(did)
        if prev is None or rank >= int(prev.get("scale_rank") or 0):
            out[did] = doc
    return out


def pool_extension_docs(
    manifest: dict,
    *,
    skip_doc_ids: set[str],
    source_type: str | None,
) -> list[dict]:
    by_id: dict[str, dict] = {}
    for doc in manifest.get("documents") or []:
        if int(doc.get("scale_rank") or 0) < 100_000:
            continue
        did = str(doc.get("doc_id") or "")
        if not did or did in skip_doc_ids:
            continue
        if source_type and str(doc.get("source_type")) != source_type:
            continue
        prev = by_id.get(did)
        if prev is None or int(doc["scale_rank"]) >= int(prev["scale_rank"]):
            by_id[did] = doc
    docs = list(by_id.values())
    docs.sort(key=lambda d: (str(d.get("source_type") or ""), int(d["scale_rank"]), d["doc_id"]))
    return docs


TRUNCATION_OVERRIDES: dict | None = None


def assemble_embed_text(doc: dict, path_index: dict[str, list[Path]]) -> tuple[str, int]:
    path = resolve_doc_path(str(doc.get("path") or ""), path_index)
    title = doc.get("title") or doc["doc_id"]
    raw = read_body(path, title)
    if TRUNCATION_OVERRIDES is not None:
        # tiktoken-exact truncation was precomputed (override file lists every document above 8,191 tokens)
        text = TRUNCATION_OVERRIDES.get(doc["doc_id"], raw)
        return text, max(1, len(text) // 4)
    text = truncate_for_embedding(raw)
    return text, token_count(text)


def existing_doc_ids(conn, qualified: str) -> set[str]:
    schema, table = parse_table_name(qualified)
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT 1 FROM information_schema.tables
            WHERE table_schema = %s AND table_name = %s
            """,
            (schema, table),
        )
        if not cur.fetchone():
            return set()
        cur.execute(
            sql.SQL("SELECT doc_id FROM {}.{}").format(sql.Identifier(schema), sql.Identifier(table))
        )
        return {str(r[0]) for r in cur.fetchall()}


def embedded_in_document_chunks(conn) -> set[str]:
    with conn.cursor() as cur:
        cur.execute("SELECT doc_id FROM document_chunks WHERE embedding IS NOT NULL")
        return {str(r[0]) for r in cur.fetchall()}


def read_spend_usd() -> float:
    if not SPEND_LOG.is_file():
        return 0.0
    total_tokens = 0
    with SPEND_LOG.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
                total_tokens += int(rec.get("tokens") or 0)
            except json.JSONDecodeError:
                continue
    return total_tokens * USD_PER_M_TOKENS / 1_000_000.0


def append_spend(tokens: int, docs: int, *, lock: threading.Lock) -> None:
    rec = {
        "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "tokens": tokens,
        "docs": docs,
    }
    SPEND_LOG.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(rec) + "\n"
    with lock:
        with SPEND_LOG.open("a", encoding="utf-8") as f:
            f.write(line)


class SpendGuard:
    def __init__(self, max_usd: float):
        self.max_usd = max_usd
        self.lock = threading.Lock()
        self.spent_usd = read_spend_usd()
        self.halt = threading.Event()

    def add_tokens(self, tokens: int, docs: int) -> bool:
        if tokens <= 0:
            return True
        with self.lock:
            if self.halt.is_set():
                return False
            self.spent_usd += tokens * USD_PER_M_TOKENS / 1_000_000.0
            if self.spent_usd >= self.max_usd:
                self.halt.set()
                return False
        append_spend(tokens, docs, lock=self.lock)
        return not self.halt.is_set()

    def remaining_usd(self) -> float:
        with self.lock:
            return max(0.0, self.max_usd - self.spent_usd)


def embeddings_url(base_url: str) -> str:
    base = base_url.rstrip("/")
    if base.endswith("/v1/embeddings"):
        return base
    return f"{base}/v1/embeddings"


def _is_retryable_http(code: int) -> bool:
    return code in (429, 500, 502, 503, 504)


def embed_batch(
    texts: list[str],
    *,
    base_url: str,
    api_key: str,
    ssl_ctx: ssl.SSLContext | None,
) -> tuple[list[list[float]], int]:
    url = embeddings_url(base_url)
    payload = json.dumps(
        {
            "model": EMBEDDING_MODEL,
            "input": texts,
            "dimensions": EMBEDDING_DIMENSIONS,
        }
    ).encode("utf-8")
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    last_err: Exception | None = None
    for attempt in range(MAX_RETRIES):
        req = urllib.request.Request(url, data=payload, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=120, context=ssl_ctx) as resp:
                body = resp.read()
            data = json.loads(body.decode("utf-8"))
            usage = data.get("usage") or {}
            total_tokens = int(usage.get("total_tokens") or 0)
            items = sorted(data.get("data") or [], key=lambda x: int(x.get("index", 0)))
            vectors = [validate_embedding(list(item["embedding"])) for item in items]
            if len(vectors) != len(texts):
                raise RuntimeError(f"embedding count {len(vectors)} != batch {len(texts)}")
            return vectors, total_tokens
        except urllib.error.HTTPError as exc:
            last_err = exc
            if not _is_retryable_http(exc.code) or attempt == MAX_RETRIES - 1:
                raise
            delay = INITIAL_BACKOFF_S * (2**attempt)
            ra = exc.headers.get("Retry-After")
            if ra:
                try:
                    delay = max(delay, float(ra))
                except ValueError:
                    pass
            time.sleep(delay)
        except Exception as exc:
            last_err = exc
            if attempt == MAX_RETRIES - 1:
                raise
            time.sleep(INITIAL_BACKOFF_S * (2**attempt))
    raise RuntimeError(f"embedding batch failed: {last_err}")


def make_batches(
    rows: list[tuple[dict, str, int]],
) -> list[list[tuple[dict, str, int]]]:
    """Split (doc, text, token_count) rows into API batches."""
    batches: list[list[tuple[dict, str, int]]] = []
    cur: list[tuple[dict, str, int]] = []
    cur_tokens = 0
    for item in rows:
        _, _, tc = item
        if cur and (
            len(cur) >= EMBED_BATCH_SIZE or cur_tokens + tc > MAX_REQUEST_TOKENS
        ):
            batches.append(cur)
            cur = []
            cur_tokens = 0
        cur.append(item)
        cur_tokens += tc
    if cur:
        batches.append(cur)
    return batches


def insert_batch(
    conn,
    qualified: str,
    batch: list[tuple[dict, str, int, list[float]]],
) -> int:
    schema, table = parse_table_name(qualified)
    now = datetime.now(timezone.utc)
    inserted = 0
    with conn.cursor() as cur:
        for doc, text, tok, vec in batch:
            cur.execute(
                sql.SQL(
                    """
                    INSERT INTO {}.{} (
                        doc_id, source_type, manifest_scale_rank, token_count, embedding, embedded_at
                    ) VALUES (%s, %s, %s, %s, %s::vector, %s)
                    ON CONFLICT (doc_id) DO NOTHING
                    """
                ).format(sql.Identifier(schema), sql.Identifier(table)),
                (
                    doc["doc_id"],
                    doc.get("source_type"),
                    int(doc["scale_rank"]),
                    tok,
                    vector_literal(vec),
                    now,
                ),
            )
            if cur.rowcount:
                inserted += 1
    conn.commit()
    return inserted


def run_dry_run(docs: list[dict], path_index: dict[str, list[Path]]) -> int:
    require_tiktoken()
    missing: list[str] = []
    total_tokens = 0
    for i, doc in enumerate(docs, 1):
        try:
            _, tc = assemble_embed_text(doc, path_index)
            total_tokens += tc
        except FileNotFoundError:
            missing.append(str(doc.get("path")))
        if i % 5000 == 0:
            print(f"dry-run scanned {i}/{len(docs)}", flush=True)
    est_usd = total_tokens * USD_PER_M_TOKENS / 1_000_000.0
    print(f"dry_run_documents={len(docs)}")
    print(f"dry_run_total_tokens={total_tokens}")
    print(f"dry_run_estimated_usd={est_usd:.6f}")
    print(f"dry_run_missing_files={len(missing)}")
    if missing:
        print("dry_run_missing_sample:")
        for p in missing[:20]:
            print(f"  {p}")
    return 0 if not missing else 2


def run_acceptance_test(*, sample_size: int = 100) -> int:
    manifest = load_manifest()
    by_id = manifest_by_doc_id(manifest)
    path_index = build_path_index()
    conn = pg_connect()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT doc_id, title, chunk_text
                FROM document_chunks
                WHERE scale_rank < 100000 AND NOT is_gold_anchor
                ORDER BY random()
                LIMIT %s
                """,
                (sample_size,),
            )
            rows = cur.fetchall()
    finally:
        conn.close()
    if len(rows) < sample_size:
        print(f"acceptance WARN: only {len(rows)} rows available", flush=True)
    matches = 0
    mismatches: list[dict] = []
    for doc_id, title, chunk_text in rows:
        doc = by_id.get(doc_id)
        if not doc:
            mismatches.append({"doc_id": doc_id, "reason": "missing manifest"})
            continue
        try:
            path = resolve_doc_path(str(doc.get("path") or ""), path_index)
        except FileNotFoundError:
            mismatches.append({"doc_id": doc_id, "reason": "missing file"})
            continue
        rebuilt = truncate_for_embedding(
            read_body(path, title or doc.get("title") or doc_id)
        )
        if rebuilt == (chunk_text or ""):
            matches += 1
        else:
            mismatches.append(
                {
                    "doc_id": doc_id,
                    "rebuilt_len": len(rebuilt),
                    "chunk_len": len(chunk_text or ""),
                    "rebuilt_head": rebuilt[:120],
                    "chunk_head": (chunk_text or "")[:120],
                }
            )
    print(f"acceptance_sample_size={len(rows)}")
    print(f"acceptance_exact_matches={matches}")
    print(f"acceptance_mismatches={len(mismatches)}")
    if mismatches:
        print("acceptance_mismatch_sample:")
        print(json.dumps(mismatches[:5], indent=2))
    return 0 if matches == len(rows) and not mismatches else 1


def run_embed(args: argparse.Namespace) -> int:
    global TRUNCATION_OVERRIDES
    if args.truncation_overrides:
        TRUNCATION_OVERRIDES = json.loads(Path(args.truncation_overrides).read_text(encoding='utf-8'))
    manifest = load_manifest()
    path_index = build_path_index()
    conn = pg_connect()
    try:
        ensure_target_table(conn, args.table)
        done = existing_doc_ids(conn, args.table)
        skip = embedded_in_document_chunks(conn)
        skip |= done
        docs = pool_extension_docs(manifest, skip_doc_ids=skip, source_type=args.source_type)
        if args.limit and args.limit > 0:
            docs = docs[: args.limit]
        if not docs:
            print("embed nothing pending")
            return 0

        api_key = os.environ.get("OPENAI_API_KEY") or ""
        if not api_key and not args.base_url.startswith("http://127.0.0.1"):
            print("OPENAI_API_KEY not set", file=sys.stderr)
            return 2

        ssl_ctx = None if args.base_url.startswith("http://127.0.0.1") else ssl.create_default_context()
        spend = SpendGuard(args.max_usd)
        print(
            f"embed pending={len(docs)} table={args.table} workers={args.workers} "
            f"spent_usd={spend.spent_usd:.4f} max_usd={args.max_usd}",
            flush=True,
        )

        prepared: list[tuple[dict, str, int]] = []
        for doc in docs:
            try:
                text, tc = assemble_embed_text(doc, path_index)
                prepared.append((doc, text, tc))
            except FileNotFoundError as exc:
                print(f"skip missing file doc_id={doc['doc_id']} path={exc}", file=sys.stderr)

        batches = make_batches(prepared)
        progress = {"embedded": 0}
        progress_lock = threading.Lock()

        def process_batch(batch: list[tuple[dict, str, int]]) -> int:
            if spend.halt.is_set():
                return 0
            texts = [t for _, t, _ in batch]
            vectors, total_tokens = embed_batch(
                texts, base_url=args.base_url, api_key=api_key, ssl_ctx=ssl_ctx
            )
            if not spend.add_tokens(total_tokens, len(batch)):
                return 0
            payload = [
                (doc, text, tok, vec)
                for (doc, text, tok), vec in zip(batch, vectors)
            ]
            local_conn = pg_connect()
            try:
                n = insert_batch(local_conn, args.table, payload)
            finally:
                local_conn.close()
            with progress_lock:
                progress["embedded"] += n
                if progress["embedded"] % PROGRESS_EVERY == 0 or progress["embedded"] == len(prepared):
                    print(
                        f"progress embedded={progress['embedded']}/{len(prepared)} "
                        f"spent_usd≈{spend.spent_usd:.4f} remaining≈{spend.remaining_usd():.4f}",
                        flush=True,
                    )
            return n

        with ThreadPoolExecutor(max_workers=args.workers) as pool:
            futures = [pool.submit(process_batch, b) for b in batches]
            for fut in as_completed(futures):
                if spend.halt.is_set():
                    break
                try:
                    fut.result()
                except Exception as exc:
                    print(f"batch error: {exc}", file=sys.stderr, flush=True)
                    return 1
        if spend.halt.is_set():
            print("halted: --max-usd budget reached", flush=True)
            return 3
        print(f"embed complete inserted≈{progress['embedded']}", flush=True)
        return 0
    finally:
        conn.close()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--truncation-overrides", type=str, default=None, help="JSON {doc_id: truncated text} for documents above 8,191 tokens (computed with tiktoken elsewhere)")
    parser.add_argument("--dry-run", action="store_true", help="Count docs/tokens/cost only")
    parser.add_argument("--acceptance-test", action="store_true", help="Compare text rebuild vs document_chunks")
    parser.add_argument("--limit", type=int, default=0, help="Max documents to process")
    parser.add_argument("--source-type", type=str, default=None, help="Filter manifest source_type")
    parser.add_argument("--max-usd", type=float, default=DEFAULT_MAX_USD)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--base-url", type=str, default="https://api.openai.com")
    parser.add_argument("--table", type=str, default="rev1.pool_ext_openai")
    args = parser.parse_args()

    if args.acceptance_test:
        return run_acceptance_test()

    manifest = load_manifest()
    path_index = build_path_index()
    conn = pg_connect()
    try:
        skip = embedded_in_document_chunks(conn)
        if not args.dry_run:
            ensure_target_table(conn, args.table)
            skip |= existing_doc_ids(conn, args.table)
        docs = pool_extension_docs(manifest, skip_doc_ids=skip, source_type=args.source_type)
    finally:
        conn.close()
    if args.limit and args.limit > 0:
        docs = docs[: args.limit]

    if args.dry_run:
        return run_dry_run(docs, path_index)
    return run_embed(args)


if __name__ == "__main__":
    raise SystemExit(main())
