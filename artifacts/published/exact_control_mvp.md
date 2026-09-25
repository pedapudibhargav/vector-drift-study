# Exact-search MVP control

If exact Hit@10 still declines with N similarly to HNSW, drift is not solely an ANN artifact. If exact stays flat while HNSW drops, HNSW parameters dominate.

| N | cond | exact Hit@10 | HNSW Hit@10 | Δ (exact−HNSW) | Hit@10 disagreements |
|---|------|--------------|-------------|----------------|----------------------|
| 5000 | raw | 0.795 | 0.795 | 0.0 | 0 |
| 50000 | raw | 0.64 | 0.555 | 0.085 | 17 |
| 100000 | raw | 0.585 | 0.51 | 0.075 | 15 |
