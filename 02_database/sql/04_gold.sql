-- ============================================================
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

    source_parent_id VARCHAR(150),

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

    source_parent_id VARCHAR(150),

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

    source_parent_id VARCHAR(150),

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

    score_input_id BIGINT,

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
    ON gold.score_output(prediction);