# Word twin packaging

## Status
- `main_word_twin.docx` — **scaffold** (title/abstract/author/keywords + finish instructions)
- `IEEE_Access_Template_2024.docx` — official Access Word template (keep)

## Why not auto-complete?
Access requires Word **or** LaTeX **plus** PDF with **exact content match**. Full body auto-conversion without a matching rebuilt PDF would create a false twin.

## Finish (author)
1. Rebuild PDF: `pdflatex main.tex` twice (MacTeX) or Overleaf Access template.
2. Prefer LaTeX + PDF on Author Portal when accepted.
3. If Word required: copy body into `IEEE_Access_Template_2024.docx`, save as `main.docx`, verify vs PDF.
4. See `PACKAGING_SUBMISSION.md`.
