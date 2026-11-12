#!/usr/bin/env python3
"""In-memory mutations: each corruption must make the named checks FAIL."""

from __future__ import annotations

import copy
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from harness_lib import sha256_text  # noqa: E402
from crosscheck_stats import extra_cross_mismatches  # noqa: E402
from validate_all import (  # noqa: E402
    check_claim_registry,
    check_invariants,
    check_query_vector_provenance,
    check_schema,
    check_search_mode_truth,
)

IDS10 = [f"d{i}" for i in range(10)]
SCORES10 = [1.0 - 0.01 * i for i in range(10)]


def _pq(qid: str, ids: list[str], scores: list[float]) -> dict[str, Any]:
    return {
        "question_id": qid,
        "retrieved_doc_ids": list(ids),
        "scores": list(scores),
        "hit_at_10": True,
        "hit_at_1": True,
        "hit_at_5": True,
        "mrr": 1.0,
        "document_recall": 1.0,
        "rank": 1,
    }


def toy_ladder() -> dict[str, Any]:
    mixed = ["jx"] + IDS10[1:]
    meta_ok = IDS10[:]
    return {
        "meta": {
            "skipped": False,
            "search_mode": "exact",
            "scales": [5000, 10000],
            "conditions": ["raw", "meta_in"],
            "plan_check": [
                {
                    "condition": "raw",
                    "scale": 5000,
                    "hnsw_index_scan": False,
                    "innermost_scan_node_type": "Seq Scan",
                    "scan_node_types": ["Seq Scan"],
                }
            ],
        },
        "runs": [
            {
                "condition": "raw",
                "scale": 5000,
                "n_questions": 1,
                "elapsed_s": 0.1,
                "metrics": {"hit_at_10": 1.0},
                "per_question": [_pq("q1::basic", mixed, SCORES10)],
            },
            {
                "condition": "meta_in",
                "scale": 5000,
                "n_questions": 1,
                "elapsed_s": 0.1,
                "metrics": {"hit_at_10": 1.0},
                "per_question": [_pq("q1::basic", meta_ok, SCORES10)],
            },
            {
                "condition": "raw",
                "scale": 10000,
                "n_questions": 1,
                "elapsed_s": 0.1,
                "metrics": {"hit_at_10": 1.0},
                "per_question": [_pq("q1::basic", mixed, SCORES10)],
            },
            {
                "condition": "meta_in",
                "scale": 10000,
                "n_questions": 1,
                "elapsed_s": 0.1,
                "metrics": {"hit_at_10": 1.0},
                "per_question": [_pq("q1::basic", meta_ok, SCORES10)],
            },
        ],
    }


def toy_docs() -> dict[str, str]:
    docs = {f"d{i}": "confluence" for i in range(12)}
    docs["jx"] = "jira"
    return docs


def toy_questions() -> dict[str, dict[str, Any]]:
    return {
        "q1::basic": {
            "eval_id": "q1::basic",
            "question": "hello world",
            "source_types": ["confluence"],
            "expected_doc_ids": ["d0"],
        }
    }


def toy_provenance() -> dict[str, Any]:
    q = toy_questions()["q1::basic"]["question"]
    return {
        "entries": [
            {
                "eval_id": "q1::basic",
                "question_sha256": sha256_text(q),
                "vector_sha256": "abc",
                "cosine_to_fresh_embedding": 1.0,
                "source": "test",
            }
        ]
    }


class _FakeManifest:
    def __init__(self, questions: dict[str, dict[str, Any]], docs: dict[str, str]) -> None:
        self.questions = questions
        self.docs = docs


def write_temp_manifest(path: Path) -> None:
    import json

    docs = [{"doc_id": k, "source_type": v, "scale_rank": i} for i, (k, v) in enumerate(toy_docs().items())]
    path.write_text(
        json.dumps({"documents": docs, "questions": [toy_questions()["q1::basic"]]}),
        encoding="utf-8",
    )


