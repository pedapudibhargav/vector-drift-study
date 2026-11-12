# Search mode diagnosis (port 5433)

Generated: 2026-11-10T19:15:44Z
## Timing (OpenAI raw)

| pass | scale | ef | sweep_s | mean_ms_ratio_vs_audit | frac_identical | Hit@10 approx |
|---|---|---|---|---|---|---|
| first_pass_after_reference_scans | 5000 | 200 | 4.873 | 0.8761 | 1.0 | 0.795 |
| first_pass_after_reference_scans | 50000 | 200 | 20.887 | 0.9121 | 1.0 | 0.64 |
| first_pass_after_reference_scans | 100000 | 200 | 11.762 | 18.9702 | 0.795 | 0.54 |
| first_pass_after_reference_scans | 5000 | 400 | 4.883 | 0.8374 | 1.0 | 0.795 |
| first_pass_after_reference_scans | 50000 | 400 | 20.152 | 0.8965 | 1.0 | 0.64 |
| first_pass_after_reference_scans | 100000 | 400 | 38.053 | 0.8968 | 1.0 | 0.585 |
| first_pass_after_reference_scans | 5000 | 800 | 4.943 | 0.9026 | 1.0 | 0.795 |
| first_pass_after_reference_scans | 50000 | 800 | 4.469 | 2.5902 | 0.9 | 0.61 |
| first_pass_after_reference_scans | 100000 | 800 | 2.325 | 1.1947 | 0.905 | 0.555 |
| warm | 5000 | 200 | 4.941 | 0.901 | 1.0 | 0.795 |
| warm | 50000 | 200 | 20.351 | 0.8893 | 1.0 | 0.64 |
| warm | 100000 | 200 | 1.256 | 1.7095 | 0.795 | 0.54 |
| warm | 5000 | 400 | 4.756 | 0.8237 | 1.0 | 0.795 |
| warm | 50000 | 400 | 20.568 | 0.9141 | 1.0 | 0.64 |
| warm | 100000 | 400 | 38.049 | 0.8972 | 1.0 | 0.585 |
| warm | 5000 | 800 | 4.943 | 0.8888 | 1.0 | 0.795 |
| warm | 50000 | 800 | 2.334 | 1.2074 | 0.9 | 0.61 |
| warm | 100000 | 800 | 2.316 | 1.1582 | 0.905 | 0.555 |

## E2 ef sweep @ 100k raw (OpenAI)

| ef | sweep_s | recall@10 | frac_identical | Hit@10 approx | Hit@10 exact | plan_hnsw |
|---|---|---|---|---|---|---|
| 100 | 0.855 | 0.908 | 0.61 | 0.49 | 0.585 | True |
| 200 | 1.061 | 0.96 | 0.795 | 0.54 | 0.585 | True |
| 300 | 40.066 | 1.0 | 1.0 | 0.585 | 0.585 | False |
| 400 | 36.845 | 1.0 | 1.0 | 0.585 | 0.585 | False |
| 500 | 38.291 | 1.0 | 1.0 | 0.585 | 0.585 | False |
| 600 | 37.712 | 1.0 | 1.0 | 0.585 | 0.585 | False |
| 800 | 2.816 | 0.985 | 0.905 | 0.555 | 0.585 | True |

## OpenAI raw HNSW recall @ ef 200 (by scale)

| scale | plan_hnsw | recall@10 | frac_identical | sweep_s |
|---|---|---|---|---|
| 10000 | False | 1.0 | 1.0 | 9.52 |
| 15000 | False | 1.0 | 1.0 | 13.597 |
| 20000 | False | 1.0 | 1.0 | 18.001 |
| 25000 | False | 1.0 | 1.0 | 21.978 |
| 40000 | False | 1.0 | 1.0 | 17.073 |
| 50000 | False | 1.0 | 1.0 | 20.508 |
| 75000 | True | 0.9555 | 0.78 | 1.07 |
| 100000 | True | 0.96 | 0.795 | 1.08 |

