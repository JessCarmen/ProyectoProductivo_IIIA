-- ============================================================
-- PROYECTO PRODUCTIVO IIIA - V2
-- Prioridades 1, 2 y 3
-- ============================================================
-- 1) Propagar source_parent_id a Gold para split por grupo.
-- 2) Mantener trazabilidad del origen de cada registro.
-- 3) Relacionar score_output con score_input para cerrar el flujo.
-- ============================================================

ALTER TABLE gold.dim_cliente
    ADD COLUMN IF NOT EXISTS source_parent_id VARCHAR(150);

ALTER TABLE gold.fact_comportamiento_crediticio
    ADD COLUMN IF NOT EXISTS source_parent_id VARCHAR(150);

ALTER TABLE gold.gold_ml
    ADD COLUMN IF NOT EXISTS source_parent_id VARCHAR(150);

-- Propagar el lineage desde Silver/Gold usando bronze_id cuando existe.
UPDATE gold.dim_cliente d
SET source_parent_id = b.source_parent_id
FROM bronze.raw_credit_card_clients b
WHERE d.bronze_id = b.bronze_id
  AND (d.source_parent_id IS NULL OR d.source_parent_id <> b.source_parent_id);

UPDATE gold.fact_comportamiento_crediticio f
SET source_parent_id = d.source_parent_id
FROM gold.dim_cliente d
WHERE f.cliente_key = d.cliente_key
  AND (f.source_parent_id IS NULL OR f.source_parent_id <> d.source_parent_id);

UPDATE gold.gold_ml m
SET source_parent_id = d.source_parent_id
FROM gold.dim_cliente d
WHERE m.id = d.id
  AND (m.source_parent_id IS NULL OR m.source_parent_id <> d.source_parent_id);

CREATE INDEX IF NOT EXISTS idx_gold_ml_source_parent_id
    ON gold.gold_ml(source_parent_id);


-- ============================================================
-- PROCEDURE PARA REFRESCAR LINEAGE DESPUES DE RECONSTRUIR GOLD
-- ============================================================

CREATE OR REPLACE PROCEDURE gold.sp_refrescar_gold_lineage()
LANGUAGE plpgsql
AS $$
BEGIN
    UPDATE gold.dim_cliente d
    SET source_parent_id = b.source_parent_id
    FROM bronze.raw_credit_card_clients b
    WHERE d.bronze_id = b.bronze_id;

    UPDATE gold.fact_comportamiento_crediticio f
    SET source_parent_id = d.source_parent_id
    FROM gold.dim_cliente d
    WHERE f.cliente_key = d.cliente_key;

    UPDATE gold.gold_ml m
    SET source_parent_id = d.source_parent_id
    FROM gold.dim_cliente d
    WHERE m.id = d.id;
END;
$$;

-- ============================================================
-- SCORING: vincular cada salida con su entrada.
-- ============================================================

ALTER TABLE gold.score_output
    ADD COLUMN IF NOT EXISTS score_input_id BIGINT;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'fk_score_output_input'
    ) THEN
        ALTER TABLE gold.score_output
            ADD CONSTRAINT fk_score_output_input
            FOREIGN KEY (score_input_id)
            REFERENCES gold.score_input(score_input_id);
    END IF;
END $$;

CREATE UNIQUE INDEX IF NOT EXISTS ux_score_output_score_input_id
    ON gold.score_output(score_input_id)
    WHERE score_input_id IS NOT NULL;

COMMENT ON COLUMN gold.gold_ml.source_parent_id IS
    'ID del registro original del que deriva el cliente; se usa para evitar leakage entre train/validation/test.';

COMMENT ON COLUMN gold.score_output.score_input_id IS
    'Registro de entrada utilizado para generar el scoring.';
