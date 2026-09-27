# ef_search ablation @ N=100k (OpenAI raw, primary-200)

If Hit@10 rises materially as ef_search increases toward exact search, part of the dense decline at 100k may be ANN recall loss rather than true semantic drift.

| ef_search | Hit@1 | Hit@5 | Hit@10 | MRR | Δ vs published ef=200 |
|-----------|-------|-------|--------|-----|------------------------|
| 200 | 0.3 | 0.465 | 0.51 | 0.3644 | 0.0 |
| 400 | 0.34 | 0.515 | 0.585 | 0.4114 | 0.075 |
| 800 | 0.34 | 0.515 | 0.585 | 0.4114 | 0.075 |
