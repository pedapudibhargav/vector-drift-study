#!/usr/bin/env python3
"""Document length / token statistics and OpenAI 8,191-token cut offsets (revision W6).

Step 1 (host venv, psycopg2): export document_chunks pool to data/rev1_doc_pool.jsonl.
Step 2 (Docker image with official tiktoken): write per-doc chars/tokens/cut_char_8191.
  Do not regenerate data/rev1_doc_token_cuts.jsonl on the host; the manager runs tiktoken in Docker.
Step 3 (host): aggregate artifacts/published/revision1/.

Text used for OpenAI cuts (and primary char stats):
  coalesce(title,'') + ' ' + coalesce(chunk_text,'')
matching scripts/erb/run_bm25_baseline.py. Alternate stats use chunk_text only.
Tokenizer: tiktoken cl100k_base, encode(..., disallowed_special=()).
OpenAI truncate rule: tokens > 8191 (apps/api/app/services/embedding.py MAX_INPUT_TOKENS).
Ingest already truncated chunk_text to 8,191 tokens (scripts/erb/ingest_erb.py ~108-110).
Titan truncate rule: chars > 24000 (scripts/erb/ingest_erb_titan.py MAX_CHARS).
Headline stats use the ladder pool: embedding IS NOT NULL AND scale_rank IS NOT NULL
AND scale_rank < 100000.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
import psycopg2

ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / "data"
PUB = ROOT / "artifacts" / "published"
OUT = PUB / "revision1"
MANIFEST = DATA / "erb_scale_manifest.json"
PRIMARY200 = PUB / "primary_questions_200.json"
POOL_JSONL = DATA / "rev1_doc_pool.jsonl"
CUTS_JSONL = DATA / "rev1_doc_token_cuts.jsonl"
SPOT_JSON = DATA / "rev1_token_spot_check.json"
HELPER_SRC = Path(__file__).resolve().parent / "doc_token_stats_tiktoken.py"
HELPER_DST = DATA / "doc_token_stats_tiktoken.py"
DOCKER = "/Applications/Docker.app/Contents/Resources/bin/docker"
IMAGE = "vector-drift-research-vector-drift-api:latest"
RAW_DOCS = Path(__file__).resolve().parents[3] / "data" / "enterprise_rag_bench" / "documents"
MAX_TOK = 8191
TITAN_CHARS = 24000
LADDER_N = 100_000
CHAR_THRESHOLDS = (4000, 8191, 24000)


def _connect():
    return psycopg2.connect(
        host=os.environ["PGHOST"],
        port=os.environ["PGPORT"],
        user=os.environ["PGUSER"],
        password=os.environ["PGPASSWORD"],
        dbname=os.environ["PGDATABASE"],
    )


def export_pool() -> int:
    DATA.mkdir(parents=True, exist_ok=True)
    n = 0
    conn = _connect()
    try:
        cur = conn.cursor(name="rev1_doc_export")
        cur.itersize = 2000
        cur.execute(
            """
            SELECT doc_id, source_type, scale_rank, is_gold_anchor, title, chunk_text,
                   (embedding IS NOT NULL) AS has_embedding
            FROM document_chunks
            ORDER BY doc_id
            """
        )
        with POOL_JSONL.open("w", encoding="utf-8") as f:
            for (
                doc_id,
                source_type,
                scale_rank,
                is_gold_anchor,
                title,
                chunk_text,
                has_embedding,
            ) in cur:
                title_s = title or ""
                chunk_s = chunk_text or ""
                rec = {
                    "doc_id": doc_id,
                    "source_type": source_type,
                    "scale_rank": scale_rank,
                    "is_gold_anchor": bool(is_gold_anchor),
                    "has_embedding": bool(has_embedding),
                    "chunk_starts_with_title": bool(title_s) and chunk_s.startswith(title_s),
                    "title": title,
                    "chunk_text": chunk_text,
                }
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                n += 1
                if n % 10000 == 0:
                    print(f"exported {n}", flush=True)
    finally:
        conn.close()
    print(f"export complete n={n} -> {POOL_JSONL}", flush=True)
    return n


def run_tiktoken_container() -> None:
    shutil.copy2(HELPER_SRC, HELPER_DST)
    cmd = [
        DOCKER,
        "run",
        "--rm",
        "--entrypoint",
        "python",
        "-v",
        f"{DATA}:/work",
        "-e",
        "TIKTOKEN_CACHE_DIR=/work/tiktoken_cache",
        IMAGE,
        "/work/doc_token_stats_tiktoken.py",
    ]
    print("running:", " ".join(cmd), flush=True)
    try:
        subprocess.run(cmd, check=True)
    except (FileNotFoundError, PermissionError, subprocess.CalledProcessError, OSError) as exc:
        raise SystemExit(
            "tiktoken is required and must be the official package "
            f"(Docker image {IMAGE}). Docker run failed ({exc!r}). "
            "No pure-Python fallback. Do not regenerate "
            "data/rev1_doc_token_cuts.jsonl on the host."
        ) from exc


def _pcts(vals: list[int]) -> dict:
    if not vals:
        return {"count": 0, "median": None, "p90": None, "max": None}
    arr = np.asarray(vals, dtype=np.int64)
    return {
        "count": int(arr.size),
        "median": float(np.percentile(arr, 50)),
        "p90": float(np.percentile(arr, 90)),
        "max": int(arr.max()),
    }


def _fracs(chars: list[int], tokens: list[int]) -> dict:
    n = len(chars)
    out = {}
    for t in CHAR_THRESHOLDS:
        c = sum(1 for x in chars if x > t)
        out[f"gt_{t}_chars"] = {"count": c, "fraction": (c / n if n else None)}
    ctok = sum(1 for x in tokens if x > MAX_TOK)
    ctok_ge = sum(1 for x in tokens if x >= MAX_TOK)
    out["gt_8191_tokens"] = {"count": ctok, "fraction": (ctok / n if n else None)}
    out["ge_8191_tokens"] = {"count": ctok_ge, "fraction": (ctok_ge / n if n else None)}
    return out


def _block(rows: list[dict], key: str) -> dict:
    chars = [r[key]["chars"] for r in rows]
    tokens = [r[key]["tokens"] for r in rows]
    block = _pcts(chars)
    block.update(_fracs(chars, tokens))
    block["char_field"] = key
    return block


def primary200_gold_ids() -> list[str]:
    primary = json.loads(PRIMARY200.read_text(encoding="utf-8"))
    qids = list(primary["question_ids"])
    man = json.loads(MANIFEST.read_text(encoding="utf-8"))
    qmap = {}
    for q in man["questions"]:
        qmap[q["eval_id"]] = q
        qmap[q["question_id"]] = q
    missing = [qid for qid in qids if qid not in qmap]
    if missing:
        raise SystemExit(f"primary-200 eval ids missing from manifest: {missing[:5]}")
    gold: set[str] = set()
    for qid in qids:
        gold.update(qmap[qid]["expected_doc_ids"])
    return sorted(gold)


def _in_ladder(meta: dict) -> bool:
    rank = meta.get("scale_rank")
    return bool(meta.get("has_embedding")) and rank is not None and int(rank) < LADDER_N


def _ingest_read_body(path: Path, title: str) -> str:
    text = path.read_text(encoding="utf-8", errors="replace").replace("\x00", "")
    lines = text.splitlines()
    if lines and lines[0].strip() == title:
        body = "\n".join(lines[1:]).strip()
        return f"{title}\n\n{body}" if body else title
    return text


def _index_raw_paths(needed: set[str]) -> dict[str, Path]:
    found: dict[str, Path] = {}
    if not RAW_DOCS.is_dir():
        raise SystemExit(f"raw document directory missing: {RAW_DOCS}")
    with os.scandir(RAW_DOCS) as it:
        for ent in it:
            if not ent.name.endswith(".txt"):
                continue
            if "__" not in ent.name:
                continue
            did = ent.name.split("__", 1)[0]
            if did in needed and did not in found:
                found[did] = Path(ent.path)
    return found


def _trunc_detail(rows: list[dict], key: str, rule: str, gold200: set[str]) -> dict:
    if rule == "openai":
        hit = [r for r in rows if r[key]["tokens"] > MAX_TOK]
        ge = [r for r in rows if r[key]["tokens"] >= MAX_TOK]
    elif rule == "titan":
        hit = [r for r in rows if r[key]["chars"] > TITAN_CHARS]
        ge = hit
    else:
        raise ValueError(rule)
    gold_anchor_ids = sorted(r["doc_id"] for r in hit if r["is_gold_anchor"])
    gold200_ids = sorted(r["doc_id"] for r in hit if r["doc_id"] in gold200)
    ge_anchor = sorted(r["doc_id"] for r in ge if r["is_gold_anchor"])
    ge_gold200 = sorted(r["doc_id"] for r in ge if r["doc_id"] in gold200)
    out = {
        "n_truncated": len(hit),
        "n_truncated_is_gold_anchor": len(gold_anchor_ids),
        "truncated_gold_anchor_doc_ids": gold_anchor_ids,
        "n_truncated_in_primary200_gold": len(gold200_ids),
        "truncated_primary200_gold_doc_ids": gold200_ids,
    }
    if rule == "openai":
        out["n_ge_8191_tokens"] = len(ge)
        out["n_ge_8191_is_gold_anchor"] = len(ge_anchor)
        out["ge_8191_gold_anchor_doc_ids"] = ge_anchor
        out["n_ge_8191_in_primary200_gold"] = len(ge_gold200)
        out["ge_8191_primary200_gold_doc_ids"] = ge_gold200
        out["ge_8191_doc_ids"] = sorted(r["doc_id"] for r in ge)
    return out


def _fmt_block(name: str, b: dict) -> list[str]:
    lines = [
        f"### {name} (n={b['count']})",
        f"- median chars: {b['median']}",
        f"- p90 chars: {b['p90']}",
        f"- max chars: {b['max']}",
    ]
    n = b["count"]
    for t in CHAR_THRESHOLDS:
        d = b[f"gt_{t}_chars"]
        if n:
            lines.append(f"- > {t} chars: {d['count']}/{n} ({d['fraction']:.4f})")
        else:
            lines.append(f"- > {t} chars: n/a")
    d = b["gt_8191_tokens"]
    dge = b["ge_8191_tokens"]
    if n:
        lines.append(f"- > 8191 tokens: {d['count']}/{n} ({d['fraction']:.4f})")
        lines.append(f"- >= 8191 tokens: {dge['count']}/{n} ({dge['fraction']:.4f})")
    else:
        lines.append("- > 8191 tokens: n/a")
        lines.append("- >= 8191 tokens: n/a")
    return lines


def _fmt_trunc(label: str, t: dict) -> list[str]:
    lines = [
        f"- {label}: OpenAI truncated (tokens > 8191) {t['openai_8191_tokens']['n_truncated']} "
        f"(gold_anchor {t['openai_8191_tokens']['n_truncated_is_gold_anchor']}, "
        f"primary200_gold {t['openai_8191_tokens']['n_truncated_in_primary200_gold']}); "
        f"Titan truncated (chars > 24000) {t['titan_24000_chars']['n_truncated']} "
        f"(gold_anchor {t['titan_24000_chars']['n_truncated_is_gold_anchor']}, "
        f"primary200_gold {t['titan_24000_chars']['n_truncated_in_primary200_gold']})."
    ]
    o = t["openai_8191_tokens"]
    if "n_ge_8191_tokens" in o:
        lines.append(
            f"  - {label} tokens >= 8191: {o['n_ge_8191_tokens']} "
            f"(gold_anchor {o['n_ge_8191_is_gold_anchor']}, "
            f"primary200_gold {o['n_ge_8191_in_primary200_gold']})."
        )
        if o["truncated_gold_anchor_doc_ids"] or o["ge_8191_gold_anchor_doc_ids"]:
            lines.append(
                f"  - OpenAI gold-anchor doc ids (tokens > 8191): "
                f"{o['truncated_gold_anchor_doc_ids'] or '[]'}"
            )
            lines.append(
                f"  - OpenAI gold-anchor doc ids (tokens >= 8191): "
                f"{o['ge_8191_gold_anchor_doc_ids'] or '[]'}"
            )
        ti = t["titan_24000_chars"]
        if ti["truncated_gold_anchor_doc_ids"]:
            lines.append(
                f"  - Titan gold-anchor doc ids (chars > 24000): "
                f"{ti['truncated_gold_anchor_doc_ids']}"
            )
        lines.append(
            f"  - n_truncated_in_primary200_gold OpenAI: {o['n_truncated_in_primary200_gold']} "
            f"{o['truncated_primary200_gold_doc_ids']}; "
            f"Titan: {ti['n_truncated_in_primary200_gold']} "
            f"{ti['truncated_primary200_gold_doc_ids']}"
        )
    return lines


def aggregate() -> dict:
    rows: list[dict] = []
    with CUTS_JSONL.open(encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    by_id = {r["doc_id"]: r for r in rows}

    pool_meta: dict[str, dict] = {}
    n_title_prefix_all = 0
    n_title_prefix_ladder = 0
    n_pool = 0
    n_ladder_export = 0
    with POOL_JSONL.open(encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            rec = json.loads(line)
            n_pool += 1
            title_s = rec.get("title") or ""
            chunk_s = rec.get("chunk_text") or ""
            starts = rec.get("chunk_starts_with_title")
            if starts is None:
                starts = bool(title_s) and chunk_s.startswith(title_s)
            meta = {
                "scale_rank": rec.get("scale_rank"),
                "has_embedding": bool(rec.get("has_embedding", True)),
                "source_type": rec.get("source_type"),
                "is_gold_anchor": bool(rec.get("is_gold_anchor")),
                "chunk_starts_with_title": bool(starts),
                "title": title_s,
            }
            if rec.get("has_embedding") is None and rec.get("scale_rank") is None:
                meta["has_embedding"] = False
            pool_meta[rec["doc_id"]] = meta
            if starts:
                n_title_prefix_all += 1
            if _in_ladder(meta):
                n_ladder_export += 1
                if starts:
                    n_title_prefix_ladder += 1

    for r in rows:
        meta = pool_meta.get(r["doc_id"])
        if meta is None:
            r["_ladder"] = False
            continue
        if r.get("scale_rank") is None:
            r["scale_rank"] = meta["scale_rank"]
        if r.get("source_type") is None:
            r["source_type"] = meta["source_type"]
        r["is_gold_anchor"] = bool(r.get("is_gold_anchor") or meta["is_gold_anchor"])
        r["_ladder"] = _in_ladder(meta)

    ladder_rows = [r for r in rows if r.get("_ladder")]
    beyond_n = len(rows) - len(ladder_rows)

    gold_ids = primary200_gold_ids()
    gold_set = set(gold_ids)
    gold_rows = [by_id[g] for g in gold_ids if g in by_id and by_id[g].get("_ladder")]
    gold_rows_all = [by_id[g] for g in gold_ids if g in by_id]
    gold_missing = [g for g in gold_ids if g not in by_id]

    def by_source(subset: list[dict]) -> dict:
        grouped: dict[str, list[dict]] = defaultdict(list)
        for r in subset:
            grouped[str(r.get("source_type") or "unknown")].append(r)
        return {
            src: {
                "title_plus_chunk": _block(rs, "title_plus_chunk"),
                "chunk_text_only": _block(rs, "chunk_text_only"),
            }
            for src, rs in sorted(grouped.items())
        }

    def trunc_block(subset: list[dict]) -> dict:
        return {
            "title_plus_chunk": {
                "openai_8191_tokens": _trunc_detail(subset, "title_plus_chunk", "openai", gold_set),
                "titan_24000_chars": _trunc_detail(subset, "title_plus_chunk", "titan", gold_set),
            },
            "chunk_text_only": {
                "openai_8191_tokens": _trunc_detail(subset, "chunk_text_only", "openai", gold_set),
                "titan_24000_chars": _trunc_detail(subset, "chunk_text_only", "titan", gold_set),
            },
        }

    # Capped = chunk_text tokens >= 8191 (ingest token cap).
    capped_ids = sorted(
        r["doc_id"] for r in ladder_rows if r["chunk_text_only"]["tokens"] >= MAX_TOK
    )
    needed_raw = set(capped_ids) | gold_set
    raw_paths = _index_raw_paths(needed_raw)
    raw_measures: dict[str, dict] = {}
    missing_raw = sorted(did for did in needed_raw if did not in raw_paths)
    for did, path in sorted(raw_paths.items()):
        title = (pool_meta.get(did) or {}).get("title") or ""
        raw_text = path.read_text(encoding="utf-8", errors="replace").replace("\x00", "")
        body = _ingest_read_body(path, title)
        stored_chunk = by_id[did]["chunk_text_only"]["chars"] if did in by_id else None
        stored_title_chunk = by_id[did]["title_plus_chunk"]["chars"] if did in by_id else None
        rec_out = {
            "doc_id": did,
            "raw_path_name": path.name,
            "is_capped_chunk_text_ge_8191_tokens": did in set(capped_ids),
            "is_primary200_gold": did in gold_set,
            "raw_file_chars": len(raw_text),
            "raw_body_chars": len(body),
            "stored_chunk_text_chars": stored_chunk,
            "stored_title_plus_chunk_chars": stored_title_chunk,
        }
        if did in set(capped_ids) and stored_chunk is not None:
            rec_out["chars_cut_from_raw_body"] = max(0, len(body) - stored_chunk)
            rec_out["chars_cut_from_raw_file"] = max(0, len(raw_text) - stored_chunk)
        raw_measures[did] = rec_out

    spot = json.loads(SPOT_JSON.read_text(encoding="utf-8")) if SPOT_JSON.exists() else {}
    encoder_name = spot.get("encoder") or "unknown"

    paper_openai = 11
    paper_titan = 90
    paper_titan_gold = 5

    man = json.loads(MANIFEST.read_text(encoding="utf-8"))
    man_src: dict[str, int] = defaultdict(int)
    for d in man["documents"]:
        man_src[str(d["source_type"])] += 1

    stats = {
        "text_definitions": {
            "title_plus_chunk": "coalesce(title,'') + ' ' + coalesce(chunk_text,'') (BM25 / task W6)",
            "chunk_text_only": "chunk_text as stored in document_chunks (ingest _read_body; title is a prefix of chunk_text for nearly all rows)",
            "tokenizer": "cl100k_base encode(text, disallowed_special=())",
            "tokenizer_implementation": encoder_name,
            "tokenizer_note": "Official tiktoken (Docker image vector-drift-research-vector-drift-api). data/rev1_doc_token_cuts.jsonl was produced with official tiktoken and is not regenerated on the host. There is no pure-Python tokenizer fallback.",
            "cut_char_8191": "len(decode(tokens[:8191])) when that string is a prefix of text; else longest prefix with <=8191 tokens",
            "openai_truncate_rule": "tokens > 8191",
            "openai_ingest_cap": "document_chunks.chunk_text was already truncated to 8,191 tokens at ingestion (scripts/erb/ingest_erb.py lines ~108-110: truncate_for_embedding(_read_body(...)); apps/api/app/services/embedding.py MAX_INPUT_TOKENS=8191). Documents at the cap therefore have chunk_text tokens == 8191, not > 8191. title + ' ' + chunk_text can exceed 8191 tokens because the title is prepended again.",
            "title_duplication": "title + ' ' + chunk_text duplicates the title when chunk_text already starts with title (ingest _read_body).",
            "titan_truncate_rule": f"chars > {TITAN_CHARS}",
            "db_token_count_column": "present on document_chunks.token_count in this database; length stats here use tiktoken cuts, not that column",
            "pool_table": "document_chunks",
            "ladder_definition": "embedding IS NOT NULL AND scale_rank IS NOT NULL AND scale_rank < 100000",
            "n_ladder_pool": len(ladder_rows),
            "n_all_rows": len(rows),
            "n_beyond_ladder": beyond_n,
            "n_pool_export": n_pool,
            "n_ladder_export": n_ladder_export,
            "headline_population": "ladder_pool",
        },
        "title_prefix": {
            "ladder_pool": {
                "n": len(ladder_rows),
                "chunk_text_starts_with_title": n_title_prefix_ladder,
                "fraction": (n_title_prefix_ladder / len(ladder_rows) if ladder_rows else None),
            },
            "all_rows": {
                "n": n_pool,
                "chunk_text_starts_with_title": n_title_prefix_all,
                "fraction": (n_title_prefix_all / n_pool if n_pool else None),
            },
        },
        "primary200_unique_gold_docs": {
            "n": len(gold_ids),
            "n_in_document_chunks": len(gold_rows_all),
            "n_in_ladder_pool": len(gold_rows),
            "missing_from_db": gold_missing,
        },
        "ladder_pool": {
            "n": len(ladder_rows),
            "title_plus_chunk": _block(ladder_rows, "title_plus_chunk"),
            "chunk_text_only": _block(ladder_rows, "chunk_text_only"),
        },
        "all_rows": {
            "n": len(rows),
            "n_beyond_ladder": beyond_n,
            "label": f"includes {beyond_n} rows beyond the ladder (scale_rank >= 100000; all still have embeddings)",
            "title_plus_chunk": _block(rows, "title_plus_chunk"),
            "chunk_text_only": _block(rows, "chunk_text_only"),
        },
        "primary200_gold": {
            "title_plus_chunk": _block(gold_rows, "title_plus_chunk"),
            "chunk_text_only": _block(gold_rows, "chunk_text_only"),
        },
        "by_source_type": {
            "ladder_pool": by_source(ladder_rows),
            "all_rows": by_source(rows),
        },
        "truncation": {
            "ladder_pool": trunc_block(ladder_rows),
            "all_rows": trunc_block(rows),
            "paper": {
                "openai_truncated": paper_openai,
                "titan_truncated": paper_titan,
                "titan_truncated_gold_anchors": paper_titan_gold,
            },
        },
        "raw_pretruncation_chars": {
            "note": "Character lengths of raw EnterpriseRAG-Bench files for documents at the ingest token cap (chunk_text tokens >= 8191) plus all primary-200 gold documents. No tiktoken. ingest _read_body is applied for raw_body_chars. chars_cut_* reported only for capped documents.",
            "raw_dir": str(RAW_DOCS),
            "n_capped_chunk_text_ge_8191_tokens": len(capped_ids),
            "capped_doc_ids": capped_ids,
            "n_primary200_gold": len(gold_ids),
            "n_raw_files_read": len(raw_measures),
            "missing_raw_files": missing_raw,
            "documents": raw_measures,
        },
        "spot_check": spot,
        "manager_quick_count_chars_only": {
            "note": "Manager counted raw files over the whole manifest, not title + chunk_text and not the ingested ladder pool.",
            "gold_gt_4000": "183/272",
            "gold_gt_8191": "66/272",
            "pool_gt_4000": "71%",
            "pool_gt_8191": "16%",
            "why_16pct_raw_manifest_vs_20pct_db_pool": (
                "Different populations. The manager's 16% is the fraction of raw files "
                "with more than 8,191 characters across the whole manifest "
                f"(n={len(man['documents'])} document records; Slack {man_src.get('slack')} "
                f"and Gmail {man_src.get('gmail')}, which are mostly short). "
                "The database ladder pool (n=99998) caps Slack and Gmail at about "
                "14,000-17,000 rows each "
                "(Slack/Gmail in this pool: see by_source_type.ladder_pool), "
                "so longer sources (Fireflies, Confluence, Drive) are over-represented "
                "and the share of documents with > 8,191 characters is about 20%."
            ),
            "manifest_source_counts": dict(sorted(man_src.items())),
        },
    }

    md: list[str] = []
    md.append("# Document length and token statistics (revision W6)")
    md.append("")
    md.append("## Keys / README")
    md.append("")
    md.append("This markdown is the human-readable copy of `doc_length_stats.json`.")
    md.append("Headline numbers use the **ladder pool** (`n = 99998`): `embedding IS NOT NULL AND scale_rank IS NOT NULL AND scale_rank < 100000`.")
    md.append("The **all-rows** block is secondary (`n = 103033`), including 3,035 rows with `scale_rank >= 100000`.")
    md.append("`doc_token_cuts_openai.json` is a `doc_id` map of `title + ' ' + chunk_text` `{chars, tokens, cut_char_8191}` from official tiktoken; see `doc_token_cuts_openai.md`.")
    md.append("")
    md.append("### text_definitions")
    for k, v in stats["text_definitions"].items():
        md.append(f"- `{k}`: {v}")
    md.append("")
    md.append(f"Tokenizer: cl100k_base (`{encoder_name}`). OpenAI cut: 8,191 tokens. Titan cap: 24,000 characters.")
    md.append("")
    md.append("Ingest (`scripts/erb/ingest_erb.py` ~108-110) stored `truncate_for_embedding(_read_body(...))`, so `chunk_text` is already capped at 8,191 tokens. Eleven documents sit at exactly that cap (`tokens == 8191` on chunk_text). `title + ' ' + chunk_text` duplicates the title when `chunk_text` starts with `title`.")
    md.append("")
    md.append("## Title prefix (`chunk_text` starts with `title`)")
    tp = stats["title_prefix"]
    md.append(
        f"- ladder pool: {tp['ladder_pool']['chunk_text_starts_with_title']}/{tp['ladder_pool']['n']} "
        f"({tp['ladder_pool']['fraction']})"
    )
    md.append(
        f"- all rows: {tp['all_rows']['chunk_text_starts_with_title']}/{tp['all_rows']['n']} "
        f"({tp['all_rows']['fraction']})"
    )
    md.append("")
    md.append("## Ladder pool (`document_chunks`, n=99998)")
    md.extend(_fmt_block("title + space + chunk_text", stats["ladder_pool"]["title_plus_chunk"]))
    md.extend(_fmt_block("chunk_text only", stats["ladder_pool"]["chunk_text_only"]))
    md.append("")
    md.append(f"## All rows (`document_chunks`, n={len(rows)}; includes {beyond_n} rows beyond the ladder)")
    md.append(stats["all_rows"]["label"] + ".")
    md.extend(_fmt_block("title + space + chunk_text", stats["all_rows"]["title_plus_chunk"]))
    md.extend(_fmt_block("chunk_text only", stats["all_rows"]["chunk_text_only"]))
    md.append("")
    md.append("## Unique gold documents of primary-200 bank")
    md.append(
        f"Union of `expected_doc_ids` over 200 eval ids: **{len(gold_ids)}** "
        f"(in DB: {len(gold_rows_all)}; in ladder pool: {len(gold_rows)}; missing: {gold_missing})."
    )
    md.extend(_fmt_block("title + space + chunk_text", stats["primary200_gold"]["title_plus_chunk"]))
    md.extend(_fmt_block("chunk_text only", stats["primary200_gold"]["chunk_text_only"]))
    md.append("")
    md.append("## By source_type, ladder pool, both text definitions")
    for src, blk in stats["by_source_type"]["ladder_pool"].items():
        md.append(f"#### {src}")
        md.extend(_fmt_block(f"{src} title + space + chunk_text", blk["title_plus_chunk"]))
        md.extend(_fmt_block(f"{src} chunk_text only", blk["chunk_text_only"]))
    md.append("")
    md.append("## By source_type, all rows, both text definitions")
    for src, blk in stats["by_source_type"]["all_rows"].items():
        md.append(f"#### {src}")
        md.extend(_fmt_block(f"{src} title + space + chunk_text", blk["title_plus_chunk"]))
        md.extend(_fmt_block(f"{src} chunk_text only", blk["chunk_text_only"]))
    md.append("")
    md.append("## Truncation vs paper (ladder pool is headline)")
    md.append(
        "- Paper: OpenAI 11 at 8,191 tokens; Titan 90 at 24,000 chars (5 gold anchors)."
    )
    md.append("### ladder_pool")
    md.extend(_fmt_trunc("title + space + chunk_text", stats["truncation"]["ladder_pool"]["title_plus_chunk"]))
    md.extend(_fmt_trunc("chunk_text only", stats["truncation"]["ladder_pool"]["chunk_text_only"]))
    md.append("### all_rows")
    md.extend(_fmt_trunc("title + space + chunk_text", stats["truncation"]["all_rows"]["title_plus_chunk"]))
    md.extend(_fmt_trunc("chunk_text only", stats["truncation"]["all_rows"]["chunk_text_only"]))
    md.append("")
    md.append("## Raw-file pre-truncation character lengths")
    rp = stats["raw_pretruncation_chars"]
    md.append(rp["note"])
    md.append(f"- raw_dir: `{rp['raw_dir']}`")
    md.append(f"- n_capped_chunk_text_ge_8191_tokens: {rp['n_capped_chunk_text_ge_8191_tokens']}")
    md.append(f"- capped_doc_ids: {rp['capped_doc_ids']}")
    md.append(f"- n_primary200_gold: {rp['n_primary200_gold']}")
    md.append(f"- n_raw_files_read: {rp['n_raw_files_read']}")
    md.append(f"- missing_raw_files: {rp['missing_raw_files']}")
    md.append("")
    for did in sorted(rp["documents"]):
        rec = rp["documents"][did]
        extra = ""
        if rec.get("chars_cut_from_raw_body") is not None:
            extra = (
                f", chars_cut_from_raw_body={rec['chars_cut_from_raw_body']}, "
                f"chars_cut_from_raw_file={rec['chars_cut_from_raw_file']}"
            )
        md.append(
            f"- `{did}` file=`{rec['raw_path_name']}` capped={rec['is_capped_chunk_text_ge_8191_tokens']} "
            f"gold200={rec['is_primary200_gold']} raw_file_chars={rec['raw_file_chars']} "
            f"raw_body_chars={rec['raw_body_chars']} stored_chunk_text_chars={rec['stored_chunk_text_chars']} "
            f"stored_title_plus_chunk_chars={rec['stored_title_plus_chunk_chars']}{extra}"
        )
    md.append("")
    md.append("## Manager 16% vs database ~20%")
    mq = stats["manager_quick_count_chars_only"]
    md.append(mq["note"])
    md.append(f"- gold_gt_4000: {mq['gold_gt_4000']}")
    md.append(f"- gold_gt_8191: {mq['gold_gt_8191']}")
    md.append(f"- pool_gt_4000 (manager raw): {mq['pool_gt_4000']}")
    md.append(f"- pool_gt_8191 (manager raw): {mq['pool_gt_8191']}")
    md.append(f"- why: {mq['why_16pct_raw_manifest_vs_20pct_db_pool']}")
    md.append(f"- manifest_source_counts: {json.dumps(mq['manifest_source_counts'])}")
    md.append("")
    md.append("## Spot check (title + space + chunk_text, seed 42)")
    md.append(json.dumps(spot, indent=2))
    md.append("")
    md.append("## JSON mirror")
    md.append("Numeric source of truth is `doc_length_stats.json`, generated from the same dict as this markdown.")
    md.append("")

    OUT.mkdir(parents=True, exist_ok=True)
    cuts_map = {
        r["doc_id"]: {
            "chars": r["title_plus_chunk"]["chars"],
            "tokens": r["title_plus_chunk"]["tokens"],
            "cut_char_8191": r["title_plus_chunk"]["cut_char_8191"],
            "in_ladder_pool": bool(r.get("_ladder")),
        }
        for r in rows
    }
    (OUT / "doc_token_cuts_openai.json").write_text(
        json.dumps(cuts_map, ensure_ascii=False),
        encoding="utf-8",
    )
    cuts_md = [
        "# OpenAI 8,191-token character cuts (`doc_token_cuts_openai.json`)",
        "",
        "## Keys",
        "",
        "Top-level object: one entry per `doc_id` in `data/rev1_doc_token_cuts.jsonl` (official tiktoken).",
        "",
        "Each value:",
        "",
        "- `chars`: character length of `title + ' ' + chunk_text`",
        "- `tokens`: cl100k_base token count of that string (`encode(..., disallowed_special=())`)",
        "- `cut_char_8191`: character offset of the first 8,191 tokens, or the full length if the string is shorter",
        "- `in_ladder_pool`: true when the document is in the headline ladder pool (`embedding IS NOT NULL AND scale_rank IS NOT NULL AND scale_rank < 100000`)",
        "",
        "Headline length / truncation tables are in `doc_length_stats.json` and `doc_length_stats.md` (ladder pool n=99998).",
        "Do not treat this cut map as the length-stats table.",
        "",
    ]
    (OUT / "doc_token_cuts_openai.md").write_text("\n".join(cuts_md), encoding="utf-8")
    (OUT / "doc_length_stats.json").write_text(
        json.dumps(stats, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    (OUT / "doc_length_stats.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"wrote {OUT / 'doc_token_cuts_openai.json'} n={len(cuts_map)}", flush=True)
    print(f"wrote {OUT / 'doc_token_cuts_openai.md'}", flush=True)
    print(f"wrote {OUT / 'doc_length_stats.json'}", flush=True)
    print(f"wrote {OUT / 'doc_length_stats.md'}", flush=True)
    t = stats["truncation"]["ladder_pool"]
    print(
        "ladder n="
        f"{len(ladder_rows)} openai_title+chunk_gt8191="
        f"{t['title_plus_chunk']['openai_8191_tokens']['n_truncated']} "
        f"gold_anchor={t['title_plus_chunk']['openai_8191_tokens']['n_truncated_is_gold_anchor']} "
        f"chunk_ge8191={t['chunk_text_only']['openai_8191_tokens']['n_ge_8191_tokens']} "
        f"titan_chunk={t['chunk_text_only']['titan_24000_chars']['n_truncated']} "
        f"titan_gold={t['chunk_text_only']['titan_24000_chars']['n_truncated_is_gold_anchor']}",
        flush=True,
    )
    return stats


def main() -> int:
    args = sys.argv[1:]
    steps = args or ["export", "tokenize", "aggregate"]
    if "export" in steps:
        export_pool()
    if "tokenize" in steps:
        run_tiktoken_container()
    if "aggregate" in steps:
        aggregate()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
