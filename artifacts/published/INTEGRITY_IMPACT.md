# Integrity findings — transparent impact assessment

**Date:** 2026-09-20 (final pre–human-review)  
**Canonical metrics:** `artifacts/published/CANONICAL_METRICS.json`

---

## Root causes (fixed)

| Finding | Cause | Fix |
|---------|-------|-----|
| 200 rows / 183 unique IDs | `extra_questions.jsonl` reuses raw IDs | `eval_id = question_id::question_type` |
| Opposite Hit@10 on same retrieval | Different gold under same ID | Unique eval_id + membership Hit@k |
| Empty `retrieved_doc_ids` | HNSW + WHERE dropped all candidates | `hnsw.iterative_scan` + ef_search + exact fallback |

## Clean ladder (publish)

- Sweep: `erb_full_primary200_to100k.json` ← `erb_scale_sweep_20260920T203818Z.json`
- Integrity: **OK** (unique IDs, 0 empties, 0 Hit≠membership)
- Hit@10 raw **0.795→0.510**; meta **0.875→0.640**; Δ stays ≥0.10 for \(N\geq10\)k → **no \(N^\star\)** on ladder
- Fit: \(a\approx1.474\), \(b\approx0.086\)
- PDF: `papers/ieee-vector-drift/access/main.pdf` rebuilt to match TeX

## Human review (done — spot-check)

Author labeled 10/10 spot-check rows: **9 agree** LLM fairness, **1 unsure** (`label_noise`).  
Exact MVP: Hit@10 exact 0.795→0.585; HNSW gap +0.075 at 100k.  
Artifacts: `L4_SPOTCHECK_HUMAN.md`, `exact_control_mvp.md`.

## Do not cite

`*.POLLUTED.json`, legacy Pages numbers before this sync, `preview.html` (superseded).
