#!/usr/bin/env python3
"""Second label-completeness audit ("audit v3"), pre-registered in audit_v3/PREREGISTRATION.md.

Subcommands:
  build     build items (question, gold reference, 10 candidates + controls) from the exact ladder and the database
  selftest  unit-test the guardrails with synthetic judge outputs (no model calls)
  run       call a judge (Cursor CLI, read-only ask mode, empty workspace) once per question; resumable
  analyze   guardrails, control calibration, consensus counts, report

Guardrails are enforced in code: verbatim-quote check, subject match required for `full`, strict JSON with exactly one
entry per candidate id (retry, then invalid), seeded per-judge shuffling, no ranks/ids/sizes in the prompt.
"""
from __future__ import annotations

import argparse, hashlib, json, os, random, re, subprocess, sys, time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import llm_audit_panel as P  # noqa: E402

REV1 = P.REV1
OUTDIR = REV1 / "audit_v3"
ITEMS = OUTDIR / "items.json"
PREREG = OUTDIR / "PREREGISTRATION.md"
MAX_CHARS = 16000
JUDGES = {"gemini": "gemini-4-argon-high", "grok": "grok-4.7-high"}

INSTRUCTIONS = """You are a strict evidence checker for an enterprise question-answering benchmark.
You will see a QUESTION, a REFERENCE (one or more documents that are known to answer the question correctly) and several CANDIDATE documents.
For EACH candidate decide, independently of the other candidates, whether the candidate itself answers the question.
Rules:
1. Use only the text shown. Do not use outside knowledge.
2. First identify the specific subject of the QUESTION (named entities, accounts, people, tickets, regions, dates, versions). A candidate can answer the question only if it is about THAT SAME subject. A document about a similar but different entity, record or time period, or a generic template, does NOT answer it.
3. Verdicts: "full" = the candidate states the information needed to answer the whole question for the same subject and its answer is consistent with the REFERENCE. "partial" = same subject but incomplete, or only background. "conflict" = same subject but its answer contradicts the REFERENCE. "no" = anything else.
4. For "full", "partial" and "conflict" you MUST quote, verbatim and in double quotes, the single sentence or phrase from THE CANDIDATE (not from the reference) that best supports the verdict. If you cannot quote one, the verdict must be "no".
5. Judge each candidate in isolation. The reference is not a candidate.
Respond with JSON only, no other text, in exactly this form (one entry per candidate id, in any order):
{"results":[{"id":"C01","subject_match":true,"reasoning":"at most 60 words","quote":"verbatim text or empty string","verdict":"full"}]}
"""


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def clip(text: str) -> tuple[str, bool]:
    if len(text) <= MAX_CHARS:
        return text, False
    return text[:MAX_CHARS] + "\n[TRUNCATED]", True


