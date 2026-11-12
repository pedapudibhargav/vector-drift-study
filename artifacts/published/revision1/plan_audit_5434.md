# pgvector plan audit (port 5434)

Generated: 2026-11-10T02:23:33Z

## Server

- PostgreSQL: `PostgreSQL 16.15 (Debian 16.15-1.pgdg12+2) on aarch64-unknown-linux-gnu, compiled by gcc (Debian 12.2.0-14+deb12u1) 12.2.0, 64-bit`
- pgvector: `0.8.6`
- Settings:
  - `shared_buffers` = `128MB`
  - `work_mem` = `4MB`
  - `effective_cache_size` = `4GB`
  - `max_parallel_workers_per_gather` = `2`
  - `hnsw.ef_search` = `40`
  - `hnsw.iterative_scan` = `off`
  - `hnsw.max_scan_tuples` = `20000`
  - `hnsw.scan_mem_multiplier` = `1`

## HNSW indexes and relation sizes

| relname | bytes | pretty |
|---|---:|---|
| `document_chunks` | 107077632 | 102 MB |
| `document_chunks_titan` | 58720256 | 56 MB |
| `idx_chunks_embedding_hnsw` | 846348288 | 807 MB |
| `idx_chunks_scale_rank` | 6111232 | 5968 kB |
| `idx_chunks_source_type` | 2637824 | 2576 kB |
| `idx_chunks_titan_embedding_hnsw` | 819175424 | 781 MB |
| `idx_chunks_titan_scale_rank` | 2260992 | 2208 kB |
| `idx_chunks_titan_source_type` | 720896 | 704 kB |

HNSW index defs:

- `document_chunks.idx_chunks_embedding_hnsw`: `CREATE INDEX idx_chunks_embedding_hnsw ON public.document_chunks USING hnsw (embedding vector_cosine_ops) WITH (m='16', ef_construction='64')`
- `document_chunks_titan.idx_chunks_titan_embedding_hnsw`: `CREATE INDEX idx_chunks_titan_embedding_hnsw ON public.document_chunks_titan USING hnsw (embedding vector_cosine_ops) WITH (m='16', ef_construction='64')`

## Load average

- start: `{'captured_at': '2026-11-10T02:07:08Z', 'os_getloadavg_error': 'Load averages are unobtainable', 'uptime_stdout': '18:07  2 users, no load average information available', 'uptime_stderr': '', 'uptime_returncode': 0}`
- end: `{'captured_at': '2026-11-10T02:23:33Z', 'os_getloadavg_error': 'Load averages are unobtainable', 'uptime_stdout': '18:23  2 users, no load average information available', 'uptime_stderr': '', 'uptime_returncode': 0}`

Query shape matches `eval_scale_raw`:
`SET hnsw.ef_search`; `SET hnsw.iterative_scan = relaxed_order`;
`SELECT doc_id, 1 - (embedding <=> $vec::vector) AS score FROM <table> WHERE embedding IS NOT NULL AND scale_rank IS NOT NULL AND scale_rank < $N [AND source_type = $st] ORDER BY embedding <=> $vec::vector LIMIT 10`.

Buffers are the **root Plan node** Shared Hit/Read Blocks (PostgreSQL 16 JSON EXPLAIN includes child buffers there). Example plans have vector literals replaced with `[VECTOR]`.

## Per-cell summary

