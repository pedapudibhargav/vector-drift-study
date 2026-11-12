# Reproducing the revision-1 results

Everything below runs against a local PostgreSQL 16 + pgvector 0.8.x container restored from the release dumps. Exact-search results do not depend on the HNSW indexes; the approximate-search studies do.

## 0. Environment
- `docker compose up -d vector-drift-postgres` (the compose file sets `shm_size: 1gb`; with Docker's default 64 MB `pg_restore` silently skips the HNSW index builds).
- `scripts/erb/restore_from_backup.sh` for the OpenAI and the Titan dump (it now fails if no HNSW index exists after the restore).
- Python with `numpy`, `psycopg2`, `rank_bm25`, `tiktoken` (cl100k_base; set `TIKTOKEN_CACHE_DIR` if the vocabulary cannot be downloaded).
- Database connection through `PGHOST PGPORT PGUSER PGPASSWORD PGDATABASE`. Query vectors come from `data/erb_query_embed_cache_rev1.json` (OpenAI) and `data/erb_titan_query_embed_cache.json`; no API call is needed. Every runner refuses to start unless the vector fingerprints in `artifacts/published/revision1/query_vector_provenance_openai.json` match.

## 1. Primary measurement: exact search
```
python scripts/erb/revision1/run_exact_ladder.py --embedder openai --bank primary200
python scripts/erb/revision1/run_exact_ladder.py --embedder titan  --bank primary200
python scripts/erb/revision1/run_exact_ladder.py --embedder openai --bank primary400
python scripts/erb/revision1/run_exact_ladder.py --verify --out artifacts/published/revision1/exact_ladder_openai_primary200.json
python scripts/erb/revision1/analyze_exact.py
python scripts/erb/revision1/equivalence_analysis.py
python scripts/erb/revision1/titan_truncation_sensitivity.py
```
## 2. Text length, BM25, fusion, routing
```
python scripts/erb/revision1/doc_token_stats_tiktoken.py
for v in chars4000 chars8191 tokens8191 untruncated dense_text raw_untruncated dense_text_chars4000; do
  python scripts/erb/revision1/run_bm25_variants.py --variant $v; done
python scripts/erb/revision1/rrf_hybrid.py
python scripts/erb/revision1/routing_simulation.py
```
## 3. Search-mode audit and approximate search
```
python scripts/erb/revision1/explain_audit.py --port 5433
python scripts/erb/revision1/search_mode_diagnosis.py --port 5433
python scripts/erb/revision1/search_mode_diagnosis.py --port 5433 --only-recall-by-cell
python scripts/erb/revision1/build_per_n_indexes.py --embedder openai
python scripts/erb/revision1/build_per_n_indexes.py --embedder titan
python scripts/erb/revision1/eval_per_n_hnsw.py --embedder both --repeats 3
```
The audit and diagnosis were run on two databases: a fresh restore (port 5433) and a frozen byte copy of the original database (port 5434).
## 4. Distractor schedules
```
python scripts/erb/revision1/run_exact_ladder_uniform.py --build-ranks
for l in uniform_s42 uniform_s0 rr_s0; do for e in openai titan; do
  python scripts/erb/revision1/run_exact_ladder_uniform.py --ladder $l --embedder $e --bank primary200 --conditions raw,meta_first,meta_in; done; done
python scripts/erb/revision1/analyze_uniform.py
```
## 5. Tables, figures, validation
```
python scripts/erb/revision1/make_paper_tables.py
SKIP_CHROME_RENDER=0 python scripts/erb/revision1/make_paper_figures_rev1.py   # needs Google Chrome for PDF output
python scripts/erb/revision1/write_artifact_manifest.py
python scripts/erb/revision1/test_harness_mutations.py
python scripts/erb/revision1/validate_all.py --tex papers/ieee-vector-drift/access/main.tex
```
`validate_all.py` must report PASS for SCHEMA, INVARIANTS, SEARCH_MODE_TRUTH, QUERY_VECTOR_PROVENANCE, ARTIFACT_PROVENANCE, CROSS_IMPLEMENTATION, DATA_HYGIENE and CLAIM_REGISTRY. Latency numbers depend on the host and are indicative only; recall and Hit@10 are deterministic for exact search and for a fixed index build.
