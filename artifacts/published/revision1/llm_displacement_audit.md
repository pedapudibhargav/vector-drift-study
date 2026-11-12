# LLM displacement relevance audit (revision 1, G3)

Generated: 2026-11-11T06:51:24Z

## Setup
- Provider: `cursor`; model: `gpt-4o`
- Displaced |M| (full): **42**; judged sample: **42**
- Planned items: `{"displacer": 42, "competitor5k": 42, "gold_control": 30, "random_control": 15, "total": 129}`

## Prompt template
```
You are a strict relevance judge for enterprise RAG evaluation.

Question:
{question}

Document (standalone; no metadata beyond this text):
{document}

Does this document BY ITSELF contain the information needed to answer the question?

Respond with JSON only (no markdown):
{{"answers": "yes" | "partial" | "no", "reason": "<=40 words"}}
```

## Category relevance (Wilson 95% on yes+partial unless noted)

| category | n | yes | partial | no | yes+partial share | Wilson 95% |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| displacer | 42 | 2 | 4 | 36 | 0.1429 | 0.0672–0.2784 |
| competitor5k | 42 | 0 | 3 | 39 | 0.0714 | 0.0246–0.1901 |
| gold_control | 30 | 20 | 7 | 3 | 0.9 | 0.7438–0.9654 |
| random_control | 15 | 0 | 0 | 15 | 0.0 | 0.0–0.2039 |

## Comparisons
- Displacer yes+partial: **0.1429**
- Competitor@5k yes+partial: **0.0714**
- Random control yes+partial: **0.0**
- McNemar paired: `{"n_pairs": 42, "b_displacer_rel_competitor_not": 4, "c_competitor_rel_displacer_not": 1, "mcnemar_chi2_with_continuity": 0.8, "note": "McNemar-style discordant counts on same displaced questions (yes+partial=relevant)"}`

## Calibration (gold control)
- Gold `yes` share: **0.6667** (Wilson [0.4878, 0.8077])

## Label incompleteness bound
- Displaced with displacer judged `yes`: **2**
- Hit@10 drop bound (yes displacers / 200): **0.01**
- Caveat: Only the top non-gold displacer per displaced question was judged.

Total cached spend (USD): 0.5557