| pass | table | cond | scale | ef | n | frac_hnsw | frac_seq | frac_btree | frac_sort | median_ms | p95_ms | median_read | n_lt_10 |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| forward | `document_chunks` | raw | 5000 | 200 | 200 | 0.000 | 0.000 | 1.000 | 1.000 | 18.840 | 21.781 | 0.000 | 0 |
| forward | `document_chunks` | raw | 5000 | 400 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 18.607 | 19.869 | 0.000 | 0 |
| forward | `document_chunks` | raw | 5000 | 800 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 18.694 | 20.318 | 0.000 | 0 |
| forward | `document_chunks` | raw | 10000 | 200 | 200 | 1.000 | 0.000 | 0.000 | 0.000 | 24.161 | 241.8 | 1633.5 | 0 |
| forward | `document_chunks` | raw | 10000 | 400 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 55.806 | 59.624 | 8912.5 | 0 |
| forward | `document_chunks` | raw | 10000 | 800 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 56.779 | 60.027 | 8698.5 | 0 |
| forward | `document_chunks` | raw | 15000 | 200 | 200 | 1.000 | 0.000 | 0.000 | 0.000 | 5.772 | 10.627 | 1583.0 | 0 |
| forward | `document_chunks` | raw | 15000 | 400 | 40 | 0.000 | 1.000 | 0.000 | 1.000 | 102.3 | 119.5 | 31673.0 | 0 |
| forward | `document_chunks` | raw | 15000 | 800 | 40 | 0.000 | 1.000 | 0.000 | 1.000 | 103.3 | 164.6 | 31634.0 | 0 |
| forward | `document_chunks` | raw | 20000 | 200 | 200 | 1.000 | 0.000 | 0.000 | 0.000 | 8.465 | 23.828 | 1551.0 | 0 |
| forward | `document_chunks` | raw | 20000 | 400 | 40 | 0.000 | 1.000 | 0.000 | 1.000 | 129.2 | 158.1 | 41310.0 | 0 |
| forward | `document_chunks` | raw | 20000 | 800 | 40 | 0.000 | 1.000 | 0.000 | 1.000 | 124.2 | 129.6 | 41282.5 | 0 |
| forward | `document_chunks` | raw | 25000 | 200 | 200 | 1.000 | 0.000 | 0.000 | 0.000 | 5.825 | 12.207 | 1544.0 | 0 |
| forward | `document_chunks` | raw | 25000 | 400 | 40 | 0.000 | 1.000 | 0.000 | 1.000 | 70.659 | 83.889 | 48540.0 | 0 |
| forward | `document_chunks` | raw | 25000 | 800 | 40 | 0.000 | 1.000 | 0.000 | 1.000 | 68.666 | 74.797 | 48541.0 | 0 |
| forward | `document_chunks` | raw | 40000 | 200 | 200 | 1.000 | 0.000 | 0.000 | 0.000 | 5.354 | 8.322 | 1525.0 | 0 |
| forward | `document_chunks` | raw | 40000 | 400 | 40 | 0.000 | 1.000 | 0.000 | 1.000 | 108.2 | 123.0 | 69954.0 | 0 |
| forward | `document_chunks` | raw | 40000 | 800 | 40 | 0.000 | 1.000 | 0.000 | 1.000 | 109.6 | 120.6 | 69957.0 | 0 |
| forward | `document_chunks` | raw | 50000 | 200 | 200 | 1.000 | 0.000 | 0.000 | 0.000 | 7.679 | 15.930 | 1514.0 | 0 |
| forward | `document_chunks` | raw | 50000 | 400 | 40 | 0.000 | 1.000 | 0.000 | 1.000 | 134.0 | 160.6 | 84234.0 | 0 |
| forward | `document_chunks` | raw | 50000 | 800 | 40 | 0.000 | 1.000 | 0.000 | 1.000 | 129.6 | 148.7 | 84235.0 | 0 |
| forward | `document_chunks` | raw | 75000 | 200 | 200 | 1.000 | 0.000 | 0.000 | 0.000 | 6.776 | 16.209 | 1508.0 | 0 |
| forward | `document_chunks` | raw | 75000 | 400 | 40 | 0.000 | 1.000 | 0.000 | 1.000 | 184.8 | 277.9 | 120528.5 | 0 |
| forward | `document_chunks` | raw | 75000 | 800 | 40 | 0.000 | 1.000 | 0.000 | 1.000 | 197.4 | 307.8 | 120530.0 | 0 |
| forward | `document_chunks` | raw | 100000 | 200 | 200 | 1.000 | 0.000 | 0.000 | 0.000 | 7.066 | 14.264 | 1506.0 | 0 |
| forward | `document_chunks` | raw | 100000 | 400 | 40 | 0.000 | 1.000 | 0.000 | 1.000 | 247.1 | 280.5 | 157727.0 | 0 |
| forward | `document_chunks` | raw | 100000 | 800 | 40 | 0.000 | 1.000 | 0.000 | 1.000 | 244.9 | 266.3 | 157728.0 | 0 |
| forward | `document_chunks` | meta | 5000 | 200 | 200 | 0.000 | 0.000 | 1.000 | 1.000 | 4.261 | 7.814 | 0.000 | 0 |
| forward | `document_chunks` | meta | 5000 | 400 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 3.914 | 4.569 | 0.000 | 0 |
| forward | `document_chunks` | meta | 5000 | 800 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 3.838 | 4.167 | 0.000 | 0 |
| forward | `document_chunks` | meta | 10000 | 200 | 200 | 0.000 | 0.000 | 1.000 | 1.000 | 7.100 | 10.951 | 0.000 | 0 |
| forward | `document_chunks` | meta | 10000 | 400 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 7.047 | 7.856 | 0.000 | 0 |
| forward | `document_chunks` | meta | 10000 | 800 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 7.095 | 7.858 | 0.000 | 0 |
| forward | `document_chunks` | meta | 15000 | 200 | 200 | 0.000 | 0.000 | 1.000 | 1.000 | 11.804 | 32.324 | 234.0 | 0 |
| forward | `document_chunks` | meta | 15000 | 400 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 13.869 | 48.325 | 276.5 | 0 |
| forward | `document_chunks` | meta | 15000 | 800 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 12.003 | 16.166 | 453.5 | 0 |
| forward | `document_chunks` | meta | 20000 | 200 | 200 | 0.000 | 0.000 | 1.000 | 1.000 | 15.639 | 26.238 | 2261.0 | 0 |
| forward | `document_chunks` | meta | 20000 | 400 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 16.478 | 20.577 | 1533.5 | 0 |
| forward | `document_chunks` | meta | 20000 | 800 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 15.925 | 18.248 | 2320.5 | 0 |
| forward | `document_chunks` | meta | 25000 | 200 | 200 | 0.000 | 0.000 | 1.000 | 1.000 | 21.828 | 36.516 | 4561.5 | 0 |
| forward | `document_chunks` | meta | 25000 | 400 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 22.153 | 76.358 | 4497.5 | 0 |
| forward | `document_chunks` | meta | 25000 | 800 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 23.718 | 40.492 | 4378.5 | 0 |
| forward | `document_chunks` | meta | 40000 | 200 | 200 | 0.435 | 0.000 | 0.565 | 0.565 | 28.071 | 47.342 | 3561.0 | 0 |
| forward | `document_chunks` | meta | 40000 | 400 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 35.722 | 56.412 | 9018.0 | 0 |
| forward | `document_chunks` | meta | 40000 | 800 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 37.456 | 63.613 | 9115.5 | 0 |
| forward | `document_chunks` | meta | 50000 | 200 | 200 | 0.505 | 0.000 | 0.495 | 0.495 | 29.739 | 52.331 | 3214.0 | 0 |
| forward | `document_chunks` | meta | 50000 | 400 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 47.823 | 83.856 | 11950.0 | 0 |
| forward | `document_chunks` | meta | 50000 | 800 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 47.386 | 87.766 | 11952.0 | 0 |
| forward | `document_chunks` | meta | 75000 | 200 | 200 | 0.795 | 0.000 | 0.205 | 0.205 | 9.429 | 42.962 | 1901.5 | 0 |
| forward | `document_chunks` | meta | 75000 | 400 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 83.593 | 162.3 | 20387.5 | 0 |
| forward | `document_chunks` | meta | 75000 | 800 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 88.267 | 158.5 | 20387.5 | 0 |
| forward | `document_chunks` | meta | 100000 | 200 | 200 | 0.795 | 0.000 | 0.205 | 0.205 | 9.281 | 47.111 | 1882.5 | 0 |
| forward | `document_chunks` | meta | 100000 | 400 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 105.7 | 332.0 | 22044.5 | 0 |
| forward | `document_chunks` | meta | 100000 | 800 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 109.8 | 195.8 | 22044.5 | 0 |
| forward | `document_chunks_titan` | raw | 5000 | 200 | 200 | 0.000 | 0.000 | 1.000 | 1.000 | 19.400 | 35.798 | 0.000 | 0 |
| forward | `document_chunks_titan` | raw | 5000 | 400 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 18.846 | 23.695 | 0.000 | 0 |
| forward | `document_chunks_titan` | raw | 5000 | 800 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 18.727 | 21.441 | 0.000 | 0 |
| forward | `document_chunks_titan` | raw | 10000 | 200 | 200 | 0.000 | 0.000 | 1.000 | 1.000 | 36.999 | 42.454 | 0.000 | 0 |
| forward | `document_chunks_titan` | raw | 10000 | 400 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 37.745 | 44.000 | 0.000 | 0 |
| forward | `document_chunks_titan` | raw | 10000 | 800 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 37.306 | 45.681 | 0.000 | 0 |
| forward | `document_chunks_titan` | raw | 15000 | 200 | 200 | 0.000 | 0.000 | 1.000 | 1.000 | 67.923 | 84.623 | 10317.0 | 0 |
| forward | `document_chunks_titan` | raw | 15000 | 400 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 68.892 | 86.966 | 10335.5 | 0 |
| forward | `document_chunks_titan` | raw | 15000 | 800 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 69.259 | 78.214 | 10338.0 | 0 |
| forward | `document_chunks_titan` | raw | 20000 | 200 | 200 | 0.000 | 0.000 | 1.000 | 1.000 | 93.767 | 103.5 | 20096.0 | 0 |
| forward | `document_chunks_titan` | raw | 20000 | 400 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 92.311 | 96.914 | 20691.5 | 0 |
| forward | `document_chunks_titan` | raw | 20000 | 800 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 91.584 | 96.635 | 20691.5 | 0 |
| forward | `document_chunks_titan` | raw | 25000 | 200 | 200 | 0.000 | 0.000 | 1.000 | 1.000 | 117.5 | 148.7 | 29245.0 | 0 |
| forward | `document_chunks_titan` | raw | 25000 | 400 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 122.1 | 139.6 | 29245.0 | 0 |
| forward | `document_chunks_titan` | raw | 25000 | 800 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 125.1 | 178.9 | 29245.0 | 0 |
| forward | `document_chunks_titan` | raw | 40000 | 200 | 200 | 0.000 | 0.000 | 1.000 | 1.000 | 189.5 | 206.5 | 46793.0 | 0 |
| forward | `document_chunks_titan` | raw | 40000 | 400 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 185.9 | 191.4 | 46793.0 | 0 |
| forward | `document_chunks_titan` | raw | 40000 | 800 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 184.7 | 188.9 | 46793.0 | 0 |
| forward | `document_chunks_titan` | raw | 50000 | 200 | 200 | 0.000 | 0.000 | 1.000 | 1.000 | 235.1 | 253.2 | 58372.0 | 0 |
| forward | `document_chunks_titan` | raw | 50000 | 400 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 234.4 | 241.2 | 58372.0 | 0 |
| forward | `document_chunks_titan` | raw | 50000 | 800 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 234.4 | 243.5 | 58372.0 | 0 |
| forward | `document_chunks_titan` | raw | 75000 | 200 | 200 | 1.000 | 0.000 | 0.000 | 0.000 | 20.423 | 206.5 | 1737.0 | 0 |
| forward | `document_chunks_titan` | raw | 75000 | 400 | 40 | 0.000 | 1.000 | 0.000 | 1.000 | 164.1 | 179.9 | 88604.0 | 0 |
| forward | `document_chunks_titan` | raw | 75000 | 800 | 40 | 1.000 | 0.000 | 0.000 | 0.000 | 16.865 | 28.373 | 4736.0 | 0 |
| forward | `document_chunks_titan` | raw | 100000 | 200 | 200 | 1.000 | 0.000 | 0.000 | 0.000 | 5.793 | 7.834 | 1718.0 | 0 |
| forward | `document_chunks_titan` | raw | 100000 | 400 | 40 | 0.000 | 1.000 | 0.000 | 1.000 | 211.2 | 226.8 | 114946.0 | 0 |
| forward | `document_chunks_titan` | raw | 100000 | 800 | 40 | 1.000 | 0.000 | 0.000 | 0.000 | 13.846 | 20.098 | 4734.0 | 0 |
| forward | `document_chunks_titan` | meta | 5000 | 200 | 200 | 0.000 | 0.000 | 1.000 | 1.000 | 3.240 | 3.866 | 0.000 | 0 |
| forward | `document_chunks_titan` | meta | 5000 | 400 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 3.214 | 3.675 | 0.000 | 0 |
| forward | `document_chunks_titan` | meta | 5000 | 800 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 3.232 | 3.681 | 0.000 | 0 |
| forward | `document_chunks_titan` | meta | 10000 | 200 | 200 | 0.000 | 0.000 | 1.000 | 1.000 | 6.292 | 6.970 | 0.000 | 0 |
| forward | `document_chunks_titan` | meta | 10000 | 400 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 6.226 | 6.737 | 0.000 | 0 |
| forward | `document_chunks_titan` | meta | 10000 | 800 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 6.361 | 8.457 | 0.000 | 0 |
| forward | `document_chunks_titan` | meta | 15000 | 200 | 200 | 0.000 | 0.000 | 1.000 | 1.000 | 9.419 | 11.322 | 0.000 | 0 |
| forward | `document_chunks_titan` | meta | 15000 | 400 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 9.509 | 11.005 | 0.000 | 0 |
| forward | `document_chunks_titan` | meta | 15000 | 800 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 9.377 | 11.425 | 0.000 | 0 |
| forward | `document_chunks_titan` | meta | 20000 | 200 | 200 | 0.000 | 0.000 | 1.000 | 1.000 | 13.266 | 20.948 | 0.000 | 0 |
| forward | `document_chunks_titan` | meta | 20000 | 400 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 13.011 | 16.229 | 0.000 | 0 |
| forward | `document_chunks_titan` | meta | 20000 | 800 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 13.333 | 15.854 | 0.000 | 0 |
| forward | `document_chunks_titan` | meta | 25000 | 200 | 200 | 0.000 | 0.000 | 1.000 | 1.000 | 17.716 | 21.001 | 685.5 | 0 |
| forward | `document_chunks_titan` | meta | 25000 | 400 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 17.335 | 20.634 | 249.0 | 0 |
| forward | `document_chunks_titan` | meta | 25000 | 800 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 17.916 | 21.179 | 1121.5 | 0 |
| forward | `document_chunks_titan` | meta | 40000 | 200 | 200 | 0.000 | 0.000 | 1.000 | 1.000 | 31.355 | 33.895 | 5518.0 | 0 |
| forward | `document_chunks_titan` | meta | 40000 | 400 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 32.283 | 34.780 | 5837.0 | 0 |
| forward | `document_chunks_titan` | meta | 40000 | 800 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 31.298 | 35.138 | 5801.5 | 0 |
| forward | `document_chunks_titan` | meta | 50000 | 200 | 200 | 0.000 | 0.000 | 1.000 | 1.000 | 39.657 | 42.120 | 8548.0 | 0 |
| forward | `document_chunks_titan` | meta | 50000 | 400 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 39.907 | 41.708 | 8657.5 | 0 |
| forward | `document_chunks_titan` | meta | 50000 | 800 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 39.617 | 41.361 | 8718.0 | 0 |
| forward | `document_chunks_titan` | meta | 75000 | 200 | 200 | 0.000 | 0.000 | 1.000 | 1.000 | 55.757 | 66.535 | 15501.5 | 0 |
| forward | `document_chunks_titan` | meta | 75000 | 400 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 58.228 | 71.889 | 15723.0 | 0 |
| forward | `document_chunks_titan` | meta | 75000 | 800 | 40 | 0.650 | 0.000 | 0.350 | 0.350 | 20.241 | 35.935 | 6615.5 | 0 |
| forward | `document_chunks_titan` | meta | 100000 | 200 | 200 | 0.000 | 0.000 | 1.000 | 1.000 | 62.199 | 91.736 | 16378.5 | 0 |
| forward | `document_chunks_titan` | meta | 100000 | 400 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 65.175 | 90.574 | 18632.5 | 0 |
| forward | `document_chunks_titan` | meta | 100000 | 800 | 40 | 0.650 | 0.000 | 0.350 | 0.350 | 19.691 | 36.349 | 6609.0 | 0 |
| reverse | `document_chunks` | raw | 100000 | 200 | 200 | 1.000 | 0.000 | 0.000 | 0.000 | 8.148 | 15.373 | 1497.5 | 0 |
| reverse | `document_chunks` | raw | 100000 | 400 | 40 | 0.000 | 1.000 | 0.000 | 1.000 | 263.8 | 273.2 | 157727.0 | 0 |
| reverse | `document_chunks` | raw | 100000 | 800 | 40 | 0.000 | 1.000 | 0.000 | 1.000 | 262.5 | 274.6 | 157727.5 | 0 |
| reverse | `document_chunks` | raw | 75000 | 200 | 200 | 1.000 | 0.000 | 0.000 | 0.000 | 4.795 | 8.144 | 1508.0 | 0 |
| reverse | `document_chunks` | raw | 75000 | 400 | 40 | 0.000 | 1.000 | 0.000 | 1.000 | 203.1 | 206.4 | 120531.0 | 0 |
| reverse | `document_chunks` | raw | 75000 | 800 | 40 | 0.000 | 1.000 | 0.000 | 1.000 | 203.9 | 212.3 | 120531.0 | 0 |
| reverse | `document_chunks` | raw | 50000 | 200 | 200 | 1.000 | 0.000 | 0.000 | 0.000 | 4.824 | 7.239 | 1517.0 | 0 |
| reverse | `document_chunks` | raw | 50000 | 400 | 40 | 0.000 | 1.000 | 0.000 | 1.000 | 141.2 | 144.0 | 84234.5 | 0 |
| reverse | `document_chunks` | raw | 50000 | 800 | 40 | 0.000 | 1.000 | 0.000 | 1.000 | 141.8 | 147.2 | 84234.0 | 0 |
| reverse | `document_chunks` | raw | 40000 | 200 | 200 | 1.000 | 0.000 | 0.000 | 0.000 | 4.502 | 6.957 | 1526.0 | 0 |
| reverse | `document_chunks` | raw | 40000 | 400 | 40 | 0.000 | 1.000 | 0.000 | 1.000 | 117.5 | 120.5 | 69954.5 | 0 |
| reverse | `document_chunks` | raw | 40000 | 800 | 40 | 0.000 | 1.000 | 0.000 | 1.000 | 117.9 | 122.4 | 69957.0 | 0 |
| reverse | `document_chunks` | raw | 25000 | 200 | 200 | 1.000 | 0.000 | 0.000 | 0.000 | 4.659 | 7.175 | 1544.0 | 0 |
| reverse | `document_chunks` | raw | 25000 | 400 | 40 | 0.000 | 1.000 | 0.000 | 1.000 | 80.326 | 105.7 | 48541.0 | 0 |
| reverse | `document_chunks` | raw | 25000 | 800 | 40 | 0.000 | 1.000 | 0.000 | 1.000 | 80.050 | 85.783 | 48543.0 | 0 |
| reverse | `document_chunks` | raw | 20000 | 200 | 200 | 1.000 | 0.000 | 0.000 | 0.000 | 4.726 | 7.509 | 1556.5 | 0 |
| reverse | `document_chunks` | raw | 20000 | 400 | 40 | 0.000 | 1.000 | 0.000 | 1.000 | 141.2 | 145.2 | 41310.0 | 0 |
| reverse | `document_chunks` | raw | 20000 | 800 | 40 | 0.000 | 1.000 | 0.000 | 1.000 | 142.4 | 149.2 | 41282.5 | 0 |
| reverse | `document_chunks` | raw | 15000 | 200 | 200 | 1.000 | 0.000 | 0.000 | 0.000 | 4.915 | 10.057 | 1581.5 | 0 |
| reverse | `document_chunks` | raw | 15000 | 400 | 40 | 0.000 | 1.000 | 0.000 | 1.000 | 110.8 | 117.9 | 31674.0 | 0 |
| reverse | `document_chunks` | raw | 15000 | 800 | 40 | 0.000 | 1.000 | 0.000 | 1.000 | 110.6 | 115.4 | 31639.5 | 0 |
| reverse | `document_chunks` | raw | 10000 | 200 | 200 | 1.000 | 0.000 | 0.000 | 0.000 | 4.831 | 9.408 | 1621.0 | 0 |
| reverse | `document_chunks` | raw | 10000 | 400 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 59.266 | 68.205 | 8787.0 | 0 |
| reverse | `document_chunks` | raw | 10000 | 800 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 59.604 | 71.605 | 8698.5 | 0 |
| reverse | `document_chunks` | raw | 5000 | 200 | 200 | 0.000 | 0.000 | 1.000 | 1.000 | 24.987 | 26.464 | 0.000 | 0 |
| reverse | `document_chunks` | raw | 5000 | 400 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 24.936 | 25.804 | 0.000 | 0 |
| reverse | `document_chunks` | raw | 5000 | 800 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 24.962 | 28.408 | 0.000 | 0 |
| reverse | `document_chunks` | meta | 100000 | 200 | 200 | 0.795 | 0.000 | 0.205 | 0.205 | 5.990 | 39.570 | 1902.0 | 0 |
| reverse | `document_chunks` | meta | 100000 | 400 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 105.9 | 178.1 | 22044.5 | 0 |
| reverse | `document_chunks` | meta | 100000 | 800 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 85.611 | 115.9 | 22044.5 | 0 |
| reverse | `document_chunks` | meta | 75000 | 200 | 200 | 0.795 | 0.000 | 0.205 | 0.205 | 5.591 | 37.693 | 1904.5 | 0 |
| reverse | `document_chunks` | meta | 75000 | 400 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 74.318 | 82.813 | 20387.5 | 0 |
| reverse | `document_chunks` | meta | 75000 | 800 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 75.550 | 92.778 | 20387.5 | 0 |
| reverse | `document_chunks` | meta | 50000 | 200 | 200 | 0.505 | 0.000 | 0.495 | 0.495 | 27.570 | 47.260 | 3214.0 | 0 |
| reverse | `document_chunks` | meta | 50000 | 400 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 46.419 | 57.186 | 11950.5 | 0 |
| reverse | `document_chunks` | meta | 50000 | 800 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 45.888 | 54.825 | 11952.0 | 0 |
| reverse | `document_chunks` | meta | 40000 | 200 | 200 | 0.435 | 0.000 | 0.565 | 0.565 | 24.819 | 36.783 | 3561.0 | 0 |
| reverse | `document_chunks` | meta | 40000 | 400 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 35.587 | 39.095 | 9015.0 | 0 |
| reverse | `document_chunks` | meta | 40000 | 800 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 36.026 | 38.372 | 9118.0 | 0 |
| reverse | `document_chunks` | meta | 25000 | 200 | 200 | 0.000 | 0.000 | 1.000 | 1.000 | 21.424 | 23.877 | 4572.0 | 0 |
| reverse | `document_chunks` | meta | 25000 | 400 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 21.612 | 24.159 | 4497.5 | 0 |
| reverse | `document_chunks` | meta | 25000 | 800 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 21.470 | 23.277 | 4377.5 | 0 |
| reverse | `document_chunks` | meta | 20000 | 200 | 200 | 0.000 | 0.000 | 1.000 | 1.000 | 15.953 | 18.987 | 2277.5 | 0 |
| reverse | `document_chunks` | meta | 20000 | 400 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 15.791 | 18.669 | 1361.5 | 0 |
| reverse | `document_chunks` | meta | 20000 | 800 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 16.806 | 33.587 | 2325.5 | 0 |
| reverse | `document_chunks` | meta | 15000 | 200 | 200 | 0.000 | 0.000 | 1.000 | 1.000 | 11.101 | 14.175 | 230.0 | 0 |
| reverse | `document_chunks` | meta | 15000 | 400 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 11.638 | 14.000 | 269.0 | 0 |
| reverse | `document_chunks` | meta | 15000 | 800 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 11.639 | 14.550 | 424.5 | 0 |
| reverse | `document_chunks` | meta | 10000 | 200 | 200 | 0.000 | 0.000 | 1.000 | 1.000 | 7.188 | 8.729 | 0.000 | 0 |
| reverse | `document_chunks` | meta | 10000 | 400 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 7.261 | 8.332 | 0.000 | 0 |
| reverse | `document_chunks` | meta | 10000 | 800 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 7.274 | 7.891 | 0.000 | 0 |
| reverse | `document_chunks` | meta | 5000 | 200 | 200 | 0.000 | 0.000 | 1.000 | 1.000 | 3.994 | 4.465 | 0.000 | 0 |
| reverse | `document_chunks` | meta | 5000 | 400 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 4.018 | 4.568 | 0.000 | 0 |
| reverse | `document_chunks` | meta | 5000 | 800 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 4.081 | 4.896 | 0.000 | 0 |
| reverse | `document_chunks_titan` | raw | 100000 | 200 | 200 | 1.000 | 0.000 | 0.000 | 0.000 | 6.932 | 19.969 | 1755.0 | 0 |
| reverse | `document_chunks_titan` | raw | 100000 | 400 | 40 | 0.000 | 1.000 | 0.000 | 1.000 | 211.8 | 221.4 | 114946.0 | 0 |
| reverse | `document_chunks_titan` | raw | 100000 | 800 | 40 | 1.000 | 0.000 | 0.000 | 0.000 | 15.399 | 24.012 | 4733.5 | 0 |
| reverse | `document_chunks_titan` | raw | 75000 | 200 | 200 | 1.000 | 0.000 | 0.000 | 0.000 | 4.819 | 6.755 | 1723.5 | 0 |
| reverse | `document_chunks_titan` | raw | 75000 | 400 | 40 | 0.000 | 1.000 | 0.000 | 1.000 | 163.4 | 167.8 | 88604.0 | 0 |
| reverse | `document_chunks_titan` | raw | 75000 | 800 | 40 | 1.000 | 0.000 | 0.000 | 0.000 | 13.870 | 20.019 | 4736.5 | 0 |
| reverse | `document_chunks_titan` | raw | 50000 | 200 | 200 | 0.000 | 0.000 | 1.000 | 1.000 | 235.2 | 263.6 | 58372.0 | 0 |
| reverse | `document_chunks_titan` | raw | 50000 | 400 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 234.2 | 244.0 | 58372.0 | 0 |
| reverse | `document_chunks_titan` | raw | 50000 | 800 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 233.0 | 248.9 | 58372.0 | 0 |
| reverse | `document_chunks_titan` | raw | 40000 | 200 | 200 | 0.000 | 0.000 | 1.000 | 1.000 | 187.0 | 200.3 | 46793.0 | 0 |
| reverse | `document_chunks_titan` | raw | 40000 | 400 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 187.0 | 195.7 | 46793.0 | 0 |
| reverse | `document_chunks_titan` | raw | 40000 | 800 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 187.8 | 192.9 | 46793.0 | 0 |
| reverse | `document_chunks_titan` | raw | 25000 | 200 | 200 | 0.000 | 0.000 | 1.000 | 1.000 | 117.0 | 126.2 | 29245.0 | 0 |
| reverse | `document_chunks_titan` | raw | 25000 | 400 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 115.9 | 122.6 | 29245.0 | 0 |
| reverse | `document_chunks_titan` | raw | 25000 | 800 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 115.8 | 121.2 | 29245.0 | 0 |
| reverse | `document_chunks_titan` | raw | 20000 | 200 | 200 | 0.000 | 0.000 | 1.000 | 1.000 | 92.540 | 98.681 | 20691.0 | 0 |
| reverse | `document_chunks_titan` | raw | 20000 | 400 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 92.757 | 99.626 | 20691.0 | 0 |
| reverse | `document_chunks_titan` | raw | 20000 | 800 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 92.373 | 97.132 | 20691.0 | 0 |
| reverse | `document_chunks_titan` | raw | 15000 | 200 | 200 | 0.000 | 0.000 | 1.000 | 1.000 | 68.308 | 73.481 | 13743.0 | 0 |
| reverse | `document_chunks_titan` | raw | 15000 | 400 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 65.969 | 77.979 | 13743.0 | 0 |
| reverse | `document_chunks_titan` | raw | 15000 | 800 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 69.250 | 79.619 | 13743.0 | 0 |
| reverse | `document_chunks_titan` | raw | 10000 | 200 | 200 | 0.000 | 0.000 | 1.000 | 1.000 | 37.464 | 46.220 | 0.000 | 0 |
| reverse | `document_chunks_titan` | raw | 10000 | 400 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 37.290 | 40.040 | 0.000 | 0 |
| reverse | `document_chunks_titan` | raw | 10000 | 800 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 36.475 | 38.558 | 0.000 | 0 |
| reverse | `document_chunks_titan` | raw | 5000 | 200 | 200 | 0.000 | 0.000 | 1.000 | 1.000 | 18.453 | 20.737 | 0.000 | 0 |
| reverse | `document_chunks_titan` | raw | 5000 | 400 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 18.609 | 19.554 | 0.000 | 0 |
| reverse | `document_chunks_titan` | raw | 5000 | 800 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 18.401 | 19.260 | 0.000 | 0 |
| reverse | `document_chunks_titan` | meta | 100000 | 200 | 200 | 0.000 | 0.000 | 1.000 | 1.000 | 64.180 | 96.626 | 16378.5 | 0 |
| reverse | `document_chunks_titan` | meta | 100000 | 400 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 69.341 | 97.654 | 18632.5 | 0 |
| reverse | `document_chunks_titan` | meta | 100000 | 800 | 40 | 0.650 | 0.000 | 0.350 | 0.350 | 30.541 | 45.415 | 6609.0 | 0 |
| reverse | `document_chunks_titan` | meta | 75000 | 200 | 200 | 0.000 | 0.000 | 1.000 | 1.000 | 55.826 | 65.948 | 15501.5 | 0 |
| reverse | `document_chunks_titan` | meta | 75000 | 400 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 59.272 | 65.732 | 15723.0 | 0 |
| reverse | `document_chunks_titan` | meta | 75000 | 800 | 40 | 0.650 | 0.000 | 0.350 | 0.350 | 19.750 | 36.355 | 6615.5 | 0 |
| reverse | `document_chunks_titan` | meta | 50000 | 200 | 200 | 0.000 | 0.000 | 1.000 | 1.000 | 39.576 | 43.487 | 8546.0 | 0 |
| reverse | `document_chunks_titan` | meta | 50000 | 400 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 39.581 | 41.002 | 8658.0 | 0 |
| reverse | `document_chunks_titan` | meta | 50000 | 800 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 38.475 | 42.448 | 8707.5 | 0 |
| reverse | `document_chunks_titan` | meta | 40000 | 200 | 200 | 0.000 | 0.000 | 1.000 | 1.000 | 30.703 | 33.218 | 5581.0 | 0 |
| reverse | `document_chunks_titan` | meta | 40000 | 400 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 31.009 | 33.125 | 5892.0 | 0 |
| reverse | `document_chunks_titan` | meta | 40000 | 800 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 30.800 | 34.411 | 5797.0 | 0 |
| reverse | `document_chunks_titan` | meta | 25000 | 200 | 200 | 0.000 | 0.000 | 1.000 | 1.000 | 17.873 | 20.742 | 913.5 | 0 |
| reverse | `document_chunks_titan` | meta | 25000 | 400 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 17.672 | 20.986 | 256.5 | 0 |
| reverse | `document_chunks_titan` | meta | 25000 | 800 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 17.037 | 20.782 | 1121.5 | 0 |
| reverse | `document_chunks_titan` | meta | 20000 | 200 | 200 | 0.000 | 0.000 | 1.000 | 1.000 | 12.671 | 16.145 | 0.000 | 0 |
| reverse | `document_chunks_titan` | meta | 20000 | 400 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 12.729 | 16.501 | 0.000 | 0 |
| reverse | `document_chunks_titan` | meta | 20000 | 800 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 13.018 | 15.985 | 209.5 | 0 |
| reverse | `document_chunks_titan` | meta | 15000 | 200 | 200 | 0.000 | 0.000 | 1.000 | 1.000 | 9.398 | 10.901 | 0.000 | 0 |
| reverse | `document_chunks_titan` | meta | 15000 | 400 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 9.486 | 11.867 | 0.000 | 0 |
| reverse | `document_chunks_titan` | meta | 15000 | 800 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 9.418 | 11.606 | 0.000 | 0 |
| reverse | `document_chunks_titan` | meta | 10000 | 200 | 200 | 0.000 | 0.000 | 1.000 | 1.000 | 6.306 | 7.028 | 0.000 | 0 |
| reverse | `document_chunks_titan` | meta | 10000 | 400 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 6.248 | 6.773 | 0.000 | 0 |
| reverse | `document_chunks_titan` | meta | 10000 | 800 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 6.225 | 6.764 | 0.000 | 0 |
| reverse | `document_chunks_titan` | meta | 5000 | 200 | 200 | 0.000 | 0.000 | 1.000 | 1.000 | 3.192 | 3.692 | 0.000 | 0 |
| reverse | `document_chunks_titan` | meta | 5000 | 400 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 3.196 | 3.741 | 0.000 | 0 |
| reverse | `document_chunks_titan` | meta | 5000 | 800 | 40 | 0.000 | 0.000 | 1.000 | 1.000 | 3.162 | 3.615 | 0.000 | 0 |

