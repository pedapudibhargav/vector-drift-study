#!/usr/bin/env python3
"""Download EnterpriseRAG-Bench questions and document archives."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import urllib.request
import zipfile
from pathlib import Path

from paths import (
    ERB_DIR,
    ERB_DOCS,
    ERB_EXTRA_QUESTIONS,
    ERB_QUESTIONS,
    ERB_ZIPS,
    GITHUB_RAW,
    GITHUB_RELEASES_API,
)

# Prefer direct release asset URLs (avoid GitHub API rate limits).
RELEASE_TAG = "v1.0.0"
RELEASE_ASSET_BASE = (
    f"https://github.com/onyx-dot-app/EnterpriseRAG-Bench/releases/download/{RELEASE_TAG}"
)

SOURCE_TYPES = (
    "slack",
    "gmail",
    "linear",
    "google_drive",
    "hubspot",
    "fireflies",
    "github",
    "jira",
    "confluence",
)


def _download(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and dest.stat().st_size > 0:
        print(f"skip existing {dest}")
        return
    print(f"download {url} -> {dest}")
    tmp = dest.with_suffix(dest.suffix + ".partial")
    req = urllib.request.Request(url, headers={"User-Agent": "erb-drift-study"})
    with urllib.request.urlopen(req, timeout=600) as resp:
        if getattr(resp, "status", 200) >= 400:
            raise RuntimeError(f"HTTP {resp.status} for {url}")
        with tmp.open("wb") as out:
            shutil.copyfileobj(resp, out)
    if tmp.stat().st_size < 100:
        tmp.unlink(missing_ok=True)
        raise RuntimeError(f"download too small for {url}")
    tmp.replace(dest)


def download_questions() -> None:
    ERB_DIR.mkdir(parents=True, exist_ok=True)
    _download(f"{GITHUB_RAW}/questions.jsonl", ERB_QUESTIONS)
    _download(f"{GITHUB_RAW}/extra_questions.jsonl", ERB_EXTRA_QUESTIONS)


def _release_assets() -> list[dict]:
    req = urllib.request.Request(
        GITHUB_RELEASES_API,
        headers={"Accept": "application/vnd.github+json", "User-Agent": "erb-drift-study"},
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        payload = json.loads(resp.read().decode("utf-8"))
    return list(payload.get("assets") or [])


def download_zips(*, all_docs: bool, sources: list[str], max_slices: int | None) -> list[Path]:
    ERB_ZIPS.mkdir(parents=True, exist_ok=True)
    chosen: list[Path] = []

    if all_docs:
        dest = ERB_ZIPS / "all_documents.zip"
        _download(f"{RELEASE_ASSET_BASE}/all_documents.zip", dest)
        return [dest]

    # Known slice naming from v1.0.0 release; try sequential indices until 404.
    for source in sources:
        found = 0
        for idx in range(1, 64):
            if max_slices is not None and found >= max_slices:
                break
            name = f"{source}_slice_{idx:04d}.zip"
            dest = ERB_ZIPS / name
            url = f"{RELEASE_ASSET_BASE}/{name}"
            try:
                _download(url, dest)
            except Exception as exc:
                if dest.exists():
                    dest.unlink(missing_ok=True)
                # stop this source when slice missing
                print(f"stop {source} at slice {idx}: {exc}")
                break
            chosen.append(dest)
            found += 1

    if not chosen:
        # Fallback: GitHub Releases API (may be rate-limited)
        try:
            assets = _release_assets()
            by_name = {a["name"]: a for a in assets if a.get("browser_download_url")}
            for source in sources:
                slices = sorted(
                    name
                    for name in by_name
                    if name.startswith(f"{source}_slice_") and name.endswith(".zip")
                )
                if max_slices is not None:
                    slices = slices[:max_slices]
                for name in slices:
                    dest = ERB_ZIPS / name
                    _download(by_name[name]["browser_download_url"], dest)
                    chosen.append(dest)
        except Exception as exc:
            raise SystemExit(
                f"Zip download failed ({exc}). Pass --zip-dir with local release assets."
            ) from exc

    if not chosen:
        raise SystemExit(
            "No release zip assets found. Check GitHub releases for "
            "onyx-dot-app/EnterpriseRAG-Bench or pass --zip-dir with local files."
        )
    return chosen


def extract_zips(zips: list[Path], *, clean: bool) -> int:
    if clean and ERB_DOCS.exists():
        shutil.rmtree(ERB_DOCS)
    ERB_DOCS.mkdir(parents=True, exist_ok=True)
    count = 0
    for zpath in zips:
        print(f"extract {zpath.name}")
        with zipfile.ZipFile(zpath, "r") as zf:
            for info in zf.infolist():
                if info.is_dir() or not info.filename.lower().endswith(".txt"):
                    continue
                name = Path(info.filename).name
                if not name.startswith("dsid_"):
                    # keep path-derived source when nested
                    pass
                target = ERB_DOCS / name
                if target.exists():
                    continue
                with zf.open(info) as src, target.open("wb") as dst:
                    shutil.copyfileobj(src, dst)
                # side-car source type from zip path or zip name
                source = _infer_source(info.filename, zpath.name)
                side = target.with_suffix(".source")
                side.write_text(source + "\n", encoding="utf-8")
                count += 1
    print(f"extracted {count} documents into {ERB_DOCS}")
    return count


def _infer_source(member: str, zip_name: str) -> str:
    parts = Path(member).parts
    for p in parts:
        key = p.lower().replace("-", "_")
        if key in SOURCE_TYPES:
            return key
    for source in SOURCE_TYPES:
        if zip_name.lower().startswith(source):
            return source
    return "unknown"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--questions-only", action="store_true")
    parser.add_argument("--all-docs", action="store_true", help="Download all_documents.zip")
    parser.add_argument(
        "--sources",
        nargs="+",
        default=["confluence", "jira", "linear", "github", "google_drive"],
        help="Source types for slice downloads (smoke-friendly default)",
    )
    parser.add_argument("--max-slices", type=int, default=1, help="Slices per source (default 1)")
    parser.add_argument("--extract", action="store_true", help="Extract downloaded zips")
    parser.add_argument("--clean-docs", action="store_true")
    parser.add_argument("--zip-dir", type=Path, help="Use local zip directory instead of download")
    args = parser.parse_args()

    download_questions()
    if args.questions_only:
        return 0

    if args.zip_dir:
        zips = sorted(args.zip_dir.glob("*.zip"))
        if not zips:
            raise SystemExit(f"No zips in {args.zip_dir}")
    else:
        zips = download_zips(
            all_docs=args.all_docs,
            sources=args.sources,
            max_slices=None if args.all_docs else args.max_slices,
        )

    if args.extract or args.zip_dir:
        extract_zips(zips, clean=args.clean_docs)
    return 0


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    raise SystemExit(main())
