#!/usr/bin/env python3
"""Write duplicate_doc_ids.json (and n400 lift-slope sidecar) from committed inputs."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / "data"
REV1 = ROOT / "artifacts" / "published" / "revision1"
MANIFEST = DATA / "erb_scale_manifest.json"


def duplicate_doc_ids(manifest: dict) -> list[str]:
    counts: Counter[str] = Counter()
    for d in manifest.get("documents") or []:
        did = d.get("doc_id")
        if did:
            counts[str(did)] += 1
    return sorted(did for did, n in counts.items() if n > 1)


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
    ladder = REV1 / "exact_ladder_openai_primary400.json"
    if ladder.is_file():
        import sys
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        import make_paper_tables as mpt
        blob = json.loads(ladder.read_text(encoding="utf-8"))
        runs = mpt.index_runs(blob)
        order = mpt.canonical_question_ids(runs[("raw", 5000)])
        lad = {int(s): (mpt.hit10_list(runs[("raw", int(s))], order), mpt.hit10_list(runs[("meta_in", int(s))], order))
               for s in blob["meta"]["scales"]}
        est, lo, hi = mpt.bootstrap_lift_slope_ci(lad, pct=mpt.CI90)
        slope = {"estimate": round(est, 6), "ci90_lo": round(lo, 6), "ci90_hi": round(hi, 6)}
        slope_payload = {
            "meta": {
                "created_at": created,
                "script": "write_duplicate_doc_ids.py (make_paper_tables.bootstrap_lift_slope_ci, the computation behind Table 13)",
                "source": "artifacts/published/revision1/exact_ladder_openai_primary400.json",
                "method": "OLS of per-scale meta_in minus raw Hit@10 lift on log10 N; 90% paired bootstrap over questions (B=10000, numpy default_rng(42), questions sorted by id)",
            },
            **slope,
        }
        args.slope_out.write_text(json.dumps(slope_payload, indent=2) + "\n", encoding="utf-8")
        print(f"wrote {args.slope_out} estimate={slope['estimate']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
