-- ============================================================
-- PROYECTO PRODUCTIVO IIIA
-- CAPA SILVER
-- PROCEDIMIENTOS DE LIMPIEZA Y TRANSFORMACIÓN
-- ============================================================


-- ============================================================
-- 1. LIMPIEZA DEL MAESTRO DE CLIENTES
-- Tabla destino:
-- silver.clientes_credito
-- ============================================================

CREATE OR REPLACE PROCEDURE silver.sp_limpieza_maestros()
LANGUAGE plpgsql
AS $$
DECLARE
    v_mediana_limit_bal NUMERIC;
    v_mediana_age NUMERIC;
BEGIN

    -- ========================================================
    -- 1. BRONZE -> SILVER
    -- ========================================================

    INSERT INTO silver.clientes_credito (
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
    FROM bronze.raw_credit_card_clients
    WHERE id IS NOT NULL

    ON CONFLICT (id)
    DO UPDATE SET
        limit_bal = EXCLUDED.limit_bal,
        sex = EXCLUDED.sex,
        education = EXCLUDED.education,
        marriage = EXCLUDED.marriage,
        age = EXCLUDED.age,
        bronze_id = EXCLUDED.bronze_id,
        fecha_carga = CURRENT_TIMESTAMP;


    -- ========================================================
    -- 2. MEDIANA DE LIMIT_BAL
    --
    -- Se excluyen los registros marcados como
    -- OUTLIER_LIMIT_BAL.
    -- ========================================================

    SELECT
        percentile_cont(0.5)
        WITHIN GROUP (ORDER BY c.limit_bal)
    INTO v_mediana_limit_bal
    FROM silver.clientes_credito c
    INNER JOIN bronze.raw_credit_card_clients b
        ON b.bronze_id = c.bronze_id
    WHERE c.limit_bal IS NOT NULL
      AND POSITION(
            'OUTLIER_LIMIT_BAL'
            IN COALESCE(b.raw_quality_flags, '')
          ) = 0;


    -- ========================================================
    -- 3. MEDIANA DE AGE
    --
    -- Se excluyen los registros marcados como
    -- OUTLIER_AGE.
    -- ========================================================

    SELECT
        percentile_cont(0.5)
        WITHIN GROUP (ORDER BY c.age)
    INTO v_mediana_age
    FROM silver.clientes_credito c
    INNER JOIN bronze.raw_credit_card_clients b
        ON b.bronze_id = c.bronze_id
    WHERE c.age IS NOT NULL
      AND POSITION(
            'OUTLIER_AGE'
            IN COALESCE(b.raw_quality_flags, '')
          ) = 0;


    -- ========================================================
    -- 4. IMPUTAR LIMIT_BAL
    --
    -- 90 valores faltantes controlados.
    -- ========================================================

    UPDATE silver.clientes_credito c
    SET limit_bal = v_mediana_limit_bal
    FROM bronze.raw_credit_card_clients b
    WHERE c.bronze_id = b.bronze_id
      AND POSITION(
            'MISSING_LIMIT_BAL'
            IN COALESCE(b.raw_quality_flags, '')
          ) > 0;


    -- ========================================================
    -- 5. IMPUTAR AGE
    --
    -- 80 valores faltantes controlados.
    -- ========================================================

    UPDATE silver.clientes_credito c
    SET age = ROUND(v_mediana_age)::INTEGER
    FROM bronze.raw_credit_card_clients b
    WHERE c.bronze_id = b.bronze_id
      AND POSITION(
            'MISSING_AGE'
            IN COALESCE(b.raw_quality_flags, '')
          ) > 0;


    -- ========================================================
    -- 6. CORREGIR SEX
    --
    -- 25 registros:
    -- INVALID_SEX -> 3
    -- ========================================================

    UPDATE silver.clientes_credito c
    SET sex = 3
    FROM bronze.raw_credit_card_clients b
    WHERE c.bronze_id = b.bronze_id
      AND POSITION(
            'INVALID_SEX'
            IN COALESCE(b.raw_quality_flags, '')
          ) > 0;


    -- ========================================================
    -- 7. CORREGIR EDUCATION
    --
    -- 60 registros:
    -- INVALID_EDUCATION -> 4
    -- ========================================================

    UPDATE silver.clientes_credito c
    SET education = 4
    FROM bronze.raw_credit_card_clients b
    WHERE c.bronze_id = b.bronze_id
      AND POSITION(
            'INVALID_EDUCATION'
            IN COALESCE(b.raw_quality_flags, '')
          ) > 0;


    -- ========================================================
    -- 8. CORREGIR MARRIAGE
    --
    -- 40 registros:
    -- INVALID_MARRIAGE -> 3
    -- ========================================================

    UPDATE silver.clientes_credito c
    SET marriage = 3
    FROM bronze.raw_credit_card_clients b
    WHERE c.bronze_id = b.bronze_id
      AND POSITION(
            'INVALID_MARRIAGE'
            IN COALESCE(b.raw_quality_flags, '')
          ) > 0;


    -- ========================================================
    -- 9. CORREGIR OUTLIER DE AGE
    --
    -- 22 registros:
    -- 95 -> 75
    -- ========================================================

    UPDATE silver.clientes_credito c
    SET age = 75
    FROM bronze.raw_credit_card_clients b
    WHERE c.bronze_id = b.bronze_id
      AND POSITION(
            'OUTLIER_AGE'
            IN COALESCE(b.raw_quality_flags, '')
          ) > 0;


    -- ========================================================
    -- 10. CORREGIR OUTLIER DE LIMIT_BAL
    --
    -- 24 registros:
    -- 2,500,000 -> 750,000
    -- ========================================================

    UPDATE silver.clientes_credito c
    SET limit_bal = 750000
    FROM bronze.raw_credit_card_clients b
    WHERE c.bronze_id = b.bronze_id
      AND b.limit_bal > 750000;

END;
$$;


-- ============================================================
-- 2. LIMPIEZA DEL COMPORTAMIENTO CREDITICIO
-- Tabla destino:
-- silver.comportamiento_crediticio
-- ============================================================

CREATE OR REPLACE PROCEDURE silver.sp_limpieza_hechos()
LANGUAGE plpgsql
AS $$
DECLARE
    v_mediana_bill_amt3 NUMERIC;
    v_mediana_pay_amt2 NUMERIC;
BEGIN

    -- ========================================================
    -- 1. BRONZE -> SILVER
    -- ========================================================

    INSERT INTO silver.comportamiento_crediticio (
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
    FROM bronze.raw_credit_card_clients
    WHERE id IS NOT NULL

    ON CONFLICT (id)
    DO UPDATE SET
        pay_0 = EXCLUDED.pay_0,
        pay_2 = EXCLUDED.pay_2,
        pay_3 = EXCLUDED.pay_3,
        pay_4 = EXCLUDED.pay_4,
        pay_5 = EXCLUDED.pay_5,
        pay_6 = EXCLUDED.pay_6,
        bill_amt1 = EXCLUDED.bill_amt1,
        bill_amt2 = EXCLUDED.bill_amt2,
        bill_amt3 = EXCLUDED.bill_amt3,
        bill_amt4 = EXCLUDED.bill_amt4,
        bill_amt5 = EXCLUDED.bill_amt5,
        bill_amt6 = EXCLUDED.bill_amt6,
        pay_amt1 = EXCLUDED.pay_amt1,
        pay_amt2 = EXCLUDED.pay_amt2,
        pay_amt3 = EXCLUDED.pay_amt3,
        pay_amt4 = EXCLUDED.pay_amt4,
        pay_amt5 = EXCLUDED.pay_amt5,
        pay_amt6 = EXCLUDED.pay_amt6,
        default_payment_next_month =
            EXCLUDED.default_payment_next_month,
        bronze_id = EXCLUDED.bronze_id,
        fecha_carga = CURRENT_TIMESTAMP;


    -- ========================================================
    -- 2. MEDIANA DE BILL_AMT3
    -- ========================================================

    SELECT
        percentile_cont(0.5)
        WITHIN GROUP (ORDER BY bill_amt3)
    INTO v_mediana_bill_amt3
    FROM silver.comportamiento_crediticio
    WHERE bill_amt3 IS NOT NULL;


    -- ========================================================
    -- 3. MEDIANA DE PAY_AMT2
    -- ========================================================

    SELECT
        percentile_cont(0.5)
        WITHIN GROUP (ORDER BY pay_amt2)
    INTO v_mediana_pay_amt2
    FROM silver.comportamiento_crediticio
    WHERE pay_amt2 IS NOT NULL;


    -- ========================================================
    -- 4. IMPUTAR BILL_AMT3
    --
    -- 110 valores faltantes controlados.
    -- ========================================================

    UPDATE silver.comportamiento_crediticio h
    SET bill_amt3 = v_mediana_bill_amt3
    FROM bronze.raw_credit_card_clients b
    WHERE h.bronze_id = b.bronze_id
      AND POSITION(
            'MISSING_BILL_AMT3'
            IN COALESCE(b.raw_quality_flags, '')
          ) > 0;


    -- ========================================================
    -- 5. IMPUTAR PAY_AMT2
    --
    -- 100 valores faltantes controlados.
    -- ========================================================

    UPDATE silver.comportamiento_crediticio h
    SET pay_amt2 = v_mediana_pay_amt2
    FROM bronze.raw_credit_card_clients b
    WHERE h.bronze_id = b.bronze_id
      AND POSITION(
            'MISSING_PAY_AMT2'
            IN COALESCE(b.raw_quality_flags, '')
          ) > 0;


    -- ========================================================
    -- 6. CORREGIR OUTLIER DE PAY_AMT1
    --
    -- 14 registros:
    -- 3,000,000 -> 250,000
    -- ========================================================

    UPDATE silver.comportamiento_crediticio h
    SET pay_amt1 = 250000
    FROM bronze.raw_credit_card_clients b
    WHERE h.bronze_id = b.bronze_id
      AND POSITION(
            'OUTLIER_PAY_AMT1'
            IN COALESCE(b.raw_quality_flags, '')
          ) > 0;

END;
$$;