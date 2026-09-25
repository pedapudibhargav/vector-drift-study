# L4 human spot-check results (author)

**Auditor:** BP · **Queue:** `l4_spotcheck_queue.csv` (10 rows) · **Source:** `/api/audit/queue`

## Summary

| Metric | Value |
|--------|-------|
| Spot rows labeled | 10/10 |
| Agree with LLM fairness (`y`) | **9/10** |
| Unsure | **1/10** (`qst_0003::metadata` N=5k raw) |
| Disagree (`n`) | 0 |
| Extra human labels beyond spot queue | 4 (total human done=14) |

## The one unsure row

- `qst_0003::metadata` · N=5000 · raw · auto Hit@10=true  
- Human: `unsure` · failure_mode=`label_noise`  
- Notes: “Chunk doesn't have answer to exact question”  
- Interpretation: Hit@10 membership can be “fair” as ID-in-top-10 while gold text is still a weak answer span — secondary label-noise signal, does **not** invalidate L1 Hit@k.

## Paper citation stance

Cite as: author spot-check corroborated LLM fairness on 9/10 rows; 1/10 unsure (label_noise). Secondary only. Primary claims remain L1.

Machine-readable: `l4_spotcheck_human_results.json`
