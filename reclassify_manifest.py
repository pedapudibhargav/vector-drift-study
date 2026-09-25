#!/usr/bin/env python3
"""Re-classify grouped_urls_manifest.json into semantic tier groups."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MANIFEST_PATH = ROOT / "data" / "grouped_urls_manifest.json"
OUTPUT_PATH = ROOT / "data" / "reclassified_manifest_5000.json"
BENCHMARK_PATH = ROOT / "data" / "benchmark_questions_200_final.json"

TIER_ORDER = (
    "group-200",
    "tier-bedrock",
    "tier-sagemaker",
    "tier-case-studies",
    "tier-general-aws",
)


def _classify_url(url: str, *, in_group_200: bool) -> str:
    if in_group_200:
        return "group-200"
    lower = url.lower()
    if "/bedrock/" in lower:
        return "tier-bedrock"
    if "/sagemaker/" in lower:
        return "tier-sagemaker"
    if "/case-studies/" in lower or "/solutions/" in lower:
        return "tier-case-studies"
    return "tier-general-aws"


def reclassify_manifest(manifest: dict) -> dict:
    source_groups = manifest.get("groups", {})
    group_200_urls = {entry["url"] for entry in source_groups.get("group-200", [])}

    if len(group_200_urls) != 200:
        print(
            f"WARNING: source group-200 has {len(group_200_urls)} URLs (expected 200)",
            file=sys.stderr,
        )

    all_entries: list[dict] = []
    seen: set[str] = set()
    for tier, entries in source_groups.items():
        for entry in entries:
            url = entry["url"]
            if url in seen:
                continue
            seen.add(url)
            all_entries.append(dict(entry))

    if not all_entries and manifest.get("urls"):
        for entry in manifest["urls"]:
            url = entry["url"]
            if url in seen:
                continue
            seen.add(url)
            all_entries.append(dict(entry))

    groups: dict[str, list[dict]] = {tier: [] for tier in TIER_ORDER}
    for entry in sorted(all_entries, key=lambda e: e["url"]):
        url = entry["url"]
        tier = _classify_url(url, in_group_200=url in group_200_urls)
        groups[tier].append({**entry, "tier_group": tier})

    for corpus_id, entry in enumerate(
        groups["group-200"] + [e for t in TIER_ORDER[1:] for e in groups[t]],
        start=1,
    ):
        entry["corpus_id"] = corpus_id
    for group_id, entry in enumerate(groups["group-200"], start=1):
        entry["group_200_id"] = group_id

    all_urls = groups["group-200"] + [e for tier in TIER_ORDER[1:] for e in groups[tier]]
    tier_counts = {tier: len(groups[tier]) for tier in TIER_ORDER}

    benchmark_urls: set[str] = set()
    if BENCHMARK_PATH.exists():
        benchmark = json.loads(BENCHMARK_PATH.read_text())
        benchmark_urls = {q["target_url"] for q in benchmark.get("questions", [])}
        missing = benchmark_urls - {e["url"] for e in groups["group-200"]}
        if missing:
            print(f"WARNING: {len(missing)} benchmark target_urls not in group-200", file=sys.stderr)

    return {
        "summary": {
            "corpus_target": 5000,
            "total_urls": len(all_urls),
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "source_manifest": str(MANIFEST_PATH.relative_to(ROOT)),
            "tier_counts": tier_counts,
            "group_200_count": tier_counts["group-200"],
            "benchmark_question_count": len(benchmark_urls),
        },
        "validation": {
            "corpus_target": 5000,
            "assigned_total": len(all_urls),
            "unique_urls": len({e["url"] for e in all_urls}),
            "meets_corpus_target": len(all_urls) >= 5000,
            "tier_counts": tier_counts,
            "group_200_exact": tier_counts["group-200"] == 200,
        },
        "groups": groups,
        "urls": all_urls,
    }


def main() -> int:
    if not MANIFEST_PATH.exists():
        print(f"Manifest not found: {MANIFEST_PATH}", file=sys.stderr)
        return 1

    manifest = json.loads(MANIFEST_PATH.read_text())
    reclassified = reclassify_manifest(manifest)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(reclassified, indent=2), encoding="utf-8")

    print(f"Wrote {OUTPUT_PATH}")
    print("=== Verified tier counts ===")
    for tier in TIER_ORDER:
        count = reclassified["validation"]["tier_counts"][tier]
        print(f"  {tier}: {count}")
    total = reclassified["validation"]["assigned_total"]
    print(f"  TOTAL: {total}")
    if total != 5000:
        print(f"WARNING: expected 5000 URLs, got {total}", file=sys.stderr)
        return 1
    if not reclassified["validation"]["group_200_exact"]:
        print("WARNING: group-200 is not exactly 200 URLs", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
