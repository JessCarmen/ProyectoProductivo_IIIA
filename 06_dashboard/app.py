import html
import json
import os
import time
from pathlib import Path
from typing import Any

import pandas as pd
import requests
import streamlit as st

# ============================================================
# CONFIGURACION
# ============================================================

st.set_page_config(
    page_title="NexaRisk | Supervisión de Cartera",
    page_icon="◆",
    layout="wide",
    initial_sidebar_state="collapsed",
)

ROOT = Path(__file__).resolve().parents[1]
METRICS_PATH = ROOT / "04_ml" / "models" / "evaluation_metrics.json"

BRAND = {
    "navy": "#0B1F33",
    "teal": "#0E7490",
    "mint": "#14B8A6",
    "gold": "#F4B942",
    "cloud": "#F5F8FB",
    "ink": "#172033",
    "muted": "#667085",
    "line": "#E3E9EF",
    "white": "#FFFFFF",
    "low": "#2E8B57",
    "medium": "#D4A017",
    "high": "#E67E22",
    "critical": "#C62828",
}

REQUEST_TIMEOUT = 90


def get_api_base_url() -> str:
    try:
        if "API_BASE_URL" in st.secrets:
            return str(st.secrets["API_BASE_URL"]).rstrip("/")
    except Exception:
        pass
    return os.getenv("API_BASE_URL", "http://127.0.0.1:8000").rstrip("/")


API_BASE_URL = get_api_base_url()

# ============================================================
# ESTILO INSTITUCIONAL FICTICIO
# ============================================================

