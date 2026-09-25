#!/usr/bin/env bash
# Resume OpenAI ERB embedding toward 100k (single process only).
# Safe to re-run: skips docs already in data/erb_ingest_checkpoint.json.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
STATUS="$ROOT/data/erb_ingest_pause_status.json"
CKPT="$ROOT/data/erb_ingest_checkpoint.json"
LOG="${ERB_INGEST_LOG:-/tmp/erb_ingest_100k.log}"
BUDGET="${ERB_BUDGET_CAP_USD:-5.50}"
LIMIT="${ERB_INGEST_LIMIT:-100000}"
BATCH="${ERB_INGEST_BATCH:-40}"

cd "$ROOT"

if ! docker ps --format '{{.Names}}' | grep -qx 'vector-drift-api'; then
  echo "ERROR: vector-drift-api container not running. Start stack first (docker compose up -d)."
  exit 1
fi
if ! docker ps --format '{{.Names}}' | grep -qx 'vector-drift-postgres'; then
  echo "ERROR: vector-drift-postgres container not running."
  exit 1
fi

# Refuse to start a second worker
existing="$(
  docker exec vector-drift-api python3 -c '
import glob
n=0
for c in glob.glob("/proc/[0-9]*/cmdline"):
  try: parts=open(c,"rb").read().replace(b"\0",b" ").decode(errors="ignore").split()
  except Exception: continue
  if len(parts)>=2 and "python" in parts[0] and parts[1].endswith("ingest_erb.py"):
    n+=1
print(n)
'
)"
if [[ "$existing" != "0" ]]; then
  echo "ERROR: ingest already running ($existing process). Stop it first."
  exit 1
fi

# Sync checkpoint from DB before resume (exact done set)
python3 - <<PY
import json, subprocess, time
from pathlib import Path
root = Path("$ROOT")
out = subprocess.check_output([
    "docker", "exec", "-i", "vector-drift-postgres",
    "psql", "-U", "vector_drift", "-d", "vector_drift", "-t", "-A", "-c",
    "SELECT doc_id FROM document_chunks",
], text=True)
ids = sorted({x.strip() for x in out.splitlines() if x.strip()})
ckpt = {
    "done_doc_ids": ids,
    "count": len(ids),
    "target_limit": int("$LIMIT"),
    "updated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    "paused": False,
    "resume_started_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
}
(root / "data" / "erb_ingest_checkpoint.json").write_text(json.dumps(ckpt))
status = {
    "paused": False,
    "embedded_count": len(ids),
    "target": int("$LIMIT"),
    "remaining": max(0, int("$LIMIT") - len(ids)),
    "updated_at": ckpt["updated_at"],
}
try:
    cost = json.loads((root / "data" / "erb_cost_tracker.json").read_text())
    status["cost_usd"] = round(cost["totals"]["total_cost_usd"], 4)
except Exception:
    pass
(root / "data" / "erb_ingest_pause_status.json").write_text(json.dumps(status, indent=2))
print(f"synced checkpoint count={len(ids)} remaining={status['remaining']}")
PY

echo "Starting single ingest (limit=$LIMIT batch=$BATCH budget=\$$BUDGET). Log: $LOG"
nohup docker exec \
  -e DATABASE_URL=postgresql://vector_drift:vector_drift@vector-drift-postgres:5432/vector_drift \
  -e ERB_BUDGET_CAP_USD="$BUDGET" \
  vector-drift-api python /app/scripts/erb/ingest_erb.py --limit "$LIMIT" --batch-size "$BATCH" \
  >>"$LOG" 2>&1 &
echo "host_pid=$!"
sleep 5
tail -n 8 "$LOG" | tr -d '\000' || true
echo "Monitor: tail -f $LOG | grep upserted"
echo "Status:  cat $STATUS"