# ----------------------------------------------------------------------------------------------- build
def cmd_build(args) -> int:
    ladder = json.loads(P.LADDER_PATH.read_text())
    byk = {int(r["scale"]): {pq["question_id"]: pq for pq in r["per_question"]} for r in ladder["runs"] if r["condition"] == "raw"}
    displaced = sorted(e for e, pq in byk[5000].items() if pq["hit_at_10"] and not byk[100000][e]["hit_at_10"])
    earlier = sorted(json.loads((REV1 / "llm_audit_top10.json").read_text())["per_question"])
    assert displaced == earlier, (len(displaced), len(earlier))
    q100 = P.load_ladder_raw()
    questions = P.load_questions()
    conn = P.pg_connect()
    with conn.cursor() as cur:
        cur.execute("SELECT doc_id, COALESCE(title,''), COALESCE(chunk_text,''), source_type FROM document_chunks WHERE scale_rank < 100000")
        docs = {str(d): (t, c, st) for d, t, c, st in cur.fetchall()}
    conn.close()
    rng = random.Random(20261112)
    all_ids = sorted(docs)
    bank_ids = list(P.load_ladder_raw().keys())
    items = []
    for e in displaced:
        q = questions[e]
        gold = [str(g) for g in q["expected_doc_ids"]]
        top = [str(d) for d in q100[e]["retrieved_doc_ids"]]
        cands = [("retrieved", d) for d in top if d not in gold]
        used = set(gold) | {d for _, d in cands}
        # random control
        while True:
            r = rng.choice(all_ids)
            if r not in used:
                break
        cands.append(("random", r)); used.add(r)
        # near-miss control: top non-gold document of another bank question with the same first source type
        st = (q.get("source_types") or [None])[0]
        others = [x for x in bank_ids if x != e and (questions[x].get("source_types") or [None])[0] == st]
        rng.shuffle(others)
        nm = None
        for x in others:
            for d in q100[x]["retrieved_doc_ids"]:
                d = str(d)
                if d not in used and d not in {str(g) for g in questions[x]["expected_doc_ids"]}:
                    nm = d; break
            if nm:
                break
        if nm:
            cands.append(("near_miss", nm)); used.add(nm)
        # positive control: a second gold document, if any
        ref_ids = gold
        if len(gold) >= 2:
            cands.append(("positive", gold[1])); ref_ids = [gold[0]]
        def pack(did):
            t, c, st_ = docs[did]
            body, trunc = clip((f"Title: {t}\n\n" if t else "") + c)
            return {"doc_id": did, "text": body, "truncated": trunc}
        items.append({"set": "main", "eval_id": e, "question": q["question"], "reference": [pack(g) for g in ref_ids if g in docs],
                      "candidates": [dict(pack(d), category=cat) for cat, d in cands]})
    # calibration set: other primary questions with >= 2 gold documents
    main_ids = set(displaced)
    for e in sorted(x for x in bank_ids if x not in main_ids and len(questions[x]["expected_doc_ids"]) >= 2):
        q = questions[e]; gold = [str(g) for g in q["expected_doc_ids"] if str(g) in docs]
        if len(gold) < 2:
            continue
        top = [str(d) for d in q100[e]["retrieved_doc_ids"]]
        used = set(gold) | set(top)
        cands = [("positive", g) for g in gold[1:3]]
        while True:
            r = rng.choice(all_ids)
            if r not in used:
                break
        cands.append(("random", r)); used.add(r)
        st = (q.get("source_types") or [None])[0]
        others = [x for x in bank_ids if x != e and (questions[x].get("source_types") or [None])[0] == st]
        rng.shuffle(others); nm = None
        for x in others:
            for d in q100[x]["retrieved_doc_ids"]:
                d = str(d)
                if d not in used and d not in {str(g) for g in questions[x]["expected_doc_ids"]}:
                    nm = d; break
            if nm:
                break
        if nm:
            cands.append(("near_miss", nm))
        def pack2(did):
            t_, c_, _st = docs[did]
            body, trunc = clip((f"Title: {t_}\n\n" if t_ else "") + c_)
            return {"doc_id": did, "text": body, "truncated": trunc}
        items.append({"set": "calibration", "eval_id": e, "question": q["question"], "reference": [pack2(gold[0])],
                      "candidates": [dict(pack2(d), category=cat) for cat, d in cands]})
    OUTDIR.mkdir(parents=True, exist_ok=True)
    ITEMS.write_text(json.dumps({"meta": {"n_questions": len(items), "n_main": sum(1 for i in items if i["set"]=="main"), "n_calibration": sum(1 for i in items if i["set"]=="calibration"), "seed": 20261112, "preregistration_sha256": sha(PREREG),
                                           "max_chars": MAX_CHARS}, "items": items}, indent=1))
    n = sum(len(i["candidates"]) for i in items)
    cats = {}
    for i in items:
        for c in i["candidates"]:
            cats[c["category"]] = cats.get(c["category"], 0) + 1
    print("items", len(items), "candidates", n, cats, "truncated", sum(c["truncated"] for i in items for c in i["candidates"]))
    return 0


