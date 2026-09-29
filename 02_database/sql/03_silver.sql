-- ============================================================
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
    ON silver.comportamiento_crediticio(id);