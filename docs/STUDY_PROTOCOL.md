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

## Headline results (primary-200)

| Result | Value | Source |
|--------|-------|--------|
| OpenAI raw Hit@10 / Hit@1 / MRR, 5k → 100k | 0.795→0.510 / 0.600→0.305 / 0.658→0.365 | `erb_full_primary200_to100k.json` |
| Exact-cosine control, OpenAI Hit@10 | 0.795→0.585 (HNSW adds ≈0.08 loss at 50k–100k) | `exact_control_mvp.json` |
| Titan raw Hit@10 / Hit@1, 5k → 100k | 0.785→0.610 / 0.620→0.385 (HNSW = exact) | `erb_titan_primary200_to100k.json`, `exact_control_titan.json` |
| Exact-vs-exact cross-embedder drop difference (Hit@10) | +0.035, 95% CI [−0.025, 0.100] | `openai_vs_titan_bootstrap.json` |
| Okapi BM25 Hit@10, 5k → 100k | 0.855→0.700 | `erb_bm25_baseline_primary200.json` |
| Δ_meta (OpenAI) | +0.08 to +0.18; N★ undefined on the ladder | `erb_full_primary200_to100k_fit.json` |
| Δ_meta (Titan) | +0.070 to +0.115; N★ = 100k (borderline) | `openai_vs_titan_bootstrap.json` |
| Log-linear fit, OpenAI Hit@10 | 1.474 − 0.086 ln N | `erb_full_primary200_to100k_fit.json` |

All numbers are checked against the manuscript by `scripts/erb/verify_paper_numbers.py` and `scripts/erb/verify_paper_tables.py`.

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