st.markdown(
    f"""
    <style>
      :root {{
        --nr-navy: {BRAND['navy']};
        --nr-teal: {BRAND['teal']};
        --nr-mint: {BRAND['mint']};
        --nr-gold: {BRAND['gold']};
        --nr-cloud: {BRAND['cloud']};
        --nr-ink: {BRAND['ink']};
        --nr-muted: {BRAND['muted']};
        --nr-line: {BRAND['line']};
      }}

      .stApp {{
        background: linear-gradient(180deg, #F8FAFC 0%, #F4F7FA 100%);
        color: var(--nr-ink);
      }}

      .block-container {{
        max-width: 1500px;
        padding-top: 1.4rem;
        padding-bottom: 3rem;
      }}

      #MainMenu {{visibility: hidden;}}
      footer {{visibility: hidden;}}

      .nr-header {{
        display:flex;
        align-items:center;
        justify-content:space-between;
        gap:24px;
        padding:22px 26px;
        border-radius:22px;
        background: linear-gradient(115deg, {BRAND['navy']} 0%, #123A50 58%, {BRAND['teal']} 100%);
        box-shadow: 0 16px 36px rgba(11,31,51,.14);
        margin-bottom: 18px;
      }}
      .nr-brand {{display:flex; align-items:center; gap:16px;}}
      .nr-logo {{
        width:58px; height:58px; border-radius:16px;
        background: linear-gradient(145deg, {BRAND['mint']}, {BRAND['gold']});
        display:flex; align-items:center; justify-content:center;
        color:{BRAND['navy']}; font-weight:900; font-size:22px;
        letter-spacing:-1px;
        box-shadow: inset 0 0 0 1px rgba(255,255,255,.35), 0 8px 20px rgba(0,0,0,.15);
      }}
      .nr-title {{color:white; font-size:28px; font-weight:850; line-height:1.05; margin:0;}}
      .nr-subtitle {{color:#DDEAF0; font-size:13px; margin-top:6px; letter-spacing:.2px;}}
      .nr-status {{
        display:inline-flex; align-items:center; gap:8px;
        background:rgba(255,255,255,.12); color:white;
        border:1px solid rgba(255,255,255,.22);
        padding:9px 13px; border-radius:999px; font-size:12px; font-weight:700;
        white-space:nowrap;
      }}
      .nr-dot {{width:8px; height:8px; border-radius:50%; background:#55E6A5; box-shadow:0 0 0 4px rgba(85,230,165,.14);}}

      .nr-section-title {{
        font-size:20px; font-weight:800; color:{BRAND['navy']};
        margin:4px 0 3px 0;
      }}
      .nr-section-note {{font-size:13px; color:{BRAND['muted']}; margin-bottom:14px;}}

      .nr-kpi {{
        background:white;
        border:1px solid {BRAND['line']};
        border-radius:18px;
        padding:18px 18px 16px 18px;
        min-height:124px;
        box-shadow: 0 8px 22px rgba(11,31,51,.055);
      }}
      .nr-kpi-label {{font-size:12px; text-transform:uppercase; letter-spacing:.65px; color:{BRAND['muted']}; font-weight:800;}}
      .nr-kpi-value {{font-size:30px; color:{BRAND['navy']}; font-weight:900; line-height:1.05; margin-top:10px;}}
      .nr-kpi-foot {{font-size:12px; color:{BRAND['muted']}; margin-top:8px;}}
      .nr-kpi-accent {{border-top:4px solid {BRAND['teal']};}}
      .nr-kpi-critical {{border-top:4px solid {BRAND['critical']};}}
      .nr-kpi-gold {{border-top:4px solid {BRAND['gold']};}}
      .nr-kpi-mint {{border-top:4px solid {BRAND['mint']};}}

      .nr-callout {{
        border-radius:16px;
        padding:16px 18px;
        background:#FFFFFF;
        border:1px solid {BRAND['line']};
        border-left:5px solid {BRAND['gold']};
        margin:8px 0 16px 0;
        color:{BRAND['ink']};
      }}
      .nr-callout strong {{color:{BRAND['navy']};}}

      .nr-risk-badge {{display:inline-block; padding:7px 11px; border-radius:999px; color:white; font-weight:800; font-size:12px;}}
      .nr-low {{background:{BRAND['low']};}}
      .nr-medium {{background:{BRAND['medium']};}}
      .nr-high {{background:{BRAND['high']};}}
      .nr-critical {{background:{BRAND['critical']};}}

      .nr-client-card {{
        background:white; border:1px solid {BRAND['line']}; border-radius:20px;
        padding:22px; box-shadow:0 10px 28px rgba(11,31,51,.06);
      }}
      .nr-reco {{
        background:#F0F9F8; border:1px solid #CBEDE8;
        border-left:5px solid {BRAND['mint']};
        border-radius:14px; padding:16px 18px; color:#173B42;
      }}
      .nr-small {{font-size:12px; color:{BRAND['muted']};}}

      div[data-testid="stMetric"] {{
        background:#FFFFFF;
        border:1px solid {BRAND['line']};
        padding:14px 16px;
        border-radius:16px;
        box-shadow:0 7px 18px rgba(11,31,51,.045);
      }}

      .stTabs [data-baseweb="tab-list"] {{gap:8px;}}
      .stTabs [data-baseweb="tab"] {{
        height:44px; padding:0 16px; border-radius:12px 12px 0 0;
        font-weight:750;
      }}
      .stTabs [aria-selected="true"] {{color:{BRAND['teal']} !important;}}

      div.stButton > button {{
        border-radius:12px;
        font-weight:800;
        border:1px solid {BRAND['teal']};
      }}
      div.stButton > button[kind="primary"] {{
        background:{BRAND['teal']};
        border-color:{BRAND['teal']};
      }}

      [data-testid="stDataFrame"] {{
        border-radius:16px; overflow:hidden; border:1px solid {BRAND['line']};
      }}
    </style>
    """,
    unsafe_allow_html=True,
)

# ============================================================
# API / DATOS
# ============================================================


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
    raise RuntimeError(f"No fue posible comunicarse con FastAPI. URL: {url}. Error: {last_error}")


@st.cache_data(ttl=60, show_spinner=False)
def load_summary():
    return api_get("/portfolio/summary")


@st.cache_data(ttl=60, show_spinner=False)
def load_portfolio(risk_level: str | None = None, prediction: int | None = None, limit: int = 100):
    params: dict[str, Any] = {"limit": limit}
    if risk_level and risk_level != "TODOS":
        params["risk_level"] = risk_level
    if prediction is not None:
        params["prediction"] = prediction
    return api_get("/portfolio", params=params)


def load_customer(customer_id: int):
    return api_get(f"/portfolio/{customer_id}")


@st.cache_data(ttl=300, show_spinner=False)
def load_model_metrics() -> dict:
    try:
        return json.loads(METRICS_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}


