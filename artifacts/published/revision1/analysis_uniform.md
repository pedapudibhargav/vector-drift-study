# Uniform ladder analysis

- Confluence-first questions: **41**
- Composition note: 627 pinned gold anchors are Confluence-heavy; small uniform corpora are Confluence-heavier than the full pool under any ladder ordering.

## Acceptance

| test | pass | detail |
|------|:----:|--------|
| invariants_zero_uniform_s0 | True | {'values': {'containment': 0, 'nested_corpus': 0, 'score_monotonicity': 0}} |
| invariants_zero_uniform_s0_titan | True | {'values': {'containment': 0, 'nested_corpus': 0, 'score_monotonicity': 0}} |
| invariants_zero_uniform_s42 | True | {'values': {'containment': 0, 'nested_corpus': 0, 'score_monotonicity': 0}} |
| invariants_zero_uniform_s42_titan | True | {'values': {'containment': 0, 'nested_corpus': 0, 'score_monotonicity': 0}} |
| invariants_zero_rr_s0 | True | {'values': {'containment': 0, 'nested_corpus': 0, 'score_monotonicity': 0}} |
| invariants_zero_rr_s0_titan | True | {'values': {'containment': 0, 'nested_corpus': 0, 'score_monotonicity': 0}} |
| 100k_endpoint_uniform_s0_openai_raw | True | {'got': 0.585, 'want': 0.585} |
| 100k_endpoint_uniform_s0_openai_meta_first | True | {'got': 0.67, 'want': 0.67} |
| 100k_endpoint_uniform_s0_titan_titan_raw | True | {'got': 0.61, 'want': 0.61} |
| 100k_endpoint_uniform_s0_titan_titan_meta_first | True | {'got': 0.69, 'want': 0.69} |
| 100k_endpoint_uniform_s42_openai_raw | True | {'got': 0.585, 'want': 0.585} |
| 100k_endpoint_uniform_s42_openai_meta_first | True | {'got': 0.67, 'want': 0.67} |
| 100k_endpoint_uniform_s42_titan_titan_raw | True | {'got': 0.61, 'want': 0.61} |
| 100k_endpoint_uniform_s42_titan_titan_meta_first | True | {'got': 0.69, 'want': 0.69} |
| 100k_endpoint_rr_s0_openai_raw | True | {'got': 0.585, 'want': 0.585} |
| 100k_endpoint_rr_s0_openai_meta_first | True | {'got': 0.67, 'want': 0.67} |
| 100k_endpoint_rr_s0_titan_titan_raw | True | {'got': 0.61, 'want': 0.61} |
| 100k_endpoint_rr_s0_titan_titan_meta_first | True | {'got': 0.69, 'want': 0.69} |
| composition_anchor_noise_uniform_s0_N5000 | True | {'L1_vs_anchor_expected': 0.0255, 'max_z_vs_anchor_expected': 1.765, 'L1_vs_pool': 0.0887, 'max_z_vs_pool': 9.535, 'n_docs': 5000} |
| composition_anchor_noise_uniform_s0_N10000 | True | {'L1_vs_anchor_expected': 0.0141, 'max_z_vs_anchor_expected': 1.624, 'L1_vs_pool': 0.044, 'max_z_vs_pool': 6.406, 'n_docs': 10000} |
| composition_anchor_noise_uniform_s0_N15000 | True | {'L1_vs_anchor_expected': 0.0154, 'max_z_vs_anchor_expected': 1.585, 'L1_vs_pool': 0.0319, 'max_z_vs_pool': 5.03, 'n_docs': 15000} |
| composition_anchor_noise_uniform_s0_N20000 | True | {'L1_vs_anchor_expected': 0.0126, 'max_z_vs_anchor_expected': 1.324, 'L1_vs_pool': 0.0206, 'max_z_vs_pool': 4.086, 'n_docs': 20000} |
| composition_anchor_noise_uniform_s0_N25000 | True | {'L1_vs_anchor_expected': 0.0123, 'max_z_vs_anchor_expected': 1.653, 'L1_vs_pool': 0.0207, 'max_z_vs_pool': 4.127, 'n_docs': 25000} |
| composition_anchor_noise_uniform_s0_N40000 | True | {'L1_vs_anchor_expected': 0.0108, 'max_z_vs_anchor_expected': 1.557, 'L1_vs_pool': 0.0132, 'max_z_vs_pool': 2.781, 'n_docs': 40000} |
| composition_anchor_noise_uniform_s0_N50000 | True | {'L1_vs_anchor_expected': 0.0066, 'max_z_vs_anchor_expected': 0.895, 'L1_vs_pool': 0.0079, 'max_z_vs_pool': 2.308, 'n_docs': 50000} |
| composition_anchor_noise_uniform_s0_N75000 | True | {'L1_vs_anchor_expected': 0.0043, 'max_z_vs_anchor_expected': 1.257, 'L1_vs_pool': 0.0048, 'max_z_vs_pool': 1.32, 'n_docs': 75000} |
| composition_anchor_noise_uniform_s0_N100000 | True | {'L1_vs_anchor_expected': 0.0, 'max_z_vs_anchor_expected': 0.0, 'L1_vs_pool': 0.0, 'max_z_vs_pool': 0.0, 'n_docs': 99998} |
| composition_anchor_noise_uniform_s0_titan_N5000 | True | {'L1_vs_anchor_expected': 0.0255, 'max_z_vs_anchor_expected': 1.765, 'L1_vs_pool': 0.0887, 'max_z_vs_pool': 9.535, 'n_docs': 5000} |
| composition_anchor_noise_uniform_s0_titan_N10000 | True | {'L1_vs_anchor_expected': 0.0141, 'max_z_vs_anchor_expected': 1.624, 'L1_vs_pool': 0.044, 'max_z_vs_pool': 6.406, 'n_docs': 10000} |
| composition_anchor_noise_uniform_s0_titan_N15000 | True | {'L1_vs_anchor_expected': 0.0154, 'max_z_vs_anchor_expected': 1.585, 'L1_vs_pool': 0.0319, 'max_z_vs_pool': 5.03, 'n_docs': 15000} |
| composition_anchor_noise_uniform_s0_titan_N20000 | True | {'L1_vs_anchor_expected': 0.0126, 'max_z_vs_anchor_expected': 1.324, 'L1_vs_pool': 0.0206, 'max_z_vs_pool': 4.086, 'n_docs': 20000} |
| composition_anchor_noise_uniform_s0_titan_N25000 | True | {'L1_vs_anchor_expected': 0.0123, 'max_z_vs_anchor_expected': 1.653, 'L1_vs_pool': 0.0207, 'max_z_vs_pool': 4.127, 'n_docs': 25000} |
| composition_anchor_noise_uniform_s0_titan_N40000 | True | {'L1_vs_anchor_expected': 0.0108, 'max_z_vs_anchor_expected': 1.557, 'L1_vs_pool': 0.0132, 'max_z_vs_pool': 2.781, 'n_docs': 40000} |
| composition_anchor_noise_uniform_s0_titan_N50000 | True | {'L1_vs_anchor_expected': 0.0066, 'max_z_vs_anchor_expected': 0.895, 'L1_vs_pool': 0.0079, 'max_z_vs_pool': 2.308, 'n_docs': 50000} |
| composition_anchor_noise_uniform_s0_titan_N75000 | True | {'L1_vs_anchor_expected': 0.0043, 'max_z_vs_anchor_expected': 1.257, 'L1_vs_pool': 0.0048, 'max_z_vs_pool': 1.32, 'n_docs': 75000} |
| composition_anchor_noise_uniform_s0_titan_N100000 | True | {'L1_vs_anchor_expected': 0.0, 'max_z_vs_anchor_expected': 0.0, 'L1_vs_pool': 0.0, 'max_z_vs_pool': 0.0, 'n_docs': 99998} |
| composition_anchor_noise_uniform_s42_N5000 | True | {'L1_vs_anchor_expected': 0.0224, 'max_z_vs_anchor_expected': 0.988, 'L1_vs_pool': 0.1092, 'max_z_vs_pool': 10.874, 'n_docs': 5000} |
| composition_anchor_noise_uniform_s42_N10000 | True | {'L1_vs_anchor_expected': 0.0175, 'max_z_vs_anchor_expected': 1.425, 'L1_vs_pool': 0.053, 'max_z_vs_pool': 6.992, 'n_docs': 10000} |
| composition_anchor_noise_uniform_s42_N15000 | True | {'L1_vs_anchor_expected': 0.0105, 'max_z_vs_anchor_expected': 0.784, 'L1_vs_pool': 0.0315, 'max_z_vs_pool': 5.729, 'n_docs': 15000} |
| composition_anchor_noise_uniform_s42_N20000 | True | {'L1_vs_anchor_expected': 0.0129, 'max_z_vs_anchor_expected': 1.386, 'L1_vs_pool': 0.0266, 'max_z_vs_pool': 4.788, 'n_docs': 20000} |
| composition_anchor_noise_uniform_s42_N25000 | True | {'L1_vs_anchor_expected': 0.0092, 'max_z_vs_anchor_expected': 1.372, 'L1_vs_pool': 0.0171, 'max_z_vs_pool': 3.899, 'n_docs': 25000} |
| composition_anchor_noise_uniform_s42_N40000 | True | {'L1_vs_anchor_expected': 0.0071, 'max_z_vs_anchor_expected': 0.898, 'L1_vs_pool': 0.0093, 'max_z_vs_pool': 1.699, 'n_docs': 40000} |
| composition_anchor_noise_uniform_s42_N50000 | True | {'L1_vs_anchor_expected': 0.0041, 'max_z_vs_anchor_expected': 0.664, 'L1_vs_pool': 0.0055, 'max_z_vs_pool': 1.662, 'n_docs': 50000} |
| composition_anchor_noise_uniform_s42_N75000 | True | {'L1_vs_anchor_expected': 0.003, 'max_z_vs_anchor_expected': 0.615, 'L1_vs_pool': 0.0043, 'max_z_vs_pool': 0.941, 'n_docs': 75000} |
| composition_anchor_noise_uniform_s42_N100000 | True | {'L1_vs_anchor_expected': 0.0, 'max_z_vs_anchor_expected': 0.0, 'L1_vs_pool': 0.0, 'max_z_vs_pool': 0.0, 'n_docs': 99998} |
| composition_anchor_noise_uniform_s42_titan_N5000 | True | {'L1_vs_anchor_expected': 0.0224, 'max_z_vs_anchor_expected': 0.988, 'L1_vs_pool': 0.1092, 'max_z_vs_pool': 10.874, 'n_docs': 5000} |
| composition_anchor_noise_uniform_s42_titan_N10000 | True | {'L1_vs_anchor_expected': 0.0175, 'max_z_vs_anchor_expected': 1.425, 'L1_vs_pool': 0.053, 'max_z_vs_pool': 6.992, 'n_docs': 10000} |
| composition_anchor_noise_uniform_s42_titan_N15000 | True | {'L1_vs_anchor_expected': 0.0105, 'max_z_vs_anchor_expected': 0.784, 'L1_vs_pool': 0.0315, 'max_z_vs_pool': 5.729, 'n_docs': 15000} |
| composition_anchor_noise_uniform_s42_titan_N20000 | True | {'L1_vs_anchor_expected': 0.0129, 'max_z_vs_anchor_expected': 1.386, 'L1_vs_pool': 0.0266, 'max_z_vs_pool': 4.788, 'n_docs': 20000} |
| composition_anchor_noise_uniform_s42_titan_N25000 | True | {'L1_vs_anchor_expected': 0.0092, 'max_z_vs_anchor_expected': 1.372, 'L1_vs_pool': 0.0171, 'max_z_vs_pool': 3.899, 'n_docs': 25000} |
| composition_anchor_noise_uniform_s42_titan_N40000 | True | {'L1_vs_anchor_expected': 0.0071, 'max_z_vs_anchor_expected': 0.898, 'L1_vs_pool': 0.0093, 'max_z_vs_pool': 1.699, 'n_docs': 40000} |
| composition_anchor_noise_uniform_s42_titan_N50000 | True | {'L1_vs_anchor_expected': 0.0041, 'max_z_vs_anchor_expected': 0.664, 'L1_vs_pool': 0.0055, 'max_z_vs_pool': 1.662, 'n_docs': 50000} |
| composition_anchor_noise_uniform_s42_titan_N75000 | True | {'L1_vs_anchor_expected': 0.003, 'max_z_vs_anchor_expected': 0.615, 'L1_vs_pool': 0.0043, 'max_z_vs_pool': 0.941, 'n_docs': 75000} |
| composition_anchor_noise_uniform_s42_titan_N100000 | True | {'L1_vs_anchor_expected': 0.0, 'max_z_vs_anchor_expected': 0.0, 'L1_vs_pool': 0.0, 'max_z_vs_pool': 0.0, 'n_docs': 99998} |
| nesting_nested_corpus | True | {'note': 'via nested_corpus violations'} |

