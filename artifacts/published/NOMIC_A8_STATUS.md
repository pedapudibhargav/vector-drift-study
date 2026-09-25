# A8 Second Embedder — Nomic (`nomic-embed-text`) Status

Updated: 2026-09-22 (local Pacific) / ingest in progress.

## Model & isolation

| Item | Value |
|------|-------|
| Model | Ollama `nomic-embed-text` (768-d) — local, $0 |
| Note | User-facing name “Nomic Embed V2” maps to this local Ollama model in-repo (not Nomic Cloud API) |
| Table | `document_chunks_ollama` (separate from OpenAI `document_chunks` / 1536-d) |
| OpenAI arm | `text-embedding-3-small` — **complete** (~103k) |
| Protocol | Same gold-pinned ladder, primary-200 `stratified_unique` seed 42, HNSW m=16 / ef_construction=64 / ef_search=200, top_k=10 |

## Live progress

| Signal | Value |
|--------|-------|
| Checkpoint | `data/erb_ollama_ingest_checkpoint.json` |
| Ingest log | `/tmp/erb_ollama_ingest.log` |
| Watchdog | `./scripts/erb/watch_ollama_ingest_and_eval.sh` → `/tmp/erb_ollama_watch.log` |
| Target | 100000 docs |
| Rate (observed) | ~700–750 docs/min → ~2–2.5 h remaining from ~2k |
| Auto after ingest | `run_scale_sweep_ollama.py` + `compare_openai_vs_nomic.py` |

## Commands

```bash
# Monitor
tail -f /tmp/erb_ollama_ingest.log
tail -f /tmp/erb_ollama_watch.log
python3 -c "import json; print(json.load(open('data/erb_ollama_ingest_checkpoint.json'))['count'])"

# Manual resume
./scripts/erb/resume_ollama_ingest.sh

# Manual eval (after ≥100k)
docker exec -e DATABASE_URL=postgresql://vector_drift:vector_drift@vector-drift-postgres:5432/vector_drift \
  -e OLLAMA_HOST=http://host.docker.internal:11434 \
  vector-drift-api python /app/scripts/erb/run_scale_sweep_ollama.py --primary-questions 200
python3 scripts/erb/compare_openai_vs_nomic.py
```

## Sweep fixes applied (before eval)

`run_scale_sweep_ollama.py` now:
1. Uses `stratified_unique` (eval_id = `question_id::question_type`)
2. Meta filter = `source_types[0]` (parity with OpenAI `vector_drift_eval`)
3. Caches query embeddings in `data/erb_ollama_query_embed_cache.json`
4. Sets `hnsw.ef_search=200`

## Paper update

Deferred until ladder JSON exists — see `NOMIC_PAPER_PATCH_PLAN.md`.
