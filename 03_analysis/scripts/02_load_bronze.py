import os
import uuid
from pathlib import Path
from datetime import datetime

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text


# ============================================================
# CONFIGURACIÓN
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[2]

CSV_PATH = BASE_DIR / "01_data" / "raw" / "credit_card_clients_raw.csv"

load_dotenv(BASE_DIR / ".env")

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError(
        "No se encontró DATABASE_URL en el archivo .env"
    )


# ============================================================
# CONEXIÓN
# ============================================================

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True
)


# ============================================================
# CARGA DEL CSV
# ============================================================

print("=" * 60)
print("CARGA CSV → BRONZE")
print("=" * 60)

print(f"Archivo: {CSV_PATH}")

if not CSV_PATH.exists():
    raise FileNotFoundError(
        f"No se encontró el archivo: {CSV_PATH}"
    )

df = pd.read_csv(
    CSV_PATH,
    sep=";"
)

print(f"Registros leídos: {len(df):,}")
print(f"Columnas: {len(df.columns)}")


# ============================================================
# IDENTIFICACIÓN DE LOTE
# ============================================================

etl_batch_id = str(uuid.uuid4())

etl_loaded_at = datetime.now()

etl_source_file = CSV_PATH.name

print(f"ETL batch ID: {etl_batch_id}")
print(f"Fecha de carga: {etl_loaded_at}")
print(f"Archivo origen: {etl_source_file}")


# ============================================================
# PREPARAR DATOS PARA BRONZE
# ============================================================

df = df.rename(
    columns={
        "bronze_record_id": "bronze_record_id",
        "source_type": "source_type",
        "source_parent_id": "source_parent_id",
        "record_origin": "record_origin",
        "ID": "id",
        "LIMIT_BAL": "limit_bal",
        "SEX": "sex",
        "EDUCATION": "education",
        "MARRIAGE": "marriage",
        "AGE": "age",
        "PAY_0": "pay_0",
        "PAY_2": "pay_2",
        "PAY_3": "pay_3",
        "PAY_4": "pay_4",
        "PAY_5": "pay_5",
        "PAY_6": "pay_6",
        "BILL_AMT1": "bill_amt1",
        "BILL_AMT2": "bill_amt2",
        "BILL_AMT3": "bill_amt3",
        "BILL_AMT4": "bill_amt4",
        "BILL_AMT5": "bill_amt5",
        "BILL_AMT6": "bill_amt6",
        "PAY_AMT1": "pay_amt1",
        "PAY_AMT2": "pay_amt2",
        "PAY_AMT3": "pay_amt3",
        "PAY_AMT4": "pay_amt4",
        "PAY_AMT5": "pay_amt5",
        "PAY_AMT6": "pay_amt6",
        "default payment next month": "default_payment_next_month",
        "raw_quality_flags": "raw_quality_flags",
    }
)


# ============================================================
# AUDITORÍA ETL
# ============================================================

df["etl_loaded_at"] = etl_loaded_at
df["etl_batch_id"] = etl_batch_id
df["etl_source_file"] = etl_source_file


# ============================================================
# CARGAR A BRONZE
# ============================================================

print("\nConectando a Supabase PostgreSQL...")

with engine.begin() as connection:

    print("Insertando registros en bronze.raw_credit_card_clients...")

    df.to_sql(
        name="raw_credit_card_clients",
        con=connection,
        schema="bronze",
        if_exists="append",
        index=False,
        method="multi",
        chunksize=1000
    )


# ============================================================
# VALIDACIÓN
# ============================================================

with engine.connect() as connection:

    result = connection.execute(
        text(
            """
            SELECT COUNT(*)
            FROM bronze.raw_credit_card_clients
            WHERE etl_batch_id = :batch_id
            """
        ),
        {
            "batch_id": etl_batch_id
        }
    )

    registros_cargados = result.scalar()


print("\n" + "=" * 60)
print("CARGA FINALIZADA")
print("=" * 60)

print(f"Registros leídos : {len(df):,}")
print(f"Registros cargados: {registros_cargados:,}")

if registros_cargados != len(df):
    raise RuntimeError(
        "La cantidad de registros cargados no coincide "
        "con la cantidad de registros leídos."
    )

print("Estado: OK")