CREATE OR REPLACE PROCEDURE gold.sp_construir_gold()
LANGUAGE plpgsql
AS $$
BEGIN

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