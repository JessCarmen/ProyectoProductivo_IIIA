-- V3: estructuras aditivas, sin alterar el scoring histórico ni el modelo.
-- Requiere gold.scoring_human_reviews y gold.score_output existentes.
-- Una propuesta del analista NO constituye por sí sola un target verificado.

CREATE TABLE IF NOT EXISTS gold.scoring_review_decisions (
    decision_id BIGSERIAL PRIMARY KEY,
    review_id BIGINT NOT NULL UNIQUE
        REFERENCES gold.scoring_human_reviews(review_id) ON DELETE RESTRICT,
    decision_status VARCHAR(20) NOT NULL
        CHECK (decision_status IN ('APROBADA', 'RECHAZADA')),
    supervisor_id VARCHAR(80) NOT NULL CHECK (length(trim(supervisor_id)) >= 3),
    decision_note TEXT NOT NULL CHECK (length(trim(decision_note)) >= 20),
    decided_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS gold.credit_outcomes_verified (
    outcome_id BIGSERIAL PRIMARY KEY,
    score_output_id BIGINT NOT NULL
        REFERENCES gold.score_output(score_output_id) ON DELETE RESTRICT,
    observation_end_date DATE NOT NULL,
    actual_default SMALLINT NOT NULL CHECK (actual_default IN (0, 1)),
    evidence_reference VARCHAR(200) NOT NULL
        CHECK (length(trim(evidence_reference)) >= 3),
    verified_by VARCHAR(80) NOT NULL CHECK (length(trim(verified_by)) >= 3),
    verified_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (score_output_id, observation_end_date)
);

CREATE TABLE IF NOT EXISTS gold.model_training_runs (
    run_id BIGSERIAL PRIMARY KEY,
    model_version VARCHAR(100) NOT NULL UNIQUE,
    base_model_version VARCHAR(100),
    run_status VARCHAR(30) NOT NULL
        CHECK (run_status IN ('CANDIDATO','EVALUADO','RECHAZADO','APROBADO')),
    metrics JSONB,
    fairness_metrics JSONB,
    artifact_path TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_credit_outcomes_score
    ON gold.credit_outcomes_verified(score_output_id);
CREATE INDEX IF NOT EXISTS idx_review_decisions_status
    ON gold.scoring_review_decisions(decision_status);

-- Vista informativa: NO crea etiquetas a partir de la opinión humana.
-- La etiqueta viene únicamente del resultado observado y verificado.
CREATE OR REPLACE VIEW gold.vw_verified_retraining_cases AS
SELECT
    r.review_id,
    r.customer_id,
    r.score_output_id,
    r.model_version,
    r.model_prediction,
    r.proposed_prediction,
    d.decision_status,
    o.actual_default,
    o.observation_end_date,
    o.outcome_id,
    o.verified_at
FROM gold.scoring_human_reviews AS r
JOIN gold.scoring_review_decisions AS d
    ON d.review_id = r.review_id AND d.decision_status = 'APROBADA'
JOIN gold.credit_outcomes_verified AS o
    ON o.score_output_id = r.score_output_id;

-- Los objetos de validación no deben exponerse directamente a roles públicos.
REVOKE ALL ON TABLE
    gold.scoring_review_decisions,
    gold.credit_outcomes_verified,
    gold.model_training_runs
FROM PUBLIC, anon, authenticated;

REVOKE ALL ON TABLE gold.vw_verified_retraining_cases
FROM PUBLIC, anon, authenticated;

REVOKE ALL ON SEQUENCE
    gold.scoring_review_decisions_decision_id_seq,
    gold.credit_outcomes_verified_outcome_id_seq,
    gold.model_training_runs_run_id_seq
FROM PUBLIC, anon, authenticated;
