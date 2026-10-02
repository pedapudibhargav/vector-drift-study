# OpenAI vs Titan — paired bootstrap (B=5000, seed=42)

| metric | quantity | estimate | 95% CI |
|---|---|---:|---|
| hit_at_1 | openai_hnsw_drop | -0.295 | [-0.355, -0.23] |
| hit_at_1 | titan_hnsw_drop | -0.235 | [-0.295, -0.18] |
| hit_at_1 | openai_exact_drop | -0.26 | [-0.32, -0.2] |
| hit_at_1 | titan_exact_drop | -0.235 | [-0.295, -0.18] |
| hit_at_1 | hnsw_titan_minus_openai_drop | 0.06 | [-0.015, 0.135] |
| hit_at_1 | hnsw_titan_minus_openai_at_100k | 0.08 | [0.02, 0.14] |
| hit_at_1 | exact_titan_minus_openai_drop | 0.025 | [-0.05, 0.1] |
| hit_at_1 | exact_titan_minus_openai_at_100k | 0.045 | [-0.01, 0.105] |
| hit_at_10 | openai_hnsw_drop | -0.285 | [-0.345, -0.225] |
| hit_at_10 | titan_hnsw_drop | -0.175 | [-0.23, -0.12] |
| hit_at_10 | openai_exact_drop | -0.21 | [-0.265, -0.155] |
| hit_at_10 | titan_exact_drop | -0.175 | [-0.23, -0.12] |
| hit_at_10 | hnsw_titan_minus_openai_drop | 0.11 | [0.04, 0.175] |
| hit_at_10 | hnsw_titan_minus_openai_at_100k | 0.1 | [0.04, 0.16] |
| hit_at_10 | exact_titan_minus_openai_drop | 0.035 | [-0.025, 0.1] |
| hit_at_10 | exact_titan_minus_openai_at_100k | 0.025 | [-0.03, 0.08] |
| mrr | openai_hnsw_drop | -0.2929 | [-0.3433, -0.2418] |
| mrr | titan_hnsw_drop | -0.2065 | [-0.2495, -0.1643] |
| mrr | openai_exact_drop | -0.2492 | [-0.2959, -0.2028] |
| mrr | titan_exact_drop | -0.2065 | [-0.2495, -0.1643] |
| mrr | hnsw_titan_minus_openai_drop | 0.0865 | [0.0302, 0.1416] |
| mrr | hnsw_titan_minus_openai_at_100k | 0.1003 | [0.0515, 0.1486] |
| mrr | exact_titan_minus_openai_drop | 0.0427 | [-0.0078, 0.0924] |
| mrr | exact_titan_minus_openai_at_100k | 0.0565 | [0.0123, 0.1023] |

## Exact − HNSW Hit@10

| arm@N | estimate | 95% CI | disagreements |
|---|---:|---|---:|
| openai_5000 | 0.0 | [0.0, 0.0] | 0 |
| openai_50000 | 0.085 | [0.05, 0.125] | 17 |
| openai_100000 | 0.075 | [0.04, 0.11] | 15 |
| titan_5000 | 0.0 | [0.0, 0.0] | 0 |
| titan_50000 | 0.0 | [0.0, 0.0] | 0 |
| titan_100000 | 0.0 | [0.0, 0.0] | 0 |

## Δmeta (Hit@10)

- openai: {5000: 0.08, 10000: 0.175, 15000: 0.18, 20000: 0.175, 25000: 0.175, 40000: 0.135, 50000: 0.135, 75000: 0.135, 100000: 0.13} · below τ at [5000] · sustained N* = None
- titan: {5000: 0.085, 10000: 0.07, 15000: 0.075, 20000: 0.095, 25000: 0.095, 40000: 0.115, 50000: 0.105, 75000: 0.1, 100000: 0.08} · below τ at [5000, 10000, 15000, 20000, 25000, 100000] · sustained N* = 100000

Fits: {'openai': {'hit_at_1': {'a': 1.279, 'b': 0.087}, 'hit_at_10': {'a': 1.474, 'b': 0.086}, 'mrr': {'a': 1.359, 'b': 0.088}}, 'titan': {'hit_at_1': {'a': 1.382, 'b': 0.087}, 'hit_at_10': {'a': 1.334, 'b': 0.064}, 'mrr': {'a': 1.312, 'b': 0.074}}}

Overlap @100k: {'both_miss': 68, 'both_hit': 92, 'openai_only_hit': 10, 'titan_only_hit': 30}
