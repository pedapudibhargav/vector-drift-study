# IEEE Access packaging — what is done vs what needs your login

Strict reviewer (Luna, Sep 2026 norms): [IEEE Access review](74c5eb97-300f-444b-9b33-5ece82fa54b1)  
Official checklist: https://ieeeaccess.ieee.org/authors/submission-guidelines/

## Done in-repo

| Item | Status |
|------|--------|
| Abstract length 150–250 | **OK** (trimmed; local `validate_access.py` gate OK) |
| Title narrowed (no “Scaling Laws”) | Done |
| RQ2 matched to Postgres FTS (not fake BM25) | Done |
| AI disclosure (systems + sections + responsibility) | Strengthened in Acknowledgment |
| ORCID + bio + author photo | Already present |
| Keywords (6) | Present — confirm Thesaurus on portal |
| Word twin scaffold | `access/main_word_twin.docx` + `IEEE_Access_Template_2024.docx` |
| Exact control + L4 spot-check in Methods/Results | Done |

## Requires you (IEEE / tooling accounts)

### 1. Rebuild PDF (blocking for twin match)
`main.pdf` on disk may lag `main.tex` until you rebuild:

- **Overleaf:** upload Access LaTeX zip + `main.tex` / figures / `author.jpg`, compile twice, download PDF.
- **Local:** `brew install --cask mactex-no-gui` then `pdflatex main.tex && pdflatex main.tex`.

### 2. PDF eXpress
1. IEEE PDF eXpress: https://ieee-pdf-express.org/  
2. Use conference/journal ID from Access Author Portal instructions.  
3. Upload final PDF → fix any font/embed issues → keep Pass certificate.

### 3. CrossCheck / similarity
1. Author Portal runs CrossCheck (iThenticate) on submit, **or**  
2. Self-check with institutional iThenticate if available.  
3. Expect overlap on methods boilerplate / shared equations — paraphrase and cite; remove copied abstract text from arXiv preprints if any.

### 4. Thesaurus / portal keywords
On submission select **3–10** keywords aligned with IEEE Thesaurus (portal search). Current draft set:

`Information retrieval, Nearest neighbor searches, Semantic search, Metadata, Vectors, Benchmark testing` (matches main.tex)

### 5. Word twin (if portal insists)
Prefer **LaTeX + matching PDF**. If Word required: paste full body into `IEEE_Access_Template_2024.docx`, insert photo, match PDF page-by-page. `main_word_twin.docx` is only a scaffold.

### 6. Paperpal Preflight (grammar)
https://ieeeaccess.ieee.org/ — Preparing Your Article → Paperpal. Fix grammar flags before submit (Access desk-rejects poor grammar).

## Manuscript type
Select **Research Article** (or **Applied Research** if you want ops framing). Do **not** select Survey/Review.