def extract_records(payload: Any) -> list[dict]:
    if payload is None:
        return []
    if isinstance(payload, list):
        return [row for row in payload if isinstance(row, dict)]
    if isinstance(payload, dict):
        for key in ("results", "items", "data", "portfolio", "records", "clientes"):
            value = payload.get(key)
            if isinstance(value, list):
                return [row for row in value if isinstance(row, dict)]
        if "id" in payload:
            return [payload]
    return []


def normalize_df(payload: Any) -> pd.DataFrame:
    records = extract_records(payload)
    if not records:
        return pd.DataFrame()
    df = pd.DataFrame(records)
    aliases = {
        "customer_id": "id",
        "cliente_id": "id",
        "pd": "probability_default",
        "probabilidad": "probability_default",
        "probabilidad_default": "probability_default",
        "prediccion": "prediction",
        "clasificacion": "prediction",
        "nivel_riesgo": "risk_level",
        "riesgo": "risk_level",
        "recomendacion": "recommendation",
        "model_version": "modelo_version",
        "score_date": "fecha_score",
    }
    rename_map = {src: dst for src, dst in aliases.items() if src in df.columns and dst not in df.columns}
    if rename_map:
        df = df.rename(columns=rename_map)
    numeric_columns = [
        "id", "probability_default", "prediction", "limit_bal", "age",
        "pay_0", "pay_max_delay", "recent_delay_months",
        "consecutive_delay_months", "bill_avg", "pay_amt_avg",
        "payment_bill_ratio_total",
    ]
    for column in numeric_columns:
        if column in df.columns:
            df[column] = pd.to_numeric(df[column], errors="coerce")
    return df.dropna(axis=1, how="all")


# ============================================================
# FORMATO
# ============================================================


def fmt_pct(value: Any) -> str:
    try:
        return f"{float(value):.2%}"
    except (TypeError, ValueError):
        return "N/D"


def fmt_int(value: Any) -> str:
    try:
        return f"{int(float(value)):,}"
    except (TypeError, ValueError):
        return "N/D"


def fmt_money(value: Any) -> str:
    try:
        return f"{float(value):,.0f}"
    except (TypeError, ValueError):
        return "N/D"


def risk_badge(level: Any) -> str:
    level_text = str(level or "N/D").upper()
    css = {
        "BAJO": "nr-low",
        "MEDIO": "nr-medium",
        "ALTO": "nr-high",
        "CRITICO": "nr-critical",
    }.get(level_text, "nr-medium")
    return f'<span class="nr-risk-badge {css}">{html.escape(level_text)}</span>'


