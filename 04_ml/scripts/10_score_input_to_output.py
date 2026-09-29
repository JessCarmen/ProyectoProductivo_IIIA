import json
import os
from pathlib import Path

import joblib
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()
ROOT = Path(__file__).resolve().parents[2]
MODEL_PATH = ROOT / "04_ml" / "models" / "model.pkl"
METADATA_PATH = ROOT / "04_ml" / "models" / "model_metadata.json"


def get_engine():
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("No se encontro DATABASE_URL en .env")

    return create_engine(
        database_url,
        pool_pre_ping=True,
    )


def load_pending_inputs():
    engine = get_engine()

    query = text("""
        SELECT
            score_input_id,
            id,
            fecha_score,
            features,
            modelo_version,
            procesado
        FROM gold.score_input
        WHERE COALESCE(procesado, FALSE) = FALSE
        ORDER BY score_input_id
    """)

    try:
        return pd.read_sql_query(query, engine)
    finally:
        engine.dispose()


def load_model_and_metadata():
    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            f"No existe el modelo: {MODEL_PATH}. Ejecuta 04_train.py primero."
        )

    if not METADATA_PATH.exists():
        raise FileNotFoundError(
            f"No existe metadata: {METADATA_PATH}. Ejecuta 04_train.py primero."
        )

    model = joblib.load(MODEL_PATH)
    metadata = json.loads(
        METADATA_PATH.read_text(encoding="utf-8")
    )

    features = metadata.get("features")
    if not features:
        raise RuntimeError(
            "model_metadata.json no contiene la lista de features del modelo."
        )

    return model, metadata, list(features)


def normalize_features(raw_features):
    if raw_features is None:
        return {}

    if isinstance(raw_features, dict):
        return raw_features

    if isinstance(raw_features, str):
        try:
            parsed = json.loads(raw_features)
        except json.JSONDecodeError as exc:
            raise RuntimeError(
                "El campo features de score_input no contiene JSON valido."
            ) from exc

        if not isinstance(parsed, dict):
            raise RuntimeError(
                "El campo features debe contener un objeto JSON."
            )

        return parsed

    raise RuntimeError(
        f"Tipo no soportado para features: {type(raw_features).__name__}"
    )


def risk_level(probability):
    # Estos rangos corresponden a la clasificacion empresarial actual del proyecto.
    if probability < 0.20:
        return "BAJO"
    if probability < 0.40:
        return "MEDIO"
    if probability < 0.70:
        return "ALTO"
    return "CRITICO"


def recommendation(features, risk):
    recommendations = []

    recent_delay = features.get("recent_delay_months", 0) or 0
    max_delay = features.get("pay_max_delay", 0) or 0
    consecutive = features.get("consecutive_delay_months", 0) or 0
    ratio = features.get("payment_bill_ratio_total")

    if risk == "CRITICO":
        recommendations.append(
            "Priorizar la atencion preventiva y revisar la capacidad de pago "
            "antes de ampliar exposicion crediticia."
        )
    elif risk == "ALTO":
        recommendations.append(
            "Realizar seguimiento preventivo y revisar el comportamiento "
            "reciente de pago."
        )
    elif risk == "MEDIO":
        recommendations.append(
            "Mantener seguimiento periodico y revisar señales tempranas "
            "de deterioro."
        )
    else:
        recommendations.append(
            "Mantener seguimiento estandar de acuerdo con la politica de riesgo."
        )

    try:
        recent_delay = float(recent_delay)
    except (TypeError, ValueError):
        recent_delay = 0.0

    try:
        max_delay = float(max_delay)
    except (TypeError, ValueError):
        max_delay = 0.0

    try:
        consecutive = float(consecutive)
    except (TypeError, ValueError):
        consecutive = 0.0

    if recent_delay >= 2 or max_delay >= 3:
        recommendations.append(
            "Revisar los atrasos recientes y establecer contacto preventivo "
            "cuando corresponda."
        )

    if consecutive >= 2:
        recommendations.append(
            "Evaluar medidas de normalizacion por la presencia de retrasos consecutivos."
        )

    if ratio is not None:
        try:
            ratio_value = float(ratio)
            if ratio_value < 0.50:
                recommendations.append(
                    "Revisar la relacion historica entre pagos y facturacion."
                )
        except (TypeError, ValueError):
            pass

    return " ".join(recommendations)


