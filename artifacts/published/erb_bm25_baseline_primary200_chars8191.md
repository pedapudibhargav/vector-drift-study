# Okapi BM25 baseline (primary-200)

RQ2 control: classic Okapi BM25 on the same gold-pinned ladder as dense HNSW. Compare Hit@10 decline vs dense; if BM25 stays flat/near-floor while dense falls from a high baseline, the measured drift curve is dense-stack-specific on this bank.

| N | docs | Hit@1 | Hit@5 | Hit@10 | MRR |
|---|------|-------|-------|--------|-----|
| 5000 | 5000 | 0.715 | 0.8 | 0.825 | 0.7537 |
| 50000 | 49999 | 0.56 | 0.695 | 0.715 | 0.617 |
| 100000 | 99998 | 0.52 | 0.645 | 0.705 | 0.5809 |
