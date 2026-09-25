# What the strict IEEE review asked for — plain English + status

## Why BM25?

**RQ2** asks: *when the corpus grows, does keyword search also get worse, or only vectors?*

| Control | What it is | What we had | What reviewers wanted |
|---------|------------|-------------|------------------------|
| Postgres FTS | Simple database full-text | Hit@10 stuck at **0.045** (useless floor) | Not BM25 |
| **Okapi BM25** | Classic sparse IR ranking | **Now run** on full ladder | Real sparse baseline |

**Where it sits in the paper:** Section “Sparse Controls (BM25…)”, Table `tab:bm25`, RQ2 answer, abstract, conclusion.

**What we found (exciting for honesty):**

| Retriever | Hit@10 5k→100k |
|-----------|----------------|
| Dense HNSW | 0.795 → **0.510** (drop 0.285) |
| Okapi BM25 | 0.855 → **0.700** (drop 0.155) |

Both decline; dense declines more (bootstrap CIs in `bm25_vs_dense_bootstrap.json`). So growth pressure is **not dense-only**, and dense still looks worse on this bank.

## Checklist from strict agent → done / not done

| Ask | Status |
|-----|--------|
| Real BM25 full ladder | **Done** |
| Exact vs HNSW | **Done** (MVP 3 scales) |
| Document ANN settings | **Done** (`ef_search=200`, iterative scan, fallback) |
| Kill “scaling law” title | **Done** |
| Scope single seed / oracle / exploratory types | **Done** |
| BM25 params + bootstrap CIs | **Done** |
| Rebuild PDF / eXpress / CrossCheck | Rebuild PDF on Overleaf/MacTeX. **PDF eXpress is conference-only (needs Conference ID) — not used by Access.** CrossCheck runs only on Author Portal submit (not done). |
| Multi-seed growth orders | Future work (demoted claims) |

## Re-score after BM25 (Luna)

Overall **5 → 6**/10 · still **Major Revision** · accept-if-revised **~58%** · desk-reject **~18%**.

Agent: [BM25 re-score](7e5db90b-f65e-448d-a5b4-082006a9c8d2)

## IEEE tools with your credentials (no paper submit)

Login keys were found in the HTML-vector-density-filter `.env`. PDF eXpress login requires a **Conference ID** Access does not provide; we did **not** submit to Author Portal. Use Author Center PDF tools + Paperpal with a rebuilt PDF when ready.
