# Titan truncation sensitivity (primary-200)

Gold documents with `chunk_text` length > 24,000 characters (Titan truncation rule) from `doc_length_stats.json`. Questions whose gold set includes any such doc are excluded; both embedder ladders are recomputed on the same reduced question set.

Truncated primary-200 gold doc_ids (2): dsid_6c4c1c875e704f09b4d791d64d7bc7e5, dsid_aa97b7293f9f4f3c8180f645e4fe5911

Excluded questions: **2** (of 200)

Excluded eval_ids:
- qst_0002::metadata
- qst_0004::basic

## Hit@10 changes at 5k, 50k, 100k (reduced − full)

| embedder | condition | 5k | 50k | 100k |
|---|---|---:|---:|---:|
| openai | raw | +0.008 | +0.006 | +0.006 |
| openai | meta_in | +0.004 | +0.002 | +0.002 |
| titan | raw | +0.003 | +0.001 | +0.001 |
| titan | meta_in | -0.001 | +0.002 | +0.002 |

## Paired drop differences (reduced − full)

- openai_minus_titan_raw_drop: +0.000
- openai_minus_titan_meta_in_drop: +0.005

## Full vs reduced snapshots (Hit@10 means)

### Full (n=200)
- openai raw: 5000=0.795, 50000=0.640, 100000=0.585
- openai meta_in: 5000=0.875, 50000=0.715, 100000=0.665
- titan raw: 5000=0.785, 50000=0.645, 100000=0.610
- titan meta_in: 5000=0.870, 50000=0.745, 100000=0.685

### Reduced (n=198)
- openai raw: 5000=0.803, 50000=0.646, 100000=0.591
- openai meta_in: 5000=0.879, 50000=0.717, 100000=0.667
- titan raw: 5000=0.788, 50000=0.646, 100000=0.611
- titan meta_in: 5000=0.869, 50000=0.747, 100000=0.687

## Equivalence on reduced set (selected)

- (a) raw drop diff: +0.035 [-0.020, +0.091] equiv@0.05=NO
  - **Equivalence is NOT shown at δ=0.05 for (a) on the reduced set.**
- (b) meta_in drop diff: +0.030 [-0.020, +0.081] equiv@0.05=NO
  - **Equivalence is NOT shown at δ=0.05 for (b) on the reduced set.**
