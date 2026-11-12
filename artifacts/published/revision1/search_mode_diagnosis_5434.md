# Search mode diagnosis (port 5434)

Generated: 2026-11-10T17:36:22Z
## Timing (OpenAI raw)

| pass | scale | ef | sweep_s | mean_ms_ratio_vs_audit | frac_identical | Hit@10 approx |
|---|---|---|---|---|---|---|
| first_pass_after_reference_scans | 5000 | 200 | 4.664 | 1.0998 | 1.0 | 0.795 |
| first_pass_after_reference_scans | 50000 | 200 | 1.568 | 0.6581 | 0.72 | 0.555 |
| first_pass_after_reference_scans | 100000 | 200 | 1.393 | 0.6764 | 0.785 | 0.51 |
| first_pass_after_reference_scans | 5000 | 400 | 4.636 | 1.1166 | 1.0 | 0.795 |
| first_pass_after_reference_scans | 50000 | 400 | 23.877 | 0.7969 | 1.0 | 0.64 |
| first_pass_after_reference_scans | 100000 | 400 | 43.506 | 0.8101 | 1.0 | 0.585 |
| first_pass_after_reference_scans | 5000 | 800 | 4.66 | 1.1107 | 1.0 | 0.795 |
| first_pass_after_reference_scans | 50000 | 800 | 23.958 | 0.8918 | 1.0 | 0.64 |
| first_pass_after_reference_scans | 100000 | 800 | 43.035 | 0.8654 | 1.0 | 0.585 |
| warm | 5000 | 200 | 4.749 | 1.1292 | 1.0 | 0.795 |
| warm | 50000 | 200 | 1.401 | 0.5617 | 0.72 | 0.555 |
| warm | 100000 | 200 | 1.407 | 0.6767 | 0.785 | 0.51 |
| warm | 5000 | 400 | 4.564 | 1.0988 | 1.0 | 0.795 |
| warm | 50000 | 400 | 24.08 | 0.8044 | 1.0 | 0.64 |
| warm | 100000 | 400 | 43.211 | 0.8042 | 1.0 | 0.585 |
| warm | 5000 | 800 | 4.681 | 1.1153 | 1.0 | 0.795 |
| warm | 50000 | 800 | 23.967 | 0.8921 | 1.0 | 0.64 |
| warm | 100000 | 800 | 45.795 | 0.922 | 1.0 | 0.585 |

## E2 ef sweep @ 100k raw (OpenAI)

| ef | sweep_s | recall@10 | frac_identical | Hit@10 approx | Hit@10 exact | plan_hnsw |
|---|---|---|---|---|---|---|
| 100 | 1.144 | 0.8935 | 0.615 | 0.495 | 0.585 | True |
| 200 | 1.321 | 0.946 | 0.785 | 0.51 | 0.585 | True |
| 300 | 1.915 | 0.967 | 0.86 | 0.53 | 0.585 | True |
| 400 | 45.016 | 1.0 | 1.0 | 0.585 | 0.585 | False |
| 500 | 47.228 | 1.0 | 1.0 | 0.585 | 0.585 | False |
| 600 | 47.466 | 1.0 | 1.0 | 0.585 | 0.585 | False |
| 800 | 47.929 | 1.0 | 1.0 | 0.585 | 0.585 | False |

## OpenAI raw HNSW recall @ ef 200 (by scale)

| scale | plan_hnsw | recall@10 | frac_identical | sweep_s |
|---|---|---|---|---|
| 10000 | True | 0.9105 | 0.56 | 1.716 |
| 15000 | True | 0.919 | 0.595 | 1.463 |
| 20000 | True | 0.9225 | 0.615 | 1.455 |
| 25000 | True | 0.926 | 0.635 | 1.43 |
| 40000 | True | 0.932 | 0.7 | 1.474 |
| 50000 | True | 0.932 | 0.72 | 1.563 |
| 75000 | True | 0.945 | 0.775 | 1.419 |
| 100000 | True | 0.946 | 0.785 | 1.485 |

## E2 GUC variants @ 100k raw

| ef | max_scan_tuples | scan_mem_mult | sweep_s | frac_identical |
|---|---|---|---|---|
| 400 | 20000 | 1 | 48.313 | 1.0 |
| 400 | 20000 | 4 | 48.738 | 1.0 |
| 400 | 100000 | 1 | 49.466 | 1.0 |
| 400 | 100000 | 4 | 49.478 | 1.0 |
| 400 | 1000000 | 1 | 47.562 | 1.0 |
| 400 | 1000000 | 4 | 47.044 | 1.0 |
| 800 | 20000 | 1 | 46.875 | 1.0 |
| 800 | 20000 | 4 | 46.498 | 1.0 |
| 800 | 100000 | 1 | 44.667 | 1.0 |
| 800 | 100000 | 4 | 46.904 | 1.0 |
| 800 | 1000000 | 1 | 47.126 | 1.0 |
| 800 | 1000000 | 4 | 46.886 | 1.0 |

## E3 iterative_scan (OpenAI)