## Confluence-first 41 questions (Hit@10)

| scale | uniform ladders (raw / meta_first) | round-robin (raw / meta_first) |
|------:|-----------------------------------:|------------------------------:|
| 5000 | 0.878 / 0.951 | 0.854 / 0.951 |
| 10000 | 0.805 / 0.927 | 0.829 / 0.927 |
| 15000 | 0.780 / 0.902 | 0.805 / 0.902 |
| 20000 | 0.756 / 0.902 | 0.780 / 0.878 |
| 25000 | 0.756 / 0.902 | 0.756 / 0.878 |
| 40000 | 0.756 / 0.878 | 0.732 / 0.829 |
| 50000 | 0.756 / 0.878 | 0.732 / 0.829 |
| 75000 | 0.707 / 0.854 | 0.707 / 0.829 |
| 100000 | 0.707 / 0.829 | 0.707 / 0.829 |

## Hit@10 (available runs)

### uniform_s0
| scale | raw | meta_first | meta_in |
|------:|----:|-----------:|--------:|
| 5000 | 0.795 | 0.870 | 0.870 |
| 10000 | 0.745 | 0.830 | 0.830 |
| 15000 | 0.725 | 0.795 | 0.795 |
| 20000 | 0.710 | 0.785 | 0.785 |
| 25000 | 0.680 | 0.775 | 0.770 |
| 40000 | 0.660 | 0.745 | 0.740 |
| 50000 | 0.630 | 0.710 | 0.705 |
| 75000 | 0.590 | 0.690 | 0.685 |
| 100000 | 0.585 | 0.670 | 0.665 |

