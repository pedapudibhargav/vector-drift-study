# pgvector plan audit (port 5433)

Generated: 2026-11-10T02:06:57Z

## Server

- PostgreSQL: `PostgreSQL 16.15 (Debian 16.15-1.pgdg12+2) on aarch64-unknown-linux-gnu, compiled by gcc (Debian 12.2.0-14+deb12u1) 12.2.0, 64-bit`
- pgvector: `0.8.6`
- Settings:
  - `shared_buffers` = `2GB`
  - `work_mem` = `64MB`
  - `effective_cache_size` = `4GB`
  - `max_parallel_workers_per_gather` = `2`
  - `hnsw.ef_search` = `40`
  - `hnsw.iterative_scan` = `off`
  - `hnsw.max_scan_tuples` = `20000`
  - `hnsw.scan_mem_multiplier` = `1`

## HNSW indexes and relation sizes

| relname | bytes | pretty |
|---|---:|---|
| `document_chunks` | 60293120 | 58 MB |
| `document_chunks_titan` | 58720256 | 56 MB |
| `idx_chunks_embedding_hnsw` | 844038144 | 805 MB |
| `idx_chunks_scale_rank` | 2326528 | 2272 kB |
| `idx_chunks_source_type` | 737280 | 720 kB |
| `idx_chunks_titan_embedding_hnsw` | 819175424 | 781 MB |
| `idx_chunks_titan_scale_rank` | 2260992 | 2208 kB |
| `idx_chunks_titan_source_type` | 712704 | 696 kB |

HNSW index defs:

- `document_chunks.idx_chunks_embedding_hnsw`: `CREATE INDEX idx_chunks_embedding_hnsw ON public.document_chunks USING hnsw (embedding vector_cosine_ops) WITH (m='16', ef_construction='64')`
- `document_chunks_titan.idx_chunks_titan_embedding_hnsw`: `CREATE INDEX idx_chunks_titan_embedding_hnsw ON public.document_chunks_titan USING hnsw (embedding vector_cosine_ops) WITH (m='16', ef_construction='64')`

## Load average

- start: `{'captured_at': '2026-11-10T01:50:11Z', 'os_getloadavg_error': 'Load averages are unobtainable', 'uptime_stdout': '17:50  2 users, no load average information available', 'uptime_stderr': '', 'uptime_returncode': 0}`
- end: `{'captured_at': '2026-11-10T02:06:57Z', 'os_getloadavg_error': 'Load averages are unobtainable', 'uptime_stdout': '18:06  2 users, no load average information available', 'uptime_stderr': '', 'uptime_returncode': 0}`

Query shape matches `eval_scale_raw`:
`SET hnsw.ef_search`; `SET hnsw.iterative_scan = relaxed_order`;
`SELECT doc_id, 1 - (embedding <=> $vec::vector) AS score FROM <table> WHERE embedding IS NOT NULL AND scale_rank IS NOT NULL AND scale_rank < $N [AND source_type = $st] ORDER BY embedding <=> $vec::vector LIMIT 10`.

Buffers are the **root Plan node** Shared Hit/Read Blocks (PostgreSQL 16 JSON EXPLAIN includes child buffers there). Example plans have vector literals replaced with `[VECTOR]`.

## Per-cell summary

