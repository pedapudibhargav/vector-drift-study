# IEEE Access manuscript — Vector Retrieval Drift

**Venue:** IEEE Access (journal, research article) → [`access/`](access/)
**Public artifacts (cited in the paper):** https://pedapudibhargav.github.io/vector-drift-study/

- Manuscript: [`access/main.tex`](access/main.tex) → [`access/main.pdf`](access/main.pdf)
- Build: `cd access && ./build_pdf.sh` (pdflatex ×2 with the official `ieeeaccess.cls`)
- Local checks: `cd access && ./validate_access.sh` (abstract 150–250 words, 3–10 keywords, page count, fonts)
- Submission package: `cd access && ./build_latexqc_zip.sh` → `ieee_access_latexqc.zip` (passes the IEEE LaTeX Analyzer)
- Figures: [`figures/`](figures/), regenerated from published JSON by `scripts/erb/make_paper_figures.py`

## Consistency checks (run after any edit)

```bash
.venv/bin/python scripts/erb/verify_paper_numbers.py   # headline numbers vs sweep → VERIFY OK
python3 scripts/erb/verify_paper_tables.py             # every table vs artifacts → ALL TABLES MATCH
```

## Related study docs

- [`docs/STUDY_PROTOCOL.md`](../../docs/STUDY_PROTOCOL.md): frozen protocol and headline results
- [`docs/REPLICATE.md`](../../docs/REPLICATE.md): reviewer replication (restore the DB dumps)
- [`docs/HUMAN_AUDIT.md`](../../docs/HUMAN_AUDIT.md): L4 LLM-assisted audit and author spot-check
- [`docs/THREATS_TO_VALIDITY.md`](../../docs/THREATS_TO_VALIDITY.md): threats to validity
- [`artifacts/published/`](../../artifacts/published/): metrics JSON behind every table and figure
