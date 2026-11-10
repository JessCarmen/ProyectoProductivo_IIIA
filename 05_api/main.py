import os
import logging

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from fastapi.encoders import jsonable_encoder
from sqlalchemy import create_engine, text


# ============================================================
# CONFIGURACION
# ============================================================

load_dotenv()
logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL no esta configurado. "
        "Definelo en .env localmente o en Environment Variables en Render."
    )


# ============================================================
# CONEXION A SUPABASE / POSTGRESQL
# ============================================================

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_size=2,
    max_overflow=1,
    pool_recycle=300,
)


# ============================================================
# FASTAPI
# ============================================================

app = FastAPI(
    title="Proyecto Productivo IIIA - API de Riesgo Crediticio",
    description=(
        "API publica para consultar los resultados del scoring crediticio "
        "persistidos en la capa Gold de Supabase."
    ),
    version="1.0.0",
)


MODEL_VERSION = "v20260929_064028"

VALID_RISK_LEVELS = {
    "BAJO",
    "MEDIO",
    "ALTO",
    "CRITICO",
}


# ============================================================
# HELPERS
# ============================================================

def serialize_row(row):
    """
    Convierte una fila SQLAlchemy en un objeto compatible con JSON.
    Maneja automaticamente Decimal, datetime y otros tipos.
    """
    if row is None:
        return None

    return jsonable_encoder(dict(row))


def serialize_rows(rows):
    """
    Convierte varias filas SQLAlchemy en una lista JSON.
    """
    return [
        jsonable_encoder(dict(row))
        for row in rows
    ]


# ============================================================
# ROOT
# ============================================================

@app.get("/")
def root():
    return {
        "status": "ok",
        "service": "Proyecto Productivo IIIA API",
        "description": "API publica de scoring de riesgo crediticio",
        "model_version": MODEL_VERSION,
        "docs": "/docs",
        "health": "/health",
    }


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/health")
def health():
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))

        return {
            "status": "ok",
            "database": "connected",
            "mode": "portfolio_scoring",
            "model_version": MODEL_VERSION,
        }

    except Exception:
        logger.exception("Error en consulta de FastAPI")
        raise HTTPException(
            status_code=503,
            detail="No fue posible conectar con la base de datos.",
        )


# ============================================================
# RESUMEN GENERAL DE CARTERA
# ============================================================

@app.get("/portfolio/summary")
def portfolio_summary():
    query = text(
        """
        SELECT
            COUNT(*) AS total,
            AVG(probability_default) AS pd_promedio,

            COUNT(*) FILTER (
                WHERE prediction = 0
            ) AS prediction_0,

            COUNT(*) FILTER (
                WHERE prediction = 1
            ) AS prediction_1,

            COUNT(*) FILTER (
                WHERE risk_level = 'BAJO'
            ) AS bajo,

            COUNT(*) FILTER (
                WHERE risk_level = 'MEDIO'
            ) AS medio,

            COUNT(*) FILTER (
                WHERE risk_level = 'ALTO'
            ) AS alto,

            COUNT(*) FILTER (
                WHERE risk_level = 'CRITICO'
            ) AS critico,

            MIN(probability_default) AS pd_min,

            MAX(probability_default) AS pd_max

        FROM gold.vw_portfolio_scoring_current;
        """
    )

    try:
        with engine.connect() as conn:
            row = conn.execute(query).mappings().one()

        return {
            "total": int(row["total"]),
            "pd_promedio": float(row["pd_promedio"]),
            "pd_min": float(row["pd_min"]),
            "pd_max": float(row["pd_max"]),
            "prediction_0": int(row["prediction_0"]),
            "prediction_1": int(row["prediction_1"]),
            "bajo": int(row["bajo"]),
            "medio": int(row["medio"]),
            "alto": int(row["alto"]),
            "critico": int(row["critico"]),
            "model_version": MODEL_VERSION,
        }

    except Exception:
        logger.exception("Error en consulta de FastAPI")
        raise HTTPException(
            status_code=500,
            detail="Error consultando resumen de cartera.",
        )


# ============================================================
# CONSULTAR CARTERA
# ============================================================

