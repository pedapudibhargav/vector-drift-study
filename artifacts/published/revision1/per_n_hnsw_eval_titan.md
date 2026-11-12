# Per-N HNSW vs exact (W9, titan)

Generated: 2026-11-10T23:48:27Z
Questions: 200
Repeats: 3
shared_buffers: 2GB

## 1. recall@10 vs exact top-10 (raw, /10 set overlap)

### iterative_scan = relaxed_order, max_scan_tuples default 20000

| N | ef=40 | ef=100 | ef=200 | ef=400 | ef=800 |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 5000 | 0.972 | 0.994 | 0.9985 | 1.0 | 1.0 |
| 10000 | 0.9555 | 0.988 | 0.999 | 1.0 | 1.0 |
| 15000 | 0.943 | 0.987 | 0.9945 | 0.999 | 1.0 |
| 20000 | 0.942 | 0.9845 | 0.9945 | 0.999 | 1.0 |
| 25000 | 0.9405 | 0.983 | 0.994 | 0.998 | 1.0 |
| 40000 | 0.92 | 0.981 | 0.9935 | 0.998 | 0.9995 |
| 50000 | 0.928 | 0.9775 | 0.99 | 0.998 | 0.9995 |
| 75000 | 0.897 | 0.966 | 0.983 | 0.994 | 0.998 |
| 100000 | 0.8915 | 0.9535 | 0.9745 | 0.993 | 0.9975 |

### iterative_scan = strict_order, max_scan_tuples default 20000

| N | ef=40 | ef=100 | ef=200 | ef=400 | ef=800 |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 5000 | 0.972 | 0.994 | 0.9985 | 1.0 | 1.0 |
| 10000 | 0.9555 | 0.988 | 0.999 | 1.0 | 1.0 |
| 15000 | 0.943 | 0.987 | 0.9945 | 0.999 | 1.0 |
| 20000 | 0.942 | 0.9845 | 0.9945 | 0.999 | 1.0 |
| 25000 | 0.9405 | 0.983 | 0.994 | 0.998 | 1.0 |
| 40000 | 0.92 | 0.981 | 0.9935 | 0.998 | 0.9995 |
| 50000 | 0.928 | 0.9775 | 0.99 | 0.998 | 0.9995 |
| 75000 | 0.897 | 0.966 | 0.983 | 0.994 | 0.998 |
| 100000 | 0.8915 | 0.9535 | 0.9745 | 0.993 | 0.9975 |

## 2. Hit@10 drop (exact − HNSW), raw

### iterative_scan = relaxed_order

| N | ef=40 | ef=100 | ef=200 | ef=400 | ef=800 |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 5000 | 0.04 | 0.01 | 0.0 | 0.0 | 0.0 |
| 10000 | 0.05 | 0.015 | 0.005 | 0.0 | 0.0 |
| 15000 | 0.055 | 0.015 | 0.015 | 0.0 | 0.0 |
| 20000 | 0.04 | 0.01 | 0.01 | 0.005 | 0.0 |
| 25000 | 0.055 | 0.03 | 0.01 | 0.005 | 0.0 |
| 40000 | 0.055 | 0.025 | 0.015 | 0.01 | 0.005 |
| 50000 | 0.04 | 0.02 | 0.015 | 0.01 | 0.005 |
| 75000 | 0.06 | 0.015 | 0.015 | 0.01 | 0.01 |
| 100000 | 0.08 | 0.035 | 0.015 | 0.015 | 0.0 |

### iterative_scan = strict_order

| N | ef=40 | ef=100 | ef=200 | ef=400 | ef=800 |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 5000 | 0.04 | 0.01 | 0.0 | 0.0 | 0.0 |
| 10000 | 0.05 | 0.015 | 0.005 | 0.0 | 0.0 |
| 15000 | 0.055 | 0.015 | 0.015 | 0.0 | 0.0 |
| 20000 | 0.04 | 0.01 | 0.01 | 0.005 | 0.0 |
| 25000 | 0.055 | 0.03 | 0.01 | 0.005 | 0.0 |
| 40000 | 0.055 | 0.025 | 0.015 | 0.01 | 0.005 |
| 50000 | 0.04 | 0.02 | 0.015 | 0.01 | 0.005 |
| 75000 | 0.06 | 0.015 | 0.015 | 0.01 | 0.01 |
| 100000 | 0.08 | 0.035 | 0.015 | 0.015 | 0.0 |

