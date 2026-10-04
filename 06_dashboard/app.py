import os
import time
from typing import Any

import altair as alt
import pandas as pd
import requests
import streamlit as st


# ============================================================
# CONFIGURACION GENERAL
# ============================================================

st.set_page_config(
    page_title="NexaRisk | Credit Risk Command Center",
    page_icon="NR",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# ============================================================
# PALETA INSTITUCIONAL
# ============================================================

MIDNIGHT = "#07111F"
NAVY = "#0C1B2A"
SLATE = "#12283A"
PANEL = "#0E1929"
PANEL_2 = "#132236"
BORDER = "#284057"

CYAN = "#19C3C8"
BLUE = "#62A7F7"
GOLD = "#D7B56D"
TEXT = "#EAF1F7"
MUTED = "#91A2B8"

RISK_COLORS = {
    "BAJO": "#36C98F",
    "MEDIO": "#F2D15A",
    "ALTO": "#F59E42",
    "CRITICO": "#EF5C6C",
}

CLASS_COLORS = {
    "Predicción 0": "#5F8FEF",
    "Predicción 1": "#D7B56D",
}


# ============================================================
# CSS
# ============================================================

st.markdown(
    f"""
    <style>
    .stApp {{
        background:
            radial-gradient(circle at 85% 0%, rgba(25,195,200,.06), transparent 28%),
            linear-gradient(180deg, {MIDNIGHT} 0%, #08101d 100%);
        color: {TEXT};
    }}

    [data-testid="stHeader"] {{
        background: rgba(7,17,31,.88);
    }}

    .block-container {{
        max-width: 1780px;
        padding-top: 0.75rem;
        padding-bottom: 2rem;
    }}

    h1, h2, h3, p, label {{
        color: {TEXT};
    }}

    .brand-shell {{
        background: linear-gradient(105deg, #0b1728 0%, #10283a 72%, #123d47 100%);
        border: 1px solid {BORDER};
        border-radius: 17px;
        padding: 20px 24px;
        margin-bottom: 14px;
        box-shadow: 0 8px 28px rgba(0,0,0,.24);
    }}

    .brand-row {{
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 20px;
    }}

    .brand-left {{
        display: flex;
        align-items: center;
        gap: 14px;
    }}

    .brand-mark {{
        width: 48px;
        height: 48px;
        border-radius: 11px;
        display: flex;
        align-items: center;
        justify-content: center;
        background: linear-gradient(135deg, {CYAN}, #3DD6C8);
        color: #06111d;
        font-weight: 900;
        font-size: 17px;
        letter-spacing: -.4px;
    }}

    .brand-name {{
        font-size: 23px;
        font-weight: 850;
        color: {TEXT};
        line-height: 1;
    }}

    .brand-sub {{
        margin-top: 5px;
        color: {MUTED};
        font-size: 11px;
    }}

    .api-state {{
        text-align: right;
        color: {MUTED};
        font-size: 10px;
        line-height: 1.65;
    }}

    .api-online {{
        color: {CYAN};
        font-size: 10px;
        font-weight: 800;
        letter-spacing: .5px;
    }}

    .kpi {{
        background: {PANEL};
        border: 1px solid {BORDER};
        border-top: 2px solid {accent};
        border-radius: 13px;
        padding: 15px 16px;
        min-height: 104px;
        box-shadow: 0 5px 18px rgba(0,0,0,.18);
    }}

    .kpi-label {{
        color: {MUTED};
        font-size: 9px;
        letter-spacing: .65px;
        font-weight: 800;
        text-transform: uppercase;
    }}

    .kpi-value {{
        color: {TEXT};
        font-size: 26px;
        font-weight: 850;
        margin-top: 6px;
    }}

    .kpi-note {{
        color: {MUTED};
        font-size: 9px;
        margin-top: 6px;
    }}

    .panel-title {{
        color: {TEXT};
        font-size: 14px;
        font-weight: 800;
        margin-bottom: 2px;
    }}

    .panel-sub {{
        color: {MUTED};
        font-size: 9px;
        margin-bottom: 8px;
    }}

    .filter-header {{
        background: linear-gradient(90deg, #16273a, #1a3147);
        border: 1px solid {BORDER};
        border-radius: 10px;
        padding: 12px 13px;
        color: {TEXT};
        font-size: 11px;
        font-weight: 850;
        letter-spacing: .3px;
        margin-bottom: 9px;
    }}

    .filter-card {{
        background: {PANEL};
        border: 1px solid {BORDER};
        border-radius: 13px;
        padding: 13px 13px 7px 13px;
        box-shadow: 0 5px 18px rgba(0,0,0,.17);
        margin-bottom: 12px;
    }}

    .executive-box {{
        background: linear-gradient(90deg, rgba(215,181,109,.10), rgba(25,195,200,.05));
        border: 1px solid rgba(215,181,109,.45);
        border-left: 4px solid {GOLD};
        border-radius: 10px;
        padding: 11px 14px;
        color: {TEXT};
        font-size: 10px;
        margin: 8px 0 15px 0;
    }}

    div[data-testid="stMetric"] {{
        background: {PANEL};
        border: 1px solid {BORDER};
        border-radius: 12px;
        padding: 12px;
    }}

    div[data-testid="stMetricLabel"] {{
        color: {MUTED};
    }}

    div[data-testid="stMetricValue"] {{
        color: {TEXT};
    }}

    div[data-baseweb="select"] > div {{
        background: {PANEL_2};
        border-color: {BORDER};
        color: {TEXT};
    }}

    div[data-testid="stNumberInput"] input {{
        background: {PANEL_2};
        color: {TEXT};
    }}

    .stButton > button {{
        background: {CYAN};
        color: #07111F;
        border: none;
        border-radius: 8px;
        font-weight: 850;
    }}

    .stButton > button:hover {{
        background: #43d6d8;
        color: #07111F;
    }}

    [data-testid="stDataFrame"] {{
        border: 1px solid {BORDER};
        border-radius: 10px;
        overflow: hidden;
    }}

    hr {{
        border-color: {BORDER};
    }}
    </style>
    """.replace("{accent}", CYAN),
    unsafe_allow_html=True,
)


# ============================================================
# API
# ============================================================

def get_api_base_url() -> str:
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
REQUEST_TIMEOUT = 90


def api_get(endpoint: str, params: dict | None = None, retries: int = 2) -> Any:
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

    raise RuntimeError(f"No fue posible conectar con FastAPI: {last_error}")


@st.cache_data(ttl=60)
def load_summary():
    return api_get("/portfolio/summary")


@st.cache_data(ttl=60)
def load_portfolio(risk_level=None, limit=500):
    params = {"limit": limit}

    if risk_level and risk_level != "TODOS":
        params["risk_level"] = risk_level

    return api_get("/portfolio", params=params)


def load_customer(customer_id: int):
    return api_get(f"/portfolio/{customer_id}")


# ============================================================
# HELPERS
# ============================================================

def extract_records(payload: Any) -> list:
    if isinstance(payload, list):
        return payload

    if isinstance(payload, dict):
        for key in ["items", "data", "results", "portfolio", "records"]:
            value = payload.get(key)
            if isinstance(value, list):
                return value

    return []


def normalize_df(payload: Any) -> pd.DataFrame:
    records = extract_records(payload)

    if not records:
        return pd.DataFrame()

    df = pd.DataFrame(records)

    numeric_columns = [
        "id",
        "probability_default",
        "prediction",
        "limit_bal",
        "age",
        "pay_max_delay",
        "recent_delay_months",
        "consecutive_delay_months",
        "payment_bill_ratio_total",
        "bill_avg",
        "pay_amt_avg",
    ]

    for col in numeric_columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    return df


def fmt_int(value):
    try:
        return f"{int(value):,}".replace(",", ".")
    except Exception:
        return "N/D"


def fmt_pct(value):
    try:
        return f"{float(value) * 100:.2f}%"
    except Exception:
        return "N/D"


def fmt_money(value):
    try:
        return f"{float(value):,.0f}".replace(",", ".")
    except Exception:
        return "N/D"


def section(title: str, subtitle: str):
    st.markdown(
        f'<div class="panel-title">{title}</div>'
        f'<div class="panel-sub">{subtitle}</div>',
        unsafe_allow_html=True,
    )


def kpi_card(label: str, value: str, note: str, accent: str):
    st.markdown(
        f"""
        <div class="kpi" style="border-top-color:{accent};">
            <div class="kpi-label">{label}</div>
            <div class="kpi-value">{value}</div>
            <div class="kpi-note">{note}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def dark_chart(chart: alt.Chart, height=280):
    return (
        chart.properties(height=height)
        .configure_view(strokeOpacity=0)
        .configure_axis(
            gridColor="#20344B",
            domainColor="#31475E",
            tickColor="#31475E",
            labelColor=TEXT,
            titleColor=MUTED,
            labelFontSize=10,
            titleFontSize=10,
        )
        .configure_legend(
            labelColor=TEXT,
            titleColor=MUTED,
        )
    )


# ============================================================
# DATOS
# ============================================================

try:
    summary = load_summary()
except Exception as exc:
    st.error("No fue posible conectar con FastAPI.")
    st.info("Render Free puede tardar algunos segundos en despertar.")
    with st.expander("Detalle técnico"):
        st.exception(exc)
    st.stop()


# ============================================================
# HEADER
# ============================================================

st.markdown(
    f"""
    <div class="brand-shell">
        <div class="brand-row">
            <div class="brand-left">
                <div class="brand-mark">NR</div>
                <div>
                    <div class="brand-name">NexaRisk</div>
                    <div class="brand-sub">
                        Credit Risk Command Center · Supervisión de cartera y priorización preventiva
                    </div>
                </div>
            </div>
            <div class="api-state">
                <span class="api-online">API ONLINE</span><br>
                Modelo {summary.get("model_version", "N/D")}<br>
                FastAPI · Supabase · Streamlit
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# KPIs
# ============================================================

total = int(summary.get("total", 0))
bajo = int(summary.get("bajo", 0))
medio = int(summary.get("medio", 0))
alto = int(summary.get("alto", 0))
critico = int(summary.get("critico", 0))
priority = alto + critico
priority_pct = priority / total if total else 0

k1, k2, k3, k4, k5 = st.columns(5)

with k1:
    kpi_card("Cartera evaluada", fmt_int(total), "Scoring vigente", CYAN)

with k2:
    kpi_card("PD promedio", fmt_pct(summary.get("pd_promedio")), "Probabilidad media", BLUE)

with k3:
    kpi_card("Gestión prioritaria", fmt_int(priority), f"{fmt_pct(priority_pct)} en Alto + Crítico", RISK_COLORS["CRITICO"])

with k4:
    kpi_card("Predicción = 1", fmt_int(summary.get("prediction_1")), "Potencial incumplimiento", GOLD)

with k5:
    kpi_card("Predicción = 0", fmt_int(summary.get("prediction_0")), "Sin señal de incumplimiento", "#6A7D94")

st.write("")


# ============================================================
# LAYOUT PRINCIPAL — FILTROS A LA IZQUIERDA
# ============================================================

filters_col, main_col = st.columns([1.15, 4.85], gap="large")


# ============================================================
# FILTROS IZQUIERDA
# ============================================================

with filters_col:
    st.markdown('<div class="filter-header">FILTROS DE CARTERA</div>', unsafe_allow_html=True)

    st.markdown('<div class="filter-card">', unsafe_allow_html=True)

    risk_filter = st.selectbox(
        "Nivel de riesgo",
        ["TODOS", "CRITICO", "ALTO", "MEDIO", "BAJO"],
    )

    prediction_filter = st.selectbox(
        "Clasificación",
        ["TODAS", "1", "0"],
    )

    min_pd = st.slider(
        "PD mínima",
        min_value=0,
        max_value=100,
        value=0,
        step=5,
    )

    row_limit = st.selectbox(
        "Clientes a mostrar",
        [50, 100, 250, 500, 1000],
        index=2,
    )

    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="filter-header">CLIENTE 360</div>', unsafe_allow_html=True)

    st.markdown('<div class="filter-card">', unsafe_allow_html=True)

    customer_id = st.number_input(
        "ID cliente",
        min_value=1,
        value=1,
        step=1,
    )

    search_customer = st.button(
        "Consultar cliente",
        type="primary",
        use_container_width=True,
    )

    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="filter-header">IDENTIDAD</div>', unsafe_allow_html=True)
    st.caption("NexaRisk")
    st.caption("Credit Risk Command Center")
    st.caption("Paleta: Midnight · Navy · Cyan · Gold")


# ============================================================
# DATA MUESTRA PARA GRAFICOS
# ============================================================

try:
    payload = load_portfolio(
        risk_level=risk_filter,
        limit=row_limit,
    )
    portfolio_df = normalize_df(payload)
except Exception as exc:
    portfolio_df = pd.DataFrame()
    with main_col:
        st.error("No fue posible cargar la cartera.")
        with st.expander("Detalle técnico"):
            st.exception(exc)


if not portfolio_df.empty:
    if prediction_filter != "TODAS" and "prediction" in portfolio_df.columns:
        portfolio_df = portfolio_df[
            portfolio_df["prediction"] == int(prediction_filter)
        ]

    if "probability_default" in portfolio_df.columns:
        portfolio_df = portfolio_df[
            portfolio_df["probability_default"] >= min_pd / 100
        ]


# ============================================================
# CONTENIDO PRINCIPAL
# ============================================================

with main_col:

    # --------------------------------------------------------
    # FILA 1: RIESGO + CLASIFICACION
    # --------------------------------------------------------

    c1, c2 = st.columns([1.15, 1], gap="medium")

    with c1:
        section("Distribución de riesgo", "Composición completa de la cartera por banda")

        risk_df = pd.DataFrame(
            {
                "Nivel": ["BAJO", "MEDIO", "ALTO", "CRITICO"],
                "Clientes": [bajo, medio, alto, critico],
            }
        )

        risk_chart = (
            alt.Chart(risk_df)
            .mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4)
            .encode(
                x=alt.X("Nivel:N", sort=["BAJO", "MEDIO", "ALTO", "CRITICO"], title=None),
                y=alt.Y("Clientes:Q", title=None),
                color=alt.Color(
                    "Nivel:N",
                    scale=alt.Scale(
                        domain=["BAJO", "MEDIO", "ALTO", "CRITICO"],
                        range=[
                            RISK_COLORS["BAJO"],
                            RISK_COLORS["MEDIO"],
                            RISK_COLORS["ALTO"],
                            RISK_COLORS["CRITICO"],
                        ],
                    ),
                    legend=None,
                ),
                tooltip=[
                    alt.Tooltip("Nivel:N", title="Nivel"),
                    alt.Tooltip("Clientes:Q", title="Clientes", format=","),
                ],
            )
        )

        st.altair_chart(dark_chart(risk_chart, 300), use_container_width=True)

    with c2:
        section("Clasificación del modelo", "Salida binaria de la cartera completa")

        class_df = pd.DataFrame(
            {
                "Clase": ["Predicción 0", "Predicción 1"],
                "Clientes": [
                    int(summary.get("prediction_0", 0)),
                    int(summary.get("prediction_1", 0)),
                ],
            }
        )

        class_chart = (
            alt.Chart(class_df)
            .mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4)
            .encode(
                x=alt.X("Clase:N", title=None),
                y=alt.Y("Clientes:Q", title=None),
                color=alt.Color(
                    "Clase:N",
                    scale=alt.Scale(
                        domain=["Predicción 0", "Predicción 1"],
                        range=[
                            CLASS_COLORS["Predicción 0"],
                            CLASS_COLORS["Predicción 1"],
                        ],
                    ),
                    legend=None,
                ),
                tooltip=[
                    alt.Tooltip("Clase:N", title="Clase"),
                    alt.Tooltip("Clientes:Q", title="Clientes", format=","),
                ],
            )
        )

        st.altair_chart(dark_chart(class_chart, 300), use_container_width=True)

    st.markdown(
        f"""
        <div class="executive-box">
        <b>Lectura ejecutiva.</b>
        {fmt_int(priority)} clientes se concentran en niveles
        <b style="color:{RISK_COLORS['ALTO']}">ALTO</b> o
        <b style="color:{RISK_COLORS['CRITICO']}">CRÍTICO</b>,
        equivalentes al <b>{fmt_pct(priority_pct)}</b> de la cartera.
        Esta población constituye la principal cola de seguimiento preventivo.
        </div>
        """,
        unsafe_allow_html=True,
    )

    # --------------------------------------------------------
    # FILA 2: EXPOSICION / EDAD / MORA
    # --------------------------------------------------------

    a1, a2, a3 = st.columns(3, gap="medium")

    with a1:
        section("Exposición por riesgo", "Suma de límites de crédito en la muestra consultada")

        if not portfolio_df.empty and {"risk_level", "limit_bal"}.issubset(portfolio_df.columns):
            exposure_df = (
                portfolio_df.groupby("risk_level", dropna=False)["limit_bal"]
                .sum()
                .reset_index()
                .rename(columns={"risk_level": "Riesgo", "limit_bal": "Exposición"})
            )

            exposure_chart = (
                alt.Chart(exposure_df)
                .mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4)
                .encode(
                    x=alt.X("Riesgo:N", title=None),
                    y=alt.Y("Exposición:Q", title=None),
                    color=alt.Color(
                        "Riesgo:N",
                        scale=alt.Scale(
                            domain=["BAJO", "MEDIO", "ALTO", "CRITICO"],
                            range=[
                                RISK_COLORS["BAJO"],
                                RISK_COLORS["MEDIO"],
                                RISK_COLORS["ALTO"],
                                RISK_COLORS["CRITICO"],
                            ],
                        ),
                        legend=None,
                    ),
                    tooltip=[
                        alt.Tooltip("Riesgo:N", title="Riesgo"),
                        alt.Tooltip("Exposición:Q", title="Exposición", format=",.0f"),
                    ],
                )
            )

            st.altair_chart(dark_chart(exposure_chart, 240), use_container_width=True)
        else:
            st.info("Sin datos suficientes.")

    with a2:
        section("PD por rango de edad", "Promedio de probabilidad de incumplimiento")

        if not portfolio_df.empty and {"age", "probability_default"}.issubset(portfolio_df.columns):
            age_df = portfolio_df.copy()
            age_df["Rango edad"] = pd.cut(
                age_df["age"],
                bins=[0, 29, 39, 49, 59, 69, 200],
                labels=["<30", "30–39", "40–49", "50–59", "60–69", "70+"],
            )

            age_pd = (
                age_df.groupby("Rango edad", observed=False)["probability_default"]
                .mean()
                .mul(100)
                .reset_index(name="PD")
            )

            age_chart = (
                alt.Chart(age_pd)
                .mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4)
                .encode(
                    x=alt.X("Rango edad:N", title=None),
                    y=alt.Y("PD:Q", title="PD %"),
                    color=alt.Color(
                        "PD:Q",
                        scale=alt.Scale(range=[BLUE, CYAN, GOLD]),
                        legend=None,
                    ),
                    tooltip=[
                        alt.Tooltip("Rango edad:N", title="Rango"),
                        alt.Tooltip("PD:Q", title="PD", format=".1f"),
                    ],
                )
            )

            st.altair_chart(dark_chart(age_chart, 240), use_container_width=True)
        else:
            st.info("Sin datos suficientes.")

    with a3:
        section("Máximo atraso vs PD", "PD promedio según severidad máxima de atraso")

        if not portfolio_df.empty and {"pay_max_delay", "probability_default"}.issubset(portfolio_df.columns):
            delay_pd = (
                portfolio_df.groupby("pay_max_delay")["probability_default"]
                .mean()
                .mul(100)
                .reset_index(name="PD")
                .sort_values("pay_max_delay")
            )

            delay_chart = (
                alt.Chart(delay_pd)
                .mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4)
                .encode(
                    x=alt.X("pay_max_delay:O", title="Máx. atraso"),
                    y=alt.Y("PD:Q", title="PD %"),
                    color=alt.Color(
                        "PD:Q",
                        scale=alt.Scale(range=[CYAN, GOLD, RISK_COLORS["CRITICO"]]),
                        legend=None,
                    ),
                    tooltip=[
                        alt.Tooltip("pay_max_delay:O", title="Máx. atraso"),
                        alt.Tooltip("PD:Q", title="PD", format=".1f"),
                    ],
                )
            )

            st.altair_chart(dark_chart(delay_chart, 240), use_container_width=True)
        else:
            st.info("Sin datos suficientes.")

    # --------------------------------------------------------
    # FILA 3
    # --------------------------------------------------------

    b1, b2, b3 = st.columns(3, gap="medium")

    with b1:
        section("Atrasos recientes", "Clientes por número de meses con atraso reciente")

        if not portfolio_df.empty and "recent_delay_months" in portfolio_df.columns:
            recent_df = (
                portfolio_df["recent_delay_months"]
                .value_counts(dropna=False)
                .sort_index()
                .reset_index()
            )
            recent_df.columns = ["Meses", "Clientes"]

            recent_chart = (
                alt.Chart(recent_df)
                .mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4)
                .encode(
                    x=alt.X("Meses:O", title="Meses con atraso"),
                    y=alt.Y("Clientes:Q", title=None),
                    color=alt.Color(
                        "Meses:O",
                        scale=alt.Scale(
                            range=[
                                RISK_COLORS["BAJO"],
                                RISK_COLORS["MEDIO"],
                                RISK_COLORS["ALTO"],
                                RISK_COLORS["CRITICO"],
                            ]
                        ),
                        legend=None,
                    ),
                    tooltip=[
                        alt.Tooltip("Meses:O", title="Meses"),
                        alt.Tooltip("Clientes:Q", title="Clientes"),
                    ],
                )
            )

            st.altair_chart(dark_chart(recent_chart, 240), use_container_width=True)
        else:
            st.info("Sin datos suficientes.")

    with b2:
        section("Pago / facturación", "Distribución del ratio de pago sobre facturación")

        if not portfolio_df.empty and "payment_bill_ratio_total" in portfolio_df.columns:
            ratio_df = portfolio_df.copy()
            ratio_df["Banda"] = pd.cut(
                ratio_df["payment_bill_ratio_total"],
                bins=[-0.001, 0.25, 0.50, 0.75, 1.00, float("inf")],
                labels=["0–.25", ".25–.50", ".50–.75", ".75–1", "1+"],
            )

            ratio_count = (
                ratio_df["Banda"]
                .value_counts(sort=False, dropna=False)
                .reset_index()
            )
            ratio_count.columns = ["Banda", "Clientes"]

            ratio_chart = (
                alt.Chart(ratio_count)
                .mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4)
                .encode(
                    x=alt.X("Banda:N", title=None),
                    y=alt.Y("Clientes:Q", title=None),
                    color=alt.Color(
                        "Banda:N",
                        scale=alt.Scale(
                            range=[
                                RISK_COLORS["CRITICO"],
                                RISK_COLORS["ALTO"],
                                RISK_COLORS["MEDIO"],
                                CYAN,
                                RISK_COLORS["BAJO"],
                            ]
                        ),
                        legend=None,
                    ),
                    tooltip=[
                        alt.Tooltip("Banda:N", title="Ratio"),
                        alt.Tooltip("Clientes:Q", title="Clientes"),
                    ],
                )
            )

            st.altair_chart(dark_chart(ratio_chart, 240), use_container_width=True)
        else:
            st.info("Sin datos suficientes.")

    with b3:
        section("Top exposición prioritaria", "Mayores líneas dentro de la muestra filtrada")

        if not portfolio_df.empty and {"id", "limit_bal", "risk_level"}.issubset(portfolio_df.columns):
            top_exp = (
                portfolio_df.sort_values("limit_bal", ascending=False)
                .head(10)[["id", "limit_bal", "risk_level"]]
                .copy()
            )
            top_exp["Cliente"] = top_exp["id"].astype(str)

            top_chart = (
                alt.Chart(top_exp)
                .mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4)
                .encode(
                    x=alt.X("Cliente:N", sort="-y", title=None),
                    y=alt.Y("limit_bal:Q", title="Límite"),
                    color=alt.Color(
                        "risk_level:N",
                        scale=alt.Scale(
                            domain=["BAJO", "MEDIO", "ALTO", "CRITICO"],
                            range=[
                                RISK_COLORS["BAJO"],
                                RISK_COLORS["MEDIO"],
                                RISK_COLORS["ALTO"],
                                RISK_COLORS["CRITICO"],
                            ],
                        ),
                        legend=None,
                    ),
                    tooltip=[
                        alt.Tooltip("Cliente:N", title="Cliente"),
                        alt.Tooltip("limit_bal:Q", title="Límite", format=",.0f"),
                        alt.Tooltip("risk_level:N", title="Riesgo"),
                    ],
                )
            )

            st.altair_chart(dark_chart(top_chart, 240), use_container_width=True)
        else:
            st.info("Sin datos suficientes.")

    # --------------------------------------------------------
    # CARTERA PRIORIZADA
    # --------------------------------------------------------

    st.write("")
    section("Cartera priorizada", "Ordenada por mayor probabilidad de incumplimiento")

    if portfolio_df.empty:
        st.warning("No existen registros para los filtros seleccionados.")
    else:
        table_df = portfolio_df.copy()

        if "probability_default" in table_df.columns:
            table_df = table_df.sort_values("probability_default", ascending=False)
            table_df["PD %"] = table_df["probability_default"] * 100

        if "risk_level" in table_df.columns:
            table_df["Riesgo"] = table_df["risk_level"].map(
                {
                    "BAJO": "BAJO",
                    "MEDIO": "MEDIO",
                    "ALTO": "ALTO",
                    "CRITICO": "CRÍTICO",
                }
            )

        wanted = [
            "id",
            "PD %",
            "prediction",
            "Riesgo",
            "limit_bal",
            "age",
            "pay_max_delay",
            "recent_delay_months",
            "consecutive_delay_months",
            "payment_bill_ratio_total",
            "recommendation",
        ]

        wanted = [c for c in wanted if c in table_df.columns]

        display_df = table_df[wanted].copy().rename(
            columns={
                "id": "Cliente",
                "prediction": "Pred.",
                "limit_bal": "Límite",
                "age": "Edad",
                "pay_max_delay": "Máx. atraso",
                "recent_delay_months": "Atrasos recientes",
                "consecutive_delay_months": "Atrasos consecutivos",
                "payment_bill_ratio_total": "Ratio pago/fact.",
                "recommendation": "Acción sugerida",
            }
        )

        st.caption(f"{len(display_df):,} clientes mostrados")

        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True,
            height=500,
            column_config={
                "Cliente": st.column_config.NumberColumn("Cliente", format="%d"),
                "PD %": st.column_config.ProgressColumn(
                    "PD %",
                    min_value=0,
                    max_value=100,
                    format="%.1f%%",
                ),
                "Pred.": st.column_config.NumberColumn("Pred.", format="%d"),
                "Límite": st.column_config.NumberColumn("Límite", format="%.0f"),
                "Ratio pago/fact.": st.column_config.NumberColumn(
                    "Ratio pago/fact.",
                    format="%.3f",
                ),
            },
        )

        csv = display_df.to_csv(index=False).encode("utf-8-sig")

        st.download_button(
            "Descargar cartera filtrada",
            data=csv,
            file_name="cartera_filtrada_nexarisk.csv",
            mime="text/csv",
        )


