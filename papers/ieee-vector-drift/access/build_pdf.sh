#!/usr/bin/env bash
# Build IEEE Access main.pdf (pdflatex x2). Auto-detects TinyTeX on macOS.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

if ! command -v pdflatex >/dev/null 2>&1; then
  for d in \
    "$HOME/Library/TinyTeX/bin/universal-darwin" \
    "$HOME/Library/TinyTeX/bin/x86_64-darwin" \
    "/Library/TeX/texbin"
  do
    if [[ -x "$d/pdflatex" ]]; then
      export PATH="$d:$PATH"
      break
    fi
  done
fi

if ! command -v pdflatex >/dev/null 2>&1; then
  echo "ERROR: pdflatex not found."
  echo "  brew install --cask mactex-no-gui"
  echo "  # or ensure TinyTeX is installed: https://yihui.org/tinytex/"
  exit 1
fi

echo "Using pdflatex: $(command -v pdflatex)"
pdflatex -interaction=nonstopmode main.tex
pdflatex -interaction=nonstopmode main.tex
python3 validate_access.py --root "$ROOT" --pdf "$ROOT/main.pdf" || true
pages="$(pdfinfo main.pdf 2>/dev/null | awk '/^Pages:/ {print $2}')"
echo "Built: $ROOT/main.pdf (${pages:-?} pages)"
