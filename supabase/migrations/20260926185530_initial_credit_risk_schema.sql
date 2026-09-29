-- ============================================================
-- PROYECTO PRODUCTIVO IIIA
-- CREACIÓN DE ESQUEMAS
-- ============================================================

-- ------------------------------------------------------------
-- META
-- Metadatos, configuración, auditoría y control del pipeline
-- ------------------------------------------------------------

CREATE SCHEMA IF NOT EXISTS meta;


-- ------------------------------------------------------------
-- BRONZE
-- Datos RAW recibidos desde la fuente original
-- ------------------------------------------------------------

CREATE SCHEMA IF NOT EXISTS bronze;


-- ------------------------------------------------------------
-- SILVER
-- Datos tipificados, validados y estructurados
-- ------------------------------------------------------------

CREATE SCHEMA IF NOT EXISTS silver;


-- ------------------------------------------------------------
-- GOLD
-- Datos preparados para analítica, ML y scoring
-- ------------------------------------------------------------

CREATE SCHEMA IF NOT EXISTS gold;-- ============================================================
-- PROYECTO PRODUCTIVO IIIA
-- CAPA META: CONTROL, TRAZABILIDAD Y AUDITORÍA
-- ============================================================


-- ============================================================
-- 1. CONFIGURACIÓN DEL PIPELINE
-- ============================================================

CREATE TABLE IF NOT EXISTS meta.pipeline_config (
    id_config BIGSERIAL PRIMARY KEY,

    nombre_tabla VARCHAR(150) NOT NULL,

    esquema_origen VARCHAR(50),
    esquema_destino VARCHAR(50),

    ruta_archivo TEXT,

    tipo_carga VARCHAR(20) NOT NULL DEFAULT 'FULL'
        CHECK (tipo_carga IN ('FULL', 'DELTA')),

    campo_delta VARCHAR(100),

    ultima_fecha_delta TIMESTAMP,

    procedimiento_sp VARCHAR(200),

    activo BOOLEAN NOT NULL DEFAULT TRUE,

    orden_ejecucion INTEGER,

    descripcion TEXT,

    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);


-- ============================================================
-- 2. LOG DE EJECUCIONES DEL PIPELINE
-- ============================================================

CREATE TABLE IF NOT EXISTS meta.pipeline_run_log (
    id_run BIGSERIAL PRIMARY KEY,

    id_config BIGINT REFERENCES meta.pipeline_config(id_config),

    nombre_proceso VARCHAR(150) NOT NULL,

    fecha_inicio TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    fecha_fin TIMESTAMP,

    estado VARCHAR(20) NOT NULL DEFAULT 'RUNNING'
        CHECK (estado IN ('RUNNING', 'SUCCESS', 'WARNING', 'ERROR')),

    registros_leidos BIGINT DEFAULT 0,

    registros_insertados BIGINT DEFAULT 0,

    registros_actualizados BIGINT DEFAULT 0,

    registros_rechazados BIGINT DEFAULT 0,

    mensaje TEXT,

    error_detalle TEXT,

    ejecutado_por VARCHAR(150),

    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);


-- ============================================================
-- 3. LOG DE ERRORES
-- ============================================================

CREATE TABLE IF NOT EXISTS meta.pipeline_error_log (
    id_error BIGSERIAL PRIMARY KEY,

    id_run BIGINT REFERENCES meta.pipeline_run_log(id_run),

    nombre_proceso VARCHAR(150),

    nombre_tabla VARCHAR(150),

    registro_id VARCHAR(150),

    record_json JSONB,

    tipo_error VARCHAR(100),

    mensaje_error TEXT NOT NULL,

    fecha_error TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    ejecutado_por VARCHAR(150)
);


-- ============================================================
-- 4. LOG DE CALIDAD DE DATOS
-- ============================================================

CREATE TABLE IF NOT EXISTS meta.data_quality_log (
    id_quality BIGSERIAL PRIMARY KEY,

    id_run BIGINT REFERENCES meta.pipeline_run_log(id_run),

    esquema VARCHAR(50),

    nombre_tabla VARCHAR(150),

    regla_calidad VARCHAR(200) NOT NULL,

    descripcion TEXT,

    registros_evaluados BIGINT DEFAULT 0,

    registros_ok BIGINT DEFAULT 0,

    registros_error BIGINT DEFAULT 0,

    porcentaje_calidad NUMERIC(6,3),

    estado VARCHAR(20)
        CHECK (estado IN ('OK', 'WARNING', 'ERROR')),

    fecha_ejecucion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);


