-- ============================================================
-- PROYECTO PRODUCTIVO IIIA
-- Vista final de cartera para Streamlit / Power BI
-- Usa el scoring mas reciente por cliente y los atributos Gold.
-- ============================================================

CREATE INDEX IF NOT EXISTS idx_score_output_id_fecha
    ON gold.score_output(id, fecha_score DESC, score_output_id DESC);

CREATE OR REPLACE VIEW gold.vw_portfolio_scoring_current AS
WITH latest_score AS (
    SELECT DISTINCT ON (so.id)
        so.score_output_id,
        so.score_input_id,
        so.id,
        so.fecha_score,
        so.modelo_version,
        so.probability_default,
        so.prediction,
        so.risk_level,
        so.recommendation,
        so.explanation
    FROM gold.score_output so
    ORDER BY so.id, so.fecha_score DESC, so.score_output_id DESC
)
SELECT
    s.score_output_id,
    s.score_input_id,
    s.id,
    s.fecha_score,
    s.modelo_version,
    s.probability_default,
    s.prediction,
    s.risk_level,
    s.recommendation,
    g.limit_bal,
    g.sex,
    g.education,
    g.marriage,
    g.age,
    g.pay_0,
    g.pay_max_delay,
    g.recent_delay_months,
    g.consecutive_delay_months,
    g.bill_avg,
    g.pay_amt_avg,
    g.payment_bill_ratio_total
FROM latest_score s
JOIN gold.gold_ml g
  ON g.id = s.id;

COMMENT ON VIEW gold.vw_portfolio_scoring_current IS
    'Vista de consumo con el scoring mas reciente por cliente para Streamlit y Power BI.';
