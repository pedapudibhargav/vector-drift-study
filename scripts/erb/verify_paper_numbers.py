#!/usr/bin/env python3
"""Revision 1: verify that the headline numbers of main.tex match the artifacts.

The first-version script compared the manuscript with the HNSW sweep; those numbers are no longer the
primary results (see verify_paper_numbers_v1.py). The check now lives in the revision-1 validation harness:
every registered claim must match its artifact value AND appear as a literal string in main.tex.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TEX = ROOT / "papers" / "ieee-vector-drift" / "access" / "main.tex"
HARNESS = ROOT / "scripts" / "erb" / "revision1" / "validate_all.py"

if not HARNESS.is_file():
    print("validate_all.py not found: revision-1 scripts are missing from this checkout", file=sys.stderr)
    sys.exit(2)
sys.exit(subprocess.run([sys.executable, "-I", str(HARNESS), "--checks", "CLAIM_REGISTRY", "--tex", str(TEX)]).returncode)
