-- ============================================================
-- PROYECTO PRODUCTIVO IIIA
-- GOLD_ML - FEATURE ENGINEERING
-- ============================================================

-- ============================================================
-- 1. AGREGAR FEATURES A GOLD_ML
-- ============================================================

ALTER TABLE gold.gold_ml

ADD COLUMN IF NOT EXISTS pay_max_delay INTEGER,

ADD COLUMN IF NOT EXISTS pay_avg_delay_positive NUMERIC(10,4),

ADD COLUMN IF NOT EXISTS pay_positive_months INTEGER,

ADD COLUMN IF NOT EXISTS pay_on_time_months INTEGER,

ADD COLUMN IF NOT EXISTS pay_duly_paid_months INTEGER,

ADD COLUMN IF NOT EXISTS pay_no_activity_months INTEGER,

ADD COLUMN IF NOT EXISTS pay_negative_code_months INTEGER,

ADD COLUMN IF NOT EXISTS bill_avg NUMERIC(15,2),

ADD COLUMN IF NOT EXISTS bill_max NUMERIC(15,2),

ADD COLUMN IF NOT EXISTS bill_min NUMERIC(15,2),

ADD COLUMN IF NOT EXISTS bill_std NUMERIC(15,2),

ADD COLUMN IF NOT EXISTS bill_negative_months INTEGER,

ADD COLUMN IF NOT EXISTS bill_zero_months INTEGER,

ADD COLUMN IF NOT EXISTS bill_positive_months INTEGER,

ADD COLUMN IF NOT EXISTS pay_amt_avg NUMERIC(15,2),

ADD COLUMN IF NOT EXISTS pay_amt_max NUMERIC(15,2),

ADD COLUMN IF NOT EXISTS pay_amt_min NUMERIC(15,2),

ADD COLUMN IF NOT EXISTS payment_bill_ratio_avg NUMERIC(15,6),

ADD COLUMN IF NOT EXISTS payment_bill_ratio_max NUMERIC(15,6),

ADD COLUMN IF NOT EXISTS high_delay_months INTEGER,

ADD COLUMN IF NOT EXISTS recent_delay_months INTEGER,

ADD COLUMN IF NOT EXISTS consecutive_delay_months INTEGER;


-- ============================================================
-- 2. RECONSTRUIR GOLD_ML
-- ============================================================

