import argparse
import json
import os
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

ROOT = Path(__file__).resolve().parents[2]
MODEL_PATH = ROOT / "04_ml" / "models" / "model.pkl"
METADATA_PATH = ROOT / "04_ml" / "models" / "model_metadata.json"
EXPECTED_PORTFOLIO_ROWS = 33377
DEFAULT_BATCH_SIZE = 1000


def get_engine():
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("No se encontro DATABASE_URL en .env")
    return create_engine(database_url, pool_pre_ping=True)


def load_model_and_metadata():
    if not MODEL_PATH.exists():
        raise FileNotFoundError(f"No existe el modelo: {MODEL_PATH}")
    if not METADATA_PATH.exists():
        raise FileNotFoundError(f"No existe metadata: {METADATA_PATH}")

    model = joblib.load(MODEL_PATH)
    metadata = json.loads(METADATA_PATH.read_text(encoding="utf-8"))
    features = metadata.get("features")
    if not features:
        raise RuntimeError("model_metadata.json no contiene features")
    return model, metadata, list(features)


def load_portfolio():
    engine = get_engine()
    try:
        return pd.read_sql_query(
            "SELECT * FROM gold.gold_ml ORDER BY id;",
            engine,
        )
    finally:
        engine.dispose()


def risk_level(probability):
    if probability < 0.20:
        return "BAJO"
    if probability < 0.40:
        return "MEDIO"
    if probability < 0.70:
        return "ALTO"
    return "CRITICO"


def recommendation(row, risk):
    recommendations = []

    if risk == "CRITICO":
        recommendations.append(
            "Priorizar la atencion preventiva y revisar la capacidad de pago "
            "antes de ampliar exposicion crediticia."
        )
    elif risk == "ALTO":
        recommendations.append(
            "Realizar seguimiento preventivo y revisar el comportamiento reciente de pago."
        )
    elif risk == "MEDIO":
        recommendations.append(
            "Mantener seguimiento periodico y revisar senales tempranas de deterioro."
        )
    else:
        recommendations.append(
            "Mantener seguimiento estandar de acuerdo con la politica de riesgo."
        )

    recent_delay = row.get("recent_delay_months", 0)
    max_delay = row.get("pay_max_delay", 0)
    consecutive = row.get("consecutive_delay_months", 0)
    ratio = row.get("payment_bill_ratio_total")

    recent_delay = 0.0 if pd.isna(recent_delay) else float(recent_delay)
    max_delay = 0.0 if pd.isna(max_delay) else float(max_delay)
    consecutive = 0.0 if pd.isna(consecutive) else float(consecutive)

    if recent_delay >= 2 or max_delay >= 3:
        recommendations.append(
            "Revisar los atrasos recientes y establecer contacto preventivo cuando corresponda."
        )

    if consecutive >= 2:
        recommendations.append(
            "Evaluar medidas de normalizacion por la presencia de retrasos consecutivos."
        )

    if ratio is not None and not pd.isna(ratio) and float(ratio) < 0.50:
        recommendations.append(
            "Revisar la relacion historica entre pagos y facturacion."
        )

    return " ".join(recommendations)


def json_value(value):
    if value is None or pd.isna(value):
        return None
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    return value


def prepare_scoring(portfolio, model, metadata, features):
    missing = [feature for feature in features if feature not in portfolio.columns]
    if missing:
        raise RuntimeError(f"Faltan features en gold.gold_ml: {missing}")

    X = portfolio[features].copy()
    probability = model.predict_proba(X)[:, 1]
    threshold = float(metadata["risk_threshold"])

    scored = portfolio[["id"] + [c for c in [
        "recent_delay_months",
        "pay_max_delay",
        "consecutive_delay_months",
        "payment_bill_ratio_total",
    ] if c in portfolio.columns]].copy()

    scored["probability_default"] = probability
    scored["prediction"] = (probability >= threshold).astype(int)
    scored["risk_level"] = scored["probability_default"].map(risk_level)
    scored["recommendation"] = scored.apply(
        lambda row: recommendation(row, row["risk_level"]),
        axis=1,
    )

    return scored, threshold


