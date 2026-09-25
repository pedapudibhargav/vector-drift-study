# IEEE Access manuscript

**Venue target:** IEEE Access (journal), **8–16 double-column pages**.  
**Overleaf template:** https://www.overleaf.com/latex/templates/ieee-access-latex-template/cdxrhtbjgszv  
**Official LaTeX zip (2026-05):** https://ieeeaccess.ieee.org/wp-content/uploads/2026/05/ACCESS_latex_template_20260513-1-1.zip  
**Official Word template:** `IEEE_Access_Template_2024.docx`

## Layout

| Path | Role |
|------|------|
| `main.tex` | Access manuscript with full-ladder findings |
| `figures/` | Symlink to shared IEEE figures |
| `validate_access.py` / `validate_access.sh` | Local pre-submission checks |
| `IEEEtran.cls` | Fallback class for drafting if `ieeeaccess.cls` missing |
| `IEEE_Access_Template_2024.docx` | Official Word shell (paste content for Author Portal) |

## Abstract / keywords (Access rules)

- Abstract: **150–250 words**, single paragraph, **no citations** (enforced by validator).
- Index terms: **4–6** Thesaurus-aligned keywords currently set to:  
  *Artificial intelligence, Databases, Information retrieval, Machine learning, Metadata, Search methods*  
  Confirm at https://www.ieee.org/publications/services/thesaurus.html or `keywords@ieee.org`.

## Local tooling

```bash
# Recommended (macOS)
brew install --cask mactex-no-gui   # provides pdflatex + chktex
brew install poppler               # pdfinfo, pdftotext, pdffonts

# Drop official Access class next to main.tex (browser download if CDN blocks curl)
# unzip ACCESS_latex_template_*.zip into this folder

./validate_access.sh
```

`chktex` is part of TeX Live / MacTeX (not a standalone Homebrew formula named `chktex` as of 2026).

## Compile notes

1. Prefer `ieeeaccess.cls` from the official zip (includes Access logo assets).  
2. Until then, `main.tex` auto-falls back to `\documentclass[journal]{IEEEtran}` with Access macro shims.  
3. Submit **matching** LaTeX (or Word) **and** PDF via IEEE Author Portal; file size ≤ 40 MB.

## Results source of truth

`artifacts/published/erb_full_primary200_to100k.json` + `_fit.json` (integrity-clean; **no N★** on ladder; Hit@10 ≈ 1.474 − 0.086 log N). See `CANONICAL_METRICS.json`.
