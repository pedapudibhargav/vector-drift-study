# Threats to Validity (paper §)

Draft language for the camera-ready paper. Expand after full ladder + human audit.

## Internal validity

1. **Corpus construction.** Scale ranks pin gold-anchor documents first, then add stratified distractors (seed 42). Results could differ under random growth or reverse-pinning; we report the gold-first protocol as the operationally relevant enterprise case (must keep answer docs as the corpus grows).
2. **Single embedding model.** Primary results use `text-embedding-3-small`. Cross-model generalization is not claimed until A8 (optional second embedder).
3. **Doc-level vectors.** One vector per `dsid_*` document (no multi-chunk passages). Drift estimates may understate passage-level RAG systems.
4. **Metadata filter.** The `meta` condition uses gold `source_type` as an oracle-style filter. This upper-bounds metadata rescue; production filters may be noisier.

## External validity

1. **EnterpriseRAG-Bench is synthetic / curated.** Label quality and question distribution may not match proprietary enterprise corpora.
2. **English, text-only.** No multimodal or non-English claims.
3. **HNSW ANN.** Approximate search (m=16) can miss true neighbors; we treat this as the deployed retrieval stack, not exact cosine.

## Construct validity

1. **Hit@k / Doc-Recall vs answer quality.** L1 metrics measure document retrieval, not grounded answer correctness. L3 (gpt-4o-mini) and L4 (human audit) are secondary checks only.
2. **Lexical baseline.** Postgres `ts_rank_cd` + `plainto_tsquery` is a strong industrial FTS baseline, not tuned BM25 with field weights.

## Statistical conclusion validity

1. **Primary-200 + full-462.** Main tables use stratified n=200; appendix repeats on all eligible questions (~462). Bootstrap / Wilson 95% CIs reported on Hit@10.
2. **Multiple scales.** Fitting \(a - b\log N\) uses the planned ladder only; do not include accidental full-corpus points outside the ladder.
