#!/usr/bin/env bash
# Phase-1 research spin: smoke loop + L1 ladder to 40k (primary-200).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
export PATH="/Applications/Docker.app/Contents/Resources/bin:$HOME/.docker/bin:/usr/local/bin:/opt/homebrew/bin:$PATH"
cd "$ROOT"

SCALES=(5000 10000 15000 20000 25000 40000)
LOG_SWEEP=/tmp/erb_phase1_sweep.log
LOG_SMOKE=/tmp/erb_phase1_smoke.log

# Periodic smoke while sweep runs
nohup docker exec \
  -e DATABASE_URL=postgresql://vector_drift:vector_drift@vector-drift-postgres:5432/vector_drift \
  vector-drift-api python /app/scripts/erb/smoke_embed_quality.py --interval 90 \
  >>"$LOG_SMOKE" 2>&1 &
echo smoke_pid=$!

nohup docker exec \
  -e DATABASE_URL=postgresql://vector_drift:vector_drift@vector-drift-postgres:5432/vector_drift \
  -e ERB_BUDGET_CAP_USD=5.50 \
  vector-drift-api python /app/scripts/erb/run_scale_sweep.py \
    --primary-questions 200 \
    --scales "${SCALES[@]}" \
    --top-k 10 \
    --out /app/data/results/erb_phase1_primary200_to40k.json \
  >>"$LOG_SWEEP" 2>&1 &
echo sweep_pid=$!
echo "Monitor: tail -f $LOG_SWEEP"
echo "Smoke:   tail -f $LOG_SMOKE"
