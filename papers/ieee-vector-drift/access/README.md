# IEEE Access manuscript (LaTeX)

**Venue:** IEEE Access (journal). Official template: [ACCESS LaTeX template, May 2026](https://ieeeaccess.ieee.org/wp-content/uploads/2026/05/ACCESS_latex_template_20260513-1-1.zip)
(also on [Overleaf](https://www.overleaf.com/latex/templates/ieee-access-latex-template/cdxrhtbjgszv)).

## Layout

| Path | Role |
|------|------|
| `main.tex` | Manuscript (bibliography is inline `thebibliography`, numbered by first citation) |
| `main.pdf` | Compiled manuscript |
| `ieeeaccess.cls`, `spotcolor.sty`, `t1*` fonts, logos | Official IEEE Access class files |
| `IEEEtran.cls`, `IEEEtran.bst` | Base class used by `ieeeaccess.cls` |
| `figures/` | Symlink to `../figures` (vector PDFs from `scripts/erb/make_paper_figures.py`) |
| `author.jpg` | Author photo for the biography |
| `build_pdf.sh` | pdflatex ×2 + local validation |
| `build_latexqc_zip.sh` | Builds `ieee_access_latexqc.zip` (source + class + figures) for the IEEE LaTeX Analyzer and Author Portal |
| `validate_access.py` / `validate_access.sh` | Local checks: abstract 150–250 words, 3–10 keywords, pages, fonts |

## Abstract / keywords (IEEE Access rules)

- Abstract: 150–250 words, single paragraph, no citations.
- Keywords (3–10), all preferred terms in the January 2026 IEEE Thesaurus:
  *Benchmark testing, Information retrieval, Metadata, Nearest neighbor methods, Retrieval augmented generation, Scalability, Semantic search*.

## Local tooling

```bash
# Lightweight (macOS, ~250 MB): TinyTeX — build_pdf.sh finds it automatically
curl -sL "https://yihui.org/tinytex/install-bin-unix.sh" | sh
# or the full distribution (~7 GB): brew install --cask mactex-no-gui
brew install poppler               # pdfinfo, pdftotext, pdffonts

./build_pdf.sh && ./build_latexqc_zip.sh
```

The build currently has **0 LaTeX warnings**. The only overfull box comes from the class's own title-block logo; IEEE's blank template produces the same one.

## Results source of truth

`artifacts/published/erb_full_primary200_to100k.json` + `_fit.json` (OpenAI), `erb_titan_primary200_to100k.json` (Titan), `exact_control_*.json`, `openai_vs_titan_bootstrap.json`, `erb_bm25_baseline_primary200.json`.
`scripts/erb/verify_paper_numbers.py` and `scripts/erb/verify_paper_tables.py` check the manuscript against them.
