# Human audit worksheet (L4)

Fill the CSVs under `artifacts/published/human_audit_*.csv`.
Step-by-step: [`docs/HUMAN_AUDIT.md`](../../docs/HUMAN_AUDIT.md).

## Files

| File | Scale | Condition |
|------|-------|-----------|
| `human_audit_n5000_raw.csv` | 5k | dense raw |
| `human_audit_n20000_raw.csv` | 20k | dense raw |

Each file: **20 hits + 20 misses** (seed 42). Target: **≥40 labeled rows** before camera-ready.

## Columns to complete

| Column | Values | Meaning |
|--------|--------|---------|
| `auditor` | initials | Who labeled |
| `label_correct` | `y` / `n` / `unsure` | Is the system Hit@10 judgment correct vs gold docs? |
| `failure_mode` | taxonomy below | Required when miss or `label_correct=n` |
| `notes` | free text | One line |

## Failure-mode taxonomy

1. `embedding_near_miss` — semantically close distractor ranked above gold
2. `lexical_mismatch` — query terms absent from gold doc surface form
3. `multi_gold_partial` — only subset of expected docs retrieved
4. `metadata_needed` — type/filter would rescue (compare meta condition)
5. `label_noise` — ERB expected_doc_ids look wrong
6. `other`

## Acceptance for paper §Human validation

- [ ] ≥40 rows labeled
- [ ] Cohen’s κ or % agreement if 2 auditors on overlapping 20
- [ ] Table: failure_mode counts at N=5k vs N=20k
