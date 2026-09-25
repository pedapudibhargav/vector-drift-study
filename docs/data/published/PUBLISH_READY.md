# Publish readiness (excluding human L4)

**Date:** 2026-09-24  
**Confidence target:** >95% for L1 science + public artifacts (human labeling still pending)

## Done
- Integrity-clean sweep promoted (`erb_full_primary200_to100k.json` from `erb_scale_sweep_20260920T203818Z.json`)
- Fit + `CANONICAL_METRICS.json` (N★ undefined; last_ge=100k; a≈1.474, b≈0.086)
- Integrity gate green; verification bundle rebuilt (3600 unique keys, Hit@10@5k raw=0.795)
- Mirrored to `docs/data/published/` + `docs/data/verification/`
- **A8 Titan** second embedder complete — `openai_vs_titan_*.json`, exact controls, `landing_summary.json`
- Single Pages landing (`docs/index.html`) documents goal, OpenAI findings, Titan replication + HNSW caveat
- Workflow `.github/workflows/deploy-gh-pages.yml` publishes on every push to `main`
- Access `main.tex` + **rebuilt `main.pdf`** show clean abstract numbers (0.795→0.510; no N★)
- OpenAI L3 triage packaged → `human_review_queue_openai.csv`
- Ollama L3 quarantined

## Still for authors (not automated)
- **Human L4** labeling (`human_review_queue_openai.csv` + Review UI)
- Access page count 7 (warn; target 8–16) — optional expand
- PDF eXpress / CrossCheck / Word twin via Author Portal
- Merge/push `main` so Actions refreshes https://pedapudibhargav.github.io/vector-drift-study/

## Do not cite
- `*.POLLUTED.json`, `llm_audit_report_ollama.json`, legacy `preview.html` / `PAPER_PREVIEW.md`
- “Titan drifts less” without the exact-cosine control (ANN gap on OpenAI HNSW)
