#!/usr/bin/env python3
"""TOST-style equivalence analysis on saved exact ladders (revision 1). No database."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / "data"
REV1 = ROOT / "artifacts" / "published" / "revision1"

OUT_JSON = REV1 / "analysis_equivalence.json"
OUT_MD = REV1 / "analysis_equivalence.md"

B = 10_000
SEED = 42
SCALES = (5000, 10000, 15000, 20000, 25000, 40000, 50000, 75000, 100000)
DELTA_PRIMARY = 0.05
DELTA_SENSITIVITY = 0.10
PCT_LO, PCT_HI = 5.0, 95.0

LADDER_OPENAI = REV1 / "exact_ladder_openai_primary200.json"
LADDER_TITAN = REV1 / "exact_ladder_titan_primary200.json"
BM25_DENSE = REV1 / "bm25_dense_text.json"
DOC_LENGTH = REV1 / "doc_length_stats.json"
DOC_TOKEN_CUTS = REV1 / "doc_token_cuts_openai.json"
MANIFEST = DATA / "erb_scale_manifest.json"

_JSON_CACHE: dict[str, Any] = {}


def to_py(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {str(k): to_py(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [to_py(v) for v in obj]
    if isinstance(obj, np.ndarray):
        return to_py(obj.tolist())
    if isinstance(obj, (np.floating,)):
        return float(obj)
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.bool_,)):
        return bool(obj)
    return obj


def dump_json(path: Path, obj: Any) -> None:
    text = json.dumps(to_py(obj), sort_keys=True, indent=2, ensure_ascii=True, allow_nan=False) + "\n"
    path.write_text(text, encoding="utf-8")


def load_json(path: Path) -> Any:
    key = str(path.resolve())
    if key not in _JSON_CACHE:
        with path.open("r", encoding="utf-8") as f:
            _JSON_CACHE[key] = json.load(f)
    return _JSON_CACHE[key]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


class IndexCache:
    def __init__(self) -> None:
        self._cache: dict[int, np.ndarray] = {}

    def get(self, n: int) -> np.ndarray:
        if n not in self._cache:
            rng = np.random.default_rng(SEED)
            self._cache[n] = rng.integers(0, n, size=(B, n), dtype=np.int64)
        return self._cache[n]


IDX = IndexCache()


def as_hit(rows: list[Any], key: str = "hit_at_10") -> np.ndarray:
    out = np.empty(len(rows), dtype=np.float64)
    for i, row in enumerate(rows):
        v = row[key]
        if isinstance(v, bool):
            out[i] = float(int(v))
        else:
            out[i] = 1.0 if float(v) != 0.0 else 0.0
    return out


def qid_set(run: dict[str, Any]) -> set[str]:
    pq = run.get("per_question") or []
    ids = [p["question_id"] for p in pq]
    unique = set(ids)
    assert len(pq) == len(unique)
    return unique


def canonical_question_ids(runs: list[dict[str, Any]]) -> list[str]:
    if not runs:
        return []
    sets = [qid_set(r) for r in runs]
    first = sets[0]
    for i, s in enumerate(sets[1:], start=1):
        if s != first:
            raise ValueError(f"question id mismatch at run {i}")
    return sorted(first)


def run_scale(run: dict[str, Any]) -> int:
    return int(run.get("scale", run.get("corpus_scale_size")))


def index_runs(blob: dict[str, Any]) -> dict[tuple[str, int], dict[str, Any]]:
    out: dict[tuple[str, int], dict[str, Any]] = {}
    for run in blob.get("runs") or []:
        out[(run["condition"], run_scale(run))] = run
    return out


def align_hits(run: dict[str, Any], order: list[str], key: str = "hit_at_10") -> np.ndarray:
    by_id = {p["question_id"]: p for p in run["per_question"]}
    return as_hit([by_id[q] for q in order], key)


def bootstrap_90(values: np.ndarray, idx: np.ndarray) -> tuple[float, float, float]:
    v = np.asarray(values, dtype=np.float64)
    point = float(v.mean())
    boot = v[idx].mean(axis=1)
    lo, hi = np.percentile(boot, [PCT_LO, PCT_HI])
    return point, float(lo), float(hi)


def smallest_equivalence_delta(ci_lo: float, ci_hi: float) -> float:
    return float(max(abs(ci_lo), abs(ci_hi)))


def equivalent_within_delta(ci_lo: float, ci_hi: float, delta: float) -> bool:
    return ci_lo > -delta and ci_hi < delta


def tost_record(
    values: np.ndarray,
    idx: np.ndarray,
    label: str,
    *,
    scale: int | None = None,
) -> dict[str, Any]:
    point, lo, hi = bootstrap_90(values, idx)
    rec: dict[str, Any] = {
        "id": label,
        "estimate": round(point, 3),
        "ci90_lo": round(lo, 3),
        "ci90_hi": round(hi, 3),
        "smallest_delta_for_equivalence": round(smallest_equivalence_delta(lo, hi), 3),
        "equivalent_delta_0.05": equivalent_within_delta(lo, hi, DELTA_PRIMARY),
        "equivalent_delta_0.10": equivalent_within_delta(lo, hi, DELTA_SENSITIVITY),
    }
    if scale is not None:
        rec["scale"] = int(scale)
    return rec


def load_bm25_per_scale() -> dict[int, list[dict[str, Any]]]:
    blob = load_json(BM25_DENSE)
    pqs = blob["per_question_by_scale"]
    return {int(s): pqs[str(s)] for s in pqs}


def align_bm25_scale(rows: list[dict[str, Any]], order: list[str]) -> np.ndarray:
    by_id = {p["question_id"]: p for p in rows}
    missing = [q for q in order if q not in by_id]
    if missing:
        raise ValueError(f"BM25 missing question ids: {missing[:8]}")
    return as_hit([by_id[q] for q in order])


def load_ladders() -> tuple[list[str], dict, dict, np.ndarray]:
    openai = load_json(LADDER_OPENAI)
    titan = load_json(LADDER_TITAN)
    ro, rt = index_runs(openai), index_runs(titan)
    order = canonical_question_ids(list(ro.values()) + list(rt.values()))
    idx = IDX.get(len(order))
    return order, ro, rt, idx


def drop_5k_100k(
    runs: dict[tuple[str, int], dict[str, Any]],
    cond: str,
    order: list[str],
) -> np.ndarray:
    v5 = align_hits(runs[(cond, 5000)], order)
    v100 = align_hits(runs[(cond, 100000)], order)
    return v5 - v100


def lift_at_scale(
    runs: dict[tuple[str, int], dict[str, Any]],
    scale: int,
    order: list[str],
) -> np.ndarray:
    raw = align_hits(runs[("raw", scale)], order)
    meta = align_hits(runs[("meta_in", scale)], order)
    return meta - raw


def subset_order(order: list[str], exclude: set[str]) -> list[str]:
    return [q for q in order if q not in exclude]


def compute_equivalence(
    order: list[str] | None = None,
    idx: np.ndarray | None = None,
    ro: dict | None = None,
    rt: dict | None = None,
) -> dict[str, Any]:
    if order is None:
        order, ro, rt, idx = load_ladders()  # type: ignore[assignment]
    else:
        assert ro is not None and rt is not None and idx is not None

    bm25_pqs = load_bm25_per_scale()
    bm25_by = {s: align_bm25_scale(bm25_pqs[s], order) for s in bm25_pqs}

    drop_o_raw = drop_5k_100k(ro, "raw", order)
    drop_t_raw = drop_5k_100k(rt, "raw", order)
    drop_o_meta = drop_5k_100k(ro, "meta_in", order)
    drop_t_meta = drop_5k_100k(rt, "meta_in", order)

    quantities: dict[str, Any] = {
        "a_openai_minus_titan_raw_drop_5k_100k": tost_record(
            drop_o_raw - drop_t_raw, idx, "a"
        ),
        "b_openai_minus_titan_meta_in_drop_5k_100k": tost_record(
            drop_o_meta - drop_t_meta, idx, "b"
        ),
    }

    lift_diff_by_scale = []
    level_diff_by_scale = []
    for scale in SCALES:
        lift_o = lift_at_scale(ro, scale, order)
        lift_t = lift_at_scale(rt, scale, order)
        lift_diff_by_scale.append(
            tost_record(lift_o - lift_t, idx, "c", scale=scale)
        )
        raw_o = align_hits(ro[("raw", scale)], order)
        raw_t = align_hits(rt[("raw", scale)], order)
        level_diff_by_scale.append(
            tost_record(raw_o - raw_t, idx, "d", scale=scale)
        )
    quantities["c_openai_minus_titan_meta_lift_by_scale"] = lift_diff_by_scale
    quantities["d_openai_minus_titan_raw_hit10_level_by_scale"] = level_diff_by_scale

    drop_bm25 = bm25_by[5000] - bm25_by[100000]
    quantities["e_dense_minus_bm25_drop_difference"] = {
        "openai_raw": tost_record(drop_o_raw - drop_bm25, idx, "e_openai"),
        "titan_raw": tost_record(drop_t_raw - drop_bm25, idx, "e_titan"),
    }

    for embedder, runs in (("openai", ro), ("titan", rt)):
        lift5 = lift_at_scale(runs, 5000, order)
        lift100 = lift_at_scale(runs, 100000, order)
        quantities[f"f_lift_100k_minus_lift_5k_{embedder}"] = tost_record(
            lift100 - lift5, idx, f"f_{embedder}"
        )

    return quantities


def input_fingerprints() -> list[dict[str, str]]:
    paths = [
        LADDER_OPENAI,
        LADDER_TITAN,
        DOC_LENGTH,
        DOC_TOKEN_CUTS,
        MANIFEST,
        BM25_DENSE,
    ]
    return [{"path": str(p.relative_to(ROOT)), "sha256": sha256_file(p)} for p in paths]


def acceptance_tests(quantities: dict[str, Any]) -> list[dict[str, Any]]:
    tests = []
    mgr = {
        "a": (0.035, -0.020, 0.090),
        "b": (0.025, -0.025, 0.075),
    }
    tol = 0.005
    for key, (est, lo, hi) in mgr.items():
        qkey = "a_openai_minus_titan_raw_drop_5k_100k" if key == "a" else "b_openai_minus_titan_meta_in_drop_5k_100k"
        q = quantities[qkey]
        ok = (
            abs(q["estimate"] - est) <= tol
            and abs(q["ci90_lo"] - lo) <= tol
            and abs(q["ci90_hi"] - hi) <= tol
        )
        tests.append(
            {
                "name": f"manager_match_{key}",
                "result": "PASS" if ok else "FAIL",
                "expected": {"estimate": est, "ci90_lo": lo, "ci90_hi": hi, "tolerance": tol},
                "actual": {
                    "estimate": q["estimate"],
                    "ci90_lo": q["ci90_lo"],
                    "ci90_hi": q["ci90_hi"],
                },
            }
        )
    a = quantities["a_openai_minus_titan_raw_drop_5k_100k"]
    tests.append(
        {
            "name": "a_equiv_delta_0.10_manager",
            "result": "PASS" if a["equivalent_delta_0.10"] and not a["equivalent_delta_0.05"] else "FAIL",
            "expected": "equivalent at 0.10, not at 0.05",
            "actual": {
                "equivalent_delta_0.05": a["equivalent_delta_0.05"],
                "equivalent_delta_0.10": a["equivalent_delta_0.10"],
            },
        }
    )
    return tests


def fmt_equiv(rec: dict[str, Any]) -> str:
    e05 = "YES" if rec["equivalent_delta_0.05"] else "NO"
    e10 = "YES" if rec["equivalent_delta_0.10"] else "NO"
    return (
        f"{rec['estimate']:+.3f} [{rec['ci90_lo']:+.3f}, {rec['ci90_hi']:+.3f}] "
        f"equiv@0.05={e05} equiv@0.10={e10} min_delta={rec['smallest_delta_for_equivalence']:.3f}"
    )


def write_md(payload: dict[str, Any]) -> None:
    q = payload["quantities"]
    lines = [
        "# Equivalence analysis (TOST-style bootstrap)",
        "",
        "Paired bootstrap over primary-200 questions (Hit@10, exact search). "
        f"B={B}, seed={SEED}, 90% percentile CI. "
        f"Equivalence within δ iff CI ⊂ (−δ, +δ) strictly.",
        "",
        "## Headline paired differences (5k→100k drop)",
        "",
        f"- **(a)** OpenAI−Titan raw drop: {fmt_equiv(q['a_openai_minus_titan_raw_drop_5k_100k'])}",
        f"- **(b)** OpenAI−Titan meta_in drop: {fmt_equiv(q['b_openai_minus_titan_meta_in_drop_5k_100k'])}",
        "",
    ]
    if not q["a_openai_minus_titan_raw_drop_5k_100k"]["equivalent_delta_0.05"]:
        lines.append(
            "**Equivalence is NOT shown at δ=0.05 for (a).** "
            "The 90% interval is not strictly inside (−0.05, +0.05)."
        )
        lines.append("")
    if not q["b_openai_minus_titan_meta_in_drop_5k_100k"]["equivalent_delta_0.05"]:
        lines.append(
            "**Equivalence is NOT shown at δ=0.05 for (b).** "
            "The 90% interval is not strictly inside (−0.05, +0.05)."
        )
        lines.append("")

    lines.extend(["## (c) OpenAI−Titan metadata lift by scale", ""])
    for rec in q["c_openai_minus_titan_meta_lift_by_scale"]:
        flag = ""
        if not rec["equivalent_delta_0.05"]:
            flag = " — **not equivalent @0.05**"
        lines.append(f"- N={rec['scale']}: {fmt_equiv(rec)}{flag}")

    lines.extend(["", "## (d) OpenAI−Titan raw Hit@10 level by scale", ""])
    for rec in q["d_openai_minus_titan_raw_hit10_level_by_scale"]:
        flag = ""
        if not rec["equivalent_delta_0.05"]:
            flag = " — **not equivalent @0.05**"
        lines.append(f"- N={rec['scale']}: {fmt_equiv(rec)}{flag}")

    lines.extend(["", "## (e) Dense drop minus BM25 drop (5k→100k)", ""])
    for label in ("openai_raw", "titan_raw"):
        rec = q["e_dense_minus_bm25_drop_difference"][label]
        ne = " — **not equivalent @0.05**" if not rec["equivalent_delta_0.05"] else ""
        lines.append(f"- {label}: {fmt_equiv(rec)}{ne}")

    lines.extend(["", "## (f) Lift(100k)−lift(5k) within embedder", ""])
    for embedder in ("openai", "titan"):
        rec = q[f"f_lift_100k_minus_lift_5k_{embedder}"]
        ne = " — **not equivalent @0.05**" if not rec["equivalent_delta_0.05"] else ""
        lines.append(f"- {embedder}: {fmt_equiv(rec)}{ne}")

    lines.extend(["", "## Acceptance tests", ""])
    for t in payload["acceptance_tests"]:
        lines.append(f"- {t['name']}: **{t['result']}** — actual={t['actual']}")

    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    order, ro, rt, idx = load_ladders()
    quantities = compute_equivalence(order, idx, ro, rt)
    tests = acceptance_tests(quantities)
    payload = {
        "meta": {
            "B": B,
            "seed": SEED,
            "delta_primary": DELTA_PRIMARY,
            "delta_sensitivity": DELTA_SENSITIVITY,
            "bootstrap": "paired_percentile_90_over_question_indices",
            "metric": "hit_at_10",
            "bank": "primary200",
            "search_mode": "exact",
            "n_questions": len(order),
            "question_order_rule": "sorted_question_ids",
            "inputs": input_fingerprints(),
            "numpy_version": np.__version__,
        },
        "quantities": quantities,
        "acceptance_tests": tests,
    }
    REV1.mkdir(parents=True, exist_ok=True)
    dump_json(OUT_JSON, payload)
    write_md(payload)
    print(f"wrote {OUT_JSON}")
    print(f"wrote {OUT_MD}")
    for t in tests:
        print(f"{t['result']}\t{t['name']}")
    return 0 if all(t["result"] == "PASS" for t in tests) else 1


if __name__ == "__main__":
    raise SystemExit(main())
