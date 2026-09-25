"""DDL for human + LLM study audit (unified evaluations + $2 LLM budget ledger)."""

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection

AUDIT_DDL = """
CREATE TABLE IF NOT EXISTS audit_samples (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    question_id VARCHAR(128) NOT NULL,
    corpus_scale_size INT NOT NULL,
    condition VARCHAR(32) NOT NULL,
    hit_at_10 BOOLEAN,
    rank INT,
    document_recall DOUBLE PRECISION,
    expected_doc_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
    retrieved_doc_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
    sample_source TEXT,
    priority VARCHAR(16),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (question_id, corpus_scale_size, condition)
);

CREATE TABLE IF NOT EXISTS study_evaluations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    eval_scope VARCHAR(32) NOT NULL DEFAULT 'retrieval_row',
    question_id VARCHAR(64),
    corpus_scale_size INT,
    condition VARCHAR(32),
    claim_key VARCHAR(128),
    evaluator_kind VARCHAR(16) NOT NULL,
    auditor_id VARCHAR(64) NOT NULL,
    label_correct VARCHAR(16),
    failure_mode VARCHAR(64),
    notes TEXT,
    status VARCHAR(32) NOT NULL DEFAULT 'pending',
    hit_at_10 BOOLEAN,
    rank INT,
    document_recall DOUBLE PRECISION,
    expected_doc_ids JSONB,
    retrieved_doc_ids JSONB,
    relevance_score DOUBLE PRECISION,
    reasoning_summary TEXT,
    model VARCHAR(100),
    prompt_version VARCHAR(32),
    latency_ms INT,
    cost_usd DECIMAL(10, 6),
    input_tokens INT,
    output_tokens INT,
    checklist_json JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_study_eval_row
ON study_evaluations (
    eval_scope,
    COALESCE(question_id, ''),
    COALESCE(corpus_scale_size, -1),
    COALESCE(condition, ''),
    COALESCE(claim_key, ''),
    evaluator_kind,
    auditor_id
);

CREATE INDEX IF NOT EXISTS idx_study_eval_q
ON study_evaluations (question_id, corpus_scale_size, condition);

CREATE INDEX IF NOT EXISTS idx_study_eval_auditor
ON study_evaluations (evaluator_kind, auditor_id, status);

CREATE TABLE IF NOT EXISTS audit_cost_ledger (
    id BIGSERIAL PRIMARY KEY,
    kind TEXT NOT NULL,
    model TEXT,
    input_tokens INT,
    output_tokens INT,
    cost_usd DOUBLE PRECISION NOT NULL,
    note TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_audit_cost_created ON audit_cost_ledger (created_at);
"""

PAPER_CHECKLIST_SEED = [
    {
        "claim_key": "hit_at_10_definition",
        "title": "Hit@10 = gold doc_id ∈ top-10 (set membership)",
        "detail": "Open Row audit → confirm badge “ID membership” matches auto Hit@10. Definition is NOT answer quality.",
        "category": "metrics",
    },
    {
        "claim_key": "scaling_fit_formula",
        "title": "Scaling-law numbers match CANONICAL_METRICS / fit JSON",
        "detail": "Compare abstract Hit@10 0.795→0.510 and fit ≈1.474−0.086 log N to artifacts/published/CANONICAL_METRICS.json and erb_full_primary200_to100k_fit.json.",
        "category": "formulas",
    },
    {
        "claim_key": "raw_vs_meta_delta",
        "title": "Δmeta table matches published ladder",
        "detail": "In papers/ieee-vector-drift/access/main.pdf Table Δmeta: +0.080 at 5k, +0.130 at 100k; no N★. Cross-check INTEGRITY_IMPACT.md.",
        "category": "claims",
    },
    {
        "claim_key": "figures_match_data",
        "title": "Figures match underlying sweep",
        "detail": "Fig.1–3 in main.pdf: Hit@10 vs log N, Δmeta vs τ=0.10, Hit@1/MRR erosion. Spot-check 5k and 100k endpoints.",
        "category": "figures",
    },
    {
        "claim_key": "chunk_quality_spotcheck",
        "title": "Read gold + retrieved chunk text (≥5 rows)",
        "detail": "Use Row audit High-priority filter. Confirm gold text answers the question; note empty/wrong bodies.",
        "category": "chunks",
    },
    {
        "claim_key": "l4_human_audit_complete",
        "title": "L4 human audit ≥40 labeled rows (prefer 62 high)",
        "detail": "Queue: human_review_queue_openai.csv. Label in UI; Export CSV when done; replace Methods TBD.",
        "category": "audit",
    },
    {
        "claim_key": "l4_second_auditor",
        "title": "Second auditor overlap (optional)",
        "detail": "Change Auditor ID; label ≥10 overlapping rows; compare in Export.",
        "category": "audit",
    },
    {
        "claim_key": "llm_assist_budget",
        "title": "LLM triage is secondary only",
        "detail": "OpenAI L3 report is triage; humans override. Do not cite quarantined Ollama report.",
        "category": "llm",
    },
    {
        "claim_key": "failure_mode_paragraph",
        "title": "Failure-mode paragraph for paper",
        "detail": "After ≥40 labels, Export → markdown blurb; paste into access/main.tex Methods L4 TBD.",
        "category": "paper",
    },
    {
        "claim_key": "ai_disclosure_orcid",
        "title": "ORCID, AI disclosure, bio photo",
        "detail": "Confirm ORCID footnote, Acknowledgment AI sentence, author.jpg on last page of main.pdf.",
        "category": "paper",
    },
]


async def ensure_audit_schema(conn: AsyncConnection) -> None:
    for stmt in AUDIT_DDL.split(";"):
        s = stmt.strip()
        if s:
            await conn.execute(text(s))
    # Forward-compatible columns for older DBs
    await conn.execute(
        text("ALTER TABLE audit_samples ADD COLUMN IF NOT EXISTS priority VARCHAR(16)")
    )
    await conn.execute(
        text("ALTER TABLE audit_samples ALTER COLUMN question_id TYPE VARCHAR(128)")
    )