# ----------------------------------------------------------------------------------------------- prompt
def build_prompt(item: dict, judge: str) -> tuple[str, dict]:
    rng = random.Random(f"{item['eval_id']}|{judge}|v3")
    cands = list(item["candidates"]); rng.shuffle(cands)
    ids = {f"C{i + 1:02d}": c for i, c in enumerate(cands)}
    parts = [INSTRUCTIONS, "QUESTION:\n" + item["question"].strip(), "REFERENCE (known to answer the question):"]
    for k, r in enumerate(item["reference"], 1):
        parts.append(f"[Reference {k}]\n{r['text']}\n[End of reference {k}]")
    parts.append("CANDIDATES:")
    for cid, c in ids.items():
        parts.append(f"[Candidate {cid}]\n{c['text']}\n[End of candidate {cid}]")
    prompt = "\n\n".join(parts)
    return prompt, ids


def parse_results(raw: str, ids: dict) -> list[dict]:
    a, b = raw.find("{"), raw.rfind("}")
    if a < 0 or b <= a:
        raise ValueError("no JSON object")
    obj = json.loads(raw[a:b + 1])
    res = obj.get("results")
    if not isinstance(res, list):
        raise ValueError("results must be a list")
    seen = set()
    for r in res:
        if not isinstance(r, dict) or r.get("id") not in ids:
            raise ValueError(f"unknown id {r.get('id') if isinstance(r, dict) else r}")
        if r["id"] in seen:
            raise ValueError(f"duplicate id {r['id']}")
        seen.add(r["id"])
        if str(r.get("verdict", "")).lower().strip() not in ("full", "partial", "conflict", "no"):
            raise ValueError(f"bad verdict for {r['id']}")
        if not isinstance(r.get("quote", ""), str) or not isinstance(r.get("reasoning", ""), str):
            raise ValueError(f"bad fields for {r['id']}")
    if seen != set(ids):
        raise ValueError(f"missing ids {sorted(set(ids) - seen)}")
    return res


def apply_guardrails(r: dict, text: str) -> dict:
    v = str(r["verdict"]).lower().strip(); q = r.get("quote", "") or ""
    sm = r.get("subject_match")
    out = {"raw_verdict": v, "subject_match": sm, "quote": q[:1000], "reasoning": (r.get("reasoning") or "")[:600]}
    if v in ("full", "partial", "conflict"):
        if len(q.strip()) < 12 or not P.quote_in_document(q, text):
            out["verdict"] = "unsupported"; return out
    if v == "full" and sm is not True:
        out["verdict"] = "no_subject"; return out
    out["verdict"] = v
    return out


# ----------------------------------------------------------------------------------------------- run
def judge_call(prompt: str, model: str, timeout: int) -> str:
    ws = Path(os.environ.get("AUDIT_EMPTY_WS", "/tmp/audit_empty_ws")); ws.mkdir(parents=True, exist_ok=True)
    return P.cursor_judge(prompt, ws, model, timeout)


def run_one(item: dict, judge: str, model: str, timeout: int, call=None) -> dict:
    call = call or judge_call
    prompt, ids = build_prompt(item, judge)
    last = ""
    for attempt in range(3):
        try:
            raw = call(prompt, model, timeout); last = raw
            res = parse_results(raw, ids)
            by = {r["id"]: r for r in res}
            rows = []
            for cid, c in ids.items():
                g = apply_guardrails(by[cid], c["text"])
                rows.append({"doc_id": c["doc_id"], "category": c["category"], "truncated": c["truncated"], **g})
            return {"eval_id": item["eval_id"], "judge": judge, "model": model, "attempts": attempt + 1, "status": "ok",
                    "rows": rows, "raw": raw[:60000]}
        except (ValueError, RuntimeError, subprocess.TimeoutExpired, json.JSONDecodeError) as exc:
            last = f"{last[:2000]}\n--ERR {exc}"
            time.sleep(2)
    return {"eval_id": item["eval_id"], "judge": judge, "model": model, "attempts": 3, "status": "invalid", "rows": [], "raw": last[:60000]}


