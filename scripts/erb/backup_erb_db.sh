#!/usr/bin/env bash
# Snapshot ERB embeddings + metric tables for Releases / local restore.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"
export PATH="/Applications/Docker.app/Contents/Resources/bin:$HOME/.docker/bin:/usr/local/bin:/opt/homebrew/bin:$PATH"

if [[ -f .env ]]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

PGUSER="${POSTGRES_USER:-postgres}"
PGPASSWORD="${POSTGRES_PASSWORD:-postgres}"
PGDB="${POSTGRES_DB:-vector_drift_db}"
CONTAINER="${POSTGRES_CONTAINER:-vector-drift-postgres}"

TS="$(date -u +%Y%m%dT%H%M%SZ)"
OUT="$ROOT/data/backups/erb_${TS}"
mkdir -p "$OUT"

echo "Backing up to $OUT"
docker exec -e PGPASSWORD="$PGPASSWORD" "$CONTAINER" \
  pg_dump -U "$PGUSER" -d "$PGDB" \
  --format=custom --no-owner \
  -t document_chunks -t document_chunks_ollama \
  -t experiment_runs -t vector_drift_results -t retrieval_hit_details \
  -t llm_eval_results \
  >"$OUT/erb_tables.dump"

# Titan V2 secondary arm lives in separate tables; dump it as its own file so each
# Release asset stays under GitHub's 2 GB limit and replicators can restore either arm.
if docker exec -e PGPASSWORD="$PGPASSWORD" "$CONTAINER" \
    psql -U "$PGUSER" -d "$PGDB" -t -A -c "SELECT to_regclass('document_chunks_titan') IS NOT NULL;" | grep -q t; then
  docker exec -e PGPASSWORD="$PGPASSWORD" "$CONTAINER" \
    pg_dump -U "$PGUSER" -d "$PGDB" \
    --format=custom --no-owner \
    -t document_chunks_titan -t experiment_runs_titan -t vector_drift_results_titan \
    >"$OUT/erb_titan_tables.dump"
fi

docker exec -e PGPASSWORD="$PGPASSWORD" "$CONTAINER" \
  psql -U "$PGUSER" -d "$PGDB" -t -A -c \
  "SELECT 'document_chunks='||COUNT(*)||' lt100k='||COUNT(*) FILTER (WHERE scale_rank<100000) FROM document_chunks;" \
  >"$OUT/counts.txt"
if [[ -f "$OUT/erb_titan_tables.dump" ]]; then
  docker exec -e PGPASSWORD="$PGPASSWORD" "$CONTAINER" \
    psql -U "$PGUSER" -d "$PGDB" -t -A -c \
    "SELECT 'document_chunks_titan='||COUNT(*)||' lt100k='||COUNT(*) FILTER (WHERE scale_rank<100000) FROM document_chunks_titan;" \
    >>"$OUT/counts.txt"
fi

cp "$ROOT/data/erb_cost_tracker.json" "$OUT/" 2>/dev/null || true
cp "$ROOT/artifacts/published/erb_full_primary200_to100k_fit.json" "$OUT/" 2>/dev/null || true
# Cached query embeddings (primary-200) so sweeps can re-run without any embedding API calls.
cp "$ROOT/data/erb_query_embed_cache.json" "$OUT/" 2>/dev/null || true
cp "$ROOT/data/erb_titan_query_embed_cache.json" "$OUT/" 2>/dev/null || true

echo "backup_ok $OUT"
ls -lh "$OUT" | head -20
echo "next: ./scripts/erb/package_release_artifacts.sh $OUT"
