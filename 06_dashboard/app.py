import os
import time
from typing import Any

import pandas as pd
import requests
import streamlit as st


# ============================================================
# CONFIGURACION GENERAL
# ============================================================

st.set_page_config(
    page_title="Cartera de Riesgo Crediticio",
    page_icon="📊",
    layout="wide",
)


# ============================================================
# CONFIGURACION DE API
# ============================================================

def get_api_base_url() -> str:
    """
    Obtiene la URL base de FastAPI.

    Prioridad:
    1. Streamlit Secrets
    2. Variable de entorno
    3. localhost para desarrollo local
    """

    try:
        if "API_BASE_URL" in st.secrets:
            return str(st.secrets["API_BASE_URL"]).rstrip("/")
    except Exception:
        pass

    return os.getenv(
        "API_BASE_URL",
        "http://127.0.0.1:8000",
    ).rstrip("/")


API_BASE_URL = get_api_base_url()

# Render Free puede tardar en despertar.
REQUEST_TIMEOUT = 90


# ============================================================
# FUNCIONES HTTP
# ============================================================

def api_get(
    endpoint: str,
    params: dict | None = None,
    retries: int = 2,
) -> Any:

    url = f"{API_BASE_URL}{endpoint}"

    last_error = None

    for attempt in range(retries + 1):

        try:

            response = requests.get(
                url,
                params=params,
                timeout=REQUEST_TIMEOUT,
            )

            response.raise_for_status()

            return response.json()

        except requests.RequestException as exc:

            last_error = exc

            if attempt < retries:
                time.sleep(3)

    raise RuntimeError(
        f"No fue posible comunicarse con FastAPI. "
        f"URL: {url}. Error: {last_error}"
    )


# ============================================================
# CACHE
# ============================================================

@st.cache_data(ttl=60)
def load_summary():
    return api_get("/portfolio/summary")


@st.cache_data(ttl=60)
def load_portfolio(
    risk_level: str | None = None,
    limit: int = 100,
):

    params = {
        "limit": limit,
    }

    if risk_level and risk_level != "TODOS":
        params["risk_level"] = risk_level

    return api_get(
        "/portfolio",
        params=params,
    )


def load_customer(customer_id: int):

    return api_get(
        f"/portfolio/{customer_id}"
    )


# ============================================================
# NORMALIZACION DE RESPUESTA DE CARTERA
# ============================================================

def extract_portfolio_records(payload: Any) -> list[dict]:
    """
    FastAPI puede devolver:
    - una lista directa de registros
    - {"items": [...]}
    - {"data": [...]}
    - {"results": [...]}
    - {"portfolio": [...]}
    - {"records": [...]}

    Esta funcion soporta todos esos formatos.
    """

    if payload is None:
        return []

    if isinstance(payload, list):

        return [
            row
            for row in payload
            if isinstance(row, dict)
        ]

    if isinstance(payload, dict):

        possible_keys = [
            "items",
            "data",
            "results",
            "portfolio",
            "records",
            "clientes",
        ]

        for key in possible_keys:

            value = payload.get(key)

            if isinstance(value, list):

                return [
                    row
                    for row in value
                    if isinstance(row, dict)
                ]

        # Caso excepcional: un unico registro
        if "id" in payload:
            return [payload]

    return []


# ============================================================
# NORMALIZACION DE NOMBRES DE COLUMNAS
# ============================================================

COLUMN_ALIASES = {
    # ID
    "customer_id": "id",
    "cliente_id": "id",

    # Probabilidad
    "pd": "probability_default",
    "probabilidad": "probability_default",
    "probabilidad_default": "probability_default",

    # Prediccion
    "prediccion": "prediction",
    "clasificacion": "prediction",

    # Riesgo
    "nivel_riesgo": "risk_level",
    "riesgo": "risk_level",

    # Recomendacion
    "recomendacion": "recommendation",

    # Modelo
    "model_version": "modelo_version",

    # Fecha
    "score_date": "fecha_score",
}