def cmd_run(args) -> int:
    data = json.loads(ITEMS.read_text()); items = data["items"]
    judge = args.judge; model = JUDGES[judge]
    outp = OUTDIR / f"judgments_{judge}.jsonl"
    done = set()
    if outp.exists():
        for line in outp.read_text().splitlines():
            if line.strip():
                r = json.loads(line)
                if r["status"] == "ok":
                    done.add(r["eval_id"])
    todo = [i for i in items if i["eval_id"] not in done][: args.limit]
    print(f"{judge}: {len(done)} done, {len(todo)} to run", flush=True)
    with ThreadPoolExecutor(args.workers) as ex:
        for res in ex.map(lambda it: run_one(it, judge, model, args.timeout), todo):
            with outp.open("a") as f:
                f.write(json.dumps(res) + "\n")
            print(res["eval_id"], res["status"], "attempts", res["attempts"], flush=True)
    return 0


# ----------------------------------------------------------------------------------------------- analyze
def load_judgments(judge: str) -> dict:
    p = OUTDIR / f"judgments_{judge}.jsonl"; out = {}
    if p.exists():
        for line in p.read_text().splitlines():
            if line.strip():
                r = json.loads(line)
                if r["status"] == "ok":
                    out[r["eval_id"]] = r
    return out