| pass | table | cond | scale | ef | n | frac_hnsw | frac_seq | frac_btree | frac_sort | median_ms | p95_ms | median_read | n_lt_10 |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| forward | `document_chunks` | raw | 5000 | 200 | 200 | 0.000 | 0.000 | 1.000 | 1.000 | 25.129 | 27.530 | 0.000 | 0 |
| forward | `document_chunks` | raw | 5000 | 400 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 27.386 | 29.085 | 0.000 | 0 |
| forward | `document_chunks` | raw | 5000 | 800 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 25.195 | 27.936 | 0.000 | 0 |
| forward | `document_chunks` | raw | 10000 | 200 | 200 | 0.000 | 0.000 | 1.000 | 1.000 | 48.361 | 53.163 | 0.000 | 0 |
| forward | `document_chunks` | raw | 10000 | 400 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 48.419 | 50.041 | 0.000 | 0 |
| forward | `document_chunks` | raw | 10000 | 800 | 40 | 1.000 | 0.000 | 0.000 | 0.000 | 54.784 | 454.3 | 1312.5 | 0 |
| forward | `document_chunks` | raw | 15000 | 200 | 200 | 0.000 | 0.000 | 1.000 | 1.000 | 69.633 | 75.587 | 0.000 | 0 |
| forward | `document_chunks` | raw | 15000 | 400 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 69.180 | 74.884 | 0.000 | 0 |
| forward | `document_chunks` | raw | 15000 | 800 | 40 | 1.000 | 0.000 | 0.000 | 0.000 | 8.184 | 11.296 | 0.000 | 0 |
| forward | `document_chunks` | raw | 20000 | 200 | 200 | 0.000 | 0.000 | 1.000 | 1.000 | 92.675 | 97.187 | 0.000 | 0 |
| forward | `document_chunks` | raw | 20000 | 400 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 93.625 | 105.7 | 0.000 | 0 |
| forward | `document_chunks` | raw | 20000 | 800 | 40 | 1.000 | 0.000 | 0.000 | 0.000 | 8.206 | 11.677 | 0.000 | 0 |
| forward | `document_chunks` | raw | 25000 | 200 | 200 | 0.000 | 0.000 | 1.000 | 1.000 | 113.3 | 117.5 | 0.000 | 0 |
| forward | `document_chunks` | raw | 25000 | 400 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 113.2 | 115.4 | 0.000 | 0 |
| forward | `document_chunks` | raw | 25000 | 800 | 40 | 1.000 | 0.000 | 0.000 | 0.000 | 8.014 | 10.979 | 0.000 | 0 |
| forward | `document_chunks` | raw | 40000 | 200 | 200 | 0.000 | 1.000 | 0.000 | 1.000 | 89.726 | 96.713 | 0.000 | 0 |
| forward | `document_chunks` | raw | 40000 | 400 | 40 | 0.000 | 1.000 | 0.000 | 1.000 | 90.787 | 115.6 | 0.000 | 0 |
| forward | `document_chunks` | raw | 40000 | 800 | 40 | 1.000 | 0.000 | 0.000 | 0.000 | 14.143 | 30.173 | 0.000 | 0 |
| forward | `document_chunks` | raw | 50000 | 200 | 200 | 0.000 | 1.000 | 0.000 | 1.000 | 110.0 | 124.2 | 0.000 | 0 |
| forward | `document_chunks` | raw | 50000 | 400 | 40 | 0.000 | 1.000 | 0.000 | 1.000 | 109.7 | 114.6 | 0.000 | 0 |
| forward | `document_chunks` | raw | 50000 | 800 | 40 | 1.000 | 0.000 | 0.000 | 0.000 | 8.290 | 11.312 | 0.000 | 0 |
| forward | `document_chunks` | raw | 75000 | 200 | 200 | 1.000 | 0.000 | 0.000 | 0.000 | 4.076 | 15.613 | 20.500 | 0 |
| forward | `document_chunks` | raw | 75000 | 400 | 40 | 0.000 | 1.000 | 0.000 | 1.000 | 154.2 | 166.3 | 0.000 | 0 |
| forward | `document_chunks` | raw | 75000 | 800 | 40 | 1.000 | 0.000 | 0.000 | 0.000 | 12.456 | 22.430 | 0.000 | 0 |
| forward | `document_chunks` | raw | 100000 | 200 | 200 | 1.000 | 0.000 | 0.000 | 0.000 | 2.990 | 4.440 | 2.000 | 0 |
| forward | `document_chunks` | raw | 100000 | 400 | 40 | 0.000 | 1.000 | 0.000 | 1.000 | 203.7 | 232.9 | 0.000 | 0 |
| forward | `document_chunks` | raw | 100000 | 800 | 40 | 1.000 | 0.000 | 0.000 | 0.000 | 8.070 | 11.832 | 0.000 | 0 |
| forward | `document_chunks` | meta | 5000 | 200 | 200 | 0.000 | 0.000 | 1.000 | 1.000 | 4.046 | 4.764 | 0.000 | 0 |
| forward | `document_chunks` | meta | 5000 | 400 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 4.089 | 4.629 | 0.000 | 0 |
| forward | `document_chunks` | meta | 5000 | 800 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 4.104 | 4.557 | 0.000 | 0 |
| forward | `document_chunks` | meta | 10000 | 200 | 200 | 0.000 | 0.000 | 1.000 | 1.000 | 7.546 | 8.360 | 0.000 | 0 |
| forward | `document_chunks` | meta | 10000 | 400 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 8.081 | 10.363 | 0.000 | 0 |
| forward | `document_chunks` | meta | 10000 | 800 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 7.588 | 8.057 | 0.000 | 0 |
| forward | `document_chunks` | meta | 15000 | 200 | 200 | 0.000 | 0.000 | 1.000 | 1.000 | 10.838 | 11.895 | 0.000 | 0 |
| forward | `document_chunks` | meta | 15000 | 400 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 10.847 | 11.472 | 0.000 | 0 |
| forward | `document_chunks` | meta | 15000 | 800 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 10.869 | 15.081 | 0.000 | 0 |
| forward | `document_chunks` | meta | 20000 | 200 | 200 | 0.000 | 0.000 | 1.000 | 1.000 | 13.938 | 15.913 | 0.000 | 0 |
| forward | `document_chunks` | meta | 20000 | 400 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 13.974 | 14.904 | 0.000 | 0 |
| forward | `document_chunks` | meta | 20000 | 800 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 14.180 | 15.116 | 0.000 | 0 |
| forward | `document_chunks` | meta | 25000 | 200 | 200 | 0.000 | 0.000 | 1.000 | 1.000 | 17.035 | 18.126 | 0.000 | 0 |
| forward | `document_chunks` | meta | 25000 | 400 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 16.656 | 17.680 | 0.000 | 0 |
| forward | `document_chunks` | meta | 25000 | 800 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 16.953 | 18.219 | 0.000 | 0 |
| forward | `document_chunks` | meta | 40000 | 200 | 200 | 0.000 | 0.000 | 1.000 | 1.000 | 28.852 | 35.257 | 0.000 | 0 |
| forward | `document_chunks` | meta | 40000 | 400 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 27.020 | 32.573 | 0.000 | 0 |
| forward | `document_chunks` | meta | 40000 | 800 | 40 | 0.175 | 0.000 | 0.825 | 0.825 | 25.796 | 30.217 | 0.000 | 0 |
| forward | `document_chunks` | meta | 50000 | 200 | 200 | 0.000 | 0.000 | 1.000 | 1.000 | 35.431 | 41.333 | 0.000 | 0 |
| forward | `document_chunks` | meta | 50000 | 400 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 34.492 | 37.982 | 0.000 | 0 |
| forward | `document_chunks` | meta | 50000 | 800 | 40 | 0.475 | 0.000 | 0.525 | 0.525 | 28.084 | 35.409 | 0.000 | 0 |
| forward | `document_chunks` | meta | 75000 | 200 | 200 | 0.000 | 0.000 | 1.000 | 1.000 | 51.626 | 61.099 | 0.000 | 0 |
| forward | `document_chunks` | meta | 75000 | 400 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 53.192 | 64.540 | 0.000 | 0 |
| forward | `document_chunks` | meta | 75000 | 800 | 40 | 0.550 | 0.000 | 0.450 | 0.450 | 16.556 | 47.151 | 0.000 | 0 |
| forward | `document_chunks` | meta | 100000 | 200 | 200 | 0.000 | 0.000 | 1.000 | 1.000 | 56.159 | 87.436 | 0.000 | 0 |
| forward | `document_chunks` | meta | 100000 | 400 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 58.707 | 83.583 | 0.000 | 0 |
| forward | `document_chunks` | meta | 100000 | 800 | 40 | 0.650 | 0.000 | 0.350 | 0.350 | 10.886 | 35.125 | 0.000 | 0 |
| forward | `document_chunks_titan` | raw | 5000 | 200 | 200 | 0.000 | 0.000 | 1.000 | 1.000 | 17.907 | 19.722 | 0.000 | 0 |
| forward | `document_chunks_titan` | raw | 5000 | 400 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 17.669 | 18.374 | 0.000 | 0 |
| forward | `document_chunks_titan` | raw | 5000 | 800 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 17.764 | 19.943 | 0.000 | 0 |
| forward | `document_chunks_titan` | raw | 10000 | 200 | 200 | 0.000 | 0.000 | 1.000 | 1.000 | 35.683 | 40.461 | 0.000 | 0 |
| forward | `document_chunks_titan` | raw | 10000 | 400 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 35.995 | 36.748 | 0.000 | 0 |
| forward | `document_chunks_titan` | raw | 10000 | 800 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 35.826 | 39.921 | 0.000 | 0 |
| forward | `document_chunks_titan` | raw | 15000 | 200 | 200 | 0.000 | 0.000 | 1.000 | 1.000 | 53.254 | 55.536 | 0.000 | 0 |
| forward | `document_chunks_titan` | raw | 15000 | 400 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 52.587 | 54.074 | 0.000 | 0 |
| forward | `document_chunks_titan` | raw | 15000 | 800 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 53.159 | 61.611 | 0.000 | 0 |
| forward | `document_chunks_titan` | raw | 20000 | 200 | 200 | 0.000 | 0.000 | 1.000 | 1.000 | 72.962 | 92.229 | 0.000 | 0 |
| forward | `document_chunks_titan` | raw | 20000 | 400 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 71.794 | 74.888 | 0.000 | 0 |
| forward | `document_chunks_titan` | raw | 20000 | 800 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 73.292 | 86.136 | 0.000 | 0 |
| forward | `document_chunks_titan` | raw | 25000 | 200 | 200 | 0.000 | 0.000 | 1.000 | 1.000 | 90.374 | 95.605 | 0.000 | 0 |
| forward | `document_chunks_titan` | raw | 25000 | 400 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 91.807 | 125.4 | 0.000 | 0 |
| forward | `document_chunks_titan` | raw | 25000 | 800 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 90.829 | 103.9 | 0.000 | 0 |
| forward | `document_chunks_titan` | raw | 40000 | 200 | 200 | 0.000 | 0.000 | 1.000 | 1.000 | 144.4 | 173.5 | 0.000 | 0 |
| forward | `document_chunks_titan` | raw | 40000 | 400 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 142.8 | 160.7 | 0.000 | 0 |
| forward | `document_chunks_titan` | raw | 40000 | 800 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 148.6 | 152.5 | 0.000 | 0 |
| forward | `document_chunks_titan` | raw | 50000 | 200 | 200 | 0.000 | 0.000 | 1.000 | 1.000 | 183.0 | 225.3 | 0.000 | 0 |
| forward | `document_chunks_titan` | raw | 50000 | 400 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 179.5 | 209.7 | 0.000 | 0 |
| forward | `document_chunks_titan` | raw | 50000 | 800 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 179.7 | 206.6 | 0.000 | 0 |
| forward | `document_chunks_titan` | raw | 75000 | 200 | 200 | 0.000 | 0.000 | 1.000 | 1.000 | 120.7 | 158.6 | 0.000 | 0 |
| forward | `document_chunks_titan` | raw | 75000 | 400 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 120.6 | 165.0 | 0.000 | 0 |
| forward | `document_chunks_titan` | raw | 75000 | 800 | 40 | 1.000 | 0.000 | 0.000 | 0.000 | 126.6 | 559.9 | 1448.5 | 0 |
| forward | `document_chunks_titan` | raw | 100000 | 200 | 200 | 1.000 | 0.000 | 0.000 | 0.000 | 5.473 | 19.182 | 28.000 | 0 |
| forward | `document_chunks_titan` | raw | 100000 | 400 | 40 | 0.000 | 1.000 | 0.000 | 1.000 | 162.7 | 191.9 | 0.000 | 0 |
| forward | `document_chunks_titan` | raw | 100000 | 800 | 40 | 1.000 | 0.000 | 0.000 | 0.000 | 12.184 | 20.902 | 0.000 | 0 |
| forward | `document_chunks_titan` | meta | 5000 | 200 | 200 | 0.000 | 0.000 | 1.000 | 1.000 | 3.623 | 8.554 | 0.000 | 0 |
| forward | `document_chunks_titan` | meta | 5000 | 400 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 3.479 | 4.358 | 0.000 | 0 |
| forward | `document_chunks_titan` | meta | 5000 | 800 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 3.058 | 4.570 | 0.000 | 0 |
| forward | `document_chunks_titan` | meta | 10000 | 200 | 200 | 0.000 | 0.000 | 1.000 | 1.000 | 6.604 | 8.067 | 0.000 | 0 |
| forward | `document_chunks_titan` | meta | 10000 | 400 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 6.497 | 7.118 | 0.000 | 0 |
| forward | `document_chunks_titan` | meta | 10000 | 800 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 6.534 | 7.150 | 0.000 | 0 |
| forward | `document_chunks_titan` | meta | 15000 | 200 | 200 | 0.000 | 0.000 | 1.000 | 1.000 | 9.983 | 11.587 | 0.000 | 0 |
| forward | `document_chunks_titan` | meta | 15000 | 400 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 9.857 | 10.473 | 0.000 | 0 |
| forward | `document_chunks_titan` | meta | 15000 | 800 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 9.837 | 10.423 | 0.000 | 0 |
| forward | `document_chunks_titan` | meta | 20000 | 200 | 200 | 0.000 | 0.000 | 1.000 | 1.000 | 13.458 | 17.250 | 0.000 | 0 |
| forward | `document_chunks_titan` | meta | 20000 | 400 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 13.262 | 14.037 | 0.000 | 0 |
| forward | `document_chunks_titan` | meta | 20000 | 800 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 13.142 | 14.014 | 0.000 | 0 |
| forward | `document_chunks_titan` | meta | 25000 | 200 | 200 | 0.000 | 0.000 | 1.000 | 1.000 | 16.660 | 19.650 | 0.000 | 0 |
| forward | `document_chunks_titan` | meta | 25000 | 400 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 16.674 | 17.329 | 0.000 | 0 |
| forward | `document_chunks_titan` | meta | 25000 | 800 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 16.797 | 17.669 | 0.000 | 0 |
| forward | `document_chunks_titan` | meta | 40000 | 200 | 200 | 0.000 | 0.000 | 1.000 | 1.000 | 26.992 | 34.137 | 0.000 | 0 |
| forward | `document_chunks_titan` | meta | 40000 | 400 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 26.311 | 26.874 | 0.000 | 0 |
| forward | `document_chunks_titan` | meta | 40000 | 800 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 27.287 | 31.789 | 0.000 | 0 |
| forward | `document_chunks_titan` | meta | 50000 | 200 | 200 | 0.000 | 0.000 | 1.000 | 1.000 | 33.729 | 43.888 | 0.000 | 0 |
| forward | `document_chunks_titan` | meta | 50000 | 400 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 34.284 | 43.968 | 0.000 | 0 |
| forward | `document_chunks_titan` | meta | 50000 | 800 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 33.641 | 48.222 | 0.000 | 0 |
| forward | `document_chunks_titan` | meta | 75000 | 200 | 200 | 0.000 | 0.000 | 1.000 | 1.000 | 43.646 | 54.620 | 0.000 | 0 |
| forward | `document_chunks_titan` | meta | 75000 | 400 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 43.210 | 46.835 | 0.000 | 0 |
| forward | `document_chunks_titan` | meta | 75000 | 800 | 40 | 0.550 | 0.000 | 0.450 | 0.450 | 24.365 | 37.862 | 0.000 | 0 |
| forward | `document_chunks_titan` | meta | 100000 | 200 | 200 | 0.000 | 0.000 | 1.000 | 1.000 | 46.796 | 75.190 | 0.000 | 0 |
| forward | `document_chunks_titan` | meta | 100000 | 400 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 47.492 | 66.209 | 0.000 | 0 |
| forward | `document_chunks_titan` | meta | 100000 | 800 | 40 | 0.650 | 0.000 | 0.350 | 0.350 | 12.073 | 31.848 | 0.000 | 0 |
| reverse | `document_chunks` | raw | 100000 | 200 | 200 | 1.000 | 0.000 | 0.000 | 0.000 | 6.323 | 23.346 | 443.5 | 0 |
| reverse | `document_chunks` | raw | 100000 | 400 | 40 | 0.000 | 1.000 | 0.000 | 1.000 | 187.3 | 212.0 | 0.000 | 0 |
| reverse | `document_chunks` | raw | 100000 | 800 | 40 | 1.000 | 0.000 | 0.000 | 0.000 | 11.140 | 18.851 | 263.0 | 0 |
| reverse | `document_chunks` | raw | 75000 | 200 | 200 | 1.000 | 0.000 | 0.000 | 0.000 | 2.654 | 4.454 | 0.000 | 0 |
| reverse | `document_chunks` | raw | 75000 | 400 | 40 | 0.000 | 1.000 | 0.000 | 1.000 | 147.3 | 201.3 | 0.000 | 0 |
| reverse | `document_chunks` | raw | 75000 | 800 | 40 | 1.000 | 0.000 | 0.000 | 0.000 | 13.038 | 43.542 | 0.000 | 0 |
| reverse | `document_chunks` | raw | 50000 | 200 | 200 | 0.000 | 1.000 | 0.000 | 1.000 | 104.4 | 135.6 | 0.000 | 0 |
| reverse | `document_chunks` | raw | 50000 | 400 | 40 | 0.000 | 1.000 | 0.000 | 1.000 | 104.2 | 113.9 | 0.000 | 0 |
| reverse | `document_chunks` | raw | 50000 | 800 | 40 | 1.000 | 0.000 | 0.000 | 0.000 | 13.512 | 28.569 | 0.000 | 0 |
| reverse | `document_chunks` | raw | 40000 | 200 | 200 | 0.000 | 1.000 | 0.000 | 1.000 | 86.487 | 102.2 | 0.000 | 0 |
| reverse | `document_chunks` | raw | 40000 | 400 | 40 | 0.000 | 1.000 | 0.000 | 1.000 | 86.712 | 90.242 | 0.000 | 0 |
| reverse | `document_chunks` | raw | 40000 | 800 | 40 | 1.000 | 0.000 | 0.000 | 0.000 | 12.427 | 32.136 | 0.000 | 0 |
| reverse | `document_chunks` | raw | 25000 | 200 | 200 | 0.000 | 0.000 | 1.000 | 1.000 | 115.7 | 138.4 | 0.000 | 0 |
| reverse | `document_chunks` | raw | 25000 | 400 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 118.9 | 132.7 | 0.000 | 0 |
| reverse | `document_chunks` | raw | 25000 | 800 | 40 | 1.000 | 0.000 | 0.000 | 0.000 | 15.256 | 47.432 | 0.000 | 0 |
| reverse | `document_chunks` | raw | 20000 | 200 | 200 | 0.000 | 0.000 | 1.000 | 1.000 | 91.313 | 100.1 | 0.000 | 0 |
| reverse | `document_chunks` | raw | 20000 | 400 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 90.917 | 95.151 | 0.000 | 0 |
| reverse | `document_chunks` | raw | 20000 | 800 | 40 | 1.000 | 0.000 | 0.000 | 0.000 | 7.780 | 11.924 | 0.000 | 0 |
| reverse | `document_chunks` | raw | 15000 | 200 | 200 | 0.000 | 0.000 | 1.000 | 1.000 | 68.273 | 73.867 | 0.000 | 0 |
| reverse | `document_chunks` | raw | 15000 | 400 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 68.144 | 72.617 | 0.000 | 0 |
| reverse | `document_chunks` | raw | 15000 | 800 | 40 | 1.000 | 0.000 | 0.000 | 0.000 | 9.450 | 25.873 | 0.000 | 0 |
| reverse | `document_chunks` | raw | 10000 | 200 | 200 | 0.000 | 0.000 | 1.000 | 1.000 | 46.213 | 52.657 | 0.000 | 0 |
| reverse | `document_chunks` | raw | 10000 | 400 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 50.370 | 60.667 | 0.000 | 0 |
| reverse | `document_chunks` | raw | 10000 | 800 | 40 | 1.000 | 0.000 | 0.000 | 0.000 | 9.494 | 14.492 | 0.000 | 0 |
| reverse | `document_chunks` | raw | 5000 | 200 | 200 | 0.000 | 0.000 | 1.000 | 1.000 | 26.130 | 27.484 | 0.000 | 0 |
| reverse | `document_chunks` | raw | 5000 | 400 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 24.198 | 25.716 | 0.000 | 0 |
| reverse | `document_chunks` | raw | 5000 | 800 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 24.024 | 25.046 | 0.000 | 0 |
| reverse | `document_chunks` | meta | 100000 | 200 | 200 | 0.000 | 0.000 | 1.000 | 1.000 | 53.872 | 86.676 | 0.000 | 0 |
| reverse | `document_chunks` | meta | 100000 | 400 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 58.037 | 84.754 | 0.000 | 0 |
| reverse | `document_chunks` | meta | 100000 | 800 | 40 | 0.650 | 0.000 | 0.350 | 0.350 | 9.739 | 35.081 | 0.000 | 0 |
| reverse | `document_chunks` | meta | 75000 | 200 | 200 | 0.000 | 0.000 | 1.000 | 1.000 | 48.871 | 57.192 | 0.000 | 0 |
| reverse | `document_chunks` | meta | 75000 | 400 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 50.056 | 53.691 | 0.000 | 0 |
| reverse | `document_chunks` | meta | 75000 | 800 | 40 | 0.550 | 0.000 | 0.450 | 0.450 | 10.713 | 43.217 | 0.000 | 0 |
| reverse | `document_chunks` | meta | 50000 | 200 | 200 | 0.000 | 0.000 | 1.000 | 1.000 | 32.136 | 36.639 | 0.000 | 0 |
| reverse | `document_chunks` | meta | 50000 | 400 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 34.166 | 37.254 | 0.000 | 0 |
| reverse | `document_chunks` | meta | 50000 | 800 | 40 | 0.475 | 0.000 | 0.525 | 0.525 | 26.410 | 32.260 | 0.000 | 0 |
| reverse | `document_chunks` | meta | 40000 | 200 | 200 | 0.000 | 0.000 | 1.000 | 1.000 | 25.971 | 30.869 | 0.000 | 0 |
| reverse | `document_chunks` | meta | 40000 | 400 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 27.130 | 31.273 | 0.000 | 0 |
| reverse | `document_chunks` | meta | 40000 | 800 | 40 | 0.175 | 0.000 | 0.825 | 0.825 | 24.933 | 29.488 | 0.000 | 0 |
| reverse | `document_chunks` | meta | 25000 | 200 | 200 | 0.000 | 0.000 | 1.000 | 1.000 | 16.337 | 17.654 | 0.000 | 0 |
| reverse | `document_chunks` | meta | 25000 | 400 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 16.614 | 17.579 | 0.000 | 0 |
| reverse | `document_chunks` | meta | 25000 | 800 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 16.154 | 17.138 | 0.000 | 0 |
| reverse | `document_chunks` | meta | 20000 | 200 | 200 | 0.000 | 0.000 | 1.000 | 1.000 | 13.470 | 15.093 | 0.000 | 0 |
| reverse | `document_chunks` | meta | 20000 | 400 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 13.309 | 13.929 | 0.000 | 0 |
| reverse | `document_chunks` | meta | 20000 | 800 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 13.886 | 16.651 | 0.000 | 0 |
| reverse | `document_chunks` | meta | 15000 | 200 | 200 | 0.000 | 0.000 | 1.000 | 1.000 | 10.305 | 11.204 | 0.000 | 0 |
| reverse | `document_chunks` | meta | 15000 | 400 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 10.430 | 11.337 | 0.000 | 0 |
| reverse | `document_chunks` | meta | 15000 | 800 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 10.419 | 11.181 | 0.000 | 0 |
| reverse | `document_chunks` | meta | 10000 | 200 | 200 | 0.000 | 0.000 | 1.000 | 1.000 | 7.395 | 8.426 | 0.000 | 0 |
| reverse | `document_chunks` | meta | 10000 | 400 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 7.257 | 7.900 | 0.000 | 0 |
| reverse | `document_chunks` | meta | 10000 | 800 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 7.252 | 8.447 | 0.000 | 0 |
| reverse | `document_chunks` | meta | 5000 | 200 | 200 | 0.000 | 0.000 | 1.000 | 1.000 | 3.875 | 4.574 | 0.000 | 0 |
| reverse | `document_chunks` | meta | 5000 | 400 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 4.010 | 4.496 | 0.000 | 0 |
| reverse | `document_chunks` | meta | 5000 | 800 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 3.954 | 4.534 | 0.000 | 0 |
| reverse | `document_chunks_titan` | raw | 100000 | 200 | 200 | 1.000 | 0.000 | 0.000 | 0.000 | 7.149 | 56.021 | 435.5 | 0 |
| reverse | `document_chunks_titan` | raw | 100000 | 400 | 40 | 0.000 | 1.000 | 0.000 | 1.000 | 163.2 | 183.8 | 0.000 | 0 |
| reverse | `document_chunks_titan` | raw | 100000 | 800 | 40 | 1.000 | 0.000 | 0.000 | 0.000 | 9.084 | 13.631 | 102.5 | 0 |
| reverse | `document_chunks_titan` | raw | 75000 | 200 | 200 | 0.000 | 0.000 | 1.000 | 1.000 | 114.9 | 119.0 | 0.000 | 0 |
| reverse | `document_chunks_titan` | raw | 75000 | 400 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 106.9 | 115.9 | 0.000 | 0 |
| reverse | `document_chunks_titan` | raw | 75000 | 800 | 40 | 1.000 | 0.000 | 0.000 | 0.000 | 7.600 | 10.549 | 0.000 | 0 |
| reverse | `document_chunks_titan` | raw | 50000 | 200 | 200 | 0.000 | 0.000 | 1.000 | 1.000 | 180.2 | 271.6 | 0.000 | 0 |
| reverse | `document_chunks_titan` | raw | 50000 | 400 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 178.2 | 190.0 | 0.000 | 0 |
| reverse | `document_chunks_titan` | raw | 50000 | 800 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 179.2 | 222.4 | 0.000 | 0 |
| reverse | `document_chunks_titan` | raw | 40000 | 200 | 200 | 0.000 | 0.000 | 1.000 | 1.000 | 143.5 | 152.1 | 0.000 | 0 |
| reverse | `document_chunks_titan` | raw | 40000 | 400 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 140.6 | 142.4 | 0.000 | 0 |
| reverse | `document_chunks_titan` | raw | 40000 | 800 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 140.7 | 143.9 | 0.000 | 0 |
| reverse | `document_chunks_titan` | raw | 25000 | 200 | 200 | 0.000 | 0.000 | 1.000 | 1.000 | 87.923 | 92.291 | 0.000 | 0 |
| reverse | `document_chunks_titan` | raw | 25000 | 400 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 87.661 | 89.898 | 0.000 | 0 |
| reverse | `document_chunks_titan` | raw | 25000 | 800 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 87.612 | 90.102 | 0.000 | 0 |
| reverse | `document_chunks_titan` | raw | 20000 | 200 | 200 | 0.000 | 0.000 | 1.000 | 1.000 | 70.877 | 79.251 | 0.000 | 0 |
| reverse | `document_chunks_titan` | raw | 20000 | 400 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 70.290 | 73.201 | 0.000 | 0 |
| reverse | `document_chunks_titan` | raw | 20000 | 800 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 70.332 | 76.062 | 0.000 | 0 |
| reverse | `document_chunks_titan` | raw | 15000 | 200 | 200 | 0.000 | 0.000 | 1.000 | 1.000 | 52.514 | 55.197 | 0.000 | 0 |
| reverse | `document_chunks_titan` | raw | 15000 | 400 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 52.839 | 70.011 | 0.000 | 0 |
| reverse | `document_chunks_titan` | raw | 15000 | 800 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 52.397 | 53.067 | 0.000 | 0 |
| reverse | `document_chunks_titan` | raw | 10000 | 200 | 200 | 0.000 | 0.000 | 1.000 | 1.000 | 34.925 | 36.635 | 0.000 | 0 |
| reverse | `document_chunks_titan` | raw | 10000 | 400 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 35.966 | 36.610 | 0.000 | 0 |
| reverse | `document_chunks_titan` | raw | 10000 | 800 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 35.136 | 41.896 | 0.000 | 0 |
| reverse | `document_chunks_titan` | raw | 5000 | 200 | 200 | 0.000 | 0.000 | 1.000 | 1.000 | 17.512 | 18.521 | 0.000 | 0 |
| reverse | `document_chunks_titan` | raw | 5000 | 400 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 18.250 | 36.309 | 0.000 | 0 |
| reverse | `document_chunks_titan` | raw | 5000 | 800 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 17.982 | 19.955 | 0.000 | 0 |
| reverse | `document_chunks_titan` | meta | 100000 | 200 | 200 | 0.000 | 0.000 | 1.000 | 1.000 | 45.919 | 71.106 | 0.000 | 0 |
| reverse | `document_chunks_titan` | meta | 100000 | 400 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 48.060 | 64.599 | 0.000 | 0 |
| reverse | `document_chunks_titan` | meta | 100000 | 800 | 40 | 0.650 | 0.000 | 0.350 | 0.350 | 24.297 | 44.741 | 0.000 | 0 |
| reverse | `document_chunks_titan` | meta | 75000 | 200 | 200 | 0.000 | 0.000 | 1.000 | 1.000 | 44.020 | 62.137 | 0.000 | 0 |
| reverse | `document_chunks_titan` | meta | 75000 | 400 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 44.023 | 47.245 | 0.000 | 0 |
| reverse | `document_chunks_titan` | meta | 75000 | 800 | 40 | 0.550 | 0.000 | 0.450 | 0.450 | 13.381 | 38.687 | 0.000 | 0 |
| reverse | `document_chunks_titan` | meta | 50000 | 200 | 200 | 0.000 | 0.000 | 1.000 | 1.000 | 32.758 | 35.407 | 0.000 | 0 |
| reverse | `document_chunks_titan` | meta | 50000 | 400 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 32.398 | 33.214 | 0.000 | 0 |
| reverse | `document_chunks_titan` | meta | 50000 | 800 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 32.746 | 34.736 | 0.000 | 0 |
| reverse | `document_chunks_titan` | meta | 40000 | 200 | 200 | 0.000 | 0.000 | 1.000 | 1.000 | 26.061 | 28.140 | 0.000 | 0 |
| reverse | `document_chunks_titan` | meta | 40000 | 400 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 25.973 | 27.042 | 0.000 | 0 |
| reverse | `document_chunks_titan` | meta | 40000 | 800 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 25.971 | 28.027 | 0.000 | 0 |
| reverse | `document_chunks_titan` | meta | 25000 | 200 | 200 | 0.000 | 0.000 | 1.000 | 1.000 | 16.294 | 17.102 | 0.000 | 0 |
| reverse | `document_chunks_titan` | meta | 25000 | 400 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 16.355 | 17.114 | 0.000 | 0 |
| reverse | `document_chunks_titan` | meta | 25000 | 800 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 16.371 | 19.235 | 0.000 | 0 |
| reverse | `document_chunks_titan` | meta | 20000 | 200 | 200 | 0.000 | 0.000 | 1.000 | 1.000 | 13.124 | 16.146 | 0.000 | 0 |
| reverse | `document_chunks_titan` | meta | 20000 | 400 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 13.210 | 13.713 | 0.000 | 0 |
| reverse | `document_chunks_titan` | meta | 20000 | 800 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 13.073 | 13.618 | 0.000 | 0 |
| reverse | `document_chunks_titan` | meta | 15000 | 200 | 200 | 0.000 | 0.000 | 1.000 | 1.000 | 9.906 | 11.092 | 0.000 | 0 |
| reverse | `document_chunks_titan` | meta | 15000 | 400 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 9.960 | 10.860 | 0.000 | 0 |
| reverse | `document_chunks_titan` | meta | 15000 | 800 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 10.349 | 15.764 | 0.000 | 0 |
| reverse | `document_chunks_titan` | meta | 10000 | 200 | 200 | 0.000 | 0.000 | 1.000 | 1.000 | 7.526 | 15.378 | 0.000 | 0 |
| reverse | `document_chunks_titan` | meta | 10000 | 400 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 6.747 | 7.866 | 0.000 | 0 |
| reverse | `document_chunks_titan` | meta | 10000 | 800 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 6.618 | 7.378 | 0.000 | 0 |
| reverse | `document_chunks_titan` | meta | 5000 | 200 | 200 | 0.000 | 0.000 | 1.000 | 1.000 | 3.349 | 5.347 | 0.000 | 0 |
| reverse | `document_chunks_titan` | meta | 5000 | 400 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 3.484 | 4.740 | 0.000 | 0 |
| reverse | `document_chunks_titan` | meta | 5000 | 800 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 3.366 | 4.432 | 0.000 | 0 |

