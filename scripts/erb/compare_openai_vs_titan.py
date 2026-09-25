#!/usr/bin/env python3
"""Compare OpenAI canonical ladder vs Amazon Titan Text Embeddings V2 (A8 arm).

Loads:
  - OpenAI: artifacts/published/erb_full_primary200_to100k.json (or CLEAN variant)
  - Titan:  argv[1], artifacts/published/erb_titan_primary200_to100k.json, or
            latest data/results/erb_titan_sweep_*.json

Writes:
  - artifacts/published/openai_vs_titan_primary200.json
  - artifacts/published/openai_vs_titan_primary200.md
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
TITAN_PUBLISHED = PUB / "erb_titan_primary200_to100k.json"
OUT_JSON = PUB / "openai_vs_titan_primary200.json"
OUT_MD = PUB / "openai_vs_titan_primary200.md"

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


def _latest_titan_sweep() -> Path | None:
    if not ERB_RESULTS_DIR.is_dir():
        return None
    sweeps = sorted(ERB_RESULTS_DIR.glob("erb_titan_sweep_*.json"))
    return sweeps[-1] if sweeps else None


def _resolve_titan(explicit: Path | None) -> Path | None:
    if explicit:
        return explicit if explicit.is_file() else None
    if TITAN_PUBLISHED.is_file():
        return TITAN_PUBLISHED
    return _latest_titan_sweep()


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


def _drift_replicates(openai_ep: dict[str, Any], titan_ep: dict[str, Any]) -> bool | None:
    o_decl = openai_ep.get("declines")
    t_decl = titan_ep.get("declines")
    if o_decl is None or t_decl is None:
        return None
    return bool(o_decl and t_decl)


def _waiting_payload(openai_path: Path) -> dict[str, Any]:
    return {
        "status": "waiting",
        "message": (
            "Titan sweep not available; run migrate_titan_results_schema.py then "
            "run_scale_sweep_titan.py --primary-questions 200."
        ),
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "openai_source": str(openai_path.relative_to(ROOT)),
        "titan_source": None,
        "outputs": {
            "json": str(OUT_JSON.relative_to(ROOT)),
            "markdown": str(OUT_MD.relative_to(ROOT)),
        },
    }


def _compare_payload(
    openai_path: Path,
    titan_path: Path,
    openai: dict[str, Any],
    titan: dict[str, Any],
) -> dict[str, Any]:
    o_idx = _index_runs(openai)
    t_idx = _index_runs(titan)
    shared_scales = sorted(set(_scales(o_idx)) & set(_scales(t_idx)))

    comparisons: list[dict[str, Any]] = []
    for n in shared_scales:
        for cond in CONDITIONS:
            o_run = o_idx.get((n, cond))
            t_run = t_idx.get((n, cond))
            if not o_run or not t_run:
                continue
            row: dict[str, Any] = {
                "corpus_scale_size": n,
                "condition": cond,
                "openai": {m: round(o_run[m], 4) for m in METRICS if m in o_run},
                "titan": {m: round(t_run[m], 4) for m in METRICS if m in t_run},
                "delta_titan_minus_openai": {},
            }
            for m in METRICS:
                if m in o_run and m in t_run:
                    row["delta_titan_minus_openai"][m] = round(t_run[m] - o_run[m], 4)
            comparisons.append(row)

    endpoint: dict[str, Any] = {}
    drift_summary: dict[str, Any] = {}
    for cond in CONDITIONS:
        endpoint[cond] = {}
        drift_summary[cond] = {}
        for m in METRICS:
            o_ep = _endpoint_delta(o_idx, condition=cond, metric=m)
            t_ep = _endpoint_delta(t_idx, condition=cond, metric=m)
            endpoint[cond][m] = {
                "openai": o_ep,
                "titan": t_ep,
                "delta_titan_minus_openai_endpoint": (
                    round(t_ep["delta_high_minus_low"] - o_ep["delta_high_minus_low"], 4)
                    if t_ep["delta_high_minus_low"] is not None
                    and o_ep["delta_high_minus_low"] is not None
                    else None
                ),
                "drift_replicates": _drift_replicates(o_ep, t_ep),
            }
            drift_summary[cond][m] = endpoint[cond][m]["drift_replicates"]

    raw_hit10_rep = drift_summary.get("raw", {}).get("hit_at_10")
    raw_hit1_rep = drift_summary.get("raw", {}).get("hit_at_1")
    raw_mrr_rep = drift_summary.get("raw", {}).get("mrr")

    return {
        "status": "complete",
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "openai_source": str(openai_path.relative_to(ROOT)),
        "titan_source": str(titan_path.relative_to(ROOT)),
        "openai_embedding_model": "text-embedding-3-small",
        "titan_embedding_model": titan.get("embedding_model") or "amazon.titan-embed-text-v2:0",
        "shared_scales": shared_scales,
        "openai_scales": _scales(o_idx),
        "titan_scales": _scales(t_idx),
        "comparisons": comparisons,
        "endpoint_deltas": endpoint,
        "drift_replication": {
            "definition": (
                "Endpoint decline replicates when both OpenAI and Titan show "
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
        "# OpenAI vs Titan embedder (primary-200)",
        "",
        "A8 second-embedder arm: Amazon Titan Text Embeddings V2 vs OpenAI on the same gold-pinned ladder.",
        "",
        f"- OpenAI: `{payload['openai_source']}` ({payload['openai_embedding_model']})",
        f"- Titan: `{payload['titan_source']}` ({payload['titan_embedding_model']})",
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
            "## Endpoint table (raw)",
            "",
            "| Metric | OpenAI 5k | OpenAI 100k | Δ | Titan 5k | Titan 100k | Δ | Replicates |",
            "|---|---:|---:|---:|---:|---:|---:|:---:|",
        ]
    )
    for m in METRICS:
        cell = payload["endpoint_deltas"]["raw"][m]
        o = cell["openai"]
        t = cell["titan"]
        lines.append(
            "| {m} | {o5} | {o1} | {od} | {t5} | {t1} | {td} | {rep} |".format(
                m=m,
                o5=_fmt(o.get("value_at_low")),
                o1=_fmt(o.get("value_at_high")),
                od=_fmt(o.get("delta_high_minus_low")),
                t5=_fmt(t.get("value_at_low")),
                t1=_fmt(t.get("value_at_high")),
                td=_fmt(t.get("delta_high_minus_low")),
                rep=cell.get("drift_replicates"),
            )
        )
    lines.extend(["", "## Per-scale raw Hit@10", "", "| N | OpenAI | Titan | Δ (T−O) |", "|---:|---:|---:|---:|"])
    for row in payload["comparisons"]:
        if row["condition"] != "raw":
            continue
        lines.append(
            f"| {row['corpus_scale_size']} | {_fmt(row['openai'].get('hit_at_10'))} | "
            f"{_fmt(row['titan'].get('hit_at_10'))} | "
            f"{_fmt(row['delta_titan_minus_openai'].get('hit_at_10'))} |"
        )
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("titan_sweep", nargs="?", type=Path, default=None)
    parser.add_argument("--openai", type=Path, default=None)
    args = parser.parse_args()

    openai_path = _resolve_openai(args.openai)
    titan_path = _resolve_titan(args.titan_sweep)
    openai = json.loads(openai_path.read_text(encoding="utf-8"))

    if titan_path is None:
        payload = _waiting_payload(openai_path)
        md = (
            "# OpenAI vs Titan (primary-200) — waiting\n\n"
            f"{payload['message']}\n"
        )
    else:
        titan = json.loads(titan_path.read_text(encoding="utf-8"))
        payload = _compare_payload(openai_path, titan_path, openai, titan)
        md = _compare_md(payload)

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    OUT_MD.write_text(md, encoding="utf-8")
    print(f"wrote {OUT_JSON}")
    print(f"wrote {OUT_MD}")
    print(f"status={payload.get('status')}")
    if payload.get("status") == "complete":
        print("drift_replication.raw=", json.dumps(payload["drift_replication"]["raw"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
