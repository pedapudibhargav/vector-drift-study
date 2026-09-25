#!/usr/bin/env bash
# Compress a backup directory for GitHub Releases upload.
# Usage: ./scripts/erb/package_release_artifacts.sh data/backups/pre_phase1_YYYYMMDDTHHMMSSZ
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"

SRC="${1:-}"
if [[ -z "$SRC" || ! -d "$SRC" ]]; then
  echo "usage: $0 <backup-dir-containing-erb_tables.dump>" >&2
  exit 2
fi

DUMP="$SRC/erb_tables.dump"
if [[ ! -f "$DUMP" ]]; then
  echo "missing $DUMP" >&2
  exit 1
fi

OUT_DIR="$ROOT/data/backups/release"
mkdir -p "$OUT_DIR"
STAMP="$(basename "$SRC")"
OUT_GZ="$OUT_DIR/erb_tables.dump.gz"
MANIFEST="$OUT_DIR/MANIFEST-${STAMP}.txt"

echo "==> gzip (this may take several minutes for ~1GB dumps)"
gzip -c -9 "$DUMP" >"$OUT_GZ"

TITAN_DUMP="$SRC/erb_titan_tables.dump"
TITAN_GZ="$OUT_DIR/erb_titan_tables.dump.gz"
if [[ -f "$TITAN_DUMP" ]]; then
  echo "==> gzip Titan dump"
  gzip -c -9 "$TITAN_DUMP" >"$TITAN_GZ"
fi

CACHES=()
for c in erb_query_embed_cache.json erb_titan_query_embed_cache.json; do
  if [[ -f "$SRC/$c" ]]; then
    gzip -c -9 "$SRC/$c" >"$OUT_DIR/$c.gz"
    CACHES+=("$OUT_DIR/$c.gz")
  fi
done

{
  echo "source_dir=$SRC"
  echo "created_at_utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "dump_gz=$(basename "$OUT_GZ")"
  echo "dump_gz_bytes=$(wc -c <"$OUT_GZ" | tr -d ' ')"
  echo "dump_bytes=$(wc -c <"$DUMP" | tr -d ' ')"
  echo "dump_sha256=$(shasum -a 256 "$OUT_GZ" | cut -d' ' -f1)"
  if [[ -f "$TITAN_DUMP" ]]; then
    echo "titan_dump_gz=$(basename "$TITAN_GZ")"
    echo "titan_dump_gz_bytes=$(wc -c <"$TITAN_GZ" | tr -d ' ')"
    echo "titan_dump_sha256=$(shasum -a 256 "$TITAN_GZ" | cut -d' ' -f1)"
  fi
  for c in ${CACHES[@]+"${CACHES[@]}"}; do
    echo "query_cache=$(basename "$c") sha256=$(shasum -a 256 "$c" | cut -d' ' -f1)"
  done
  if [[ -f "$SRC/counts.txt" ]]; then
    echo "counts=$(tr '\n' ' ' <"$SRC/counts.txt")"
  fi
  echo
  echo "Upload to GitHub Release:"
  echo "  gh release create v1.0.0-artifacts \\"
  echo "    \"$OUT_GZ\" \\"
  [[ -f "$TITAN_DUMP" ]] && echo "    \"$TITAN_GZ\" \\"
  for c in ${CACHES[@]+"${CACHES[@]}"}; do echo "    \"$c\" \\"; done
  echo "    --title \"Vector drift study DB snapshot\" \\"
  echo "    --notes \"pg_dump custom format: OpenAI document_chunks + metrics tables; Titan V2 tables in erb_titan_tables.dump.gz; cached primary-200 query embeddings. Restore with ./scripts/erb/restore_from_backup.sh\""
} | tee "$MANIFEST"

ls -lh "$OUT_GZ" ${TITAN_GZ:+$( [[ -f "$TITAN_GZ" ]] && echo "$TITAN_GZ")}
echo "package_ok $OUT_GZ"
