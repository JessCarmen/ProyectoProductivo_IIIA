-- ============================================================
-- PROYECTO PRODUCTIVO IIIA
-- FIX GOLD_ML / FEATURE ENGINEERING
-- Fecha: 2026-09-28
--
-- Objetivos:
-- 1. Mantener intactos RAW y BRONZE.
-- 2. Mantener las features actuales para trazabilidad.
-- 3. Incorporar agregaciones robustas de pago/facturación.
-- 4. Evitar que un BILL_AMT mensual muy pequeño domine el ratio.
-- 5. Hacer explícita la semántica de los NULL de algunas features.
-- 6. Reconstruir GOLD_ML desde GOLD.
-- ============================================================

-- ------------------------------------------------------------
-- 1. NUEVAS FEATURES ROBUSTAS
-- ------------------------------------------------------------

ALTER TABLE gold.gold_ml
    ADD COLUMN IF NOT EXISTS bill_positive_total NUMERIC(18,2),
    ADD COLUMN IF NOT EXISTS pay_amt_total NUMERIC(18,2),
    ADD COLUMN IF NOT EXISTS payment_bill_positive_months INTEGER,
    ADD COLUMN IF NOT EXISTS payment_bill_ratio_total NUMERIC(18,8);


-- ------------------------------------------------------------
-- 2. PROCEDURE GOLD_ML
-- ------------------------------------------------------------

