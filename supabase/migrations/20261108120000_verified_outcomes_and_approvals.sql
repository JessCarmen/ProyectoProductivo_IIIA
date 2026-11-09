-- NexaRisk V3: concilia la migracion con las tablas YA existentes.
-- No elimina datos, no recrea tablas y no modifica score_output.
-- Esquema comprobado por consulta a information_schema del usuario.

DO $$
DECLARE
  missing text;
BEGIN
  SELECT string_agg(t.object_name || '.' || t.column_name, ', ')
  INTO missing
  FROM (VALUES
    ('scoring_human_reviews','review_id'),
    ('scoring_human_reviews','customer_id'),
    ('scoring_human_reviews','score_output_id'),
    ('scoring_human_reviews','model_version'),
    ('scoring_human_reviews','model_prediction'),
    ('scoring_human_reviews','proposed_prediction'),
    ('scoring_review_decisions','review_id'),
    ('scoring_review_decisions','decision'),
    ('credit_outcomes_verified','outcome_id'),
    ('credit_outcomes_verified','customer_id'),
    ('credit_outcomes_verified','score_output_id'),
    ('credit_outcomes_verified','observed_default'),
    ('credit_outcomes_verified','observation_start'),
    ('credit_outcomes_verified','observation_end'),
    ('credit_outcomes_verified','verified_at'),
    ('model_training_runs','version'),
    ('model_training_runs','status')
  ) AS t(object_name,column_name)
  WHERE NOT EXISTS (
    SELECT 1 FROM information_schema.columns c
    WHERE c.table_schema = 'gold'
      AND c.table_name = t.object_name
      AND c.column_name = t.column_name
  );

  IF missing IS NOT NULL THEN
    RAISE EXCEPTION 'Estructura V3 no coincide. Columnas ausentes: %', missing;
  END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_credit_outcomes_score
    ON gold.credit_outcomes_verified(score_output_id);

CREATE INDEX IF NOT EXISTS idx_review_decisions_status
    ON gold.scoring_review_decisions(decision);

-- La vista gold.vw_verified_retraining_cases YA existe en la base remota.
-- Se conserva su definicion y el orden original de sus 12 columnas.
-- No usamos CREATE OR REPLACE VIEW para evitar romper dependencias.
DO $$
BEGIN
  IF to_regclass('gold.vw_verified_retraining_cases') IS NULL THEN
    RAISE EXCEPTION 'Falta gold.vw_verified_retraining_cases: verificar esquema antes de continuar';
  END IF;
END $$;

REVOKE ALL ON TABLE
    gold.scoring_review_decisions,
    gold.credit_outcomes_verified,
    gold.model_training_runs
FROM PUBLIC, anon, authenticated;

REVOKE ALL ON TABLE gold.vw_verified_retraining_cases
FROM PUBLIC, anon, authenticated;

COMMENT ON VIEW gold.vw_verified_retraining_cases IS
'Casos con revision aprobada y resultado observado vinculado. Requiere validacion adicional antes del reentrenamiento.';
