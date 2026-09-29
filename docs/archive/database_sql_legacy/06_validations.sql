-- ============================================================
-- PROYECTO PRODUCTIVO IIIA
-- VALIDACIONES CAPA SILVER
-- ============================================================


-- ============================================================
-- 1. CONTEOS GENERALES
-- ============================================================

SELECT
    (SELECT COUNT(*)
     FROM bronze.raw_credit_card_clients)
        AS bronze_total,

    (SELECT COUNT(*)
     FROM silver.clientes_credito)
        AS silver_clientes_credito,

    (SELECT COUNT(*)
     FROM silver.comportamiento_crediticio)
        AS silver_comportamiento_crediticio;


-- ============================================================
-- 2. DUPLICADOS EN CLIENTES
-- ============================================================

SELECT
    COUNT(*) AS total_clientes,
    COUNT(DISTINCT id) AS clientes_unicos,
    COUNT(*) - COUNT(DISTINCT id) AS clientes_duplicados
FROM silver.clientes_credito;


-- ============================================================
-- 3. DUPLICADOS EN COMPORTAMIENTO
-- ============================================================

SELECT
    COUNT(*) AS total_comportamientos,
    COUNT(DISTINCT id) AS ids_unicos,
    COUNT(*) - COUNT(DISTINCT id) AS registros_duplicados
FROM silver.comportamiento_crediticio;


-- ============================================================
-- 4. COMPORTAMIENTOS SIN CLIENTE
-- ============================================================

SELECT
    COUNT(*) AS comportamientos_sin_cliente
FROM silver.comportamiento_crediticio h
LEFT JOIN silver.clientes_credito c
    ON h.id = c.id
WHERE c.id IS NULL;


-- ============================================================
-- 5. FALTANTES EN CLIENTES
-- ============================================================

SELECT
    COUNT(*) FILTER (
        WHERE limit_bal IS NULL
    ) AS null_limit_bal,

    COUNT(*) FILTER (
        WHERE age IS NULL
    ) AS null_age,

    COUNT(*) FILTER (
        WHERE sex IS NULL
    ) AS null_sex,

    COUNT(*) FILTER (
        WHERE education IS NULL
    ) AS null_education,

    COUNT(*) FILTER (
        WHERE marriage IS NULL
    ) AS null_marriage

FROM silver.clientes_credito;


-- ============================================================
-- 6. FALTANTES EN COMPORTAMIENTO
-- ============================================================

SELECT
    COUNT(*) FILTER (
        WHERE bill_amt3 IS NULL
    ) AS null_bill_amt3,

    COUNT(*) FILTER (
        WHERE pay_amt2 IS NULL
    ) AS null_pay_amt2

FROM silver.comportamiento_crediticio;


-- ============================================================
-- 7. CONTROL DE PROBLEMAS MARCADOS EN BRONZE
--
-- Estas cantidades representan los problemas agregados
-- deliberadamente en la fuente RAW.
--
-- Esperado:
-- INVALID_SEX          = 25
-- INVALID_EDUCATION    = 60
-- INVALID_MARRIAGE     = 40
-- OUTLIER_AGE          = 22
-- OUTLIER_LIMIT_BAL    = 24
-- OUTLIER_PAY_AMT1     = 14
-- ============================================================

SELECT
    COUNT(*) FILTER (
        WHERE POSITION(
            'INVALID_SEX'
            IN COALESCE(raw_quality_flags, '')
        ) > 0
    ) AS invalid_sex_marcados,

    COUNT(*) FILTER (
        WHERE POSITION(
            'INVALID_EDUCATION'
            IN COALESCE(raw_quality_flags, '')
        ) > 0
    ) AS invalid_education_marcados,

    COUNT(*) FILTER (
        WHERE POSITION(
            'INVALID_MARRIAGE'
            IN COALESCE(raw_quality_flags, '')
        ) > 0
    ) AS invalid_marriage_marcados,

    COUNT(*) FILTER (
        WHERE POSITION(
            'OUTLIER_AGE'
            IN COALESCE(raw_quality_flags, '')
        ) > 0
    ) AS outlier_age_marcados,

    COUNT(*) FILTER (
        WHERE POSITION(
            'OUTLIER_LIMIT_BAL'
            IN COALESCE(raw_quality_flags, '')
        ) > 0
    ) AS outlier_limit_bal_marcados,

    COUNT(*) FILTER (
        WHERE POSITION(
            'OUTLIER_PAY_AMT1'
            IN COALESCE(raw_quality_flags, '')
        ) > 0
    ) AS outlier_pay_amt1_marcados