def cmd_analyze(args) -> int:
    data = json.loads(ITEMS.read_text()); items = {i["eval_id"]: i for i in data["items"]}
    main_ids = {e for e, i in items.items() if i["set"] == "main"}
    J_all = {j: load_judgments(j) for j in JUDGES}
    J = {j: {e: r for e, r in recs.items() if e in main_ids} for j, recs in J_all.items()}
    report = {"meta": {"preregistration_sha256": sha(PREREG), "items_sha256": sha(ITEMS), "judges": JUDGES,
                       "questions": len(items), "valid_calls": {j: len(v) for j, v in J.items()}}}
    full = {j: {(e, r["doc_id"]) for e, rec in J[j].items() for r in rec["rows"] if r["category"] == "retrieved" and r["verdict"] == "full"} for j in J}
    per_judge = {}
    for j, recs in J_all.items():
        rows = [dict(r, eval_id=e) for e, rec in recs.items() for r in rec["rows"]]
        cat = {}
        for c in ("retrieved", "random", "near_miss", "positive"):
            rs = [r for r in rows if r["category"] == c]
            vc = {v: sum(1 for r in rs if r["verdict"] == v) for v in ("full", "partial", "conflict", "no", "unsupported", "no_subject")}
            cat[c] = {"n": len(rs), "verdicts": vc}
        fp = [r for r in rows if r["category"] in ("random", "near_miss")]
        fpk = sum(1 for r in fp if r["verdict"] == "full")
        pos = [r for r in rows if r["category"] == "positive"]
        posk = sum(1 for r in pos if r["verdict"] in ("full", "partial"))
        lo, hi = P.wilson_ci(fpk, len(fp)) if fp else (None, None)
        plo, phi = P.wilson_ci(posk, len(pos)) if pos else (None, None)
        qs_any = sorted({e for (e, _) in full[j]})
        pos_full = sum(1 for r in pos if r["verdict"] == "full")
        per_judge[j] = {"by_category": cat, "control_false_positive_full": {"k": fpk, "n": len(fp), "wilson95": [lo, hi]},
                        "positive_control_full_or_partial": {"k": posk, "n": len(pos), "wilson95": [plo, phi]}, "positive_control_full": {"k": pos_full, "n": len(pos)},
                        "questions_with_any_full": len(qs_any), "candidate_docs_full": len(full[j])}
    both = full["gemini"] & full["grok"]; either = full["gemini"] | full["grok"]
    qb = sorted({e for e, _ in both}); qe = sorted({e for e, _ in either})
    # agreement over retrieved candidates judged by both
    keys = [(e, r["doc_id"]) for e, rec in J["gemini"].items() if e in J["grok"] for r in rec["rows"] if r["category"] == "retrieved"]
    a = [k in full["gemini"] for k in keys]; b = [k in full["grok"] for k in keys]
    qs_any_by = {j: sorted({e for (e, _) in full[j]}) for j in J}
    report["per_judge"] = per_judge
    report["consensus"] = {"questions_scored_by_both": len({e for e in J["gemini"] if e in J["grok"]}),
                           "K_both_questions_with_any_full": len(qb), "K_either_questions_with_any_full": len(qe),
                           "docs_full_both": len(both), "docs_full_either": len(either),
                           "credit_both": len(qb) / 200.0, "credit_either": len(qe) / 200.0,
                           "adjusted_drop_both": 0.210 - len(qb) / 200.0, "adjusted_drop_either": 0.210 - len(qe) / 200.0,
                           "share_of_drop_both": len(qb) / 200.0 / 0.210, "share_of_drop_either": len(qe) / 200.0 / 0.210,
                           "kappa_full_vs_not": (P.cohens_kappa(a, b) if (any(a) or any(b)) else None), "kappa_note": "undefined when neither judge rated any candidate full", "n_candidate_pairs": len(keys),
                           "questions_both": qb, "questions_either": qe}
    # comparison with the earlier single-judge audit
    old = json.loads((REV1 / "llm_audit_top10.json").read_text())
    old_q = sorted(e for e, v in old["per_question"].items() if v.get("full", 0) > 0)
    report["comparison_with_earlier_terra_audit"] = {"earlier_questions_with_any_full": len(old_q),
        "of_which_confirmed_by_both": len(set(old_q) & set(qb)), "of_which_confirmed_by_either": len(set(old_q) & set(qe)),
        "new_questions_found_by_both_not_in_earlier": len(set(qb) - set(old_q))}
    # the earlier single-judge (Terra) 'full' documents, as judged by the two v3 judges
    old_rows = [json.loads(l) for l in (REV1 / "audit_judgments" / "llm_audit_top10_cache_terra.jsonl").read_text().splitlines() if l.strip()]
    old_full = {(r["eval_id"], r["doc_id"]) for r in old_rows if r["verdict"] == "full"}
    byk = {j: {(e, r["doc_id"]): r for e, rec in J_all[j].items() for r in rec["rows"] if r["category"] == "retrieved"} for j in J_all}
    report["earlier_terra_full_documents"] = {"n": len(old_full)}
    both_diff = sum(1 for k in old_full if all(k in byk[j] and byk[j][k].get("subject_match") is not True for j in J_all))
    report["earlier_terra_full_documents"]["both_judges_different_subject"] = both_diff
    for j in J_all:
        vc = {}
        sm = {"subject_match_false": 0, "subject_match_true": 0}
        for k in old_full:
            r = byk[j].get(k)
            if r is None:
                continue
            vc[r["verdict"]] = vc.get(r["verdict"], 0) + 1
            sm["subject_match_true" if r.get("subject_match") is True else "subject_match_false"] += 1
        report["earlier_terra_full_documents"][j] = {"verdicts": vc, **sm}
    for j, v in report["per_judge"].items():
        pos = v["by_category"]["positive"]
        n = pos["n"]; non_no = n - pos["verdicts"].get("no", 0)
        v["positive_control_any_verdict_other_than_no"] = {"k": non_no, "n": n, "rate": non_no / n if n else None}
        sens = v["positive_control_full_or_partial"]["k"] / n if n else None
        v["rescaled_credit_if_sensitivity_below_0.9"] = {"sensitivity_full_or_partial": sens, "rescaled_credit": (len(qs_any_by[j]) / 200.0 / sens) if sens else None}
    (OUTDIR / "analysis.json").write_text(json.dumps(report, indent=1))
    print(json.dumps({k: v for k, v in report.items() if k != "per_judge"}, indent=1)[:3000])
    for j, v in per_judge.items():
        print(j, "FP", v["control_false_positive_full"], "POS", v["positive_control_full_or_partial"], "Q any full", v["questions_with_any_full"])
    return 0


