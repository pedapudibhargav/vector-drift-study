# Result verification UI & GitHub Pages (A+B+C)

**Chosen:** A+B+C. Embeddings stay off Pages.

---

## 1. What is stored where

| Layer | Location | What peer reviewers get |
|-------|----------|-------------------------|
| **A** Metrics | `artifacts/published/` + Pages | Hit@1/5/10 aggregates + per-query flags/ids |
| **B** Verify bundle | `artifacts/verification/` → `docs/data/verification/` | Paginated UI with **question text + chunk text** + scores |
| **C** Full dumps | **GitHub Releases** ([v1.0.0-artifacts](https://github.com/pedapudibhargav/vector-drift-study/releases/tag/v1.0.0-artifacts): OpenAI + Titan dumps, query caches) | Restore Postgres+pgvector incl. **embeddings** for local re-runs |

**DB (author machine / restored dump):** `vector_drift_results`, `retrieval_hit_details`, `document_chunks` (OpenAI text + vectors); `document_chunks_titan`, `vector_drift_results_titan` (Titan arm).

---

## 2. Static verify UI

- Page: `docs/verify/index.html` → `/verify/` on Pages  
- Build: `python3 scripts/erb/export_verification_bundle.py`  
- Live after deploy: https://pedapudibhargav.github.io/vector-drift-study/verify/

Without a DB, reviewers can still validate **every published query row**: Hit@1/5/10, MRR, ranks/scores, retrieved ids, and truncated chunk text for gold∪retrieved docs (~5325/5334 resolved).

---

## 3. Where the DB dumps go

**GitHub Releases**, not the `gh-pages` branch and not git history.

```bash
./scripts/erb/package_release_artifacts.sh data/backups/<dir>
gh release create v1.0.0-artifacts data/backups/release/erb_tables.dump.gz \
  data/backups/release/erb_titan_tables.dump.gz \
  data/backups/release/erb_query_embed_cache.json.gz \
  data/backups/release/erb_titan_query_embed_cache.json.gz \
  --title "DB snapshot (embeddings + metrics)" \
  --notes "Restore with ./scripts/erb/restore_from_backup.sh"
```

See `data/backups/README.md`.

---

## 4. Deploy pipeline

`.github/workflows/deploy-gh-pages.yml` on every push to **`main`**:

1. Assemble `docs/` (incl. verification data) into `_site/`
2. Strip accidental local-only docs from the published site
3. Force-push orphan commit to **`gh-pages`**

**One-time:** Repo → Settings → Pages → Deploy from a branch → **`gh-pages` / (root)**.

---

## 5. Docker Results UI (optional later)

Static Pages cover reviewer verification. A live `/results` React page against Postgres remains optional for author-side Adminer-quality browsing.