### uniform_s0_titan
| scale | raw | meta_first | meta_in |
|------:|----:|-----------:|--------:|
| 5000 | 0.795 | 0.895 | 0.895 |
| 10000 | 0.750 | 0.840 | 0.835 |
| 15000 | 0.730 | 0.800 | 0.795 |
| 20000 | 0.715 | 0.785 | 0.785 |
| 25000 | 0.690 | 0.775 | 0.775 |
| 40000 | 0.665 | 0.760 | 0.760 |
| 50000 | 0.660 | 0.755 | 0.755 |
| 75000 | 0.620 | 0.705 | 0.705 |
| 100000 | 0.610 | 0.690 | 0.685 |

### uniform_s42
| scale | raw | meta_first | meta_in |
|------:|----:|-----------:|--------:|
| 5000 | 0.790 | 0.865 | 0.865 |
| 10000 | 0.760 | 0.840 | 0.840 |
| 15000 | 0.720 | 0.800 | 0.800 |
| 20000 | 0.685 | 0.775 | 0.775 |
| 25000 | 0.675 | 0.765 | 0.760 |
| 40000 | 0.640 | 0.740 | 0.730 |
| 50000 | 0.630 | 0.720 | 0.715 |
| 75000 | 0.590 | 0.695 | 0.685 |
| 100000 | 0.585 | 0.670 | 0.665 |

