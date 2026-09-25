#!/usr/bin/env python3
"""IEEE Access local pre-submission checks (source + optional PDF).

Guidelines encoded here:
  - Abstract: one paragraph, 150--250 words, no \\cite
  - Index terms: 4--6 comma-separated keywords
  - Target length: 8--16 double-column pages (warn if PDF outside)
  - Prefer ieeeaccess.cls; allow IEEEtran journal fallback with warning

PDF tooling (after brew install):
  pdfinfo / pdftotext / pdffonts  (poppler)
  chktex main.tex
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
from pathlib import Path


def abstract_stats(tex: str) -> dict:
    m = re.search(r"\\begin\{abstract\}(.*?)\\end\{abstract\}", tex, re.S)
    if not m:
        return {"ok": False, "error": "missing abstract"}
    body = m.group(1)
    has_cite = bool(re.search(r"\\cite[a-z]*\{", body))
    plain = re.sub(r"\\[a-zA-Z]+\*?(\[[^\]]*\])?(\{[^}]*\})?", " ", body)
    plain = re.sub(r"[{}$\\]", " ", plain)
    words = plain.split()
    n = len(words)
    return {
        "ok": (150 <= n <= 250) and (not has_cite),
        "words": n,
        "has_cite": has_cite,
        "range": "150-250",
    }


def keywords_stats(tex: str) -> dict:
    m = re.search(r"\\begin\{keywords\}(.*?)\\end\{keywords\}", tex, re.S)
    if not m:
        m = re.search(r"\\begin\{IEEEkeywords\}(.*?)\\end\{IEEEkeywords\}", tex, re.S)
    if not m:
        return {"ok": False, "error": "missing keywords"}
    body = re.sub(r"%.*", "", m.group(1))
    body = re.sub(r"\\[a-zA-Z]+\{([^}]*)\}", r"\1", body)
    body = re.sub(r"\s+", " ", body).strip()
    kws = [k.strip() for k in body.split(",") if k.strip() and "Enter key" not in k]
    return {
        "ok": 4 <= len(kws) <= 6,
        "count": len(kws),
        "keywords": kws,
        "note": "Confirm each term against the IEEE Thesaurus before submission",
    }


def check_tex(path: Path) -> dict:
    tex = path.read_text(encoding="utf-8")
    issues: list[str] = []
    uses_access = "\\documentclass{ieeeaccess}" in tex or "ieeeaccess.cls" in tex
    cls_present = (path.parent / "ieeeaccess.cls").exists()
    if not uses_access and not cls_present:
        issues.append("ieeeaccess.cls not found — using IEEEtran fallback; drop official Access zip into access/ for camera-ready")
    abs_s = abstract_stats(tex)
    if not abs_s.get("ok"):
        issues.append(f"abstract words={abs_s.get('words')} cite={abs_s.get('has_cite')} (need 150-250, no cites)")
    kw_s = keywords_stats(tex)
    if not kw_s.get("ok"):
        issues.append(f"keywords count={kw_s.get('count')} (need 4-6)")
    for fig in re.findall(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}", tex):
        p = (path.parent / fig).resolve()
        if not p.exists():
            issues.append(f"missing figure {fig}")
    return {
        "abstract": abs_s,
        "keywords": kw_s,
        "ieeeaccess_cls_present": cls_present,
        "issues": issues,
    }


def check_pdf(pdf: Path) -> dict:
    out: dict = {"path": str(pdf), "exists": pdf.exists()}
    if not pdf.exists():
        out["issues"] = ["PDF not built yet"]
        return out
    issues: list[str] = []
    pdfinfo = shutil.which("pdfinfo")
    pdffonts = shutil.which("pdffonts")
    if pdfinfo:
        r = subprocess.run([pdfinfo, str(pdf)], capture_output=True, text=True)
        pages = None
        for line in r.stdout.splitlines():
            if line.startswith("Pages:"):
                pages = int(line.split(":")[1].strip())
            if line.startswith("Page size:"):
                out["page_size"] = line.split(":", 1)[1].strip()
        out["pages"] = pages
        if pages is not None and not (8 <= pages <= 16):
            issues.append(f"pages={pages} outside Access target 8-16 (warn; not hard reject)")
        elif pages is not None and pages < 8:
            issues.append(f"pages={pages} < 8 — risk of desk reject for insufficient depth")
    else:
        issues.append("pdfinfo not installed (brew install poppler)")
    if pdffonts:
        r = subprocess.run([pdffonts, str(pdf)], capture_output=True, text=True)
        lines = [ln for ln in r.stdout.splitlines()[2:] if ln.strip()]
        not_embedded = [ln for ln in lines if "no" in ln.lower().split()[len(ln.split()) - 4 :]]
        # simpler: look for emb column
        bad = []
        for ln in lines:
            cols = ln.split()
            if len(cols) >= 7 and cols[4] in {"no", "No"}:
                bad.append(cols[0])
        if bad:
            issues.append(f"fonts not embedded: {bad[:5]}")
        out["font_rows"] = len(lines)
    else:
        issues.append("pdffonts not installed (brew install poppler)")
    out["issues"] = issues
    return out


def run_chktex(tex: Path) -> dict:
    chktex = shutil.which("chktex")
    if not chktex:
        return {"ok": None, "error": "chktex not installed (brew install chktex)"}
    r = subprocess.run([chktex, "-q", "-v0", str(tex)], capture_output=True, text=True)
    warnings = [ln for ln in r.stdout.splitlines() if ln.strip()]
    return {"ok": len(warnings) == 0, "warning_count": len(warnings), "sample": warnings[:20]}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", type=Path, default=Path(__file__).resolve().parent)
    ap.add_argument("--pdf", type=Path, default=None)
    args = ap.parse_args()
    tex = args.root / "main.tex"
    pdf = args.pdf or (args.root / "main.pdf")
    report = {
        "venue": "IEEE Access",
        "tex": check_tex(tex) if tex.exists() else {"issues": ["main.tex missing"]},
        "chktex": run_chktex(tex) if tex.exists() else {},
        "pdf": check_pdf(pdf),
        "online_tools": [
            "IEEE Author Portal submission requires matching LaTeX/Word + PDF",
            "Paperpal Preflight (grammar): linked from ieeeaccess.ieee.org preparing-your-article",
            "Official LaTeX zip: https://ieeeaccess.ieee.org/wp-content/uploads/2026/05/ACCESS_latex_template_20260513-1-1.zip",
            "Overleaf template: https://www.overleaf.com/latex/templates/ieee-access-latex-template/cdxrhtbjgszv",
        ],
        "install": [
            "brew install --cask mactex-no-gui   # pdflatex / IEEEtran ecosystem",
            "brew install poppler chktex",
        ],
    }
    issues = list(report["tex"].get("issues") or [])
    # PDF absence is expected before TeX install; only hard-fail PDF issues when PDF exists
    pdf_issues = list(report["pdf"].get("issues") or [])
    if report["pdf"].get("exists"):
        issues.extend(pdf_issues)
    elif pdf_issues and pdf_issues != ["PDF not built yet"]:
        issues.extend(pdf_issues)
    print(json.dumps(report, indent=2))
    print(f"ACCESS_GATE={'FAIL' if issues else 'OK'} issues={len(issues)}")
    if not report["pdf"].get("exists"):
        print("NOTE: PDF not built yet — install MacTeX and rerun ./validate_access.sh")
    return 1 if issues else 0


if __name__ == "__main__":
    raise SystemExit(main())