@app.get("/portfolio")
def portfolio(
    risk_level: str | None = Query(
        default=None,
        description="BAJO, MEDIO, ALTO o CRITICO",
    ),
    prediction: int | None = Query(
        default=None,
        ge=0,
        le=1,
        description="0 = no default, 1 = default",
    ),
    limit: int = Query(
        default=100,
        ge=1,
        le=1000,
    ),
    offset: int = Query(
        default=0,
        ge=0,
    ),
):
    filters = []
    params = {
        "limit": limit,
        "offset": offset,
    }

    if risk_level:
        risk_level = risk_level.upper()

        if risk_level not in VALID_RISK_LEVELS:
            raise HTTPException(
                status_code=400,
                detail=(
                    "risk_level invalido. "
                    "Valores permitidos: BAJO, MEDIO, ALTO, CRITICO."
                ),
            )

        filters.append(
            "risk_level = :risk_level"
        )

        params["risk_level"] = risk_level

    if prediction is not None:
        filters.append(
            "prediction = :prediction"
        )

        params["prediction"] = prediction

    where_clause = ""

    if filters:
        where_clause = (
            "WHERE "
            + " AND ".join(filters)
        )

    query = text(
        f"""
        SELECT
            score_output_id,
            score_input_id,
            id,
            fecha_score,
            modelo_version,
            probability_default,
            prediction,
            risk_level,
            recommendation,
            limit_bal,
            sex,
            education,
            marriage,
            age,
            pay_0,
            pay_max_delay,
            recent_delay_months,
            consecutive_delay_months,
            bill_avg,
            pay_amt_avg,
            payment_bill_ratio_total

        FROM gold.vw_portfolio_scoring_current

        {where_clause}

        ORDER BY probability_default DESC

        LIMIT :limit
        OFFSET :offset;
        """
    )

    try:
        with engine.connect() as conn:
            rows = (
                conn.execute(
                    query,
                    params,
                )
                .mappings()
                .all()
            )

        return {
            "count": len(rows),
            "limit": limit,
            "offset": offset,
            "risk_level": risk_level,
            "prediction": prediction,
            "results": serialize_rows(rows),
        }

    except Exception:
        logger.exception("Error en consulta de FastAPI")
        raise HTTPException(
            status_code=500,
            detail="Error consultando cartera.",
        )


# ============================================================
# ANALITICA DE CARTERA COMPLETA (NO LIMITADA AL TOP N)
# ============================================================

@app.get("/portfolio/analytics")
def portfolio_analytics(
    risk_level: str | None = Query(default=None),
    prediction: int | None = Query(default=None, ge=0, le=1),
    min_pd: float = Query(default=0.0, ge=0.0, le=1.0),
):
    """Agregados de toda la poblacion filtrada; nunca del top 250."""
    if risk_level:
        risk_level = risk_level.upper()
        if risk_level not in VALID_RISK_LEVELS:
            raise HTTPException(status_code=400, detail="risk_level invalido")

    clauses = ["probability_default >= :min_pd"]
    params = {"min_pd": min_pd}
    if risk_level:
        clauses.append("risk_level = :risk_level")
        params["risk_level"] = risk_level
    if prediction is not None:
        clauses.append("prediction = :prediction")
        params["prediction"] = prediction
    where = " AND ".join(clauses)
    base = f"FROM gold.vw_portfolio_scoring_current WHERE {where}"
    # Las categorias se construyen en SQL sobre la cartera completa.
    queries = {
        "overall": f"""SELECT COUNT(*) AS clientes, AVG(probability_default) AS pd_promedio
                       {base}""",
        "exposure": f"""SELECT risk_level AS categoria, COUNT(*) AS clientes,
                            SUM(COALESCE(limit_bal, 0)) AS exposicion
                            {base} GROUP BY risk_level""",
        "age": f"""SELECT CASE WHEN age < 30 THEN '<30'
                              WHEN age < 40 THEN '30-39'
                              WHEN age < 50 THEN '40-49'
                              WHEN age < 60 THEN '50-59'
                              WHEN age < 70 THEN '60-69'
                              WHEN age IS NOT NULL THEN '70+'
                              ELSE 'Sin dato' END AS categoria,
                              COUNT(*) AS clientes, AVG(probability_default) AS pd_promedio
                              {base} GROUP BY 1""",
        "delay": f"""SELECT COALESCE(pay_max_delay::text, 'Sin dato') AS categoria,
                                COUNT(*) AS clientes, AVG(probability_default) AS pd_promedio
                                {base} GROUP BY 1""",
        "recent": f"""SELECT COALESCE(recent_delay_months::text, 'Sin dato') AS categoria,
                                 COUNT(*) AS clientes
                                 {base} GROUP BY 1""",
        "ratio": f"""SELECT CASE WHEN payment_bill_ratio_total IS NULL THEN 'Sin dato'
                              WHEN payment_bill_ratio_total < 0 THEN 'Negativo'
                              WHEN payment_bill_ratio_total <= 0.25 THEN '0-0.25'
                              WHEN payment_bill_ratio_total <= 0.50 THEN '0.25-0.50'
                              WHEN payment_bill_ratio_total <= 0.75 THEN '0.50-0.75'
                              WHEN payment_bill_ratio_total <= 1.00 THEN '0.75-1'
                              ELSE '>1' END AS categoria,
                              COUNT(*) AS clientes
                              {base} GROUP BY 1""",
    }
    try:
        with engine.connect() as conn:
            result = {}
            for key, sql in queries.items():
                rows = conn.execute(text(sql), params).mappings().all()
                result[key] = serialize_row(rows[0]) if key == "overall" else serialize_rows(rows)
        return {"scope": "cartera_filtrada_completa", "filters": {
            "risk_level": risk_level, "prediction": prediction, "min_pd": min_pd
        }, **result}
    except Exception:
        logger.exception("Error consultando analitica de cartera")
        raise HTTPException(status_code=500, detail="Error consultando analitica de cartera")