CREATE OR REPLACE PROCEDURE gold.sp_construir_gold_ml()
LANGUAGE plpgsql
AS $$
BEGIN

    TRUNCATE TABLE gold.gold_ml RESTART IDENTITY;

    INSERT INTO gold.gold_ml (
        id,
        target_default,

        limit_bal,
        sex,
        education,
        marriage,
        age,

        pay_0,
        pay_2,
        pay_3,
        pay_4,
        pay_5,
        pay_6,

        pay_max_delay,
        pay_avg_delay_positive,
        pay_positive_months,
        pay_on_time_months,
        pay_duly_paid_months,
        pay_no_activity_months,
        pay_negative_code_months,

        bill_amt1,
        bill_amt2,
        bill_amt3,
        bill_amt4,
        bill_amt5,
        bill_amt6,

        bill_avg,
        bill_max,
        bill_min,
        bill_std,
        bill_negative_months,
        bill_zero_months,
        bill_positive_months,
        bill_positive_total,

        pay_amt1,
        pay_amt2,
        pay_amt3,
        pay_amt4,
        pay_amt5,
        pay_amt6,

        pay_amt_avg,
        pay_amt_max,
        pay_amt_min,
        pay_amt_total,

        payment_bill_ratio_avg,
        payment_bill_ratio_max,
        payment_bill_ratio_total,
        payment_bill_positive_months,

        high_delay_months,
        recent_delay_months,
        consecutive_delay_months
    )
    SELECT
        d.id,
        f.default_payment_next_month,

        d.limit_bal,
        d.sex,
        d.education,
        d.marriage,
        d.age,

        f.pay_0,
        f.pay_2,
        f.pay_3,
        f.pay_4,
        f.pay_5,
        f.pay_6,

        -- ====================================================
        -- PAY: comportamiento de atraso
        -- ====================================================

        GREATEST(
            f.pay_0,
            f.pay_2,
            f.pay_3,
            f.pay_4,
            f.pay_5,
            f.pay_6
        ) AS pay_max_delay,

        (
            SELECT AVG(x::NUMERIC)
            FROM unnest(ARRAY[
                f.pay_0,
                f.pay_2,
                f.pay_3,
                f.pay_4,
                f.pay_5,
                f.pay_6
            ]) AS u(x)
            WHERE x > 0
        ) AS pay_avg_delay_positive,

        (
            CASE WHEN f.pay_0 > 0 THEN 1 ELSE 0 END +
            CASE WHEN f.pay_2 > 0 THEN 1 ELSE 0 END +
            CASE WHEN f.pay_3 > 0 THEN 1 ELSE 0 END +
            CASE WHEN f.pay_4 > 0 THEN 1 ELSE 0 END +
            CASE WHEN f.pay_5 > 0 THEN 1 ELSE 0 END +
            CASE WHEN f.pay_6 > 0 THEN 1 ELSE 0 END
        ) AS pay_positive_months,

        (
            CASE WHEN f.pay_0 = 0 THEN 1 ELSE 0 END +
            CASE WHEN f.pay_2 = 0 THEN 1 ELSE 0 END +
            CASE WHEN f.pay_3 = 0 THEN 1 ELSE 0 END +
            CASE WHEN f.pay_4 = 0 THEN 1 ELSE 0 END +
            CASE WHEN f.pay_5 = 0 THEN 1 ELSE 0 END +
            CASE WHEN f.pay_6 = 0 THEN 1 ELSE 0 END
        ) AS pay_on_time_months,

        (
            CASE WHEN f.pay_0 = -1 THEN 1 ELSE 0 END +
            CASE WHEN f.pay_2 = -1 THEN 1 ELSE 0 END +
            CASE WHEN f.pay_3 = -1 THEN 1 ELSE 0 END +
            CASE WHEN f.pay_4 = -1 THEN 1 ELSE 0 END +
            CASE WHEN f.pay_5 = -1 THEN 1 ELSE 0 END +
            CASE WHEN f.pay_6 = -1 THEN 1 ELSE 0 END
        ) AS pay_duly_paid_months,

        (
            CASE WHEN f.pay_0 = -2 THEN 1 ELSE 0 END +
            CASE WHEN f.pay_2 = -2 THEN 1 ELSE 0 END +
            CASE WHEN f.pay_3 = -2 THEN 1 ELSE 0 END +
            CASE WHEN f.pay_4 = -2 THEN 1 ELSE 0 END +
            CASE WHEN f.pay_5 = -2 THEN 1 ELSE 0 END +
            CASE WHEN f.pay_6 = -2 THEN 1 ELSE 0 END
        ) AS pay_no_activity_months,

        (
            CASE WHEN f.pay_0 < 0 THEN 1 ELSE 0 END +
            CASE WHEN f.pay_2 < 0 THEN 1 ELSE 0 END +
            CASE WHEN f.pay_3 < 0 THEN 1 ELSE 0 END +
            CASE WHEN f.pay_4 < 0 THEN 1 ELSE 0 END +
            CASE WHEN f.pay_5 < 0 THEN 1 ELSE 0 END +
            CASE WHEN f.pay_6 < 0 THEN 1 ELSE 0 END
        ) AS pay_negative_code_months,

        -- ====================================================
        -- BILL
        -- ====================================================

        f.bill_amt1,
        f.bill_amt2,
        f.bill_amt3,
        f.bill_amt4,
        f.bill_amt5,
        f.bill_amt6,

        (
            SELECT AVG(x::NUMERIC)
            FROM unnest(ARRAY[
                f.bill_amt1,
                f.bill_amt2,
                f.bill_amt3,
                f.bill_amt4,
                f.bill_amt5,
                f.bill_amt6
            ]) AS u(x)
        ) AS bill_avg,

        GREATEST(
            f.bill_amt1,
            f.bill_amt2,
            f.bill_amt3,
            f.bill_amt4,
            f.bill_amt5,
            f.bill_amt6
        ) AS bill_max,

        LEAST(
            f.bill_amt1,
            f.bill_amt2,
            f.bill_amt3,
            f.bill_amt4,
            f.bill_amt5,
            f.bill_amt6
        ) AS bill_min,

        (
            SELECT STDDEV_POP(x::NUMERIC)
            FROM unnest(ARRAY[
                f.bill_amt1,
                f.bill_amt2,
                f.bill_amt3,
                f.bill_amt4,
                f.bill_amt5,
                f.bill_amt6
            ]) AS u(x)
        ) AS bill_std,

        (
            SELECT COUNT(*)
            FROM unnest(ARRAY[
                f.bill_amt1,
                f.bill_amt2,
                f.bill_amt3,
                f.bill_amt4,
                f.bill_amt5,
                f.bill_amt6
            ]) AS u(x)
            WHERE x < 0
        ) AS bill_negative_months,

        (
            SELECT COUNT(*)
            FROM unnest(ARRAY[
                f.bill_amt1,
                f.bill_amt2,
                f.bill_amt3,
                f.bill_amt4,
                f.bill_amt5,
                f.bill_amt6
            ]) AS u(x)
            WHERE x = 0
        ) AS bill_zero_months,

        (
            SELECT COUNT(*)
            FROM unnest(ARRAY[
                f.bill_amt1,
                f.bill_amt2,
                f.bill_amt3,
                f.bill_amt4,
                f.bill_amt5,
                f.bill_amt6
            ]) AS u(x)
            WHERE x > 0
        ) AS bill_positive_months,

        COALESCE((
            SELECT SUM(x::NUMERIC)
            FROM unnest(ARRAY[
                f.bill_amt1,
                f.bill_amt2,
                f.bill_amt3,
                f.bill_amt4,
                f.bill_amt5,
                f.bill_amt6
            ]) AS u(x)
            WHERE x > 0
        ), 0) AS bill_positive_total,

        -- ====================================================
        -- PAY AMT
        -- ====================================================

        f.pay_amt1,
        f.pay_amt2,
        f.pay_amt3,
        f.pay_amt4,
        f.pay_amt5,
        f.pay_amt6,

        (
            SELECT AVG(x::NUMERIC)
            FROM unnest(ARRAY[
                f.pay_amt1,
                f.pay_amt2,
                f.pay_amt3,
                f.pay_amt4,
                f.pay_amt5,
                f.pay_amt6
            ]) AS u(x)
        ) AS pay_amt_avg,

        GREATEST(
            f.pay_amt1,
            f.pay_amt2,
            f.pay_amt3,
            f.pay_amt4,
            f.pay_amt5,
            f.pay_amt6
        ) AS pay_amt_max,

        LEAST(
            f.pay_amt1,
            f.pay_amt2,
            f.pay_amt3,
            f.pay_amt4,
            f.pay_amt5,
            f.pay_amt6
        ) AS pay_amt_min,

        COALESCE((
            SELECT SUM(x::NUMERIC)
            FROM unnest(ARRAY[
                f.pay_amt1,
                f.pay_amt2,
                f.pay_amt3,
                f.pay_amt4,
                f.pay_amt5,
                f.pay_amt6
            ]) AS u(x)
        ), 0) AS pay_amt_total,

        -- ====================================================
        -- RATIOS
        --
        -- AVG/MAX se conservan para trazabilidad y análisis.
        -- NO deben ser usadas como variables principales del
        -- modelo debido a su sensibilidad a BILL_AMT pequeño.
        --
        -- El nuevo ratio_total usa únicamente meses con
        -- BILL_AMT > 0 y agrega primero los importes.
        -- ====================================================

        (
            SELECT AVG(p::NUMERIC / NULLIF(b::NUMERIC, 0))
            FROM unnest(
                ARRAY[
                    f.bill_amt1,
                    f.bill_amt2,
                    f.bill_amt3,
                    f.bill_amt4,
                    f.bill_amt5,
                    f.bill_amt6
                ],
                ARRAY[
                    f.pay_amt1,
                    f.pay_amt2,
                    f.pay_amt3,
                    f.pay_amt4,
                    f.pay_amt5,
                    f.pay_amt6
                ]
            ) AS u(b, p)
            WHERE b > 0
              AND p IS NOT NULL
        ) AS payment_bill_ratio_avg,

        (
            SELECT MAX(p::NUMERIC / NULLIF(b::NUMERIC, 0))
            FROM unnest(
                ARRAY[
                    f.bill_amt1,
                    f.bill_amt2,
                    f.bill_amt3,
                    f.bill_amt4,
                    f.bill_amt5,
                    f.bill_amt6
                ],
                ARRAY[
                    f.pay_amt1,
                    f.pay_amt2,
                    f.pay_amt3,
                    f.pay_amt4,
                    f.pay_amt5,
                    f.pay_amt6
                ]
            ) AS u(b, p)
            WHERE b > 0
              AND p IS NOT NULL
        ) AS payment_bill_ratio_max,

        (
            SELECT
                SUM(p::NUMERIC) / NULLIF(SUM(b::NUMERIC), 0)
            FROM unnest(
                ARRAY[
                    f.bill_amt1,
                    f.bill_amt2,
                    f.bill_amt3,
                    f.bill_amt4,
                    f.bill_amt5,
                    f.bill_amt6
                ],
                ARRAY[
                    f.pay_amt1,
                    f.pay_amt2,
                    f.pay_amt3,
                    f.pay_amt4,
                    f.pay_amt5,
                    f.pay_amt6
                ]
            ) AS u(b, p)
            WHERE b > 0
              AND p IS NOT NULL
        ) AS payment_bill_ratio_total,

        (
            SELECT COUNT(*)
            FROM unnest(
                ARRAY[
                    f.bill_amt1,
                    f.bill_amt2,
                    f.bill_amt3,
                    f.bill_amt4,
                    f.bill_amt5,
                    f.bill_amt6
                ],
                ARRAY[
                    f.pay_amt1,
                    f.pay_amt2,
                    f.pay_amt3,
                    f.pay_amt4,
                    f.pay_amt5,
                    f.pay_amt6
                ]
            ) AS u(b, p)
            WHERE b > 0
              AND p IS NOT NULL
        ) AS payment_bill_positive_months,

        -- ====================================================
        -- ATRASOS
        -- ====================================================

        (
            CASE WHEN f.pay_0 >= 2 THEN 1 ELSE 0 END +
            CASE WHEN f.pay_2 >= 2 THEN 1 ELSE 0 END +
            CASE WHEN f.pay_3 >= 2 THEN 1 ELSE 0 END +
            CASE WHEN f.pay_4 >= 2 THEN 1 ELSE 0 END +
            CASE WHEN f.pay_5 >= 2 THEN 1 ELSE 0 END +
            CASE WHEN f.pay_6 >= 2 THEN 1 ELSE 0 END
        ) AS high_delay_months,

        (
            CASE WHEN f.pay_0 > 0 THEN 1 ELSE 0 END +
            CASE WHEN f.pay_2 > 0 THEN 1 ELSE 0 END +
            CASE WHEN f.pay_3 > 0 THEN 1 ELSE 0 END
        ) AS recent_delay_months,

        CASE
            WHEN f.pay_0 IS NULL OR f.pay_0 <= 0 THEN 0
            WHEN f.pay_2 IS NULL OR f.pay_2 <= 0 THEN 1
            WHEN f.pay_3 IS NULL OR f.pay_3 <= 0 THEN 2
            WHEN f.pay_4 IS NULL OR f.pay_4 <= 0 THEN 3
            WHEN f.pay_5 IS NULL OR f.pay_5 <= 0 THEN 4
            WHEN f.pay_6 IS NULL OR f.pay_6 <= 0 THEN 5
            ELSE 6
        END AS consecutive_delay_months

    FROM gold.dim_cliente d
    INNER JOIN gold.fact_comportamiento_crediticio f
        ON d.cliente_key = f.cliente_key;

