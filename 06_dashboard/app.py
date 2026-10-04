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
    page_title="NexaRisk | Supervisión de Riesgo Crediticio",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ============================================================
# ESTILO VISUAL SIN HTML VISIBLE
# ============================================================

st.markdown(
    """
    <style>
    .stApp {
        background: #F4F7FA;
    }
    .block-container {
        max-width: 1720px;
        padding-top: 1rem;
        padding-bottom: 2rem;
    }
    [data-testid="stHeader"] {
        background: rgba(244,247,250,0.92);
    }
    div[data-testid="stMetric"] {
        background: #FFFFFF;
        border: 1px solid #DDE6EE;
        border-radius: 16px;
        padding: 16px 18px;
        box-shadow: 0 4px 18px rgba(11,31,51,0.05);
    }
    div[data-testid="stMetric"] label {
        color: #667085 !important;
        font-size: 0.78rem !important;
        font-weight: 700 !important;
        text-transform: uppercase;
        letter-spacing: 0.04em;
    }
    div[data-testid="stMetricValue"] {
        color: #102033;
        font-weight: 800;
    }
    div[data-testid="stDataFrame"] {
        border-radius: 14px;
        overflow: hidden;
        border: 1px solid #DDE6EE;
    }
    .stButton > button {
        border-radius: 10px;
        font-weight: 800;
        background: #0E7490;
        color: white;
        border: 0;
    }
    .stDownloadButton > button {
        border-radius: 10px;
        font-weight: 800;
        border: 1px solid #0E7490;
        color: #0E7490;
    }
    section[data-testid="stSidebar"] {
        display: none;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ============================================================
# CONSTANTES
# ============================================================

API_DEFAULT = "https://pproyecto-productivo-iiia-api.onrender.com"
REQUEST_TIMEOUT = 90

RISK_ORDER = ["CRITICO", "ALTO", "MEDIO", "BAJO"]
RISK_COLORS = {
    "BAJO": "🟢",
    "MEDIO": "🟡",
    "ALTO": "🟠",
    "CRITICO": "🔴",
}

# ============================================================
# CONEXION API
# ============================================================


def get_api_base_url() -> str:
    try:
        if "API_BASE_URL" in st.secrets:
            return str(st.secrets["API_BASE_URL"]).rstrip("/")
    except Exception:
        pass

    return os.getenv("API_BASE_URL", API_DEFAULT).rstrip("/")


API_BASE_URL = get_api_base_url()


def api_get(endpoint: str, params: dict | None = None, retries: int = 2) -> Any:
    url = f"{API_BASE_URL}{endpoint}"
    last_error = None

    for attempt in range(retries + 1):
        try:
            response = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as exc:
            last_error = exc
            if attempt < retries:
                time.sleep(3)

    raise RuntimeError(f"No fue posible conectar con FastAPI: {last_error}")


@st.cache_data(ttl=60)
def load_summary() -> dict:
    return api_get("/portfolio/summary")


@st.cache_data(ttl=60)
def load_portfolio(risk_level: str | None = None, limit: int = 250) -> Any:
    params = {"limit": limit}
    if risk_level and risk_level != "TODOS":
        params["risk_level"] = risk_level
    return api_get("/portfolio", params=params)


@st.cache_data(ttl=60)
def load_customer(customer_id: int) -> dict:
    return api_get(f"/portfolio/{customer_id}")

# ============================================================
# HELPERS
# ============================================================


def extract_records(payload: Any) -> list[dict]:
    if isinstance(payload, list):
        return [x for x in payload if isinstance(x, dict)]

    if isinstance(payload, dict):
        for key in ["items", "data", "results", "portfolio", "records"]:
            value = payload.get(key)
            if isinstance(value, list):
                return [x for x in value if isinstance(x, dict)]
        if "id" in payload:
            return [payload]

    return []


def to_df(payload: Any) -> pd.DataFrame:
    records = extract_records(payload)
    if not records:
        return pd.DataFrame()

    df = pd.DataFrame(records)

    numeric_cols = [
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

    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    return df


def fmt_int(value: Any) -> str:
    try:
        return f"{int(float(value)):,}".replace(",", ".")
    except Exception:
        return "N/D"


def fmt_pct(value: Any) -> str:
    try:
        return f"{float(value) * 100:.2f}%"
    except Exception:
        return "N/D"


def fmt_money(value: Any) -> str:
    try:
        return f"{float(value):,.0f}".replace(",", ".")
    except Exception:
        return "N/D"


def risk_badge(value: Any) -> str:
    value = str(value or "N/D").upper()
    return f"{RISK_COLORS.get(value, '⚪')} {value}"


def add_section_title(title: str, caption: str | None = None):
    st.markdown(f"### {title}")
    if caption:
        st.caption(caption)

# ============================================================
# CARGA DE DATOS
# ============================================================

try:
    summary = load_summary()
except Exception as exc:
    st.error("No fue posible conectar con la API pública.")
    st.info("Render Free puede tardar hasta 60 segundos en despertar después de inactividad.")
    st.code(API_BASE_URL)
    with st.expander("Detalle técnico"):
        st.exception(exc)
    st.stop()

# ============================================================
# HEADER INSTITUCIONAL
# ============================================================

header_left, header_right = st.columns([4, 1.3], vertical_alignment="center")

with header_left:
    st.markdown("# 🛡️ NexaRisk")
    st.markdown("#### Centro de Supervisión de Riesgo Crediticio")
    st.caption("Vista ejecutiva de cartera puntuada · Scoring real persistido en Gold · FastAPI + Supabase + Streamlit")

with header_right:
    st.success("● API ONLINE")
    st.caption(f"Modelo: {summary.get('model_version', 'N/D')}")
    st.caption("Paleta: Navy · Teal · Mint · Gold")

st.divider()

# ============================================================
# KPIS EJECUTIVOS
# ============================================================

total = int(summary.get("total", 0))
critico = int(summary.get("critico", 0))
alto = int(summary.get("alto", 0))
medio = int(summary.get("medio", 0))
bajo = int(summary.get("bajo", 0))
pred_1 = int(summary.get("prediction_1", 0))
pred_0 = int(summary.get("prediction_0", 0))
priority = critico + alto
priority_pct = priority / total if total else 0

k1, k2, k3, k4, k5 = st.columns(5)

k1.metric("Cartera evaluada", fmt_int(total), "registros")
k2.metric("PD promedio", fmt_pct(summary.get("pd_promedio")), "probabilidad media")
k3.metric("Gestión prioritaria", fmt_int(priority), f"{fmt_pct(priority_pct)} alto + crítico")
k4.metric("Predicción = 1", fmt_int(pred_1), "potencial incumplimiento")
k5.metric("Predicción = 0", fmt_int(pred_0), "sin señal de incumplimiento")

# ============================================================
# LAYOUT CON FILTROS A LA DERECHA
# ============================================================

main_col, filter_col = st.columns([4.8, 1.25], gap="large")

with filter_col:
    with st.container(border=True):
        st.markdown("### 🎛️ Filtros")
        risk_filter = st.selectbox("Nivel de riesgo", ["TODOS", "CRITICO", "ALTO", "MEDIO", "BAJO"])
        prediction_filter = st.selectbox("Clasificación", ["TODAS", "1", "0"])
        min_pd = st.slider("PD mínima", min_value=0, max_value=100, value=0, step=5)
        row_limit = st.selectbox("Clientes a mostrar", [50, 100, 250, 500, 1000], index=2)
        st.caption("Los filtros se aplican sobre la cartera consultada desde FastAPI.")

    with st.container(border=True):
        st.markdown("### 🔎 Cliente 360")
        quick_customer = st.number_input("ID cliente", min_value=1, value=1, step=1)
        quick_search = st.button("Consultar cliente", type="primary", use_container_width=True)

    with st.container(border=True):
        st.markdown("### 🎨 Identidad")
        st.caption("NexaRisk · Supervisión de cartera")
        st.caption("#0B1F33 · #0E7490 · #14B8A6 · #F4B942")

with main_col:
    # --------------------------------------------------------
    # GRAFICOS PRINCIPALES
    # --------------------------------------------------------
    graph_left, graph_right = st.columns([1.25, 1], gap="medium")

    with graph_left:
        with st.container(border=True):
            add_section_title("Distribución de riesgo", "Composición de la cartera por banda de supervisión")
            risk_df = pd.DataFrame(
                {
                    "Nivel": ["BAJO", "MEDIO", "ALTO", "CRITICO"],
                    "Clientes": [bajo, medio, alto, critico],
                }
            )
            risk_df["% cartera"] = risk_df["Clientes"] / max(total, 1) * 100
            st.bar_chart(risk_df.set_index("Nivel")[["Clientes"]], height=300)
            st.dataframe(
                risk_df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Clientes": st.column_config.NumberColumn("Clientes", format="%d"),
                    "% cartera": st.column_config.NumberColumn("% cartera", format="%.2f%%"),
                },
            )

    with graph_right:
        with st.container(border=True):
            add_section_title("Clasificación del modelo", "Salida binaria del scoring")
            pred_df = pd.DataFrame(
                {
                    "Clase": ["Predicción 0", "Predicción 1"],
                    "Clientes": [pred_0, pred_1],
                }
            )
            st.bar_chart(pred_df.set_index("Clase"), height=300)

            st.metric("PD mínima", fmt_pct(summary.get("pd_min")))
            st.metric("PD máxima", fmt_pct(summary.get("pd_max")))

    # --------------------------------------------------------
    # LECTURA EJECUTIVA
    # --------------------------------------------------------
    with st.container(border=True):
        st.markdown("### 🚨 Lectura ejecutiva")
        st.warning(
            f"Actualmente **{fmt_int(priority)} clientes** están en niveles **ALTO o CRÍTICO**, "
            f"equivalentes al **{fmt_pct(priority_pct)}** de la cartera evaluada. "
            "Esta población constituye la principal cola de seguimiento preventivo para el supervisor de créditos."
        )

    # --------------------------------------------------------
    # CARTERA PRIORIZADA
    # --------------------------------------------------------
    with st.container(border=True):
        add_section_title("Cartera priorizada", "Ordenada por mayor probabilidad de incumplimiento")

        try:
            portfolio_payload = load_portfolio(risk_level=risk_filter, limit=row_limit)
            df = to_df(portfolio_payload)

            if df.empty:
                st.warning("No existen registros para los filtros seleccionados.")
            else:
                if prediction_filter != "TODAS" and "prediction" in df.columns:
                    df = df[df["prediction"] == int(prediction_filter)]

                if "probability_default" in df.columns:
                    df = df[df["probability_default"] >= min_pd / 100]
                    df = df.sort_values("probability_default", ascending=False)
                    df["pd_percent"] = df["probability_default"] * 100

                if "risk_level" in df.columns:
                    df["risk_display"] = df["risk_level"].map(risk_badge)

                display_cols = [
                    "id",
                    "pd_percent",
                    "prediction",
                    "risk_display",
                    "limit_bal",
                    "age",
                    "pay_max_delay",
                    "recent_delay_months",
                    "consecutive_delay_months",
                    "payment_bill_ratio_total",
                    "recommendation",
                ]
                display_cols = [c for c in display_cols if c in df.columns]
                display_df = df[display_cols].copy()
                display_df = display_df.rename(
                    columns={
                        "id": "Cliente",
                        "pd_percent": "PD %",
                        "prediction": "Pred.",
                        "risk_display": "Riesgo",
                        "limit_bal": "Límite",
                        "age": "Edad",
                        "pay_max_delay": "Máx. atraso",
                        "recent_delay_months": "Atrasos recientes",
                        "consecutive_delay_months": "Atrasos consecutivos",
                        "payment_bill_ratio_total": "Ratio pago/fact.",
                        "recommendation": "Acción sugerida",
                    }
                )

                st.caption(f"{fmt_int(len(display_df))} clientes mostrados")
                st.dataframe(
                    display_df,
                    use_container_width=True,
                    hide_index=True,
                    height=470,
                    column_config={
                        "Cliente": st.column_config.NumberColumn("Cliente", format="%d"),
                        "PD %": st.column_config.ProgressColumn("PD %", min_value=0, max_value=100, format="%.1f%%"),
                        "Pred.": st.column_config.NumberColumn("Pred.", format="%d"),
                        "Límite": st.column_config.NumberColumn("Límite", format="%.0f"),
                        "Ratio pago/fact.": st.column_config.NumberColumn("Ratio pago/fact.", format="%.3f"),
                    },
                )

                csv = display_df.to_csv(index=False).encode("utf-8-sig")
                st.download_button(
                    "⬇ Descargar cartera filtrada",
                    data=csv,
                    file_name="cartera_filtrada_nexarisk.csv",
                    mime="text/csv",
                )

        except Exception as exc:
            st.error("No fue posible cargar la cartera operativa.")
            with st.expander("Detalle técnico"):
                st.exception(exc)

# ============================================================
# CLIENTE 360
# ============================================================

if quick_search:
    st.divider()
    with st.container(border=True):
        st.markdown(f"## 👤 Cliente 360 · #{int(quick_customer)}")

        try:
            customer = load_customer(int(quick_customer))
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("PD", fmt_pct(customer.get("probability_default")))
            c2.metric("Nivel de riesgo", risk_badge(customer.get("risk_level")))
            c3.metric("Clasificación", customer.get("prediction", "N/D"))
            c4.metric("Límite de crédito", fmt_money(customer.get("limit_bal")))

            st.markdown("### Recomendación de gestión")
            st.info(customer.get("recommendation", "No disponible"))

            s1, s2, s3, s4 = st.columns(4)
            s1.metric("Edad", customer.get("age", "N/D"))
            s2.metric("Máximo atraso", customer.get("pay_max_delay", "N/D"))
            s3.metric("Atrasos recientes", customer.get("recent_delay_months", "N/D"))
            s4.metric("Atrasos consecutivos", customer.get("consecutive_delay_months", "N/D"))

            with st.expander("Ver registro técnico completo"):
                st.json(customer)

        except Exception as exc:
            st.error("No fue posible consultar el cliente.")
            with st.expander("Detalle técnico"):
                st.exception(exc)

# ============================================================
# FOOTER
# ============================================================

st.divider()
f1, f2, f3 = st.columns([2, 1, 1])
f1.caption("NexaRisk · Proyecto Productivo IIIA")
f2.caption(f"Modelo: {summary.get('model_version', 'N/D')}")
f3.caption("FastAPI · Supabase · Streamlit")