-- ============================================================
-- 5. REGISTRO DE MODELOS
-- ============================================================

CREATE TABLE IF NOT EXISTS meta.model_registry (
    id_modelo BIGSERIAL PRIMARY KEY,

    nombre_modelo VARCHAR(150) NOT NULL,

    version VARCHAR(50) NOT NULL,

    algoritmo VARCHAR(100),

    objetivo VARCHAR(200),

    variables_usadas JSONB,

    metricas JSONB,

    ruta_modelo TEXT,

    estado VARCHAR(30) DEFAULT 'EXPERIMENTAL'
        CHECK (
            estado IN (
                'EXPERIMENTAL',
                'VALIDATED',
                'PRODUCTION',
                'RETIRED'
            )
        ),

    fecha_entrenamiento TIMESTAMP,

    fecha_registro TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    observaciones TEXT
);


-- ============================================================
-- ÍNDICES
-- ============================================================

CREATE INDEX IF NOT EXISTS idx_pipeline_config_activo
    ON meta.pipeline_config(activo);

CREATE INDEX IF NOT EXISTS idx_pipeline_config_orden
    ON meta.pipeline_config(orden_ejecucion);

CREATE INDEX IF NOT EXISTS idx_pipeline_run_log_estado
    ON meta.pipeline_run_log(estado);

CREATE INDEX IF NOT EXISTS idx_pipeline_run_log_fecha
    ON meta.pipeline_run_log(fecha_inicio);

CREATE INDEX IF NOT EXISTS idx_pipeline_error_log_run
    ON meta.pipeline_error_log(id_run);

CREATE INDEX IF NOT EXISTS idx_data_quality_log_run
    ON meta.data_quality_log(id_run);

CREATE INDEX IF NOT EXISTS idx_model_registry_nombre
    ON meta.model_registry(nombre_modelo);-- ============================================================
-- PROYECTO PRODUCTIVO IIIA
-- CAPA BRONZE
-- FUENTE RAW DE CLIENTES DE TARJETA DE CRÉDITO
-- ============================================================

CREATE TABLE IF NOT EXISTS bronze.raw_credit_card_clients (

    -- ========================================================
    -- IDENTIFICADOR TÉCNICO DE BRONZE
    -- ========================================================

    bronze_id BIGSERIAL PRIMARY KEY,


    -- ========================================================
    -- DATOS RECIBIDOS DESDE LA FUENTE
    -- ========================================================

    bronze_record_id BIGINT,

    source_type VARCHAR(50),

    source_parent_id VARCHAR(150),

    record_origin VARCHAR(100),


    -- ========================================================
    -- IDENTIFICACIÓN DEL CLIENTE
    -- ========================================================

    id BIGINT,


    -- ========================================================
    -- INFORMACIÓN DEL CLIENTE
    -- ========================================================

    limit_bal NUMERIC,

    sex INTEGER,

    education INTEGER,

    marriage INTEGER,

    age INTEGER,


    -- ========================================================
    -- HISTORIAL DE PAGOS
    -- ========================================================

    pay_0 INTEGER,

    pay_2 INTEGER,

    pay_3 INTEGER,

    pay_4 INTEGER,

    pay_5 INTEGER,

    pay_6 INTEGER,


    -- ========================================================
    -- ESTADOS DE CUENTA
    -- ========================================================

    bill_amt1 NUMERIC,

    bill_amt2 NUMERIC,

    bill_amt3 NUMERIC,

    bill_amt4 NUMERIC,

    bill_amt5 NUMERIC,

    bill_amt6 NUMERIC,


    -- ========================================================
    -- PAGOS REALIZADOS
    -- ========================================================

    pay_amt1 NUMERIC,

    pay_amt2 NUMERIC,

    pay_amt3 NUMERIC,

    pay_amt4 NUMERIC,

    pay_amt5 NUMERIC,

    pay_amt6 NUMERIC,


    -- ========================================================
    -- VARIABLE OBJETIVO
    -- ========================================================

    default_payment_next_month INTEGER,


    -- ========================================================
    -- CALIDAD / TRAZABILIDAD RAW
    -- ========================================================

    raw_quality_flags TEXT,


    -- ========================================================
    -- AUDITORÍA ETL
    -- ========================================================

    etl_loaded_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    etl_batch_id VARCHAR(100),

    etl_source_file VARCHAR(255)
);


-- ============================================================
-- ÍNDICES
-- ============================================================

CREATE INDEX IF NOT EXISTS idx_bronze_source_id
    ON bronze.raw_credit_card_clients(id);

