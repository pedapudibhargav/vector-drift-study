# Pool ladder analysis

- Confluence-first questions: **41**
- Aligned questions: **200**

## Acceptance

| test | pass | detail |
|------|:----:|--------|
| invariants_zero_prop_s0 | True | {'values': {'containment': 0, 'nested_corpus': 0, 'score_monotonicity': 0}} |
| invariants_zero_prop_s42 | True | {'values': {'containment': 0, 'nested_corpus': 0, 'score_monotonicity': 0}} |
| invariants_zero_rr_full | True | {'values': {'containment': 0, 'nested_corpus': 0, 'score_monotonicity': 0}} |

## Hit@10

### prop_s0
| scale | raw | meta_first | meta_in |
|------:|----:|-----------:|--------:|
| 5000 | 0.8000 | 0.8750 | 0.8750 |
| 10000 | 0.7700 | 0.8600 | 0.8600 |
| 15000 | 0.7550 | 0.8200 | 0.8200 |
| 20000 | 0.7200 | 0.8000 | 0.8000 |
| 25000 | 0.7000 | 0.7900 | 0.7900 |
| 40000 | 0.6600 | 0.7550 | 0.7500 |
| 50000 | 0.6500 | 0.7450 | 0.7400 |
| 75000 | 0.6150 | 0.7250 | 0.7200 |
| 100000 | 0.5750 | 0.6950 | 0.6850 |
| 150000 | 0.5200 | 0.6750 | 0.6600 |
| full | 0.5150 | 0.6550 | 0.6450 |

### prop_s42
| scale | raw | meta_first | meta_in |
|------:|----:|-----------:|--------:|
| 5000 | 0.8250 | 0.9000 | 0.9000 |
| 10000 | 0.7650 | 0.8550 | 0.8550 |
| 15000 | 0.7450 | 0.8200 | 0.8200 |
| 20000 | 0.7200 | 0.8050 | 0.8050 |
| 25000 | 0.6900 | 0.7900 | 0.7900 |
| 40000 | 0.6600 | 0.7650 | 0.7600 |
| 50000 | 0.6550 | 0.7600 | 0.7550 |
| 75000 | 0.6100 | 0.7250 | 0.7150 |
| 100000 | 0.5950 | 0.6900 | 0.6800 |
| 150000 | 0.5200 | 0.6750 | 0.6600 |
| full | 0.5150 | 0.6550 | 0.6450 |

### rr_full
| scale | raw | meta_first | meta_in |
|------:|----:|-----------:|--------:|
| 5000 | 0.7950 | 0.8750 | 0.8750 |
| 10000 | 0.7350 | 0.8350 | 0.8350 |
| 15000 | 0.7100 | 0.8050 | 0.8050 |
| 20000 | 0.6800 | 0.7750 | 0.7700 |
| 25000 | 0.6700 | 0.7650 | 0.7600 |
| 40000 | 0.6450 | 0.7200 | 0.7200 |
| 50000 | 0.6400 | 0.7150 | 0.7150 |
| 75000 | 0.5950 | 0.6850 | 0.6850 |
| 100000 | 0.5850 | 0.6700 | 0.6650 |
| 150000 | 0.5400 | 0.6600 | 0.6500 |
| full | 0.5150 | 0.6550 | 0.6450 |

## Composition shares
- extracted pool (100k unique): {'confluence': 0.0519, 'fireflies': 0.1017, 'github': 0.0805, 'gmail': 0.1407, 'google_drive': 0.1412, 'hubspot': 0.141, 'jira': 0.0612, 'linear': 0.1412, 'slack': 0.1406}