def normalize_portfolio_dataframe(
    payload: Any,
) -> pd.DataFrame:

    records = extract_portfolio_records(payload)

    if not records:
        return pd.DataFrame()

    df = pd.DataFrame(records)

    # --------------------------------------------------------
    # Normalizar nombres
    # --------------------------------------------------------

    rename_map = {}

    for source, destination in COLUMN_ALIASES.items():

        if (
            source in df.columns
            and destination not in df.columns
        ):
            rename_map[source] = destination

    if rename_map:
        df = df.rename(columns=rename_map)

    # --------------------------------------------------------
    # Convertir valores numericos
    # --------------------------------------------------------

    numeric_columns = [
        "id",
        "probability_default",
        "prediction",
        "limit_bal",
        "age",
        "pay_0",
        "pay_max_delay",
        "recent_delay_months",
        "consecutive_delay_months",
        "bill_avg",
        "pay_amt_avg",
        "payment_bill_ratio_total",
    ]

    for column in numeric_columns:

        if column in df.columns:

            df[column] = pd.to_numeric(
                df[column],
                errors="coerce",
            )

    # --------------------------------------------------------
    # Eliminar columnas completamente vacias
    # --------------------------------------------------------

    df = df.dropna(
        axis=1,
        how="all",
    )

    return df


# ============================================================
# HELPERS
# ============================================================

def format_percent(value):

    if value is None:
        return "N/D"

    try:
        return f"{float(value):.2%}"

    except (TypeError, ValueError):
        return "N/D"


def format_integer(value):

    if value is None:
        return "N/D"

    try:
        return f"{int(float(value)):,}"

    except (TypeError, ValueError):
        return "N/D"


def format_money(value):

    if value is None:
        return "N/D"

    try:
        return f"{float(value):,.2f}"

    except (TypeError, ValueError):
        return "N/D"


def risk_icon(value):

    mapping = {
        "BAJO": "🟢",
        "MEDIO": "🟡",
        "ALTO": "🟠",
        "CRITICO": "🔴",
    }

    return mapping.get(
        str(value).upper(),
        "⚪",
    )


# ============================================================
# CABECERA
# ============================================================

st.title("📊 Cartera de Riesgo Crediticio")

st.caption(
    "Vista operativa basada en el scoring real "
    "almacenado en la capa Gold de Supabase."
)


# ============================================================
# CARGAR RESUMEN
# ============================================================

try:

    summary = load_summary()

except Exception as exc:

    st.error(
        "No fue posible conectarse con FastAPI."
    )

    st.warning(
        "Render utiliza un servicio gratuito y puede tardar "
        "algunos segundos en despertar después de un periodo "
        "de inactividad."
    )

    st.code(API_BASE_URL)

    with st.expander("Detalle técnico"):
        st.exception(exc)

    st.stop()


# ============================================================
# KPI PRINCIPALES
# ============================================================

st.subheader("Resumen general")

c1, c2, c3, c4 = st.columns(4)

c1.metric(
    "Cartera",
    format_integer(
        summary.get("total")
    ),
)

c2.metric(
    "PD promedio",
    format_percent(
        summary.get("pd_promedio")
    ),
)

c3.metric(
    "Predicción = 1",
    format_integer(
        summary.get("prediction_1")
    ),
)

c4.metric(
    "Predicción = 0",
    format_integer(
        summary.get("prediction_0")
    ),
)


# ============================================================
# RIESGO
# ============================================================

r1, r2, r3, r4 = st.columns(4)

r1.metric(
    "🟢 Bajo",
    format_integer(
        summary.get("bajo")
    ),
)

r2.metric(
    "🟡 Medio",
    format_integer(
        summary.get("medio")
    ),
)

r3.metric(
    "🟠 Alto",
    format_integer(
        summary.get("alto")
    ),
)

r4.metric(
    "🔴 Crítico",
    format_integer(
        summary.get("critico")
    ),
)


# ============================================================
# INFORMACION MODELO
# ============================================================

