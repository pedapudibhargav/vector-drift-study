# Strict IEEE Access review (Sep 2026 norms) — agent report

**Agent:** Cursor Task `gpt-5.6-luna-medium` (strict AE/reviewer persona)  
**ID:** `74c5eb97-300f-444b-9b33-5ece82fa54b1`  
**Plus:** Official Access submission guidelines (fetched Sep 2026)

## How Access reviewing works (synthesized + official)

- **Binary decision:** Accept or Reject (with/without resubmission encouragement). Reviewer language of “Major Revision” maps to **Reject — resubmit allowed** in Access’s binary system.
- **≥2 independent reviewers**, single-anonymized; AE makes final call.
- **Prescreen:** scope, quality, duplicate submission, PPL; then AE triage.
- **Must:** Access template; **LaTeX or Word + PDF exact match**; ORCID; bios for all authors; AI disclosure in Acknowledgments (system + sections + extent); 3–10 keywords; grammar OK (Paperpal offered).
- **AI:** Disclose AI-generated content; AI not an author; reviewers must not paste manuscripts into public AI tools.
- **Kill shots for this genre:** single stack sold as universal law; weak “BM25” that isn’t; oracle filters as production; missing exact/ANN docs; overclaimed scaling laws; packaging gaps.

## Scores (1–10) — harsh

| Dimension | Score |
|-----------|------:|
| Novelty | 5 |
| Technical soundness | 6 |
| Experimental design | 5 |
| Clarity | 7 |
| Reproducibility | 7 |
| Significance | 5 |
| **Overall** | **5** |

**Recommendation:** Major Revision (Access: Reject with resubmit)  
**Accept if revised (agent):** ~55%  
**Desk-reject risk if packaging incomplete:** still material

## What is already strong

Integrity-clean L1; membership Hit@k; exact cosine still declines 0.795→0.585; HNSW gap quantified; oracle Δ_meta honest; L4 not oversold; 9/10 human spot-check; stack-scoped claims.

## Major issues (priority)

1. Novelty / “scaling law” framing → **title already retitled**; keep “trend fits” language.
2. Single gold-first seed → demote operational claims or add seeds (future).
3. n=200 + type claims → keep exploratory labels on thin strata.
4. Oracle metadata → already upper-bound language; keep loud.
5. RQ2 BM25 mismatch → **RQ2 rewritten** to Postgres FTS negative control.
6. ANN config completeness → document ef_search / fallback (future polish).
7. Scaling-law statistics → descriptive fits only (done).
8. Gold adequacy / label noise → disclose spot-check unsure (done).
9. Reproducibility manifest polish → ongoing.

## Applied already from this review

- Title without “Scaling Laws”
- Abstract ≤250 words + exact control sentence
- RQ2/RQ3 honest wording
- Stronger AI Acknowledgment (systems + sections)
- Packaging guide for eXpress / CrossCheck / Word / Paperpal

## Still needs author action

Rebuild PDF · PDF eXpress Pass · CrossCheck · Thesaurus confirm · finish Word if required · Paperpal.
