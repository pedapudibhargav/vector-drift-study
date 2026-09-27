# L4 Hit@10 fairness — transparency note

## Is LLM L4 OK for an IEEE Access paper?

**Yes, if framed correctly and disclosed.** Treat L4 here as *secondary corroboration of Hit@10 fairness*, not as a replacement for L1 labeled IR metrics or as a claim that every top-10 chunk was human-read.

IEEE Access expects honest methods: state the model, prompt version, sample size, what was judged, and that primary claims do not depend on the LLM auditor.

## What we did (this repo)

| Item | Value |
|------|--------|
| Queue | 62 high-priority rows (`human_review_queue_openai.csv`) |
| Model | OpenAI `gpt-4o` via `OPENAI_API_KEY` |
| Prompt | `l4-hit-fairness-v1` in `scripts/erb/run_l4_hit_fairness_llm.py` |
| Inputs per row | Question + **full gold .txt** + truncated top-10 previews |
| Judgment | `y`/`n`/`unsure` = is auto Hit@10 **fair**? + does gold text answer? |
| Cost | ≈ $0.79 |
| Artifacts | `l4_hit_fairness_llm.{json,csv,md}` |

## Results (summary)

- **Hit@10 fairness:** 62/62 → `y` (membership consistent; MISS with good gold stays `y`)
- **Gold answers question (LLM):** 49 true / 13 false
- **Failure modes tagged:** none (no `n` / `label_noise` on this pass)

## Rubric (what “y” means)

1. Agree with Hit@10 when gold `doc_id` ∈ top-10 matches the auto flag.
2. If **HIT** and gold text does **not** answer → prefer `n` + `label_noise`.
3. If **MISS** but gold text **does** answer → still `y` (true miss / drift-relevant).
4. Do **not** require reading all 10 chunks to invent an answer; top-10 is context only.

## Known limitation (be transparent)

Same gold document for `qst_0010::metadata` was labeled `gold_answers_question=true` at N=5k (found Due 2025-12-04) and `false` at N=40k. The due date is in the file. Long-document auditor misses are possible; do not cite gold-adequacy % as a hard science claim without human spot-check.

## Paper wording stance

- Primary: L1 Hit@k / MRR / DocRecall on integrity-clean ladder.
- Secondary: L3 + LLM L4 disclosed in Methods + Acknowledgment.
- Optional: author spot-checks a handful of rows in `/review` for narrative examples.

## Reproduce

```bash
python3 scripts/erb/run_l4_hit_fairness_llm.py --budget-usd 5.0
# smoke:
python3 scripts/erb/run_l4_hit_fairness_llm.py --limit 1
```