| scale | cond | mode | frac_non_increasing | recall@10 | frac_identical | sweep_s |
|---|---|---|---|---|---|---|
| 5000 | raw | off | 1.0 | 1.0 | 1.0 | 5.712 |
| 5000 | raw | strict_order | 1.0 | 1.0 | 1.0 | 12.792 |
| 5000 | raw | relaxed_order | 1.0 | 1.0 | 1.0 | 5.639 |
| 5000 | meta | off | 1.0 | 1.0 | 1.0 | 1.293 |
| 5000 | meta | strict_order | 1.0 | 1.0 | 1.0 | 1.194 |
| 5000 | meta | relaxed_order | 1.0 | 1.0 | 1.0 | 1.481 |
| 25000 | raw | off | 1.0 | 0.926 | 0.635 | 1.659 |
| 25000 | raw | strict_order | 1.0 | 0.926 | 0.635 | 1.418 |
| 25000 | raw | relaxed_order | 1.0 | 0.926 | 0.635 | 1.679 |
| 25000 | meta | off | 1.0 | 1.0 | 1.0 | 25.415 |
| 25000 | meta | strict_order | 1.0 | 1.0 | 1.0 | 8.836 |
| 25000 | meta | relaxed_order | 1.0 | 1.0 | 1.0 | 4.682 |
| 100000 | raw | off | 1.0 | 0.946 | 0.785 | 2.119 |
| 100000 | raw | strict_order | 1.0 | 0.946 | 0.785 | 1.292 |
| 100000 | raw | relaxed_order | 1.0 | 0.946 | 0.785 | 1.683 |
| 100000 | meta | off | 1.0 | 0.8705 | 0.75 | 2.526 |
| 100000 | meta | strict_order | 1.0 | 0.9045 | 0.76 | 2.761 |
| 100000 | meta | relaxed_order | 0.935 | 0.9545 | 0.78 | 2.835 |

## E4 cross-scale meta swaps (relaxed_order)

| scale_lo | scale_hi | n_swap_q | frac |
|---|---|---|---|
| 25000 | 40000 | 5 | 0.025 |
| 40000 | 50000 | 3 | 0.015 |
| 50000 | 75000 | 1 | 0.005 |
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
| 100 | 5663.39 | 5663.39 | 0.8935 | 0.495 | Index Scan |
| 200 | 9838.16 | 9838.16 | 0.946 | 0.51 | Index Scan |
| 300 | 13737.64 | 13737.64 | 0.967 | 0.53 | Index Scan |
| 400 | 15785.01 | 17476.73 | 0.978 | 0.545 | Index Scan |
| 500 | 15785.01 | 21104.63 | 0.9845 | 0.55 | Index Scan |
| 600 | 15785.01 | 24648.43 | 0.986 | 0.555 | Index Scan |
| 800 | 15785.01 | 31546.28 | 0.9895 | 0.565 | Index Scan |

## Titan E2 @ 100k raw

| ef | sweep_s | frac_identical | plan_hnsw |
|---|---|---|---|
| 200 | 1.174 | 0.89 | True |
| 400 | 38.003 | 1.0 | False |
| 800 | 3.699 | 0.98 | True |

## Titan E3 @ 100k raw

| mode | frac_non_increasing | frac_identical | sweep_s |
|---|---|---|---|
| relaxed_order | 1.0 | 0.89 | 1.349 |
| strict_order | 1.0 | 0.89 | 1.345 |

## OpenAI meta mixed plans (ef 200)

| scale | n_hnsw | n_exact | mean_recall_hnsw | mean_recall_exact | frac_hnsw_identical |
|---|---|---|---|---|---|
| 40000 | 87 | 113 | 0.9494 | 1.0 | 0.6437 |
| 50000 | 101 | 99 | 0.9347 | 1.0 | 0.5545 |
| 75000 | 159 | 41 | 0.9472 | 1.0 | 0.7044 |
| 100000 | 159 | 41 | 0.9428 | 1.0 | 0.7233 |

## Tie handling (exact top-11)

- lists checked: 3600
- rank 10/11 score ties (≤1e-12): 0
- duplicate scores in top 10: 0
- note: Ties at rank 10/11 can change which doc occupies rank 10 under doc_id tie-break; Hit@10 uses set membership of top-10 ids, not rank-11.

## Observations

- `port`: 5434
- `timing_first_pass_mean_ms_ratio_5k_over_50k_ef200`: 3.516
- `ef400_800_frac_identical_exact_100k_raw`: {'ef400': 1.0, 'ef800': 1.0}
- `e3_openai_relaxed_frac_non_increasing_min`: 0.935
- `e4_relaxed_total_pair_swaps`: 9
- `e4_strict_total_pair_swaps`: 0
- `titan_e3_frac_scores_non_increasing`: {'relaxed_order': 1.0, 'strict_order': 1.0}
- `tie_handling`: {'n_lists_checked': 3600, 'n_rank10_11_score_ties': 0, 'rank10_11_tie_samples': [], 'n_lists_duplicate_scores_in_top10': 0, 'hit_at_10_impact_note': 'Ties at rank 10/11 can change which doc occupies rank 10 under doc_id tie-break; Hit@10 uses set membership of top-10 ids, not rank-11.'}

## Acceptance

- `exact_self_recall`: **PASS** — {"n_lists_compared": 3600, "n_identical": 3600, "frac_identical": 1.0, "status": "PASS", "sample_mismatches": []}
- `latency_5k_vs_50k_ef200_raw`: {'port': 5434, 'timing_pass': 'first_pass_after_reference_scans', 'sweep_s_5k': 4.664, 'sweep_s_50k': 1.568, 'sum_ms_5k': 4213.536, 'sum_ms_50k': 1198.551, 'mean_ms_ratio_5k_over_50k': 3.516, 'sum_ms_ratio_5k_over_50k': 3.516, 'audit_mean_ms_ratio_5k_over_50k': 2.103, 'reproduces_3x_band': True, 'note': 'Pass runs after exact-reference scans; not a cold-cache measurement.'}
- `ef400_800_identical_to_exact_100k_raw`: {'ef400_frac_identical': 1.0, 'ef800_frac_identical': 1.0, 'ef400_status': 'PASS', 'ef800_status': 'PASS'}

HNSW recall table: `<repo>/artifacts/published/revision1/hnsw_recall_by_cell_5434.json`