## Did this configuration use the HNSW index?

Values are fractions of queries in that cell. This is a planner audit, not a recall result.

- `forward` `document_chunks` `meta` ef=200 frac_hnsw by scale: N=5000:0.000, N=10000:0.000, N=15000:0.000, N=20000:0.000, N=25000:0.000, N=40000:0.435, N=50000:0.505, N=75000:0.795, N=100000:0.795
- `forward` `document_chunks` `meta` ef=400 frac_hnsw by scale: N=5000:0.000, N=10000:0.000, N=15000:0.000, N=20000:0.000, N=25000:0.000, N=40000:0.000, N=50000:0.000, N=75000:0.000, N=100000:0.000
- `forward` `document_chunks` `meta` ef=800 frac_hnsw by scale: N=5000:0.000, N=10000:0.000, N=15000:0.000, N=20000:0.000, N=25000:0.000, N=40000:0.000, N=50000:0.000, N=75000:0.000, N=100000:0.000
- `forward` `document_chunks` `raw` ef=200 frac_hnsw by scale: N=5000:0.000, N=10000:1.000, N=15000:1.000, N=20000:1.000, N=25000:1.000, N=40000:1.000, N=50000:1.000, N=75000:1.000, N=100000:1.000
- `forward` `document_chunks` `raw` ef=400 frac_hnsw by scale: N=5000:0.000, N=10000:0.000, N=15000:0.000, N=20000:0.000, N=25000:0.000, N=40000:0.000, N=50000:0.000, N=75000:0.000, N=100000:0.000
- `forward` `document_chunks` `raw` ef=800 frac_hnsw by scale: N=5000:0.000, N=10000:0.000, N=15000:0.000, N=20000:0.000, N=25000:0.000, N=40000:0.000, N=50000:0.000, N=75000:0.000, N=100000:0.000
- `forward` `document_chunks_titan` `meta` ef=200 frac_hnsw by scale: N=5000:0.000, N=10000:0.000, N=15000:0.000, N=20000:0.000, N=25000:0.000, N=40000:0.000, N=50000:0.000, N=75000:0.000, N=100000:0.000
- `forward` `document_chunks_titan` `meta` ef=400 frac_hnsw by scale: N=5000:0.000, N=10000:0.000, N=15000:0.000, N=20000:0.000, N=25000:0.000, N=40000:0.000, N=50000:0.000, N=75000:0.000, N=100000:0.000
- `forward` `document_chunks_titan` `meta` ef=800 frac_hnsw by scale: N=5000:0.000, N=10000:0.000, N=15000:0.000, N=20000:0.000, N=25000:0.000, N=40000:0.000, N=50000:0.000, N=75000:0.650, N=100000:0.650
- `forward` `document_chunks_titan` `raw` ef=200 frac_hnsw by scale: N=5000:0.000, N=10000:0.000, N=15000:0.000, N=20000:0.000, N=25000:0.000, N=40000:0.000, N=50000:0.000, N=75000:1.000, N=100000:1.000
- `forward` `document_chunks_titan` `raw` ef=400 frac_hnsw by scale: N=5000:0.000, N=10000:0.000, N=15000:0.000, N=20000:0.000, N=25000:0.000, N=40000:0.000, N=50000:0.000, N=75000:0.000, N=100000:0.000
- `forward` `document_chunks_titan` `raw` ef=800 frac_hnsw by scale: N=5000:0.000, N=10000:0.000, N=15000:0.000, N=20000:0.000, N=25000:0.000, N=40000:0.000, N=50000:0.000, N=75000:1.000, N=100000:1.000
- `reverse` `document_chunks` `meta` ef=200 frac_hnsw by scale: N=5000:0.000, N=10000:0.000, N=15000:0.000, N=20000:0.000, N=25000:0.000, N=40000:0.435, N=50000:0.505, N=75000:0.795, N=100000:0.795
- `reverse` `document_chunks` `meta` ef=400 frac_hnsw by scale: N=5000:0.000, N=10000:0.000, N=15000:0.000, N=20000:0.000, N=25000:0.000, N=40000:0.000, N=50000:0.000, N=75000:0.000, N=100000:0.000
- `reverse` `document_chunks` `meta` ef=800 frac_hnsw by scale: N=5000:0.000, N=10000:0.000, N=15000:0.000, N=20000:0.000, N=25000:0.000, N=40000:0.000, N=50000:0.000, N=75000:0.000, N=100000:0.000
- `reverse` `document_chunks` `raw` ef=200 frac_hnsw by scale: N=5000:0.000, N=10000:1.000, N=15000:1.000, N=20000:1.000, N=25000:1.000, N=40000:1.000, N=50000:1.000, N=75000:1.000, N=100000:1.000
- `reverse` `document_chunks` `raw` ef=400 frac_hnsw by scale: N=5000:0.000, N=10000:0.000, N=15000:0.000, N=20000:0.000, N=25000:0.000, N=40000:0.000, N=50000:0.000, N=75000:0.000, N=100000:0.000
- `reverse` `document_chunks` `raw` ef=800 frac_hnsw by scale: N=5000:0.000, N=10000:0.000, N=15000:0.000, N=20000:0.000, N=25000:0.000, N=40000:0.000, N=50000:0.000, N=75000:0.000, N=100000:0.000
- `reverse` `document_chunks_titan` `meta` ef=200 frac_hnsw by scale: N=5000:0.000, N=10000:0.000, N=15000:0.000, N=20000:0.000, N=25000:0.000, N=40000:0.000, N=50000:0.000, N=75000:0.000, N=100000:0.000
- `reverse` `document_chunks_titan` `meta` ef=400 frac_hnsw by scale: N=5000:0.000, N=10000:0.000, N=15000:0.000, N=20000:0.000, N=25000:0.000, N=40000:0.000, N=50000:0.000, N=75000:0.000, N=100000:0.000
- `reverse` `document_chunks_titan` `meta` ef=800 frac_hnsw by scale: N=5000:0.000, N=10000:0.000, N=15000:0.000, N=20000:0.000, N=25000:0.000, N=40000:0.000, N=50000:0.000, N=75000:0.650, N=100000:0.650
- `reverse` `document_chunks_titan` `raw` ef=200 frac_hnsw by scale: N=5000:0.000, N=10000:0.000, N=15000:0.000, N=20000:0.000, N=25000:0.000, N=40000:0.000, N=50000:0.000, N=75000:1.000, N=100000:1.000
- `reverse` `document_chunks_titan` `raw` ef=400 frac_hnsw by scale: N=5000:0.000, N=10000:0.000, N=15000:0.000, N=20000:0.000, N=25000:0.000, N=40000:0.000, N=50000:0.000, N=75000:0.000, N=100000:0.000
- `reverse` `document_chunks_titan` `raw` ef=800 frac_hnsw by scale: N=5000:0.000, N=10000:0.000, N=15000:0.000, N=20000:0.000, N=25000:0.000, N=40000:0.000, N=50000:0.000, N=75000:1.000, N=100000:1.000

