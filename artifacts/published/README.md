# Published artifacts

Result files behind the IEEE Access manuscript and the GitHub Pages site. The paper's section and table for each file are listed.

## Primary results (OpenAI `text-embedding-3-small`)

| File | Contents | Paper |
|------|----------|-------|
| `erb_full_primary200_to100k.json` | Integrity-clean primary-200 sweep, raw + meta, 9 scales, per-query rows | Tables 2, 3, 4, 9 |
| `erb_full_primary200_to100k_fit.json` | Log-linear fits, Δ_meta, N★, bootstrap 95% CIs (seed 42, B=1000) | Table 2 CIs, Eqs. 6–8, Table 10 |
| `CANONICAL_METRICS.json`, `paper_metrics_for_tex.json` | Headline numbers used by `verify_paper_numbers.py` | — |
| `primary_questions_200.json` | The 200 stratified eval IDs (`question_id::question_type`) | Sec. IV-A |
| `exact_control_mvp.{json,md}` | Exact cosine vs HNSW at 5k/50k/100k | Table 5 |
| `integrity_hit10_recompute.json` | Hit@10 recomputed from gold ∈ top-k | Appendix D |

## Controls and secondary embedder

| File | Contents | Paper |
|------|----------|-------|
| `erb_bm25_baseline_primary200.{json,md}`, `bm25_vs_dense_bootstrap.json` | Okapi BM25 full ladder + paired bootstrap vs dense | Sec. V-H, Table 6 |
| `erb_lexical_baseline_primary200.json` | Postgres FTS negative control (partial ladder) | Sec. V-H |
| `erb_titan_primary200_to100k.json` | Titan V2 sweep with per-query rows | Appendix E, Table 11 |
| `exact_control_titan.{json,md}` | Titan exact vs HNSW | Table 5 |
| `openai_vs_titan_primary200.{json,md}`, `openai_vs_titan_bootstrap.{json,md}` | Cross-embedder comparison, paired bootstrap (B=5000) | Sec. V-I, Tables 7–8 |
| `TITAN_A8_STATUS.md` | Titan arm parity and status notes | — |

## Secondary audits (L3/L4)

| File | Contents |
|------|----------|
| `llm_audit_report_openai.{json,md}` | L3 `gpt-4o` relevance audit on 180 stratified cells |
| `l3_judge_{raw,meta}_5000-40000_n40.json` | Legacy exploratory L3 judge (no weight in RQ answers) |
| `human_review_queue_openai.csv` | 62 high-priority rows for L4 |
| `l4_hit_fairness_llm.{json,csv,md}` | L4 `gpt-4o` Hit@10-fairness audit (62/62 fair) |
| `l4_spotcheck_queue.csv`, `l4_spotcheck_human_results.json`, `L4_SPOTCHECK_HUMAN.md` | Author spot-check (9/10 agree, 1 unsure) |
| `L4_LLM_TRANSPARENCY.md`, `INTEGRITY_IMPACT.md` | How L4 and the integrity fixes are framed |

## Provenance only — do not cite

`*.POLLUTED.json`, `*.CLEAN.json`, `erb_full_primary_corrected*.json`, `sweep_repair_*`, and `*.log` files record the integrity repair history (Sec. V-E).

**Database dumps** (too large for git): [GitHub Release v1.0.0-artifacts](https://github.com/pedapudibhargav/vector-drift-study/releases/tag/v1.0.0-artifacts). Restore with `./scripts/erb/restore_from_backup.sh`; see [docs/REPLICATE.md](../../docs/REPLICATE.md).
