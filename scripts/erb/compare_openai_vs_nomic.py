#!/usr/bin/env python3
"""Compare OpenAI canonical ladder vs Ollama nomic-embed-text (A8 arm).

Loads:
  - OpenAI: artifacts/published/erb_full_primary200_to100k.json (or CLEAN variant)
  - Nomic:  argv[1], artifacts/published/erb_ollama_primary200_to100k.json, or
            latest data/results/erb_ollama_sweep_*.json

Writes:
  - artifacts/published/openai_vs_nomic_primary200.json
  - artifacts/published/openai_vs_nomic_primary200.md

If no Nomic sweep exists yet, exits 0 with a waiting message (stub outputs).
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from paths import ERB_RESULTS_DIR, ROOT  # noqa: E402

PUB = ROOT / "artifacts" / "published"
OPENAI_CANDIDATES = (
    PUB / "erb_full_primary200_to100k.json",
    PUB / "erb_full_primary200_to100k.CLEAN.json",
    PUB / "erb_full_primary_corrected.json",
)
NOMIC_PUBLISHED = PUB / "erb_ollama_primary200_to100k.json"
OUT_JSON = PUB / "openai_vs_nomic_primary200.json"
OUT_MD = PUB / "openai_vs_nomic_primary200.md"

METRICS = ("hit_at_1", "hit_at_5", "hit_at_10", "mrr")
CONDITIONS = ("raw", "meta")
ENDPOINT_LOW = 5_000
ENDPOINT_HIGH = 100_000


def _first_existing(paths: tuple[Path, ...]) -> Path | None:
    for p in paths:
        if p.is_file():
            return p
    return None


def _resolve_openai(explicit: Path | None) -> Path:
    if explicit and explicit.is_file():
        return explicit
    found = _first_existing(OPENAI_CANDIDATES)
    if not found:
        raise SystemExit(
            "OpenAI canonical sweep not found; expected one of: "
            + ", ".join(str(p) for p in OPENAI_CANDIDATES)
        )
    return found


def _latest_ollama_sweep() -> Path | None:
    if not ERB_RESULTS_DIR.is_dir():
        return None
    sweeps = sorted(ERB_RESULTS_DIR.glob("erb_ollama_sweep_*.json"))
    return sweeps[-1] if sweeps else None


def _resolve_nomic(explicit: Path | None) -> Path | None:
    if explicit:
        return explicit if explicit.is_file() else None
    if NOMIC_PUBLISHED.is_file():
        return NOMIC_PUBLISHED
    return _latest_ollama_sweep()


def _index_runs(payload: dict[str, Any]) -> dict[tuple[int, str], dict[str, float]]:
    out: dict[tuple[int, str], dict[str, float]] = {}
    for run in payload.get("runs") or []:
        scale = int(run.get("corpus_scale_size") or 0)
        cond = str(run.get("condition") or "").lower()
        if not scale or cond not in CONDITIONS:
            continue
        row: dict[str, float] = {}
        for m in METRICS:
            if run.get(m) is not None:
                row[m] = float(run[m])
        if row:
            out[(scale, cond)] = row
    return out


def _scales(index: dict[tuple[int, str], dict[str, float]]) -> list[int]:
    return sorted({k[0] for k in index})


def _metric(run: dict[str, float] | None, name: str) -> float | None:
    if not run:
        return None
    v = run.get(name)
    return float(v) if v is not None else None


def _endpoint_delta(
    index: dict[tuple[int, str], dict[str, float]],
    *,
    condition: str,
    metric: str,
    low: int = ENDPOINT_LOW,
    high: int = ENDPOINT_HIGH,
) -> dict[str, Any]:
    lo = index.get((low, condition))
    hi = index.get((high, condition))
    v_lo = _metric(lo, metric)
    v_hi = _metric(hi, metric)
    if v_lo is None or v_hi is None:
        return {
            "low_n": low,
            "high_n": high,
            "value_at_low": v_lo,
            "value_at_high": v_hi,
            "delta_high_minus_low": None,
            "declines": None,
        }
    delta = round(v_hi - v_lo, 4)
    return {
        "low_n": low,
        "high_n": high,
        "value_at_low": round(v_lo, 4),
        "value_at_high": round(v_hi, 4),
        "delta_high_minus_low": delta,
        "declines": delta < 0,
    }


def _drift_replicates(
    openai_ep: dict[str, Any],
    nomic_ep: dict[str, Any],
) -> bool | None:
    o_decl = openai_ep.get("declines")
    n_decl = nomic_ep.get("declines")
    if o_decl is None or n_decl is None:
        return None
    # Both embedders should show endpoint decline for drift to replicate.
    return bool(o_decl and n_decl)


def _waiting_payload(openai_path: Path, nomic_hint: str) -> dict[str, Any]:
    return {
        "status": "waiting",
        "message": "Nomic Ollama sweep not available; re-run after erb_ollama ingest + run_scale_sweep_ollama.py complete.",
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "openai_source": str(openai_path.relative_to(ROOT)),
        "nomic_source": None,
        "nomic_search": nomic_hint,
        "outputs": {
            "json": str(OUT_JSON.relative_to(ROOT)),
            "markdown": str(OUT_MD.relative_to(ROOT)),
        },
    }


def _waiting_md(payload: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# OpenAI vs Nomic (primary-200) — waiting",
            "",
            payload["message"],
            "",
            f"- OpenAI source: `{payload['openai_source']}`",
            f"- Nomic search: `{payload['nomic_search']}`",
            "",
            "Re-run:",
            "",
            "```bash",
            "python scripts/erb/compare_openai_vs_nomic.py",
            "# or after publishing:",
            "python scripts/erb/compare_openai_vs_nomic.py artifacts/published/erb_ollama_primary200_to100k.json",
            "```",
            "",
        ]
    )


def _compare_payload(
    openai_path: Path,
    nomic_path: Path,
    openai: dict[str, Any],
    nomic: dict[str, Any],
) -> dict[str, Any]:
    o_idx = _index_runs(openai)
    n_idx = _index_runs(nomic)
    shared_scales = sorted(set(_scales(o_idx)) & set(_scales(n_idx)))

    comparisons: list[dict[str, Any]] = []
    for n in shared_scales:
        for cond in CONDITIONS:
            o_run = o_idx.get((n, cond))
            n_run = n_idx.get((n, cond))
            if not o_run or not n_run:
                continue
            row: dict[str, Any] = {
                "corpus_scale_size": n,
                "condition": cond,
                "openai": {m: round(o_run[m], 4) for m in METRICS if m in o_run},
                "nomic": {m: round(n_run[m], 4) for m in METRICS if m in n_run},
                "delta_nomic_minus_openai": {},
            }
            for m in METRICS:
                if m in o_run and m in n_run:
                    row["delta_nomic_minus_openai"][m] = round(n_run[m] - o_run[m], 4)
            comparisons.append(row)

    endpoint: dict[str, Any] = {}
    drift_summary: dict[str, Any] = {}
    for cond in CONDITIONS:
        endpoint[cond] = {}
        drift_summary[cond] = {}
        for m in METRICS:
            o_ep = _endpoint_delta(o_idx, condition=cond, metric=m)
            n_ep = _endpoint_delta(n_idx, condition=cond, metric=m)
            endpoint[cond][m] = {
                "openai": o_ep,
                "nomic": n_ep,
                "delta_nomic_minus_openai_endpoint": (
                    round(n_ep["delta_high_minus_low"] - o_ep["delta_high_minus_low"], 4)
                    if n_ep["delta_high_minus_low"] is not None
                    and o_ep["delta_high_minus_low"] is not None
                    else None
                ),
                "drift_replicates": _drift_replicates(o_ep, n_ep),
            }
            drift_summary[cond][m] = endpoint[cond][m]["drift_replicates"]

    # Primary headline: raw Hit@10 / Hit@1 / MRR endpoint decline replication
    raw_hit10_rep = drift_summary.get("raw", {}).get("hit_at_10")
    raw_hit1_rep = drift_summary.get("raw", {}).get("hit_at_1")
    raw_mrr_rep = drift_summary.get("raw", {}).get("mrr")

    return {
        "status": "complete",
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "openai_source": str(openai_path.relative_to(ROOT)),
        "nomic_source": str(nomic_path.relative_to(ROOT)),
        "openai_embedding_model": "text-embedding-3-small",
        "nomic_embedding_model": nomic.get("embedding_model") or "nomic-embed-text",
        "shared_scales": shared_scales,
        "openai_scales": _scales(o_idx),
        "nomic_scales": _scales(n_idx),
        "comparisons": comparisons,
        "endpoint_deltas": endpoint,
        "drift_replication": {
            "definition": (
                "Endpoint decline replicates when both OpenAI and Nomic show "
                f"negative delta ({ENDPOINT_HIGH} minus {ENDPOINT_LOW}) for the metric."
            ),
            "raw": {
                "hit_at_10": raw_hit10_rep,
                "hit_at_1": raw_hit1_rep,
                "mrr": raw_mrr_rep,
                "all_three_replicate": (
                    raw_hit10_rep and raw_hit1_rep and raw_mrr_rep
                    if None not in (raw_hit10_rep, raw_hit1_rep, raw_mrr_rep)
                    else None
                ),
            },
            "by_condition_metric": drift_summary,
        },
    }


def _fmt(v: float | None) -> str:
    return "—" if v is None else f"{v:.3f}"


def _compare_md(payload: dict[str, Any]) -> str:
    lines = [
        "# OpenAI vs Nomic embedder (primary-200)",
        "",
        "A8 second-embedder arm: compare dense drift curves on the same gold-pinned ladder.",
        "",
        f"- OpenAI: `{payload['openai_source']}` ({payload['openai_embedding_model']})",
        f"- Nomic: `{payload['nomic_source']}` ({payload['nomic_embedding_model']})",
        f"- Shared scales: {payload['shared_scales']}",
        "",
    ]

    rep = payload["drift_replication"]["raw"]
    lines.extend(
        [
            "## Drift replication (5k → 100k endpoints)",
            "",
            f"- Raw Hit@10 replicates: **{rep['hit_at_10']}**",
            f"- Raw Hit@1 replicates: **{rep['hit_at_1']}**",
            f"- Raw MRR replicates: **{rep['mrr']}**",
            f"- All three raw metrics replicate: **{rep['all_three_replicate']}**",
            "",
            payload["drift_replication"]["definition"],
            "",
        ]
    )

    for cond in CONDITIONS:
        lines.append(f"### Endpoint deltas ({cond})")
        lines.append("")
        lines.append("| Metric | OpenAI 5k | OpenAI 100k | Δ OpenAI | Nomic 5k | Nomic 100k | Δ Nomic | Replicates? |")
        lines.append("|--------|-----------|-------------|----------|----------|------------|---------|-------------|")
        for m in METRICS:
            block = payload["endpoint_deltas"][cond][m]
            o = block["openai"]
            n = block["nomic"]
            lines.append(
                f"| {m} | {_fmt(o['value_at_low'])} | {_fmt(o['value_at_high'])} | "
                f"{_fmt(o['delta_high_minus_low'])} | {_fmt(n['value_at_low'])} | "
                f"{_fmt(n['value_at_high'])} | {_fmt(n['delta_high_minus_low'])} | "
                f"{block['drift_replicates']} |"
            )
        lines.append("")

    lines.extend(["## Per-scale deltas (Nomic − OpenAI)", ""])
    for cond in CONDITIONS:
        rows = [c for c in payload["comparisons"] if c["condition"] == cond]
        if not rows:
            continue
        lines.append(f"### {cond}")
        lines.append("")
        lines.append("| N | Δ Hit@1 | Δ Hit@5 | Δ Hit@10 | Δ MRR |")
        lines.append("|---|---------|---------|----------|-------|")
        for row in rows:
            d = row["delta_nomic_minus_openai"]
            n = row["corpus_scale_size"]
            lines.append(
                f"| {n // 1000}k | {_fmt(d.get('hit_at_1'))} | {_fmt(d.get('hit_at_5'))} | "
                f"{_fmt(d.get('hit_at_10'))} | {_fmt(d.get('mrr'))} |"
            )
        lines.append("")

    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "nomic_json",
        nargs="?",
        type=Path,
        default=None,
        help="Published or sweep JSON for Ollama arm (optional)",
    )
    parser.add_argument(
        "--openai",
        type=Path,
        default=None,
        help="Override OpenAI canonical JSON",
    )
    args = parser.parse_args()

    openai_path = _resolve_openai(args.openai)
    nomic_path = _resolve_nomic(args.nomic_json)
    nomic_hint = (
        str(args.nomic_json)
        if args.nomic_json
        else f"{NOMIC_PUBLISHED.name} or {ERB_RESULTS_DIR}/erb_ollama_sweep_*.json"
    )

    PUB.mkdir(parents=True, exist_ok=True)

    if nomic_path is None:
        payload = _waiting_payload(openai_path, nomic_hint)
        OUT_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        OUT_MD.write_text(_waiting_md(payload), encoding="utf-8")
        print(payload["message"])
        print(f"wrote {OUT_JSON.relative_to(ROOT)}")
        print(f"wrote {OUT_MD.relative_to(ROOT)}")
        return 0

    openai = json.loads(openai_path.read_text(encoding="utf-8"))
    nomic = json.loads(nomic_path.read_text(encoding="utf-8"))
    payload = _compare_payload(openai_path, nomic_path, openai, nomic)
    OUT_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    OUT_MD.write_text(_compare_md(payload), encoding="utf-8")

    rep = payload["drift_replication"]["raw"]
    print(
        f"compared {openai_path.name} vs {nomic_path.name}; "
        f"shared_scales={payload['shared_scales']}; "
        f"raw Hit@10 replicates={rep['hit_at_10']}"
    )
    print(f"wrote {OUT_JSON.relative_to(ROOT)}")
    print(f"wrote {OUT_MD.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