## Plan-type changes vs neighbouring scales

- forward document_chunks raw ef=200: scale 5000 sig=Limit > Sort > Bitmap Heap Scan > Bitmap Index Scan frac_hnsw=0.000 then scale 10000 sig=Limit > Index Scan frac_hnsw=1.000
- forward document_chunks raw ef=400: scale 10000 sig=Limit > Sort > Bitmap Heap Scan > Bitmap Index Scan frac_hnsw=0.000 then scale 15000 sig=Limit > Sort > Seq Scan frac_hnsw=0.000
- forward document_chunks raw ef=400: scale 20000 sig=Limit > Sort > Seq Scan frac_hnsw=0.000 then scale 25000 sig=Limit > Gather Merge > Sort > Seq Scan frac_hnsw=0.000
- forward document_chunks raw ef=800: scale 10000 sig=Limit > Sort > Bitmap Heap Scan > Bitmap Index Scan frac_hnsw=0.000 then scale 15000 sig=Limit > Sort > Seq Scan frac_hnsw=0.000
- forward document_chunks raw ef=800: scale 20000 sig=Limit > Sort > Seq Scan frac_hnsw=0.000 then scale 25000 sig=Limit > Gather Merge > Sort > Seq Scan frac_hnsw=0.000
- forward document_chunks meta ef=200: scale 25000 sig=Limit > Sort > Bitmap Heap Scan > BitmapAnd > Bitmap Index Scan > Bitmap Index Scan frac_hnsw=0.000 then scale 40000 sig=Limit > Sort > Bitmap Heap Scan > BitmapAnd > Bitmap Index Scan > Bitmap Index Scan frac_hnsw=0.435
- forward document_chunks meta ef=200: scale 40000 sig=Limit > Sort > Bitmap Heap Scan > BitmapAnd > Bitmap Index Scan > Bitmap Index Scan frac_hnsw=0.435 then scale 50000 sig=Limit > Index Scan frac_hnsw=0.505
- forward document_chunks meta ef=200: scale 50000 sig=Limit > Index Scan frac_hnsw=0.505 then scale 75000 sig=Limit > Index Scan frac_hnsw=0.795
- forward document_chunks meta ef=400: scale 50000 sig=Limit > Sort > Bitmap Heap Scan > BitmapAnd > Bitmap Index Scan > Bitmap Index Scan frac_hnsw=0.000 then scale 75000 sig=Limit > Sort > Bitmap Heap Scan > Bitmap Index Scan frac_hnsw=0.000
- forward document_chunks meta ef=800: scale 50000 sig=Limit > Sort > Bitmap Heap Scan > BitmapAnd > Bitmap Index Scan > Bitmap Index Scan frac_hnsw=0.000 then scale 75000 sig=Limit > Sort > Bitmap Heap Scan > Bitmap Index Scan frac_hnsw=0.000
- forward document_chunks_titan raw ef=200: scale 50000 sig=Limit > Sort > Index Scan frac_hnsw=0.000 then scale 75000 sig=Limit > Index Scan frac_hnsw=1.000
- forward document_chunks_titan raw ef=400: scale 50000 sig=Limit > Sort > Index Scan frac_hnsw=0.000 then scale 75000 sig=Limit > Gather Merge > Sort > Seq Scan frac_hnsw=0.000
- forward document_chunks_titan raw ef=800: scale 50000 sig=Limit > Sort > Index Scan frac_hnsw=0.000 then scale 75000 sig=Limit > Index Scan frac_hnsw=1.000
- forward document_chunks_titan meta ef=200: scale 50000 sig=Limit > Sort > Index Scan frac_hnsw=0.000 then scale 75000 sig=Limit > Sort > Bitmap Heap Scan > Bitmap Index Scan frac_hnsw=0.000
- forward document_chunks_titan meta ef=400: scale 50000 sig=Limit > Sort > Index Scan frac_hnsw=0.000 then scale 75000 sig=Limit > Sort > Bitmap Heap Scan > Bitmap Index Scan frac_hnsw=0.000
- forward document_chunks_titan meta ef=800: scale 50000 sig=Limit > Sort > Index Scan frac_hnsw=0.000 then scale 75000 sig=Limit > Index Scan frac_hnsw=0.650
- reverse document_chunks raw ef=200: scale 5000 sig=Limit > Sort > Bitmap Heap Scan > Bitmap Index Scan frac_hnsw=0.000 then scale 10000 sig=Limit > Index Scan frac_hnsw=1.000
- reverse document_chunks raw ef=400: scale 10000 sig=Limit > Sort > Bitmap Heap Scan > Bitmap Index Scan frac_hnsw=0.000 then scale 15000 sig=Limit > Sort > Seq Scan frac_hnsw=0.000
- reverse document_chunks raw ef=400: scale 20000 sig=Limit > Sort > Seq Scan frac_hnsw=0.000 then scale 25000 sig=Limit > Gather Merge > Sort > Seq Scan frac_hnsw=0.000
- reverse document_chunks raw ef=800: scale 10000 sig=Limit > Sort > Bitmap Heap Scan > Bitmap Index Scan frac_hnsw=0.000 then scale 15000 sig=Limit > Sort > Seq Scan frac_hnsw=0.000
- reverse document_chunks raw ef=800: scale 20000 sig=Limit > Sort > Seq Scan frac_hnsw=0.000 then scale 25000 sig=Limit > Gather Merge > Sort > Seq Scan frac_hnsw=0.000
- reverse document_chunks meta ef=200: scale 25000 sig=Limit > Sort > Bitmap Heap Scan > BitmapAnd > Bitmap Index Scan > Bitmap Index Scan frac_hnsw=0.000 then scale 40000 sig=Limit > Sort > Bitmap Heap Scan > BitmapAnd > Bitmap Index Scan > Bitmap Index Scan frac_hnsw=0.435
- reverse document_chunks meta ef=200: scale 40000 sig=Limit > Sort > Bitmap Heap Scan > BitmapAnd > Bitmap Index Scan > Bitmap Index Scan frac_hnsw=0.435 then scale 50000 sig=Limit > Index Scan frac_hnsw=0.505
- reverse document_chunks meta ef=200: scale 50000 sig=Limit > Index Scan frac_hnsw=0.505 then scale 75000 sig=Limit > Index Scan frac_hnsw=0.795
- reverse document_chunks meta ef=400: scale 50000 sig=Limit > Sort > Bitmap Heap Scan > BitmapAnd > Bitmap Index Scan > Bitmap Index Scan frac_hnsw=0.000 then scale 75000 sig=Limit > Sort > Bitmap Heap Scan > Bitmap Index Scan frac_hnsw=0.000
- reverse document_chunks meta ef=800: scale 50000 sig=Limit > Sort > Bitmap Heap Scan > BitmapAnd > Bitmap Index Scan > Bitmap Index Scan frac_hnsw=0.000 then scale 75000 sig=Limit > Sort > Bitmap Heap Scan > Bitmap Index Scan frac_hnsw=0.000
- reverse document_chunks_titan raw ef=200: scale 50000 sig=Limit > Sort > Index Scan frac_hnsw=0.000 then scale 75000 sig=Limit > Index Scan frac_hnsw=1.000
- reverse document_chunks_titan raw ef=400: scale 50000 sig=Limit > Sort > Index Scan frac_hnsw=0.000 then scale 75000 sig=Limit > Gather Merge > Sort > Seq Scan frac_hnsw=0.000
- reverse document_chunks_titan raw ef=800: scale 50000 sig=Limit > Sort > Index Scan frac_hnsw=0.000 then scale 75000 sig=Limit > Index Scan frac_hnsw=1.000
- reverse document_chunks_titan meta ef=200: scale 50000 sig=Limit > Sort > Index Scan frac_hnsw=0.000 then scale 75000 sig=Limit > Sort > Bitmap Heap Scan > Bitmap Index Scan frac_hnsw=0.000
- reverse document_chunks_titan meta ef=400: scale 50000 sig=Limit > Sort > Index Scan frac_hnsw=0.000 then scale 75000 sig=Limit > Sort > Bitmap Heap Scan > Bitmap Index Scan frac_hnsw=0.000
- reverse document_chunks_titan meta ef=800: scale 50000 sig=Limit > Sort > Index Scan frac_hnsw=0.000 then scale 75000 sig=Limit > Index Scan frac_hnsw=0.650

## Acceptance

- `cell_counts`: **PASS** — ef200 cells with n=200: 72/72 (saw 72); ef400/800 cells with n=40: 144/144 (saw 144)
- `hand_explain_openai_raw_5k_ef200`: **PASS** — hand node_types=['Limit', 'Sort', 'Bitmap Heap Scan', 'Bitmap Index Scan'] summary_first=['Limit', 'Sort', 'Bitmap Heap Scan', 'Bitmap Index Scan'] eval_id_hand=qst_0102::basic eval_id_first=qst_0102::basic

