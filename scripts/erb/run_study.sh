#!/usr/bin/env bash
# End-to-end EnterpriseRAG vector-drift study runner.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"

if [[ -f .env ]]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

PGUSER="${POSTGRES_USER:-postgres}"
PGPASSWORD="${POSTGRES_PASSWORD:-postgres}"
PGDB="${POSTGRES_DB:-vector_drift_db}"
SYNC_URL="postgresql://${PGUSER}:${PGPASSWORD}@vector-drift-postgres:5432/${PGDB}"
ASYNC_URL="postgresql+asyncpg://${PGUSER}:${PGPASSWORD}@vector-drift-postgres:5432/${PGDB}"

MODE="${1:-smoke}"  # smoke | full-local | full-all

case "$MODE" in
  smoke)
    python3 scripts/erb/download_erb.py --sources confluence jira linear github --max-slices 1 --extract
    python3 scripts/erb/build_scale_manifest.py
    docker exec -e DATABASE_URL="$SYNC_URL" \
      vector-drift-api python /app/scripts/erb/ingest_erb.py --limit 5000 --batch-size 40
    docker exec -e DATABASE_URL="$ASYNC_URL" \
      vector-drift-api python /app/scripts/erb/run_scale_sweep.py --smoke --question-limit 50 --scales 1000 5000
    ;;
  full-local)
    python3 scripts/erb/download_erb.py --sources confluence jira linear github google_drive hubspot fireflies --max-slices 1 --extract
    python3 scripts/erb/build_scale_manifest.py
    docker exec -e DATABASE_URL="$SYNC_URL" \
      vector-drift-api python /app/scripts/erb/ingest_erb.py --batch-size 40
    docker exec -e DATABASE_URL="$ASYNC_URL" \
      vector-drift-api python /app/scripts/erb/run_scale_sweep.py --primary-questions
    ;;
  full-all)
    python3 scripts/erb/download_erb.py --all-docs --extract
    python3 scripts/erb/build_scale_manifest.py
    docker exec -e DATABASE_URL="$SYNC_URL" \
      vector-drift-api python /app/scripts/erb/ingest_erb.py --batch-size 40
    docker exec -e DATABASE_URL="$ASYNC_URL" \
      vector-drift-api python /app/scripts/erb/run_scale_sweep.py --primary-questions
    ;;
  *)
    echo "usage: $0 [smoke|full-local|full-all]" >&2
    exit 2
    ;;
esac

LATEST="$(ls -t data/results/erb_scale_sweep_*.json 2>/dev/null | head -1 || true)"
if [[ -n "$LATEST" ]]; then
  python3 scripts/erb/fit_scaling_law.py "$LATEST"
  echo "done: $LATEST"
else
  echo "done (no sweep JSON found under data/results/)"
fi
