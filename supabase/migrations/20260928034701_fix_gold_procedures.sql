-- ============================================================
-- FIX GOLD PROCEDURES
-- ============================================================

-- ============================================================
-- 1. CONSTRUIR GOLD
-- ============================================================

CREATE OR REPLACE PROCEDURE gold.sp_construir_gold()
LANGUAGE plpgsql
AS $$
BEGIN

    -- --------------------------------------------------------
    -- Limpiar primero FACT porque depende de DIM
    -- --------------------------------------------------------

    TRUNCATE TABLE
        gold.fact_comportamiento_crediticio,
        gold.dim_cliente
    RESTART IDENTITY;


    -- --------------------------------------------------------
    -- DIM CLIENTE
    -- --------------------------------------------------------

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

    INSERT INTO gold.fact_comportamiento_crediticio (
        cliente_key,
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
        default_payment_next_month
    )
    SELECT
        d.cliente_key,
        s.pay_0,
        s.pay_2,
        s.pay_3,
        s.pay_4,
        s.pay_5,
        s.pay_6,
        s.bill_amt1,
        s.bill_amt2,
        s.bill_amt3,
        s.bill_amt4,
        s.bill_amt5,
        s.bill_amt6,
        s.pay_amt1,
        s.pay_amt2,
        s.pay_amt3,
        s.pay_amt4,
        s.pay_amt5,
        s.pay_amt6,
        s.default_payment_next_month
    FROM silver.comportamiento_crediticio s
    INNER JOIN gold.dim_cliente d
        ON d.id = s.id;

END;
$$;


-- ============================================================
-- 2. CONSTRUIR GOLD_ML
-- ============================================================

CREATE OR REPLACE PROCEDURE gold.sp_construir_gold_ml()
LANGUAGE plpgsql
AS $$
BEGIN

    -- --------------------------------------------------------
    -- Limpiar GOLD_ML
    -- --------------------------------------------------------

    TRUNCATE TABLE gold.gold_ml
    RESTART IDENTITY;


    -- --------------------------------------------------------
    -- Cargar variables base desde GOLD
    -- --------------------------------------------------------

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
        pay_amt6
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

        f.bill_amt1,
        f.bill_amt2,
        f.bill_amt3,
        f.bill_amt4,
        f.bill_amt5,
        f.bill_amt6,

        f.pay_amt1,
        f.pay_amt2,
        f.pay_amt3,
        f.pay_amt4,
        f.pay_amt5,
        f.pay_amt6

    FROM gold.dim_cliente d
    INNER JOIN gold.fact_comportamiento_crediticio f
        ON d.cliente_key = f.cliente_key;

END;
$$;