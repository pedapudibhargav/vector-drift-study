# L4 Human / LLM Audit — status after author spot-check

## Done

| Layer | Result |
|-------|--------|
| L1 + verify | `python3 scripts/erb/verify_paper_numbers.py` → **VERIFY OK** |
| L4 LLM | 62/62 fairness Agree (`l4_hit_fairness_llm.md`) |
| Author spot-check | **9/10** agree LLM; **1/10** unsure (`label_noise`) — `L4_SPOTCHECK_HUMAN.md` |
| Exact MVP | Exact Hit@10 0.795→0.585; HNSW gap +0.075 at 100k — `exact_control_mvp.md` |

## Still optional / packaging

- Thesaurus keywords, Word twin, PDF eXpress, CrossCheck
- Rebuild `main.pdf` after TeX edits (`pdflatex` locally)

## Do not cite

Ollama report, `*.POLLUTED.json`.