## 3. Latency (raw, p50 / p95 ms of per-query medians over repeats)

### iterative_scan = relaxed_order

| N | ef=40 p50 | ef=100 p50 | ef=200 p50 | ef=400 p50 | ef=800 p50 | ef=40 p95 | ef=100 p95 | ef=200 p95 | ef=400 p95 | ef=800 p95 |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 5000 | 1.551 | 2.038 | 2.773 | 15.915 | 16.087 | 1.943 | 2.505 | 3.305 | 16.425 | 16.443 |
| 10000 | 1.845 | 2.332 | 3.144 | 4.558 | 29.867 | 2.293 | 2.944 | 3.958 | 5.567 | 30.277 |
| 15000 | 1.782 | 2.508 | 3.469 | 5.23 | 7.302 | 2.358 | 3.147 | 4.482 | 6.569 | 8.859 |
| 20000 | 1.9 | 2.486 | 3.503 | 5.354 | 8.302 | 2.336 | 3.237 | 4.516 | 6.773 | 10.419 |
| 25000 | 1.703 | 2.353 | 3.45 | 5.354 | 8.496 | 2.122 | 3.06 | 4.423 | 6.767 | 10.65 |
| 40000 | 1.626 | 2.487 | 3.426 | 5.219 | 8.382 | 2.064 | 3.163 | 4.667 | 6.726 | 10.88 |
| 50000 | 1.332 | 2.01 | 3.013 | 5.233 | 9.318 | 1.694 | 2.72 | 4.03 | 7.313 | 12.257 |
| 75000 | 1.891 | 2.644 | 3.797 | 5.93 | 10.174 | 2.749 | 3.428 | 4.955 | 7.643 | 13.17 |
| 100000 | 1.892 | 2.78 | 4.063 | 6.234 | 10.438 | 2.489 | 3.763 | 5.374 | 8.2 | 13.78 |

### iterative_scan = strict_order

| N | ef=40 p50 | ef=100 p50 | ef=200 p50 | ef=400 p50 | ef=800 p50 | ef=40 p95 | ef=100 p95 | ef=200 p95 | ef=400 p95 | ef=800 p95 |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 5000 | 1.554 | 2.109 | 2.818 | 16.197 | 16.004 | 1.909 | 2.585 | 3.533 | 16.524 | 16.338 |
| 10000 | 1.771 | 2.397 | 3.135 | 4.533 | 29.885 | 2.257 | 3.044 | 3.925 | 5.482 | 30.489 |
| 15000 | 1.758 | 2.453 | 3.669 | 4.95 | 7.711 | 2.217 | 3.11 | 4.6 | 6.243 | 9.389 |
| 20000 | 1.984 | 2.441 | 3.494 | 5.374 | 8.367 | 2.615 | 3.091 | 4.444 | 6.744 | 10.233 |
| 25000 | 1.662 | 2.343 | 3.4 | 5.345 | 8.183 | 2.125 | 2.981 | 4.336 | 6.823 | 10.367 |
| 40000 | 1.625 | 2.426 | 3.42 | 5.25 | 8.551 | 2.117 | 3.141 | 4.563 | 6.882 | 11.012 |
| 50000 | 1.322 | 2.005 | 2.99 | 6.186 | 9.669 | 1.702 | 2.72 | 3.963 | 8.438 | 12.407 |
| 75000 | 1.772 | 2.672 | 3.784 | 6.141 | 10.252 | 2.465 | 3.775 | 5.232 | 8.194 | 13.761 |
| 100000 | 1.816 | 2.72 | 3.977 | 6.254 | 10.287 | 2.382 | 3.524 | 5.445 | 8.284 | 13.975 |

## 4. Capacity (index / table from W8; latency = raw, ef=200, relaxed_order)

