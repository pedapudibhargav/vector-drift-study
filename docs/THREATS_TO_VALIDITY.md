# Threats to Validity

Mirrors Sec. VII of the IEEE Access manuscript (`papers/ieee-vector-drift/access/main.tex`).

## Internal validity

1. **Corpus construction.** Scale ranks pin gold-anchor documents first, then add stratified distractors (single seed, 42). Results could differ under random growth or reverse-pinning; we report the gold-first protocol as the operationally relevant enterprise case (answer documents stay indexed as the corpus grows). Multi-seed insertion orders are not claimed.
2. **Embedders.** Primary results use OpenAI `text-embedding-3-small` (d=1536). A secondary Amazon Titan Text Embeddings V2 arm (d=1024) replicates the decline on the same pins under identical HNSW settings. Two commercial API embedders do not cover open-weight or instruction-tuned models.
3. **Truncation.** Long documents were truncated differently per arm (11 OpenAI documents at 8,191 tokens; 90 Titan documents at a 24k-character cap, 5 of them gold anchors).
4. **Doc-level vectors.** One vector per `dsid_*` document (no multi-chunk passages). Drift estimates may understate passage-level RAG systems.
5. **Metadata filter.** The `meta` condition uses gold `source_type` as an oracle filter. This upper-bounds metadata rescue; production filters may be noisier.
6. **ANN recall.** Exact-cosine controls at 5k/50k/100k show most of the decline survives exact search (all of it for Titan; 0.210 of the 0.285 Hit@10 drop for OpenAI). Why the OpenAI HNSW index loses recall at large N while the Titan index does not was not isolated.

## External validity

1. **EnterpriseRAG-Bench is curated/synthetic.** Coefficients must be re-fit before transfer to proprietary corpora.
2. **English, text-only.** No multimodal or non-English claims.
3. **Single ANN stack.** pgvector HNSW (m=16, ef_construction=64, ef_search=200); other ANN libraries may behave differently.

## Construct validity

1. **Hit@k / Doc-Recall vs answer quality.** L1 metrics measure labeled document retrieval, not grounded answer correctness. L3 (LLM relevance judge) and L4 (LLM-assisted Hit@10-fairness audit with a 10-row author spot-check) are secondary corroboration only.
2. **Lexical baseline.** Okapi BM25 (`rank_bm25.BM25Okapi`, default k1=1.5, b=0.75) on truncated title+body text, not a tuned or field-weighted variant. Postgres FTS is kept only as a weak operational negative control.

## Statistical conclusion validity

1. **Sample size.** Primary bank n=200 unique eval IDs; percentile-bootstrap 95% CIs from the published sweep's per-question flags only (seed 42).
2. **Thresholds.** τ=0.10 is an operational threshold, not pre-registered; Titan's single late sub-τ point (+0.080 at 100k) is borderline.
3. **Small strata.** Question-type strata with small n (e.g., completeness n=6) are exploratory.
4. **Fits.** Log-linear fits use the nine planned ladder points only.