CREATE INDEX IF NOT EXISTS idx_bronze_record_id
    ON bronze.raw_credit_card_clients(bronze_record_id);

CREATE INDEX IF NOT EXISTS idx_bronze_loaded_at
    ON bronze.raw_credit_card_clients(etl_loaded_at);

CREATE INDEX IF NOT EXISTS idx_bronze_batch
    ON bronze.raw_credit_card_clients(etl_batch_id);-- ============================================================
-- PROYECTO PRODUCTIVO IIIA
-- CAPA SILVER
-- DATOS TIPADOS, VALIDADOS Y TRANSFORMADOS
-- ============================================================


-- ============================================================
-- 1. MAESTRO DE CLIENTES
-- ============================================================

CREATE TABLE IF NOT EXISTS silver.clientes_credito (

    id BIGINT PRIMARY KEY,

    limit_bal NUMERIC(15,2),

    sex INTEGER,

    education INTEGER,

    marriage INTEGER,

    age INTEGER,

    bronze_id BIGINT,

    fecha_carga TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_clientes_bronze
        FOREIGN KEY (bronze_id)
        REFERENCES bronze.raw_credit_card_clients(bronze_id)

);


-- ============================================================
-- 2. COMPORTAMIENTO CREDITICIO
-- ============================================================

CREATE TABLE IF NOT EXISTS silver.comportamiento_crediticio (

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

    fecha_carga TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_comportamiento_bronze
        FOREIGN KEY (bronze_id)
        REFERENCES bronze.raw_credit_card_clients(bronze_id),

    CONSTRAINT fk_comportamiento_cliente
        FOREIGN KEY (id)
        REFERENCES silver.clientes_credito(id)

);


-- ============================================================
-- ÍNDICES
-- ============================================================

CREATE INDEX IF NOT EXISTS idx_clientes_bronze
    ON silver.clientes_credito(bronze_id);

CREATE INDEX IF NOT EXISTS idx_comportamiento_bronze
    ON silver.comportamiento_crediticio(bronze_id);

CREATE INDEX IF NOT EXISTS idx_comportamiento_default
    ON silver.comportamiento_crediticio(default_payment_next_month);

CREATE INDEX IF NOT EXISTS idx_comportamiento_id
    ON silver.comportamiento_crediticio(id);-- ============================================================
-- PROYECTO PRODUCTIVO IIIA
-- CAPA GOLD
-- MODELO ANALÍTICO Y MACHINE LEARNING
-- ============================================================


-- ============================================================
-- 1. DIMENSIÓN CLIENTE
-- ============================================================

CREATE TABLE IF NOT EXISTS gold.dim_cliente (

    cliente_key BIGSERIAL PRIMARY KEY,

    id BIGINT NOT NULL UNIQUE,

    limit_bal NUMERIC(15,2),

    sex INTEGER,

    education INTEGER,

    marriage INTEGER,

    age INTEGER,

    fecha_carga TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);


-- ============================================================
-- 2. FACT DE COMPORTAMIENTO CREDITICIO
-- ============================================================

CREATE TABLE IF NOT EXISTS gold.fact_comportamiento_crediticio (

    comportamiento_key BIGSERIAL PRIMARY KEY,

    cliente_key BIGINT NOT NULL,

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

    fecha_carga TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_fact_cliente
        FOREIGN KEY (cliente_key)
        REFERENCES gold.dim_cliente(cliente_key)
);


-- ============================================================
-- 3. DATASET PARA MACHINE LEARNING
-- ============================================================

CREATE TABLE IF NOT EXISTS gold.gold_ml (

    ml_record_id BIGSERIAL PRIMARY KEY,

    id BIGINT NOT NULL UNIQUE,

    target_default INTEGER,

    -- Variables originales
    limit_bal NUMERIC(15,2),
    sex INTEGER,
    education INTEGER,
    marriage INTEGER,
    age INTEGER,

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

    -- Auditoría
    fecha_carga TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);


-- ============================================================
-- 4. ENTRADA PARA SCORING
-- ============================================================

CREATE TABLE IF NOT EXISTS gold.score_input (

    score_input_id BIGSERIAL PRIMARY KEY,

    id BIGINT NOT NULL,

    fecha_score TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    features JSONB,

    modelo_version VARCHAR(50),

    procesado BOOLEAN DEFAULT FALSE
);


-- ============================================================
-- 5. SALIDA DEL MODELO
-- ============================================================

