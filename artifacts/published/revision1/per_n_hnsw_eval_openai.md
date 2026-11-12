# Per-N HNSW vs exact (W9, openai)

Generated: 2026-11-10T23:48:11Z
Questions: 200
Repeats: 3
shared_buffers: 2GB

## 1. recall@10 vs exact top-10 (raw, /10 set overlap)

### iterative_scan = relaxed_order, max_scan_tuples default 20000

| N | ef=40 | ef=100 | ef=200 | ef=400 | ef=800 |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 5000 | 0.9495 | 0.988 | 0.996 | 1.0 | 1.0 |
| 10000 | 0.926 | 0.9715 | 0.99 | 0.9975 | 1.0 |
| 15000 | 0.9225 | 0.9725 | 0.9875 | 0.9975 | 0.9995 |
| 20000 | 0.901 | 0.957 | 0.9825 | 0.996 | 0.999 |
| 25000 | 0.8965 | 0.9505 | 0.9785 | 0.9925 | 0.9985 |
| 40000 | 0.87 | 0.943 | 0.978 | 0.9935 | 0.9995 |
| 50000 | 0.854 | 0.9395 | 0.9665 | 0.981 | 0.9935 |
| 75000 | 0.8385 | 0.9155 | 0.9595 | 0.985 | 0.9945 |
| 100000 | 0.819 | 0.9135 | 0.9575 | 0.9735 | 0.986 |

### iterative_scan = strict_order, max_scan_tuples default 20000

| N | ef=40 | ef=100 | ef=200 | ef=400 | ef=800 |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 5000 | 0.9495 | 0.988 | 0.996 | 1.0 | 1.0 |
| 10000 | 0.926 | 0.9715 | 0.99 | 0.9975 | 1.0 |
| 15000 | 0.9225 | 0.9725 | 0.9875 | 0.9975 | 0.9995 |
| 20000 | 0.901 | 0.957 | 0.9825 | 0.996 | 0.999 |
| 25000 | 0.8965 | 0.9505 | 0.9785 | 0.9925 | 0.9985 |
| 40000 | 0.87 | 0.943 | 0.978 | 0.9935 | 0.9995 |
| 50000 | 0.854 | 0.9395 | 0.9665 | 0.981 | 0.9935 |
| 75000 | 0.8385 | 0.9155 | 0.9595 | 0.985 | 0.9945 |
| 100000 | 0.819 | 0.9135 | 0.9575 | 0.9735 | 0.986 |

## 2. Hit@10 drop (exact − HNSW), raw

### iterative_scan = relaxed_order

| N | ef=40 | ef=100 | ef=200 | ef=400 | ef=800 |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 5000 | 0.065 | 0.02 | 0.005 | 0.0 | 0.0 |
| 10000 | 0.075 | 0.035 | 0.025 | 0.005 | 0.0 |
| 15000 | 0.065 | 0.035 | 0.02 | 0.01 | 0.0 |
| 20000 | 0.085 | 0.05 | 0.025 | 0.005 | 0.0 |
| 25000 | 0.105 | 0.055 | 0.025 | 0.015 | 0.0 |
| 40000 | 0.08 | 0.055 | 0.03 | 0.01 | 0.0 |
| 50000 | 0.075 | 0.055 | 0.045 | 0.025 | 0.01 |
| 75000 | 0.105 | 0.065 | 0.04 | 0.02 | 0.005 |
| 100000 | 0.14 | 0.085 | 0.05 | 0.04 | 0.025 |

### iterative_scan = strict_order

| N | ef=40 | ef=100 | ef=200 | ef=400 | ef=800 |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 5000 | 0.065 | 0.02 | 0.005 | 0.0 | 0.0 |
| 10000 | 0.075 | 0.035 | 0.025 | 0.005 | 0.0 |
| 15000 | 0.065 | 0.035 | 0.02 | 0.01 | 0.0 |
| 20000 | 0.085 | 0.05 | 0.025 | 0.005 | 0.0 |
| 25000 | 0.105 | 0.055 | 0.025 | 0.015 | 0.0 |
| 40000 | 0.08 | 0.055 | 0.03 | 0.01 | 0.0 |
| 50000 | 0.075 | 0.055 | 0.045 | 0.025 | 0.01 |
| 75000 | 0.105 | 0.065 | 0.04 | 0.02 | 0.005 |
| 100000 | 0.14 | 0.085 | 0.05 | 0.04 | 0.025 |

## 3. Latency (raw, p50 / p95 ms of per-query medians over repeats)

### iterative_scan = relaxed_order

| N | ef=40 p50 | ef=100 p50 | ef=200 p50 | ef=400 p50 | ef=800 p50 | ef=40 p95 | ef=100 p95 | ef=200 p95 | ef=400 p95 | ef=800 p95 |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 5000 | 1.836 | 2.299 | 3.221 | 22.432 | 22.046 | 2.248 | 2.814 | 3.985 | 23.143 | 23.335 |
| 10000 | 1.709 | 2.372 | 4.035 | 5.031 | 40.632 | 2.211 | 3.127 | 5.5 | 6.297 | 41.731 |
| 15000 | 1.93 | 2.422 | 3.272 | 5.244 | 8.234 | 2.469 | 3.126 | 4.274 | 6.82 | 10.376 |
| 20000 | 1.871 | 2.457 | 3.82 | 5.401 | 7.879 | 2.518 | 3.172 | 5.122 | 7.158 | 10.128 |
| 25000 | 2.105 | 2.541 | 3.282 | 4.865 | 7.445 | 2.662 | 3.335 | 4.289 | 6.365 | 9.559 |
| 40000 | 1.885 | 2.942 | 3.801 | 5.578 | 8.61 | 2.362 | 3.74 | 5.1 | 7.576 | 11.685 |
| 50000 | 1.931 | 2.778 | 3.931 | 6.231 | 9.797 | 2.375 | 3.652 | 5.204 | 8.137 | 12.967 |
| 75000 | 2.073 | 2.852 | 4.078 | 6.094 | 9.749 | 2.645 | 3.692 | 5.535 | 8.12 | 12.861 |
| 100000 | 2.284 | 3.127 | 4.308 | 6.704 | 10.857 | 3.175 | 4.218 | 6.22 | 8.398 | 14.639 |