CREATE OR REPLACE PROCEDURE gold.sp_construir_gold_ml()
LANGUAGE plpgsql
AS $$
BEGIN

    -- --------------------------------------------------------
    -- Limpiar GOLD_ML
    -- --------------------------------------------------------

    TRUNCATE TABLE gold.gold_ml RESTART IDENTITY;


    -- --------------------------------------------------------
    -- Cargar variables originales + features
    -- --------------------------------------------------------

    INSERT INTO gold.gold_ml (

        id,
        target_default,

        -- Cliente
        limit_bal,
        sex,
        education,
        marriage,
        age,

        -- PAY originales
        pay_0,
        pay_2,
        pay_3,
        pay_4,
        pay_5,
        pay_6,

        -- PAY features
        pay_max_delay,
        pay_avg_delay_positive,
        pay_positive_months,
        pay_on_time_months,
        pay_duly_paid_months,
        pay_no_activity_months,
        pay_negative_code_months,

        -- BILL originales
        bill_amt1,
        bill_amt2,
        bill_amt3,
        bill_amt4,
        bill_amt5,
        bill_amt6,

        -- BILL features
        bill_avg,
        bill_max,
        bill_min,
        bill_std,
        bill_negative_months,
        bill_zero_months,
        bill_positive_months,

        -- PAY_AMT originales
        pay_amt1,
        pay_amt2,
        pay_amt3,
        pay_amt4,
        pay_amt5,
        pay_amt6,

        -- PAY_AMT features
        pay_amt_avg,
        pay_amt_max,
        pay_amt_min,

        -- Ratios
        payment_bill_ratio_avg,
        payment_bill_ratio_max,

        -- Indicadores de atraso
        high_delay_months,
        recent_delay_months,
        consecutive_delay_months

    )

    SELECT

        d.id,

        f.default_payment_next_month,

        -- ====================================================
        -- CLIENTE
        -- ====================================================

        d.limit_bal,
        d.sex,
        d.education,
        d.marriage,
        d.age,

        -- ====================================================
        -- PAY ORIGINALES
        -- ====================================================

        f.pay_0,
        f.pay_2,
        f.pay_3,
        f.pay_4,
        f.pay_5,
        f.pay_6,

        -- ====================================================
        -- PAY FEATURES
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
            SELECT AVG(x)
            FROM unnest(
                ARRAY[
                    f.pay_0,
                    f.pay_2,
                    f.pay_3,
                    f.pay_4,
                    f.pay_5,
                    f.pay_6
                ]
            ) AS x
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
        -- BILL ORIGINALES
        -- ====================================================

        f.bill_amt1,
        f.bill_amt2,
        f.bill_amt3,
        f.bill_amt4,
        f.bill_amt5,
        f.bill_amt6,

        -- ====================================================
        -- BILL FEATURES
        -- ====================================================

        (
            f.bill_amt1 +
            f.bill_amt2 +
            f.bill_amt3 +
            f.bill_amt4 +
            f.bill_amt5 +
            f.bill_amt6
        ) / 6.0 AS bill_avg,

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
            SELECT STDDEV_POP(x)
            FROM unnest(
                ARRAY[
                    f.bill_amt1,
                    f.bill_amt2,
                    f.bill_amt3,
                    f.bill_amt4,
                    f.bill_amt5,
                    f.bill_amt6
                ]
            ) AS x
        ) AS bill_std,

        (
            CASE WHEN f.bill_amt1 < 0 THEN 1 ELSE 0 END +
            CASE WHEN f.bill_amt2 < 0 THEN 1 ELSE 0 END +
            CASE WHEN f.bill_amt3 < 0 THEN 1 ELSE 0 END +
            CASE WHEN f.bill_amt4 < 0 THEN 1 ELSE 0 END +
            CASE WHEN f.bill_amt5 < 0 THEN 1 ELSE 0 END +
            CASE WHEN f.bill_amt6 < 0 THEN 1 ELSE 0 END
        ) AS bill_negative_months,

        (
            CASE WHEN f.bill_amt1 = 0 THEN 1 ELSE 0 END +
            CASE WHEN f.bill_amt2 = 0 THEN 1 ELSE 0 END +
            CASE WHEN f.bill_amt3 = 0 THEN 1 ELSE 0 END +
            CASE WHEN f.bill_amt4 = 0 THEN 1 ELSE 0 END +
            CASE WHEN f.bill_amt5 = 0 THEN 1 ELSE 0 END +
            CASE WHEN f.bill_amt6 = 0 THEN 1 ELSE 0 END
        ) AS bill_zero_months,

        (
            CASE WHEN f.bill_amt1 > 0 THEN 1 ELSE 0 END +
            CASE WHEN f.bill_amt2 > 0 THEN 1 ELSE 0 END +
            CASE WHEN f.bill_amt3 > 0 THEN 1 ELSE 0 END +
            CASE WHEN f.bill_amt4 > 0 THEN 1 ELSE 0 END +
            CASE WHEN f.bill_amt5 > 0 THEN 1 ELSE 0 END +
            CASE WHEN f.bill_amt6 > 0 THEN 1 ELSE 0 END
        ) AS bill_positive_months,

        -- ====================================================
        -- PAY_AMT ORIGINALES
        -- ====================================================

        f.pay_amt1,
        f.pay_amt2,
        f.pay_amt3,
        f.pay_amt4,
        f.pay_amt5,
        f.pay_amt6,

        -- ====================================================
        -- PAY_AMT FEATURES
        -- ====================================================

        (
            f.pay_amt1 +
            f.pay_amt2 +
            f.pay_amt3 +
            f.pay_amt4 +
            f.pay_amt5 +
            f.pay_amt6
        ) / 6.0 AS pay_amt_avg,

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

        -- ====================================================
        -- PAYMENT / BILL
        -- ====================================================

        (
            SELECT AVG(
                CASE
                    WHEN b > 0 THEN p / b
                    ELSE NULL
                END
            )
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
            ) AS t(b, p)
        ) AS payment_bill_ratio_avg,

        (
            SELECT MAX(
                CASE
                    WHEN b > 0 THEN p / b
                    ELSE NULL
                END
            )
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
            ) AS t(b, p)
        ) AS payment_bill_ratio_max,

        -- ====================================================
        -- ATRASOS ALTOS
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

        -- ====================================================
        -- ATRASOS CONSECUTIVOS
        --
        -- Se cuenta la racha de meses consecutivos con
        -- atraso positivo comenzando por el mes más reciente.
        -- ====================================================

        CASE
            WHEN f.pay_0 <= 0 THEN 0

            WHEN f.pay_0 > 0
             AND f.pay_2 > 0
             AND f.pay_3 > 0
             AND f.pay_4 > 0
             AND f.pay_5 > 0
             AND f.pay_6 > 0
                THEN 6

            WHEN f.pay_0 > 0
             AND f.pay_2 > 0
             AND f.pay_3 > 0
             AND f.pay_4 > 0
             AND f.pay_5 > 0
                THEN 5

            WHEN f.pay_0 > 0
             AND f.pay_2 > 0
             AND f.pay_3 > 0
             AND f.pay_4 > 0
                THEN 4

            WHEN f.pay_0 > 0
             AND f.pay_2 > 0
             AND f.pay_3 > 0
                THEN 3

            WHEN f.pay_0 > 0
             AND f.pay_2 > 0
                THEN 2

            ELSE 1
        END AS consecutive_delay_months

    FROM gold.dim_cliente d

    INNER JOIN gold.fact_comportamiento_crediticio f
        ON d.cliente_key = f.cliente_key;

END;
$$;