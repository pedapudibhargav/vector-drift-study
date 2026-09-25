#!/usr/bin/env python3
"""
Full corpus embedding quality audit for document_chunks (pgvector).

Usage:
  python verify_embeddings.py
  python verify_embeddings.py --json reports/embedding_audit.json
  python verify_embeddings.py --skip-semantic

Run inside API container:
  docker exec vector-drift-api python /app/verify_embeddings.py
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path

import psycopg
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
_API_ROOT = ROOT / "apps" / "api"
if not (_API_ROOT / "app").exists() and (ROOT / "app").exists():
    _API_ROOT = ROOT
sys.path.insert(0, str(_API_ROOT))

load_dotenv(ROOT / ".env")

from app.config import resolve_openai_api_key  # noqa: E402
from app.services.embedding import (  # noqa: E402
    EMBEDDING_DIMENSIONS,
    EMBEDDING_MODEL,
    embed_texts_sync,
)

HIGH_SIM_QUERY = "How do Knowledge Bases work in Bedrock?"
HIGH_SIM_THRESHOLD = 0.75
LOW_SIM_THRESHOLD = 0.40
NORM_TOLERANCE = 0.02
VECTOR_BATCH_SIZE = 2000


@dataclass
class CheckResult:
    name: str
    passed: bool
    detail: str
    metrics: dict = field(default_factory=dict)


def resolve_dsn() -> str:
    in_docker = Path("/.dockerenv").exists() or Path("/app/app").exists()

    raw = os.getenv("DATABASE_URL", "")
    if not raw:
        try:
            from app.config import settings

            raw = settings.database_url
        except Exception:
            raw = ""

    if in_docker and (not raw or "@localhost:" in raw or "@vector-drift-db:" in raw):
        user = os.getenv("POSTGRES_USER", "vector_drift")
        password = os.getenv("POSTGRES_PASSWORD", "vector_drift")
        db = os.getenv("POSTGRES_DB", "vector_drift")
        raw = f"postgresql://{user}:{password}@vector-drift-postgres:5432/{db}"
    elif not raw:
        raw = "postgresql://postgres:postgres@localhost:5432/vector_drift_db"

    dsn = raw.replace("postgresql+asyncpg://", "postgresql://")
    if not in_docker:
        dsn = dsn.replace("@vector-drift-db:", "@localhost:")
        dsn = dsn.replace("@vector-drift-postgres:", "@localhost:")
    return dsn


def parse_vector(raw) -> list[float]:
    if raw is None:
        return []
    if isinstance(raw, (list, tuple)):
        return [float(v) for v in raw]
    text = str(raw).strip()
    if text.startswith("[") and text.endswith("]"):
        text = text[1:-1]
    if not text:
        return []
    return [float(part) for part in text.split(",")]


def l2_norm(vector: list[float]) -> float:
    return math.sqrt(sum(v * v for v in vector))


def cosine_similarity(a: list[float], b: list[float]) -> float:
    if len(a) != len(b) or not a:
        return 0.0
    return sum(x * y for x, y in zip(a, b))


def check_url_pipeline(conn: psycopg.Connection) -> CheckResult:
    row = conn.execute("""
        SELECT
            (SELECT COUNT(*) FROM dataset_urls WHERE http_status = 200) AS urls_total,
            (SELECT COUNT(*) FROM dataset_urls WHERE html_content IS NULL) AS urls_no_html,
            (SELECT COUNT(*) FROM dataset_urls
             WHERE text_content IS NULL OR btrim(text_content) = '') AS urls_no_text,
            (SELECT COUNT(*) FROM dataset_urls WHERE ingestion_status = 'text_failed') AS urls_text_failed,
            (SELECT COUNT(*) FROM dataset_urls WHERE last_error IS NOT NULL) AS urls_with_error,
            (SELECT COUNT(*) FROM dataset_urls du
             WHERE NOT EXISTS (SELECT 1 FROM document_chunks dc WHERE dc.url = du.url)) AS urls_no_chunks,
            (SELECT COUNT(*) FROM dataset_urls du
             WHERE EXISTS (SELECT 1 FROM document_chunks dc WHERE dc.url = du.url AND dc.embedding IS NULL)
            ) AS urls_missing_vectors,
            (SELECT COUNT(*) FROM dataset_urls du
             WHERE EXISTS (SELECT 1 FROM document_chunks dc WHERE dc.url = du.url)
               AND NOT EXISTS (
                   SELECT 1 FROM document_chunks dc
                   WHERE dc.url = du.url AND dc.embedding IS NULL
               )) AS urls_fully_embedded
    """).fetchone()

    metrics = {
        "urls_total": row[0],
        "urls_no_html": row[1],
        "urls_no_text": row[2],
        "urls_text_failed": row[3],
        "urls_with_error": row[4],
        "urls_no_chunks": row[5],
        "urls_missing_vectors": row[6],
        "urls_fully_embedded": row[7],
    }
    bad = (
        metrics["urls_no_html"]
        + metrics["urls_no_text"]
        + metrics["urls_text_failed"]
        + metrics["urls_with_error"]
        + metrics["urls_no_chunks"]
        + metrics["urls_missing_vectors"]
    )
    passed = bad == 0 and metrics["urls_fully_embedded"] == metrics["urls_total"]
    detail = (
        f"total={metrics['urls_total']}, fully_embedded={metrics['urls_fully_embedded']}, "
        f"text_failed={metrics['urls_text_failed']}, missing_vectors={metrics['urls_missing_vectors']}, "
        f"no_html={metrics['urls_no_html']}, no_text={metrics['urls_no_text']}, "
        f"no_chunks={metrics['urls_no_chunks']}, last_error={metrics['urls_with_error']}"
    )
    return CheckResult("url_pipeline", passed, detail, metrics)


def check_chunk_integrity(conn: psycopg.Connection) -> CheckResult:
    row = conn.execute("""
        SELECT
            (SELECT COUNT(*) FROM document_chunks) AS chunks_total,
            (SELECT COUNT(*) FROM document_chunks dc
             WHERE NOT EXISTS (SELECT 1 FROM dataset_urls du WHERE du.url = dc.url)) AS orphan_chunks,
            (SELECT COUNT(*) FROM document_chunks
             WHERE chunk_text IS NULL OR btrim(chunk_text) = '') AS empty_chunks,
            (SELECT COUNT(*) FROM document_chunks
             WHERE token_count IS NULL OR token_count > 512) AS token_violations,
            (SELECT COUNT(*) FROM (
                SELECT url, chunk_index FROM document_chunks
                GROUP BY url, chunk_index HAVING COUNT(*) > 1
            ) d) AS duplicate_keys,
            (SELECT COUNT(*) FROM dataset_urls du
             WHERE du.chunk_count <> (
                 SELECT COUNT(*) FROM document_chunks dc WHERE dc.url = du.url
             )) AS chunk_count_mismatch
    """).fetchone()

    metrics = {
        "chunks_total": row[0],
        "orphan_chunks": row[1],
        "empty_chunks": row[2],
        "token_violations": row[3],
        "duplicate_keys": row[4],
        "chunk_count_mismatch": row[5],
    }
    bad = sum(v for k, v in metrics.items() if k != "chunks_total")
    passed = bad == 0
    detail = (
        f"total={metrics['chunks_total']}, orphan={metrics['orphan_chunks']}, "
        f"empty={metrics['empty_chunks']}, token_violations={metrics['token_violations']}, "
        f"duplicate_keys={metrics['duplicate_keys']}, chunk_count_mismatch={metrics['chunk_count_mismatch']}"
    )
    return CheckResult("chunk_integrity", passed, detail, metrics)


def check_dimensionality(conn: psycopg.Connection) -> CheckResult:
    row = conn.execute(
        """
        SELECT
            COUNT(*) AS total,
            COUNT(embedding) AS with_embedding,
            COUNT(*) FILTER (
                WHERE embedding IS NULL OR vector_dims(embedding) <> %s
            ) AS bad_rows
        FROM document_chunks
        """,
        (EMBEDDING_DIMENSIONS,),
    ).fetchone()

    total, with_embedding, bad_rows = row
    metrics = {
        "total": total,
        "with_embedding": with_embedding,
        "bad_rows": bad_rows,
        "expected_dim": EMBEDDING_DIMENSIONS,
    }
    if total == 0:
        return CheckResult("vector_dimensionality", False, "no rows in document_chunks", metrics)
    passed = bad_rows == 0 and with_embedding == total
    detail = (
        f"total={total}, embedded={with_embedding}, bad_or_null={bad_rows}, "
        f"expected_dim={EMBEDDING_DIMENSIONS}"
    )
    return CheckResult("vector_dimensionality", passed, detail, metrics)


def check_metadata(conn: psycopg.Connection) -> CheckResult:
    row = conn.execute(
        """
        SELECT
            COUNT(*) FILTER (
                WHERE embedding IS NOT NULL
                  AND (metadata->>'embedded') IS DISTINCT FROM 'true'
            ) AS meta_embed_flag_bad,
            COUNT(*) FILTER (
                WHERE embedding IS NOT NULL
                  AND COALESCE(metadata->>'embedding_model', '') <> %s
            ) AS meta_model_bad,
            COUNT(*) FILTER (
                WHERE embedding IS NULL AND (metadata->>'embedded') = 'true'
            ) AS embedded_flag_without_vector
        FROM document_chunks
        """,
        (EMBEDDING_MODEL,),
    ).fetchone()

    metrics = {
        "meta_embed_flag_bad": row[0],
        "meta_model_bad": row[1],
        "embedded_flag_without_vector": row[2],
    }
    bad = sum(metrics.values())
    passed = bad == 0
    detail = (
        f"wrong_embed_flag={metrics['meta_embed_flag_bad']}, "
        f"wrong_model={metrics['meta_model_bad']}, "
        f"flag_without_vector={metrics['embedded_flag_without_vector']}, "
        f"expected_model={EMBEDDING_MODEL}"
    )
    return CheckResult("metadata_consistency", passed, detail, metrics)


def check_all_vector_norms(conn: psycopg.Connection) -> CheckResult:
    """Scan every stored vector for finiteness and L2 norm ≈ 1."""
    total = conn.execute(
        "SELECT COUNT(*) FROM document_chunks WHERE embedding IS NOT NULL"
    ).fetchone()[0]
    if total == 0:
        return CheckResult("vector_norms_full", False, "no embedded vectors", {"scanned": 0})

    scanned = 0
    dim_bad = 0
    non_finite = 0
    norm_outlier_count = 0
    sample_outliers: list[dict] = []
    min_norm = float("inf")
    max_norm = 0.0
    sum_norm = 0.0

    with conn.cursor(name="vector_norm_scan") as cur:
        cur.itersize = VECTOR_BATCH_SIZE
        cur.execute("""
            SELECT id, url, chunk_index, embedding::text
            FROM document_chunks
            WHERE embedding IS NOT NULL
            ORDER BY id
        """)
        for chunk_id, url, chunk_index, raw in cur:
            vec = parse_vector(raw)
            scanned += 1

            if len(vec) != EMBEDDING_DIMENSIONS:
                dim_bad += 1
                if len(sample_outliers) < 10:
                    sample_outliers.append({
                        "id": chunk_id, "url": url, "chunk_index": chunk_index,
                        "issue": "bad_dim", "dim": len(vec),
                    })
                continue

            if not all(math.isfinite(v) for v in vec):
                non_finite += 1
                if len(sample_outliers) < 10:
                    sample_outliers.append({
                        "id": chunk_id, "url": url, "chunk_index": chunk_index,
                        "issue": "non_finite",
                    })
                continue

            norm = l2_norm(vec)
            min_norm = min(min_norm, norm)
            max_norm = max(max_norm, norm)
            sum_norm += norm
            if abs(norm - 1.0) > NORM_TOLERANCE:
                norm_outlier_count += 1
                if len(sample_outliers) < 10:
                    sample_outliers.append({
                        "id": chunk_id, "url": url, "chunk_index": chunk_index,
                        "issue": "norm_outlier", "norm": round(norm, 6),
                    })

    avg_norm = sum_norm / max(scanned - dim_bad - non_finite, 1)
    metrics = {
        "scanned": scanned,
        "dim_bad": dim_bad,
        "non_finite": non_finite,
        "norm_outliers": norm_outlier_count,
        "avg_norm": round(avg_norm, 6),
        "min_norm": round(min_norm, 6) if min_norm != float("inf") else None,
        "max_norm": round(max_norm, 6),
        "tolerance": NORM_TOLERANCE,
        "sample_outliers": sample_outliers,
    }
    passed = dim_bad == 0 and non_finite == 0 and norm_outlier_count == 0
    detail = (
        f"scanned={scanned}, dim_bad={dim_bad}, non_finite={non_finite}, "
        f"norm_outliers(>{NORM_TOLERANCE})={norm_outlier_count}, "
        f"avg={avg_norm:.6f}, min={metrics['min_norm']}, max={metrics['max_norm']}"
    )
    return CheckResult("vector_norms_full", passed, detail, metrics)


def fetch_anchor_chunk(
    conn: psycopg.Connection,
    *,
    url_pattern: str,
    chunk_text_pattern: str | None = None,
    exclude_url_pattern: str | None = None,
) -> tuple[str, str, list[float]] | None:
    clauses = ["dc.embedding IS NOT NULL", "dc.url ILIKE %s"]
    params: list = [url_pattern]
    if chunk_text_pattern:
        clauses.append("dc.chunk_text ILIKE %s")
        params.append(chunk_text_pattern)
    if exclude_url_pattern:
        clauses.append("dc.url NOT ILIKE %s")
        params.append(exclude_url_pattern)

    row = conn.execute(
        f"""
        SELECT dc.url, dc.chunk_text, dc.embedding::text
        FROM document_chunks dc
        WHERE {' AND '.join(clauses)}
        ORDER BY dc.token_count DESC, dc.chunk_index
        LIMIT 1
        """,
        tuple(params),
    ).fetchone()
    if not row:
        return None
    return row[0], row[1], parse_vector(row[2])


def check_semantic_similarity(
    conn: psycopg.Connection,
    *,
    api_key: str,
    strict: bool,
) -> CheckResult:
    bedrock = fetch_anchor_chunk(
        conn,
        url_pattern="%bedrock/knowledge-bases%",
        chunk_text_pattern="%how does it work%",
    )
    if not bedrock:
        bedrock = fetch_anchor_chunk(
            conn,
            url_pattern="%bedrock/knowledge-bases%",
            chunk_text_pattern="%Knowledge Base%",
        )
    if not bedrock:
        return CheckResult("semantic_sanity", False, "no embedded chunk on bedrock/knowledge-bases product URL")

    low_topic = fetch_anchor_chunk(
        conn,
        url_pattern="%sagemaker/canvas%",
        exclude_url_pattern="%blog%",
    )
    if not low_topic:
        low_topic = fetch_anchor_chunk(conn, url_pattern="%ec2%on-demand%pricing%")
    if not low_topic:
        low_topic = fetch_anchor_chunk(conn, url_pattern="%ec2%pricing%")
    if not low_topic:
        return CheckResult("semantic_sanity", False, "no embedded chunk for SageMaker Canvas or EC2 Pricing")

    bedrock_url, bedrock_text, bedrock_vec = bedrock
    low_url, low_text, low_vec = low_topic

    query_vec = embed_texts_sync([HIGH_SIM_QUERY], api_key=api_key)[0]
    high_sim = cosine_similarity(query_vec, bedrock_vec)
    low_sim = cosine_similarity(bedrock_vec, low_vec)

    high_ok = high_sim > HIGH_SIM_THRESHOLD
    low_ok = low_sim < LOW_SIM_THRESHOLD
    passed = high_ok and low_ok if strict else True
    metrics = {
        "high_similarity": round(high_sim, 4),
        "high_threshold": HIGH_SIM_THRESHOLD,
        "high_ok": high_ok,
        "low_similarity": round(low_sim, 4),
        "low_threshold": LOW_SIM_THRESHOLD,
        "low_ok": low_ok,
        "strict_mode": strict,
        "bedrock_url": bedrock_url,
        "low_url": low_url,
        "model": EMBEDDING_MODEL,
    }
    detail = (
        f"query_vs_bedrock={high_sim:.4f} (target>{HIGH_SIM_THRESHOLD}, "
        f"{'PASS' if high_ok else 'FAIL'}); "
        f"bedrock_vs_other={low_sim:.4f} (target<{LOW_SIM_THRESHOLD}, "
        f"{'PASS' if low_ok else 'FAIL'}); "
        f"bedrock_url={bedrock_url}; other_url={low_url}"
    )
    return CheckResult("semantic_sanity", passed, detail, metrics)


def run_audit(
    conn: psycopg.Connection,
    *,
    skip_semantic: bool,
    strict_semantic: bool,
    api_key: str,
) -> list[CheckResult]:
    checks = [
        check_url_pipeline(conn),
        check_chunk_integrity(conn),
        check_dimensionality(conn),
        check_metadata(conn),
        check_all_vector_norms(conn),
    ]
    if not skip_semantic:
        checks.append(check_semantic_similarity(conn, api_key=api_key, strict=strict_semantic))
    else:
        checks.append(CheckResult("semantic_sanity", True, "skipped (--skip-semantic)", {"skipped": True}))
    return checks


def main() -> int:
    parser = argparse.ArgumentParser(description="Full corpus embedding quality audit")
    parser.add_argument("--dsn", default="", help="Override PostgreSQL DSN")
    parser.add_argument("--json", dest="json_path", default="", help="Write JSON report to path")
    parser.add_argument("--skip-semantic", action="store_true", help="Skip live OpenAI semantic probe")
    parser.add_argument(
        "--strict-semantic",
        action="store_true",
        help="Fail audit when semantic smoke thresholds are not met (default: advisory only)",
    )
    args = parser.parse_args()

    api_key = resolve_openai_api_key()
    if not args.skip_semantic and (not api_key or api_key.startswith("sk-your")):
        print("FAIL env: OPENAI_API_KEY missing — use --skip-semantic or set root .env")
        return 1

    dsn = args.dsn or resolve_dsn()
    try:
        with psycopg.connect(dsn) as conn:
            results = run_audit(
                conn,
                skip_semantic=args.skip_semantic,
                strict_semantic=args.strict_semantic,
                api_key=api_key,
            )
    except Exception as exc:
        print(f"FAIL connection: {exc}")
        print(f"  DSN target: {dsn.split('@')[-1]}")
        return 1

    all_ok = True
    for result in results:
        if result.name == "semantic_sanity" and not result.metrics.get("strict_mode") and not result.metrics.get("skipped"):
            sem_ok = result.metrics.get("high_ok") and result.metrics.get("low_ok")
            status = "PASS" if sem_ok else "WARN"
        else:
            status = "PASS" if result.passed else "FAIL"
        print(f"[{status}] {result.name}: {result.detail}")
        all_ok = all_ok and result.passed

    print(f"\nOverall: {'PASS — corpus clean' if all_ok else 'FAIL — review metrics above'}")

    if args.json_path:
        out = Path(args.json_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "model": EMBEDDING_MODEL,
            "dimensions": EMBEDDING_DIMENSIONS,
            "overall_pass": all_ok,
            "checks": [asdict(r) for r in results],
        }
        out.write_text(json.dumps(payload, indent=2))
        print(f"Report written: {out}")

    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