# ============================================================
# CLIENTE 360
# ============================================================

if search_customer:
    st.divider()

    try:
        customer = load_customer(int(customer_id))

        st.subheader(f"Cliente 360 · #{int(customer_id)}")

        x1, x2, x3, x4 = st.columns(4)

        x1.metric(
            "PD",
            fmt_pct(customer.get("probability_default")),
        )

        x2.metric(
            "Nivel de riesgo",
            customer.get("risk_level", "N/D"),
        )

        x3.metric(
            "Clasificación",
            customer.get("prediction", "N/D"),
        )

        x4.metric(
            "Límite de crédito",
            fmt_money(customer.get("limit_bal")),
        )

        st.markdown("#### Recomendación de gestión")
        st.info(customer.get("recommendation", "No disponible"))

        y1, y2, y3, y4 = st.columns(4)

        y1.metric("Edad", customer.get("age", "N/D"))
        y2.metric("Máximo atraso", customer.get("pay_max_delay", "N/D"))
        y3.metric("Atrasos recientes", customer.get("recent_delay_months", "N/D"))
        y4.metric("Atrasos consecutivos", customer.get("consecutive_delay_months", "N/D"))

    except Exception as exc:
        st.error("No fue posible consultar el cliente.")
        with st.expander("Detalle técnico"):
            st.exception(exc)


# ============================================================
# PIE
# ============================================================

st.divider()

f1, f2, f3 = st.columns([2, 1, 1])

with f1:
    st.caption("NexaRisk · Proyecto Productivo IIIA")

with f2:
    st.caption(f"Modelo: {summary.get('model_version', 'N/D')}")

with f3:
    st.caption("FastAPI · Supabase · Streamlit")
