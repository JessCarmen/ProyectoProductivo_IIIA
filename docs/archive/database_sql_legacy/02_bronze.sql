-- ============================================================
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
    ON bronze.raw_credit_card_clients(etl_batch_id);