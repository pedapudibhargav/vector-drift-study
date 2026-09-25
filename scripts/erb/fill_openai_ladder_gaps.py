#!/usr/bin/env python3
"""Fill missing scale_rank gaps in document_chunks for the 0..N-1 ladder."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "apps" / "api"))
from paths import ERB_DOCS, ERB_MANIFEST, api_pythonpath  # noqa: E402

sys.path.insert(0, str(api_pythonpath()))


def main() -> int:
    from app import ssl_bundle

    ssl_bundle.apply_corporate_ssl_bundle()
    import psycopg
    from app.services.embedding import (
        EMBEDDING_MODEL,
        embed_texts_sync,
        truncate_for_embedding,
        validate_embedding,
        vector_literal,
    )

    max_rank = int(os.environ.get("ERB_MAX_RANK", "100000"))
    url = os.environ.get(
        "DATABASE_URL",
        "postgresql://vector_drift:vector_drift@localhost:5432/vector_drift",
    ).replace("postgresql+asyncpg://", "postgresql://")
    man = json.loads(ERB_MANIFEST.read_text(encoding="utf-8"))
    by_rank = {int(d["scale_rank"]): d for d in man["documents"]}

    def resolve(raw: str) -> Path:
        p = Path(raw)
        return p if p.is_file() else ERB_DOCS / p.name

    def body(path: Path, title: str) -> str:
        text = path.read_text(encoding="utf-8", errors="replace").replace("\x00", "")
        lines = text.splitlines()
        if lines and lines[0].strip() == title:
            b = "\n".join(lines[1:]).strip()
            return f"{title}\n\n{b}" if b else title
        return text

    for round_i in range(8):
        with psycopg.connect(url) as conn:
            cur = conn.cursor()
            cur.execute("SELECT scale_rank FROM document_chunks WHERE scale_rank IS NOT NULL")
            have = {int(r[0]) for r in cur.fetchall()}
            missing = sorted(set(range(max_rank)) - have)
            print(f"round={round_i} missing_n={len(missing)} sample={missing[:10]}", flush=True)
            if not missing:
                break
            to_insert: list[dict] = []
            for r in missing:
                d = by_rank[r]
                cur.execute("SELECT scale_rank FROM document_chunks WHERE doc_id=%s", (d["doc_id"],))
                ex = cur.fetchone()
                if ex is None:
                    to_insert.append(d)
                else:
                    cur.execute(
                        """
                        UPDATE document_chunks
                        SET scale_rank = %s,
                            metadata = metadata || jsonb_build_object('scale_rank', %s::int)
                        WHERE doc_id = %s
                        """,
                        (r, r, d["doc_id"]),
                    )
                    print(f"  reassigned {d['doc_id']} {ex[0]}->{r}", flush=True)
            conn.commit()

        if not to_insert:
            continue
        texts = [
            truncate_for_embedding(body(resolve(d["path"]), d.get("title") or d["doc_id"]))
            for d in to_insert
        ]
        vecs = [validate_embedding(v) for v in embed_texts_sync(texts)]
        with psycopg.connect(url) as conn:
            with conn.cursor() as cur:
                for d, vec, text in zip(to_insert, vecs, texts):
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
                            %s, %s, %s, 0, %s, %s::jsonb, %s::vector, %s, %s, %s
                        )
                        """,
                        (
                            d["doc_id"],
                            d["doc_id"],
                            d.get("title"),
                            text,
                            json.dumps(meta),
                            vector_literal(vec),
                            d["source_type"],
                            d["scale_rank"],
                            d["is_gold_anchor"],
                        ),
                    )
            conn.commit()
        print(f"  inserted {len(to_insert)}", flush=True)

    with psycopg.connect(url) as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT COUNT(DISTINCT scale_rank) FROM document_chunks WHERE scale_rank < %s",
            (max_rank,),
        )
        print(f"FINAL_distinct_lt_{max_rank}={cur.fetchone()[0]}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
