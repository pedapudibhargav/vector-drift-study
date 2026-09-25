#!/usr/bin/env bash
# Stop ollama ERB ingest workers inside vector-drift-api.
set -euo pipefail
export PATH="/Applications/Docker.app/Contents/Resources/bin:$HOME/.docker/bin:/usr/local/bin:/opt/homebrew/bin:$PATH"
docker exec vector-drift-api python3 -c '
import glob, os, signal, time
for c in glob.glob("/proc/[0-9]*/cmdline"):
  try: parts=open(c,"rb").read().replace(b"\0",b" ").decode(errors="ignore").split()
  except Exception: continue
  if len(parts)>=2 and "python" in parts[0] and parts[1].endswith("ingest_erb_ollama.py"):
    os.kill(int(c.split("/")[2]), signal.SIGTERM)
    print("SIGTERM", c.split("/")[2])
time.sleep(1)
' 2>/dev/null || true
pkill -f 'ingest_erb_ollama.py' 2>/dev/null || true
echo "ollama ingest stop requested"
