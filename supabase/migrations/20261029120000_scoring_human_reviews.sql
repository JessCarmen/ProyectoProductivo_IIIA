-- Proyecto Productivo IIIA - revision humana del scoring
-- ADITIVO: no modifica gold.score_output ni gold.gold_ml.
CREATE TABLE IF NOT EXISTS gold.scoring_human_reviews (
    review_id BIGSERIAL PRIMARY KEY,
    score_output_id BIGINT NOT NULL REFERENCES gold.score_output(score_output_id) ON DELETE RESTRICT,
    customer_id BIGINT NOT NULL,
    model_version VARCHAR(80),
    model_probability NUMERIC(8,6) NOT NULL CHECK (model_probability BETWEEN 0 AND 1),
    model_prediction INTEGER NOT NULL CHECK (model_prediction IN (0,1)),
    review_status VARCHAR(30) NOT NULL CHECK (review_status IN ('CONFIRMADO','OBSERVADO','CORRECCION_PROPUESTA')),
    proposed_prediction INTEGER CHECK (proposed_prediction IN (0,1)),
    reviewer_id VARCHAR(80) NOT NULL CHECK (length(trim(reviewer_id)) >= 3),
    evidence_type VARCHAR(40) NOT NULL CHECK (evidence_type IN ('HISTORIAL_PAGOS','INGRESOS_VERIFICADOS','OBLIGACIONES','DATOS_INCORRECTOS','OTRO')),
    evidence_reference VARCHAR(160),
    review_note VARCHAR(500) NOT NULL CHECK (length(trim(review_note)) >= 20),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT review_correction_requires_evidence CHECK (
        (review_status = 'CORRECCION_PROPUESTA'
          AND proposed_prediction IS NOT NULL
          AND proposed_prediction <> model_prediction
          AND evidence_reference IS NOT NULL
          AND length(trim(evidence_reference)) >= 3)
        OR
        (review_status <> 'CORRECCION_PROPUESTA' AND proposed_prediction IS NULL)
    )
);

CREATE INDEX IF NOT EXISTS idx_scoring_reviews_customer_date
    ON gold.scoring_human_reviews(customer_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_scoring_reviews_score_output
    ON gold.scoring_human_reviews(score_output_id);

-- Solo el backend conectado con rol autorizado debe acceder a las revisiones.
REVOKE ALL ON TABLE gold.scoring_human_reviews FROM PUBLIC, anon, authenticated;
REVOKE ALL ON SEQUENCE gold.scoring_human_reviews_review_id_seq FROM PUBLIC, anon, authenticated;
COMMENT ON TABLE gold.scoring_human_reviews IS
'Revisiones humanas append-only. No cambian la prediccion original ni constituyen por si solas una etiqueta real de incumplimiento.';