### prop_s42
| scale | n | shares |
|------:|--:|--------|
| 5000 | 5000 | {'confluence': 0.0632, 'fireflies': 0.0544, 'github': 0.049, 'gmail': 0.192, 'google_drive': 0.1382, 'hubspot': 0.0784, 'jira': 0.052, 'linear': 0.1876, 'slack': 0.1852} |
| 10000 | 10000 | {'confluence': 0.0439, 'fireflies': 0.0546, 'github': 0.0451, 'gmail': 0.2066, 'google_drive': 0.1369, 'hubspot': 0.0811, 'jira': 0.0441, 'linear': 0.1886, 'slack': 0.1991} |
| 15000 | 15000 | {'confluence': 0.0385, 'fireflies': 0.054, 'github': 0.0428, 'gmail': 0.2089, 'google_drive': 0.1372, 'hubspot': 0.083, 'jira': 0.0403, 'linear': 0.1912, 'slack': 0.2041} |
| 20000 | 20000 | {'confluence': 0.0361, 'fireflies': 0.0553, 'github': 0.0432, 'gmail': 0.2125, 'google_drive': 0.1368, 'hubspot': 0.0822, 'jira': 0.0375, 'linear': 0.189, 'slack': 0.2073} |
| 25000 | 25000 | {'confluence': 0.0336, 'fireflies': 0.0558, 'github': 0.0439, 'gmail': 0.2125, 'google_drive': 0.1361, 'hubspot': 0.0826, 'jira': 0.0364, 'linear': 0.1877, 'slack': 0.2113} |
| 40000 | 40000 | {'confluence': 0.0319, 'fireflies': 0.0567, 'github': 0.0438, 'gmail': 0.2137, 'google_drive': 0.1326, 'hubspot': 0.0829, 'jira': 0.0347, 'linear': 0.1898, 'slack': 0.214} |
| 50000 | 50000 | {'confluence': 0.0309, 'fireflies': 0.056, 'github': 0.0438, 'gmail': 0.2135, 'google_drive': 0.1343, 'hubspot': 0.0815, 'jira': 0.0347, 'linear': 0.19, 'slack': 0.2154} |
| 75000 | 75000 | {'confluence': 0.0292, 'fireflies': 0.0552, 'github': 0.044, 'gmail': 0.2143, 'google_drive': 0.1347, 'hubspot': 0.0811, 'jira': 0.0341, 'linear': 0.1909, 'slack': 0.2164} |
| 100000 | 100000 | {'confluence': 0.0284, 'fireflies': 0.055, 'github': 0.0441, 'gmail': 0.2156, 'google_drive': 0.1355, 'hubspot': 0.0815, 'jira': 0.0335, 'linear': 0.1902, 'slack': 0.2163} |
| 150000 | 150000 | {'confluence': 0.0282, 'fireflies': 0.0549, 'github': 0.0434, 'gmail': 0.216, 'google_drive': 0.1358, 'hubspot': 0.0811, 'jira': 0.0333, 'linear': 0.1909, 'slack': 0.2165} |
| full | 184963 | {'confluence': 0.0281, 'fireflies': 0.055, 'github': 0.0435, 'gmail': 0.2163, 'google_drive': 0.1357, 'hubspot': 0.0812, 'jira': 0.0331, 'linear': 0.1909, 'slack': 0.2163} |