END;
$$;


-- ============================================================
-- 3. COMENTARIOS DE TRAZABILIDAD
-- ============================================================

COMMENT ON COLUMN gold.gold_ml.payment_bill_ratio_avg IS
'Ratio promedio mensual PAY_AMT/BILL_AMT para meses con BILL_AMT > 0. Se conserva para análisis; sensible a facturas muy pequeñas y no recomendado como feature principal del modelo.';

COMMENT ON COLUMN gold.gold_ml.payment_bill_ratio_max IS
'Máximo ratio mensual PAY_AMT/BILL_AMT para meses con BILL_AMT > 0. Se conserva como variable diagnóstica; sensible a denominadores muy pequeños y no recomendado como feature principal del modelo.';

COMMENT ON COLUMN gold.gold_ml.payment_bill_ratio_total IS
'Ratio agregado: suma de PAY_AMT de meses con BILL_AMT > 0 dividida entre suma de BILL_AMT positivo de esos mismos meses. Feature principal recomendada para relación pago/facturación.';

COMMENT ON COLUMN gold.gold_ml.payment_bill_positive_months IS
'Cantidad de meses con BILL_AMT > 0 y PAY_AMT disponible, utilizada para interpretar payment_bill_ratio_total.';

COMMENT ON COLUMN gold.gold_ml.bill_positive_total IS
'Suma de BILL_AMT positivos de los seis meses. Los BILL_AMT negativos y cero no participan en esta agregación y permanecen intactos en las columnas originales.';

COMMENT ON COLUMN gold.gold_ml.pay_amt_total IS
'Suma de PAY_AMT de los seis meses.';

END;
