#!/usr/bin/env bash
# Wide L4 LLM audit — runs OUTSIDE the Cursor agent sandbox.
#
# Alternative when the agent cannot reach api.openai.com (proxy 403):
#   1) Prefer local Ollama (OpenAI-compatible, $0, no proxy)
#   2) Else OpenAI with AUDIT_LLM_BUDGET_USD cap (default $2)
#
# Usage:
#   ./scripts/erb/run_wide_llm_audit.sh
#   ./scripts/erb/run_wide_llm_audit.sh --dry-run
#   ./scripts/erb/run_wide_llm_audit.sh --pct 5 --provider ollama
#   ./scripts/erb/run_wide_llm_audit.sh --provider openai
#
# Outputs:
#   artifacts/published/llm_audit_report.json
#   artifacts/published/llm_audit_report.md
#   Postgres study_evaluations (if DATABASE_URL / docker DB is up)

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"

PCT="${PCT:-5}"
PROVIDER="${PROVIDER:-auto}"   # auto | ollama | openai
DRY_RUN=0
LIMIT=0
OLLAMA_MODEL="${OLLAMA_MODEL:-qwen2.5:7b-instruct}"
OPENAI_MODEL="${OPENAI_MODEL:-gpt-4o}"
BUDGET="${AUDIT_LLM_BUDGET_USD:-2.0}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run) DRY_RUN=1; shift ;;
    --pct) PCT="$2"; shift 2 ;;
    --provider) PROVIDER="$2"; shift 2 ;;
    --limit) LIMIT="$2"; shift 2 ;;
    --ollama-model) OLLAMA_MODEL="$2"; shift 2 ;;
    --openai-model) OPENAI_MODEL="$2"; shift 2 ;;
    -h|--help)
      sed -n '1,25p' "$0"
      exit 0
      ;;
    *) echo "Unknown arg: $1" >&2; exit 2 ;;
  esac
done

# Load .env without printing secrets
if [[ -f .env ]]; then
  set -a
  # shellcheck disable=SC1091
  source <(grep -E '^[A-Za-z_][A-Za-z0-9_]*=' .env | sed 's/\r$//')
  set +a
fi

PYTHON="${PYTHON:-}"
if [[ -z "$PYTHON" ]]; then
  if [[ -x .venv/bin/python ]]; then
    PYTHON=".venv/bin/python"
  else
    PYTHON="python3"
  fi
fi

ensure_corrected_metrics() {
  if [[ ! -f artifacts/published/erb_full_primary_corrected.json ]]; then
    echo "==> Recomputing corrected metrics from published sweep…"
    PYTHONPATH=apps/api "$PYTHON" scripts/erb/recompute_metrics_from_published.py
  fi
}

ollama_up() {
  curl -sf --connect-timeout 2 http://127.0.0.1:11434/api/tags >/dev/null 2>&1
}

start_ollama() {
  if ollama_up; then
    return 0
  fi
  if ! command -v ollama >/dev/null 2>&1; then
    return 1
  fi
  echo "==> Starting ollama serve…"
  nohup ollama serve >/tmp/ollama-audit-serve.log 2>&1 &
  for _ in $(seq 1 30); do
    if ollama_up; then
      echo "==> Ollama ready"
      return 0
    fi
    sleep 0.5
  done
  echo "WARN: ollama serve did not become ready; see /tmp/ollama-audit-serve.log" >&2
  return 1
}

ensure_ollama_model() {
  local model="$1"
  local tags
  tags="$(curl -sf http://127.0.0.1:11434/api/tags || true)"
  if echo "$tags" | grep -Fq "\"name\":\"${model}\""; then
    return 0
  fi
  if echo "$tags" | grep -Fq "$model"; then
    return 0
  fi
  echo "==> Pulling Ollama model: $model (one-time)…"
  ollama pull "$model"
}

openai_reachable() {
  local key="${OPENAI_API_KEY:-}"
  if [[ -z "$key" || "$key" == sk-your* ]]; then
    return 1
  fi
  # Direct call; do not force corp proxy if it 403s CONNECT
  env -u HTTP_PROXY -u HTTPS_PROXY -u ALL_PROXY -u http_proxy -u https_proxy -u all_proxy \
    curl -sf --connect-timeout 8 \
      -H "Authorization: Bearer ${key}" \
      https://api.openai.com/v1/models >/dev/null 2>&1
}

