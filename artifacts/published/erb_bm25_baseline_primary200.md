# Okapi BM25 baseline (primary-200)

RQ2 control: classic Okapi BM25 on the same gold-pinned ladder as dense HNSW. Compare Hit@10 decline vs dense; if BM25 stays flat/near-floor while dense falls from a high baseline, the measured drift curve is dense-stack-specific on this bank.

| N | docs | Hit@1 | Hit@5 | Hit@10 | MRR |
|---|------|-------|-------|--------|-----|
| 5000 | 5000 | 0.74 | 0.81 | 0.855 | 0.772 |
| 10000 | 10000 | 0.695 | 0.79 | 0.815 | 0.7321 |
| 15000 | 15000 | 0.665 | 0.78 | 0.8 | 0.708 |
| 20000 | 20000 | 0.655 | 0.76 | 0.79 | 0.6971 |
| 25000 | 25000 | 0.63 | 0.745 | 0.78 | 0.6776 |
| 40000 | 39999 | 0.595 | 0.71 | 0.75 | 0.6452 |
| 50000 | 49999 | 0.56 | 0.695 | 0.745 | 0.6231 |
| 75000 | 74999 | 0.53 | 0.68 | 0.715 | 0.5945 |
| 100000 | 99998 | 0.51 | 0.66 | 0.7 | 0.5748 |
