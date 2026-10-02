# Replicate the Vector Drift Study

This guide is written for reviewers and independent labs who want to reproduce
the IEEE paper results on a local machine with **minimal friction**.

**Recommended path:** restore the published Postgres dump (embeddings already computed) → validate → optionally re-sweep.

**Artifact homepage:** https://pedapudibhargav.github.io/vector-drift-study/

**Repository:** https://github.com/pedapudibhargav/vector-drift-study

---

## 0. What you get

| Artifact | Where | Purpose |
|----------|--------|---------|
| Code + Docker stack | this repo | API, pgvector, sweep scripts |
| Published metrics | `artifacts/published/` | Paper tables / fits (no DB needed) |
| Embedding DB dumps | GitHub **Releases** (`erb_tables.dump.gz`, `erb_titan_tables.dump.gz`) | Skip re-embedding ~100k docs (OpenAI and Titan arms) |
| Questions | `data/enterprise_rag_bench/questions.jsonl` | ERB question bank |
| Primary-200 list | `artifacts/published/primary_questions_200.json` | Stratified eval set (seed 42) |
| L3/L4 audit outputs | `artifacts/published/llm_audit_report_openai.json`, `l4_hit_fairness_llm.*`, `L4_SPOTCHECK_HUMAN.md` | Secondary LLM audits + author spot-check |

Frozen study constants: seed **42**, primary embedder **`text-embedding-3-small`** (secondary: Titan Text Embeddings V2), HNSW **m=16 / ef_construction=64 / ef_search=200**, eval **k=10**, ladder **5k…100k**, τ**=0.10**. See [STUDY_PROTOCOL.md](STUDY_PROTOCOL.md).

---

## 1. Machine requirements

- Docker Desktop 4.x+ (macOS/Windows) or Docker Engine + Compose v2 (Linux)
- ~8 GB free disk for the dump + Postgres volume (~4 GB after restore)
- 8 GB RAM recommended
- Optional: Python 3.12+ on the host for `validate_study.py` / fit scripts
- Optional: `OPENAI_API_KEY` only if you re-embed, re-query without cache, or run L3 judge

You do **not** need NVIDIA GPUs or any cloud credentials to restore and validate the published results.

---

## 2. Clone and configure

```bash
git clone https://github.com/pedapudibhargav/vector-drift-study.git
cd vector-drift-study
cp .env.example .env
# Edit .env only if you need OPENAI_API_KEY or non-default ports.
```

Default DB credentials (must match compose):

```text
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=vector_drift_db
```

Public registries are the defaults. Leave `DOCKER_*`, `NPM_REGISTRY`, and `PYPI_*` blank unless you maintain a local (gitignored) mirror override in `.env`.

---

## 3. Start services

```bash
docker compose up -d --build vector-drift-postgres vector-drift-api
# Optional UI:
docker compose up -d --build vector-drift-web
```

Health checks:

```bash
curl -s http://localhost:8000/api/health
# → {"status":"...","vector_db":"connected:<rows>_chunks","postgres":"connected",...}
#   "openai":"error" is expected when OPENAI_API_KEY is blank; it is not needed for restore/validate.
```

- API docs: http://localhost:8000/api/docs  
- UI (if started): http://localhost:5173  
- Adminer (optional): http://localhost:8081  

---

## 4. Restore the published database (preferred)

### 4.1 Download the dump