## Did this configuration use the HNSW index?

Values are fractions of queries in that cell. This is a planner audit, not a recall result.

- `forward` `document_chunks` `meta` ef=200 frac_hnsw by scale: N=5000:0.000, N=10000:0.000, N=15000:0.000, N=20000:0.000, N=25000:0.000, N=40000:0.000, N=50000:0.000, N=75000:0.000, N=100000:0.000
- `forward` `document_chunks` `meta` ef=400 frac_hnsw by scale: N=5000:0.000, N=10000:0.000, N=15000:0.000, N=20000:0.000, N=25000:0.000, N=40000:0.000, N=50000:0.000, N=75000:0.000, N=100000:0.000
- `forward` `document_chunks` `meta` ef=800 frac_hnsw by scale: N=5000:0.000, N=10000:0.000, N=15000:0.000, N=20000:0.000, N=25000:0.000, N=40000:0.175, N=50000:0.475, N=75000:0.550, N=100000:0.650
- `forward` `document_chunks` `raw` ef=200 frac_hnsw by scale: N=5000:0.000, N=10000:0.000, N=15000:0.000, N=20000:0.000, N=25000:0.000, N=40000:0.000, N=50000:0.000, N=75000:1.000, N=100000:1.000
- `forward` `document_chunks` `raw` ef=400 frac_hnsw by scale: N=5000:0.000, N=10000:0.000, N=15000:0.000, N=20000:0.000, N=25000:0.000, N=40000:0.000, N=50000:0.000, N=75000:0.000, N=100000:0.000
- `forward` `document_chunks` `raw` ef=800 frac_hnsw by scale: N=5000:0.000, N=10000:1.000, N=15000:1.000, N=20000:1.000, N=25000:1.000, N=40000:1.000, N=50000:1.000, N=75000:1.000, N=100000:1.000
- `forward` `document_chunks_titan` `meta` ef=200 frac_hnsw by scale: N=5000:0.000, N=10000:0.000, N=15000:0.000, N=20000:0.000, N=25000:0.000, N=40000:0.000, N=50000:0.000, N=75000:0.000, N=100000:0.000
- `forward` `document_chunks_titan` `meta` ef=400 frac_hnsw by scale: N=5000:0.000, N=10000:0.000, N=15000:0.000, N=20000:0.000, N=25000:0.000, N=40000:0.000, N=50000:0.000, N=75000:0.000, N=100000:0.000
- `forward` `document_chunks_titan` `meta` ef=800 frac_hnsw by scale: N=5000:0.000, N=10000:0.000, N=15000:0.000, N=20000:0.000, N=25000:0.000, N=40000:0.000, N=50000:0.000, N=75000:0.550, N=100000:0.650
- `forward` `document_chunks_titan` `raw` ef=200 frac_hnsw by scale: N=5000:0.000, N=10000:0.000, N=15000:0.000, N=20000:0.000, N=25000:0.000, N=40000:0.000, N=50000:0.000, N=75000:0.000, N=100000:1.000
- `forward` `document_chunks_titan` `raw` ef=400 frac_hnsw by scale: N=5000:0.000, N=10000:0.000, N=15000:0.000, N=20000:0.000, N=25000:0.000, N=40000:0.000, N=50000:0.000, N=75000:0.000, N=100000:0.000
- `forward` `document_chunks_titan` `raw` ef=800 frac_hnsw by scale: N=5000:0.000, N=10000:0.000, N=15000:0.000, N=20000:0.000, N=25000:0.000, N=40000:0.000, N=50000:0.000, N=75000:1.000, N=100000:1.000
- `reverse` `document_chunks` `meta` ef=200 frac_hnsw by scale: N=5000:0.000, N=10000:0.000, N=15000:0.000, N=20000:0.000, N=25000:0.000, N=40000:0.000, N=50000:0.000, N=75000:0.000, N=100000:0.000
- `reverse` `document_chunks` `meta` ef=400 frac_hnsw by scale: N=5000:0.000, N=10000:0.000, N=15000:0.000, N=20000:0.000, N=25000:0.000, N=40000:0.000, N=50000:0.000, N=75000:0.000, N=100000:0.000
- `reverse` `document_chunks` `meta` ef=800 frac_hnsw by scale: N=5000:0.000, N=10000:0.000, N=15000:0.000, N=20000:0.000, N=25000:0.000, N=40000:0.175, N=50000:0.475, N=75000:0.550, N=100000:0.650
- `reverse` `document_chunks` `raw` ef=200 frac_hnsw by scale: N=5000:0.000, N=10000:0.000, N=15000:0.000, N=20000:0.000, N=25000:0.000, N=40000:0.000, N=50000:0.000, N=75000:1.000, N=100000:1.000
- `reverse` `document_chunks` `raw` ef=400 frac_hnsw by scale: N=5000:0.000, N=10000:0.000, N=15000:0.000, N=20000:0.000, N=25000:0.000, N=40000:0.000, N=50000:0.000, N=75000:0.000, N=100000:0.000
- `reverse` `document_chunks` `raw` ef=800 frac_hnsw by scale: N=5000:0.000, N=10000:1.000, N=15000:1.000, N=20000:1.000, N=25000:1.000, N=40000:1.000, N=50000:1.000, N=75000:1.000, N=100000:1.000
- `reverse` `document_chunks_titan` `meta` ef=200 frac_hnsw by scale: N=5000:0.000, N=10000:0.000, N=15000:0.000, N=20000:0.000, N=25000:0.000, N=40000:0.000, N=50000:0.000, N=75000:0.000, N=100000:0.000
- `reverse` `document_chunks_titan` `meta` ef=400 frac_hnsw by scale: N=5000:0.000, N=10000:0.000, N=15000:0.000, N=20000:0.000, N=25000:0.000, N=40000:0.000, N=50000:0.000, N=75000:0.000, N=100000:0.000
- `reverse` `document_chunks_titan` `meta` ef=800 frac_hnsw by scale: N=5000:0.000, N=10000:0.000, N=15000:0.000, N=20000:0.000, N=25000:0.000, N=40000:0.000, N=50000:0.000, N=75000:0.550, N=100000:0.650
- `reverse` `document_chunks_titan` `raw` ef=200 frac_hnsw by scale: N=5000:0.000, N=10000:0.000, N=15000:0.000, N=20000:0.000, N=25000:0.000, N=40000:0.000, N=50000:0.000, N=75000:0.000, N=100000:1.000
- `reverse` `document_chunks_titan` `raw` ef=400 frac_hnsw by scale: N=5000:0.000, N=10000:0.000, N=15000:0.000, N=20000:0.000, N=25000:0.000, N=40000:0.000, N=50000:0.000, N=75000:0.000, N=100000:0.000
- `reverse` `document_chunks_titan` `raw` ef=800 frac_hnsw by scale: N=5000:0.000, N=10000:0.000, N=15000:0.000, N=20000:0.000, N=25000:0.000, N=40000:0.000, N=50000:0.000, N=75000:1.000, N=100000:1.000

