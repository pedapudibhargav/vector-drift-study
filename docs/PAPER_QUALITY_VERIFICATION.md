# Paper quality verification — end-goal checklist

**Venue (primary):** IEEE Access (official `ieeeaccess.cls` from ACCESS LaTeX template 2026-05-13).  
**Artifacts / replication site:** https://pedapudibhargav.github.io/vector-drift-study/  
**GitHub repo:** https://github.com/pedapudibhargav/vector-drift-study  
**Local Access draft:** `papers/ieee-vector-drift/access/main.tex`  
**Local validators:** `papers/ieee-vector-drift/access/validate_access.py`

This note stores the **submission-quality bar** so we can drive the manuscript and tooling toward peer-review readiness (target: minimize desk-reject and formatting/integrity pushback).

---

## 1. Official IEEE templates & author hubs

| Resource | URL | Use |
|----------|-----|-----|
| IEEE Author Center (template hub) | https://journals.ieeeauthorcenter.ieee.org/ | Official article templates tool; download IEEEtran / Access Word+LaTeX packages |
| IEEE Access site — Authors | https://ieeeaccess.ieee.org/authors/ | Manuscript types, ORCID, AI disclosure, bios |
| IEEE Access — Submission guidelines | https://ieeeaccess.ieee.org/authors/submission-guidelines/ | Checklist (Word+LaTeX+PDF match, keywords 3–10, &lt;20 pages recommended) |
| IEEE Access — Preparing your article | https://ieeeaccess.ieee.org/authors/preparing-your-article/ | Pre-submission prep |
| Official Access LaTeX zip (2026-05) | https://ieeeaccess.ieee.org/wp-content/uploads/2026/05/ACCESS_latex_template_20260513-1-1.zip | Camera-ready class + fonts (local copy: `Downloads/ACCESS_latex_template_20260513`) |
| Overleaf gallery (IEEE-tagged) | https://www.overleaf.com/gallery/tagged/ieee | Online compile without local TeX |
| Overleaf Access template | https://www.overleaf.com/latex/templates/ieee-access-latex-template/cdxrhtbjgszv | Pre-wired `ieeeaccess.cls` |

---

## 2. Format / PDF validators (must pass before final upload)

| Tool | URL / install | What it checks |
|------|---------------|----------------|
| **IEEE PDF eXpress®** | https://ieee-pdf-express.org/ | Required Xplore PDF spec: font embedding, margins, color space; produces Pass/Fail report |
| LaTeX Workshop (VS Code/Cursor) | Extension marketplace | Live compile, cross-refs vs Access/IEEEtran class |
| **ChkTeX / Lacheck** | `chktex` (TinyTeX / TeX Live) | Typographic lint (cite spacing, caption style, math) |
| Local Access gate | `python3 papers/ieee-vector-drift/access/validate_access.py` | Abstract 150–250w, 4–6 keywords, page band warn, fonts |
| Paperpal Preflight (Access-linked) | https://preflight.paperpal.com/partner/ieee/access | Grammar / language before submission |
| Vale / Grammarly | CLI or app + IEEE-ish style rules | Passive style, abbreviations, passive voice (advisory) |

**Local toolchain already present:** TinyTeX (`pdflatex`), `chktex`, poppler (`pdfinfo` / `pdftotext` / `pdffonts`).

---

## 3. Plagiarism & integrity

| Tool | Notes |
|------|-------|
| IEEE CrossCheck / iThenticate | All submissions screened. Target similarity **&lt;10–12%** excluding references and standard equations |
| AI-generated text policy | Disclose in Acknowledgments; cite AI system for generated sections ([IEEE AI text policy](https://journals.ieeeauthorcenter.ieee.org/become-an-ieee-journal-author/publishing-ethics/guidelines-and-policies/submission-and-peer-review-policies/#ai-generated-text)) |
| Authorship / ORCID | Submitting author needs populated public ORCID; bios required for all authors in Access template |

---

## 4. Scientific peer-review bar (content, not formatting)

Drive toward **&gt;95% confidence of surviving peer review** (not a guarantee—reviewers vary):

| Area | Status / action |
|------|-----------------|
| Reproducible ladder + frozen protocol | Done — `docs/STUDY_PROTOCOL.md`, seed 42, HNSW frozen |
| Primary-200 full ladder metrics + fits + \(N^\star\) | Done — `artifacts/published/erb_full_primary200_to100k*.json` |
| Bootstrap CIs from this sweep only | Done — documented; join semantics called out |
| Lexical baseline | Partial (5k–25k); extend or mark limitation |
| L3 LLM judge | Done (n=40, corroboration only) |
| L4 Hit@10 fairness | LLM-assisted (`gpt-4o`, 62 high-pri rows, 62/62 `y`); disclose secondary — `l4_hit_fairness_llm.*` |
| Exact-search ANN control | **Placeholder / future work** |
| Second embedder | Optional; do not over-claim single-embedder generality |
| Related-work positioning vs coverage scaling | In Access draft; keep contrast sharp |
| Threats to validity | Present; keep honest |
| Public artifacts + restoreable dump | Site + GitHub; dump on Releases (~1 GB) |

---

## 5. Manuscript submission package (Access)

1. LaTeX source matching PDF **exactly**  
2. Word twin (from official Access `.docx` template) — **still TODO**  
3. PDF that passes **PDF eXpress**  
4. Keywords (Thesaurus-aligned preferred)  
5. Author bios + ORCID  
6. Supplementary: published JSON, audit worksheets, dump link  

---

## 6. Related internal docs

- Protocol: [STUDY_PROTOCOL.md](STUDY_PROTOCOL.md)  
- Replication: [REPLICATE.md](REPLICATE.md)  
- Human audit: [HUMAN_AUDIT.md](HUMAN_AUDIT.md)  
- Threats: [THREATS_TO_VALIDITY.md](THREATS_TO_VALIDITY.md)  
- Verification UI + static hosting options: [VERIFICATION_UI_AND_STATIC_HOSTING.md](VERIFICATION_UI_AND_STATIC_HOSTING.md)  
- Literature notes: `papers/ieee-vector-drift/LITERATURE_2025_2026.md`  
