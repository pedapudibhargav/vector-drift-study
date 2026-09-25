#!/usr/bin/env bash
# Stop all ERB OpenAI ingest workers and sync checkpoint from Postgres.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"

docker exec vector-drift-api python3 -c '
import glob, os, signal, time
killed=[]
for c in glob.glob("/proc/[0-9]*/cmdline"):
  try: parts=open(c,"rb").read().replace(b"\0",b" ").decode(errors="ignore").split()
  except Exception: continue
  if len(parts)>=2 and "python" in parts[0] and parts[1].endswith("ingest_erb.py"):
    pid=int(c.split("/")[2])
    os.kill(pid, signal.SIGTERM)
    killed.append(pid)
print("SIGTERM", killed)
time.sleep(2)
for c in glob.glob("/proc/[0-9]*/cmdline"):
  try: parts=open(c,"rb").read().replace(b"\0",b" ").decode(errors="ignore").split()
  except Exception: continue
  if len(parts)>=2 and "python" in parts[0] and parts[1].endswith("ingest_erb.py"):
    pid=int(c.split("/")[2])
    os.kill(pid, signal.SIGKILL)
    print("SIGKILL", pid)
' 2>/dev/null || echo "api container not reachable (ok if already down)"

pkill -f 'ingest_erb.py --limit' 2>/dev/null || true

python3 - <<PY
import json, subprocess, time
from pathlib import Path
root = Path("$ROOT")
try:
    out = subprocess.check_output([
        "docker", "exec", "-i", "vector-drift-postgres",
        "psql", "-U", "vector_drift", "-d", "vector_drift", "-t", "-A", "-c",
        "SELECT doc_id FROM document_chunks",
    ], text=True)
    ids = sorted({x.strip() for x in out.splitlines() if x.strip()})
except Exception as e:
    print("WARN: could not sync from DB:", e)
    raise SystemExit(0)
ckpt = {
    "done_doc_ids": ids,
    "count": len(ids),
    "target_limit": 100000,
    "updated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    "paused": True,
    "pause_reason": "stopped via stop_openai_ingest.sh",
}
(root / "data" / "erb_ingest_checkpoint.json").write_text(json.dumps(ckpt))
status = {
    "paused": True,
    "embedded_count": len(ids),
    "target": 100000,
    "remaining": max(0, 100000 - len(ids)),
    "updated_at": ckpt["updated_at"],
    "resume": "./scripts/erb/resume_openai_ingest.sh",
}
try:
    cost = json.loads((root / "data" / "erb_cost_tracker.json").read_text())
    status["cost_usd"] = round(cost["totals"]["total_cost_usd"], 4)
except Exception:
    pass
(root / "data" / "erb_ingest_pause_status.json").write_text(json.dumps(status, indent=2))
print(json.dumps(status, indent=2))
PY

echo "Verify:"
docker exec vector-drift-api python3 -c '
import glob
n=0
for c in glob.glob("/proc/[0-9]*/cmdline"):
  try: parts=open(c,"rb").read().replace(b"\0",b" ").decode(errors="ignore").split()
  except Exception: continue
  if len(parts)>=2 and "python" in parts[0] and parts[1].endswith("ingest_erb.py"):
    n+=1
print("ingest_procs", n)
' 2>/dev/null || echo "api down"