### uniform_s42_titan
| scale | raw | meta_first | meta_in |
|------:|----:|-----------:|--------:|
| 5000 | 0.805 | 0.905 | 0.905 |
| 10000 | 0.765 | 0.830 | 0.830 |
| 15000 | 0.750 | 0.800 | 0.800 |
| 20000 | 0.725 | 0.790 | 0.790 |
| 25000 | 0.710 | 0.785 | 0.785 |
| 40000 | 0.665 | 0.765 | 0.765 |
| 50000 | 0.660 | 0.750 | 0.750 |
| 75000 | 0.625 | 0.710 | 0.710 |
| 100000 | 0.610 | 0.690 | 0.685 |

### rr_s0
| scale | raw | meta_first | meta_in |
|------:|----:|-----------:|--------:|
| 5000 | 0.785 | 0.865 | 0.865 |
| 10000 | 0.750 | 0.835 | 0.835 |
| 15000 | 0.715 | 0.815 | 0.815 |
| 20000 | 0.685 | 0.790 | 0.785 |
| 25000 | 0.675 | 0.775 | 0.770 |
| 40000 | 0.655 | 0.730 | 0.735 |
| 50000 | 0.635 | 0.710 | 0.710 |
| 75000 | 0.615 | 0.685 | 0.685 |
| 100000 | 0.585 | 0.670 | 0.665 |

### rr_s0_titan
| scale | raw | meta_first | meta_in |
|------:|----:|-----------:|--------:|
| 5000 | 0.795 | 0.875 | 0.880 |
| 10000 | 0.745 | 0.830 | 0.830 |
| 15000 | 0.725 | 0.810 | 0.810 |
| 20000 | 0.705 | 0.795 | 0.795 |
| 25000 | 0.685 | 0.780 | 0.780 |
| 40000 | 0.650 | 0.765 | 0.765 |
| 50000 | 0.630 | 0.750 | 0.745 |
| 75000 | 0.610 | 0.710 | 0.710 |
| 100000 | 0.610 | 0.690 | 0.685 |