CREATE TABLE IF NOT EXISTS gold.score_output (

    score_output_id BIGSERIAL PRIMARY KEY,

    id BIGINT NOT NULL,

    fecha_score TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    modelo_version VARCHAR(50),

    probability_default NUMERIC(8,6),

    prediction INTEGER,

    risk_level VARCHAR(30),

    recommendation TEXT,

    explanation JSONB
);


-- ============================================================
-- ÍNDICES
-- ============================================================

CREATE INDEX IF NOT EXISTS idx_gold_ml_target
    ON gold.gold_ml(target_default);

CREATE INDEX IF NOT EXISTS idx_gold_ml_id
    ON gold.gold_ml(id);

CREATE INDEX IF NOT EXISTS idx_score_input_id
    ON gold.score_input(id);

CREATE INDEX IF NOT EXISTS idx_score_output_id
    ON gold.score_output(id);

CREATE INDEX IF NOT EXISTS idx_score_output_prediction
    ON gold.score_output(prediction);-- ============================================================
-- PROYECTO PRODUCTIVO IIIA
-- STORED PROCEDURES DE LIMPIEZA Y TRANSFORMACIÓN
-- ============================================================


-- ============================================================
-- 1. LIMPIEZA DE MAESTRO DE CLIENTES
-- ============================================================

CREATE OR REPLACE PROCEDURE silver.sp_limpieza_maestros()

LANGUAGE plpgsql

AS $$

BEGIN

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

END;

$$;


-- ============================================================
-- 2. LIMPIEZA DE COMPORTAMIENTO CREDITICIO
-- ============================================================

CREATE OR REPLACE PROCEDURE silver.sp_limpieza_hechos()

LANGUAGE plpgsql

AS $$

BEGIN

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

        bronze_id =
            EXCLUDED.bronze_id,

        fecha_carga = CURRENT_TIMESTAMP;

END;

$$;-- ============================================================
-- PROYECTO PRODUCTIVO IIIA
-- VALIDACIONES DE CALIDAD
-- ============================================================


-- ============================================================
-- 1. VALIDACIÓN DE CLIENTES
-- ============================================================

SELECT
    COUNT(*) AS total_clientes,
    COUNT(DISTINCT id) AS clientes_unicos,
    COUNT(*) - COUNT(DISTINCT id) AS clientes_duplicados
FROM silver.clientes_credito;


-- ============================================================
-- 2. VALIDACIÓN DE COMPORTAMIENTO
-- ============================================================

SELECT
    COUNT(*) AS total_registros,
    COUNT(DISTINCT id) AS ids_unicos,
    COUNT(*) - COUNT(DISTINCT id) AS ids_duplicados
FROM silver.comportamiento_crediticio;


-- ============================================================
-- 3. VALIDACIÓN DE TARGET
-- ============================================================

SELECT
    default_payment_next_month AS target,
    COUNT(*) AS cantidad
FROM silver.comportamiento_crediticio
GROUP BY default_payment_next_month
ORDER BY default_payment_next_month;


-- ============================================================
-- 4. VALORES NULOS EN VARIABLES PRINCIPALES
-- ============================================================

SELECT
    COUNT(*) AS total,

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
-- 5. RANGOS DE EDAD
-- ============================================================

SELECT
    MIN(age) AS edad_minima,
    MAX(age) AS edad_maxima,
    AVG(age) AS edad_promedio
FROM silver.clientes_credito;


-- ============================================================
-- 6. RANGOS DE LÍMITE DE CRÉDITO
-- ============================================================

SELECT
    MIN(limit_bal) AS limite_minimo,
    MAX(limit_bal) AS limite_maximo,
    AVG(limit_bal) AS limite_promedio
FROM silver.clientes_credito;


-- ============================================================
-- 7. CÓDIGOS SEX
-- ============================================================

SELECT
    sex,
    COUNT(*) AS cantidad
FROM silver.clientes_credito
GROUP BY sex
ORDER BY sex;


-- ============================================================
-- 8. CÓDIGOS EDUCATION
-- ============================================================

SELECT
    education,
    COUNT(*) AS cantidad
FROM silver.clientes_credito
GROUP BY education
ORDER BY education;


-- ============================================================
-- 9. CÓDIGOS MARRIAGE
-- ============================================================

SELECT
    marriage,
    COUNT(*) AS cantidad
FROM silver.clientes_credito
GROUP BY marriage
ORDER BY marriage;


-- ============================================================
-- 10. CÓDIGOS DE PAGO
-- ============================================================

SELECT pay_0 AS periodo, COUNT(*) AS cantidad
FROM silver.comportamiento_crediticio
GROUP BY pay_0
ORDER BY pay_0;