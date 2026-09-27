# L4 audit — LLM-assisted fairness check and author spot-check

L4 is **secondary corroboration** of Hit@10 fairness. Every paper claim rests on L1 labeled IR metrics.
See Sec. IV-D (Validation Layers) of the manuscript.

| Step | What was done | Result | Artifact |
|------|---------------|--------|----------|
| LLM-assisted audit | `gpt-4o` judged 62 high-priority rows (full gold text + truncated top-10 previews; prompt `l4-hit-fairness-v1`) | Hit@10 fair on **62/62**; gold text answers the question on 49/62 | `artifacts/published/l4_hit_fairness_llm.{json,csv,md}` |
| Author spot-check | The author labeled a stratified 10-row subset in the Review UI | **9/10** agree with the LLM; **1/10** unsure (`label_noise`) | `artifacts/published/L4_SPOTCHECK_HUMAN.md`, `l4_spotcheck_human_results.json` |
| Transparency note | How L4 is framed and disclosed | — | `artifacts/published/L4_LLM_TRANSPARENCY.md` |

The spot-check is not a claim that a human labeled all 62 rows. Long gold documents can confuse the LLM auditor, so the 49/62 gold-adequacy rate is not used as a primary result.

## Re-running

- LLM audit (needs `OPENAI_API_KEY`): `scripts/erb/run_l4_hit_fairness_llm.py`
- Review UI for manual labels: `docker compose up -d vector-drift-web`, then open http://localhost:5173/review

## Do not cite

`*.POLLUTED.json` (pre-integrity exploratory aggregates).
