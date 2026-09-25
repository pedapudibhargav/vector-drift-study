# Vector Drift Study

Empirical scaling laws for dense retrieval Hit@$k$ as an EnterpriseRAG-Bench corpus grows from 5k → 100k documents (gold-anchor pinning, frozen HNSW).

| Link | URL |
|------|-----|
| **Artifact / verify site** | https://pedapudibhargav.github.io/vector-drift-study/ |
| **Per-query Hit@k browser (no DB)** | https://pedapudibhargav.github.io/vector-drift-study/verify/ |
| **Source repo** | https://github.com/pedapudibhargav/vector-drift-study |
| **Full DB dump (embeddings)** | [GitHub Releases](https://github.com/pedapudibhargav/vector-drift-study/releases): `erb_tables.dump.gz` (OpenAI arm) + `erb_titan_tables.dump.gz` (Titan V2 arm) + cached query embeddings |
| **Study protocol** | [docs/STUDY_PROTOCOL.md](docs/STUDY_PROTOCOL.md) |
| **Replication** | [docs/REPLICATE.md](docs/REPLICATE.md) |
| **IEEE Access draft** | [papers/ieee-vector-drift/access/](papers/ieee-vector-drift/access/) |

## What you can do on GitHub Pages (no Postgres)

Open **[Verify results](https://pedapudibhargav.github.io/vector-drift-study/verify/)**:

- Paginated table of all **primary-200 × scale × condition** rows (Hit@1 / @5 / @10, MRR, scores)
- Click a row → question text, gold chunks, ranked retrieved chunks + ids
- Data is static Option **A+B** (`docs/data/verification/`). **Embeddings are not on Pages.**

## What requires the Release dump (Option C)

Restoring `erb_tables.dump.gz` gives you the full pgvector DB (embeddings + metrics) so you can re-run sweeps / ANN locally without re-paying for OpenAI document embedding. Restoring `erb_titan_tables.dump.gz` as well adds the Amazon Titan Text Embeddings V2 arm (`document_chunks_titan`, `experiment_runs_titan`, `vector_drift_results_titan`) with no Bedrock calls needed. Unzip `erb_query_embed_cache.json.gz` / `erb_titan_query_embed_cache.json.gz` into `data/` to re-run sweeps without any embedding API.

---

## Quick start for reviewers (easiest path)

### A) Browse published results only (~1 minute)

1. Open https://pedapudibhargav.github.io/vector-drift-study/verify/
2. Filter by scale / condition / Hit@10 and inspect chunk text

### B) Full local stack + restore embeddings (~30 minutes)

Prerequisites: Docker Desktop (or Engine + Compose v2), ~8 GB free disk, `git`, `python3`.

```bash
git clone https://github.com/pedapudibhargav/vector-drift-study.git
cd vector-drift-study
cp .env.example .env
# Leave NPM_REGISTRY / PYPI_* blank unless you use a private mirror locally.

docker compose up -d --build vector-drift-postgres vector-drift-api

# Download erb_tables.dump.gz from the latest GitHub Release into data/backups/
# https://github.com/pedapudibhargav/vector-drift-study/releases
./scripts/erb/restore_from_backup.sh data/backups/erb_tables.dump.gz
./scripts/erb/restore_from_backup.sh data/backups/erb_titan_tables.dump.gz   # optional: Titan V2 arm
python3 scripts/erb/validate_study.py
```

Optional UI: `docker compose up -d vector-drift-web` → http://localhost:5173  
Optional Adminer: `docker compose --profile tools up -d` → http://localhost:8081

### C) Tiny smoke (needs `OPENAI_API_KEY`, no dump)

```bash
cp .env.example .env   # set OPENAI_API_KEY
docker compose up -d --build
./scripts/erb/run_study.sh smoke
```

---

## Published numbers (primary-200, integrity-clean)

| N | Hit@1 raw | Hit@10 raw | Δ_meta Hit@10 |
|---|-----------|------------|---------------|
| 5k | 0.600 | 0.795 | +0.080 |
| 20k | 0.410 | 0.600 | +0.175 |
| 100k | 0.305 | 0.510 | +0.130 |

\(N^\star(\tau{=}0.10)\): **not observed** on this ladder (Δ stays ≥0.10 for \(N\geq10\)k).  
Fit: Hit@10 ≈ `1.474 − 0.086 log N`. Source: `artifacts/published/CANONICAL_METRICS.json`.

## Artifact layout (A+B+C)

| Layer | Location | Contents |
|-------|----------|----------|
| **A** Metrics | `artifacts/published/*.json` | Aggregates + per-query Hit@k / ids |
| **B** Verify bundle | `artifacts/verification/` (+ mirrored under `docs/data/verification/`) | `per_query.jsonl`, `chunks_by_id.json` (text only) |
| **C** Full dump | GitHub **Releases** (not git) | `erb_tables.dump.gz` ≈ 1.1 GB with embeddings |

Rebuild B after changing published metrics:

```bash
python3 scripts/erb/export_verification_bundle.py
```

## GitHub Pages deploy

On every push to `main`, [`.github/workflows/deploy-gh-pages.yml`](.github/workflows/deploy-gh-pages.yml) publishes `docs/` to the **`gh-pages`** branch.

**One-time repo setting:** Settings → Pages → Deploy from a branch → **`gh-pages` / root**.

## Environment variables

Defaults are **public** registries. Optional private mirrors belong only in local `.env` (gitignored) — see `.env.example`. Do not commit corporate mirror hostnames.

## Layout

| Path | Role |
|------|------|
| `apps/api` | FastAPI + pgvector |
| `apps/web` | Study UI (Docker) |
| `scripts/erb/` | Ingest, sweep, fit, backup/restore, verification export |
| `artifacts/published/` | Camera-ready metrics |
| `artifacts/verification/` | Static verify bundle (no embeddings) |
| `docs/` | GitHub Pages site |
| `papers/ieee-vector-drift/access/` | IEEE Access LaTeX |