pick_provider() {
  case "$PROVIDER" in
    ollama|openai) echo "$PROVIDER"; return ;;
    auto) ;;
    *) echo "Invalid --provider $PROVIDER (auto|ollama|openai)" >&2; exit 2 ;;
  esac

  if start_ollama; then
    echo "ollama"
    return
  fi
  if openai_reachable; then
    echo "openai"
    return
  fi
  echo "ERROR: Neither Ollama (localhost:11434) nor OpenAI is reachable." >&2
  echo "  Fix: brew services start ollama   OR   ensure OPENAI_API_KEY works outside Cursor." >&2
  exit 1
}

ensure_corrected_metrics

CHOSEN="$(pick_provider)"
echo "==> Provider: $CHOSEN"

export AUDIT_LLM_BUDGET_USD="$BUDGET"
EXTRA_ARGS=(--wide --pct "$PCT")
if [[ "$LIMIT" != "0" ]]; then
  EXTRA_ARGS+=(--limit "$LIMIT")
fi
if [[ "$DRY_RUN" == "1" ]]; then
  EXTRA_ARGS+=(--dry-run)
fi

if [[ "$CHOSEN" == "ollama" ]]; then
  ensure_ollama_model "$OLLAMA_MODEL"
  export AUDIT_LLM_BASE_URL="http://127.0.0.1:11434/v1"
  export AUDIT_LLM_MODEL="$OLLAMA_MODEL"
  # Ollama is free — raise soft cap so wide runs are not truncated by $2 OpenAI accounting
  export AUDIT_LLM_BUDGET_USD="${AUDIT_LLM_BUDGET_USD_OLLAMA:-50}"
  export AUDIT_LLM_PRICE_IN_PER_1M="${AUDIT_LLM_PRICE_IN_PER_1M:-0}"
  export AUDIT_LLM_PRICE_OUT_PER_1M="${AUDIT_LLM_PRICE_OUT_PER_1M:-0}"
  export OPENAI_API_KEY="${OPENAI_API_KEY:-ollama}"
  # Avoid Metal OOM in constrained sessions; set AUDIT_OLLAMA_NUM_GPU=-1 for full GPU
  export AUDIT_OLLAMA_NUM_GPU="${AUDIT_OLLAMA_NUM_GPU:-0}"
  echo "==> Ollama model=$AUDIT_LLM_MODEL base=$AUDIT_LLM_BASE_URL num_gpu=$AUDIT_OLLAMA_NUM_GPU (cost \$0)"
else
  export AUDIT_LLM_MODEL="$OPENAI_MODEL"
  unset AUDIT_LLM_BASE_URL || true
  echo "==> OpenAI model=$AUDIT_LLM_MODEL budget=\$$AUDIT_LLM_BUDGET_USD"
fi

echo "==> Running wide audit (${PCT}% of corrected matrix)…"
REPORT_STEM="llm_audit_report_${CHOSEN}"
EXTRA_ARGS+=(--report-stem "$REPORT_STEM")
PYTHONPATH=apps/api "$PYTHON" scripts/erb/run_audit_llm_batch.py "${EXTRA_ARGS[@]}"

REPORT="artifacts/published/${REPORT_STEM}.json"
MD="artifacts/published/${REPORT_STEM}.md"
echo ""
echo "==> Done."
echo "    JSON: $REPORT"
echo "    MD:   $MD"
if [[ -f "$REPORT" ]]; then
  REPORT_PATH="$REPORT" PYTHONPATH=apps/api "$PYTHON" - <<'PY'
import json, os
from pathlib import Path
r = json.loads(Path(os.environ["REPORT_PATH"]).read_text())
print(f"    evaluated={r.get('n_evaluated')} spent_usd={r.get('spent_usd')} labels={r.get('label_counts')}")
print(f"    flagged={r.get('n_flagged')} issues={r.get('pipeline_issue_counts')}")
print(f"    draft: {(r.get('paper_paragraph_draft') or '')[:240]}…")
PY
fi
echo ""
echo "Open Review UI → LLM results: http://localhost:5173/review"