FROM bronze.raw_credit_card_clients;


-- ============================================================
-- 8. VALIDACIÓN INVALID_SEX
--
-- Los 25 registros marcados deben haber sido transformados
-- a SEX = 3.
--
-- Debe devolver 0.
-- ============================================================

SELECT
    COUNT(*) AS sex_invalido_pendiente
FROM silver.clientes_credito c
INNER JOIN bronze.raw_credit_card_clients b
    ON c.bronze_id = b.bronze_id
WHERE POSITION(
        'INVALID_SEX'
        IN COALESCE(b.raw_quality_flags, '')
      ) > 0
  AND c.sex <> 3;


-- ============================================================
-- 9. VALIDACIÓN INVALID_EDUCATION
--
-- Los 60 registros marcados deben haber sido transformados
-- a EDUCATION = 4.
--
-- Debe devolver 0.
-- ============================================================

SELECT
    COUNT(*) AS education_invalido_pendiente
FROM silver.clientes_credito c
INNER JOIN bronze.raw_credit_card_clients b
    ON c.bronze_id = b.bronze_id
WHERE POSITION(
        'INVALID_EDUCATION'
        IN COALESCE(b.raw_quality_flags, '')
      ) > 0
  AND c.education <> 4;


-- ============================================================
-- 10. VALIDACIÓN INVALID_MARRIAGE
--
-- Los 40 registros marcados deben haber sido transformados
-- a MARRIAGE = 3.
--
-- Debe devolver 0.
--
-- IMPORTANTE:
-- Los 55 registros MARRIAGE = 0 que ya existían en RAW
-- NO se consideran error agregado y no deben limpiarse
-- mediante esta regla.
-- ============================================================

SELECT
    COUNT(*) AS marriage_invalido_pendiente
FROM silver.clientes_credito c
INNER JOIN bronze.raw_credit_card_clients b
    ON c.bronze_id = b.bronze_id
WHERE POSITION(
        'INVALID_MARRIAGE'
        IN COALESCE(b.raw_quality_flags, '')
      ) > 0
  AND c.marriage <> 3;


-- ============================================================
-- 11. VALIDACIÓN OUTLIER_AGE
--
-- Los 22 registros marcados deben haber sido transformados
-- a AGE = 75.
--
-- Debe devolver 0.
--
-- IMPORTANTE:
-- Si existen valores AGE > 75 que NO tienen la marca
-- OUTLIER_AGE, se conservan para su análisis posterior
-- en EDA.
-- ============================================================

SELECT
    COUNT(*) AS age_outlier_pendiente
FROM silver.clientes_credito c
INNER JOIN bronze.raw_credit_card_clients b
    ON c.bronze_id = b.bronze_id
WHERE POSITION(
        'OUTLIER_AGE'
        IN COALESCE(b.raw_quality_flags, '')
      ) > 0
  AND c.age <> 75;


-- ============================================================
-- 12. VALIDACIÓN OUTLIER_LIMIT_BAL
--
-- Los 24 registros marcados deben haber sido transformados
-- a LIMIT_BAL = 750000.
--
-- Debe devolver 0.
-- ============================================================

SELECT
    COUNT(*) AS limit_bal_outlier_pendiente
FROM silver.clientes_credito c
INNER JOIN bronze.raw_credit_card_clients b
    ON c.bronze_id = b.bronze_id