# ============================================================
# CONSULTAR UN CLIENTE
# ============================================================

@app.get("/portfolio/{customer_id}")
def portfolio_customer(
    customer_id: int,
):
    query = text(
        """
        SELECT
            score_output_id,
            score_input_id,
            id,
            fecha_score,
            modelo_version,
            probability_default,
            prediction,
            risk_level,
            recommendation,
            limit_bal,
            sex,
            education,
            marriage,
            age,
            pay_0,
            pay_max_delay,
            recent_delay_months,
            consecutive_delay_months,
            bill_avg,
            pay_amt_avg,
            payment_bill_ratio_total

        FROM gold.vw_portfolio_scoring_current

        WHERE id = :customer_id

        LIMIT 1;
        """
    )

    try:
        with engine.connect() as conn:
            row = (
                conn.execute(
                    query,
                    {
                        "customer_id": customer_id,
                    },
                )
                .mappings()
                .first()
            )

        if row is None:
            raise HTTPException(
                status_code=404,
                detail=f"Cliente {customer_id} no encontrado.",
            )

        return serialize_row(row)

    except HTTPException:
        raise

    except Exception:
        logger.exception("Error en consulta de FastAPI")
        raise HTTPException(
            status_code=500,
            detail="Error consultando cliente.",
        )


# ============================================================
# ENDPOINT COMPATIBLE CON STREAMLIT
# ============================================================
#
# IMPORTANTE:
# En Render Free este endpoint NO vuelve a cargar model.pkl.
#
# Devuelve el scoring REAL previamente generado por XGBoost
# y almacenado en Gold.
#
# Esto permite mantener compatibilidad con el dashboard
# sin superar los 512 MB de memoria del plan gratuito.
# ============================================================

@app.post("/predict/{customer_id}")
def predict_customer(
    customer_id: int,
):
    query = text(
        """
        SELECT
            score_output_id,
            score_input_id,
            id,
            fecha_score,
            modelo_version,
            probability_default,
            prediction,
            risk_level,
            recommendation,
            limit_bal,
            sex,
            education,
            marriage,
            age,
            pay_0,
            pay_max_delay,
            recent_delay_months,
            consecutive_delay_months,
            bill_avg,
            pay_amt_avg,
            payment_bill_ratio_total

        FROM gold.vw_portfolio_scoring_current

        WHERE id = :customer_id

        LIMIT 1;
        """
    )

    try:
        with engine.connect() as conn:
            row = (
                conn.execute(
                    query,
                    {
                        "customer_id": customer_id,
                    },
                )
                .mappings()
                .first()
            )

        if row is None:
            raise HTTPException(
                status_code=404,
                detail=f"Cliente {customer_id} no encontrado.",
            )

        result = serialize_row(row)

        result["scoring_mode"] = (
            "persisted_xgboost_scoring"
        )

        result["message"] = (
            "Resultado generado previamente por el modelo XGBoost "
            "y persistido en gold.score_output."
        )

        return result

    except HTTPException:
        raise

    except Exception:
        logger.exception("Error en consulta de FastAPI")
        raise HTTPException(
            status_code=500,
            detail="Error consultando scoring.",
        )

# ============================================================
# REVISION HUMANA PROTEGIDA (sin reentrenar ni cambiar score_output)
# ============================================================
from importlib import import_module

review_module = import_module("05_api.reviews")
app.include_router(review_module.register_review_routes(engine))
review_module.register_supervisor_routes(engine)