def process_input(item, model, metadata, model_features):
    score_input_id = int(item["score_input_id"])
    customer_id = int(item["id"])
    features = normalize_features(item["features"])

    missing = [
        feature
        for feature in model_features
        if feature not in features
    ]

    if missing:
        raise RuntimeError(
            f"Faltan features para score_input_id={score_input_id}, "
            f"cliente={customer_id}: {missing}"
        )

    row = {
        feature: features[feature]
        for feature in model_features
    }

    X = pd.DataFrame([row], columns=model_features)

    probability = float(
        model.predict_proba(X)[0, 1]
    )

    threshold = float(
        metadata.get("risk_threshold", 0.50)
    )

    prediction = int(
        probability >= threshold
    )

    risk = risk_level(probability)
    rec = recommendation(features, risk)
    version = metadata.get("model_version", "unknown")

    return {
        "score_input_id": score_input_id,
        "id": customer_id,
        "modelo_version": version,
        "probability_default": probability,
        "prediction": prediction,
        "risk_level": risk,
        "recommendation": rec,
        "explanation": {
            "risk_logic": "probability_to_risk_rules",
            "risk_level": risk,
            "model_version": version,
            "classification_threshold": threshold,
        },
    }


def save_output(result):
    engine = get_engine()

    insert_query = text("""
        INSERT INTO gold.score_output (
            score_input_id,
            id,
            modelo_version,
            probability_default,
            prediction,
            risk_level,
            recommendation,
            explanation
        )
        VALUES (
            :score_input_id,
            :id,
            :modelo_version,
            :probability_default,
            :prediction,
            :risk_level,
            :recommendation,
            CAST(:explanation AS JSONB)
        )
        ON CONFLICT DO NOTHING
    """)

    update_query = text("""
        UPDATE gold.score_input
        SET
            procesado = TRUE,
            modelo_version = :modelo_version
        WHERE score_input_id = :score_input_id
    """)

    try:
        with engine.begin() as connection:
            connection.execute(
                insert_query,
                {
                    "score_input_id": result["score_input_id"],
                    "id": result["id"],
                    "modelo_version": result["modelo_version"],
                    "probability_default": result["probability_default"],
                    "prediction": result["prediction"],
                    "risk_level": result["risk_level"],
                    "recommendation": result["recommendation"],
                    "explanation": json.dumps(
                        result["explanation"],
                        ensure_ascii=False,
                    ),
                },
            )

            connection.execute(
                update_query,
                {
                    "modelo_version": result["modelo_version"],
                    "score_input_id": result["score_input_id"],
                },
            )
    finally:
        engine.dispose()


def main():
    print("=" * 72)
    print("SCORING: SCORE_INPUT -> SCORE_OUTPUT")
    print("=" * 72)

    model, metadata, model_features = load_model_and_metadata()
    pending = load_pending_inputs()

    if pending.empty:
        print("No hay registros pendientes en gold.score_input.")
        return

    print(f"Registros pendientes: {len(pending)}")
    print(f"Modelo: {metadata.get('model_version', 'unknown')}")
    print(f"Features esperadas: {len(model_features)}")

    processed = 0

    for _, item in pending.iterrows():
        result = process_input(
            item,
            model,
            metadata,
            model_features,
        )

        save_output(result)
        processed += 1

        print(
            f"Cliente {result['id']} | "
            f"PD={result['probability_default']:.4f} | "
            f"Pred={result['prediction']} | "
            f"Riesgo={result['risk_level']}"
        )

    print("\n" + "=" * 72)
    print(f"Registros procesados: {processed}")
    print("Flujo score_input -> score_output finalizado.")
    print("=" * 72)


if __name__ == "__main__":
    main()