def clear_existing_scoring(connection):
    connection.execute(text("DELETE FROM gold.score_output;"))
    connection.execute(text("DELETE FROM gold.score_input;"))


def insert_batch(connection, source_batch, scored_batch, features, metadata, threshold):
    model_version = metadata.get("model_version", "unknown")

    payload = []
    for _, row in source_batch.iterrows():
        feature_values = {
            feature: json_value(row[feature])
            for feature in features
        }
        payload.append({
            "id": int(row["id"]),
            "features": feature_values,
            "modelo_version": model_version,
        })

    input_query = text("""
        WITH payload AS (
            SELECT *
            FROM jsonb_to_recordset(CAST(:payload AS jsonb))
            AS x(id bigint, features jsonb, modelo_version text)
        )
        INSERT INTO gold.score_input (
            id, features, modelo_version, procesado
        )
        SELECT id, features, modelo_version, TRUE
        FROM payload
        RETURNING score_input_id, id;
    """)

    returned = connection.execute(
        input_query,
        {"payload": json.dumps(payload, ensure_ascii=False)},
    ).fetchall()

    score_input_by_id = {int(row.id): int(row.score_input_id) for row in returned}
    if len(score_input_by_id) != len(source_batch):
        raise RuntimeError("No se generaron todos los score_input_id del lote")

    output_rows = []
    for _, row in scored_batch.iterrows():
        customer_id = int(row["id"])
        explanation = {
            "risk_logic": "probability_to_risk_rules",
            "risk_level": row["risk_level"],
            "model_version": model_version,
            "classification_threshold": threshold,
            "scoring_scope": "portfolio_33377",
        }
        output_rows.append({
            "score_input_id": score_input_by_id[customer_id],
            "id": customer_id,
            "modelo_version": model_version,
            "probability_default": float(row["probability_default"]),
            "prediction": int(row["prediction"]),
            "risk_level": row["risk_level"],
            "recommendation": row["recommendation"],
            "explanation": json.dumps(explanation, ensure_ascii=False),
        })

    output_query = text("""
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
            CAST(:explanation AS jsonb)
        );
    """)
    connection.execute(output_query, output_rows)


def validate_final(connection, expected_rows):
    total_input = connection.execute(
        text("SELECT COUNT(*) FROM gold.score_input;")
    ).scalar_one()
    total_output = connection.execute(
        text("SELECT COUNT(*) FROM gold.score_output;")
    ).scalar_one()
    distinct_output = connection.execute(
        text("SELECT COUNT(DISTINCT id) FROM gold.score_output;")
    ).scalar_one()
    null_outputs = connection.execute(text("""
        SELECT COUNT(*)
        FROM gold.score_output
        WHERE probability_default IS NULL
           OR prediction IS NULL
           OR risk_level IS NULL
           OR recommendation IS NULL
           OR score_input_id IS NULL;
    """)).scalar_one()

    if total_input != expected_rows:
        raise RuntimeError(
            f"score_input tiene {total_input} filas; se esperaban {expected_rows}"
        )
    if total_output != expected_rows:
        raise RuntimeError(
            f"score_output tiene {total_output} filas; se esperaban {expected_rows}"
        )
    if distinct_output != expected_rows:
        raise RuntimeError(
            f"score_output tiene {distinct_output} IDs distintos; se esperaban {expected_rows}"
        )
    if null_outputs != 0:
        raise RuntimeError(
            f"score_output tiene {null_outputs} filas incompletas"
        )

    risk_counts = connection.execute(text("""
        SELECT risk_level, COUNT(*) AS clientes
        FROM gold.score_output
        GROUP BY risk_level
        ORDER BY risk_level;
    """)).fetchall()

    prediction_counts = connection.execute(text("""
        SELECT prediction, COUNT(*) AS clientes
        FROM gold.score_output
        GROUP BY prediction
        ORDER BY prediction;
    """)).fetchall()

    return {
        "score_input": int(total_input),
        "score_output": int(total_output),
        "distinct_ids": int(distinct_output),
        "null_outputs": int(null_outputs),
        "risk_counts": [(row.risk_level, int(row.clientes)) for row in risk_counts],
        "prediction_counts": [(int(row.prediction), int(row.clientes)) for row in prediction_counts],
    }