def must_fail(name: str, result, *, also: tuple[str, ...] = ()) -> None:
    ok = result.status == "FAIL"
    extra = True
    for label in also:
        extra = extra and any(label in m for m in result.messages)
    if not (ok and extra):
        raise SystemExit(
            f"MUTATION FAIL {name}: expected check FAIL"
            f"{' with ' + str(also) if also else ''}, "
            f"got {result.status} {result.messages[:8]}"
        )
    print(f"PASS mutation {name} detected ({result.name} FAIL n_fail={result.n_fail})")


def main() -> int:
    import json
    import tempfile

    tmp = Path(tempfile.mkdtemp(prefix="rev1_mut_"))
    man_path = tmp / "manifest.json"
    write_temp_manifest(man_path)
    bank_dir = tmp / "published"
    bank_dir.mkdir()
    (bank_dir / "primary_questions_200.json").write_text(
        '{"count": 1, "question_ids": ["q1::basic"]}', encoding="utf-8"
    )
    ladder_name = str(tmp / "exact_ladder_openai_primary200.json")

    # 1. swapped question vector / provenance mismatch
    prov_bad = toy_provenance()
    prov_bad["entries"][0]["question_sha256"] = "0" * 64
    r = check_query_vector_provenance(
        ladders={ladder_name: toy_ladder()},
        provenance=prov_bad,
        rev1=tmp,
        pub=bank_dir,
        manifest_path=man_path,
        script_dir=Path(__file__).resolve().parent,
    )
    must_fail("swapped_question_vector_id", r)

    # 2. metadata list equal to raw (includes jira while filter is confluence)
    bad_eq = toy_ladder()
    raw_ids = bad_eq["runs"][0]["per_question"][0]["retrieved_doc_ids"]
    for run in bad_eq["runs"]:
        if run["condition"] == "meta_in":
            run["per_question"][0]["retrieved_doc_ids"] = list(raw_ids)
    r = check_invariants(ladders={ladder_name: bad_eq}, rev1=tmp, manifest_path=man_path)
    must_fail("metadata_equals_raw", r)

    # 3. empty list
    bad_empty = toy_ladder()
    bad_empty["runs"][0]["per_question"][0]["retrieved_doc_ids"] = []
    bad_empty["runs"][0]["per_question"][0]["scores"] = []
    r = check_schema(ladders={ladder_name: bad_empty}, rev1=tmp, pub=bank_dir)
    must_fail("empty_list", r)

    # 4. dropped top document at larger scale
    bad_drop = toy_ladder()
    small = IDS10[:]
    large = IDS10[1:] + ["d10"]
    scores_large = [0.99 - 0.01 * i for i in range(10)]
    for run in bad_drop["runs"]:
        if run["condition"] == "raw" and run["scale"] == 5000:
            run["per_question"][0]["retrieved_doc_ids"] = small
            run["per_question"][0]["scores"] = SCORES10[:]
        if run["condition"] == "raw" and run["scale"] == 10000:
            run["per_question"][0]["retrieved_doc_ids"] = large
            run["per_question"][0]["scores"] = scores_large
    r = check_invariants(ladders={ladder_name: bad_drop}, rev1=tmp, manifest_path=man_path)
    must_fail("dropped_top_at_larger_scale", r)

    # 5. duplicated doc id
    bad_dup = toy_ladder()
    ids = IDS10[:]
    ids[1] = ids[0]
    bad_dup["runs"][0]["per_question"][0]["retrieved_doc_ids"] = ids
    r = check_schema(ladders={ladder_name: bad_dup}, rev1=tmp, pub=bank_dir)
    must_fail("duplicate_doc_id", r)

    # 6. labelled HNSW with Seq Scan evidence
    hnsw_seq = {
        "meta": {
            "search_mode": "hnsw",
            "plan_check": [
                {
                    "hnsw_index_scan": False,
                    "innermost_scan_node_type": "Seq Scan",
                    "scan_node_types": ["Seq Scan"],
                }
            ],
        },
        "runs": [],
    }
    r = check_search_mode_truth(artifacts=[("per_n_hnsw_eval_toy.json", hnsw_seq)], rev1=tmp, pub=bank_dir)
    must_fail("hnsw_label_seq_scan", r)

    all_false = {
        "meta": {"search_mode": "hnsw"},
        "cells": [
            {
                "condition": "raw",
                "scale_n": 5000,
                "ef_search": 200,
                "iterative_scan": "relaxed_order",
                "max_scan_tuples": 20000,
                "seqscan_off": False,
                "hnsw_index_used": False,
                "plan": {"hnsw_index_used": False, "seq_scan": False, "plan_kind": "other"},
                "cell_id": "raw_5k_all_false",
            }
        ],
    }
    r = check_search_mode_truth(artifacts=[("per_n_hnsw_eval_allfalse.json", all_false)], rev1=tmp, pub=bank_dir)
    must_fail("per_n_all_hnsw_false", r, also=("hnsw_index_used=false",))

    empty_runs = toy_ladder()
    empty_runs["meta"]["skipped"] = False
    empty_runs["runs"] = []
    r = check_schema(ladders={ladder_name: empty_runs}, rev1=tmp, pub=bank_dir)
    must_fail("empty_runs_not_skipped", r, also=("runs==[]",))

    missing_cell = toy_ladder()
    missing_cell["runs"] = [run for run in missing_cell["runs"] if not (run["condition"] == "raw" and run["scale"] == 10000)]
    r = check_schema(ladders={ladder_name: missing_cell}, rev1=tmp, pub=bank_dir)
    must_fail("missing_meta_cell", r, also=("missing cells",))

    all_plan_skipped = toy_ladder()
    all_plan_skipped["meta"]["skipped"] = False
    all_plan_skipped["meta"]["plan_check"] = [
        {"eval_id": "q1::basic", "skipped": True, "skip_reason": "missing_query_vector"}
    ]
    r = check_schema(ladders={ladder_name: all_plan_skipped}, rev1=tmp, pub=bank_dir)
    must_fail("all_plan_check_skipped", r, also=("no_executed_plan_check",))

    qid_mismatch = toy_ladder()
    qid_mismatch["runs"][1]["per_question"][0]["question_id"] = "q2::basic"
    r = check_invariants(ladders={ladder_name: qid_mismatch}, rev1=tmp, manifest_path=man_path)
    must_fail("qid_set_mismatch", r, also=("question_id set mismatch",))

    # 7. missing plan_check
    missing = toy_ladder()
    del missing["meta"]["plan_check"]
    r = check_schema(ladders={ladder_name: missing}, rev1=tmp, pub=bank_dir)
    must_fail("missing_plan_check", r)

    # 8. claim expected off by 0.01
    claims = [
        {
            "id": "toy.hit",
            "description": "off by 0.01",
            "artifact": "toy.json",
            "json_path": ["value"],
            "expected": 0.80,
            "tolerance": 0,
        }
    ]
    toy_json = tmp / "toy.json"
    toy_json.write_text('{"value": 0.81}', encoding="utf-8")
    r = check_claim_registry(claims=claims, root=tmp, claims_path=tmp / "claims.json")
    must_fail("claim_expected_off_by_0.01", r)

    gold = {"q1::basic": ["d000"]}
    ids100 = [f"d{i:03d}" for i in range(100)]
    bm_ids = [f"b{i:03d}" for i in range(100)]
    from harness_lib import question_metrics, rrf_fuse

    def scale_block(scale: int) -> dict:
        fused = rrf_fuse([ids100, bm_ids], k=60, top_n=10)
        m = question_metrics(gold["q1::basic"], fused)
        return {
            "scale": scale,
            "rrf_k60": {"hit_at_10": m["hit_at_10"], "mrr": m["mrr"]},
        }

    dense = {"by_scale": {str(s): {"q1::basic": {"retrieved_top100": list(ids100)}} for s in (5000, 50000, 100000)}}
    bm25 = {
        "per_question_by_scale": {
            str(s): [{"question_id": "q1::basic", "retrieved_top100": list(bm_ids)}]
            for s in (5000, 50000, 100000)
        }
    }
    rrf = {"by_scale": [scale_block(s) for s in (5000, 50000, 100000)]}
    dense_bad = copy.deepcopy(dense)
    dense_bad["by_scale"]["5000"]["q1::basic"]["retrieved_top100"] = list(reversed(ids100))
    msgs = extra_cross_mismatches(
        rev1=tmp,
        dense=dense_bad,
        bm25=bm25,
        rrf=rrf,
        gold=gold,
        routing={"results": []},
        exact_openai={"runs": []},
        per_n={"openai": {"cells": [], "per_question_ef200": {}}, "titan": {"cells": [], "per_question_ef200": {}}},
        exact_by_emb={"openai": {"runs": []}, "titan": {"runs": []}},
        uniform_blobs={},
        manifest_path=tmp / "no_manifest.json",
    )
    if not any(m.startswith("FAIL:") and "RRF" in m for m in msgs):
        raise SystemExit(f"MUTATION FAIL rrf_list_order: {msgs[:12]}")
    print("PASS mutation rrf_list_order detected (CROSS_IMPLEMENTATION FAIL)")

    pern = {
        "cells": [
            {
                "scale_n": 5000,
                "condition": "raw",
                "ef_search": 200,
                "iterative_scan": "relaxed_order",
                "seqscan_off": False,
                "max_scan_tuples": 20000,
                "recall_at_10_vs_exact": 0.5,
                "hit_at_10_drop": 0.005,
            }
        ],
        "per_question_ef200": {
            "N=5000|raw|ef=200|relaxed_order|mst=20000": [
                {
                    "question_id": "q1::basic",
                    "retrieved_doc_ids": IDS10,
                    "hit_at_10": 1.0,
                }
            ]
        },
    }
    exact_toy = {
        "runs": [
            {
                "condition": "raw",
                "scale": 5000,
                "metrics": {"hit_at_10": 1.0},
                "per_question": [{"question_id": "q1::basic", "retrieved_doc_ids": IDS10, "hit_at_10": True}],
            }
        ]
    }
    msgs = extra_cross_mismatches(
        rev1=tmp,
        dense={"by_scale": {}},
        bm25={"per_question_by_scale": {}},
        rrf={"by_scale": []},
        gold=gold,
        routing={"results": []},
        exact_openai=exact_toy,
        per_n={"openai": pern, "titan": {"cells": [], "per_question_ef200": {}}},
        exact_by_emb={"openai": exact_toy, "titan": {"runs": []}},
        uniform_blobs={},
        manifest_path=tmp / "no_manifest.json",
    )
    if not any(m.startswith("FAIL:") and "per-size recall" in m for m in msgs):
        raise SystemExit(f"MUTATION FAIL per_size_recall: {msgs[:12]}")
    print("PASS mutation per_size_recall detected (CROSS_IMPLEMENTATION FAIL)")

    routing_bad = {
        "results": [
            {"mode": "wrong_type", "p": 0.0, "scale": s, "hit_at_10": {"estimate": 0.5}}
            for s in (5000, 10000, 15000, 20000, 25000, 40000, 50000, 75000, 100000)
        ]
    }
    exact_meta = {
        "runs": [
            {
                "condition": "meta_in",
                "scale": s,
                "metrics": {"hit_at_10": 0.875},
                "per_question": [],
            }
            for s in (5000, 10000, 15000, 20000, 25000, 40000, 50000, 75000, 100000)
        ]
    }
    msgs = extra_cross_mismatches(
        rev1=tmp,
        dense={"by_scale": {}},
        bm25={"per_question_by_scale": {}},
        rrf={"by_scale": []},
        gold=gold,
        routing=routing_bad,
        exact_openai=exact_meta,
        per_n={"openai": {"cells": [], "per_question_ef200": {}}, "titan": {"cells": [], "per_question_ef200": {}}},
        exact_by_emb={"openai": exact_meta, "titan": {"runs": []}},
        uniform_blobs={},
        manifest_path=tmp / "no_manifest.json",
    )
    if not any(m.startswith("FAIL:") and "routing" in m for m in msgs):
        raise SystemExit(f"MUTATION FAIL routing_probability: {msgs[:12]}")
    print("PASS mutation routing_probability detected (CROSS_IMPLEMENTATION FAIL)")

    claims_tex = [
        {
            "id": "toy.tex",
            "artifact": "toy.json",
            "json_path": ["value"],
            "expected": 0.81,
            "tolerance": 0,
            "tex_strings": ["THIS_STRING_IS_NOT_IN_THE_MANUSCRIPT"],
        }
    ]
    r = check_claim_registry(
        claims=claims_tex,
        root=tmp,
        claims_path=tmp / "claims.json",
        tex_text="Hit@10 falls $0.795{\\to}0.585$.",
    )
    must_fail("tex_string_absent", r)

    uni_name = str(tmp / "exact_ladder_uniform_s42_openai_primary200.json")
    bad_uni = toy_ladder()
    small = IDS10[:]
    large = IDS10[1:] + ["d10"]
    scores_large = [0.99 - 0.01 * i for i in range(10)]
    for run in bad_uni["runs"]:
        if run["condition"] == "raw" and run["scale"] == 5000:
            run["per_question"][0]["retrieved_doc_ids"] = small
            run["per_question"][0]["scores"] = SCORES10[:]
        if run["condition"] == "raw" and run["scale"] == 10000:
            run["per_question"][0]["retrieved_doc_ids"] = large
            run["per_question"][0]["scores"] = scores_large
    r = check_invariants(ladders={uni_name: bad_uni}, rev1=tmp, manifest_path=man_path)
    must_fail("uniform_ladder_dropped_top", r)

    pool_name = str(tmp / "exact_ladder_pool_prop_s42_openai_primary200.json")
    bad_pool = toy_ladder()
    small = IDS10[:]
    large = IDS10[1:] + ["d10"]
    scores_large = [0.99 - 0.01 * i for i in range(10)]
    for run in bad_pool["runs"]:
        if run["condition"] == "raw" and run["scale"] == 5000:
            run["per_question"][0]["retrieved_doc_ids"] = small
            run["per_question"][0]["scores"] = SCORES10[:]
        if run["condition"] == "raw" and run["scale"] == 10000:
            run["per_question"][0]["retrieved_doc_ids"] = large
            run["per_question"][0]["scores"] = scores_large
    r = check_invariants(ladders={pool_name: bad_pool}, rev1=tmp, manifest_path=man_path)
    must_fail("pool_ladder_dropped_top", r)

    compact = {
        "n_documents": 12,
        "documents": [
            [did, st, i, 0] for i, (did, st) in enumerate(toy_docs().items())
        ],
        "questions": [
            {
                "eval_id": "q1::basic",
                "question_type": "basic",
                "source_types": ["confluence"],
                "expected_doc_ids": ["d0"],
            }
        ],
    }
    for row in compact["documents"]:
        if row[0] == "d0":
            row[1] = "jira"
    compact_path = tmp / "scale_manifest_compact.json"
    compact_path.write_text(json.dumps(compact), encoding="utf-8")
    r = check_invariants(ladders={ladder_name: toy_ladder()}, rev1=tmp, manifest_path=compact_path)
    must_fail("compact_manifest_bad_source_type", r)

    slope_ladder = toy_ladder()
    for run in slope_ladder["runs"]:
        if run["condition"] == "meta_in" and run["scale"] == 10000:
            run["per_question"][0]["hit_at_10"] = False
    slope_path = tmp / "exact_ladder_openai_primary400.json"
    slope_path.write_text(json.dumps(slope_ladder), encoding="utf-8")
    claims_slope = [
        {
            "id": "toy.n400.slope",
            "artifact": "exact_ladder_openai_primary400.json",
            "compute": "n400_lift_slope",
            "json_path": [],
            "expected": {"estimate": 0.0, "ci90_lo": 0.0, "ci90_hi": 0.0},
            "tolerance": 0.01,
        }
    ]
    r = check_claim_registry(claims=claims_slope, root=tmp, claims_path=tmp / "claims.json")
    must_fail("changed_n400_slope", r)

    print("ALL MUTATION TESTS DETECTED THEIR CORRUPTIONS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
