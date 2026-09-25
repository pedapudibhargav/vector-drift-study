#!/usr/bin/env bash
# Local dev helper — reads mirror overrides from .env, falls back to public registries.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [ -f .env ]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

NPM_REG="${NPM_REGISTRY:-https://registry.npmjs.org/}"
PYPI_URL="${PYPI_INDEX_URL:-https://pypi.org/simple/}"

echo "NPM registry:  ${NPM_REG}"
echo "PyPI index:    ${PYPI_URL}"

case "${1:-}" in
  install-web)
    cd apps/web
    npm install --registry "${NPM_REG}"
    ;;
  install-api)
    python3.12 -m venv .venv 2>/dev/null || python3 -m venv .venv
    # shellcheck disable=SC1091
    source .venv/bin/activate
    if [ -n "${PIP_TRUSTED_HOST:-}" ]; then
      pip install --index-url "${PYPI_URL}" --trusted-host "${PIP_TRUSTED_HOST}" -r apps/api/requirements.txt
    else
      pip install --index-url "${PYPI_URL}" -r apps/api/requirements.txt
    fi
    ;;
  docker)
    export PATH="/usr/local/bin:/Applications/Docker.app/Contents/Resources/bin:${PATH}"
    docker compose up --build
    ;;
  *)
    echo "Usage: $0 {install-web|install-api|docker}"
    exit 1
    ;;
esac
