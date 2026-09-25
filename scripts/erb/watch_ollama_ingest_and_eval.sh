#!/usr/bin/env bash
# Watchdog: keep Ollama + nomic ingest alive; when coverage >= 100k run ladder + compare.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"
export PATH="/Applications/Docker.app/Contents/Resources/bin:$HOME/.docker/bin:/opt/homebrew/bin:/usr/local/bin:$PATH"
LOG="${ERB_OLLAMA_LOG:-/tmp/erb_ollama_ingest.log}"
WATCH_LOG="${ERB_OLLAMA_WATCH_LOG:-/tmp/erb_ollama_watch.log}"
TARGET="${ERB_INGEST_TARGET:-100000}"
STALL_MIN="${ERB_STALL_MINUTES:-8}"

log() { echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] $*" | tee -a "$WATCH_LOG"; }

ckpt_count() {
  python3 - <<'PY'
import json
from pathlib import Path
p=Path("data/erb_ollama_ingest_checkpoint.json")
print(json.loads(p.read_text())["count"] if p.exists() else 0)
PY
}

ollama_up() { curl -sf http://127.0.0.1:11434/api/tags >/dev/null; }

ensure_ollama() {
  if ollama_up; then return 0; fi
  log "starting ollama serve"
  pkill -f 'ollama serve' 2>/dev/null || true
  sleep 1
  OLLAMA_HOST=0.0.0.0:11434 OLLAMA_NUM_PARALLEL=6 OLLAMA_KEEP_ALIVE=24h \
    nohup ollama serve >>/tmp/ollama_serve.log 2>&1 &
  for _ in $(seq 1 20); do
    ollama_up && return 0
    sleep 1
  done
  return 1
}

ingest_running() {
  docker exec vector-drift-api python3 -c '
import glob
n=0
for c in glob.glob("/proc/[0-9]*/cmdline"):
  try: s=open(c,"rb").read().replace(b"\0",b" ").decode(errors="ignore")
  except Exception: continue
  if "ingest_erb_ollama.py" in s: n+=1
print(n)
' 2>/dev/null | tr -d '[:space:]'
}

start_ingest() {
  ensure_ollama || { log "ollama failed"; return 1; }
  docker exec vector-drift-api python /app/scripts/erb/migrate_ollama_schema.py >/dev/null
  # refresh ckpt from DB
  docker exec -e PGPASSWORD=vector_drift vector-drift-postgres \
    psql -U vector_drift -d vector_drift -t -A -c "SELECT doc_id FROM document_chunks_ollama;" \
    > /tmp/ollama_done_ids.txt
  python3 - <<'PY'
import json,time
from pathlib import Path
ids=[ln.strip() for ln in Path("/tmp/ollama_done_ids.txt").read_text().splitlines() if ln.strip()]
Path("data/erb_ollama_ingest_checkpoint.json").write_text(json.dumps({
  "done_doc_ids": ids, "count": len(ids), "model": "nomic-embed-text",
  "updated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
}, indent=2))
print(len(ids))
PY
  log "starting ingest workers=8 batch=16"
  nohup docker exec \
    -e DATABASE_URL=postgresql://vector_drift:vector_drift@vector-drift-postgres:5432/vector_drift \
    -e OLLAMA_HOST=http://host.docker.internal:11434 \
    -e OLLAMA_EMBED_MODEL=nomic-embed-text \
    vector-drift-api python /app/scripts/erb/ingest_erb_ollama.py \
      --limit 100000 --batch-size 16 --workers 8 --smoke-every 400 \
    >>"$LOG" 2>&1 &
  sleep 5
}

run_eval() {
  log "INGEST COMPLETE — starting full ladder sweep"
  docker exec \
    -e DATABASE_URL=postgresql://vector_drift:vector_drift@vector-drift-postgres:5432/vector_drift \
    -e OLLAMA_HOST=http://host.docker.internal:11434 \
    -e OLLAMA_EMBED_MODEL=nomic-embed-text \
    vector-drift-api python /app/scripts/erb/run_scale_sweep_ollama.py \
      --primary-questions 200 \
      --scales 5000 10000 15000 20000 25000 40000 50000 75000 100000 \
      --top-k 10 \
      --workers 8 \
    | tee -a /tmp/erb_ollama_sweep.log
  python3 scripts/erb/compare_openai_vs_nomic.py \
    artifacts/published/erb_ollama_primary200_to100k.json || true
  log "EVAL+COMPARE done — see artifacts/published/openai_vs_nomic_primary200.md"
}

log "watchdog start target=$TARGET"
last=$(ckpt_count)
last_change=$(date +%s)
stall_restarts=0

while true; do
  ensure_ollama || true
  cur=$(ckpt_count)
  now=$(date +%s)
  if [[ "$cur" -gt "$last" ]]; then
    last=$cur
    last_change=$now
    stall_restarts=0
  fi
  running=$(ingest_running || echo 0)
  elapsed_min=$(( (now - last_change) / 60 ))
  log "count=$cur/$TARGET ingest_procs=$running stall_min=$elapsed_min"

  if [[ "$cur" -ge "$TARGET" ]]; then
    # stop ingest if still running
    docker exec vector-drift-api bash -c 'pkill -f ingest_erb_ollama.py || true' 2>/dev/null || true
    run_eval
    exit 0
  fi

  if [[ "$running" == "0" ]]; then
    log "ingest not running — restart"
    start_ingest || true
  elif [[ "$elapsed_min" -ge "$STALL_MIN" ]]; then
    stall_restarts=$((stall_restarts + 1))
    log "STALLED ${elapsed_min}m — restart ingest (#$stall_restarts)"
    docker exec vector-drift-api bash -c 'pkill -f ingest_erb_ollama.py || true' 2>/dev/null || true
    sleep 2
    start_ingest || true
    last_change=$(date +%s)
  fi
  sleep 60
done
