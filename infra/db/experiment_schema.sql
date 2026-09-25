-- Experiment tracking schema for log-scale corpus runs and multi-model LLM evaluations.

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE IF NOT EXISTS experiment_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_name VARCHAR(255) NOT NULL,
    corpus_scale_size INT NOT NULL,
    embedding_model VARCHAR(100) NOT NULL,
    vector_index_type VARCHAR(100) NOT NULL,
    status VARCHAR(50) DEFAULT 'COMPLETED',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS vector_drift_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    experiment_run_id UUID REFERENCES experiment_runs(id) ON DELETE CASCADE,
    question_id VARCHAR(50) NOT NULL,
    target_db_id INT NOT NULL,
    retrieved_rank INT,
    cosine_similarity FLOAT,
    euclidean_distance FLOAT,
    mrr_score FLOAT,
    recall_at_1 BOOLEAN,
    recall_at_5 BOOLEAN,
    recall_at_10 BOOLEAN,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS llm_eval_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    experiment_run_id UUID REFERENCES experiment_runs(id) ON DELETE CASCADE,
    question_id VARCHAR(50) NOT NULL,
    evaluator_model VARCHAR(100) NOT NULL,
    faithfulness_score FLOAT,
    answer_relevance_score FLOAT,
    context_recall_score FLOAT,
    context_precision_score FLOAT,
    latency_ms INT,
    cost_usd DECIMAL(10, 6),
    reasoning_summary TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_experiment_runs_scale ON experiment_runs (corpus_scale_size);
CREATE INDEX IF NOT EXISTS idx_vector_drift_run ON vector_drift_results (experiment_run_id);
CREATE INDEX IF NOT EXISTS idx_llm_eval_run ON llm_eval_results (experiment_run_id);
