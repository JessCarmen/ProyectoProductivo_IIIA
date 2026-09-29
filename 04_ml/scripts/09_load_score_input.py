import argparse
import json
import os
from pathlib import Path

import pandas as pd
import psycopg
from dotenv import load_dotenv

load_dotenv()
ROOT = Path(__file__).resolve().parents[2]


def get_connection():
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("No se encontro DATABASE_URL en .env")
    return psycopg.connect(database_url)


def main():
    parser = argparse.ArgumentParser(description="Carga clientes de Gold a score_input para pruebas de scoring.")
    parser.add_argument("--id", type=int, required=True)
    args = parser.parse_args()

    with get_connection() as conn:
        df = pd.read_sql_query("SELECT * FROM gold.gold_ml WHERE id = %s", conn, params=(args.id,))
        if df.empty:
            raise ValueError(f"No existe el cliente {args.id} en gold.gold_ml")

        row = df.iloc[0]
        payload = {
            k: (None if pd.isna(row[k]) else row[k].item() if hasattr(row[k], "item") else row[k])
            for k in df.columns
            if k not in {"target_default", "ml_record_id", "id", "fecha_carga"}
        }
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO gold.score_input (id, features, modelo_version, procesado) VALUES (%s, %s::jsonb, NULL, FALSE) RETURNING score_input_id",
                (args.id, json.dumps(payload, ensure_ascii=False, default=str)),
            )
            score_input_id = cur.fetchone()[0]
        conn.commit()

    print(f"score_input_id creado: {score_input_id}")
    print(f"Cliente: {args.id}")
    print("Estado: pendiente de scoring")


if __name__ == "__main__":
    main()