### prop_s0
| scale | n | shares |
|------:|--:|--------|
| 5000 | 5000 | {'confluence': 0.0618, 'fireflies': 0.0554, 'github': 0.0492, 'gmail': 0.1846, 'google_drive': 0.139, 'hubspot': 0.0812, 'jira': 0.0524, 'linear': 0.1846, 'slack': 0.1918} |
| 10000 | 10000 | {'confluence': 0.045, 'fireflies': 0.0545, 'github': 0.0485, 'gmail': 0.2033, 'google_drive': 0.1341, 'hubspot': 0.0823, 'jira': 0.0422, 'linear': 0.1864, 'slack': 0.2037} |
| 15000 | 15000 | {'confluence': 0.0379, 'fireflies': 0.055, 'github': 0.0467, 'gmail': 0.209, 'google_drive': 0.1344, 'hubspot': 0.0833, 'jira': 0.0389, 'linear': 0.1874, 'slack': 0.2074} |
| 20000 | 20000 | {'confluence': 0.0352, 'fireflies': 0.0551, 'github': 0.0457, 'gmail': 0.2111, 'google_drive': 0.1346, 'hubspot': 0.0827, 'jira': 0.037, 'linear': 0.1883, 'slack': 0.2103} |
| 25000 | 25000 | {'confluence': 0.0337, 'fireflies': 0.0539, 'github': 0.0452, 'gmail': 0.2117, 'google_drive': 0.1346, 'hubspot': 0.0818, 'jira': 0.0366, 'linear': 0.1896, 'slack': 0.2128} |
| 40000 | 40000 | {'confluence': 0.0315, 'fireflies': 0.0527, 'github': 0.0442, 'gmail': 0.216, 'google_drive': 0.1352, 'hubspot': 0.0817, 'jira': 0.0354, 'linear': 0.1903, 'slack': 0.213} |
| 50000 | 50000 | {'confluence': 0.03, 'fireflies': 0.0527, 'github': 0.044, 'gmail': 0.2172, 'google_drive': 0.1349, 'hubspot': 0.0816, 'jira': 0.0345, 'linear': 0.1903, 'slack': 0.2148} |
| 75000 | 75000 | {'confluence': 0.029, 'fireflies': 0.0537, 'github': 0.0442, 'gmail': 0.2167, 'google_drive': 0.1345, 'hubspot': 0.0811, 'jira': 0.0334, 'linear': 0.1905, 'slack': 0.2169} |
| 100000 | 100000 | {'confluence': 0.0285, 'fireflies': 0.0539, 'github': 0.0436, 'gmail': 0.2167, 'google_drive': 0.1353, 'hubspot': 0.0817, 'jira': 0.0334, 'linear': 0.1906, 'slack': 0.2163} |
| 150000 | 150000 | {'confluence': 0.0283, 'fireflies': 0.0544, 'github': 0.0435, 'gmail': 0.2167, 'google_drive': 0.1353, 'hubspot': 0.081, 'jira': 0.0334, 'linear': 0.1911, 'slack': 0.2164} |
| full | 184963 | {'confluence': 0.0281, 'fireflies': 0.055, 'github': 0.0435, 'gmail': 0.2163, 'google_drive': 0.1357, 'hubspot': 0.0812, 'jira': 0.0331, 'linear': 0.1909, 'slack': 0.2163} |

