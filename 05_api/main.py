import json
import os
from functools import lru_cache
from pathlib import Path

import joblib
import pandas as pd
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import create_engine, text

load_dotenv()
ROOT = Path(__file__).resolve().parents[1]
MODEL_PATH = ROOT / "04_ml" / "models" / "model.pkl"
METADATA_PATH = ROOT / "04_ml" / "models" / "model_metadata.json"

app = FastAPI(title="Credit Risk API", version="2.0.0")


def get_engine():
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("No se encontro DATABASE_URL en el entorno")
    return create_engine(database_url, pool_pre_ping=True)


@lru_cache(maxsize=1)
def get_model_bundle():
    if not MODEL_PATH.exists() or not METADATA_PATH.exists():
        raise RuntimeError("Faltan model.pkl o model_metadata.json")
    model = joblib.load(MODEL_PATH)
    metadata = json.loads(METADATA_PATH.read_text(encoding="utf-8"))
    return model, metadata


def risk_level(probability: float) -> str:
    if probability < 0.20:
        return "BAJO"
    if probability < 0.40:
        return "MEDIO"
    if probability < 0.70:
        return "ALTO"
    return "CRITICO"


def recommendation(features: dict, risk: str) -> str:
    recs = []
    if risk == "CRITICO":
        recs.append("Priorizar la atencion preventiva y revisar la capacidad de pago antes de ampliar exposicion crediticia.")
    elif risk == "ALTO":
        recs.append("Realizar seguimiento preventivo y revisar el comportamiento reciente de pago.")
    elif risk == "MEDIO":
        recs.append("Mantener seguimiento periodico y revisar señales tempranas de deterioro.")
    else:
        recs.append("Mantener seguimiento estandar de acuerdo con la politica de riesgo.")

    def number(name, default=0.0):
        try:
            value = features.get(name, default)
            return default if value is None else float(value)
        except (TypeError, ValueError):
            return default

    if number("recent_delay_months") >= 2 or number("pay_max_delay") >= 3:
        recs.append("Revisar los atrasos recientes y establecer contacto preventivo cuando corresponda.")
    if number("consecutive_delay_months") >= 2:
        recs.append("Evaluar medidas de normalizacion por la presencia de retrasos consecutivos.")
    ratio = features.get("payment_bill_ratio_total")
    if ratio is not None:
        try:
            if float(ratio) < 0.50:
                recs.append("Revisar la relacion historica entre pagos y facturacion.")
        except (TypeError, ValueError):
            pass
    return " ".join(recs)


class PredictionResponse(BaseModel):
    id: int
    model_version: str
    probability_default: float
    prediction: int
    risk_level: str
    recommendation: str
    threshold: float


@app.get("/health")
def health():
    model, metadata = get_model_bundle()
    return {
        "status": "ok",
        "model_loaded": model is not None,
        "model_version": metadata.get("model_version"),
        "algorithm": metadata.get("algorithm"),
    }


@app.get("/portfolio/summary")
def portfolio_summary():
    query = text("""
        SELECT
            COUNT(*)::int AS total,
            AVG(probability_default)::float AS pd_promedio,
            COUNT(*) FILTER (WHERE prediction = 1)::int AS prediccion_1,
            COUNT(*) FILTER (WHERE risk_level = 'BAJO')::int AS bajo,
            COUNT(*) FILTER (WHERE risk_level = 'MEDIO')::int AS medio,
            COUNT(*) FILTER (WHERE risk_level = 'ALTO')::int AS alto,
            COUNT(*) FILTER (WHERE risk_level = 'CRITICO')::int AS critico
        FROM gold.vw_portfolio_scoring_current
    """)
    engine = get_engine()
    try:
        with engine.connect() as conn:
            row = conn.execute(query).mappings().one()
            return dict(row)
    finally:
        engine.dispose()


@app.get("/portfolio")
def portfolio(
    risk: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
):
    where = "WHERE risk_level = :risk" if risk else ""
    query = text(f"""
        SELECT *
        FROM gold.vw_portfolio_scoring_current
        {where}
        ORDER BY probability_default DESC, id
        LIMIT :limit OFFSET :offset
    """)
    params = {"limit": limit, "offset": offset}
    if risk:
        params["risk"] = risk.upper()
    engine = get_engine()
    try:
        df = pd.read_sql_query(query, engine, params=params)
        return df.to_dict(orient="records")
    finally:
        engine.dispose()


@app.get("/portfolio/{customer_id}")
def portfolio_customer(customer_id: int):
    query = text("SELECT * FROM gold.vw_portfolio_scoring_current WHERE id = :id")
    engine = get_engine()
    try:
        with engine.connect() as conn:
            row = conn.execute(query, {"id": customer_id}).mappings().first()
        if row is None:
            raise HTTPException(status_code=404, detail="Cliente no encontrado en la cartera puntuada")
        return dict(row)
    finally:
        engine.dispose()


@app.post("/predict/{customer_id}", response_model=PredictionResponse)
def predict(customer_id: int):
    model, metadata = get_model_bundle()
    features = list(metadata["features"])
    query = text("SELECT * FROM gold.gold_ml WHERE id = :id")
    engine = get_engine()
    try:
        df = pd.read_sql_query(query, engine, params={"id": customer_id})
    finally:
        engine.dispose()
    if df.empty:
        raise HTTPException(status_code=404, detail="Cliente no encontrado en gold.gold_ml")
    missing = [c for c in features if c not in df.columns]
    if missing:
        raise HTTPException(status_code=500, detail=f"Faltan features: {missing}")
    probability = float(model.predict_proba(df[features])[:, 1][0])
    threshold = float(metadata["risk_threshold"])
    pred = int(probability >= threshold)
    risk = risk_level(probability)
    rec = recommendation(df.iloc[0].to_dict(), risk)
    return PredictionResponse(
        id=customer_id,
        model_version=str(metadata["model_version"]),
        probability_default=probability,
        prediction=pred,
        risk_level=risk,
        recommendation=rec,
        threshold=threshold,
    )
