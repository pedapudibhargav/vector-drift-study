# LLM audit panel (revision 1, G6)

Generated: 2026-11-11T08:31:26Z

## Rubric

A document FULLY ANSWERS the question only if every part of the question can be answered from the document alone. It PARTIALLY answers if it contains some but not all of what is needed, or only background. It does NOT answer if it is about something else or lacks the requested information. First think step by step in at most 80 words. Then give a verdict. You must quote, verbatim and in double quotes, the single sentence or phrase from the document that best supports your verdict; if there is none, write the empty string and the verdict must be 'no'. Respond with JSON only: {"reasoning": "...", "quote": "...", "verdict": "full" | "partial" | "no"}.

## Models / judges

Judges: `terra, grok47, gpt4o, gemini`

Planned items: `{"displacer": 42, "competitor5k": 42, "gold_control": 15, "random_control": 10, "near_miss": 20, "total": 129}`

## Per-judge category shares (Wilson 95% per verdict label)

### Judge `terra`

- API judgments in cache: 129; quote downgrades: 0
- Displacer `full` count: 3 (0.015 / 200)

| category | n | full | partial | no | unsupported | invalid | full+partial | Wilson |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| displacer | 42 | 3 | 24 | 15 | 0 | 0 | 0.6429 | 0.4917–0.7701 |
| competitor5k | 42 | 3 | 25 | 14 | 0 | 0 | 0.6667 | 0.5155–0.7899 |
| gold_control | 15 | 10 | 4 | 1 | 0 | 0 | 0.9333 | 0.7018–0.9881 |
| random_control | 10 | 0 | 0 | 10 | 0 | 0 | 0.0 | 0.0–0.2775 |
| near_miss | 20 | 0 | 2 | 18 | 0 | 0 | 0.1 | 0.0279–0.301 |

- Calibration gold full+partial: **0.9333** (Wilson [0.7018, 0.9881])
- Random control full+partial: **0.0**
- Near-miss control full+partial: **0.1**

### Judge `grok47`

- API judgments in cache: 129; quote downgrades: 1
- Displacer `full` count: 0 (0.0 / 200)

| category | n | full | partial | no | unsupported | invalid | full+partial | Wilson |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| displacer | 42 | 0 | 17 | 25 | 0 | 0 | 0.4048 | 0.2704–0.5551 |
| competitor5k | 42 | 0 | 13 | 29 | 0 | 0 | 0.3095 | 0.1907–0.4603 |
| gold_control | 15 | 9 | 4 | 1 | 1 | 0 | 0.8667 | 0.6212–0.9626 |
| random_control | 10 | 0 | 0 | 10 | 0 | 0 | 0.0 | 0.0–0.2775 |
| near_miss | 20 | 0 | 0 | 20 | 0 | 0 | 0.0 | 0.0–0.1611 |

- Calibration gold full+partial: **0.8667** (Wilson [0.6212, 0.9626])
- Random control full+partial: **0.0**
- Near-miss control full+partial: **0.0**

### Judge `gpt4o`

- API judgments in cache: 109; quote downgrades: 0
- Displacer `full` count: 10 (0.05 / 200)

| category | n | full | partial | no | unsupported | invalid | full+partial | Wilson |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| displacer | 42 | 10 | 10 | 22 | 0 | 0 | 0.4762 | 0.3336–0.6228 |
| competitor5k | 42 | 12 | 7 | 23 | 0 | 0 | 0.4524 | 0.3122–0.6005 |
| gold_control | 15 | 12 | 0 | 3 | 0 | 0 | 0.8 | 0.5481–0.9295 |
| random_control | 10 | 0 | 0 | 10 | 0 | 0 | 0.0 | 0.0–0.2775 |
| near_miss | 0 | 0 | 0 | 0 | 0 | 0 | None | None–None |

- Calibration gold full+partial: **0.8** (Wilson [0.5481, 0.9295])
- Random control full+partial: **0.0**
- Near-miss control full+partial: **None**

### Judge `gemini`

- API judgments in cache: 109; quote downgrades: 0
- Displacer `full` count: 2 (0.01 / 200)

| category | n | full | partial | no | unsupported | invalid | full+partial | Wilson |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| displacer | 42 | 2 | 4 | 36 | 0 | 0 | 0.1429 | 0.0672–0.2784 |
| competitor5k | 42 | 0 | 3 | 39 | 0 | 0 | 0.0714 | 0.0246–0.1901 |
| gold_control | 15 | 10 | 2 | 3 | 0 | 0 | 0.8 | 0.5481–0.9295 |
| random_control | 10 | 0 | 0 | 10 | 0 | 0 | 0.0 | 0.0–0.2775 |
| near_miss | 0 | 0 | 0 | 0 | 0 | 0 | None | None–None |

- Calibration gold full+partial: **0.8** (Wilson [0.5481, 0.9295])
- Random control full+partial: **0.0**
- Near-miss control full+partial: **None**

## Pairwise agreement

- `['terra', 'grok47']`: n=129, κ(full±partial)=0.49, κ(full)=0.6925
- `['terra', 'gpt4o']`: n=109, κ(full±partial)=0.531, κ(full)=0.4503
- `['terra', 'gemini']`: n=109, κ(full±partial)=0.2431, κ(full)=0.7549
- `['grok47', 'gpt4o']`: n=109, κ(full±partial)=0.4048, κ(full)=0.3313
- `['grok47', 'gemini']`: n=109, κ(full±partial)=0.4518, κ(full)=0.8423
- `['gpt4o', 'gemini']`: n=109, κ(full±partial)=0.3887, κ(full)=0.3249

## Displacer majority (`full` by ≥ half of judges)

- Count: **3** / displaced M=42
- Upper bound on Hit@10 drop (÷200): **0.015**

Total API calls (session metas): 0
