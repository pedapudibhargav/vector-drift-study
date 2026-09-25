# EnterpriseRAG-Bench Vector Drift Study Protocol

**Publication target:** IEEE Access (8–16 pp evidence band; Access template 2026-05).  
**Public artifacts:** https://pedapudibhargav.github.io/vector-drift-study/  
**GitHub:** https://github.com/pedapudibhargav/vector-drift-study  
**Replication:** [REPLICATE.md](REPLICATE.md)  
**Paper quality / PDF eXpress / CrossCheck notes:** [PAPER_QUALITY_VERIFICATION.md](PAPER_QUALITY_VERIFICATION.md)  
**Results verify UI + Pages export options:** [VERIFICATION_UI_AND_STATIC_HOSTING.md](VERIFICATION_UI_AND_STATIC_HOSTING.md)

## Status snapshot (final ladder)

| Item | Value |
|------|-------|
| Indexing unit | 1 vector / document (`dsid_*`) |
| Corpus ladder | **5k → 10k → 15k → 20k → 25k → 40k → 50k → 75k → 100k** (9 points) |
| Eval `top_k` | 10 |
| Embedder | Primary: `text-embedding-3-small` (1536-d), HNSW m=16 · A8: `amazon.titan-embed-text-v2:0` |
| Seed | 42 |
| OpenAI embed | ≈100k unique `scale_rank` &lt; 100000 (manifest dup shortfall OK) |
| Primary-200 raw Hit@10 | **0.795 → 0.510** (5k → 100k; integrity-clean) |
| Primary-200 raw Hit@1 | **0.600 → 0.305** (5k → 100k) |
| \(N^\star(\tau{=}0.10)\) | **undefined on this ladder** (Δ_meta stays ≥0.10 for \(N\geq10\)k; `n_star_last_ge=100k`) |
| Fit Hit@10 | \(a\approx1.474\), \(b\approx0.086\) (`erb_full_primary200_to100k_fit.json`) |
| Bootstrap CIs | in `artifacts/published/erb_full_primary200_to100k_fit.json` |
| Lexical FTS | Hit@10 ≈ 0.045 at 5k–25k (dense ≫ FTS) |
| Eval identity | `question_id::question_type` (200 unique; no base/extra collisions) |
| Human audit | **labeling pending** → [HUMAN_AUDIT.md](HUMAN_AUDIT.md); OpenAI L4 triage packaged |

## Question sets

| Set | Size | Use |
|-----|------|-----|
| **Primary** | **200**, stratified by `question_type`, seed 42 | Main tables / figures |
| **Full** | ~462 eligible | Appendix / sensitivity |

Exclude `high_level` / `info_not_found`; require non-empty `expected_doc_ids`.

## Camera-ready checklist

| # | Action | Status |
|---|--------|--------|
| A1 | Embed to ~100k | **Done** |
| A2 | Ladder sweep primary-200 (raw+meta) | **Done** → `artifacts/published/erb_full_primary200_to100k*.json` |
| A3 | Lexical baseline (partial ladder OK; extend optional) | **Partial** (5k–25k) |
| A4 | Bootstrap 95% CIs | **Done** |
| A5 | Fit \(a,b\) + \(N^\star\) | **Done** (\(a\approx1.474\), \(b\approx0.086\); **no \(N^\star\)** on ladder) |
| A6 | Human label ≥40 audit rows | **Pending (manual)** — [HUMAN_AUDIT.md](HUMAN_AUDIT.md) |
| A7 | Threats prose in paper | **Done** (see §Threats + [THREATS_TO_VALIDITY.md](THREATS_TO_VALIDITY.md)) |
| A8 | Second embedder (Amazon Titan Text Embeddings V2) | **Done** (2026-09-23) — raw Hit@1/10/MRR replicate; exact-control caveat in `TITAN_A8_STATUS.md` + Pages landing |
| A9 | Public artifact URL in paper | **Ready** (Pages + Releases) |

## Scale construction

1. Gold anchors = union of eval `expected_doc_ids` → ranks `0 .. A-1`  
2. Distractors stratified by `source_type`, seed 42  
3. Corpus at \(N\): `scale_rank < N`

## Validation layers

| Layer | Role |
|-------|------|
| L1 Label IR | Defines scaling law / \(N^\star\) |
| L2 Code asserts | `scripts/erb/validate_study.py` |
| L3 gpt-4o-mini | Safety appendix (`artifacts/published/l3_judge_*.json`) |
| L4 Human audit | Spot-check failure modes |

## Paper

[`papers/ieee-vector-drift/`](../papers/ieee-vector-drift/) — `main.tex` + `CHECKLIST.md`.
