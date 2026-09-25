# Ready-for-you: Access packaging status (no portal submit)

Updated after BM25 confirmation + Luna grammar pass.

## 1. BM25 — yes, full ladder

Same 9 corpus sizes as dense: **5k, 10k, 15k, 20k, 25k, 40k, 50k, 75k, 100k**.  
Per scale metrics: **Hit@1, Hit@5, Hit@10, MRR, DocRecall** (+ per-question ranks).

| N | Hit@1 | Hit@5 | Hit@10 | MRR |
|---|------:|------:|-------:|----:|
| 5k | 0.740 | 0.810 | 0.855 | 0.772 |
| 10k | 0.695 | 0.790 | 0.815 | 0.732 |
| … | … | … | … | … |
| 100k | 0.510 | 0.660 | 0.700 | 0.575 |

Artifact: `artifacts/published/erb_bm25_baseline_primary200.json`

## 2. Tools already used (science / integrity)

| Tool / gate | Status |
|-------------|--------|
| L1 integrity-clean ladder | Done |
| Exact cosine MVP | Done |
| Okapi BM25 full ladder | Done |
| L4 LLM + human spot-check | Done |
| `verify_paper_numbers.py` | Done |
| Local `validate_access.py` | **ACCESS_GATE=OK** |
| Luna grammar pass | Done → `GRAMMAR_PASS_REPORT.md` |
| Strict IEEE re-score | Overall 6/10 (Major Revision) |

## 3. What still needs *you* (cannot fake without submit)

| Step | Why |
|------|-----|
| **Rebuild `main.pdf`** | **Done** (Sep 22) — TinyTeX at `~/Library/TinyTeX`; run `./build_pdf.sh` in `papers/ieee-vector-drift/access/` |
| Paperpal / Author Center PDF tools | Upload the **new** PDF after rebuild |
| CrossCheck | Runs on Author Portal **submit** only |
| PDF eXpress | **Conference** tool (needs Conference ID) — **not** Access journal pre-check |
| Author Portal draft/submit | **Not done** — say when you want draft upload |

### Overleaf rebuild (recommended)

1. New Overleaf project → upload Access LaTeX zip from ieeeaccess.ieee.org (May 2026 zip).  
2. Replace with our `papers/ieee-vector-drift/access/` contents (`main.tex`, `author.jpg`, cls/fonts as needed).  
3. Compile **twice**. Download PDF.  
4. Diff-check abstract/title/BM25 table vs TeX.  
5. Optional: Author Center → validate PDF; Paperpal for grammar.

## 4. Git / commits

**Current work is NOT committed** — large dirty tree on `feature/l4-audit-review` (papers, artifacts, BM25, review UI, etc.).

Recent commits are authored by **pedapudibhargav**, not Cursor.

**Is “Cursor” in a commit OK?**  
- **Author name should be you** (it is).  
- Optional `Co-authored-by: Cursor` trailers are fine for git history but **do not replace** IEEE Acknowledgment AI disclosure.  
- Don’t list Cursor as a paper author.

Say if you want a curated commit of the paper+artifacts (we will not commit secrets / `.env`).
