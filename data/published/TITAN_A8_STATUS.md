# A8 Second Embedder — Amazon Titan Text Embeddings V2 Status

**Status:** complete (2026-09-23)

## Corpus parity

| Arm | Table | Rows | Under `scale_rank < 100k` | Gold anchors |
|-----|-------|------|---------------------------|--------------|
| OpenAI | `document_chunks` | 103033 | **99998** | 627 |
| Titan | `document_chunks_titan` | 99998 | **99998** | 627 |

- All Titan `doc_id`s ⊆ OpenAI; OpenAI-only rows are `scale_rank ≥ 100000` (3035 distractors beyond the ladder).
- `scale_rank` / `source_type` / `is_gold_anchor` aligned to OpenAI (`migrate_titan_results_schema.py`).
- Shared rank holes under 100k: `38706`, `89113` (same on both arms).
- 90 docs truncated to 24k chars for Titan input limit (same `doc_id`, shorter `chunk_text`).

## Ladder

Same scales as OpenAI: `5k, 10k, 15k, 20k, 25k, 40k, 50k, 75k, 100k` × `{raw, meta}` × primary-200.

- Sweep JSON: `artifacts/published/erb_titan_primary200_to100k.json`
- Compare: `artifacts/published/openai_vs_titan_primary200.json`
- DB: `experiment_runs_titan` + `vector_drift_results_titan` (18 runs × 200 rows)

## Drift replication (5k → 100k raw)

| Metric | OpenAI Δ | Titan Δ | Replicates |
|--------|----------|---------|------------|
| Hit@1 | −0.295 | −0.235 | yes |
| Hit@5 | −0.280 | −0.165 | yes |
| Hit@10 | −0.285 | −0.175 | yes |
| MRR | −0.293 | −0.206 | yes |

**all_three_replicate = true** (Hit@1, Hit@10, MRR).

Titan absolute Hit@10 stays ~0.09–0.11 above OpenAI after 5k; slope is milder.

## UI

- `/compare` — OpenAI vs Titan ladder + endpoint table
- `/corpus` — embedder toggle (OpenAI / Titan tables)
- API: `/api/metrics/vector-drift?embedder=titan`, `/api/metrics/openai-vs-titan`

## Exact-cosine control (2026-09-23)

`exact_control_titan.json` — Titan exact search at 5k/50k/100k returns **identical top-10 lists** to Titan HNSW for 200/200 questions (Δ = 0, 0 disagreements). OpenAI HNSW, by contrast, loses 0.085/0.075 Hit@10 vs exact at 50k/100k.

## Paired bootstrap (B=5000, seed 42) — `openai_vs_titan_bootstrap.json`

| 5k→100k drop | HNSW: Titan − OpenAI | Exact: Titan − OpenAI |
|---|---|---|
| Hit@10 | +0.110 [0.040, 0.175] | +0.035 [−0.025, 0.100] |
| Hit@1 | +0.060 [−0.015, 0.135] | +0.025 [−0.050, 0.100] |
| MRR | +0.087 [0.030, 0.142] | +0.043 [−0.008, 0.092] |

**Correction to the earlier reading:** "Titan drifts less" holds only on the deployed HNSW curves. Under exact search the two embedders' drops are statistically indistinguishable; most of the gap is ANN recall loss in the OpenAI index.

## Δmeta is embedder-dependent

Titan Δmeta (Hit@10): 0.085, 0.070, 0.075, 0.095, 0.095, 0.115, 0.105, 0.100, 0.080 — below τ=0.10 at 6/9 points; sustained N* = 100k (borderline). OpenAI: sustained N* undefined.

## Truncation (both arms)

- OpenAI: 8,191-token cap → 11 docs truncated.
- Titan: 24k-char client-side cap (Titan limit is 8,192 tokens / 50,000 chars) → 90 docs truncated, 5 gold anchors.
