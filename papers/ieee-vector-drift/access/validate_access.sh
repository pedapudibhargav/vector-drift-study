#!/usr/bin/env bash
# IEEE Access local validation helper
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

# TinyTeX / MacTeX often installed but not on PATH in non-interactive shells
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

echo "== toolchain =="
for c in pdflatex chktex pdfinfo pdftotext pdffonts; do
  if command -v "$c" >/dev/null 2>&1; then
    echo "OK  $c -> $(command -v "$c")"
  else
    echo "MISS $c"
  fi
done

if [[ ! -f ieeeaccess.cls ]]; then
  echo
  echo "WARN: ieeeaccess.cls missing."
  echo "  1) Download official zip (may require browser if CDN blocks curl):"
  echo "     https://ieeeaccess.ieee.org/wp-content/uploads/2026/05/ACCESS_latex_template_20260513-1-1.zip"
  echo "  2) Or open Overleaf template and download source:"
  echo "     https://www.overleaf.com/latex/templates/ieee-access-latex-template/cdxrhtbjgszv"
  echo "  3) Unzip into this directory (ieeeaccess.cls + logo PNGs)."
  echo "  Drafting can proceed with IEEEtran.cls fallback already in main.tex."
fi

echo
echo "== source checks =="
python3 validate_access.py --root "$ROOT" || true

if command -v chktex >/dev/null 2>&1; then
  echo
  echo "== chktex =="
  chktex -q main.tex || true
fi

if command -v pdflatex >/dev/null 2>&1; then
  echo
  echo "== build (pdflatex x2) =="
  pdflatex -interaction=nonstopmode main.tex >/tmp/access_build1.log || true
  pdflatex -interaction=nonstopmode main.tex >/tmp/access_build2.log || true
  python3 validate_access.py --root "$ROOT" --pdf "$ROOT/main.pdf" || true
else
  echo
  echo "SKIP build: pdflatex not installed. Suggested:"
  echo "  brew install --cask mactex-no-gui"
  echo "  # then reopen terminal so /Library/TeX/texbin is on PATH"
fi