## E2 GUC variants @ 100k raw

| ef | max_scan_tuples | scan_mem_mult | sweep_s | frac_identical |
|---|---|---|---|---|
| 400 | 20000 | 1 | 37.628 | 1.0 |
| 400 | 20000 | 4 | 38.605 | 1.0 |
| 400 | 100000 | 1 | 38.4 | 1.0 |
| 400 | 100000 | 4 | 38.289 | 1.0 |
| 400 | 1000000 | 1 | 40.261 | 1.0 |
| 400 | 1000000 | 4 | 39.121 | 1.0 |
| 800 | 20000 | 1 | 2.561 | 0.905 |
| 800 | 20000 | 4 | 2.263 | 0.905 |
| 800 | 100000 | 1 | 2.641 | 0.905 |
| 800 | 100000 | 4 | 2.298 | 0.905 |
| 800 | 1000000 | 1 | 2.317 | 0.905 |
| 800 | 1000000 | 4 | 2.266 | 0.905 |

## E3 iterative_scan (OpenAI)

| scale | cond | mode | frac_non_increasing | recall@10 | frac_identical | sweep_s |
|---|---|---|---|---|---|---|
| 5000 | raw | off | 1.0 | 1.0 | 1.0 | 4.842 |
| 5000 | raw | strict_order | 1.0 | 1.0 | 1.0 | 4.876 |
| 5000 | raw | relaxed_order | 1.0 | 1.0 | 1.0 | 4.934 |
| 5000 | meta | off | 1.0 | 1.0 | 1.0 | 1.346 |
| 5000 | meta | strict_order | 1.0 | 1.0 | 1.0 | 1.254 |
| 5000 | meta | relaxed_order | 1.0 | 1.0 | 1.0 | 1.273 |
| 25000 | raw | off | 1.0 | 1.0 | 1.0 | 22.206 |
| 25000 | raw | strict_order | 1.0 | 1.0 | 1.0 | 22.318 |
| 25000 | raw | relaxed_order | 1.0 | 1.0 | 1.0 | 23.053 |
| 25000 | meta | off | 1.0 | 1.0 | 1.0 | 3.943 |
| 25000 | meta | strict_order | 1.0 | 1.0 | 1.0 | 3.839 |
| 25000 | meta | relaxed_order | 1.0 | 1.0 | 1.0 | 3.874 |
| 100000 | raw | off | 1.0 | 0.96 | 0.795 | 1.516 |
| 100000 | raw | strict_order | 1.0 | 0.96 | 0.795 | 1.121 |
| 100000 | raw | relaxed_order | 1.0 | 0.96 | 0.795 | 1.108 |
| 100000 | meta | off | 1.0 | 1.0 | 1.0 | 11.66 |
| 100000 | meta | strict_order | 1.0 | 1.0 | 1.0 | 11.374 |
| 100000 | meta | relaxed_order | 1.0 | 1.0 | 1.0 | 11.343 |

## E4 cross-scale meta swaps (relaxed_order)

| scale_lo | scale_hi | n_swap_q | frac |
|---|---|---|---|
| 25000 | 40000 | 0 | 0.0 |
| 40000 | 50000 | 0 | 0.0 |
| 50000 | 75000 | 0 | 0.0 |
| 75000 | 100000 | 0 | 0.0 |

## E4 cross-scale meta swaps (strict_order)

| scale_lo | scale_hi | n_swap_q | frac |
|---|---|---|---|
| 25000 | 40000 | 0 | 0.0 |
| 40000 | 50000 | 0 | 0.0 |
| 50000 | 75000 | 0 | 0.0 |
| 75000 | 100000 | 0 | 0.0 |

## Planner cost matrix @ 100k raw (median over 200 queries)

