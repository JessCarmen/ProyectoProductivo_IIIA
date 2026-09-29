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
    if probability < 0.20:
        return "BAJO"
    if probability < 0.40:
        return "MEDIO"
    if probability < 0.70:
        return "ALTO"
    return "CRITICO"


def build_recommendations(row, probability):
    risk = classify_risk(probability)
    recommendations = []

    recent_delay = row.get("recent_delay_months", 0) or 0
    max_delay = row.get("pay_max_delay", 0) or 0
    consecutive = row.get("consecutive_delay_months", 0) or 0
    ratio = row.get("payment_bill_ratio_total")

    if risk == "CRITICO":
        recommendations.append("Priorizar la atencion preventiva y revisar la capacidad de pago antes de ampliar la exposicion crediticia.")
    elif risk == "ALTO":
        recommendations.append("Realizar seguimiento preventivo y revisar el comportamiento reciente de pago.")
    elif risk == "MEDIO":
        recommendations.append("Mantener seguimiento periodico y revisar señales tempranas de deterioro.")
    else:
        recommendations.append("Mantener seguimiento estandar de acuerdo con la politica de riesgo.")

    if recent_delay >= 2 or max_delay >= 3:
        recommendations.append("Revisar los atrasos recientes y establecer contacto preventivo cuando corresponda.")
    if consecutive >= 2:
        recommendations.append("Evaluar medidas de normalizacion por la presencia de retrasos consecutivos.")
    if ratio is not None and not pd.isna(ratio) and float(ratio) < 0.50:
        recommendations.append("Revisar la relacion historica entre pagos y facturacion.")

    return recommendations


def main():
    parser = argparse.ArgumentParser(description="Genera recomendaciones mediante reglas de negocio.")
    parser.add_argument("--id", type=int, required=True)
    args = parser.parse_args()

    if not MODEL_PATH.exists() or not METADATA_PATH.exists():
        raise FileNotFoundError("Faltan model.pkl o model_metadata.json. Ejecuta 04_train.py.")

    metadata = json.loads(METADATA_PATH.read_text(encoding="utf-8"))
    model = joblib.load(MODEL_PATH)
    customer = load_customer(args.id)
    if customer.empty:
        raise ValueError(f"No se encontro el cliente con ID {args.id}")

    row = customer.iloc[0]
    probability = float(model.predict_proba(customer[metadata["features"]])[0, 1])
    threshold = float(metadata.get("risk_threshold", 0.50))
    prediction = int(probability >= threshold)
    risk = classify_risk(probability)
    recommendations = build_recommendations(row, probability)

    print("=" * 60)
    print("MOTOR PRESCRIPTIVO")
    print("=" * 60)
    print(f"Cliente ID      : {args.id}")
    print(f"Probabilidad    : {probability:.4%}")
    print(f"Clasificacion   : {prediction}")
    print(f"Nivel de riesgo : {risk}")
    print("\nRecomendaciones:")
    for i, rec in enumerate(recommendations, 1):
        print(f"{i}. {rec}")
    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
