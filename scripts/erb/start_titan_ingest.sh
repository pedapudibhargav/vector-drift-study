#!/usr/bin/env bash
# Start Titan ingest detached from the parent process group (survives IDE/agent shell exit).
# Usage: ./scripts/erb/start_titan_ingest.sh
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"

LOG="${ERB_TITAN_LOG:-/tmp/erb_titan_ingest.log}"
PIDFILE="${ERB_TITAN_PIDFILE:-/tmp/erb_titan_ingest.pid}"

# Require caller to export AWS_CONFIG_FILE / AWS_PROFILE (or rely on ~/.aws).
: "${DATABASE_URL:=postgresql://vector_drift:vector_drift@localhost:5432/vector_drift}"
export DATABASE_URL
export PYTHONPATH="${ROOT}/scripts/erb${PYTHONPATH:+:$PYTHONPATH}"
export PYTHONUNBUFFERED=1
export AWS_REGION="${AWS_REGION:-us-east-1}"
export BEDROCK_REGION="${BEDROCK_REGION:-$AWS_REGION}"

# Stop prior ingest if pidfile present
if [[ -f "$PIDFILE" ]]; then
  old="$(cat "$PIDFILE" || true)"
  if [[ -n "${old:-}" ]] && kill -0 "$old" 2>/dev/null; then
    echo "stopping prior ingest pid=$old"
    kill "$old" 2>/dev/null || true
    sleep 2
  fi
fi

BATCH="${ERB_TITAN_BATCH:-24}"
WORKERS="${ERB_TITAN_WORKERS:-8}"

# Detach into a new session so closing the shell does not kill ingest.
# Linux: setsid. macOS: Python start_new_session (setsid is often absent).
{
  echo "==== START $(date -u +%Y-%m-%dT%H:%M:%SZ) ===="
  echo "cwd=$ROOT batch=$BATCH workers=$WORKERS"
} >>"$LOG"

PY="$ROOT/.venv/bin/python"
INGEST="$ROOT/scripts/erb/ingest_erb_titan.py"
ARGS=(--limit 100000 --batch-size "$BATCH" --workers "$WORKERS" --smoke-every 500)

if command -v setsid >/dev/null 2>&1; then
  # shellcheck disable=SC2086
  setsid "$PY" -u "$INGEST" "${ARGS[@]}" >>"$LOG" 2>&1 < /dev/null &
  echo $! >"$PIDFILE"
  disown || true
else
  # macOS / BSD: open a new session via Python (equivalent to setsid)
  "$PY" -u - "$PY" "$INGEST" "$LOG" "$PIDFILE" "${ARGS[@]}" <<'PY'
import os, subprocess, sys
py, ingest, log_path, pidfile, *args = sys.argv[1:]
with open(log_path, "a", encoding="utf-8") as log:
    proc = subprocess.Popen(
        [py, "-u", ingest, *args],
        stdin=subprocess.DEVNULL,
        stdout=log,
        stderr=subprocess.STDOUT,
        start_new_session=True,
        env=os.environ.copy(),
    )
Path = __import__("pathlib").Path
Path(pidfile).write_text(str(proc.pid) + "\n", encoding="utf-8")
print(proc.pid)
PY
fi

sleep 2
echo "started pid=$(cat "$PIDFILE") log=$LOG"
tail -n 15 "$LOG" || true
