#!/usr/bin/env python3
"""Full top-10 relevance audit of the 42 displaced questions (reviewer-driven extension of the panel audit).

Judges EVERY non-gold document in the raw exact top-10 at 100k with the same blinded rubric, so the result
answers: for how many displaced questions does at least one retrieved non-gold document fully answer it?
Provider: OpenAI chat (model from --model), cost-capped; documents judged once and cached.
"""
from __future__ import annotations

import argparse, json, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import llm_audit_panel as P  # noqa: E402

ROOT = P.ROOT
CACHE = P.DATA / "llm_audit_top10_cache_terra.jsonl"
OUT = P.REV1 / "llm_audit_top10.json"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="gpt-5.6-terra")
    ap.add_argument("--effort", default="high")
    ap.add_argument("--max-usd", type=float, default=3.0)
    ap.add_argument("--max-calls", type=int, default=500)
    ap.add_argument("--analyze", action="store_true")
    args = ap.parse_args()
    P.OPENAI_STATE["cap"] = args.max_usd
    P.OPENAI_STATE["effort"] = args.effort
    frozen, meta = P.load_frozen_plan_specs()
    displaced = meta["displaced_eval_ids"]
    q100 = P.load_ladder_raw()
    ladder = json.loads(P.LADDER_PATH.read_text())
    q5 = next({pq["question_id"]: pq for pq in r["per_question"]} for r in ladder["runs"] if r["condition"] == "raw" and int(r["scale"]) == 5000)
    questions = P.load_questions()
    tok = P.Tokenizer.load()
    specs = []
    for e in displaced:
        gold = set(questions[e]["expected_doc_ids"])
        top5 = set(q5[e]["retrieved_doc_ids"])
        for rank, d in enumerate(q100[e]["retrieved_doc_ids"], 1):
            if d in gold:
                continue
            specs.append({"eval_id": e, "doc_id": d, "rank100": rank, "was_in_top10_at_5k": d in top5})
    conn = P.pg_connect(); texts = {}
    with conn.cursor() as cur:
        ids = sorted({s["doc_id"] for s in specs})
        for i in range(0, len(ids), 500):
            cur.execute("SELECT doc_id, chunk_text FROM document_chunks WHERE doc_id = ANY(%s)", (ids[i:i+500],))
            for did, t in cur.fetchall():
                texts[str(did)] = t or ""
    conn.close()
    cache = P.load_cache(CACHE)
    for s in specs:
        s["item_id"] = P.stable_item_id("top10", s["eval_id"], s["doc_id"])
    n = 0
    for s in specs:
        key = P.stable_item_id("top10", s["eval_id"], s["doc_id"])
        s["item_id"] = key
        if key in cache or args.analyze:
            continue
        if n >= args.max_calls:
            break
        body, _ = tok.truncate_chunk(texts[s["doc_id"]], s["doc_id"], P.MAX_DOC_TOKENS)
        prompt = P.JUDGE_USER_PREFIX.format(question=questions[s["eval_id"]]["question"], document=body) + P.RUBRIC_INSTRUCTIONS
        P.assert_blinding(prompt, s["eval_id"], s["doc_id"])
        res = None
        for _try in range(2):
            try:
                res = P.process_response(P.openai_judge(prompt, args.model, 600), body)
            except (ValueError, RuntimeError) as exc:
                res = {"verdict": "invalid", "parse_error": str(exc)}
            n += 1
            if res["verdict"] != "invalid":
                break
        row = {"item_id": key, "eval_id": s["eval_id"], "doc_id": s["doc_id"], "rank100": s["rank100"],
               "new": not s["was_in_top10_at_5k"], "verdict": res["verdict"], "quote": res.get("quote"),
               "reasoning": res.get("reasoning"), "model": args.model}
        P.append_cache(CACHE, row); cache[key] = row
    # analysis
    per_q = {}
    for s in specs:
        r = cache.get(s["item_id"])
        if not r:
            continue
        d = per_q.setdefault(s["eval_id"], {"n_docs": 0, "full": 0, "partial": 0, "full_new": 0, "full_old": 0})
        d["n_docs"] += 1
        if r["verdict"] == "full":
            d["full"] += 1
            d["full_new" if r["new"] else "full_old"] += 1
        elif r["verdict"] == "partial":
            d["partial"] += 1
    judged = [e for e in displaced if e in per_q and per_q[e]["n_docs"] == sum(1 for s in specs if s["eval_id"] == e)]
    q_any_full = sum(1 for e in judged if per_q[e]["full"] > 0)
    q_any_new_full = sum(1 for e in judged if per_q[e]["full_new"] > 0)
    docs = [cache[s["item_id"]] for s in specs if s["item_id"] in cache]
    out = {
        "model": args.model, "effort": args.effort, "displaced_questions": len(displaced), "fully_judged_questions": len(judged),
        "n_documents_judged": len(docs),
        "verdict_counts": {v: sum(1 for d in docs if d["verdict"] == v) for v in ("full", "partial", "no", "unsupported", "invalid")},
        "questions_with_any_full": q_any_full, "questions_with_any_new_full": q_any_new_full,
        "share_questions_any_full": q_any_full / max(1, len(judged)),
        "upper_share_of_200": q_any_full / 200.0,
        "per_question": per_q,
    }
    OUT.write_text(json.dumps(out, indent=1))
    print(json.dumps({k: v for k, v in out.items() if k != "per_question"}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
