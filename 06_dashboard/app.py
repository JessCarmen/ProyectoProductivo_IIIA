import os
import time
import textwrap
from typing import Any

import pandas as pd
import requests
import streamlit as st

# ============================================================
# PAGE
# ============================================================
st.set_page_config(
    page_title="NexaRisk | Credit Risk Command Center",
    page_icon="NR",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ============================================================
# BRAND PALETTE
# ============================================================
BG = "#07111F"
PANEL = "#0C1B2A"
PANEL_2 = "#102436"
PANEL_3 = "#12283A"
BORDER = "#22384A"
TEXT = "#EAF1F7"
MUTED = "#8FA4B7"
ACCENT = "#19C3C8"
GOLD = "#D7B56D"
GREEN = "#2EA66F"
AMBER = "#D9A441"
ORANGE = "#D97835"
RED = "#D95656"


def html(content: str) -> None:
    st.markdown(textwrap.dedent(content).strip(), unsafe_allow_html=True)


html(
    f"""
    <style>
    .stApp {{ background: {BG}; color: {TEXT}; }}
    [data-testid="stHeader"] {{ background: transparent; }}
    [data-testid="stToolbar"] {{ visibility: hidden; }}
    .block-container {{ max-width: 1780px; padding-top: 1rem; padding-bottom: 2rem; }}

    h1, h2, h3, h4, p, label {{ color: {TEXT} !important; }}
    [data-testid="stCaptionContainer"] p {{ color: {MUTED} !important; }}

    .nr-topbar {{
        background: linear-gradient(110deg, #081725 0%, #0C2234 58%, #0E3946 100%);
        border: 1px solid {BORDER}; border-radius: 18px; padding: 22px 26px;
        display: flex; justify-content: space-between; align-items: center;
        box-shadow: 0 16px 42px rgba(0,0,0,.26); margin-bottom: 16px;
    }}
    .nr-brand {{ display:flex; align-items:center; gap:16px; }}
    .nr-mark {{ width:58px; height:58px; border-radius:14px; background:{ACCENT}; color:{BG};
        font-weight:900; font-size:22px; display:flex; align-items:center; justify-content:center; letter-spacing:-1px; }}
    .nr-name {{ color:{TEXT}; font-weight:850; font-size:28px; line-height:1; }}
    .nr-sub {{ color:{MUTED}; font-size:12px; margin-top:7px; letter-spacing:.2px; }}
    .nr-meta {{ text-align:right; color:{MUTED}; font-size:11px; line-height:1.8; }}
    .nr-live {{ color:{ACCENT}; font-weight:800; letter-spacing:.4px; }}

    .kpi {{ background:{PANEL}; border:1px solid {BORDER}; border-radius:14px; padding:16px 17px;
        min-height:110px; box-shadow:0 8px 22px rgba(0,0,0,.12); }}
    .kpi-label {{ color:{MUTED}; font-size:10px; font-weight:800; letter-spacing:.75px; text-transform:uppercase; }}
    .kpi-value {{ color:{TEXT}; font-size:29px; font-weight:850; margin-top:4px; }}
    .kpi-note {{ color:{MUTED}; font-size:10px; margin-top:4px; }}
    .kpi-accent {{ border-top:3px solid {ACCENT}; }}
    .kpi-gold {{ border-top:3px solid {GOLD}; }}
    .kpi-red {{ border-top:3px solid {RED}; }}

    .section-head {{ color:{TEXT}; font-weight:800; font-size:15px; margin-bottom:2px; }}
    .section-sub {{ color:{MUTED}; font-size:10px; margin-bottom:8px; }}

    .right-head {{ background:{PANEL_3}; border:1px solid {BORDER}; border-radius:12px; padding:12px 14px;
        color:{TEXT}; font-size:14px; font-weight:800; margin-bottom:10px; }}
    .right-box {{ background:{PANEL}; border:1px solid {BORDER}; border-radius:12px; padding:13px; margin-bottom:10px; }}

    .exec-box {{ background:#0B1C29; border:1px solid #25485D; border-left:4px solid {GOLD};
        border-radius:12px; padding:13px 15px; color:{TEXT}; font-size:11px; line-height:1.6; margin-top:8px; }}

    [data-testid="stMetric"] {{ background:{PANEL}; border:1px solid {BORDER}; padding:13px; border-radius:12px; }}
    [data-testid="stMetricLabel"] {{ color:{MUTED}; }}
    [data-testid="stMetricValue"] {{ color:{TEXT}; }}

    [data-baseweb="select"] > div, [data-testid="stNumberInput"] input, [data-testid="stTextInput"] input {{
        background:{PANEL_2} !important; color:{TEXT} !important; border-color:{BORDER} !important;
    }}
    [data-testid="stSlider"] {{ color:{ACCENT}; }}
    .stButton > button, .stDownloadButton > button {{
        background:{ACCENT}; color:{BG}; border:0; border-radius:9px; font-weight:800;
    }}
    .stButton > button:hover, .stDownloadButton > button:hover {{ background:#35D5D9; color:{BG}; }}

    [data-testid="stDataFrame"] {{ background:{PANEL}; border:1px solid {BORDER}; border-radius:12px; }}
    hr {{ border-color:{BORDER} !important; }}

    /* Make chart containers visually integrated */
    [data-testid="stVegaLiteChart"], [data-testid="stArrowVegaLiteChart"] {{
        background:{PANEL}; border:1px solid {BORDER}; border-radius:12px; padding:6px;
    }}
    </style>
    """
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
    return os.getenv("API_BASE_URL", "http://127.0.0.1:8000").rstrip("/")


API_BASE_URL = get_api_base_url()
REQUEST_TIMEOUT = 90


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
def load_summary():
    return api_get("/portfolio/summary")


@st.cache_data(ttl=60)
def load_portfolio(risk_level: str | None = None, limit: int = 1000):
    params = {"limit": limit}
    if risk_level and risk_level != "TODOS":
        params["risk_level"] = risk_level
    return api_get("/portfolio", params=params)


def load_customer(customer_id: int):
    return api_get(f"/portfolio/{customer_id}")


# ============================================================
# HELPERS
# ============================================================
def extract_records(payload: Any) -> list[dict]:
    if isinstance(payload, list):
        return [x for x in payload if isinstance(x, dict)]
    if isinstance(payload, dict):
        for key in ["items", "data", "results", "portfolio", "records", "clientes"]:
            value = payload.get(key)
            if isinstance(value, list):
                return [x for x in value if isinstance(x, dict)]
    return []


def normalize_df(payload: Any) -> pd.DataFrame:
    df = pd.DataFrame(extract_records(payload))
    if df.empty:
        return df
    numeric = [
        "id", "probability_default", "prediction", "limit_bal", "age", "pay_0",
        "pay_max_delay", "recent_delay_months", "consecutive_delay_months",
        "bill_avg", "pay_amt_avg", "payment_bill_ratio_total",
    ]
    for c in numeric:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    return df


def fmt_int(v):
    try:
        return f"{int(v):,}".replace(",", ".")
    except Exception:
        return "N/D"


def fmt_pct(v):
    try:
        return f"{float(v) * 100:.2f}%"
    except Exception:
        return "N/D"


def fmt_money(v):
    try:
        return f"{float(v):,.0f}".replace(",", ".")
    except Exception:
        return "N/D"


def risk_color(level: str) -> str:
    return {"BAJO": GREEN, "MEDIO": AMBER, "ALTO": ORANGE, "CRITICO": RED}.get(str(level).upper(), MUTED)


# ============================================================
# LOAD
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
html(
    f"""
    <div class="nr-topbar">
      <div class="nr-brand">
        <div class="nr-mark">NR</div>
        <div>
          <div class="nr-name">NexaRisk</div>
          <div class="nr-sub">Credit Risk Command Center · Supervisión de cartera y priorización preventiva</div>
        </div>
      </div>
      <div class="nr-meta">
        <div class="nr-live">API ONLINE</div>
        <div>Modelo {summary.get('model_version','N/D')}</div>
        <div>FastAPI · Supabase · Streamlit</div>
      </div>
    </div>
    """
)

# ============================================================
# KPI STRIP
# ============================================================
total = int(summary.get("total", 0))
bajo = int(summary.get("bajo", 0))
medio = int(summary.get("medio", 0))
alto = int(summary.get("alto", 0))
critico = int(summary.get("critico", 0))
priority = alto + critico
priority_pct = priority / total if total else 0

k1, k2, k3, k4, k5 = st.columns(5)
for col, label, value, note, cls in [
    (k1, "Cartera evaluada", fmt_int(total), "Scoring vigente", "kpi-accent"),
    (k2, "PD promedio", fmt_pct(summary.get("pd_promedio")), "Probabilidad media", ""),
    (k3, "Gestión prioritaria", fmt_int(priority), f"{fmt_pct(priority_pct)} en Alto + Crítico", "kpi-red"),
    (k4, "Predicción = 1", fmt_int(summary.get("prediction_1")), "Potencial incumplimiento", "kpi-gold"),
    (k5, "Predicción = 0", fmt_int(summary.get("prediction_0")), "Sin señal de incumplimiento", ""),
]:
    with col:
        html(f"""
        <div class="kpi {cls}">
          <div class="kpi-label">{label}</div>
          <div class="kpi-value">{value}</div>
          <div class="kpi-note">{note}</div>
        </div>
        """)

st.write("")

# ============================================================
# RIGHT RAIL FILTERS + MAIN DASHBOARD
# ============================================================
main_col, right_col = st.columns([5.6, 1.35], gap="large")

with right_col:
    html('<div class="right-head">FILTROS DE CARTERA</div>')
    risk_filter = st.selectbox("Nivel de riesgo", ["TODOS", "CRITICO", "ALTO", "MEDIO", "BAJO"])
    prediction_filter = st.selectbox("Clasificación", ["TODAS", "1", "0"])
    min_pd = st.slider("PD mínima", 0, 100, 0, 5)
    row_limit = st.selectbox("Clientes a mostrar", [100, 250, 500, 1000], index=1)

    st.divider()
    html('<div class="right-head">CLIENTE 360</div>')
    customer_id = st.number_input("ID cliente", min_value=1, value=1, step=1)
    search_customer = st.button("Consultar", type="primary", use_container_width=True)

    st.divider()
    html('<div class="right-head">IDENTIDAD</div>')
    html(f"""
    <div class="right-box">
      <div style="color:{TEXT};font-weight:800;font-size:13px;">NexaRisk</div>
      <div style="color:{MUTED};font-size:10px;margin-top:5px;">Supervisión de riesgo crediticio</div>
      <div style="color:{MUTED};font-size:9px;margin-top:8px;">Paleta institucional: Midnight · Slate · Cyan · Gold</div>
    </div>
    """)

with main_col:
    # Full-portfolio distributions
    c1, c2 = st.columns([1.25, 1], gap="medium")
    with c1:
        html('<div class="section-head">Distribución de riesgo</div><div class="section-sub">Composición de la cartera completa por banda</div>')
        risk_df = pd.DataFrame({
            "Nivel": ["BAJO", "MEDIO", "ALTO", "CRITICO"],
            "Clientes": [bajo, medio, alto, critico],
        })
        st.bar_chart(risk_df.set_index("Nivel"), height=300)

    with c2:
        html('<div class="section-head">Clasificación del modelo</div><div class="section-sub">Salida binaria de la cartera completa</div>')
        pred_df = pd.DataFrame({
            "Clase": ["Predicción 0", "Predicción 1"],
            "Clientes": [int(summary.get("prediction_0",0)), int(summary.get("prediction_1",0))],
        })
        st.bar_chart(pred_df.set_index("Clase"), height=300)

    # Load filtered sample for analytical panels
    payload = load_portfolio(risk_level=risk_filter, limit=row_limit)
    df = normalize_df(payload)
    if not df.empty:
        if prediction_filter != "TODAS" and "prediction" in df.columns:
            df = df[df["prediction"] == int(prediction_filter)]
        if "probability_default" in df.columns:
            df = df[df["probability_default"] >= min_pd / 100]
            df = df.sort_values("probability_default", ascending=False)

    # Executive message
    html(f"""
    <div class="exec-box"><b>Lectura ejecutiva.</b> {fmt_int(priority)} clientes se concentran en niveles ALTO o CRÍTICO,
    equivalentes al <b>{fmt_pct(priority_pct)}</b> de la cartera. Esta población constituye la principal cola de gestión preventiva.</div>
    """)

    st.write("")

    # Analytical row 2
    a1, a2, a3 = st.columns(3, gap="medium")
    if not df.empty:
        with a1:
            html('<div class="section-head">Exposición por riesgo</div><div class="section-sub">Suma de límite de crédito en la muestra consultada</div>')
            if {"risk_level", "limit_bal"}.issubset(df.columns):
                tmp = df.groupby("risk_level", as_index=False)["limit_bal"].sum().set_index("risk_level")
                st.bar_chart(tmp, height=250)
            else:
                st.info("Sin variables suficientes")

        with a2:
            html('<div class="section-head">PD por rango de edad</div><div class="section-sub">Promedio de PD en la muestra consultada</div>')
            if {"age", "probability_default"}.issubset(df.columns):
                age_bins = pd.cut(df["age"], bins=[17,29,39,49,59,69,100], labels=["18-29","30-39","40-49","50-59","60-69","70+"])
                tmp = df.assign(age_band=age_bins).groupby("age_band", observed=False)["probability_default"].mean().mul(100).to_frame("PD %")
                st.bar_chart(tmp, height=250)
            else:
                st.info("Sin variables suficientes")

        with a3:
            html('<div class="section-head">Máximo atraso vs PD</div><div class="section-sub">PD promedio según severidad máxima de atraso</div>')
            if {"pay_max_delay", "probability_default"}.issubset(df.columns):
                tmp = df.groupby("pay_max_delay")["probability_default"].mean().mul(100).sort_index().to_frame("PD %")
                st.line_chart(tmp, height=250)
            else:
                st.info("Sin variables suficientes")

        # Analytical row 3
        b1, b2, b3 = st.columns(3, gap="medium")
        with b1:
            html('<div class="section-head">Atrasos recientes</div><div class="section-sub">Clientes por número de meses con atraso reciente</div>')
            if "recent_delay_months" in df.columns:
                tmp = df["recent_delay_months"].value_counts().sort_index().to_frame("Clientes")
                st.bar_chart(tmp, height=240)
            else:
                st.info("Sin variable disponible")

        with b2:
            html('<div class="section-head">Pago / facturación</div><div class="section-sub">Distribución del ratio total en la muestra consultada</div>')
            if "payment_bill_ratio_total" in df.columns:
                ratio = df["payment_bill_ratio_total"].clip(upper=2)
                buckets = pd.cut(ratio, bins=[-0.001,0.25,0.5,0.75,1,2], labels=["0-.25",".25-.50",".50-.75",".75-1","1+"])
                tmp = buckets.value_counts().sort_index().to_frame("Clientes")
                st.bar_chart(tmp, height=240)
            else:
                st.info("Sin variable disponible")

        with b3:
            html('<div class="section-head">Top exposición prioritaria</div><div class="section-sub">Mayores líneas dentro del filtro actual</div>')
            if {"id","limit_bal","probability_default"}.issubset(df.columns):
                top = df.sort_values(["probability_default","limit_bal"], ascending=[False,False]).head(10)[["id","limit_bal"]].copy()
                top["id"] = top["id"].astype(int).astype(str)
                st.bar_chart(top.set_index("id"), height=240)
            else:
                st.info("Sin variables suficientes")

    st.write("")
    html('<div class="section-head">Cartera priorizada</div><div class="section-sub">Clientes ordenados por mayor probabilidad de incumplimiento</div>')

    if df.empty:
        st.warning("No existen registros para los filtros seleccionados.")
    else:
        if "probability_default" in df.columns:
            df["pd_percent"] = df["probability_default"] * 100
        cols = [
            "id","pd_percent","prediction","risk_level","limit_bal","age",
            "pay_max_delay","recent_delay_months","consecutive_delay_months",
            "payment_bill_ratio_total","recommendation"
        ]
        cols = [c for c in cols if c in df.columns]
        out = df[cols].copy().rename(columns={
            "id":"Cliente","pd_percent":"PD %","prediction":"Pred.","risk_level":"Riesgo",
            "limit_bal":"Límite","age":"Edad","pay_max_delay":"Máx. atraso",
            "recent_delay_months":"Atrasos recientes","consecutive_delay_months":"Atrasos consecutivos",
            "payment_bill_ratio_total":"Ratio pago/fact.","recommendation":"Acción sugerida"
        })
        st.caption(f"{len(out):,} clientes mostrados")
        st.dataframe(
            out, use_container_width=True, hide_index=True, height=470,
            column_config={
                "Cliente": st.column_config.NumberColumn("Cliente", format="%d"),
                "PD %": st.column_config.ProgressColumn("PD %", min_value=0, max_value=100, format="%.1f%%"),
                "Pred.": st.column_config.NumberColumn("Pred.", format="%d"),
                "Límite": st.column_config.NumberColumn("Límite", format="%.0f"),
            }
        )
        csv = out.to_csv(index=False).encode("utf-8-sig")
        st.download_button("Descargar cartera filtrada", csv, "cartera_nexarisk.csv", "text/csv")

# ============================================================
# CUSTOMER 360
# ============================================================
if search_customer:
    st.divider()
    try:
        customer = load_customer(int(customer_id))
        html(f'<div class="section-head">Cliente 360 · #{int(customer_id)}</div><div class="section-sub">Ficha operativa individual</div>')
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("PD", fmt_pct(customer.get("probability_default")))
        c2.metric("Riesgo", customer.get("risk_level", "N/D"))
        c3.metric("Clasificación", customer.get("prediction", "N/D"))
        c4.metric("Límite", fmt_money(customer.get("limit_bal")))
        st.markdown("#### Recomendación de gestión")
        st.info(customer.get("recommendation", "No disponible"))
        s1, s2, s3, s4 = st.columns(4)
        s1.metric("Edad", customer.get("age", "N/D"))
        s2.metric("Máximo atraso", customer.get("pay_max_delay", "N/D"))
        s3.metric("Atrasos recientes", customer.get("recent_delay_months", "N/D"))
        s4.metric("Atrasos consecutivos", customer.get("consecutive_delay_months", "N/D"))
    except Exception as exc:
        st.error("No fue posible consultar ese cliente.")
        with st.expander("Detalle técnico"):
            st.exception(exc)

# ============================================================
# FOOTER
# ============================================================
st.divider()
f1, f2, f3 = st.columns([2,1,1])
with f1:
    st.caption("NexaRisk · Proyecto Productivo IIIA")
with f2:
    st.caption(f"Modelo {summary.get('model_version','N/D')}")
with f3:
    st.caption("FastAPI · Supabase · Streamlit")
