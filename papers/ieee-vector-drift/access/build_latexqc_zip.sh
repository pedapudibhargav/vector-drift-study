#!/usr/bin/env bash
# Package IEEE Access sources for https://latexqc.ieee.org/upload
# Upload the generated zip (not the PDF alone).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"
OUT="${ROOT}/ieee_access_latexqc.zip"
STAGE="$(mktemp -d)"

FIGSRC="${ROOT}/figures"
[[ -L "$FIGSRC" ]] && FIGSRC="$(cd "$FIGSRC" && pwd -P)"

mkdir -p "$STAGE/figures"
cp main.tex ieeeaccess.cls IEEEtran.cls IEEEtran.bst spotcolor.sty author.jpg \
   logo.png bullet.png notaglinelogo.png \
   t1-*.pfb t1-*.tfm t1-*.map t1*.fd "$STAGE/"
cp "$FIGSRC"/fig1_hit_vs_logN.png "$FIGSRC"/fig2_delta_meta.png "$FIGSRC"/fig3_rank_erosion.png \
   "$STAGE/figures/"

rm -f "$OUT"
(cd "$STAGE" && zip -r "$OUT" . -x "*.DS_Store")
rm -rf "$STAGE"

echo "Created: $OUT"
echo "Size: $(du -h "$OUT" | awk '{print $1}')"
echo ""
echo "Zip must contain main.tex at root (not PDF-only). Verify:"
unzip -l "$OUT" | rg 'main\.tex|figures/'
echo ""
echo "Upload: https://latexqc.ieee.org/upload"
