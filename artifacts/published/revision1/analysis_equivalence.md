# Equivalence analysis (TOST-style bootstrap)

Paired bootstrap over primary-200 questions (Hit@10, exact search). B=10000, seed=42, 90% percentile CI. Equivalence within δ iff CI ⊂ (−δ, +δ) strictly.

## Headline paired differences (5k→100k drop)

- **(a)** OpenAI−Titan raw drop: +0.035 [-0.020, +0.090] equiv@0.05=NO equiv@0.10=YES min_delta=0.090
- **(b)** OpenAI−Titan meta_in drop: +0.025 [-0.025, +0.075] equiv@0.05=NO equiv@0.10=YES min_delta=0.075

**Equivalence is NOT shown at δ=0.05 for (a).** The 90% interval is not strictly inside (−0.05, +0.05).

**Equivalence is NOT shown at δ=0.05 for (b).** The 90% interval is not strictly inside (−0.05, +0.05).

## (c) OpenAI−Titan metadata lift by scale

- N=5000: -0.005 [-0.045, +0.035] equiv@0.05=YES equiv@0.10=YES min_delta=0.045
- N=10000: +0.030 [-0.005, +0.065] equiv@0.05=NO equiv@0.10=YES min_delta=0.065 — **not equivalent @0.05**
- N=15000: +0.020 [-0.010, +0.050] equiv@0.05=NO equiv@0.10=YES min_delta=0.050 — **not equivalent @0.05**
- N=20000: -0.005 [-0.045, +0.035] equiv@0.05=YES equiv@0.10=YES min_delta=0.045
- N=25000: -0.005 [-0.045, +0.035] equiv@0.05=YES equiv@0.10=YES min_delta=0.045
- N=40000: -0.040 [-0.085, +0.005] equiv@0.05=NO equiv@0.10=YES min_delta=0.085 — **not equivalent @0.05**
- N=50000: -0.025 [-0.070, +0.015] equiv@0.05=NO equiv@0.10=YES min_delta=0.070 — **not equivalent @0.05**
- N=75000: -0.010 [-0.055, +0.035] equiv@0.05=NO equiv@0.10=YES min_delta=0.055 — **not equivalent @0.05**
- N=100000: +0.005 [-0.030, +0.045] equiv@0.05=YES equiv@0.10=YES min_delta=0.045

## (d) OpenAI−Titan raw Hit@10 level by scale

- N=5000: +0.010 [-0.030, +0.050] equiv@0.05=NO equiv@0.10=YES min_delta=0.050 — **not equivalent @0.05**
- N=10000: -0.020 [-0.060, +0.020] equiv@0.05=NO equiv@0.10=YES min_delta=0.060 — **not equivalent @0.05**
- N=15000: -0.025 [-0.070, +0.020] equiv@0.05=NO equiv@0.10=YES min_delta=0.070 — **not equivalent @0.05**
- N=20000: -0.020 [-0.065, +0.025] equiv@0.05=NO equiv@0.10=YES min_delta=0.065 — **not equivalent @0.05**
- N=25000: -0.025 [-0.070, +0.020] equiv@0.05=NO equiv@0.10=YES min_delta=0.070 — **not equivalent @0.05**
- N=40000: -0.005 [-0.055, +0.045] equiv@0.05=NO equiv@0.10=YES min_delta=0.055 — **not equivalent @0.05**
- N=50000: -0.005 [-0.055, +0.045] equiv@0.05=NO equiv@0.10=YES min_delta=0.055 — **not equivalent @0.05**
- N=75000: -0.020 [-0.070, +0.030] equiv@0.05=NO equiv@0.10=YES min_delta=0.070 — **not equivalent @0.05**
- N=100000: -0.025 [-0.075, +0.020] equiv@0.05=NO equiv@0.10=YES min_delta=0.075 — **not equivalent @0.05**

## (e) Dense drop minus BM25 drop (5k→100k)

- openai_raw: +0.085 [+0.025, +0.145] equiv@0.05=NO equiv@0.10=NO min_delta=0.145 — **not equivalent @0.05**
- titan_raw: +0.050 [-0.005, +0.105] equiv@0.05=NO equiv@0.10=NO min_delta=0.105 — **not equivalent @0.05**

## (f) Lift(100k)−lift(5k) within embedder

- openai: +0.000 [-0.040, +0.040] equiv@0.05=YES equiv@0.10=YES min_delta=0.040
- titan: -0.010 [-0.055, +0.035] equiv@0.05=NO equiv@0.10=YES min_delta=0.055 — **not equivalent @0.05**

## Acceptance tests

- manager_match_a: **PASS** — actual={'estimate': 0.035, 'ci90_lo': -0.02, 'ci90_hi': 0.09}
- manager_match_b: **PASS** — actual={'estimate': 0.025, 'ci90_lo': -0.025, 'ci90_hi': 0.075}
- a_equiv_delta_0.10_manager: **PASS** — actual={'equivalent_delta_0.05': False, 'equivalent_delta_0.10': True}