| N | rows | table_MB | hnsw_index_MB | build_s | p50_ms | p95_ms | mean_sweep_s |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 5000 | 5000 | 0.48 | 40.97 | 1.57 | 2.773 | 3.305 | 0.8657 |
| 10000 | 10000 | 0.97 | 81.93 | 3.6 | 3.144 | 3.958 | 0.9736 |
| 15000 | 15000 | 1.45 | 122.89 | 6.33 | 3.469 | 4.482 | 1.0603 |
| 20000 | 20000 | 1.93 | 163.85 | 8.74 | 3.503 | 4.516 | 1.0248 |
| 25000 | 25000 | 2.42 | 204.81 | 11.54 | 3.45 | 4.423 | 1.0221 |
| 40000 | 39999 | 3.86 | 327.68 | 19.21 | 3.426 | 4.667 | 1.0292 |
| 50000 | 49999 | 4.83 | 409.6 | 27.34 | 3.013 | 4.03 | 0.7834 |
| 75000 | 74999 | 7.23 | 614.38 | 39.5 | 3.797 | 4.955 | 1.1072 |
| 100000 | 99998 | 9.63 | 819.18 | 13.24 | 4.063 | 5.374 | 1.1741 |

## Extra max_scan_tuples=100000 (N=100000, ef=200)

| cond | mode | recall@10 | hit@10 | drop | short | p50_ms | p95_ms |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| raw | relaxed_order | 0.9745 | 0.595 | 0.015 | 0 | 4.3 | 5.744 |
| raw | strict_order | 0.9745 | 0.595 | 0.015 | 0 | 4.232 | 5.546 |
| meta_first | relaxed_order | 0.971 | 0.675 | 0.015 | 0 | 10.765 | 33.193 |
| meta_first | strict_order | 0.953 | 0.665 | 0.025 | 0 | 11.365 | 33.295 |

## N=5000 planner (HNSW vs seq scan)

| cond | ef | mode | seqscan_off | plan_kind | used_n_*_hnsw | has_sort | recall@10 |
| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: |
| raw | 40 | relaxed_order | False | hnsw_index_scan | True | False | 0.972 |
| raw | 40 | strict_order | False | hnsw_index_scan | True | False | 0.972 |
| raw | 100 | relaxed_order | False | hnsw_index_scan | True | False | 0.994 |
| raw | 100 | strict_order | False | hnsw_index_scan | True | False | 0.994 |
| raw | 200 | relaxed_order | False | hnsw_index_scan | True | False | 0.9985 |
| raw | 200 | strict_order | False | hnsw_index_scan | True | False | 0.9985 |
| raw | 400 | relaxed_order | False | seq_scan | False | True | 1.0 |
| raw | 400 | strict_order | False | seq_scan | False | True | 1.0 |
| raw | 800 | relaxed_order | False | seq_scan | False | True | 1.0 |
| raw | 800 | strict_order | False | seq_scan | False | True | 1.0 |
| meta_first | 40 | relaxed_order | False | other | False | True | 1.0 |
| meta_first | 40 | strict_order | False | other | False | True | 1.0 |
| meta_first | 100 | relaxed_order | False | other | False | True | 1.0 |
| meta_first | 100 | strict_order | False | other | False | True | 1.0 |
| meta_first | 200 | relaxed_order | False | other | False | True | 1.0 |
| meta_first | 200 | strict_order | False | other | False | True | 1.0 |
| meta_first | 400 | relaxed_order | False | other | False | True | 1.0 |
| meta_first | 400 | strict_order | False | other | False | True | 1.0 |
| meta_first | 800 | relaxed_order | False | other | False | True | 1.0 |
| meta_first | 800 | strict_order | False | other | False | True | 1.0 |
| meta_in | 40 | relaxed_order | False | other | False | True | 1.0 |
| meta_in | 40 | strict_order | False | other | False | True | 1.0 |
| meta_in | 100 | relaxed_order | False | other | False | True | 1.0 |
| meta_in | 100 | strict_order | False | other | False | True | 1.0 |
| meta_in | 200 | relaxed_order | False | other | False | True | 1.0 |
| meta_in | 200 | strict_order | False | other | False | True | 1.0 |
| meta_in | 400 | relaxed_order | False | other | False | True | 1.0 |
| meta_in | 400 | strict_order | False | other | False | True | 1.0 |
| meta_in | 800 | relaxed_order | False | other | False | True | 1.0 |
| meta_in | 800 | strict_order | False | other | False | True | 1.0 |
| raw | 400 | relaxed_order | True | hnsw_index_scan | True | False | 0.9995 |
| raw | 400 | strict_order | True | hnsw_index_scan | True | False | 0.9995 |
| raw | 800 | relaxed_order | True | hnsw_index_scan | True | False | 1.0 |
| raw | 800 | strict_order | True | hnsw_index_scan | True | False | 1.0 |

