import argparse
import json
import os
from pathlib import Path

import joblib
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()
ROOT = Path(__file__).resolve().parents[2]
MODEL_PATH = ROOT / "04_ml/models/model.pkl"
METADATA_PATH = ROOT / "04_ml/models/model_metadata.json"


def get_engine():
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("No se encontro DATABASE_URL en .env")
    return create_engine(database_url, pool_pre_ping=True)


def load_customer(customer_id):
    engine = get_engine()
    query = text("SELECT * FROM gold.gold_ml WHERE id = :customer_id")
    try:
        return pd.read_sql_query(query, engine, params={"customer_id": customer_id})
    finally:
        engine.dispose()


def classify_risk(probability):
    # Umbrales operativos provisionales para el nivel de riesgo.
    # El umbral binario del modelo proviene de model_metadata.json.
    if probability < 0.20:
        return "BAJO"
    if probability < 0.40:
        return "MEDIO"
    if probability < 0.70:
        return "ALTO"
    return "CRITICO"


def main():
    parser = argparse.ArgumentParser(
        description="Prediccion de default para un cliente de gold.gold_ml"
    )
    parser.add_argument("--id", type=int, required=True)
    args = parser.parse_args()

    if not MODEL_PATH.exists() or not METADATA_PATH.exists():
        raise FileNotFoundError(
            "Faltan model.pkl o model_metadata.json. Ejecuta 04_train.py."
        )

    metadata = json.loads(METADATA_PATH.read_text(encoding="utf-8"))
    model = joblib.load(MODEL_PATH)
    customer = load_customer(args.id)

    if customer.empty:
        raise ValueError(f"No se encontro el cliente con ID {args.id}")

    X = customer[metadata["features"]]
    probability = float(model.predict_proba(X)[0, 1])
    threshold = float(metadata.get("risk_threshold", 0.50))
    prediction = int(probability >= threshold)

    print("=" * 60)
    print("PREDICCION DE RIESGO CREDITICIO")
    print("=" * 60)
    print(f"Cliente ID       : {args.id}")
    print(f"Probabilidad     : {probability:.4%}")
    print(f"Umbral binario   : {threshold:.4%}")
    print(f"Clasificacion    : {prediction}")
    print(f"Nivel de riesgo  : {classify_risk(probability)}")
    print("=" * 60)


if __name__ == "__main__":
    main()
