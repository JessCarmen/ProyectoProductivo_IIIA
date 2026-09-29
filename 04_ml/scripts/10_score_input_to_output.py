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


def risk_level(probability):
    if probability < 0.20:
        return "BAJO"
    if probability < 0.40:
        return "MEDIO"
    if probability < 0.70:
        return "ALTO"
    return "CRITICO"


def recommendation(row, probability):
    risk = risk_level(probability)
    recs = []
    recent_delay = row.get("recent_delay_months", 0) or 0
    max_delay = row.get("pay_max_delay", 0) or 0
    consecutive = row.get("consecutive_delay_months", 0) or 0
    ratio = row.get("payment_bill_ratio_total")

    if risk == "CRITICO":
        recs.append("Priorizar la atencion preventiva y revisar la capacidad de pago antes de ampliar exposicion crediticia.")
    elif risk == "ALTO":
        recs.append("Realizar seguimiento preventivo y revisar el comportamiento reciente de pago.")
    elif risk == "MEDIO":
        recs.append("Mantener seguimiento periodico y revisar señales tempranas de deterioro.")
    else:
        recs.append("Mantener seguimiento estandar de acuerdo con la politica de riesgo.")
    if recent_delay >= 2 or max_delay >= 3:
        recs.append("Revisar los atrasos recientes y establecer contacto preventivo cuando corresponda.")
    if consecutive >= 2:
        recs.append("Evaluar medidas de normalizacion por la presencia de retrasos consecutivos.")
    if ratio is not None and not pd.isna(ratio) and float(ratio) < 0.50:
        recs.append("Revisar la relacion historica entre pagos y facturacion.")
    return " ".join(recs)


def main():
    if not MODEL_PATH.exists() or not METADATA_PATH.exists():
        raise FileNotFoundError("Faltan model.pkl o model_metadata.json. Ejecuta 04_train.py.")

    metadata = json.loads(METADATA_PATH.read_text(encoding="utf-8"))
    model = joblib.load(MODEL_PATH)
    features = metadata["features"]
    version = metadata.get("model_version", "unknown")

    with get_connection() as conn:
        pending = pd.read_sql_query(
            "SELECT score_input_id, id, features FROM gold.score_input WHERE COALESCE(procesado, FALSE) = FALSE ORDER BY score_input_id",
            conn,
        )

        if pending.empty:
            print("No hay registros pendientes en gold.score_input.")
            return

        for _, item in pending.iterrows():
            raw_features = item["features"] or {}
            row = pd.Series(raw_features)
            missing = [c for c in features if c not in row.index]
            if missing:
                # Fallback for demo cases: recover the features from gold_ml by id.
                gold_row = pd.read_sql_query("SELECT * FROM gold.gold_ml WHERE id = %s", conn, params=(int(item["id"]),))
                if gold_row.empty:
                    raise RuntimeError(f"No hay features suficientes para score_input_id={item['score_input_id']}: faltan {missing}")
                row = gold_row.iloc[0]

            X = pd.DataFrame([{c: row.get(c) for c in features}])
            probability = float(model.predict_proba(X)[0, 1])
            threshold = float(metadata.get("risk_threshold", 0.50))
            prediction = int(probability >= threshold)
            risk = risk_level(probability)
            rec = recommendation(row, probability)
            explanation = {
                "risk_logic": "probability_to_risk_rules",
                "risk_level": risk,
                "model_version": version,
            }

            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO gold.score_output
                        (score_input_id, id, modelo_version, probability_default, prediction, risk_level, recommendation, explanation)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s::jsonb)
                    """,
                    (
                        int(item["score_input_id"]),
                        int(item["id"]),
                        version,
                        probability,
                        prediction,
                        risk,
                        rec,
                        json.dumps(explanation, ensure_ascii=False),
                    ),
                )
                cur.execute(
                    "UPDATE gold.score_input SET procesado = TRUE, modelo_version = %s WHERE score_input_id = %s",
                    (version, int(item["score_input_id"])),
                )
        conn.commit()

    print(f"Registros procesados: {len(pending)}")
    print("Flujo score_input -> score_output finalizado.")


if __name__ == "__main__":
    main()
