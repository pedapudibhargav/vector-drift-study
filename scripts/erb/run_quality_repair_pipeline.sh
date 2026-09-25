#!/usr/bin/env bash
# Quality repair pipeline: fix ID collisions → re-sweep → fit → integrity gate → optional LLM.
#
# Usage:
#   ./scripts/erb/run_quality_repair_pipeline.sh
#   ./scripts/erb/run_quality_repair_pipeline.sh --skip-sweep     # only rebuild manifest/primary + offline recompute
#   ./scripts/erb/run_quality_repair_pipeline.sh --with-llm-openai
#   ./scripts/erb/run_quality_repair_pipeline.sh --with-llm-ollama
#
# LLM is NEVER mixed. OpenAI and Ollama are separate optional stages, only after integrity OK.

set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"

SKIP_SWEEP=0
WITH_LLM_OPENAI=0
WITH_LLM_OLLAMA=0
PYTHON="${PYTHON:-}"
[[ -z "$PYTHON" && -x .venv/bin/python ]] && PYTHON=".venv/bin/python"
PYTHON="${PYTHON:-python3}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --skip-sweep) SKIP_SWEEP=1; shift ;;
    --with-llm-openai) WITH_LLM_OPENAI=1; shift ;;
    --with-llm-ollama) WITH_LLM_OLLAMA=1; shift ;;
    -h|--help) sed -n '1,20p' "$0"; exit 0 ;;
    *) echo "Unknown: $1" >&2; exit 2 ;;
  esac
done

if [[ -f .env ]]; then
  set -a
  # shellcheck disable=SC1091
  source <(grep -E '^[A-Za-z_][A-Za-z0-9_]*=' .env | sed 's/\r$//')
  set +a
fi

echo "======== 1) Rebuild manifest + unique primary (eval_id = question_id::type) ========"
"$PYTHON" scripts/erb/rebuild_primary_and_manifest.py

db_ok=0
if [[ "$SKIP_SWEEP" == "0" ]]; then
  echo "======== 2) Scale sweep (raw+meta full ladder, primary-200 unique) ========"
  if command -v docker >/dev/null 2>&1 && docker ps --format '{{.Names}}' 2>/dev/null | grep -q 'vector-drift-api'; then
    echo "Using docker exec vector-drift-api…"
    # Prefer the container's compose-injected DATABASE_URL (do not override with host .env
    # which often points at vector-drift-db / wrong DB name).
    docker exec \
      vector-drift-api \
      python /app/scripts/erb/run_scale_sweep.py \
        --manifest /app/data/erb_scale_manifest.json \
        --primary-questions 200 \
        --scales 5000 10000 15000 20000 25000 40000 50000 75000 100000 \
      && db_ok=1
  else
    echo "Docker API container not running — attempting local sweep if DATABASE_URL works…"
    if PYTHONPATH=apps/api "$PYTHON" - <<'PY'
import asyncio, os
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
url=os.environ.get('DATABASE_URL','postgresql+asyncpg://vector_drift:vector_drift@127.0.0.1:5432/vector_drift')
# Host-side: rewrite docker DNS hostname to localhost
url=url.replace('@vector-drift-postgres:', '@127.0.0.1:').replace('@vector-drift-db:', '@127.0.0.1:')
if url.startswith('postgresql://'):
  url=url.replace('postgresql://','postgresql+asyncpg://',1)
os.environ['DATABASE_URL']=url
async def main():
  eng=create_async_engine(url)
  async with eng.connect() as c:
    n=(await c.execute(text('select count(*) from document_chunks where embedding is not null'))).scalar_one()
  await eng.dispose()
  print('embedded_chunks', n)
  if int(n)<5000: raise SystemExit(2)
asyncio.run(main())
PY
    then
      # Ensure host can reach published postgres port
      export DATABASE_URL="${DATABASE_URL//@vector-drift-postgres:/@127.0.0.1:}"
      export DATABASE_URL="${DATABASE_URL//@vector-drift-db:/@127.0.0.1:}"
      PYTHONPATH=apps/api "$PYTHON" scripts/erb/run_scale_sweep.py \
        --primary-questions 200 \
        --scales 5000 10000 15000 20000 25000 40000 50000 75000 100000 \
        && db_ok=1
    else
      echo "WARN: cannot reach DB with embeddings — will use offline recompute only"
    fi
  fi
fi

echo "======== 3) Publish sweep JSON + fit ========"
RESULTS_DIR="data/results"
# Prefer newest full sweep artifact from results/
LATEST="$(ls -t "$RESULTS_DIR"/erb_*primary*.json 2>/dev/null | head -1 || true)"
if [[ "$db_ok" == "1" && -n "${LATEST}" ]]; then
  cp -f "$LATEST" artifacts/published/erb_full_primary200_to100k.json
  echo "published sweep from $LATEST"
fi

# Always produce corrected view (dedupe + membership) as safety net / offline path
PYTHONPATH=apps/api "$PYTHON" scripts/erb/recompute_metrics_from_published.py \
  --src artifacts/published/erb_full_primary200_to100k.json

# If sweep was re-run with eval_ids, prefer moving corrected → canonical when integrity passes
cp -f artifacts/published/erb_full_primary_corrected.json \
      artifacts/published/erb_full_primary200_to100k.CLEAN.json
cp -f artifacts/published/erb_full_primary_corrected_fit.json \
      artifacts/published/erb_full_primary200_to100k_fit.CLEAN.json

echo "======== 4) Integrity gate ========"
if ! "$PYTHON" scripts/erb/assert_sweep_integrity.py --sweep artifacts/published/erb_full_primary_corrected.json; then
  echo "Integrity gate FAILED — refusing LLM evaluation." >&2
  exit 1
fi

# Promote clean files to canonical names only after gate passes
cp -f artifacts/published/erb_full_primary_corrected.json artifacts/published/erb_full_primary200_to100k.json
cp -f artifacts/published/erb_full_primary_corrected_fit.json artifacts/published/erb_full_primary200_to100k_fit.json
echo "Promoted CLEAN corrected metrics to canonical published JSON."

echo "======== 5) Optional LLM (separate providers) ========"
if [[ "$WITH_LLM_OPENAI" == "1" ]]; then
  echo "--- OpenAI-only wide audit ---"
  ./scripts/erb/run_wide_llm_audit.sh --provider openai --pct 5
fi
if [[ "$WITH_LLM_OLLAMA" == "1" ]]; then
  echo "--- Ollama-only wide audit ---"
  ./scripts/erb/run_wide_llm_audit.sh --provider ollama --pct 5
fi
if [[ "$WITH_LLM_OPENAI" == "0" && "$WITH_LLM_OLLAMA" == "0" ]]; then
  echo "LLM skipped (integrity fixed first). When ready:"
  echo "  ./scripts/erb/run_quality_repair_pipeline.sh --skip-sweep --with-llm-openai"
  echo "  ./scripts/erb/run_quality_repair_pipeline.sh --skip-sweep --with-llm-ollama"
fi

echo "DONE."
