#!/usr/bin/env python3
"""Wrong-routing simulation for the oracle metadata source-type filter.

Per-type exact top-10 lists are merged by score (tie-break doc_id) to obtain
the top-10 of any filter set S without re-querying. OpenAI primary-200, exact
search, seq-scan session.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))
import run_exact_ladder as ladder  # noqa: E402

ROOT = ladder.ROOT
DATA = ladder.DATA
REV1 = ladder.REV1
CACHE_PATH = ladder.OPENAI_CACHE_REV1
LADDER_PATH = REV1 / "exact_ladder_openai_primary200.json"
SCRATCH_CACHE = DATA / "rev1_routing_per_type_top10.json"

TABLE = "document_chunks"
TOP_N = 10
MC_REPS = 200
MC_SEED = 2026
BOOT_B = 2000
IDENTITY_N = 50
P_GRID = (0.0, 0.05, 0.1, 0.2, 0.3, 0.5, 1.0)
MODES = ("wrong_type", "wrong_dropgold", "superset", "abstain")
MODE_ID = {"wrong_type": 1, "wrong_dropgold": 2, "superset": 3, "abstain": 4}


def load_scratch() -> dict[str, Any]:
    if not SCRATCH_CACHE.is_file():
        return {"by_scale": {}}
    return json.loads(SCRATCH_CACHE.read_text(encoding="utf-8"))


def save_scratch(blob: dict[str, Any]) -> None:
    SCRATCH_CACHE.parent.mkdir(parents=True, exist_ok=True)
    tmp = SCRATCH_CACHE.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(blob), encoding="utf-8")
    tmp.replace(SCRATCH_CACHE)


def merge_topn(
    lists: list[tuple[list[str], list[float]]], top_n: int = TOP_N
) -> tuple[list[str], list[float]]:
    """Merge per-type (doc_id, score) lists: higher score first, then doc_id asc."""
    best: dict[str, float] = {}
    for ids, scores in lists:
        for did, sc in zip(ids, scores):
            prev = best.get(did)
            if prev is None or sc > prev:
                best[did] = sc
    ordered = sorted(best.items(), key=lambda kv: (-kv[1], kv[0]))[:top_n]
    if not ordered:
        return [], []
    return [d for d, _ in ordered], [s for _, s in ordered]


def metrics_of(expected: set[str], retrieved: list[str]) -> tuple[float, float]:
    m = ladder.per_question_metrics(expected, retrieved, [0.0] * len(retrieved), TOP_N)
    return float(m["hit_at_10"]), float(m["mrr"])


def corpus_types_at_scales(cur, scales: list[int]) -> dict[int, dict[str, int]]:
    out: dict[int, dict[str, int]] = {}
    for scale in scales:
        cur.execute(
            f"""
            SELECT source_type, COUNT(*)::int
            FROM {TABLE}
            WHERE embedding IS NOT NULL
              AND scale_rank IS NOT NULL
              AND scale_rank < %s
            GROUP BY source_type
            ORDER BY source_type
            """,
            (scale,),
        )
        out[scale] = {str(r[0]): int(r[1]) for r in cur.fetchall() if r[0]}
    return out


def fetch_per_type(
    cur,
    questions: list[dict],
    qvecs: dict[str, list[float]],
    scales: list[int],
    types_by_scale: dict[int, dict[str, int]],
) -> dict[str, dict[str, dict[str, dict[str, list]]]]:
    scratch = load_scratch()
    by_scale: dict[str, Any] = dict(scratch.get("by_scale") or {})
    for scale in scales:
        sk = str(scale)
        slot = dict(by_scale.get(sk) or {})
        types = list(types_by_scale[scale].keys())
        t0 = time.time()
        n_new = 0
        for q in questions:
            eid = q["eval_id"]
            qslot = dict(slot.get(eid) or {})
            for st in types:
                if st in qslot and qslot[st].get("retrieved_doc_ids") is not None:
                    continue
                extra, params = " AND source_type = %s", (st,)
                rows = ladder.exact_search(
                    cur, TABLE, qvecs[eid], scale, extra, params, TOP_N
                )
                qslot[st] = {
                    "retrieved_doc_ids": [d for d, _ in rows],
                    "scores": [s for _, s in rows],
                }
                n_new += 1
            slot[eid] = qslot
        by_scale[sk] = slot
        save_scratch({"by_scale": by_scale})
        print(
            f"per-type top-10 N={scale} types={len(types)} new_queries={n_new} "
            f"({time.time() - t0:.1f}s)",
            flush=True,
        )
    return by_scale


def lists_for_set(
    qslot: dict[str, dict[str, list]], type_set: list[str]
) -> tuple[list[str], list[float]]:
    packed = []
    for st in type_set:
        cell = qslot.get(st)
        if not cell:
            continue
        packed.append((list(cell.get("retrieved_doc_ids") or []), list(cell.get("scores") or [])))
    return merge_topn(packed, TOP_N)


def identity_check(
    cur,
    questions: list[dict],
    qvecs: dict[str, list[float]],
    scales: list[int],
    types_by_scale: dict[int, dict[str, int]],
    per_type: dict[str, dict[str, dict[str, dict[str, list]]]],
    n_triples: int = IDENTITY_N,
) -> dict[str, Any]:
    rng = np.random.default_rng(MC_SEED)
    triples: list[dict] = []
    mismatches = 0
    attempts = 0
    max_attempts = n_triples * 20
    while len(triples) < n_triples and attempts < max_attempts:
        attempts += 1
        qi = int(rng.integers(0, len(questions)))
        q = questions[qi]
        scale = int(scales[int(rng.integers(0, len(scales)))])
        types = list(types_by_scale[scale].keys())
        if not types:
            continue
        n_s = int(rng.integers(1, min(3, len(types)) + 1))
        chosen_idx = rng.choice(len(types), size=n_s, replace=False)
        S = sorted(types[int(i)] for i in np.atleast_1d(chosen_idx))
        merged_ids, _ = lists_for_set(per_type[str(scale)][q["eval_id"]], S)
        extra, params = " AND source_type = ANY(%s)", (S,)
        rows = ladder.exact_search(cur, TABLE, qvecs[q["eval_id"]], scale, extra, params, TOP_N)
        direct_ids = [d for d, _ in rows]
        ok = merged_ids == direct_ids
        if not ok:
            mismatches += 1
        triples.append(
            {
                "eval_id": q["eval_id"],
                "scale": scale,
                "S": S,
                "merged": merged_ids,
                "direct": direct_ids,
                "match": ok,
            }
        )
    return {
        "n_checked": len(triples),
        "n_mismatches": mismatches,
        "attempts": attempts,
        "triples_sample": [t for t in triples if not t["match"]][:5],
        "status": "PASS" if mismatches == 0 and len(triples) == n_triples else "FAIL",
    }


def rng_for(mode: str, p: float) -> np.random.Generator:
    p_key = int(round(p * 100))
    return np.random.default_rng([MC_SEED, MODE_ID[mode], p_key])


def route_set(
    rng: np.random.Generator,
    mode: str,
    fail: bool,
    oracle: list[str],
    corpus_types: list[str],
) -> tuple[list[str] | None, str]:
    """Return filter set, or None meaning 'use unfiltered / raw'."""
    oracle_set = list(oracle)
    others = [t for t in corpus_types if t not in set(oracle_set)]
    if not fail:
        return oracle_set, "oracle"
    if mode == "abstain":
        return None, "raw"
    if mode == "wrong_type":
        if not others:
            return oracle_set, "oracle_no_wrong_type"
        pick = str(others[int(rng.integers(0, len(others)))])
        return [pick], "wrong_type"
    if mode == "wrong_dropgold":
        if not oracle_set:
            return None, "raw"
        drop_i = int(rng.integers(0, len(oracle_set)))
        remaining = [t for i, t in enumerate(oracle_set) if i != drop_i]
        if not remaining:
            return None, "raw"
        return remaining, "dropgold"
    if mode == "superset":
        if not others:
            return oracle_set, "oracle_no_extra"
        extra = str(others[int(rng.integers(0, len(others)))])
        return sorted(set(oracle_set) | {extra}), "superset"
    raise ValueError(mode)


def breakeven_p(ps: list[float], ys: list[float], raw: float) -> float | str:
    if not ps:
        return "never"
    if ys[0] <= raw + 1e-15:
        return 0.0
    for i in range(len(ps) - 1):
        y0, y1 = ys[i], ys[i + 1]
        p0, p1 = ps[i], ps[i + 1]
        if y0 >= raw and y1 <= raw:
            if abs(y1 - y0) < 1e-15:
                return float(p1)
            t = (raw - y0) / (y1 - y0)
            return float(p0 + t * (p1 - p0))
    if ys[-1] > raw:
        return "never"
    return float(ps[-1])


def bootstrap_ci(values: np.ndarray, seed: int = MC_SEED, b: int = BOOT_B) -> tuple[float, float, float]:
    v = np.asarray(values, dtype=np.float64)
    point = float(v.mean()) if v.size else 0.0
    if v.size == 0:
        return point, point, point
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, v.size, size=(b, v.size), dtype=np.int64)
    boot = v[idx].mean(axis=1)
    lo, hi = np.percentile(boot, [2.5, 97.5])
    return point, float(lo), float(hi)


def ci_obj(point: float, lo: float, hi: float) -> dict[str, float]:
    return {"estimate": round(point, 6), "ci_lo": round(lo, 6), "ci_hi": round(hi, 6)}


def write_markdown(path: Path, payload: dict) -> None:
    lines = [
        "# Routing simulation (OpenAI primary-200, exact meta_in)",
        "",
        f"MC repetitions per question = {MC_REPS}; seed {MC_SEED} per (p, mode); "
        f"bootstrap B={BOOT_B} on per-question expected values.",
        "",
        f"Identity check: {payload.get('identity', {}).get('status')} "
        f"mismatches={payload.get('identity', {}).get('n_mismatches')}/"
        f"{payload.get('identity', {}).get('n_checked')}.",
        "",
        "## Compact table (5k / 50k / 100k)",
        "",
        "| mode | p | Hit@10 5k | MRR 5k | Hit@10 50k | MRR 50k | Hit@10 100k | MRR 100k |",
        "|------|--:|----------:|-------:|-----------:|--------:|------------:|---------:|",
    ]
    cells = payload.get("table_compact") or []
    for row in cells:
        lines.append(
            f"| {row['mode']} | {row['p']} | {row.get('hit_at_10_5000', '—')} | "
            f"{row.get('mrr_5000', '—')} | {row.get('hit_at_10_50000', '—')} | "
            f"{row.get('mrr_50000', '—')} | {row.get('hit_at_10_100000', '—')} | "
            f"{row.get('mrr_100000', '—')} |"
        )
    lines.extend(["", "## Break-even p (Hit@10 vs raw)", "", "| mode | 5k | 50k | 100k |", "|------|----|-----|------|"])
    for mode in MODES:
        be = (payload.get("breakeven") or {}).get(mode) or {}
        lines.append(
            f"| {mode} | {be.get('5000', '—')} | {be.get('50000', '—')} | {be.get('100000', '—')} |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def compare_p0_to_ladder(
    questions: list[dict],
    results: list[dict],
) -> list[dict]:
    checks: list[dict] = []
    nq = len(questions)
    if not LADDER_PATH.is_file():
        return [{"name": "p0_vs_meta_in", "status": "FAIL", "detail": "missing ladder"}]
    blob = json.loads(LADDER_PATH.read_text(encoding="utf-8"))
    by = {(r["condition"], int(r["scale"])): r for r in blob.get("runs") or []}
    eids = [q["eval_id"] for q in questions]
    full = nq == 200
    p0_rows = [r for r in results if r["p"] == 0.0]
    for row in p0_rows:
        scale = int(row["scale"])
        meta = by.get(("meta_in", scale))
        raw = by.get(("raw", scale))
        if not meta:
            checks.append({"name": f"p0_meta_in_N={scale}", "status": "FAIL", "detail": "no ladder run"})
            continue
        want = {p["question_id"]: bool(p["hit_at_10"]) for p in meta.get("per_question") or []}
        got_map = {x["question_id"]: x["expected_hit_at_10"] for x in row["per_question"]}
        # p=0 is deterministic: expected hit should be 0 or 1 matching meta_in
        n_match = 0
        for eid in eids:
            g = got_map.get(eid)
            w = want.get(eid)
            if w is None:
                continue
            if abs(float(g) - float(w)) < 1e-12:
                n_match += 1
        ok = n_match == nq
        name = f"p0_{row['mode']}_hit10_vs_meta_in_N={scale}"
        if full:
            got_mean = round(float(row["hit_at_10"]["estimate"]), 4)
            lad = float(meta["metrics"]["hit_at_10"])
            checks.append(
                {
                    "name": name,
                    "status": "PASS" if got_mean == lad and ok else "FAIL",
                    "got": got_mean,
                    "ladder": lad,
                    "n_match": n_match,
                    "n": nq,
                }
            )
        else:
            checks.append(
                {
                    "name": name + "_subset",
                    "status": "PASS" if ok else "FAIL",
                    "n_match": n_match,
                    "n": nq,
                    "note": "smoke/subset vs ladder per-question meta_in",
                }
            )
        if row["mode"] == "abstain" and raw is not None:
            # p=0 abstain is still oracle; p=1 checked separately
            pass
    # abstain p=1 vs raw; wrong_type p=0 vs meta_in already covered
    p1_abs = [r for r in results if r["mode"] == "abstain" and r["p"] == 1.0]
    for row in p1_abs:
        scale = int(row["scale"])
        raw = by.get(("raw", scale))
        if not raw:
            continue
        want = {p["question_id"]: bool(p["hit_at_10"]) for p in raw.get("per_question") or []}
        got_map = {x["question_id"]: x["expected_hit_at_10"] for x in row["per_question"]}
        n_match = sum(1 for eid in eids if abs(float(got_map[eid]) - float(want[eid])) < 1e-12)
        ok = n_match == nq
        if full:
            got_mean = round(float(row["hit_at_10"]["estimate"]), 4)
            lad = float(raw["metrics"]["hit_at_10"])
            checks.append(
                {
                    "name": f"abstain_p1_vs_raw_N={scale}",
                    "status": "PASS" if got_mean == lad and ok else "FAIL",
                    "got": got_mean,
                    "ladder": lad,
                }
            )
        else:
            checks.append(
                {
                    "name": f"abstain_p1_vs_raw_N={scale}_subset",
                    "status": "PASS" if ok else "FAIL",
                    "n_match": n_match,
                    "n": nq,
                }
            )
    if not full:
        checks.append(
            {
                "name": "p0_meta_in_published_200q",
                "status": "NOT_RUN",
                "reason": f"n_questions={nq}; full job required",
            }
        )
    return checks


def run(args: argparse.Namespace) -> int:
    manifest = ladder.load_manifest()
    questions = ladder.load_questions(manifest, "primary200")
    if args.limit and args.limit > 0:
        questions = questions[: args.limit]
    eval_ids = [q["eval_id"] for q in questions]
    qvecs, missing = ladder.load_query_cache("openai", eval_ids, CACHE_PATH)
    if missing:
        print(f"FAIL missing query vectors: {missing[:5]}", file=sys.stderr)
        return 1
    pf = ladder.run_openai_preflight(
        "openai",
        "primary200",
        questions,
        qvecs,
        skip_preflight=False,
        provenance_path=ladder.PROVENANCE_DEFAULT,
    )
    if pf != 0:
        return pf

    scales = [int(x) for x in args.scales.split(",") if x.strip()]
    nq = len(questions)

    conn = ladder.pg_connect()
    conn.autocommit = True
    cur = conn.cursor()
    ladder.apply_seqscan_session(cur)
    pg_version, pgvector_version = ladder.session_pg_versions(cur)
    types_by_scale = corpus_types_at_scales(cur, scales)
    print(
        "source types: "
        + ", ".join(
            f"N={s}:{list(types_by_scale[s].keys())}" for s in scales
        ),
        flush=True,
    )
    per_type = fetch_per_type(cur, questions, qvecs, scales, types_by_scale)

    identity = identity_check(
        cur, questions, qvecs, scales, types_by_scale, per_type, IDENTITY_N
    )
    print(
        f"identity {identity['status']} mismatches={identity['n_mismatches']}/"
        f"{identity['n_checked']}",
        flush=True,
    )
    cur.close()
    conn.close()

    # precompute merged lists per question/scale for oracle, raw, each type
    prepared: dict[tuple[int, str], dict[str, Any]] = {}
    for scale in scales:
        corpus_types = list(types_by_scale[scale].keys())
        for q in questions:
            eid = q["eval_id"]
            qslot = per_type[str(scale)][eid]
            oracle = [str(s) for s in (q.get("source_types") or []) if s]
            raw_ids, raw_sc = lists_for_set(qslot, corpus_types)
            ora_ids, ora_sc = lists_for_set(qslot, oracle)
            expected = {str(x) for x in (q.get("expected_doc_ids") or []) if x}
            prepared[(scale, eid)] = {
                "oracle": oracle,
                "corpus_types": corpus_types,
                "qslot": qslot,
                "raw_ids": raw_ids,
                "ora_ids": ora_ids,
                "expected": expected,
            }

    results: list[dict] = []
    for scale in scales:
        t0 = time.time()
        for mode in MODES:
            for p in P_GRID:
                rng = rng_for(mode, p)
                per_q_hit: list[float] = []
                per_q_mrr: list[float] = []
                per_q_rows: list[dict] = []
                for q in questions:
                    eid = q["eval_id"]
                    prep = prepared[(scale, eid)]
                    hits = np.empty(MC_REPS, dtype=np.float64)
                    mrrs = np.empty(MC_REPS, dtype=np.float64)
                    for r in range(MC_REPS):
                        fail = bool(rng.random() < p)
                        S, tag = route_set(
                            rng, mode, fail, prep["oracle"], prep["corpus_types"]
                        )
                        if S is None:
                            retrieved = prep["raw_ids"]
                        else:
                            retrieved, _ = lists_for_set(prep["qslot"], S)
                        h, m = metrics_of(prep["expected"], retrieved)
                        hits[r] = h
                        mrrs[r] = m
                    eh = float(hits.mean())
                    em = float(mrrs.mean())
                    per_q_hit.append(eh)
                    per_q_mrr.append(em)
                    per_q_rows.append(
                        {
                            "question_id": eid,
                            "expected_hit_at_10": eh,
                            "expected_mrr": em,
                        }
                    )
                h_arr = np.asarray(per_q_hit, dtype=np.float64)
                m_arr = np.asarray(per_q_mrr, dtype=np.float64)
                results.append(
                    {
                        "mode": mode,
                        "p": p,
                        "scale": scale,
                        "n_questions": nq,
                        "n_reps": MC_REPS,
                        "hit_at_10": ci_obj(*bootstrap_ci(h_arr)),
                        "mrr": ci_obj(*bootstrap_ci(m_arr)),
                        "per_question": per_q_rows,
                    }
                )
        print(
            f"routing N={scale} modes={len(MODES)} p-grid={len(P_GRID)} "
            f"({time.time() - t0:.1f}s)",
            flush=True,
        )

    # raw hit@10 per scale from merge-all (for breakeven)
    raw_hit: dict[int, float] = {}
    for scale in scales:
        hs = []
        for q in questions:
            prep = prepared[(scale, q["eval_id"])]
            h, _ = metrics_of(prep["expected"], prep["raw_ids"])
            hs.append(h)
        raw_hit[scale] = float(np.mean(hs))

    breakeven: dict[str, dict[str, Any]] = {m: {} for m in MODES}
    for mode in MODES:
        for scale in scales:
            ys = []
            ps = []
            for p in P_GRID:
                row = next(r for r in results if r["mode"] == mode and r["scale"] == scale and r["p"] == p)
                ps.append(float(p))
                ys.append(float(row["hit_at_10"]["estimate"]))
            be = breakeven_p(ps, ys, raw_hit[scale])
            breakeven[mode][str(scale)] = be if isinstance(be, str) else round(be, 6)

    compact_keys = [s for s in (5000, 50000, 100000) if s in scales]
    table_compact: list[dict] = []
    for mode in MODES:
        for p in P_GRID:
            rec: dict[str, Any] = {"mode": mode, "p": p}
            for s in compact_keys:
                row = next(r for r in results if r["mode"] == mode and r["scale"] == s and r["p"] == p)
                rec[f"hit_at_10_{s}"] = round(row["hit_at_10"]["estimate"], 4)
                rec[f"mrr_{s}"] = round(row["mrr"]["estimate"], 4)
            table_compact.append(rec)

    acceptance = [
        {
            "name": "identity_merge_vs_direct",
            "status": identity["status"],
            "n_mismatches": identity["n_mismatches"],
            "n_checked": identity["n_checked"],
        }
    ]
    acceptance.extend(compare_p0_to_ladder(questions, results))

    # reproducibility: recompute one cell
    mode, p, scale = "wrong_type", 0.2, scales[0]
    rng_a = rng_for(mode, p)
    rng_b = rng_for(mode, p)
    # one question one fail draw
    q0 = questions[0]
    prep = prepared[(scale, q0["eval_id"])]
    seq_a = []
    seq_b = []
    for _ in range(5):
        fa = bool(rng_a.random() < p)
        Sa, _ = route_set(rng_a, mode, fa, prep["oracle"], prep["corpus_types"])
        seq_a.append((fa, Sa))
        fb = bool(rng_b.random() < p)
        Sb, _ = route_set(rng_b, mode, fb, prep["oracle"], prep["corpus_types"])
        seq_b.append((fb, Sb))
    repro_ok = seq_a == seq_b
    acceptance.append(
        {
            "name": "seed_reproducible_per_p_mode",
            "status": "PASS" if repro_ok else "FAIL",
            "sample": seq_a,
        }
    )

    payload = {
        "meta": {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "embedder": "openai",
            "bank": "primary200",
            "search_mode": "exact",
            "table": TABLE,
            "n_questions": nq,
            "scales": scales,
            "p_grid": list(P_GRID),
            "modes": list(MODES),
            "mc_reps": MC_REPS,
            "mc_seed": MC_SEED,
            "bootstrap_B": BOOT_B,
            "session_settings": {"enable_indexscan": "off", "enable_bitmapscan": "off"},
            "postgresql_version": pg_version,
            "pgvector_version": pgvector_version,
            "query_cache_path": str(CACHE_PATH.relative_to(ROOT)),
            "query_vector_key_rule": ladder.QUERY_VECTOR_KEY_RULE,
            "source_type_counts": {str(s): types_by_scale[s] for s in scales},
            "limit": args.limit,
        },
        "identity": identity,
        "raw_hit_at_10": {str(s): raw_hit[s] for s in scales},
        "results": [
            {k: v for k, v in r.items() if k != "per_question"} | {"per_question": r["per_question"]}
            for r in results
        ],
        "breakeven": breakeven,
        "table_compact": table_compact,
        "acceptance": acceptance,
    }
    out = args.out or (REV1 / "routing_simulation_openai_primary200.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    write_markdown(out.with_suffix(".md"), payload)
    print(f"wrote {out}", flush=True)
    print(f"wrote {out.with_suffix('.md')}", flush=True)
    failed = [a for a in acceptance if a.get("status") == "FAIL"]
    return 1 if failed else 0


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--scales", default=",".join(str(s) for s in ladder.DEFAULT_SCALES))
    p.add_argument("--limit", type=int, default=0)
    p.add_argument("--out", type=Path, default=None)
    p.add_argument("--smoke", action="store_true")
    args = p.parse_args()
    if args.smoke:
        args.scales = "5000,100000"
        args.limit = 10
    return run(args)


if __name__ == "__main__":
    raise SystemExit(main())
