#!/usr/bin/env python3
"""Revision 1: verify that the table fragments included by main.tex are exactly the generated ones.

Every table of the revised manuscript is generated from the artifacts by
scripts/erb/revision1/make_paper_tables.py into artifacts/published/revision1/paper_tables/ and copied to
papers/ieee-vector-drift/access/generated/. This script fails if a copy differs from its source or if main.tex
includes a fragment that does not exist (the first-version script is verify_paper_tables_v1.py).
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "artifacts" / "published" / "revision1" / "paper_tables"
DST = ROOT / "papers" / "ieee-vector-drift" / "access" / "generated"
TEX = ROOT / "papers" / "ieee-vector-drift" / "access" / "main.tex"

errors: list[str] = []
if not SRC.is_dir() or not DST.is_dir():
    print("paper_tables or generated directory missing", file=sys.stderr)
    sys.exit(2)
for f in sorted(SRC.glob("tab_*.tex")):
    g = DST / f.name
    if not g.is_file():
        errors.append(f"missing in manuscript folder: {f.name}")
    elif f.read_bytes() != g.read_bytes():
        errors.append(f"differs from generated source: {f.name}")
tex = TEX.read_text(encoding="utf-8")
for name in re.findall(r"\\input\{generated/([A-Za-z0-9_]+)\}", tex):
    if not (SRC / f"{name}.tex").is_file():
        errors.append(f"main.tex includes unknown fragment: {name}")
if errors:
    print("FAIL")
    print("\n".join(errors))
    sys.exit(1)
print(f"OK: {len(list(SRC.glob('tab_*.tex')))} fragments identical to their generated sources")
