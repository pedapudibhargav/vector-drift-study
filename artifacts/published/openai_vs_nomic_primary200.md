# OpenAI vs Nomic (primary-200) — waiting

Nomic Ollama sweep not available; re-run after erb_ollama ingest + run_scale_sweep_ollama.py complete.

- OpenAI source: `artifacts/published/erb_full_primary200_to100k.json`
- Nomic search: `erb_ollama_primary200_to100k.json or data/results/erb_ollama_sweep_*.json`

Re-run:

```bash
python scripts/erb/compare_openai_vs_nomic.py
# or after publishing:
python scripts/erb/compare_openai_vs_nomic.py artifacts/published/erb_ollama_primary200_to100k.json
```