with st.expander(
    "Información técnica del scoring"
):

    m1, m2, m3 = st.columns(3)

    m1.metric(
        "PD mínima",
        format_percent(
            summary.get("pd_min")
        ),
    )

    m2.metric(
        "PD máxima",
        format_percent(
            summary.get("pd_max")
        ),
    )

    m3.metric(
        "Versión del modelo",
        summary.get(
            "model_version",
            "N/D",
        ),
    )


# ============================================================
# GRAFICO DE RIESGO
# ============================================================

st.divider()

st.subheader(
    "Distribución de clientes por nivel de riesgo"
)

risk_df = pd.DataFrame(
    {
        "Nivel": [
            "BAJO",
            "MEDIO",
            "ALTO",
            "CRITICO",
        ],
        "Clientes": [
            int(summary.get("bajo", 0)),
            int(summary.get("medio", 0)),
            int(summary.get("alto", 0)),
            int(summary.get("critico", 0)),
        ],
    }
)

total_clients = max(
    int(summary.get("total", 1)),
    1,
)

risk_df["Porcentaje"] = (
    risk_df["Clientes"]
    / total_clients
    * 100
)

st.bar_chart(
    risk_df.set_index("Nivel")[
        ["Clientes"]
    ]
)

st.dataframe(
    risk_df,
    hide_index=True,
    use_container_width=True,
    column_config={
        "Clientes":
            st.column_config.NumberColumn(
                "Clientes",
                format="%d",
            ),

        "Porcentaje":
            st.column_config.NumberColumn(
                "% cartera",
                format="%.2f%%",
            ),
    },
)


# ============================================================
# CONSULTA INDIVIDUAL
# ============================================================

st.divider()

st.subheader(
    "Consulta individual de cliente"
)

search_col, button_col = st.columns(
    [4, 1],
    vertical_alignment="bottom",
)

with search_col:

    customer_id = st.number_input(
        "ID del cliente",
        min_value=1,
        value=1,
        step=1,
    )

with button_col:

    search_button = st.button(
        "Consultar",
        type="primary",
        use_container_width=True,
    )


if search_button:

    try:

        customer = load_customer(
            int(customer_id)
        )

        st.success(
            f"Cliente {int(customer_id):,} encontrado."
        )

        probability = customer.get(
            "probability_default"
        )

        prediction = customer.get(
            "prediction"
        )

        risk_level = customer.get(
            "risk_level"
        )

        q1, q2, q3, q4 = st.columns(4)

        q1.metric(
            "Probabilidad de incumplimiento",
            format_percent(probability),
        )

        q2.metric(
            "Clasificación",
            format_integer(prediction),
        )

        q3.metric(
            "Nivel de riesgo",
            (
                f"{risk_icon(risk_level)} "
                f"{risk_level or 'N/D'}"
            ),
        )

        q4.metric(
            "Límite de crédito",
            format_money(
                customer.get(
                    "limit_bal"
                )
            ),
        )

        st.subheader(
            "Recomendación"
        )

        st.info(
            customer.get(
                "recommendation",
                "No existe recomendación disponible.",
            )
        )

        st.subheader(
            "Señales principales"
        )

        s1, s2, s3, s4 = st.columns(4)

        s1.metric(
            "Edad",
            format_integer(
                customer.get("age")
            ),
        )

        s2.metric(
            "Máximo atraso",
            format_integer(
                customer.get(
                    "pay_max_delay"
                )
            ),
        )

        s3.metric(
            "Atrasos recientes",
            format_integer(
                customer.get(
                    "recent_delay_months"
                )
            ),
        )

        s4.metric(
            "Atrasos consecutivos",
            format_integer(
                customer.get(
                    "consecutive_delay_months"
                )
            ),
        )

        with st.expander(
            "Ver registro completo"
        ):

            st.json(customer)

    except Exception as exc:

        st.error(
            "No fue posible consultar "
            f"el cliente {customer_id}."
        )

        with st.expander(
            "Detalle técnico"
        ):
            st.exception(exc)


# ============================================================
# TABLA OPERATIVA
# ============================================================

st.divider()

st.subheader(
    "Tabla operativa para gestión de cartera"
)