def kpi_card(label: str, value: str, foot: str, css_class: str = "nr-kpi-accent") -> None:
    st.markdown(
        f"""
        <div class="nr-kpi {css_class}">
            <div class="nr-kpi-label">{html.escape(label)}</div>
            <div class="nr-kpi-value">{html.escape(value)}</div>
            <div class="nr-kpi-foot">{html.escape(foot)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# HEADER / ESTADO
# ============================================================

try:
    summary = load_summary()
    api_online = True
except Exception as exc:
    api_online = False
    summary = {}
    st.error("No fue posible conectar con FastAPI. Render Free puede tardar en despertar.")
    with st.expander("Detalle técnico"):
        st.exception(exc)
    st.stop()

model_metrics = load_model_metrics()
model_version = summary.get("model_version", model_metrics.get("model_version", "N/D"))

st.markdown(
    f"""
    <div class="nr-header">
      <div class="nr-brand">
        <div class="nr-logo">NR</div>
        <div>
          <div class="nr-title">NexaRisk</div>
          <div class="nr-subtitle">Centro de Supervisión de Riesgo Crediticio · Proyecto Productivo IIIA</div>
        </div>
      </div>
      <div class="nr-status"><span class="nr-dot"></span> API ONLINE · {html.escape(str(model_version))}</div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.caption("Identidad visual ficticia creada para fines académicos. El dashboard consume scoring persistido en la capa Gold mediante FastAPI.")

# ============================================================
# KPIs SUPERVISOR
# ============================================================

total = int(summary.get("total", 0) or 0)
pd_avg = float(summary.get("pd_promedio", 0) or 0)
pred_1 = int(summary.get("prediction_1", 0) or 0)
critical = int(summary.get("critico", 0) or 0)
high = int(summary.get("alto", 0) or 0)
priority = critical + high
priority_pct = (priority / total) if total else 0
pred_1_pct = (pred_1 / total) if total else 0

k1, k2, k3, k4 = st.columns(4)
with k1:
    kpi_card("Cartera evaluada", fmt_int(total), "Clientes con scoring disponible", "nr-kpi-accent")
with k2:
    kpi_card("PD promedio", fmt_pct(pd_avg), "Probabilidad media de incumplimiento", "nr-kpi-mint")
with k3:
    kpi_card("Gestión prioritaria", fmt_int(priority), f"Alto + Crítico · {fmt_pct(priority_pct)} de la cartera", "nr-kpi-gold")
with k4:
    kpi_card("Predicción = 1", fmt_int(pred_1), f"{fmt_pct(pred_1_pct)} de la cartera", "nr-kpi-critical")

st.markdown(
    f"""
    <div class="nr-callout">
      <strong>Lectura supervisora:</strong> {fmt_int(critical)} clientes están en nivel <strong>CRÍTICO</strong> y {fmt_int(high)} en <strong>ALTO</strong>.
      La prioridad operativa sugerida es revisar primero la cola CRÍTICA ordenada por PD y luego los casos ALTOS con señales de atraso recurrente.
    </div>
    """,
    unsafe_allow_html=True,
)

# ============================================================
# NAVEGACION
# ============================================================

tab_resumen, tab_prioridad, tab_cliente, tab_cartera, tab_modelo = st.tabs(
    ["Resumen ejecutivo", "Prioridad de gestión", "Cliente 360", "Cartera operativa", "Modelo"]
)

# ============================================================
# TAB 1 - RESUMEN
# ============================================================

with tab_resumen:
    st.markdown('<div class="nr-section-title">Composición de riesgo</div>', unsafe_allow_html=True)
    st.markdown('<div class="nr-section-note">Distribución de la cartera puntuada por banda operativa.</div>', unsafe_allow_html=True)

    risk_df = pd.DataFrame({
        "Nivel": ["BAJO", "MEDIO", "ALTO", "CRITICO"],
        "Clientes": [
            int(summary.get("bajo", 0)),
            int(summary.get("medio", 0)),
            high,
            critical,
        ],
    })
    risk_df["Porcentaje"] = risk_df["Clientes"] / max(total, 1) * 100

    left, right = st.columns([1.55, 1])
    with left:
        st.bar_chart(risk_df.set_index("Nivel")[["Clientes"]], height=330)
    with right:
        st.dataframe(
            risk_df,
            hide_index=True,
            use_container_width=True,
            height=330,
            column_config={
                "Clientes": st.column_config.NumberColumn("Clientes", format="%d"),
                "Porcentaje": st.column_config.NumberColumn("% cartera", format="%.2f%%"),
            },
        )

    a, b, c = st.columns(3)
    a.metric("BAJO", fmt_int(summary.get("bajo")), fmt_pct(int(summary.get("bajo", 0))/max(total,1)))
    b.metric("MEDIO", fmt_int(summary.get("medio")), fmt_pct(int(summary.get("medio", 0))/max(total,1)))
    c.metric("ALTO + CRÍTICO", fmt_int(priority), fmt_pct(priority_pct))

# ============================================================
# TAB 2 - PRIORIDAD
# ============================================================

with tab_prioridad:
    st.markdown('<div class="nr-section-title">Cola prioritaria del supervisor</div>', unsafe_allow_html=True)
    st.markdown('<div class="nr-section-note">Los endpoints de cartera llegan ordenados por PD de mayor a menor. Esta vista facilita la priorización diaria.</div>', unsafe_allow_html=True)

    priority_level = st.radio("Nivel a supervisar", ["CRITICO", "ALTO"], horizontal=True)
    top_n = st.selectbox("Cantidad de casos", [20, 50, 100, 250], index=1)

    with st.spinner("Consultando cartera prioritaria..."):
        priority_df = normalize_df(load_portfolio(risk_level=priority_level, limit=top_n))

    if priority_df.empty:
        st.warning("No se encontraron casos para el nivel seleccionado.")
    else:
        if "probability_default" in priority_df.columns:
            priority_df["PD %"] = priority_df["probability_default"] * 100

        show_cols = [
            c for c in [
                "id", "PD %", "risk_level", "limit_bal", "age", "pay_max_delay",
                "recent_delay_months", "consecutive_delay_months",
                "payment_bill_ratio_total", "recommendation"
            ] if c in priority_df.columns
        ]
        priority_view = priority_df[show_cols].rename(columns={
            "id": "Cliente",
            "risk_level": "Riesgo",
            "limit_bal": "Límite",
            "age": "Edad",
            "pay_max_delay": "Máx. atraso",
            "recent_delay_months": "Atrasos recientes",
            "consecutive_delay_months": "Atrasos consecutivos",
            "payment_bill_ratio_total": "Ratio pago/facturación",
            "recommendation": "Acción sugerida",
        })

        st.dataframe(
            priority_view,
            use_container_width=True,
            hide_index=True,
            column_config={
                "PD %": st.column_config.ProgressColumn("PD", min_value=0, max_value=100, format="%.1f%%"),
                "Límite": st.column_config.NumberColumn("Límite", format="%,.0f"),
            },
        )
        st.download_button(
            "Descargar cola prioritaria CSV",
            data=priority_view.to_csv(index=False).encode("utf-8-sig"),
            file_name=f"cartera_prioritaria_{priority_level.lower()}.csv",
            mime="text/csv",
            use_container_width=False,
        )

# ============================================================
# TAB 3 - CLIENTE 360
# ============================================================

with tab_cliente:
    st.markdown('<div class="nr-section-title">Cliente 360</div>', unsafe_allow_html=True)
    st.markdown('<div class="nr-section-note">Consulta individual orientada a decisión: riesgo, señales conductuales y recomendación.</div>', unsafe_allow_html=True)

    sc1, sc2 = st.columns([4, 1], vertical_alignment="bottom")
    with sc1:
        customer_id = st.number_input("ID del cliente", min_value=1, value=1, step=1)
    with sc2:
        consult = st.button("Consultar cliente", type="primary", use_container_width=True)

    if consult:
        try:
            customer = load_customer(int(customer_id))
            pd_value = float(customer.get("probability_default", 0) or 0)
            risk = str(customer.get("risk_level", "N/D"))
            reco = str(customer.get("recommendation", "Sin recomendación disponible."))

            st.markdown(
                f"""
                <div class="nr-client-card">
                  <div style="display:flex; justify-content:space-between; align-items:center; gap:18px;">
                    <div>
                      <div class="nr-small">CLIENTE</div>
                      <div style="font-size:28px;font-weight:900;color:{BRAND['navy']};">#{int(customer_id):,}</div>
                    </div>
                    <div>{risk_badge(risk)}</div>
                  </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            q1, q2, q3, q4 = st.columns(4)
            q1.metric("Probabilidad de incumplimiento", fmt_pct(pd_value))
            q2.metric("Clasificación", fmt_int(customer.get("prediction")))
            q3.metric("Límite de crédito", fmt_money(customer.get("limit_bal")))
            q4.metric("Edad", fmt_int(customer.get("age")))

            st.markdown('<div class="nr-section-title">Señales conductuales</div>', unsafe_allow_html=True)
            s1, s2, s3, s4 = st.columns(4)
            s1.metric("Máximo atraso", fmt_int(customer.get("pay_max_delay")))
            s2.metric("Atrasos recientes", fmt_int(customer.get("recent_delay_months")))
            s3.metric("Atrasos consecutivos", fmt_int(customer.get("consecutive_delay_months")))
            s4.metric("Ratio pago/facturación", f"{float(customer.get('payment_bill_ratio_total', 0) or 0):.2f}")

            st.markdown('<div class="nr-section-title">Recomendación de gestión</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="nr-reco">{html.escape(reco)}</div>', unsafe_allow_html=True)

            with st.expander("Ver registro técnico completo"):
                st.json(customer)

        except Exception as exc:
            st.error(f"No fue posible consultar el cliente {int(customer_id)}.")
            with st.expander("Detalle técnico"):
                st.exception(exc)

# ============================================================
# TAB 4 - CARTERA OPERATIVA
# ============================================================

with tab_cartera:
    st.markdown('<div class="nr-section-title">Cartera operativa</div>', unsafe_allow_html=True)
    st.markdown('<div class="nr-section-note">Exploración filtrada para gestión, seguimiento y exportación.</div>', unsafe_allow_html=True)

    f1, f2, f3 = st.columns(3)
    with f1:
        risk_filter = st.selectbox("Nivel de riesgo", ["TODOS", "CRITICO", "ALTO", "MEDIO", "BAJO"])
    with f2:
        pred_label = st.selectbox("Clasificación", ["TODAS", "1 - Riesgo de incumplimiento", "0 - No incumplimiento"])
    with f3:
        row_limit = st.selectbox("Registros", [50, 100, 250, 500, 1000], index=2)

    prediction_filter = None
    if pred_label.startswith("1"):
        prediction_filter = 1
    elif pred_label.startswith("0"):
        prediction_filter = 0

    portfolio_df = normalize_df(load_portfolio(
        risk_level=risk_filter,
        prediction=prediction_filter,
        limit=row_limit,
    ))

    if portfolio_df.empty:
        st.warning("No se encontraron registros con los filtros seleccionados.")
    else:
        if "probability_default" in portfolio_df.columns:
            portfolio_df["PD %"] = portfolio_df["probability_default"] * 100

        columns = [
            c for c in [
                "id", "PD %", "prediction", "risk_level", "limit_bal", "age",
                "pay_max_delay", "recent_delay_months", "consecutive_delay_months",
                "recommendation", "modelo_version", "fecha_score"
            ] if c in portfolio_df.columns
        ]
        view = portfolio_df[columns].rename(columns={
            "id": "Cliente",
            "prediction": "Predicción",
            "risk_level": "Riesgo",
            "limit_bal": "Límite",
            "age": "Edad",
            "pay_max_delay": "Máx. atraso",
            "recent_delay_months": "Atrasos recientes",
            "consecutive_delay_months": "Atrasos consecutivos",
            "recommendation": "Acción sugerida",
            "modelo_version": "Modelo",
            "fecha_score": "Fecha scoring",
        })

        st.dataframe(
            view,
            use_container_width=True,
            hide_index=True,
            column_config={
                "PD %": st.column_config.ProgressColumn("PD", min_value=0, max_value=100, format="%.1f%%"),
                "Límite": st.column_config.NumberColumn("Límite", format="%,.0f"),
            },
        )
        st.download_button(
            "Exportar vista CSV",
            data=view.to_csv(index=False).encode("utf-8-sig"),
            file_name="cartera_operativa.csv",
            mime="text/csv",
        )

# ============================================================
# TAB 5 - MODELO
# ============================================================

with tab_modelo:
    st.markdown('<div class="nr-section-title">Ficha de control del modelo</div>', unsafe_allow_html=True)
    st.markdown('<div class="nr-section-note">Indicadores del test reservado. Esta sección es técnica; no modifica el scoring de cartera.</div>', unsafe_allow_html=True)

    if not model_metrics:
        st.info("No fue posible leer evaluation_metrics.json en este despliegue.")
    else:
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("ROC-AUC", f"{float(model_metrics.get('roc_auc', 0)):.4f}")
        m2.metric("PR-AUC", f"{float(model_metrics.get('pr_auc', 0)):.4f}")
        m3.metric("F1 default", f"{float(model_metrics.get('f1_default', 0)):.4f}")
        m4.metric("Recall default", f"{float(model_metrics.get('recall_default', 0)):.4f}")

        n1, n2, n3, n4 = st.columns(4)
        n1.metric("Accuracy", f"{float(model_metrics.get('accuracy', 0)):.4f}")
        n2.metric("Precision default", f"{float(model_metrics.get('precision_default', 0)):.4f}")
        n3.metric("Brier score", f"{float(model_metrics.get('brier_score', 0)):.4f}")
        n4.metric("Threshold", fmt_pct(model_metrics.get("risk_threshold", 0.38)))

        st.info(
            f"Evaluación final realizada sobre {fmt_int(model_metrics.get('test_records'))} registros del conjunto test reservado. "
            "La cartera operativa utiliza el scoring masivo persistido en Gold."
        )

# ============================================================
# FOOTER
# ============================================================

st.markdown("---")
st.caption(
    f"NexaRisk · Identidad ficticia académica · FastAPI público conectado · Modelo {model_version} · "
    "Las recomendaciones son apoyo analítico y no sustituyen una política crediticia institucional."
)
