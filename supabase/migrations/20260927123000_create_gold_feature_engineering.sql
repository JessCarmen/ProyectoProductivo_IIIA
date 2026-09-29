-- ============================================================
-- GOLD / FEATURE ENGINEERING
-- Proyecto Productivo IIIA
-- ============================================================

-- ------------------------------------------------------------
-- 1. DIMENSION CLIENTE
-- ------------------------------------------------------------

CREATE TABLE IF NOT EXISTS gold.dim_cliente (
    id BIGINT PRIMARY KEY,
    limit_bal NUMERIC(15,2),
    sex INTEGER,
    education INTEGER,
    marriage INTEGER,
    age INTEGER,
    bronze_id BIGINT,
    fecha_proceso TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ------------------------------------------------------------
-- 2. FACT COMPORTAMIENTO CREDITICIO
-- ------------------------------------------------------------

CREATE TABLE IF NOT EXISTS gold.fact_comportamiento_crediticio (
    id BIGINT PRIMARY KEY,

    pay_0 INTEGER,
    pay_2 INTEGER,
    pay_3 INTEGER,
    pay_4 INTEGER,
    pay_5 INTEGER,
    pay_6 INTEGER,

    bill_amt1 NUMERIC(15,2),
    bill_amt2 NUMERIC(15,2),
    bill_amt3 NUMERIC(15,2),
    bill_amt4 NUMERIC(15,2),
    bill_amt5 NUMERIC(15,2),
    bill_amt6 NUMERIC(15,2),

    pay_amt1 NUMERIC(15,2),
    pay_amt2 NUMERIC(15,2),
    pay_amt3 NUMERIC(15,2),
    pay_amt4 NUMERIC(15,2),
    pay_amt5 NUMERIC(15,2),
    pay_amt6 NUMERIC(15,2),

    default_payment_next_month INTEGER,

    bronze_id BIGINT,
    fecha_proceso TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ------------------------------------------------------------
-- 3. GOLD_ML
-- ------------------------------------------------------------

CREATE TABLE IF NOT EXISTS gold.gold_ml (
    id BIGINT PRIMARY KEY,

    -- =========================
    -- Variables demográficas
    -- =========================

    limit_bal NUMERIC(15,2),
    sex INTEGER,
    education INTEGER,
    marriage INTEGER,
    age INTEGER,

    -- =========================
    -- Variables PAY
    -- =========================

    pay_0 INTEGER,
    pay_2 INTEGER,
    pay_3 INTEGER,
    pay_4 INTEGER,
    pay_5 INTEGER,
    pay_6 INTEGER,

    pay_max_delay INTEGER,
    pay_avg_delay_positive NUMERIC(10,4),
    pay_positive_months INTEGER,
    pay_on_time_months INTEGER,
    pay_duly_paid_months INTEGER,
    pay_no_activity_months INTEGER,

    pay_negative_code_months INTEGER,

    -- =========================
    -- BILL AMT
    -- =========================

    bill_amt1 NUMERIC(15,2),
    bill_amt2 NUMERIC(15,2),
    bill_amt3 NUMERIC(15,2),
    bill_amt4 NUMERIC(15,2),
    bill_amt5 NUMERIC(15,2),
    bill_amt6 NUMERIC(15,2),

    bill_avg NUMERIC(15,2),
    bill_max NUMERIC(15,2),
    bill_min NUMERIC(15,2),
    bill_std NUMERIC(15,2),

    bill_negative_months INTEGER,
    bill_zero_months INTEGER,
    bill_positive_months INTEGER,

    -- =========================
    -- PAY AMT
    -- =========================

    pay_amt1 NUMERIC(15,2),
    pay_amt2 NUMERIC(15,2),
    pay_amt3 NUMERIC(15,2),
    pay_amt4 NUMERIC(15,2),
    pay_amt5 NUMERIC(15,2),
    pay_amt6 NUMERIC(15,2),

    pay_amt_avg NUMERIC(15,2),
    pay_amt_max NUMERIC(15,2),
    pay_amt_min NUMERIC(15,2),

    -- =========================
    -- Relación pago / factura
    -- =========================

    payment_bill_ratio_avg NUMERIC(15,6),
    payment_bill_ratio_max NUMERIC(15,6),

    -- =========================
    -- Indicadores adicionales
    -- =========================

    high_delay_months INTEGER,
    recent_delay_months INTEGER,
    consecutive_delay_months INTEGER,

    -- =========================
    -- Target
    -- =========================

    default_payment_next_month INTEGER,

    -- =========================
    -- Trazabilidad
    -- =========================

    fecha_proceso TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);


-- ============================================================
-- 4. PROCEDURE: CARGA GOLD
-- ============================================================

CREATE OR REPLACE PROCEDURE gold.sp_construir_gold()
LANGUAGE plpgsql
AS $$
BEGIN

    -- --------------------------------------------------------
    -- DIM CLIENTE
    -- --------------------------------------------------------

    TRUNCATE TABLE
        gold.fact_comportamiento_crediticio,
        gold.dim_cliente;


    INSERT INTO gold.dim_cliente (
        id,
        limit_bal,
        sex,
        education,
        marriage,
        age,
        bronze_id
    )
    SELECT
        id,
        limit_bal,
        sex,
        education,
        marriage,
        age,
        bronze_id
    FROM silver.clientes_credito;


    -- --------------------------------------------------------
    -- FACT COMPORTAMIENTO
    -- --------------------------------------------------------

    TRUNCATE TABLE gold.fact_comportamiento_crediticio;

    INSERT INTO gold.fact_comportamiento_crediticio (
        id,
        pay_0,
        pay_2,
        pay_3,
        pay_4,
        pay_5,
        pay_6,
        bill_amt1,
        bill_amt2,
        bill_amt3,
        bill_amt4,
        bill_amt5,
        bill_amt6,
        pay_amt1,
        pay_amt2,
        pay_amt3,
        pay_amt4,
        pay_amt5,
        pay_amt6,
        default_payment_next_month,
        bronze_id
    )
    SELECT
        id,
        pay_0,
        pay_2,
        pay_3,
        pay_4,
        pay_5,
        pay_6,
        bill_amt1,
        bill_amt2,
        bill_amt3,
        bill_amt4,
        bill_amt5,
        bill_amt6,
        pay_amt1,
        pay_amt2,
        pay_amt3,
        pay_amt4,
        pay_amt5,
        pay_amt6,
        default_payment_next_month,
        bronze_id
    FROM silver.comportamiento_crediticio;

END;
$$;

-- ============================================================
-- 5. PROCEDURE: FEATURE ENGINEERING
-- ============================================================

CREATE OR REPLACE PROCEDURE gold.sp_construir_gold_ml()
LANGUAGE plpgsql
AS $$
BEGIN

    TRUNCATE TABLE gold.gold_ml;

    INSERT INTO gold.gold_ml (

        id,

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

        pay_amt1,
        pay_amt2,
        pay_amt3,
        pay_amt4,
        pay_amt5,
        pay_amt6,

        pay_amt_avg,
        pay_amt_max,
        pay_amt_min,

        payment_bill_ratio_avg,
        payment_bill_ratio_max,

        high_delay_months,
        recent_delay_months,
        consecutive_delay_months,

        default_payment_next_month
    )

    SELECT

        c.id,

        -- ==============================================
        -- Cliente
        -- ==============================================

        c.limit_bal,
        c.sex,
        c.education,
        c.marriage,
        c.age,

        -- ==============================================
        -- PAY originales
        -- ==============================================

        f.pay_0,
        f.pay_2,
        f.pay_3,
        f.pay_4,
        f.pay_5,
        f.pay_6,

        -- Máximo atraso real
        GREATEST(
            f.pay_0,
            f.pay_2,
            f.pay_3,
            f.pay_4,
            f.pay_5,
            f.pay_6
        ) AS pay_max_delay,

        -- Promedio únicamente de meses con atraso positivo
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

        -- Meses con atraso
        (
            CASE WHEN f.pay_0 > 0 THEN 1 ELSE 0 END +
            CASE WHEN f.pay_2 > 0 THEN 1 ELSE 0 END +
            CASE WHEN f.pay_3 > 0 THEN 1 ELSE 0 END +
            CASE WHEN f.pay_4 > 0 THEN 1 ELSE 0 END +
            CASE WHEN f.pay_5 > 0 THEN 1 ELSE 0 END +
            CASE WHEN f.pay_6 > 0 THEN 1 ELSE 0 END
        ) AS pay_positive_months,

        -- Meses con código 0
        (
            CASE WHEN f.pay_0 = 0 THEN 1 ELSE 0 END +
            CASE WHEN f.pay_2 = 0 THEN 1 ELSE 0 END +
            CASE WHEN f.pay_3 = 0 THEN 1 ELSE 0 END +
            CASE WHEN f.pay_4 = 0 THEN 1 ELSE 0 END +
            CASE WHEN f.pay_5 = 0 THEN 1 ELSE 0 END +
            CASE WHEN f.pay_6 = 0 THEN 1 ELSE 0 END
        ) AS pay_on_time_months,

        -- Meses con -1
        (
            CASE WHEN f.pay_0 = -1 THEN 1 ELSE 0 END +
            CASE WHEN f.pay_2 = -1 THEN 1 ELSE 0 END +
            CASE WHEN f.pay_3 = -1 THEN 1 ELSE 0 END +
            CASE WHEN f.pay_4 = -1 THEN 1 ELSE 0 END +
            CASE WHEN f.pay_5 = -1 THEN 1 ELSE 0 END +
            CASE WHEN f.pay_6 = -1 THEN 1 ELSE 0 END
        ) AS pay_duly_paid_months,

        -- Meses con -2
        (
            CASE WHEN f.pay_0 = -2 THEN 1 ELSE 0 END +
            CASE WHEN f.pay_2 = -2 THEN 1 ELSE 0 END +
            CASE WHEN f.pay_3 = -2 THEN 1 ELSE 0 END +
            CASE WHEN f.pay_4 = -2 THEN 1 ELSE 0 END +
            CASE WHEN f.pay_5 = -2 THEN 1 ELSE 0 END +
            CASE WHEN f.pay_6 = -2 THEN 1 ELSE 0 END
        ) AS pay_no_activity_months,

        -- Códigos negativos
        (
            CASE WHEN f.pay_0 < 0 THEN 1 ELSE 0 END +
            CASE WHEN f.pay_2 < 0 THEN 1 ELSE 0 END +
            CASE WHEN f.pay_3 < 0 THEN 1 ELSE 0 END +
            CASE WHEN f.pay_4 < 0 THEN 1 ELSE 0 END +
            CASE WHEN f.pay_5 < 0 THEN 1 ELSE 0 END +
            CASE WHEN f.pay_6 < 0 THEN 1 ELSE 0 END
        ) AS pay_negative_code_months,

        -- ==============================================
        -- BILL AMT
        -- ==============================================

        f.bill_amt1,
        f.bill_amt2,
        f.bill_amt3,
        f.bill_amt4,
        f.bill_amt5,
        f.bill_amt6,

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

        -- BILL negativos
        (
            CASE WHEN f.bill_amt1 < 0 THEN 1 ELSE 0 END +
            CASE WHEN f.bill_amt2 < 0 THEN 1 ELSE 0 END +
            CASE WHEN f.bill_amt3 < 0 THEN 1 ELSE 0 END +
            CASE WHEN f.bill_amt4 < 0 THEN 1 ELSE 0 END +
            CASE WHEN f.bill_amt5 < 0 THEN 1 ELSE 0 END +
            CASE WHEN f.bill_amt6 < 0 THEN 1 ELSE 0 END
        ) AS bill_negative_months,

        -- BILL igual a cero
        (
            CASE WHEN f.bill_amt1 = 0 THEN 1 ELSE 0 END +
            CASE WHEN f.bill_amt2 = 0 THEN 1 ELSE 0 END +
            CASE WHEN f.bill_amt3 = 0 THEN 1 ELSE 0 END +
            CASE WHEN f.bill_amt4 = 0 THEN 1 ELSE 0 END +
            CASE WHEN f.bill_amt5 = 0 THEN 1 ELSE 0 END +
            CASE WHEN f.bill_amt6 = 0 THEN 1 ELSE 0 END
        ) AS bill_zero_months,

        -- BILL positivo
        (
            CASE WHEN f.bill_amt1 > 0 THEN 1 ELSE 0 END +
            CASE WHEN f.bill_amt2 > 0 THEN 1 ELSE 0 END +
            CASE WHEN f.bill_amt3 > 0 THEN 1 ELSE 0 END +
            CASE WHEN f.bill_amt4 > 0 THEN 1 ELSE 0 END +
            CASE WHEN f.bill_amt5 > 0 THEN 1 ELSE 0 END +
            CASE WHEN f.bill_amt6 > 0 THEN 1 ELSE 0 END
        ) AS bill_positive_months,

        -- ==============================================
        -- PAY AMT
        -- ==============================================

        f.pay_amt1,
        f.pay_amt2,
        f.pay_amt3,
        f.pay_amt4,
        f.pay_amt5,
        f.pay_amt6,

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

        -- ==============================================
        -- PAYMENT / BILL
        -- ==============================================

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

        -- ==============================================
        -- ATRASOS ALTOS
        -- ==============================================

        (
            CASE WHEN f.pay_0 >= 2 THEN 1 ELSE 0 END +
            CASE WHEN f.pay_2 >= 2 THEN 1 ELSE 0 END +
            CASE WHEN f.pay_3 >= 2 THEN 1 ELSE 0 END +
            CASE WHEN f.pay_4 >= 2 THEN 1 ELSE 0 END +
            CASE WHEN f.pay_5 >= 2 THEN 1 ELSE 0 END +
            CASE WHEN f.pay_6 >= 2 THEN 1 ELSE 0 END
        ) AS high_delay_months,

        -- Atrasos recientes: pay_0, pay_2, pay_3
        (
            CASE WHEN f.pay_0 > 0 THEN 1 ELSE 0 END +
            CASE WHEN f.pay_2 > 0 THEN 1 ELSE 0 END +
            CASE WHEN f.pay_3 > 0 THEN 1 ELSE 0 END
        ) AS recent_delay_months,

        -- ==============================================
        -- Target
        -- ==============================================

        f.default_payment_next_month

    FROM silver.clientes_credito c

    INNER JOIN silver.comportamiento_crediticio f
        ON c.id = f.id;

END;
$$;