### rr_full
| scale | n | shares |
|------:|--:|--------|
| 5000 | 5000 | {'confluence': 0.1366, 'fireflies': 0.1036, 'github': 0.1102, 'gmail': 0.1008, 'google_drive': 0.1118, 'hubspot': 0.1072, 'jira': 0.1192, 'linear': 0.1108, 'slack': 0.0998} |
| 10000 | 10000 | {'confluence': 0.1239, 'fireflies': 0.1074, 'github': 0.1107, 'gmail': 0.106, 'google_drive': 0.1114, 'hubspot': 0.1091, 'jira': 0.1151, 'linear': 0.1109, 'slack': 0.1055} |
| 15000 | 15000 | {'confluence': 0.1196, 'fireflies': 0.1086, 'github': 0.1108, 'gmail': 0.1077, 'google_drive': 0.1113, 'hubspot': 0.1098, 'jira': 0.1138, 'linear': 0.111, 'slack': 0.1074} |
| 20000 | 20000 | {'confluence': 0.1175, 'fireflies': 0.1092, 'github': 0.1109, 'gmail': 0.1085, 'google_drive': 0.1113, 'hubspot': 0.1101, 'jira': 0.1131, 'linear': 0.111, 'slack': 0.1083} |
| 25000 | 25000 | {'confluence': 0.1163, 'fireflies': 0.1096, 'github': 0.1109, 'gmail': 0.109, 'google_drive': 0.1112, 'hubspot': 0.1103, 'jira': 0.1127, 'linear': 0.111, 'slack': 0.1089} |
| 40000 | 39999 | {'confluence': 0.1143, 'fireflies': 0.1102, 'github': 0.111, 'gmail': 0.1098, 'google_drive': 0.1112, 'hubspot': 0.1106, 'jira': 0.1121, 'linear': 0.1111, 'slack': 0.1097} |
| 50000 | 49999 | {'confluence': 0.1038, 'fireflies': 0.1116, 'github': 0.1123, 'gmail': 0.1113, 'google_drive': 0.1124, 'hubspot': 0.112, 'jira': 0.1131, 'linear': 0.1123, 'slack': 0.1112} |
| 75000 | 74999 | {'confluence': 0.0692, 'fireflies': 0.1235, 'github': 0.1074, 'gmail': 0.1233, 'google_drive': 0.1241, 'hubspot': 0.1237, 'jira': 0.0816, 'linear': 0.124, 'slack': 0.1233} |
| 100000 | 99998 | {'confluence': 0.0519, 'fireflies': 0.1017, 'github': 0.0805, 'gmail': 0.1407, 'google_drive': 0.1412, 'hubspot': 0.141, 'jira': 0.0612, 'linear': 0.1412, 'slack': 0.1406} |
| 150000 | 149997 | {'confluence': 0.0346, 'fireflies': 0.0678, 'github': 0.0537, 'gmail': 0.1784, 'google_drive': 0.1674, 'hubspot': 0.1001, 'jira': 0.0408, 'linear': 0.1788, 'slack': 0.1784} |
| full | 184963 | {'confluence': 0.0281, 'fireflies': 0.055, 'github': 0.0435, 'gmail': 0.2163, 'google_drive': 0.1357, 'hubspot': 0.0812, 'jira': 0.0331, 'linear': 0.1909, 'slack': 0.2163} |

## Drop 5k vs 100k / full (paired bootstrap)

### prop_s0
- **raw**: `{"drop_5k_to_100k": {"estimate": 0.225, "ci_lo": 0.17, "ci_hi": 0.285}, "drop_5k_to_100k_minus_original_rr": {"estimate": 0.015, "ci_lo": -0.015, "ci_hi": 0.045, "original_rr_drop": 0.21}, "drop_5k_to_full": {"estimate": 0.285, "ci_lo": 0.225, "ci_hi": 0.35, "full_n": 184963}, "drop_5k_to_full_minus_original_rr": {"estimate": 0.075, "ci_lo": 0.035, "ci_hi": 0.12, "original_rr_drop": 0.21}}`
- **meta_first**: `{"drop_5k_to_100k": {"estimate": 0.18, "ci_lo": 0.13, "ci_hi": 0.235}, "drop_5k_to_100k_minus_original_rr": {"estimate": -0.025, "ci_lo": -0.055, "ci_hi": 0.005, "original_rr_drop": 0.205}, "drop_5k_to_full": {"estimate": 0.22, "ci_lo": 0.165, "ci_hi": 0.28, "full_n": 184963}, "drop_5k_to_full_minus_original_rr": {"estimate": 0.015, "ci_lo": -0.01, "ci_hi": 0.04, "original_rr_drop": 0.205}}`
- **meta_in**: `{"drop_5k_to_100k": {"estimate": 0.19, "ci_lo": 0.135, "ci_hi": 0.245}, "drop_5k_to_100k_minus_original_rr": {"estimate": -0.02, "ci_lo": -0.05, "ci_hi": 0.005, "original_rr_drop": 0.21}, "drop_5k_to_full": {"estimate": 0.23, "ci_lo": 0.175, "ci_hi": 0.29, "full_n": 184963}, "drop_5k_to_full_minus_original_rr": {"estimate": 0.02, "ci_lo": -0.005, "ci_hi": 0.05, "original_rr_drop": 0.21}}`

