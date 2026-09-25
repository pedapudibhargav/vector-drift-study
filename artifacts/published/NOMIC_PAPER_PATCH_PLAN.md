# Paper patch plan — A8 nomic-embed-text (do not edit `main.tex` yet)

Apply only after `erb_ollama_primary200_to100k.json` exists and
`compare_openai_vs_nomic.py` reports `status: complete`.

Source of truth for numbers: `artifacts/published/openai_vs_nomic_primary200.json`.

---

## 1. Abstract (`main.tex` L37–38)

**Current:** Single embedder (`text-embedding-3-small`); no cross-model claim.

**Patch:**
- Add one sentence after BM25 sentence: secondary 768-d local embedder (`nomic-embed-text`) on the same ladder **[does / does not]** replicate raw endpoint decline (Hit@10 $X{\to}Y$).
- Keep primary claims OpenAI-first; nomic is corroboration only.

---

## 2. Introduction — Research questions (L56–61)

**Current:** RQ1–RQ3 only (dense drift, BM25, metadata rescue).

**Patch:**
- Optional **RQ4** (or footnote): Does rank erosion replicate under a second frozen embedder?
- Or extend RQ1 parenthetical: “…under the primary OpenAI embedder, with nomic-embed-text as secondary confirmation.”

---

## 3. Introduction — Contributions bullet (L65)

**Current:** “frozen embedder/ANN settings” (singular).

**Patch:**
- Split: primary arm = OpenAI + HNSW; secondary arm = Ollama nomic (768-d, exact scan on `document_chunks_ollama`).
- Add bullet: “Secondary embedder confirmation on the same gold-pinned ladder (Appendix~\ref{app:nomic}).”

---

## 4. Experimental Setup — Indexing (L141–144)

**Current:** “Primary claims use a single embedder; cross-model generalization is not asserted.”

**Patch:**
- Replace with two-tier wording:
  - Primary: OpenAI `text-embedding-3-small`, HNSW as now.
  - Secondary (A8): `nomic-embed-text` via Ollama, separate pgvector table, same `scale_rank` predicate — **report whether drift direction replicates**, not universal law.
- Note ANN parity caveat if ollama arm stays exact-scan.

---

## 5. Results — new subsection (after L185 or after BM25 subsection)

**Add:** `\subsection{Secondary embedder (nomic-embed-text)}`
- Table: raw Hit@1/5/10, MRR at 5k and 100k for OpenAI vs Nomic.
- One paragraph: endpoint deltas; `drift_replication.raw.all_three_replicate` from compare JSON.
- If meta fixed: brief $\Delta_{\mathrm{meta}}$ comparison; else “meta omitted pending filter parity fix.”

---

## 6. Discussion — Implications (L388–396)

**Patch item (2)** (L390): Already says re-estimate when embedders change — add forward pointer: “We provide one such re-estimate in Appendix~\ref{app:nomic}.”

---

## 7. Threats to Validity — Internal (L400–401)

**Current:** “A single embedder … intentional controls, not claims of universality.”

**Patch:**
- Soften to: “Primary claims use OpenAI; a secondary local embedder (nomic-embed-text) tests whether endpoint decline replicates on the same bank.”
- Retain caveat: different dimensionality, training data, and ANN path (exact vs HNSW).

---

## 8. Threats — External validity (L403–404)

**Patch:** Add sentence: secondary embedder is English text / same ERB corpus only; does not establish multimodal or proprietary-stack transfer.

---

## 9. Conclusion (L419–420)

**Current:** “cross-embedder generality … are not claimed. Future work includes … multi-embedder confirmation.”

**Patch:**
- If replication holds: “A secondary nomic-embed-text arm on the same ladder **[replicates / partially replicates]** raw endpoint decline (Hit@10 …), supporting directionality while magnitudes remain stack-specific.”
- Update future-work line: remove or narrow “multi-embedder confirmation” if A8 completes.

---

## 10. Reproducibility (L414–416)

**Patch:** List new artifacts:
- `erb_ollama_primary200_to100k.json`
- `openai_vs_nomic_primary200.json`
- `NOMIC_A8_STATUS.md`
- Ollama ingest checkpoint / restore notes for `document_chunks_ollama`

---

## 11. New appendix

**Add:** `\section{Secondary embedder ladder}\label{app:nomic}`
- Full per-scale table (raw; meta if fixed).
- Figure optional: overlay Hit@10 vs $\log N$ (OpenAI vs Nomic).
- Protocol delta table (768-d, exact scan, local Ollama).

---

## 12. Figures / bibliography

- **Fig. 1** (`fig1_hit_vs_logN.png`): optional third curve for nomic raw Hit@10.
- **No new citation required** unless citing nomic model card; optional `\cite{nomic2024}` if added to `.bib`.

---

## Numbers to paste (TBD placeholders)

| Slot | OpenAI (canonical) | Nomic (TBD) |
|------|-------------------|-------------|
| Raw Hit@10 @ 5k | 0.795 | ___ |
| Raw Hit@10 @ 100k | 0.510 | ___ |
| Raw Hit@1 @ 5k → 100k | 0.600 → 0.305 | ___ |
| Raw MRR @ 5k → 100k | 0.658 → 0.365 | ___ |
| Drift replicates? | (reference) | ___ |

Run `python scripts/erb/compare_openai_vs_nomic.py` to fill the Nomic column and replication flags.
