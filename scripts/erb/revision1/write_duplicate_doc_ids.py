#!/usr/bin/env python3
"""Write duplicate_doc_ids.json (and n400 lift-slope sidecar) from committed inputs."""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / "data"
REV1 = ROOT / "artifacts" / "published" / "revision1"
MANIFEST = DATA / "erb_scale_manifest.json"
TAB_EQUIV = REV1 / "paper_tables" / "tab_equiv.tex"


def duplicate_doc_ids(manifest: dict) -> list[str]:
    counts: Counter[str] = Counter()
    for d in manifest.get("documents") or []:
        did = d.get("doc_id")
        if did:
            counts[str(did)] += 1
    return sorted(did for did, n in counts.items() if n > 1)


def parse_n400_lift_slope(tex: str) -> dict[str, float]:
    m = re.search(
        r"Lift slope per tenfold \$N\$, OpenAI \$n\{=\}400\$\s*&\s*(-?[0-9.]+)\s*&\s*\$\[(-?[0-9.]+),\s*(-?[0-9.]+)\]\$",
        tex,
    )
    if not m:
        raise SystemExit("could not parse n=400 lift slope from tab_equiv.tex")
    return {
        "estimate": float(m.group(1)),
        "ci90_lo": float(m.group(2)),
        "ci90_hi": float(m.group(3)),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=MANIFEST)
    parser.add_argument("--out", type=Path, default=REV1 / "duplicate_doc_ids.json")
    parser.add_argument("--slope-out", type=Path, default=REV1 / "n400_lift_slope.json")
    args = parser.parse_args(argv)
    created = datetime.now(timezone.utc).isoformat()
    if not args.manifest.is_file():
        payload = {
            "meta": {
                "created_at": created,
                "script": "write_duplicate_doc_ids.py",
                "skipped": True,
                "skip_reason": "manifest_missing",
            },
            "duplicate_doc_ids": [],
            "n_duplicate_doc_ids": 0,
        }
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        print(f"SKIP wrote empty {args.out} (manifest missing)")
        return 0
    man = json.loads(args.manifest.read_text(encoding="utf-8"))
    dups = duplicate_doc_ids(man)
    payload = {
        "meta": {
            "created_at": created,
            "script": "write_duplicate_doc_ids.py",
            "manifest": str(args.manifest.relative_to(ROOT)) if ROOT in args.manifest.parents else str(args.manifest),
        },
        "duplicate_doc_ids": dups,
        "n_duplicate_doc_ids": len(dups),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {args.out} n={len(dups)}")
    if TAB_EQUIV.is_file():
        slope = parse_n400_lift_slope(TAB_EQUIV.read_text(encoding="utf-8"))
        slope_payload = {
            "meta": {
                "created_at": created,
                "script": "write_duplicate_doc_ids.py",
                "source": "artifacts/published/revision1/paper_tables/tab_equiv.tex",
            },
            **slope,
        }
        args.slope_out.write_text(json.dumps(slope_payload, indent=2) + "\n", encoding="utf-8")
        print(f"wrote {args.slope_out} estimate={slope['estimate']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