| ef | cost_default | cost_forced_hnsw | forced recall@10 | forced Hit@10 | scan_node |
|---|---|---|---|---|---|
| 100 | 5539.04 | 5539.04 | 0.908 | 0.49 | Index Scan |
| 200 | 9624.22 | 9624.22 | 0.96 | 0.54 | Index Scan |
| 300 | 10110.06 | 13440.02 | 0.9725 | 0.54 | Index Scan |
| 400 | 10110.06 | 17098.86 | 0.976 | 0.54 | Index Scan |
| 500 | 10110.06 | 20648.91 | 0.9785 | 0.54 | Index Scan |
| 600 | 10110.06 | 24116.66 | 0.9825 | 0.55 | Index Scan |
| 800 | 7461.41 | 7461.41 | 0.985 | 0.555 | Index Scan |

## Titan E2 @ 100k raw

| ef | sweep_s | frac_identical | plan_hnsw |
|---|---|---|---|
| 200 | 1.084 | 0.88 | True |
| 400 | 31.308 | 1.0 | False |
| 800 | 2.381 | 0.98 | True |

## Titan E3 @ 100k raw

| mode | frac_non_increasing | frac_identical | sweep_s |
|---|---|---|---|
| relaxed_order | 1.0 | 0.88 | 1.027 |
| strict_order | 1.0 | 0.88 | 1.068 |

## OpenAI meta mixed plans (ef 200)

| scale | n_hnsw | n_exact | mean_recall_hnsw | mean_recall_exact | frac_hnsw_identical |
|---|---|---|---|---|---|
| 40000 | 0 | 200 | None | 1.0 | 0.0 |
| 50000 | 0 | 200 | None | 1.0 | 0.0 |
| 75000 | 0 | 200 | None | 1.0 | 0.0 |
| 100000 | 0 | 200 | None | 1.0 | 0.0 |

## Tie handling (exact top-11)

- lists checked: 3600
- rank 10/11 score ties (≤1e-12): 0
- duplicate scores in top 10: 0
- note: Ties at rank 10/11 can change which doc occupies rank 10 under doc_id tie-break; Hit@10 uses set membership of top-10 ids, not rank-11.

## Observations

- `port`: 5433
- `timing_first_pass_mean_ms_ratio_5k_over_50k_ef200`: 0.216
- `ef400_800_frac_identical_exact_100k_raw`: {'ef400': 1.0, 'ef800': 0.905}
- `e3_openai_relaxed_frac_non_increasing_min`: 1.0
- `e4_relaxed_total_pair_swaps`: 0
- `e4_strict_total_pair_swaps`: 0
- `titan_e3_frac_scores_non_increasing`: {'relaxed_order': 1.0, 'strict_order': 1.0}
- `tie_handling`: {'n_lists_checked': 3600, 'n_rank10_11_score_ties': 0, 'rank10_11_tie_samples': [], 'n_lists_duplicate_scores_in_top10': 0, 'hit_at_10_impact_note': 'Ties at rank 10/11 can change which doc occupies rank 10 under doc_id tie-break; Hit@10 uses set membership of top-10 ids, not rank-11.'}

## Acceptance

- `exact_self_recall`: **PASS** — {"n_lists_compared": 3600, "n_identical": 3600, "frac_identical": 1.0, "status": "PASS", "sample_mismatches": []}
- `latency_5k_vs_50k_ef200_raw`: {'port': 5433, 'timing_pass': 'first_pass_after_reference_scans', 'sweep_s_5k': 4.873, 'sweep_s_50k': 20.887, 'sum_ms_5k': 4452.662, 'sum_ms_50k': 20580.967, 'mean_ms_ratio_5k_over_50k': 0.216, 'sum_ms_ratio_5k_over_50k': 0.216, 'audit_mean_ms_ratio_5k_over_50k': 0.225, 'reproduces_3x_band': False, 'note': 'Pass runs after exact-reference scans; not a cold-cache measurement.'}
- `ef400_800_identical_to_exact_100k_raw`: {'ef400_frac_identical': 1.0, 'ef800_frac_identical': 0.905, 'ef400_status': 'PASS', 'ef800_status': 'FAIL'}

HNSW recall table: `<repo>/artifacts/published/revision1/hnsw_recall_by_cell_5433.json`

