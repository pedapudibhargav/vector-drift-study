#!/usr/bin/env python3
"""Paired statistics for the OpenAI vs Titan V2 arms (paper Sec. Titan, RQ4).

Inputs (artifacts/published):
  erb_full_primary200_to100k.json   OpenAI HNSW ladder (per_question)
  erb_titan_primary200_to100k.json  Titan HNSW ladder (per_question)
  exact_control_mvp.json            OpenAI exact cosine at 5k/50k/100k
  exact_control_titan.json          Titan exact cosine at 5k/50k/100k

Writes artifacts/published/openai_vs_titan_bootstrap.{json,md}.

Paired bootstrap resamples the 200 eval IDs jointly across arms/scales
(B=5000, seed=42, same convention as bm25_vs_dense_bootstrap.json).
"""

from __future__ import annotations

import argparse
import json
import math
import random
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from paths import ROOT  # noqa: E402

PUB = ROOT / "artifacts" / "published"
SCALES = (5000, 10000, 15000, 20000, 25000, 40000, 50000, 75000, 100000)
TAU = 0.10


def _ladder(path: Path) -> dict[tuple[str, int], dict[str, dict]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    runs = data.get("runs_with_per_question") or data["runs"]
    return {
        (r["condition"], int(r["corpus_scale_size"])): {str(q["question_id"]): q for q in r["per_question"]}
        for r in runs
    }


def _exact(path: Path) -> dict[int, dict[str, dict]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return {
        int(r["corpus_scale_size"]): {str(q["question_id"]): q for q in r["per_question"]}
        for r in data["runs"]
        if r["condition"] == "raw"
    }


def _vec(rows: dict[str, dict], ids: list[str], metric: str) -> list[float]:
    return [float(rows[i][metric] or 0) for i in ids]


def _mean(v: list[float], idx: list[int]) -> float:
    return sum(v[i] for i in idx) / len(idx)


class Boot:
    def __init__(self, n: int, b: int, seed: int) -> None:
        rng = random.Random(seed)
        self.samples = [[rng.randrange(n) for _ in range(n)] for _ in range(b)]
        self.full = list(range(n))

    def ci(self, fn) -> dict:
        vals = sorted(fn(s) for s in self.samples)
        b = len(vals)
        return {
            "estimate": round(fn(self.full), 4),
            "ci95": [round(vals[int(0.025 * b)], 4), round(vals[int(0.975 * b) - 1], 4)],
        }


def _fit(ys: list[float]) -> dict:
    xs = [math.log(n) for n in SCALES]
    mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
    slope = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sum((x - mx) ** 2 for x in xs)
    return {"a": round(my - slope * mx, 3), "b": round(-slope, 3)}


def _sustained_n_star(deltas: dict[int, float]) -> int | None:
    for i, n in enumerate(SCALES):
        if all(deltas[m] < TAU for m in SCALES[i:]):
            return n
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pub", type=Path, default=PUB)
    parser.add_argument("--titan-exact", type=Path, default=None)
    parser.add_argument("--out-dir", type=Path, default=PUB)
    parser.add_argument("--B", type=int, default=5000)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    oa = _ladder(args.pub / "erb_full_primary200_to100k.json")
    ti = _ladder(args.pub / "erb_titan_primary200_to100k.json")
    oa_ex = _exact(args.pub / "exact_control_mvp.json")
    ti_ex = _exact(args.titan_exact or args.pub / "exact_control_titan.json")

    ids = sorted(oa[("raw", 5000)])
    for key in oa:
        assert sorted(oa[key]) == ids and sorted(ti[key]) == ids, f"bank mismatch at {key}"
    for n in (5000, 50000, 100000):
        assert sorted(oa_ex[n]) == ids and sorted(ti_ex[n]) == ids, f"exact bank mismatch at {n}"
    for i in ids:
        assert sorted(map(str, oa[("raw", 5000)][i]["expected_doc_ids"])) == sorted(
            ti[("raw", 5000)][i]["expected_doc_ids"]
        ), f"gold mismatch {i}"

    boot = Boot(len(ids), args.B, args.seed)
    out: dict = {"B": args.B, "seed": args.seed, "n": len(ids), "tau": TAU}

    # Endpoint drops (5k -> 100k) per arm and search mode; difference-in-drop; 100k gap.
    arms = {
        "openai_hnsw": (oa[("raw", 5000)], oa[("raw", 100000)]),
        "titan_hnsw": (ti[("raw", 5000)], ti[("raw", 100000)]),
        "openai_exact": (oa_ex[5000], oa_ex[100000]),
        "titan_exact": (ti_ex[5000], ti_ex[100000]),
    }
    endpoint: dict = {}
    for metric in ("hit_at_1", "hit_at_10", "mrr"):
        v = {k: (_vec(lo, ids, metric), _vec(hi, ids, metric)) for k, (lo, hi) in arms.items()}
        m: dict = {}
        for k, (lo, hi) in v.items():
            m[f"{k}_drop"] = boot.ci(lambda s, lo=lo, hi=hi: _mean(hi, s) - _mean(lo, s))
        for mode in ("hnsw", "exact"):
            (olo, ohi), (tlo, thi) = v[f"openai_{mode}"], v[f"titan_{mode}"]
            m[f"{mode}_titan_minus_openai_drop"] = boot.ci(
                lambda s, olo=olo, ohi=ohi, tlo=tlo, thi=thi: (_mean(thi, s) - _mean(tlo, s))
                - (_mean(ohi, s) - _mean(olo, s))
            )
            m[f"{mode}_titan_minus_openai_at_100k"] = boot.ci(
                lambda s, ohi=ohi, thi=thi: _mean(thi, s) - _mean(ohi, s)
            )
        endpoint[metric] = m
    out["endpoint"] = endpoint

    # Exact vs HNSW gap per arm at each exact scale.
    ann_gap: dict = {}
    for arm, lad, ex in (("openai", oa, oa_ex), ("titan", ti, ti_ex)):
        for n in (5000, 50000, 100000):
            e, h = _vec(ex[n], ids, "hit_at_10"), _vec(lad[("raw", n)], ids, "hit_at_10")
            ann_gap[f"{arm}_{n}"] = {
                **boot.ci(lambda s, e=e, h=h: _mean(e, s) - _mean(h, s)),
                "hit10_disagreements": sum(1 for a, b in zip(e, h) if a != b),
            }
    out["exact_minus_hnsw_hit10"] = ann_gap

    # Titan per-scale Hit@10 CI (raw) and log-linear fits.
    out["titan_raw_hit10_ci"] = {
        n: boot.ci(lambda s, v=_vec(ti[("raw", n)], ids, "hit_at_10"): _mean(v, s)) for n in SCALES
    }
    out["fits"] = {
        arm: {
            metric: _fit([sum(_vec(lad[("raw", n)], ids, metric)) / len(ids) for n in SCALES])
            for metric in ("hit_at_1", "hit_at_10", "mrr")
        }
        for arm, lad in (("openai", oa), ("titan", ti))
    }

    # Early step 5k -> 10k.
    out["early_step_hit10_5k_to_10k"] = {
        arm: boot.ci(
            lambda s, lo=_vec(lad[("raw", 5000)], ids, "hit_at_10"), hi=_vec(lad[("raw", 10000)], ids, "hit_at_10"): _mean(hi, s)
            - _mean(lo, s)
        )
        for arm, lad in (("openai", oa), ("titan", ti))
    }

    # Delta_meta and sustained N* per arm.
    dm: dict = {}
    for arm, lad in (("openai", oa), ("titan", ti)):
        deltas = {
            n: round(
                (sum(_vec(lad[("meta", n)], ids, "hit_at_10")) - sum(_vec(lad[("raw", n)], ids, "hit_at_10")))
                / len(ids),
                4,
            )
            for n in SCALES
        }
        dm[arm] = {
            "delta_meta": deltas,
            "points_below_tau": [n for n in SCALES if deltas[n] < TAU],
            "n_star_sustained": _sustained_n_star(deltas),
            "n_star_first_crossing": next((n for n in SCALES if deltas[n] < TAU), None),
        }
    out["delta_meta"] = dm

    # Failure overlap and per-type endpoints.
    o100, t100 = oa[("raw", 100000)], ti[("raw", 100000)]
    out["hit10_overlap_100k"] = {
        "both_miss": sum(1 for i in ids if not o100[i]["hit_at_10"] and not t100[i]["hit_at_10"]),
        "both_hit": sum(1 for i in ids if o100[i]["hit_at_10"] and t100[i]["hit_at_10"]),
        "openai_only_hit": sum(1 for i in ids if o100[i]["hit_at_10"] and not t100[i]["hit_at_10"]),
        "titan_only_hit": sum(1 for i in ids if t100[i]["hit_at_10"] and not o100[i]["hit_at_10"]),
    }
    by_type: dict = defaultdict(dict)
    for arm, lad in (("openai", oa), ("titan", ti)):
        for n in (5000, 100000):
            groups: dict = defaultdict(list)
            for i in ids:
                groups[lad[("raw", n)][i]["question_type"]].append(float(lad[("raw", n)][i]["hit_at_10"]))
            for t, v in groups.items():
                by_type[t][f"{arm}_{n}"] = round(sum(v) / len(v), 3)
                by_type[t]["n"] = len(v)
    out["hit10_by_type"] = dict(by_type)

    args.out_dir.mkdir(parents=True, exist_ok=True)
    (args.out_dir / "openai_vs_titan_bootstrap.json").write_text(json.dumps(out, indent=2), encoding="utf-8")

    md = ["# OpenAI vs Titan — paired bootstrap (B={}, seed={})".format(args.B, args.seed), ""]
    md += ["| metric | quantity | estimate | 95% CI |", "|---|---|---:|---|"]
    for metric, m in endpoint.items():
        for q, v in m.items():
            md.append(f"| {metric} | {q} | {v['estimate']} | {v['ci95']} |")
    md += ["", "## Exact − HNSW Hit@10", "", "| arm@N | estimate | 95% CI | disagreements |", "|---|---:|---|---:|"]
    for k, v in ann_gap.items():
        md.append(f"| {k} | {v['estimate']} | {v['ci95']} | {v['hit10_disagreements']} |")
    md += ["", "## Δmeta (Hit@10)", ""]
    for arm, v in dm.items():
        md.append(f"- {arm}: {v['delta_meta']} · below τ at {v['points_below_tau']} · sustained N* = {v['n_star_sustained']}")
    md += ["", f"Fits: {out['fits']}", "", f"Overlap @100k: {out['hit10_overlap_100k']}"]
    (args.out_dir / "openai_vs_titan_bootstrap.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(json.dumps({k: out[k] for k in ("endpoint", "exact_minus_hnsw_hit10", "delta_meta", "fits")}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
