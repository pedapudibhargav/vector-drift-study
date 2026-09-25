# Published artifacts

Tracked, camera-ready outputs for the IEEE paper and GitHub Pages site.

| File | Description |
|------|-------------|
| `erb_full_primary200_to100k.json` | Full primary-200 dense sweep (raw+meta) |
| `erb_full_primary200_to100k_fit.json` | Scaling fits, \(N^\star\), bootstrap CIs |
| `erb_lexical_baseline_primary200.json` | Postgres FTS baseline (5k–25k) |
| `primary_questions_200.json` | Stratified question IDs used in the sweep |
| `human_audit_n5000_raw.csv` | L4 worksheet (fill auditor / labels) |
| `human_audit_n20000_raw.csv` | L4 worksheet at 20k |
| `HUMAN_AUDIT_TEMPLATE.md` | Labeling taxonomy |
| `l3_judge_*.json` | Optional gpt-4o-mini corroboration |

**Database dump** (too large for git): download `erb_tables.dump.gz` from
[GitHub Releases](https://github.com/pedapudibhargav/vector-drift-study/releases)
and restore with `./scripts/erb/restore_from_backup.sh`.

See [docs/REPLICATE.md](../docs/REPLICATE.md).
