# LLM displacement relevance audit (revision 1, G3)

Generated: 2026-11-11T06:11:09Z

## Setup
- Provider: `openai`; model: `gpt-4o`
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
| displacer | 42 | 10 | 10 | 22 | 0.4762 | 0.3336–0.6228 |
| competitor5k | 42 | 12 | 7 | 23 | 0.4524 | 0.3122–0.6005 |
| gold_control | 30 | 25 | 2 | 3 | 0.9 | 0.7438–0.9654 |
| random_control | 15 | 0 | 1 | 14 | 0.0667 | 0.0119–0.2982 |

## Comparisons
- Displacer yes+partial: **0.4762**
- Competitor@5k yes+partial: **0.4524**
- Random control yes+partial: **0.0667**
- McNemar paired: `{"n_pairs": 42, "b_displacer_rel_competitor_not": 4, "c_competitor_rel_displacer_not": 3, "mcnemar_chi2_with_continuity": 0.0, "note": "McNemar-style discordant counts on same displaced questions (yes+partial=relevant)"}`

## Calibration (gold control)
- Gold `yes` share: **0.8333** (Wilson [0.6644, 0.9266])

## Label incompleteness bound
- Displaced with displacer judged `yes`: **10**
- Hit@10 drop bound (yes displacers / 200): **0.05**
- Caveat: Only the top non-gold displacer per displaced question was judged.

Total cached spend (USD): 0.4809
