# Gemini response schema (paste back to humans)

After reviewing `GEMINI_L4_REVIEW_PACK.md`, return **only**:

```json
[
  {
    "row_id": 1,
    "question_id": "qst_0003::metadata",
    "corpus_scale_size": 5000,
    "condition": "raw",
    "auto_hit_at_10": true,
    "gold_answers_question": false,
    "human_label_correct": "n",
    "human_failure_mode": "label_noise",
    "answer_span": null,
    "human_notes": "No explicit due date in full gold text."
  }
]
```

Valid `human_label_correct`: `y` | `n` | `unsure`

Valid `human_failure_mode`: `label_noise` | `chunk_too_thin` | `embedding_near_miss` | `semantic_near_miss` | `lexical_mismatch` | `wrong_source_type` | `stale_gold` | `multi_gold_partial` | `metadata_needed` | `other` | null

Example: Irene Choi SKU due date — full gold ends with `Due 2025-12-04` →
`gold_answers_question: true`, `human_label_correct: y`, `answer_span` quotes that line.
