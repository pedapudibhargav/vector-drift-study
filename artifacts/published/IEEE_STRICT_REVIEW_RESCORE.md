# IEEE strict review — after BM25 + fixes (re-score)

**Agent:** Luna `gpt-5.6-luna-medium` · ID `7e5db90b-f65e-448d-a5b4-082006a9c8d2`  
**Previous overall:** 5/10 → **Now: 6/10**  
**Recommendation:** still Major Revision (Access binary ≈ Reject+resubmit)  
**Accept if revised:** ~58% · **Desk-reject risk:** ~18%

## Score table

| Dimension | Before | After BM25 pack |
|-----------|-------:|----------------:|
| Novelty | 5 | 6 |
| Technical soundness | 6 | 6 |
| Experimental design | 5 | 6 |
| Clarity | 7 | 7 |
| Reproducibility | 7 | 6* |
| Significance | 5 | 6 |
| **Overall** | **5** | **6** |

\*Reproducibility dipped slightly pending BM25 param docs / PDF package — params now recorded in JSON.

## What improved (agent)

- Real Okapi BM25 full ladder (not FTS-as-BM25)
- Exact cosine MVP already present
- ANN config documented
- Claims scoped; title fixed; AI disclosure clearer

## IEEE portal tools (no paper submit)

| Tool | Result |
|------|--------|
| Local `validate_access.py` | **ACCESS_GATE=OK** |
| PDF eXpress | **N/A for Access journal** — tool needs a *conference* ID; Access uses Author Portal + matching LaTeX/Word+PDF |
| CrossCheck | Runs **on Author Portal submit** — cannot run without submitting |
| Paperpal | Link from Access “Preparing Your Article” / Author Center — needs rebuilt PDF upload by author |
| Author Portal submit | **Not done** (per your request) |

IEEE login credentials were available but **cannot complete PDF eXpress** without a conference ID (Access is not enrolled that way).

## Plain-English fix guide

See `IEEE_FIXES_PLAIN_ENGLISH.md`.
