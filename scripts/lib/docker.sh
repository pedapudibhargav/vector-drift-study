#!/usr/bin/env bash
# Resolve Docker CLI on macOS (Docker Desktop) and Linux.
if [[ -n "${DOCKER:-}" && -x "${DOCKER}" ]]; then
  :
elif command -v docker >/dev/null 2>&1; then
  DOCKER="$(command -v docker)"
elif [[ -x /Applications/Docker.app/Contents/Resources/bin/docker ]]; then
  DOCKER=/Applications/Docker.app/Contents/Resources/bin/docker
else
  echo "ERROR: docker not found. Set DOCKER=/path/to/docker or install Docker Desktop." >&2
  exit 1
fi

export DOCKER

ensure_ingest_container() {
  local container="${1:-vector-drift-api}"
  local service="${2:-vector-drift-api}"
  if "${DOCKER}" ps --format '{{.Names}}' | grep -qx "${container}"; then
    return 0
  fi
  echo "==> Container '${container}' is not running — starting via docker compose ..."
  if ! "${DOCKER}" compose up -d "${service}"; then
    echo "ERROR: failed to start '${service}'. Is Docker Desktop running?" >&2
    return 1
  fi
  local i
  for i in $(seq 1 150); do
    if ! "${DOCKER}" inspect -f '{{.State.Running}}' "${container}" 2>/dev/null | grep -qx true; then
      sleep 2
      continue
    fi
    if "${DOCKER}" exec "${container}" python -c "import docling" >/dev/null 2>&1 \
      || "${DOCKER}" exec "${container}" python -c \
        "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/health', timeout=3)" \
        >/dev/null 2>&1; then
      echo "==> ${container} is ready."
      return 0
    fi
    sleep 2
  done
  echo "ERROR: ${container} did not become ready within 300s. Check: docker logs ${container}" >&2
  return 1
}
