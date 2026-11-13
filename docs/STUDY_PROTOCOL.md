> **Archived v1 document.** It describes the first release (v1.0.0-artifacts), whose HNSW-based numbers are superseded. The current results and procedures are in `artifacts/published/revision1/` and `docs/REPRODUCE_REVISION1.md`.

# EnterpriseRAG-Bench Vector Drift Study Protocol

**Manuscript:** IEEE Access submission — [`papers/ieee-vector-drift/access/main.tex`](../papers/ieee-vector-drift/access/main.tex)
**Public artifacts:** https://pedapudibhargav.github.io/vector-drift-study/
**GitHub:** https://github.com/pedapudibhargav/vector-drift-study
**Replication:** [REPLICATE.md](REPLICATE.md) · **Threats:** [THREATS_TO_VALIDITY.md](THREATS_TO_VALIDITY.md)
**Results verify UI + Pages export:** [VERIFICATION_UI_AND_STATIC_HOSTING.md](VERIFICATION_UI_AND_STATIC_HOSTING.md)

## Frozen protocol

| Item | Value |
|------|-------|
| Indexing unit | 1 vector / document (`dsid_*`; title + body) |
| Corpus ladder | **5k → 10k → 15k → 20k → 25k → 40k → 50k → 75k → 100k** (9 points) |
| Eval `top_k` | 10 |
| Primary embedder | OpenAI `text-embedding-3-small` (1536-d) |
| Secondary embedder | Amazon Titan Text Embeddings V2 `amazon.titan-embed-text-v2:0` (1024-d, unit-normalized) |
| ANN index | pgvector HNSW, m=16, ef_construction=64, ef_search=200, iterative scan; exact-cosine fallback when a filter under-fills top-k |
| Seed | 42 (question sampling and distractor stratification) |
| Eval identity | `question_id::question_type` (200 unique eval IDs) |
| Metadata threshold | τ = 0.10 (operational, not pre-registered) |

## Headline results (primary-200, exact search; revision 1)

| Result | Value | Source |
|--------|-------|--------|
| OpenAI raw Hit@10 / Hit@1 / MRR, 5k → 100k (exact) | 0.795→0.585 / 0.600→0.340 / 0.658→0.408 | `revision1/exact_ladder_openai_primary200.json` |
| Hit@10 drop, OpenAI (paired 95% interval) | 0.210 [0.155, 0.270] | `revision1/analysis_exact.json` |
| Titan raw Hit@10 / Hit@1, 5k → 100k (exact) | 0.785→0.610 / 0.620→0.385 | `revision1/exact_ladder_titan_primary200.json` |
| Difference in drop, OpenAI − Titan (90% interval) | +0.035 [−0.020, +0.090]: equivalent within ±0.10, not within ±0.05 | `revision1/analysis_equivalence.json` |
| Okapi BM25 (text the dense model saw) Hit@10, 5k → 100k | 0.810→0.685 | `revision1/bm25_dense_text.json` |
| Δ_meta (oracle filter vs. exact baseline) | OpenAI +0.075 to +0.100; Titan +0.070 to +0.115; no detectable trend; N★ not used | `revision1/analysis_exact.json` |
| Reciprocal rank fusion (k=60) Hit@10, 5k → 100k | 0.905→0.720 | `revision1/rrf_hybrid_openai_primary200.json` |
| Log-linear fit, OpenAI raw Hit@10 | 1.369 − 0.068 ln N | `revision1/analysis_exact.json` |

The first-version HNSW numbers (Hit@10 0.795→0.510; +0.130 lift at 100k) mixed exact and approximate search and are superseded (manuscript Sec. V-F). Equivalence margins (0.05 primary, 0.10 sensitivity) are operational choices of the authors, not externally registered.

All numbers are checked against the manuscript by `scripts/erb/verify_paper_numbers.py` and `scripts/erb/verify_paper_tables.py` (which delegate to `scripts/erb/revision1/validate_all.py`).

## Question sets

| Set | Size | Use |
|-----|------|-----|
| **Primary** | **200**, stratified by `question_type`, seed 42 | All tables and figures |

Exclude `high_level` / `info_not_found`; require non-empty `expected_doc_ids`.

## Scale construction

1. Gold anchors = union of eval `expected_doc_ids` → ranks `0 .. A-1`
2. Distractors stratified by `source_type`, seed 42
3. Corpus at N: `scale_rank < N` (one physical index per embedder; no per-N rebuild)

## Validation layers

| Layer | Role | Artifact |
|-------|------|----------|
| L1 labeled IR | Primary claims (Hit@k, DocRecall@10, MRR) | `erb_full_primary200_to100k.json` |
| L2 integrity gates | Unique eval IDs, Hit@k = gold ∈ top-k, no empty retrievals | `scripts/erb/validate_study.py`, `integrity_hit10_recompute.json` |
| L3 LLM relevance audit | Secondary triage (`gpt-4o`, 180 stratified cells) | `llm_audit_report_openai.json` |
| L4 LLM-assisted fairness audit | `gpt-4o` on 62 high-priority rows (62/62 fair) + author spot-check of 10 rows (9 agree, 1 unsure) | `l4_hit_fairness_llm.json`, `L4_SPOTCHECK_HUMAN.md` |

L3/L4 are secondary corroboration only; no paper claim depends on them.

## Do not cite

`*.POLLUTED.json` (pre-integrity exploratory aggregates, retained for transparency only).