def main():
    parser = argparse.ArgumentParser(
        description="Scoring masivo de los 33,377 registros de gold.gold_ml."
    )
    parser.add_argument(
        "--replace-existing",
        action="store_true",
        help="Borra score_input/score_output actuales antes de generar la cartera completa.",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=DEFAULT_BATCH_SIZE,
        help=f"Tamano de lote de insercion. Default: {DEFAULT_BATCH_SIZE}.",
    )
    args = parser.parse_args()

    print("=" * 72)
    print("SCORING MASIVO DE CARTERA - 33,377 REGISTROS")
    print("=" * 72)

    model, metadata, features = load_model_and_metadata()
    portfolio = load_portfolio()

    print(f"Registros GOLD_ML: {len(portfolio):,}")
    print(f"Modelo: {metadata.get('model_version', 'unknown')} / {metadata.get('algorithm', 'unknown')}")
    print(f"Features del modelo: {len(features)}")
    print(f"Threshold binario: {float(metadata['risk_threshold']):.3f}")

    if len(portfolio) != EXPECTED_PORTFOLIO_ROWS:
        raise RuntimeError(
            f"Se esperaban {EXPECTED_PORTFOLIO_ROWS:,} registros en gold.gold_ml "
            f"y se encontraron {len(portfolio):,}. No se ejecuta el scoring."
        )
    if portfolio["id"].isna().any():
        raise RuntimeError("gold.gold_ml contiene IDs nulos")
    if portfolio["id"].duplicated().any():
        raise RuntimeError("gold.gold_ml contiene IDs duplicados")

    scored, threshold = prepare_scoring(portfolio, model, metadata, features)

    engine = get_engine()
    try:
        with engine.begin() as connection:
            existing_output = connection.execute(
                text("SELECT COUNT(*) FROM gold.score_output;")
            ).scalar_one()

            if existing_output and not args.replace_existing:
                raise RuntimeError(
                    f"gold.score_output ya contiene {existing_output} registros. "
                    "Para generar el score_output final de 33,377 filas usa "
                    "--replace-existing."
                )

            if args.replace_existing:
                print("Limpiando scoring de prueba anterior...")
                clear_existing_scoring(connection)

            total = len(portfolio)
            for start in range(0, total, args.batch_size):
                end = min(start + args.batch_size, total)
                source_batch = portfolio.iloc[start:end]
                scored_batch = scored.iloc[start:end]
                insert_batch(
                    connection,
                    source_batch,
                    scored_batch,
                    features,
                    metadata,
                    threshold,
                )
                print(f"Procesados: {end:,}/{total:,}")

            validation = validate_final(connection, EXPECTED_PORTFOLIO_ROWS)
    finally:
        engine.dispose()

    print("\n" + "=" * 72)
    print("VALIDACION FINAL")
    print("=" * 72)
    print(f"score_input : {validation['score_input']:,}")
    print(f"score_output: {validation['score_output']:,}")
    print(f"IDs unicos  : {validation['distinct_ids']:,}")
    print(f"Filas incompletas: {validation['null_outputs']}")
    print("Distribucion por riesgo:", validation["risk_counts"])
    print("Distribucion 0/1:", validation["prediction_counts"])
    print("\nSCORING MASIVO FINALIZADO CORRECTAMENTE")


if __name__ == "__main__":
    main()
