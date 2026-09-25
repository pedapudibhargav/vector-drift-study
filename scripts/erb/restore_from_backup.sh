#!/usr/bin/env bash
# Restore ERB pg_dump into the local dockerized Postgres.
# Usage:
#   ./scripts/erb/restore_from_backup.sh data/backups/erb_tables.dump.gz
#   ./scripts/erb/restore_from_backup.sh data/backups/erb_titan_tables.dump.gz   # Titan V2 arm
#   ./scripts/erb/restore_from_backup.sh data/backups/pre_phase1_*/erb_tables.dump
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"
export PATH="/Applications/Docker.app/Contents/Resources/bin:$HOME/.docker/bin:/usr/local/bin:/opt/homebrew/bin:$PATH"

DUMP_IN="${1:-}"
if [[ -z "$DUMP_IN" ]]; then
  echo "usage: $0 <path-to-erb_tables.dump[.gz]>" >&2
  exit 2
fi
if [[ ! -f "$DUMP_IN" ]]; then
  echo "file not found: $DUMP_IN" >&2
  exit 1
fi

# Load .env defaults if present
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

echo "==> waiting for $CONTAINER"
for _ in $(seq 1 60); do
  if docker exec -e PGPASSWORD="$PGPASSWORD" "$CONTAINER" \
      pg_isready -U "$PGUSER" -d "$PGDB" >/dev/null 2>&1; then
    break
  fi
  sleep 2
done
docker exec -e PGPASSWORD="$PGPASSWORD" "$CONTAINER" \
  pg_isready -U "$PGUSER" -d "$PGDB"

WORKDIR="$(mktemp -d)"
cleanup() { rm -rf "$WORKDIR"; }
trap cleanup EXIT

DUMP_PATH="$WORKDIR/erb_tables.dump"
case "$DUMP_IN" in
  *.gz)
    echo "==> decompressing $DUMP_IN"
    gzip -dc "$DUMP_IN" >"$DUMP_PATH"
    ;;
  *)
    cp "$DUMP_IN" "$DUMP_PATH"
    ;;
esac

echo "==> copying dump into container"
docker cp "$DUMP_PATH" "$CONTAINER:/tmp/erb_tables.dump"

echo "==> ensuring base extensions"
docker exec -e PGPASSWORD="$PGPASSWORD" "$CONTAINER" \
  psql -U "$PGUSER" -d "$PGDB" -v ON_ERROR_STOP=1 \
  -c 'CREATE EXTENSION IF NOT EXISTS vector;' \
  -c 'CREATE EXTENSION IF NOT EXISTS "uuid-ossp";'

echo "==> pg_restore (clean, no-owner)"
# Custom-format dump from backup_erb_db.sh. --clean drops existing target tables first.
docker exec -e PGPASSWORD="$PGPASSWORD" "$CONTAINER" \
  pg_restore -U "$PGUSER" -d "$PGDB" \
    --clean --if-exists --no-owner --no-acl \
    --verbose \
    /tmp/erb_tables.dump \
  || true
# pg_restore returns 1 on some benign notice/errors (e.g. missing optional ollama table).
# Verify the critical table instead of trusting exit code alone.

# The OpenAI dump carries document_chunks; the Titan dump carries document_chunks_titan.
CHUNK_TABLE="document_chunks"
if docker exec "$CONTAINER" pg_restore --list /tmp/erb_tables.dump \
    | grep -qE "TABLE public document_chunks_titan "; then
  CHUNK_TABLE="document_chunks_titan"
fi

echo "==> verifying $CHUNK_TABLE"
COUNTS="$(docker exec -e PGPASSWORD="$PGPASSWORD" "$CONTAINER" \
  psql -U "$PGUSER" -d "$PGDB" -t -A -c \
  "SELECT '${CHUNK_TABLE}='||COUNT(*)||' lt100k='||COUNT(*) FILTER (WHERE scale_rank < 100000)
   FROM ${CHUNK_TABLE};")"
echo "$COUNTS"

LT100K="$(echo "$COUNTS" | sed -n 's/.*lt100k=\([0-9]*\).*/\1/p')"
if [[ -z "$LT100K" || "$LT100K" -lt 1000 ]]; then
  echo "restore_failed: $CHUNK_TABLE looks empty or missing scale_rank data" >&2
  exit 1
fi

docker exec "$CONTAINER" rm -f /tmp/erb_tables.dump
echo "restore_ok $COUNTS"
echo "next: python3 scripts/erb/validate_study.py"
