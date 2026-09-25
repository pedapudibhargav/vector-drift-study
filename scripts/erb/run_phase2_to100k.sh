#!/usr/bin/env bash
# Phase-2: continue primary-200 ladder 50k → 75k → 100k (raw+meta) with periodic smoke.
# Assumes Phase-1 reconciliation passed (clean CIs from to40k fit).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
export PATH="/Applications/Docker.app/Contents/Resources/bin:$HOME/.docker/bin:/usr/local/bin:/opt/homebrew/bin:$PATH"
cd "$ROOT"

SCALES=(50000 75000 100000)
LOG_SWEEP=/tmp/erb_phase2_sweep.log
LOG_SMOKE=/tmp/erb_phase2_smoke.log
OUT=/app/data/results/erb_phase2_primary200_50_75_100k.json

: >"$LOG_SWEEP"
: >"$LOG_SMOKE"

nohup docker exec \
  -e DATABASE_URL=postgresql://vector_drift:vector_drift@vector-drift-postgres:5432/vector_drift \
  vector-drift-api python /app/scripts/erb/smoke_embed_quality.py --interval 120 \
  >>"$LOG_SMOKE" 2>&1 &
echo smoke_pid=$!

nohup docker exec \
  -e DATABASE_URL=postgresql://vector_drift:vector_drift@vector-drift-postgres:5432/vector_drift \
  -e ERB_BUDGET_CAP_USD=5.50 \
  vector-drift-api python /app/scripts/erb/run_scale_sweep.py \
    --primary-questions 200 \
    --scales "${SCALES[@]}" \
    --top-k 10 \
    --out "$OUT" \
  >>"$LOG_SWEEP" 2>&1 &
echo sweep_pid=$!
echo "Phase-2 scales: ${SCALES[*]}"
echo "Monitor: tail -f $LOG_SWEEP"
echo "Smoke:   tail -f $LOG_SMOKE"
