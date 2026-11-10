import os
import time
from typing import Any

import altair as alt
import pandas as pd
import requests
import streamlit as st
from review_ui import render_review_panel, render_supervisor_panel


# ============================================================
# CONFIGURACION GENERAL
# ============================================================

st.set_page_config(
    page_title="NexaRisk | Credit Risk Command Center",
    page_icon="💠",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# PALETA INSTITUCIONAL
# ============================================================

MIDNIGHT = "#F3F6FA"
NAVY = "#10243F"
SLATE = "#233E5F"
PANEL = "#FFFFFF"
PANEL_2 = "#F8FAFC"
BORDER = "#D8E0EA"
CYAN = "#2B648B"
BLUE = "#7199C2"
GOLD = "#C58A2A"
TEXT = "#15253B"
MUTED = "#617184"

# Sobriedad visual: los colores de riesgo se reservan para la severidad.
RISK_COLORS = {
    "BAJO": "#76A58B",
    "MEDIO": "#D6B36C",
    "ALTO": "#CB925E",
    "CRITICO": "#B65A68",
}
CLASS_COLORS = {
    "Predicción 0": "#76A58B",
    "Predicción 1": "#D6B36C",
}

# ============================================================
# CSS
# ============================================================

st.markdown(
    f"""
    <style>
    /* NexaRisk UX 3.0: light institutional visual design; business logic unchanged. */
    .stApp {{background:#F3F6FA;color:{TEXT};}}
    [data-testid="stHeader"] {{background:rgba(243,246,250,.98);}}
    .block-container {{max-width:1680px;padding-top:1.2rem;padding-bottom:2.4rem;}}
    /* No global h/p/label overrides: sidebar has independent contrast. */
    [data-testid="stMarkdownContainer"] p {{line-height:1.48;}}
    .brand-shell {{background:#FFFFFF;border:1px solid {BORDER};border-radius:16px;
        padding:18px 24px;margin-bottom:16px;box-shadow:0 3px 12px rgba(18,37,62,.045);}}
    .brand-row {{display:flex;align-items:center;justify-content:space-between;gap:20px;flex-wrap:wrap;}}
    .brand-left {{display:flex;align-items:center;gap:16px;min-width:0;flex-wrap:wrap;}}
    .brand-mark {{width:52px;height:52px;min-width:52px;border-radius:12px;
        display:flex;align-items:center;justify-content:center;background:{NAVY};
        color:#FFFFFF;font-weight:800;font-size:21px;line-height:1;letter-spacing:0;}}
    .brand-name {{font-size:29px;font-weight:800;color:{NAVY};line-height:1.2;
        letter-spacing:-.7px;white-space:nowrap;overflow:visible;}}
    .brand-sub {{margin-top:5px;color:{MUTED};font-size:12px;line-height:1.5;}}
    .api-state {{color:{MUTED};font-size:11px;line-height:1.7;text-align:right;}}
    .api-online {{color:#24744E;background:#E8F5EC;border-radius:20px;
        padding:4px 10px;font-weight:750;letter-spacing:.1px;}}
    .kpi {{background:#FFFFFF;border:1px solid {BORDER};border-left:4px solid {CYAN};
        border-radius:13px;padding:19px 17px;min-height:132px;
        box-shadow:0 3px 12px rgba(18,37,62,.04);}}
    .kpi-label {{color:{NAVY};font-size:12px;letter-spacing:0;font-weight:700;}}
    .kpi-value {{color:{NAVY};font-size:27px;font-weight:800;margin-top:8px;line-height:1.2;}}
    .kpi-note {{color:{MUTED};font-size:11px;margin-top:7px;line-height:1.35;}}
    .panel-title {{color:{NAVY};font-size:17px;font-weight:800;margin:8px 0 3px;}}
    .panel-sub {{color:{MUTED};font-size:11px;margin-bottom:10px;}}
    .filter-header {{background:{NAVY};border:1px solid {NAVY};border-radius:10px;
        padding:11px 13px;color:#FFFFFF;font-size:12px;font-weight:750;margin-bottom:10px;}}
    .filter-card {{background:#FFFFFF;border:1px solid {BORDER};border-radius:12px;
        padding:13px 12px 7px;margin-bottom:13px;}}
    .executive-box {{background:#F8FAFC;border:1px solid {BORDER};border-left:4px solid {GOLD};
        border-radius:10px;padding:13px 16px;color:{TEXT};font-size:12px;line-height:1.55;
        margin:12px 0 16px;}}
    div[data-testid="stMetric"] {{background:#FFFFFF;border:1px solid {BORDER};border-radius:12px;padding:13px;}}
    div[data-testid="stMetricLabel"] {{color:{MUTED};}}
    div[data-testid="stMetricValue"] {{color:{NAVY};}}
    div[data-baseweb="select"] > div {{background:#FFFFFF;border-color:{BORDER};color:{TEXT};}}
    div[data-testid="stNumberInput"] input {{background:#FFFFFF;color:{TEXT};}}
    .stButton > button[kind="primary"],.stButton > button[data-testid="stBaseButton-primary"] {{
        background:{NAVY};color:#FFFFFF;border:1px solid {NAVY};border-radius:9px;font-weight:700;}}
    .stButton > button[kind="primary"]:hover,.stButton > button[data-testid="stBaseButton-primary"]:hover {{
        background:#24476B;color:#FFFFFF;border-color:#24476B;}}
    .stButton > button:not([kind="primary"]):not([data-testid="stBaseButton-primary"]) {{
        border-radius:9px;border-color:{BORDER};}}
    [data-testid="stDataFrame"] {{border:1px solid {BORDER};border-radius:10px;overflow:hidden;}}
    [data-testid="stAlert"] {{border-radius:11px;}}
    hr {{border-color:{BORDER};}}
    @media (max-width:900px) {{.brand-name {{font-size:24px;}} .api-state {{text-align:left;}}}}
    [data-testid="stSidebar"] {{background:linear-gradient(180deg,#11243E 0%,#172F4D 100%);}}
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2 {{color:#F8FAFC !important;}}
    [data-testid="stSidebar"] [data-testid="stRadio"] label p {{color:#F8FAFC !important;}}
    [data-testid="stSidebar"] [data-baseweb="select"] > div {{background:#FFFFFF !important;color:#15253B !important;}}
    [data-testid="stSidebar"] [data-testid="stNumberInput"] input {{background:#FFFFFF !important;color:#15253B !important;}}
    [data-testid="stSidebar"] [data-testid="stSlider"] p {{color:#FFFFFF !important;}}
    [data-testid="stSidebar"] .stButton button {{background:#FFFFFF;color:#11243E;border-radius:9px;}}
    [data-testid="stSidebar"] .stButton button:hover {{background:#E7EFF8;color:#11243E;}}
    [data-testid="stSidebar"] [data-testid="stCaptionContainer"] p {{color:#B9CBDF !important;}}
    .stApp [data-testid="stVegaLiteChart"] {{background:#FFFFFF;border:1px solid #D8E0EA;border-radius:13px;padding:10px;}}
    .stApp [data-testid="stVegaLiteChart"] canvas {{background:#FFFFFF;}}
    /* Real chart cards: white background, spacing and readable labels. */
    .stApp [data-testid="stVegaLiteChart"] {{background:#FFFFFF !important;
        border:1px solid #D8E0EA;border-radius:14px;padding:16px 12px 8px;
        box-shadow:0 2px 9px rgba(16,36,63,.035);}}
    .stApp [data-testid="stVegaLiteChart"] canvas,
    .stApp [data-testid="stVegaLiteChart"] svg {{background:#FFFFFF !important;}}
    /* Streamlit native table + progress column must match the light UI. */
    .stApp [data-testid="stDataFrame"] {{background:#FFFFFF !important;
        border:1px solid #D8E0EA;border-radius:12px;overflow:hidden;}}
    .stApp [data-testid="stDataFrame"] [data-testid="stDataFrameResizable"] {{background:#FFFFFF !important;}}
    .stApp [data-testid="stDataFrame"] canvas {{background:#FFFFFF !important;}}
    .stApp [data-testid="stDownloadButton"] button {{background:#FFFFFF !important;
        color:#10243F !important;border:1px solid #BAC8D8 !important;
        font-weight:650 !important;min-height:42px;}}
    .stApp [data-testid="stDownloadButton"] button:hover {{background:#EAF0F7 !important;}}
    .stApp [data-testid="stMarkdownContainer"] .panel-title {{font-size:17px;}}
    [data-testid="stSidebar"] {{min-width:252px;}}
    [data-testid="stSidebar"] [data-testid="stRadio"] label {{padding:6px 5px;}}
    [data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] {{gap:4px;}}
    [data-testid="stSidebar"] [data-testid="stRadio"] label:has(input:checked) {{background:#294B70;border-radius:8px;}}
    [data-testid="stSidebar"] [data-testid="stRadio"] label:hover {{background:#233D5D;border-radius:8px;}}
    @media (max-width:1100px) {{.kpi-value {{font-size:23px;}} .kpi-label {{font-size:11px;}}}}

    [data-testid="stHeader"] {{background:rgba(243,246,250,.98);}}
    </style>
    """,
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


@st.cache_data(ttl=60)
def load_analytics(risk_level="TODOS", prediction="TODAS", min_pd=0):
    params = {"min_pd": min_pd / 100}
    if risk_level != "TODOS":
        params["risk_level"] = risk_level
    if prediction != "TODAS":
        params["prediction"] = int(prediction)
    return api_get("/portfolio/analytics", params=params)


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
        <div class="kpi" style="border-left-color:{accent};">
            <div class="kpi-label">{label}</div>
            <div class="kpi-value">{value}</div>
            <div class="kpi-note">{note}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def dark_chart(chart: alt.Chart, height=280):
    """Institutional LIGHT chart. Explicit Vega theme prevents dark chart regression."""
    return (
        chart.properties(height=height, background="#FFFFFF",
                         padding={"left": 10, "right": 14, "top": 18, "bottom": 10})
        .configure_view(strokeOpacity=0, fill="#FFFFFF")
        .configure_axis(
            gridColor="#E8EDF4", gridOpacity=0.8, gridWidth=1,
            domain=False, ticks=False,
            labelColor="#43546A", titleColor="#52657A",
            labelFont="Arial", titleFont="Arial",
            labelFontSize=11, titleFontSize=11, labelPadding=8,
        )
        .configure_legend(labelColor="#43546A", titleColor="#52657A")
        .configure(background="#FFFFFF")
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
                <span class="api-online">● En línea</span><br>
                Modelo {summary.get("model_version", "N/D")}<br>
                FastAPI · Supabase · Streamlit
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# NAVEGACION Y FILTROS - SIDEBAR REAL
# ============================================================
with st.sidebar:
    st.markdown("### ◈ NexaRisk")
    st.caption("Credit Risk Command Center")
    page = st.radio(
        "Navegación",
        ["Cartera", "Cliente 360", "Revisión de casos", "Supervisión", "Resultados"],
        label_visibility="collapsed",
        key="nexarisk_page",
    )
    st.divider()
    st.markdown("**Filtros de cartera**")
    risk_filter = st.selectbox("Nivel de riesgo", ["TODOS", "CRITICO", "ALTO", "MEDIO", "BAJO"], key="risk_filter")
    prediction_filter = st.selectbox("Clasificación", ["TODAS", "1", "0"], key="prediction_filter")
    min_pd = st.slider("PD mínima (%)", 0, 100, 0, 5, key="min_pd")
    row_limit = st.selectbox("Clientes a mostrar", [50, 100, 250, 500, 1000], index=2, key="row_limit")
    st.divider()
    st.caption("Modelo productivo: XGBoost V2")
    st.caption("FastAPI · Supabase · Streamlit")

# La navegación conserva los módulos originales y su autenticación.
main_col = st.container()

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

if page == "Cartera":
    k1, k2, k3, k4, k5 = st.columns(5)

    with k1:
        kpi_card("Cartera evaluada", fmt_int(total), "Scoring vigente", NAVY)

    with k2:
        kpi_card("PD promedio", fmt_pct(summary.get("pd_promedio")), "Probabilidad media", "#55856B")

    with k3:
        kpi_card("Gestión prioritaria", fmt_int(priority), f"{fmt_pct(priority_pct)} en Alto + Crítico", GOLD)

    with k4:
        kpi_card("Predicción = 1", fmt_int(summary.get("prediction_1")), "Potencial incumplimiento", "#7C8896")

    with k5:
        kpi_card("Predicción = 0", fmt_int(summary.get("prediction_0")), "Sin señal de incumplimiento", "#6A7D94")

    st.markdown('<div style="height:12px"></div>', unsafe_allow_html=True)


if page == "Cartera":
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


    # La API calcula los graficos sobre toda la poblacion filtrada, no sobre
    # los primeros N clientes ordenados por PD.
    try:
        analytics = load_analytics(risk_filter, prediction_filter, min_pd)
    except Exception as exc:
        analytics = None
        with main_col:
            st.error("No fue posible calcular los graficos de la cartera completa.")
            st.caption("Los graficos analiticos se ocultan para no mostrar datos sesgados.")
            with st.expander("Detalle tecnico"):
                st.exception(exc)


    def analytics_frame(key):
        if not analytics:
            return pd.DataFrame()
        return pd.DataFrame(analytics.get(key) or [])


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

            risk_labels = alt.Chart(risk_df).mark_text(dy=-10, color=NAVY, fontSize=12, fontWeight="bold").encode(
                x=alt.X("Nivel:N", sort=["BAJO", "MEDIO", "ALTO", "CRITICO"]),
                y=alt.Y("Clientes:Q"),
                text=alt.Text("Clientes:Q", format=",.0f"),
            )
            st.altair_chart(dark_chart(risk_chart + risk_labels, 265), use_container_width=True, theme=None)

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

            class_labels = alt.Chart(class_df).mark_text(dy=-10, color=NAVY, fontSize=12, fontWeight="bold").encode(
                x=alt.X("Clase:N"), y=alt.Y("Clientes:Q"),
                text=alt.Text("Clientes:Q", format=",.0f"),
            )
            st.altair_chart(dark_chart(class_chart + class_labels, 265), use_container_width=True, theme=None)

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
        if analytics:
            n_filtered = int((analytics.get("overall") or {}).get("clientes") or 0)
            st.caption(
                f"Gráficos inferiores: {n_filtered:,} clientes de la cartera filtrada completa. "
                f"La tabla parte de hasta {row_limit:,} clientes con mayor PD y aplica filtros locales. "
                "Los indicadores y gráficos superiores corresponden a toda la cartera sin filtros."
            )

        # FILA 2: EXPOSICION / EDAD / MORA
        # --------------------------------------------------------
        a1, a2, a3 = st.columns(3, gap="medium")

        with a1:
            section("Exposición por riesgo", "Suma de límites en toda la cartera filtrada")
            exposure = analytics_frame("exposure")
            if not exposure.empty:
                exposure["exposicion"] = pd.to_numeric(exposure["exposicion"], errors="coerce").fillna(0)
                chart = alt.Chart(exposure).mark_bar().encode(
                    x=alt.X("categoria:N", sort=["BAJO", "MEDIO", "ALTO", "CRITICO"], title="Riesgo"),
                    y=alt.Y("exposicion:Q", title="Límite total", axis=alt.Axis(format="~s")),
                    color=alt.Color("categoria:N", scale=alt.Scale(
                        domain=["BAJO", "MEDIO", "ALTO", "CRITICO"],
                        range=[RISK_COLORS[k] for k in ["BAJO", "MEDIO", "ALTO", "CRITICO"]]), legend=None),
                    tooltip=[alt.Tooltip("categoria:N", title="Riesgo"),
                             alt.Tooltip("clientes:Q", title="Clientes", format=","),
                             alt.Tooltip("exposicion:Q", title="Límite total", format=",.0f")],
                )
                st.altair_chart(dark_chart(chart, 225), use_container_width=True, theme=None)
            else:
                st.info("Sin registros para estos filtros.")

        with a2:
            section("PD por rango de edad", "Promedio sobre todos los clientes filtrados")
            ages = analytics_frame("age")
            if not ages.empty:
                ages["PD"] = pd.to_numeric(ages["pd_promedio"], errors="coerce") * 100
                chart = alt.Chart(ages).mark_bar(color=BLUE).encode(
                    x=alt.X("categoria:N", sort=["<30", "30-39", "40-49", "50-59", "60-69", "70+", "Sin dato"], title="Edad"),
                    y=alt.Y("PD:Q", title="PD promedio (%)", scale=alt.Scale(domain=[0, 100])),
                    tooltip=[alt.Tooltip("categoria:N", title="Edad"),
                             alt.Tooltip("clientes:Q", title="Clientes", format=","),
                             alt.Tooltip("PD:Q", title="PD promedio (%)", format=".2f")],
                )
                st.altair_chart(dark_chart(chart, 225), use_container_width=True, theme=None)
            else:
                st.info("Sin registros para estos filtros.")

        with a3:
            section("Máximo atraso vs PD", "PD media y número de clientes por atraso")
            delays = analytics_frame("delay")
            if not delays.empty:
                delays["PD"] = pd.to_numeric(delays["pd_promedio"], errors="coerce") * 100
                delays["orden"] = pd.to_numeric(delays["categoria"], errors="coerce").fillna(999)
                delays = delays.sort_values("orden")
                chart = alt.Chart(delays).mark_bar(color=CYAN).encode(
                    x=alt.X("categoria:N", sort=delays["categoria"].tolist(), title="Máx. atraso"),
                    y=alt.Y("PD:Q", title="PD promedio (%)", scale=alt.Scale(domain=[0, 100])),
                    tooltip=[alt.Tooltip("categoria:N", title="Máx. atraso"),
                             alt.Tooltip("clientes:Q", title="Clientes", format=","),
                             alt.Tooltip("PD:Q", title="PD promedio (%)", format=".2f")],
                )
                st.altair_chart(dark_chart(chart, 225), use_container_width=True, theme=None)
            else:
                st.info("Sin registros para estos filtros.")

        # --------------------------------------------------------
        # FILA 3: ATRASOS / RATIOS / EXPOSICION PRIORITARIA
        # --------------------------------------------------------
        b1, b2, b3 = st.columns(3, gap="medium")

        with b1:
            section("Atrasos recientes", "Clientes de la cartera filtrada completa")
            recent = analytics_frame("recent")
            if not recent.empty:
                recent["orden"] = pd.to_numeric(recent["categoria"], errors="coerce").fillna(999)
                recent = recent.sort_values("orden")
                chart = alt.Chart(recent).mark_bar(color=GOLD).encode(
                    x=alt.X("categoria:N", sort=recent["categoria"].tolist(), title="Meses con atraso"),
                    y=alt.Y("clientes:Q", title="Clientes"),
                    tooltip=[alt.Tooltip("categoria:N", title="Meses"),
                             alt.Tooltip("clientes:Q", title="Clientes", format=",")],
                )
                st.altair_chart(dark_chart(chart, 225), use_container_width=True, theme=None)
            else:
                st.info("Sin registros para estos filtros.")

        with b2:
            section("Pago / facturación", "Distribución del ratio en toda la cartera filtrada")
            ratios = analytics_frame("ratio")
            if not ratios.empty:
                chart = alt.Chart(ratios).mark_bar(color=RISK_COLORS["BAJO"]).encode(
                    x=alt.X("categoria:N", sort=["Negativo", "0-0.25", "0.25-0.50", "0.50-0.75", "0.75-1", ">1", "Sin dato"], title="Ratio"),
                    y=alt.Y("clientes:Q", title="Clientes"),
                    tooltip=[alt.Tooltip("categoria:N", title="Ratio"),
                             alt.Tooltip("clientes:Q", title="Clientes", format=",")],
                )
                st.altair_chart(dark_chart(chart, 225), use_container_width=True, theme=None)
            else:
                st.info("Sin registros para estos filtros.")

        with b3:
            section("Top exposición prioritaria", f"Top 10 de los {row_limit} clientes listados (muestra por PD)")
            if not portfolio_df.empty and {"id", "limit_bal", "risk_level"}.issubset(portfolio_df.columns):
                top_exp = portfolio_df.nlargest(10, "limit_bal")[["id", "limit_bal", "risk_level"]].copy()
                top_exp["Cliente"] = top_exp["id"].astype(str)
                chart = alt.Chart(top_exp).mark_bar().encode(
                    x=alt.X("Cliente:N", sort="-y", title="Cliente"),
                    y=alt.Y("limit_bal:Q", title="Límite"),
                    color=alt.Color("risk_level:N", scale=alt.Scale(
                        domain=["BAJO", "MEDIO", "ALTO", "CRITICO"],
                        range=[RISK_COLORS[k] for k in ["BAJO", "MEDIO", "ALTO", "CRITICO"]]), legend=None),
                    tooltip=[alt.Tooltip("Cliente:N", title="Cliente"),
                             alt.Tooltip("limit_bal:Q", title="Límite", format=",.0f"),
                             alt.Tooltip("risk_level:N", title="Riesgo")],
                )
                st.altair_chart(dark_chart(chart, 225), use_container_width=True, theme=None)
            else:
                st.info("Sin registros para estos filtros.")

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
                height=430,
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
# CLIENTE 360, ANALISTA Y SUPERVISOR
# ============================================================
if page in ("Cliente 360", "Revisión de casos"):
    st.subheader("Cliente 360" if page == "Cliente 360" else "Revisión del analista")
    st.caption("Consulta individual y registro de observaciones con evidencia.")
    customer_id = st.number_input("ID cliente", min_value=1, value=int(st.session_state.get("nexarisk_selected_customer_id", 1)), step=1)
    if st.button("Consultar cliente", type="primary", key="customer_lookup"):
        st.session_state["nexarisk_selected_customer_id"] = int(customer_id)
    selected_customer_id = st.session_state.get("nexarisk_selected_customer_id")
    if selected_customer_id is not None:
        try:
            customer = load_customer(int(selected_customer_id))
            st.markdown(f"### Cliente 360 · #{int(selected_customer_id)}")
            x1, x2, x3, x4 = st.columns(4)
            x1.metric("PD", fmt_pct(customer.get("probability_default")))
            x2.metric("Nivel de riesgo", customer.get("risk_level", "N/D"))
            x3.metric("Clasificación", customer.get("prediction", "N/D"))
            x4.metric("Límite de crédito", fmt_money(customer.get("limit_bal")))
            st.markdown("#### Recomendación de gestión")
            st.info(customer.get("recommendation", "No disponible"))
            y1, y2, y3, y4 = st.columns(4)
            y1.metric("Edad", customer.get("age", "N/D"))
            y2.metric("Máximo atraso", customer.get("pay_max_delay", "N/D"))
            y3.metric("Atrasos recientes", customer.get("recent_delay_months", "N/D"))
            y4.metric("Atrasos consecutivos", customer.get("consecutive_delay_months", "N/D"))
            # Mantener la lógica de autenticación y registro de review_ui.py.
            render_review_panel(customer, API_BASE_URL)
        except Exception as exc:
            st.error("No fue posible consultar el cliente.")
            with st.expander("Detalle técnico"):
                st.exception(exc)

if page == "Supervisión":
    st.subheader("Administración · Supervisor")
    st.caption("Revisiones pendientes, aprobaciones, rechazos y trazabilidad.")
    # No sustituir ni duplicar controles de identidad existentes.
    render_supervisor_panel(API_BASE_URL)

if page == "Resultados":
    st.subheader("Resultados del modelo")
    st.caption("Indicadores vigentes de cartera y versión productiva.")
    r1, r2, r3 = st.columns(3)
    r1.metric("Cartera evaluada", fmt_int(total))
    r2.metric("PD promedio", fmt_pct(summary.get("pd_promedio")))
    r3.metric("Modelo", str(summary.get("model_version", "N/D")))
    st.info("XGBoost V2 permanece en producción. V3 es un experimento histórico no promovido; sus métricas no se consultan desde esta API.")

st.divider()
st.caption(f"NexaRisk · Proyecto Productivo IIIA · Modelo: {summary.get('model_version', 'N/D')} · FastAPI / Supabase / Streamlit")