filter_col, limit_col = st.columns(2)

with filter_col:

    risk_filter = st.selectbox(
        "Nivel de riesgo",
        [
            "TODOS",
            "CRITICO",
            "ALTO",
            "MEDIO",
            "BAJO",
        ],
    )

with limit_col:

    row_limit = st.selectbox(
        "Registros a mostrar",
        [
            50,
            100,
            250,
            500,
            1000,
        ],
        index=1,
    )


try:

    portfolio_payload = load_portfolio(
        risk_level=risk_filter,
        limit=row_limit,
    )

    portfolio_df = normalize_portfolio_dataframe(
        portfolio_payload
    )

    if portfolio_df.empty:

        st.warning(
            "La API no devolvió registros "
            "para el filtro seleccionado."
        )

    else:

        # ----------------------------------------------------
        # Columnas que realmente queremos mostrar
        # ----------------------------------------------------

        preferred_columns = [
            "id",
            "probability_default",
            "prediction",
            "risk_level",
            "limit_bal",
            "age",
            "pay_max_delay",
            "recent_delay_months",
            "consecutive_delay_months",
            "recommendation",
            "modelo_version",
            "fecha_score",
        ]

        available_columns = [
            column
            for column in preferred_columns
            if column in portfolio_df.columns
        ]

        # Si por alguna razon no coincide ninguna,
        # mostramos lo que la API realmente envio.
        if not available_columns:

            st.warning(
                "La estructura recibida desde FastAPI "
                "no coincide con las columnas esperadas. "
                "Se muestran los datos originales."
            )

            display_df = portfolio_df.copy()

        else:

            display_df = portfolio_df[
                available_columns
            ].copy()

        # ----------------------------------------------------
        # Renombrar para usuario final
        # ----------------------------------------------------

        display_df = display_df.rename(
            columns={
                "id":
                    "Cliente",

                "probability_default":
                    "PD",

                "prediction":
                    "Predicción",

                "risk_level":
                    "Nivel de riesgo",

                "limit_bal":
                    "Límite de crédito",

                "age":
                    "Edad",

                "pay_max_delay":
                    "Máximo atraso",

                "recent_delay_months":
                    "Atrasos recientes",

                "consecutive_delay_months":
                    "Atrasos consecutivos",

                "recommendation":
                    "Recomendación",

                "modelo_version":
                    "Versión modelo",

                "fecha_score":
                    "Fecha scoring",
            }
        )

        # ----------------------------------------------------
        # Evitar filas visualmente vacias
        # ----------------------------------------------------

        display_df = display_df.dropna(
            axis=1,
            how="all",
        )

        st.caption(
            f"Registros mostrados: "
            f"{len(display_df):,}"
        )

        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True,
            column_config={

                "PD":
                    st.column_config.NumberColumn(
                        "PD",
                        format="%.4f",
                    ),

                "Límite de crédito":
                    st.column_config.NumberColumn(
                        "Límite de crédito",
                        format="%.2f",
                    ),

                "Cliente":
                    st.column_config.NumberColumn(
                        "Cliente",
                        format="%d",
                    ),

                "Predicción":
                    st.column_config.NumberColumn(
                        "Predicción",
                        format="%d",
                    ),

                "Edad":
                    st.column_config.NumberColumn(
                        "Edad",
                        format="%d",
                    ),
            },
        )


except Exception as exc:

    st.error(
        "No fue posible cargar la tabla "
        "operativa de cartera."
    )

    with st.expander(
        "Detalle técnico"
    ):
        st.exception(exc)


# ============================================================
# ESTADO DEL SISTEMA
# ============================================================

st.divider()

status_col1, status_col2 = st.columns(2)

with status_col1:

    st.success(
        "FastAPI conectado"
    )

with status_col2:

    st.info(
        f"Modelo: "
        f"{summary.get('model_version', 'N/D')}"
    )


# ============================================================
# FOOTER
# ============================================================

st.caption(
    "Proyecto Productivo IIIA · "
    "Sistema Predictivo y Prescriptivo "
    "de Riesgo Crediticio"
)