1. Open the latest [GitHub Release](https://github.com/pedapudibhargav/vector-drift-study/releases).
2. Download `erb_tables.dump.gz` (compressed pg_dump custom format of the OpenAI embedding + metric tables) and, for the secondary embedder, `erb_titan_tables.dump.gz` (Titan V2 embeddings, runs and per-query results).
3. Place them under `data/backups/`.
4. Optional: gunzip `erb_query_embed_cache.json.gz` and `erb_titan_query_embed_cache.json.gz` into `data/` so sweeps reuse the published query embeddings (no embedding API calls).

If Releases are unavailable, any local path from `scripts/erb/backup_erb_db.sh` works the same way.

### 4.2 Restore

```bash
./scripts/erb/restore_from_backup.sh data/backups/erb_tables.dump.gz
./scripts/erb/restore_from_backup.sh data/backups/erb_titan_tables.dump.gz   # optional Titan arm
```

The script:

1. Waits for Postgres healthy  
2. Ensures schema (`init_vector_db.py` / migrate)  
3. `pg_restore --clean --if-exists` into `vector_drift_db`  
4. Prints row counts for `document_chunks` with `scale_rank < 100000`

Expected: ≈ **100k** rows with `scale_rank < 100000` (minor shortfall possible from manifest duplicate `doc_id`s).

### 4.3 Validate

```bash
python3 scripts/erb/validate_study.py
# or inside the API container:
docker exec vector-drift-api python /app/scripts/erb/validate_study.py
```

---

## 5. Re-run the scale sweep (optional but recommended)

With embeddings restored, re-running the sweep should match published Hit@k within sampling noise.

```bash
docker exec \
  -e DATABASE_URL=postgresql+asyncpg://postgres:postgres@vector-drift-postgres:5432/vector_drift_db \
  vector-drift-api \
  python /app/scripts/erb/run_scale_sweep.py \
    --primary-questions \
    --scales 5000 10000 15000 20000 25000 40000 50000 75000 100000 \
    --top-k 10
```

Fit the log-linear trend (descriptive, not a universal law):

```bash
python3 scripts/erb/fit_scaling_law.py data/results/erb_scale_sweep_*.json
```

Compare to the published fit:

```bash
diff -u artifacts/published/erb_full_primary200_to100k_fit.json \
        data/results/*_fit.json | head
```

Published headline numbers (primary-200, **integrity-clean** re-sweep):

| N | Hit@1 raw | Hit@10 raw | Hit@10 meta | Δ_meta |
|---|-----------|------------|-------------|--------|
| 5k | 0.600 | 0.795 | 0.875 | +0.080 |
| 20k | 0.410 | 0.600 | 0.775 | +0.175 |
| 100k | 0.305 | 0.510 | 0.640 | +0.130 |

\(N^\star(\tau{=}0.10)\): **not observed** (lift stays ≥0.10 for \(N\geq10\)k). Fits: Hit@10 ≈ `1.474 − 0.086 log N`.  
Source: `artifacts/published/CANONICAL_METRICS.json` + `erb_full_primary200_to100k*.json`.

---

## 6. Smoke path (no dump, tiny corpus)

Useful to verify Docker wiring without downloading ~1 GB:

```bash
# Requires OPENAI_API_KEY in .env
python3 scripts/erb/download_erb.py --sources confluence jira linear github --max-slices 1 --extract
python3 scripts/erb/build_scale_manifest.py
docker exec -e DATABASE_URL=postgresql://postgres:postgres@vector-drift-postgres:5432/vector_drift_db \
  vector-drift-api python /app/scripts/erb/migrate_erb_schema.py
docker exec -e DATABASE_URL=postgresql://postgres:postgres@vector-drift-postgres:5432/vector_drift_db \
  vector-drift-api python /app/scripts/erb/ingest_erb.py --limit 1000 --batch-size 40
docker exec -e DATABASE_URL=postgresql+asyncpg://postgres:postgres@vector-drift-postgres:5432/vector_drift_db \
  vector-drift-api python /app/scripts/erb/run_scale_sweep.py --smoke --question-limit 20 --scales 500 1000
```

Or: `./scripts/erb/run_study.sh smoke`

---

## 7. From-scratch full embed (expensive)

Only if you must regenerate vectors:

1. Download / extract ERB documents (`scripts/erb/download_erb.py --extract`).  
2. `build_scale_manifest.py` (seed 42, gold anchors first).  
3. `ingest_erb.py` until `COUNT(DISTINCT scale_rank) WHERE scale_rank < 100000` ≈ 100000.  
4. `run_scale_sweep.py` on the ladder above.  
5. `fit_scaling_law.py`.

Expect hours of wall time and non-trivial OpenAI embedding cost. Prefer the Release dump.

---

## 8. BM25 baseline & LLM judges

Okapi BM25 (RQ2) runs on the host over the ERB document text, so it needs the ERB documents
(`python3 scripts/erb/download_erb.py --extract`) and the scale manifest:

```bash
python3 scripts/erb/run_bm25_baseline.py            # full ladder, k=10, title+body truncated to 4k chars
```

Published: `artifacts/published/erb_bm25_baseline_primary200.json` (Hit@10 0.855→0.700) and
`bm25_vs_dense_bootstrap.json`. The Postgres FTS negative control is `erb_lexical_baseline_primary200.json`
(Hit@10 ≈ 0.045 on a partial ladder); it is not a BM25 substitute.

Optional LLM judge (needs `OPENAI_API_KEY`):

```bash
docker exec -e DATABASE_URL=postgresql+asyncpg://postgres:postgres@vector-drift-postgres:5432/vector_drift_db \
  vector-drift-api python /app/scripts/erb/run_l3_judge.py
```

---

## 9. Packaging your own backup

```bash
./scripts/erb/backup_erb_db.sh
./scripts/erb/package_release_artifacts.sh data/backups/<timestamp_dir>
# Upload the printed .gz to a GitHub Release
```

---

## 10. Troubleshooting

| Symptom | Fix |
|---------|-----|
| `pg_restore: connection refused` | Wait for `docker compose ps` healthy; re-run restore |
| Empty `document_chunks` | Confirm dump path; check `restore_from_backup.sh` logs |
| Compose build fails pulling packages | Ensure `.env` has blank `PYPI_INDEX_URL` / `NPM_REGISTRY` (public registries) |
| API TLS errors behind a local intercepting proxy | Install the proxy CA locally; do not commit PEMs |
| Hit@k far from paper | Confirm `--primary-questions`, ladder points only, seed 42 manifest |

---

## 11. What “reproduced” means for reviewers

Minimum bar:

1. Restore dump → `validate_study.py` passes  
2. `python3 scripts/erb/verify_paper_numbers.py` and `python3 scripts/erb/verify_paper_tables.py` pass (published JSON ↔ every table in the paper)  
3. Optional: re-sweep one scale (e.g. 5k + 100k) and compare Hit@10  

The L4 LLM-assisted audit and the author spot-check are already published ([HUMAN_AUDIT.md](HUMAN_AUDIT.md)); they are secondary and not needed to reproduce the metrics.