### prop_s42
- **raw**: `{"drop_5k_to_100k": {"estimate": 0.23, "ci_lo": 0.175, "ci_hi": 0.29}, "drop_5k_to_100k_minus_original_rr": {"estimate": 0.02, "ci_lo": -0.01, "ci_hi": 0.055, "original_rr_drop": 0.21}, "drop_5k_to_full": {"estimate": 0.31, "ci_lo": 0.245, "ci_hi": 0.375, "full_n": 184963}, "drop_5k_to_full_minus_original_rr": {"estimate": 0.1, "ci_lo": 0.06, "ci_hi": 0.145, "original_rr_drop": 0.21}}`
- **meta_first**: `{"drop_5k_to_100k": {"estimate": 0.21, "ci_lo": 0.155, "ci_hi": 0.27}, "drop_5k_to_100k_minus_original_rr": {"estimate": 0.005, "ci_lo": -0.025, "ci_hi": 0.035, "original_rr_drop": 0.205}, "drop_5k_to_full": {"estimate": 0.245, "ci_lo": 0.185, "ci_hi": 0.305, "full_n": 184963}, "drop_5k_to_full_minus_original_rr": {"estimate": 0.04, "ci_lo": 0.015, "ci_hi": 0.07, "original_rr_drop": 0.205}}`
- **meta_in**: `{"drop_5k_to_100k": {"estimate": 0.22, "ci_lo": 0.165, "ci_hi": 0.28}, "drop_5k_to_100k_minus_original_rr": {"estimate": 0.01, "ci_lo": -0.015, "ci_hi": 0.04, "original_rr_drop": 0.21}, "drop_5k_to_full": {"estimate": 0.255, "ci_lo": 0.195, "ci_hi": 0.315, "full_n": 184963}, "drop_5k_to_full_minus_original_rr": {"estimate": 0.045, "ci_lo": 0.02, "ci_hi": 0.075, "original_rr_drop": 0.21}}`

### rr_full
- **raw**: `{"drop_5k_to_100k": {"estimate": 0.21, "ci_lo": 0.155, "ci_hi": 0.27}, "drop_5k_to_100k_minus_original_rr": {"estimate": 0.0, "ci_lo": 0.0, "ci_hi": 0.0, "original_rr_drop": 0.21}, "drop_5k_to_full": {"estimate": 0.28, "ci_lo": 0.22, "ci_hi": 0.345, "full_n": 184963}, "drop_5k_to_full_minus_original_rr": {"estimate": 0.07, "ci_lo": 0.035, "ci_hi": 0.105, "original_rr_drop": 0.21}}`
- **meta_first**: `{"drop_5k_to_100k": {"estimate": 0.205, "ci_lo": 0.15, "ci_hi": 0.26}, "drop_5k_to_100k_minus_original_rr": {"estimate": 0.0, "ci_lo": 0.0, "ci_hi": 0.0, "original_rr_drop": 0.205}, "drop_5k_to_full": {"estimate": 0.22, "ci_lo": 0.165, "ci_hi": 0.28, "full_n": 184963}, "drop_5k_to_full_minus_original_rr": {"estimate": 0.015, "ci_lo": 0.0, "ci_hi": 0.035, "original_rr_drop": 0.205}}`
- **meta_in**: `{"drop_5k_to_100k": {"estimate": 0.21, "ci_lo": 0.155, "ci_hi": 0.27}, "drop_5k_to_100k_minus_original_rr": {"estimate": 0.0, "ci_lo": 0.0, "ci_hi": 0.0, "original_rr_drop": 0.21}, "drop_5k_to_full": {"estimate": 0.23, "ci_lo": 0.175, "ci_hi": 0.29, "full_n": 184963}, "drop_5k_to_full_minus_original_rr": {"estimate": 0.02, "ci_lo": 0.005, "ci_hi": 0.04, "original_rr_drop": 0.21}}`
