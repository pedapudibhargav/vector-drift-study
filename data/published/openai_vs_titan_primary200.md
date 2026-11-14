# OpenAI vs Titan embedder (primary-200)

A8 second-embedder arm: Amazon Titan Text Embeddings V2 vs OpenAI on the same gold-pinned ladder.

- OpenAI: `artifacts/published/erb_full_primary200_to100k.json` (text-embedding-3-small)
- Titan: `artifacts/published/erb_titan_primary200_to100k.json` (amazon.titan-embed-text-v2:0)
- Shared scales: [5000, 10000, 15000, 20000, 25000, 40000, 50000, 75000, 100000]

## Drift replication (5k → 100k endpoints)

- Raw Hit@10 replicates: **True**
- Raw Hit@1 replicates: **True**
- Raw MRR replicates: **True**
- All three raw metrics replicate: **True**

Endpoint decline replicates when both OpenAI and Titan show negative delta (100000 minus 5000) for the metric.

## Endpoint table (raw)

| Metric | OpenAI 5k | OpenAI 100k | Δ | Titan 5k | Titan 100k | Δ | Replicates |
|---|---:|---:|---:|---:|---:|---:|:---:|
| hit_at_1 | 0.600 | 0.305 | -0.295 | 0.620 | 0.385 | -0.235 | True |
| hit_at_5 | 0.740 | 0.460 | -0.280 | 0.730 | 0.565 | -0.165 | True |
| hit_at_10 | 0.795 | 0.510 | -0.285 | 0.785 | 0.610 | -0.175 | True |
| mrr | 0.658 | 0.365 | -0.293 | 0.671 | 0.465 | -0.206 | True |

## Per-scale raw Hit@10

| N | OpenAI | Titan | Δ (T−O) |
|---:|---:|---:|---:|
| 5000 | 0.795 | 0.785 | -0.010 |
| 10000 | 0.660 | 0.755 | 0.095 |
| 15000 | 0.625 | 0.735 | 0.110 |
| 20000 | 0.600 | 0.700 | 0.100 |
| 25000 | 0.590 | 0.695 | 0.105 |
| 40000 | 0.565 | 0.650 | 0.085 |
| 50000 | 0.555 | 0.645 | 0.090 |
| 75000 | 0.515 | 0.615 | 0.100 |
| 100000 | 0.510 | 0.610 | 0.100 |
