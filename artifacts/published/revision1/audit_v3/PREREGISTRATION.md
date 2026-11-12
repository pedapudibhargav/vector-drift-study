# Pre-registration: second label-completeness audit ("audit v3")

Written before any judge call. File hash is recorded in every output file.

## Question
For the 42 primary questions whose gold document is in the exact raw top-10 at 5k and not at 100k, how many have at least one retrieved NON-gold document in the 100k top-10 that genuinely answers the question? This bounds how much of the Hit@10 drop could be an artifact of incomplete labels.

## Design (fixed)
- Candidates: every non-gold document in the exact raw top-10 at 100k for each of the 42 questions (420 documents).
- Reference: the question's known-correct gold document(s) are shown to the judge as REFERENCE (not as a candidate).
- Judges: two models from vendors other than the embedder's vendor (OpenAI): Google Gemini (gemini-4-argon-high) and xAI Grok (grok-4.7-high), run through the Cursor CLI in read-only ask mode, in an empty workspace. Each judge sees one question per call, with candidates in a different seeded random order and opaque ids; no ranks, sizes, document ids, question ids or category names are shown. Candidates are judged independently; judges never see each other's output.
- Controls inside every call: 1 random document (expected no), 1 near-miss document (top-ranked document of a different question of the same first source type; expected no), and, when the question has two or more gold documents, 1 other gold document as a positive control (expected full or partial).
- Rubric: a candidate answers only if it is about the SAME subject (entity, record, account, ticket, region, date) as the question and its answer is consistent with the reference. Verdicts: full, partial, conflict (same subject, contradicts reference), no. A verbatim quote from the candidate is required for full, partial and conflict.
- Guardrails applied in code, not by the judge: (1) the quote must be a verbatim (whitespace- and case-normalized) substring of the candidate text that was shown, otherwise the verdict becomes `unsupported`; (2) `full` requires subject_match=true, otherwise it becomes `no_subject`; (3) responses must be valid JSON with exactly one entry per candidate id, otherwise the call is retried up to twice and then marked invalid; (4) candidates are truncated at 16,000 characters with a marker, and truncation is recorded; (5) all raw responses are stored.

## Calibration set (added before any judge call)
Only 2 of the 42 questions have a second gold document, which is too few positive controls. A calibration set is therefore added: the 28 other primary questions with two or more gold documents. For each, gold document 1 is the REFERENCE; candidates are up to 2 other gold documents (positive controls, expected full or partial), 1 random document and 1 near-miss document (expected no). The calibration set is used only to estimate each judge's sensitivity (full-or-partial on positive controls) and false-positive rate; it never enters K_both or K_either.

## Primary outcomes (decided now)
- K_both = number of the 42 questions with at least one candidate whose verdict is `full` (after guardrails) for BOTH judges. Credit = K_both/200; adjusted drop = 0.210 - credit.
- K_either = same with `full` for EITHER judge (liberal bound). 
- Per judge: false-positive rate on random and near-miss controls (with Wilson 95% intervals), sensitivity on positive controls, agreement (Cohen's kappa on full vs not full over all candidates).
- The paper will report K_both and K_either with the control rates, will compare them with the earlier single-judge value (13 questions), and will NOT rescale by judge sensitivity unless the calibration set shows sensitivity (full-or-partial) below 0.9 for a judge, in which case the rescaled value is reported separately and labeled as such.

## Interpretation rule (decided now)
- If K_both <= 3 (credit <= 0.015): label incompleteness explains at most about 7% of the drop under this audit.
- If K_both is between 4 and 8: it explains roughly 10-20%.
- If K_both >= 9: it explains at least 20%, and the abstract keeps a limitation statement of "a substantial part".
- Whatever the outcome, the audit is described as model-judged and not human relabeling.