WHERE POSITION(
        'OUTLIER_LIMIT_BAL'
        IN COALESCE(b.raw_quality_flags, '')
      ) > 0
  AND c.limit_bal <> 750000;


-- ============================================================
-- 13. VALIDACIÓN OUTLIER_PAY_AMT1
--
-- Los 14 registros marcados deben haber sido transformados
-- a PAY_AMT1 = 250000.
--
-- Debe devolver 0.
--
-- IMPORTANTE:
-- Otros valores PAY_AMT1 > 250000 que NO tengan la marca
-- OUTLIER_PAY_AMT1 no se consideran error de limpieza.
-- Serán analizados posteriormente mediante EDA.
-- ============================================================

SELECT
    COUNT(*) AS pay_amt1_outlier_pendiente
FROM silver.comportamiento_crediticio h
INNER JOIN bronze.raw_credit_card_clients b
    ON h.bronze_id = b.bronze_id
WHERE POSITION(
        'OUTLIER_PAY_AMT1'
        IN COALESCE(b.raw_quality_flags, '')
      ) > 0
  AND h.pay_amt1 <> 250000;


-- ============================================================
-- 14. TARGET
--
-- Se verifica que la limpieza no haya alterado
-- la variable objetivo.
-- ============================================================

SELECT
    default_payment_next_month AS target,
    COUNT(*) AS cantidad,
    ROUND(
        COUNT(*) * 100.0 /
        SUM(COUNT(*)) OVER (),
        2
    ) AS porcentaje
FROM silver.comportamiento_crediticio
GROUP BY default_payment_next_month
ORDER BY default_payment_next_month;


-- ============================================================
-- 15. DOMINIOS BÁSICOS OBSERVADOS
--
-- Esta consulta es DESCRIPTIVA.
--
-- No se utiliza para declarar automáticamente como errores
-- los valores poco frecuentes que ya existían en RAW.
-- ============================================================

SELECT
    sex,
    COUNT(*) AS cantidad
FROM silver.clientes_credito
GROUP BY sex
ORDER BY sex;


SELECT
    education,
    COUNT(*) AS cantidad
FROM silver.clientes_credito
GROUP BY education
ORDER BY education;


SELECT
    marriage,
    COUNT(*) AS cantidad
FROM silver.clientes_credito
GROUP BY marriage
ORDER BY marriage;


-- ============================================================
-- 16. VALORES ORIGINALES EXTREMOS NO MARCADOS
--
-- Estos registros NO se corrigen automáticamente.
-- Se conservan para ser estudiados durante el EDA.
-- ============================================================

-- AGE > 75 sin marca OUTLIER_AGE
SELECT
    COUNT(*) AS age_extremo_original_no_marcado
FROM silver.clientes_credito c
INNER JOIN bronze.raw_credit_card_clients b
    ON c.bronze_id = b.bronze_id
WHERE c.age > 75
  AND POSITION(
        'OUTLIER_AGE'
        IN COALESCE(b.raw_quality_flags, '')
      ) = 0;


-- PAY_AMT1 > 250000 sin marca OUTLIER_PAY_AMT1
SELECT
    COUNT(*) AS pay_amt1_extremo_original_no_marcado
FROM silver.comportamiento_crediticio h
INNER JOIN bronze.raw_credit_card_clients b
    ON h.bronze_id = b.bronze_id
WHERE h.pay_amt1 > 250000
  AND POSITION(
        'OUTLIER_PAY_AMT1'
        IN COALESCE(b.raw_quality_flags, '')
      ) = 0;


-- MARRIAGE = 0 sin marca INVALID_MARRIAGE
SELECT
    COUNT(*) AS marriage_0_original_no_marcado
FROM silver.clientes_credito c
INNER JOIN bronze.raw_credit_card_clients b
    ON c.bronze_id = b.bronze_id
WHERE c.marriage = 0
  AND POSITION(
        'INVALID_MARRIAGE'
        IN COALESCE(b.raw_quality_flags, '')
      ) = 0;