## Plan-type changes vs neighbouring scales

- forward document_chunks raw ef=200: scale 25000 sig=Limit > Sort > Bitmap Heap Scan > Bitmap Index Scan frac_hnsw=0.000 then scale 40000 sig=Limit > Gather Merge > Sort > Seq Scan frac_hnsw=0.000
- forward document_chunks raw ef=200: scale 50000 sig=Limit > Gather Merge > Sort > Seq Scan frac_hnsw=0.000 then scale 75000 sig=Limit > Index Scan frac_hnsw=1.000
- forward document_chunks raw ef=400: scale 25000 sig=Limit > Sort > Bitmap Heap Scan > Bitmap Index Scan frac_hnsw=0.000 then scale 40000 sig=Limit > Gather Merge > Sort > Seq Scan frac_hnsw=0.000
- forward document_chunks raw ef=800: scale 5000 sig=Limit > Sort > Bitmap Heap Scan > Bitmap Index Scan frac_hnsw=0.000 then scale 10000 sig=Limit > Index Scan frac_hnsw=1.000
- forward document_chunks meta ef=200: scale 40000 sig=Limit > Sort > Bitmap Heap Scan > BitmapAnd > Bitmap Index Scan > Bitmap Index Scan frac_hnsw=0.000 then scale 50000 sig=Limit > Sort > Bitmap Heap Scan > Bitmap Index Scan frac_hnsw=0.000
- forward document_chunks meta ef=400: scale 40000 sig=Limit > Sort > Bitmap Heap Scan > BitmapAnd > Bitmap Index Scan > Bitmap Index Scan frac_hnsw=0.000 then scale 50000 sig=Limit > Sort > Bitmap Heap Scan > Bitmap Index Scan frac_hnsw=0.000
- forward document_chunks meta ef=800: scale 25000 sig=Limit > Sort > Bitmap Heap Scan > BitmapAnd > Bitmap Index Scan > Bitmap Index Scan frac_hnsw=0.000 then scale 40000 sig=Limit > Sort > Bitmap Heap Scan > BitmapAnd > Bitmap Index Scan > Bitmap Index Scan frac_hnsw=0.175
- forward document_chunks meta ef=800: scale 40000 sig=Limit > Sort > Bitmap Heap Scan > BitmapAnd > Bitmap Index Scan > Bitmap Index Scan frac_hnsw=0.175 then scale 50000 sig=Limit > Index Scan frac_hnsw=0.475
- forward document_chunks meta ef=800: scale 50000 sig=Limit > Index Scan frac_hnsw=0.475 then scale 75000 sig=Limit > Index Scan frac_hnsw=0.550
- forward document_chunks meta ef=800: scale 75000 sig=Limit > Index Scan frac_hnsw=0.550 then scale 100000 sig=Limit > Index Scan frac_hnsw=0.650
- forward document_chunks_titan raw ef=200: scale 50000 sig=Limit > Sort > Index Scan frac_hnsw=0.000 then scale 75000 sig=Limit > Gather Merge > Sort > Index Scan frac_hnsw=0.000
- forward document_chunks_titan raw ef=200: scale 75000 sig=Limit > Gather Merge > Sort > Index Scan frac_hnsw=0.000 then scale 100000 sig=Limit > Index Scan frac_hnsw=1.000
- forward document_chunks_titan raw ef=400: scale 50000 sig=Limit > Sort > Index Scan frac_hnsw=0.000 then scale 75000 sig=Limit > Gather Merge > Sort > Index Scan frac_hnsw=0.000
- forward document_chunks_titan raw ef=400: scale 75000 sig=Limit > Gather Merge > Sort > Index Scan frac_hnsw=0.000 then scale 100000 sig=Limit > Gather Merge > Sort > Seq Scan frac_hnsw=0.000
- forward document_chunks_titan raw ef=800: scale 50000 sig=Limit > Sort > Index Scan frac_hnsw=0.000 then scale 75000 sig=Limit > Index Scan frac_hnsw=1.000
- forward document_chunks_titan meta ef=200: scale 50000 sig=Limit > Sort > Index Scan frac_hnsw=0.000 then scale 75000 sig=Limit > Sort > Bitmap Heap Scan > Bitmap Index Scan frac_hnsw=0.000
- forward document_chunks_titan meta ef=400: scale 50000 sig=Limit > Sort > Index Scan frac_hnsw=0.000 then scale 75000 sig=Limit > Sort > Bitmap Heap Scan > Bitmap Index Scan frac_hnsw=0.000
- forward document_chunks_titan meta ef=800: scale 50000 sig=Limit > Sort > Index Scan frac_hnsw=0.000 then scale 75000 sig=Limit > Index Scan frac_hnsw=0.550
- forward document_chunks_titan meta ef=800: scale 75000 sig=Limit > Index Scan frac_hnsw=0.550 then scale 100000 sig=Limit > Index Scan frac_hnsw=0.650
- reverse document_chunks raw ef=200: scale 25000 sig=Limit > Sort > Bitmap Heap Scan > Bitmap Index Scan frac_hnsw=0.000 then scale 40000 sig=Limit > Gather Merge > Sort > Seq Scan frac_hnsw=0.000
- reverse document_chunks raw ef=200: scale 50000 sig=Limit > Gather Merge > Sort > Seq Scan frac_hnsw=0.000 then scale 75000 sig=Limit > Index Scan frac_hnsw=1.000
- reverse document_chunks raw ef=400: scale 25000 sig=Limit > Sort > Bitmap Heap Scan > Bitmap Index Scan frac_hnsw=0.000 then scale 40000 sig=Limit > Gather Merge > Sort > Seq Scan frac_hnsw=0.000
- reverse document_chunks raw ef=800: scale 5000 sig=Limit > Sort > Bitmap Heap Scan > Bitmap Index Scan frac_hnsw=0.000 then scale 10000 sig=Limit > Index Scan frac_hnsw=1.000
- reverse document_chunks meta ef=200: scale 40000 sig=Limit > Sort > Bitmap Heap Scan > BitmapAnd > Bitmap Index Scan > Bitmap Index Scan frac_hnsw=0.000 then scale 50000 sig=Limit > Sort > Bitmap Heap Scan > Bitmap Index Scan frac_hnsw=0.000
- reverse document_chunks meta ef=400: scale 40000 sig=Limit > Sort > Bitmap Heap Scan > BitmapAnd > Bitmap Index Scan > Bitmap Index Scan frac_hnsw=0.000 then scale 50000 sig=Limit > Sort > Bitmap Heap Scan > Bitmap Index Scan frac_hnsw=0.000
- reverse document_chunks meta ef=800: scale 25000 sig=Limit > Sort > Bitmap Heap Scan > BitmapAnd > Bitmap Index Scan > Bitmap Index Scan frac_hnsw=0.000 then scale 40000 sig=Limit > Sort > Bitmap Heap Scan > BitmapAnd > Bitmap Index Scan > Bitmap Index Scan frac_hnsw=0.175
- reverse document_chunks meta ef=800: scale 40000 sig=Limit > Sort > Bitmap Heap Scan > BitmapAnd > Bitmap Index Scan > Bitmap Index Scan frac_hnsw=0.175 then scale 50000 sig=Limit > Index Scan frac_hnsw=0.475
- reverse document_chunks meta ef=800: scale 50000 sig=Limit > Index Scan frac_hnsw=0.475 then scale 75000 sig=Limit > Index Scan frac_hnsw=0.550
- reverse document_chunks meta ef=800: scale 75000 sig=Limit > Index Scan frac_hnsw=0.550 then scale 100000 sig=Limit > Index Scan frac_hnsw=0.650
- reverse document_chunks_titan raw ef=200: scale 50000 sig=Limit > Sort > Index Scan frac_hnsw=0.000 then scale 75000 sig=Limit > Gather Merge > Sort > Index Scan frac_hnsw=0.000
- reverse document_chunks_titan raw ef=200: scale 75000 sig=Limit > Gather Merge > Sort > Index Scan frac_hnsw=0.000 then scale 100000 sig=Limit > Index Scan frac_hnsw=1.000
- reverse document_chunks_titan raw ef=400: scale 50000 sig=Limit > Sort > Index Scan frac_hnsw=0.000 then scale 75000 sig=Limit > Gather Merge > Sort > Index Scan frac_hnsw=0.000
- reverse document_chunks_titan raw ef=400: scale 75000 sig=Limit > Gather Merge > Sort > Index Scan frac_hnsw=0.000 then scale 100000 sig=Limit > Gather Merge > Sort > Seq Scan frac_hnsw=0.000
- reverse document_chunks_titan raw ef=800: scale 50000 sig=Limit > Sort > Index Scan frac_hnsw=0.000 then scale 75000 sig=Limit > Index Scan frac_hnsw=1.000
- reverse document_chunks_titan meta ef=200: scale 50000 sig=Limit > Sort > Index Scan frac_hnsw=0.000 then scale 75000 sig=Limit > Sort > Bitmap Heap Scan > Bitmap Index Scan frac_hnsw=0.000
- reverse document_chunks_titan meta ef=400: scale 50000 sig=Limit > Sort > Index Scan frac_hnsw=0.000 then scale 75000 sig=Limit > Sort > Bitmap Heap Scan > Bitmap Index Scan frac_hnsw=0.000
- reverse document_chunks_titan meta ef=800: scale 50000 sig=Limit > Sort > Index Scan frac_hnsw=0.000 then scale 75000 sig=Limit > Index Scan frac_hnsw=0.550
- reverse document_chunks_titan meta ef=800: scale 75000 sig=Limit > Index Scan frac_hnsw=0.550 then scale 100000 sig=Limit > Index Scan frac_hnsw=0.650

## Acceptance

- `cell_counts`: **PASS** — ef200 cells with n=200: 72/72 (saw 72); ef400/800 cells with n=40: 144/144 (saw 144)
- `hand_explain_openai_raw_5k_ef200`: **PASS** — hand node_types=['Limit', 'Sort', 'Bitmap Heap Scan', 'Bitmap Index Scan'] summary_first=['Limit', 'Sort', 'Bitmap Heap Scan', 'Bitmap Index Scan'] eval_id_hand=qst_0102::basic eval_id_first=qst_0102::basic

