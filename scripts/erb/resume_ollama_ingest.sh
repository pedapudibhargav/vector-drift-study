#!/usr/bin/env bash
# Start efficient local nomic-embed-text ingest (host Ollama + container Python/DB).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
LOG="${ERB_OLLAMA_LOG:-/tmp/erb_ollama_ingest.log}"
LIMIT="${ERB_INGEST_LIMIT:-100000}"
BATCH="${ERB_OLLAMA_BATCH:-16}"
WORKERS="${ERB_OLLAMA_WORKERS:-10}"

export PATH="/Applications/Docker.app/Contents/Resources/bin:$HOME/.docker/bin:/usr/local/bin:/opt/homebrew/bin:$PATH"

# Do not kill host ollama in resume — only start if down
if ! curl -sf http://127.0.0.1:11434/api/tags >/dev/null; then
  echo "Starting ollama serve on 0.0.0.0:11434 ..."
  OLLAMA_HOST=0.0.0.0:11434 OLLAMA_NUM_PARALLEL=4 OLLAMA_KEEP_ALIVE=24h \
    nohup ollama serve >>/tmp/ollama_serve.log 2>&1 &
  sleep 3
fi
curl -sf http://127.0.0.1:11434/api/tags >/dev/null
ollama pull nomic-embed-text >/dev/null 2>&1 || true

# Refuse duplicate ollama ingest
existing="$(
  docker exec vector-drift-api python3 -c '
import glob
n=0
for c in glob.glob("/proc/[0-9]*/cmdline"):
  try: parts=open(c,"rb").read().replace(b"\0",b" ").decode(errors="ignore").split()
  except Exception: continue
  if len(parts)>=2 and "python" in parts[0] and parts[1].endswith("ingest_erb_ollama.py"):
    n+=1
print(n)
'
)"
if [[ "$existing" != "0" ]]; then
  echo "ERROR: ollama ingest already running ($existing)"
  exit 1
fi

docker exec vector-drift-api python /app/scripts/erb/migrate_ollama_schema.py

echo "Starting ollama nomic ingest batch=$BATCH workers=$WORKERS log=$LOG"
nohup docker exec \
  -e DATABASE_URL=postgresql://vector_drift:vector_drift@vector-drift-postgres:5432/vector_drift \
  -e OLLAMA_HOST=http://host.docker.internal:11434 \
  -e OLLAMA_EMBED_MODEL=nomic-embed-text \
  vector-drift-api python /app/scripts/erb/ingest_erb_ollama.py \
    --limit "$LIMIT" --batch-size "$BATCH" --workers "$WORKERS" --smoke-every 200 \
  >>"$LOG" 2>&1 &
echo "host_pid=$!"
sleep 6
tail -n 15 "$LOG" | tr -d '\000' || true
