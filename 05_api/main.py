import os

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from fastapi.encoders import jsonable_encoder
from sqlalchemy import create_engine, text


# ============================================================
# CONFIGURACION
# ============================================================

load_dotenv()

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

    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail=f"No fue posible conectar con la base de datos: {exc}",
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

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Error consultando resumen de cartera: {exc}",
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

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Error consultando cartera: {exc}",
        )


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

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Error consultando cliente: {exc}",
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

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Error consultando scoring: {exc}",
        )
