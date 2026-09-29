import argparse
import json
import os
from pathlib import Path

import numpy as np
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()
ROOT = Path(__file__).resolve().parents[2]
METADATA_PATH = ROOT / "04_ml" / "models" / "model_metadata.json"


def get_engine():
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("No se encontro DATABASE_URL en .env")

    return create_engine(
        database_url,
        pool_pre_ping=True,
    )


def load_model_features():
    if not METADATA_PATH.exists():
        raise FileNotFoundError(
            f"No existe {METADATA_PATH}. Ejecuta 04_train.py primero."
        )

    metadata = json.loads(METADATA_PATH.read_text(encoding="utf-8"))
    features = metadata.get("features")

    if not features:
        raise RuntimeError(
            "model_metadata.json no contiene la lista de features del modelo."
        )

    return list(features)


def to_json_value(value):
    """Convierte tipos de pandas/numpy a tipos compatibles con JSON."""
    if value is None:
        return None

    if pd.isna(value):
        return None

    if isinstance(value, np.generic):
        return value.item()

    if isinstance(value, pd.Timestamp):
        return value.isoformat()

    return value


def load_customer(customer_id):
    engine = get_engine()

    query = text("""
        SELECT *
        FROM gold.gold_ml
        WHERE id = :customer_id
        ORDER BY id
    """)

    try:
        df = pd.read_sql_query(
            query,
            engine,
            params={"customer_id": customer_id},
        )
    finally:
        engine.dispose()

    if df.empty:
        raise ValueError(
            f"No existe el cliente {customer_id} en gold.gold_ml."
        )

    if len(df) > 1:
        raise RuntimeError(
            f"Se encontraron {len(df)} registros para el cliente {customer_id}. "
            "Se esperaba un unico registro."
        )

    return df.iloc[0], df.columns.tolist()


def insert_score_input(row, model_features, model_version=None):
    # Guardar SOLAMENTE las variables que realmente utiliza el modelo.
    missing = [feature for feature in model_features if feature not in row.index]
    if missing:
        raise RuntimeError(
            "Faltan variables requeridas por el modelo en gold.gold_ml: "
            + ", ".join(missing)
        )

    features = {
        feature: to_json_value(row[feature])
        for feature in model_features
    }

    engine = get_engine()

    query = text("""
        INSERT INTO gold.score_input (
            id,
            features,
            modelo_version,
            procesado
        )
        VALUES (
            :id,
            CAST(:features AS JSONB),
            :modelo_version,
            FALSE
        )
        RETURNING score_input_id
    """)

    try:
        with engine.begin() as connection:
            result = connection.execute(
                query,
                {
                    "id": int(row["id"]),
                    "features": json.dumps(
                        features,
                        ensure_ascii=False,
                    ),
                    "modelo_version": model_version,
                },
            )
            return int(result.scalar_one())
    finally:
        engine.dispose()


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Carga un cliente de gold.gold_ml en gold.score_input "
            "usando exactamente las features registradas en model_metadata.json."
        )
    )
    parser.add_argument(
        "--id",
        type=int,
        required=True,
        help="ID del cliente a enviar a scoring.",
    )
    args = parser.parse_args()

    print("=" * 72)
    print("CARGA DE SCORE INPUT")
    print("=" * 72)

    model_features = load_model_features()
    row, _ = load_customer(args.id)

    score_input_id = insert_score_input(
        row,
        model_features,
        model_version=None,
    )

    print(f"score_input_id creado: {score_input_id}")
    print(f"Cliente: {args.id}")
    print(f"Features guardadas: {len(model_features)}")
    print("Estado: pendiente de scoring")
    print("=" * 72)


if __name__ == "__main__":
    main()
