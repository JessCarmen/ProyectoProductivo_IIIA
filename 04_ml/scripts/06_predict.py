import argparse
import json
import os
from pathlib import Path

import joblib
import pandas as pd
import psycopg
from dotenv import load_dotenv

load_dotenv()
ROOT = Path(__file__).resolve().parents[2]
MODEL_PATH = ROOT / "04_ml/models/model.pkl"
METADATA_PATH = ROOT / "04_ml/models/model_metadata.json"


def get_connection():
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("No se encontro DATABASE_URL en .env")
    return psycopg.connect(database_url)


def load_customer(customer_id):
    with get_connection() as conn:
        return pd.read_sql_query("SELECT * FROM gold.gold_ml WHERE id = %s", conn, params=(customer_id,))


def classify_risk(probability):
    # Default visual mapping; final thresholds for binary prediction come from model_metadata.
    if probability < 0.20:
        return "BAJO"
    if probability < 0.40:
        return "MEDIO"
    if probability < 0.70:
        return "ALTO"
    return "CRITICO"


def main():
    parser = argparse.ArgumentParser(description="Prediccion de default para un cliente de gold.gold_ml")
    parser.add_argument("--id", type=int, required=True)
    args = parser.parse_args()

    if not MODEL_PATH.exists() or not METADATA_PATH.exists():
        raise FileNotFoundError("Faltan model.pkl o model_metadata.json. Ejecuta 04_train.py.")

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