### iterative_scan = strict_order

| N | ef=40 p50 | ef=100 p50 | ef=200 p50 | ef=400 p50 | ef=800 p50 | ef=40 p95 | ef=100 p95 | ef=200 p95 | ef=400 p95 | ef=800 p95 |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 5000 | 1.829 | 2.316 | 3.242 | 22.471 | 22.107 | 2.383 | 2.806 | 4.054 | 23.296 | 23.342 |
| 10000 | 1.767 | 2.535 | 3.435 | 5.127 | 40.435 | 2.238 | 3.244 | 4.422 | 6.346 | 42.065 |
| 15000 | 1.903 | 2.338 | 3.432 | 5.177 | 8.152 | 2.47 | 3.078 | 4.577 | 6.771 | 10.096 |
| 20000 | 1.702 | 2.476 | 3.729 | 5.375 | 7.795 | 2.127 | 3.21 | 5.275 | 7.053 | 9.977 |
| 25000 | 1.951 | 2.544 | 3.176 | 4.793 | 7.495 | 2.509 | 3.404 | 4.213 | 6.332 | 9.648 |
| 40000 | 2.036 | 2.902 | 3.795 | 5.629 | 9.081 | 2.899 | 4.144 | 5.14 | 7.687 | 12.314 |
| 50000 | 1.985 | 2.777 | 4.022 | 6.224 | 9.606 | 2.488 | 3.722 | 5.235 | 8.249 | 12.688 |
| 75000 | 2.152 | 2.853 | 4.03 | 6.309 | 9.587 | 2.737 | 3.847 | 5.395 | 8.529 | 12.715 |
| 100000 | 2.25 | 3.07 | 4.382 | 6.727 | 10.607 | 3.326 | 4.274 | 6.374 | 8.558 | 14.682 |

## 4. Capacity (index / table from W8; latency = raw, ef=200, relaxed_order)

| N | rows | table_MB | hnsw_index_MB | build_s | p50_ms | p95_ms | mean_sweep_s |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 5000 | 5000 | 0.48 | 40.97 | 2.16 | 3.221 | 3.985 | 0.9674 |
| 10000 | 10000 | 0.97 | 81.93 | 4.87 | 4.035 | 5.5 | 1.1575 |
| 15000 | 15000 | 1.45 | 122.89 | 7.74 | 3.272 | 4.274 | 0.9702 |
| 20000 | 20000 | 1.93 | 163.85 | 11.07 | 3.82 | 5.122 | 1.1094 |
| 25000 | 25000 | 2.41 | 204.81 | 14.26 | 3.282 | 4.289 | 1.1291 |
| 40000 | 39999 | 3.86 | 327.68 | 25.04 | 3.801 | 5.1 | 1.093 |
| 50000 | 49999 | 4.82 | 409.6 | 30.67 | 3.931 | 5.204 | 1.0915 |
| 75000 | 74999 | 7.22 | 614.38 | 48.93 | 4.078 | 5.535 | 1.2663 |
| 100000 | 99998 | 9.63 | 819.18 | 16.86 | 4.308 | 6.22 | 1.4476 |

## Extra max_scan_tuples=100000 (N=100000, ef=200)

| cond | mode | recall@10 | hit@10 | drop | short | p50_ms | p95_ms |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| raw | relaxed_order | 0.9575 | 0.535 | 0.05 | 0 | 3.861 | 5.278 |
| raw | strict_order | 0.9575 | 0.535 | 0.05 | 0 | 3.967 | 5.342 |
| meta_first | relaxed_order | 0.9585 | 0.645 | 0.025 | 0 | 18.822 | 33.174 |
| meta_first | strict_order | 0.921 | 0.625 | 0.045 | 0 | 19.278 | 33.181 |

## N=5000 planner (HNSW vs seq scan)

| cond | ef | mode | seqscan_off | plan_kind | used_n_*_hnsw | has_sort | recall@10 |
| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: |
| raw | 40 | relaxed_order | False | hnsw_index_scan | True | False | 0.9495 |
| raw | 40 | strict_order | False | hnsw_index_scan | True | False | 0.9495 |
| raw | 100 | relaxed_order | False | hnsw_index_scan | True | False | 0.988 |
| raw | 100 | strict_order | False | hnsw_index_scan | True | False | 0.988 |
| raw | 200 | relaxed_order | False | hnsw_index_scan | True | False | 0.996 |
| raw | 200 | strict_order | False | hnsw_index_scan | True | False | 0.996 |
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
| raw | 800 | relaxed_order | True | hnsw_index_scan | True | False | 0.9995 |
| raw | 800 | strict_order | True | hnsw_index_scan | True | False | 0.9995 |

