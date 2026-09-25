# Database backups

Large pgvector dumps are **not** stored in git.

## For replicators

1. Download `erb_tables.dump.gz` (OpenAI arm) and optionally `erb_titan_tables.dump.gz`
   (Titan V2 arm) from the repository
   [Releases](https://github.com/pedapudibhargav/vector-drift-study/releases).
2. Save them under `data/backups/`.
3. Run:

```bash
docker compose up -d vector-drift-postgres vector-drift-api
./scripts/erb/restore_from_backup.sh data/backups/erb_tables.dump.gz
./scripts/erb/restore_from_backup.sh data/backups/erb_titan_tables.dump.gz   # optional
```

## For maintainers

```bash
# While stack is up:
./scripts/erb/backup_erb_db.sh
./scripts/erb/package_release_artifacts.sh data/backups/<timestamp_dir>
gh release create v1.0.0-artifacts data/backups/release/erb_tables.dump.gz \
  data/backups/release/erb_titan_tables.dump.gz \
  data/backups/release/erb_query_embed_cache.json.gz \
  data/backups/release/erb_titan_query_embed_cache.json.gz \
  --title "DB snapshot (embeddings + metrics tables)" \
  --notes "Restore with ./scripts/erb/restore_from_backup.sh"
```

Local snapshots on author machines are gitignored (`data/backups/*/`).