# ----------------------------------------------------------------------------------------------- selftest
def cmd_selftest(args) -> int:
    item = {"eval_id": "qst_9999::x", "question": "What is the retry limit for Acme Corp?",
            "reference": [{"doc_id": "dsid_ref", "text": "Acme Corp retry limit is 5.", "truncated": False}],
            "candidates": [{"doc_id": "dsid_a", "text": "Acme Corp: the retry limit is 5 attempts.", "truncated": False, "category": "retrieved"},
                           {"doc_id": "dsid_b", "text": "Beta Inc: the retry limit is 7 attempts.", "truncated": False, "category": "retrieved"},
                           {"doc_id": "dsid_c", "text": "Unrelated text about lunch.", "truncated": False, "category": "random"}]}
    prompt, ids = build_prompt(item, "gemini")
    assert item["eval_id"] not in prompt and "dsid_" not in prompt, "identifier leaked"
    inv = {c["doc_id"]: cid for cid, c in ids.items()}
    def mk(rs): return json.dumps({"results": rs})
    # 1 good answer for A, fabricated quote for B, subject_match false full for C
    good = mk([{"id": inv["dsid_a"], "subject_match": True, "reasoning": "x", "quote": "the retry limit is 5 attempts", "verdict": "full"},
               {"id": inv["dsid_b"], "subject_match": True, "reasoning": "x", "quote": "the retry limit is 5 attempts for Beta", "verdict": "full"},
               {"id": inv["dsid_c"], "subject_match": False, "reasoning": "x", "quote": "lunch", "verdict": "full"}])
    r = run_one(item, "gemini", "m", 1, call=lambda p, m, t: good)
    v = {x["doc_id"]: x["verdict"] for x in r["rows"]}
    assert v["dsid_a"] == "full", v
    assert v["dsid_b"] == "unsupported", v          # fabricated quote caught
    assert v["dsid_c"] == "unsupported", v          # quote too short / not usable
    # entity mismatch with a real quote must not count as full
    ent = mk([{"id": inv["dsid_a"], "subject_match": True, "reasoning": "x", "quote": "the retry limit is 5 attempts", "verdict": "full"},
              {"id": inv["dsid_b"], "subject_match": False, "reasoning": "x", "quote": "the retry limit is 7 attempts", "verdict": "full"},
              {"id": inv["dsid_c"], "subject_match": False, "reasoning": "x", "quote": "", "verdict": "no"}])
    r = run_one(item, "gemini", "m", 1, call=lambda p, m, t: ent); v = {x["doc_id"]: x["verdict"] for x in r["rows"]}
    assert v["dsid_b"] == "no_subject", v
    # missing id -> retries then invalid
    miss = mk([{"id": inv["dsid_a"], "subject_match": True, "reasoning": "x", "quote": "", "verdict": "no"}])
    r = run_one(item, "gemini", "m", 1, call=lambda p, m, t: miss)
    assert r["status"] == "invalid" and r["attempts"] == 3
    # prose around JSON is tolerated; garbage retried
    calls = {"n": 0}
    def flaky(p, m, t):
        calls["n"] += 1
        return "not json" if calls["n"] == 1 else "Here you go:\n" + ent
    r = run_one(item, "gemini", "m", 1, call=flaky)
    assert r["status"] == "ok" and r["attempts"] == 2
    # per-judge shuffles differ
    _, ids_g = build_prompt(item, "gemini"); _, ids_k = build_prompt(item, "grok")
    print("SELFTEST OK")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(); sp = ap.add_subparsers(dest="cmd", required=True)
    sp.add_parser("build"); sp.add_parser("selftest"); sp.add_parser("analyze")
    r = sp.add_parser("run"); r.add_argument("--judge", choices=list(JUDGES), required=True)
    r.add_argument("--workers", type=int, default=4); r.add_argument("--limit", type=int, default=10 ** 6); r.add_argument("--timeout", type=int, default=1500)
    args = ap.parse_args()
    return {"build": cmd_build, "selftest": cmd_selftest, "run": cmd_run, "analyze": cmd_analyze}[args.cmd](args)


if __name__ == "__main__":
    raise SystemExit(main())
