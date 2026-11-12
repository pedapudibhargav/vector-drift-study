# OpenAI 8,191-token character cuts (`doc_token_cuts_openai.json`)

## Keys

Top-level object: one entry per `doc_id` in `data/rev1_doc_token_cuts.jsonl` (official tiktoken).

Each value:

- `chars`: character length of `title + ' ' + chunk_text`
- `tokens`: cl100k_base token count of that string (`encode(..., disallowed_special=())`)
- `cut_char_8191`: character offset of the first 8,191 tokens, or the full length if the string is shorter
- `in_ladder_pool`: true when the document is in the headline ladder pool (`embedding IS NOT NULL AND scale_rank IS NOT NULL AND scale_rank < 100000`)

Headline length / truncation tables are in `doc_length_stats.json` and `doc_length_stats.md` (ladder pool n=99998).
Do not treat this cut map as the length-stats table.
