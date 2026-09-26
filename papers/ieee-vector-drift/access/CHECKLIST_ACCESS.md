# IEEE Access camera-ready checklist (peer-review + format)

**Venue:** IEEE Access · **Local draft:** `access/main.tex` · **Quality notes:** `docs/PAPER_QUALITY_VERIFICATION.md`

## A — Scientific completeness (minimize peer pushback)

- [x] Clear RQs; gold-pinned protocol; frozen embedder/HNSW
- [x] Primary-200 full ladder through 100k; Hit@1/5/10, DocRecall, MRR
- [x] \(\Delta_{\mathrm{meta}}\), \(N^\star(\tau{=}0.10)\), log-linear fits
- [x] Bootstrap CIs from this sweep only; join semantics documented
- [x] Lexical baseline (partial ladder) as RQ2 control
- [x] L3 judge corroboration (secondary)
- [x] L4 Hit@10 fairness — LLM-assisted (`gpt-4o`, 62/62 high-priority `y`); see `artifacts/published/l4_hit_fairness_llm.md` + `L4_LLM_TRANSPARENCY.md` (disclose as secondary, not human)
- [x] Threats to validity + reproducibility URLs (Pages + GitHub)
- [x] Positioning vs coverage-scaling literature
- [x] Exact-search MVP control at N∈{5k,50k,100k} raw — `artifacts/published/exact_control_mvp.json`
- [ ] Thesaurus keyword confirmation on Author Portal (draft set in TeX + PACKAGING_SUBMISSION.md)

## B — Access submission package

- [x] Official `ieeeaccess.cls` + Formata fonts in `access/`
- [x] Author name, affiliation, email, bio — Independent Researcher; ORCID set
- [x] ORCID iD — https://orcid.org/0009-0002-8523-8415
- [x] Author photo `author.jpg` — 600×750 @ 300 dpi
- [x] Word twin **scaffold** `main_word_twin.docx` + official `IEEE_Access_Template_2024.docx` — **finish body match after PDF rebuild** (see PACKAGING_SUBMISSION.md)
- [x] Abstract 150–250 words (local validator OK after trim)
- [x] 4–6 keywords (confirm Thesaurus on portal)
- [ ] IEEE LaTeX Analyzer (https://latexqc.ieee.org/) on `ieee_access_latexqc.zip` — PDF eXpress needs a *conference* ID and does not apply to IEEE Access
- [ ] CrossCheck / similarity — **author login / portal**
- [x] AI disclosure in Acknowledgment (systems + sections + L3/L4)
- [x] M.S. biography line — Northwest Missouri State University, Maryville, MO, 2015
- [x] Page depth target 8–16 — rebuild PDF after latest TeX edits
- [x] Strict IEEE review artifact — `artifacts/published/IEEE_STRICT_REVIEW_2026.md`

## C — Local tools

```bash
cd papers/ieee-vector-drift/access
pdflatex main.tex && pdflatex main.tex
python3 validate_access.py --pdf main.pdf
chktex -q main.tex | head
```

## D — External validators (links)

See `docs/PAPER_QUALITY_VERIFICATION.md` (PDF eXpress, Paperpal, Author Center, Overleaf).
