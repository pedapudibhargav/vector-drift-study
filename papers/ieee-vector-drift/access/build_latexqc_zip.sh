#!/usr/bin/env bash
# Package IEEE Access sources for https://latexqc.ieee.org/upload
# Upload the generated zip (not the PDF alone).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"
OUT="${OUT:-${ROOT}/ieee_access_latexqc.zip}"
STAGE="$(mktemp -d)"

FIGSRC="${ROOT}/figures"
[[ -L "$FIGSRC" ]] && FIGSRC="$(cd "$FIGSRC" && pwd -P)"

mkdir -p "$STAGE/figures"
cp main.tex ieeeaccess.cls IEEEtran.cls IEEEtran.bst spotcolor.sty author.jpg \
   logo.png bullet.png notaglinelogo.png \
   t1-*.pfb t1-*.tfm t1-*.map t1*.fd "$STAGE/"
# copy exactly the figures and generated table fragments that main.tex uses
for f in $(grep -o 'figures/[A-Za-z0-9_]*\.pdf' main.tex | sort -u); do cp "$ROOT/$f" "$STAGE/figures/"; done
mkdir -p "$STAGE/generated"
for f in $(grep -o 'generated/[A-Za-z0-9_]*' main.tex | sort -u); do cp "$ROOT/$f.tex" "$STAGE/generated/"; done

rm -f "$OUT"
(cd "$STAGE" && zip -r "$OUT" . -x "*.DS_Store")
rm -rf "$STAGE"

echo "Created: $OUT"
echo "Size: $(du -h "$OUT" | awk '{print $1}')"
echo ""
echo "Zip must contain main.tex at root (not PDF-only). Verify:"
unzip -l "$OUT" | grep -E 'main\.tex|figures/|generated/'
echo ""
echo "Upload: https://latexqc.ieee.org/upload"
