import os
import time
import textwrap
from typing import Any

import pandas as pd
import requests
import streamlit as st


# ============================================================
# CONFIGURACION
# ============================================================

st.set_page_config(
    page_title="NexaRisk | Supervisión de Riesgo Crediticio",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# ============================================================
# IDENTIDAD VISUAL
# ============================================================

NAVY = "#0B1F33"
NAVY_2 = "#153A59"
TEAL = "#0E7490"
MINT = "#14B8A6"
GOLD = "#F4B942"

CLOUD = "#F5F8FB"
WHITE = "#FFFFFF"
INK = "#172033"
MUTED = "#667085"
BORDER = "#DFE7EE"

GREEN = "#2E8B57"
AMBER = "#D4A017"
ORANGE = "#E67E22"
RED = "#C62828"


def html(content: str):
    """
    Render HTML without Markdown interpreting indentation
    as a code block.
    """
    st.markdown(
        textwrap.dedent(content).strip(),
        unsafe_allow_html=True,
    )


# ============================================================
# CSS
# ============================================================

html(
    f"""
    <style>
    .stApp {{
        background: {CLOUD};
    }}

    .block-container {{
        max-width: 1650px;
        padding-top: 1rem;
        padding-bottom: 2rem;
    }}

    [data-testid="stHeader"] {{
        background: transparent;
    }}

    /* ---------- HEADER ---------- */

    .nexa-header {{
        background: linear-gradient(
            120deg,
            {NAVY} 0%,
            {NAVY_2} 65%,
            {TEAL} 100%
        );
        border-radius: 16px;
        padding: 22px 26px;
        margin-bottom: 16px;
        box-shadow: 0 8px 24px rgba(11,31,51,.12);
        display: flex;
        justify-content: space-between;
        align-items: center;
    }}

    .nexa-brand {{
        display: flex;
        align-items: center;
        gap: 16px;
    }}

    .nexa-logo {{
        width: 58px;
        height: 58px;
        border-radius: 13px;
        background: linear-gradient(135deg, {MINT}, {TEAL});
        color: white;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 23px;
        font-weight: 850;
        box-shadow: inset 0 0 0 1px rgba(255,255,255,.20);
    }}

    .nexa-name {{
        color: white;
        font-size: 27px;
        line-height: 1.05;
        font-weight: 800;
    }}

    .nexa-subtitle {{
        margin-top: 5px;
        color: rgba(255,255,255,.75);
        font-size: 13px;
    }}

    .nexa-status {{
        color: white;
        background: rgba(255,255,255,.10);
        border: 1px solid rgba(255,255,255,.20);
        padding: 9px 13px;
        border-radius: 10px;
        font-size: 12px;
    }}

    .online {{
        color: #58E6A7;
        font-weight: 800;
    }}

    /* ---------- KPI ---------- */

    .kpi-card {{
        background: white;
        border: 1px solid {BORDER};
        border-radius: 13px;
        padding: 17px 18px;
        min-height: 112px;
        box-shadow: 0 3px 12px rgba(16,24,40,.04);
    }}

    .kpi-label {{
        font-size: 11px;
        color: {MUTED};
        font-weight: 750;
        letter-spacing: .55px;
        text-transform: uppercase;
    }}

    .kpi-value {{
        margin-top: 5px;
        color: {INK};
        font-size: 29px;
        font-weight: 800;
    }}

    .kpi-note {{
        margin-top: 3px;
        color: {MUTED};
        font-size: 11px;
    }}

    .accent-red {{
        border-left: 5px solid {RED};
    }}

    .accent-teal {{
        border-left: 5px solid {MINT};
    }}

    /* ---------- TITULOS ---------- */

    .section-title {{
        color: {INK};
        font-size: 16px;
        font-weight: 800;
        margin-bottom: 1px;
    }}

    .section-caption {{
        color: {MUTED};
        font-size: 11px;
        margin-bottom: 9px;
    }}

    /* ---------- PANEL FILTROS ---------- */

    .filter-head {{
        background: {NAVY};
        color: white;
        padding: 12px 14px;
        border-radius: 10px;
        font-weight: 800;
        margin-bottom: 10px;
    }}

    /* ---------- ALERTA ---------- */

    .exec-alert {{
        margin-top: 8px;
        background: #FFF7F5;
        border: 1px solid #F7D6CF;
        border-left: 5px solid {RED};
        border-radius: 10px;
        padding: 13px 15px;
        color: {INK};
        font-size: 12px;
    }}

    /* ---------- STREAMLIT METRICS ---------- */

    [data-testid="stMetric"] {{
        background: white;
        border: 1px solid {BORDER};
        padding: 14px;
        border-radius: 12px;
    }}

    /* ---------- TABLA ---------- */

    [data-testid="stDataFrame"] {{
        background: white;
        border-radius: 10px;
    }}

    /* ---------- BOTON ---------- */

    .stButton > button {{
        border-radius: 8px;
        font-weight: 700;
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

    return os.getenv(
        "API_BASE_URL",
        "http://127.0.0.1:8000",
    ).rstrip("/")


API_BASE_URL = get_api_base_url()
REQUEST_TIMEOUT = 90


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
        f"No fue posible conectar con FastAPI: {last_error}"
    )


@st.cache_data(ttl=60)
def load_summary():
    return api_get("/portfolio/summary")


@st.cache_data(ttl=60)
def load_portfolio(
    risk_level: str | None = None,
    limit: int = 250,
):
    params = {"limit": limit}

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
# HELPERS
# ============================================================

def extract_records(payload: Any) -> list:
    if isinstance(payload, list):
        return payload

    if isinstance(payload, dict):
        for key in [
            "items",
            "data",
            "results",
            "portfolio",
            "records",
        ]:
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
    ]

    for col in numeric_columns:
        if col in df.columns:
            df[col] = pd.to_numeric(
                df[col],
                errors="coerce",
            )

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


def fmt_num(value):
    try:
        return f"{float(value):,.0f}".replace(",", ".")
    except Exception:
        return "N/D"


# ============================================================
# CARGA INICIAL
# ============================================================

try:
    summary = load_summary()

except Exception as exc:
    st.error(
        "No fue posible conectar con FastAPI."
    )

    st.info(
        "El servicio gratuito de Render puede tardar "
        "algunos segundos en despertar."
    )

    with st.expander("Detalle técnico"):
        st.exception(exc)

    st.stop()


# ============================================================
# HEADER
# ============================================================

html(
    f"""
    <div class="nexa-header">
        <div class="nexa-brand">
            <div class="nexa-logo">NR</div>

            <div>
                <div class="nexa-name">
                    NexaRisk
                </div>

                <div class="nexa-subtitle">
                    Centro de Supervisión de Riesgo Crediticio
                </div>
            </div>
        </div>

        <div class="nexa-status">
            <span class="online">● API ONLINE</span>
            &nbsp;&nbsp;|&nbsp;&nbsp;
            Modelo {summary.get("model_version", "N/D")}
        </div>
    </div>
    """
)


# ============================================================
# CALCULOS
# ============================================================

total = int(summary.get("total", 0))
bajo = int(summary.get("bajo", 0))
medio = int(summary.get("medio", 0))
alto = int(summary.get("alto", 0))
critico = int(summary.get("critico", 0))

priority = alto + critico

priority_pct = (
    priority / total
    if total
    else 0
)


# ============================================================
# KPIs
# ============================================================

k1, k2, k3, k4 = st.columns(4)


with k1:
    html(
        f"""
        <div class="kpi-card accent-teal">
            <div class="kpi-label">Cartera evaluada</div>
            <div class="kpi-value">{fmt_int(total)}</div>
            <div class="kpi-note">
                Clientes con scoring vigente
            </div>
        </div>
        """
    )


with k2:
    html(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">PD promedio</div>
            <div class="kpi-value">
                {fmt_pct(summary.get("pd_promedio"))}
            </div>
            <div class="kpi-note">
                Probabilidad media de incumplimiento
            </div>
        </div>
        """
    )


with k3:
    html(
        f"""
        <div class="kpi-card accent-red">
            <div class="kpi-label">
                Gestión prioritaria
            </div>

            <div class="kpi-value">
                {fmt_int(priority)}
            </div>

            <div class="kpi-note">
                {fmt_pct(priority_pct)}
                de la cartera en Alto + Crítico
            </div>
        </div>
        """
    )


with k4:
    html(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">
                Predicción positiva
            </div>

            <div class="kpi-value">
                {fmt_int(summary.get("prediction_1"))}
            </div>

            <div class="kpi-note">
                Clientes clasificados como potencial incumplimiento
            </div>
        </div>
        """
    )


st.write("")


# ============================================================
# LAYOUT: DASHBOARD + FILTROS DERECHA
# ============================================================

main_col, right_col = st.columns(
    [5, 1.35],
    gap="large",
)


# ============================================================
# PANEL DERECHO
# ============================================================

with right_col:

    html(
        """
        <div class="filter-head">
            Filtros de cartera
        </div>
        """
    )

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

    prediction_filter = st.selectbox(
        "Clasificación",
        [
            "TODAS",
            "1",
            "0",
        ],
    )

    min_pd = st.slider(
        "PD mínima",
        min_value=0,
        max_value=100,
        value=0,
        step=5,
    )

    row_limit = st.selectbox(
        "Registros",
        [
            50,
            100,
            250,
            500,
            1000,
        ],
        index=2,
    )

    st.divider()

    html(
        """
        <div class="section-title">
            Consulta rápida
        </div>
        """
    )

    customer_id = st.number_input(
        "ID cliente",
        min_value=1,
        step=1,
        value=1,
    )

    search_customer = st.button(
        "Consultar cliente",
        type="primary",
        use_container_width=True,
    )


# ============================================================
# CONTENIDO PRINCIPAL
# ============================================================

with main_col:

    # --------------------------------------------------------
    # FILA DE GRAFICOS
    # --------------------------------------------------------

    g1, g2 = st.columns(
        [1.25, 1],
        gap="medium",
    )


    with g1:

        html(
            """
            <div class="section-title">
                Distribución de riesgo
            </div>
            <div class="section-caption">
                Clientes por banda de riesgo
            </div>
            """
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
                    bajo,
                    medio,
                    alto,
                    critico,
                ],
            }
        )

        st.bar_chart(
            risk_df.set_index("Nivel"),
            height=310,
        )


    with g2:

        html(
            """
            <div class="section-title">
                Clasificación del modelo
            </div>
            <div class="section-caption">
                Distribución de predicción binaria
            </div>
            """
        )

        prediction_df = pd.DataFrame(
            {
                "Clase": [
                    "Predicción 0",
                    "Predicción 1",
                ],
                "Clientes": [
                    int(
                        summary.get(
                            "prediction_0",
                            0,
                        )
                    ),
                    int(
                        summary.get(
                            "prediction_1",
                            0,
                        )
                    ),
                ],
            }
        )

        st.bar_chart(
            prediction_df.set_index("Clase"),
            height=310,
        )


    # --------------------------------------------------------
    # LECTURA EJECUTIVA
    # --------------------------------------------------------

    html(
        f"""
        <div class="exec-alert">
            <b>Lectura ejecutiva:</b>
            actualmente
            <b>{fmt_int(priority)}</b>
            clientes están clasificados en niveles
            <b>ALTO o CRÍTICO</b>,
            equivalentes al
            <b>{fmt_pct(priority_pct)}</b>
            de la cartera evaluada.

            Esta población constituye la principal
            cola de seguimiento preventivo.
        </div>
        """
    )


    st.write("")


    # --------------------------------------------------------
    # TABLA
    # --------------------------------------------------------

    html(
        """
        <div class="section-title">
            Cartera priorizada
        </div>

        <div class="section-caption">
            Ordenada por mayor probabilidad de incumplimiento
        </div>
        """
    )


    try:
        payload = load_portfolio(
            risk_level=risk_filter,
            limit=row_limit,
        )

        df = normalize_df(payload)


        if df.empty:
            st.warning(
                "No existen registros para los filtros seleccionados."
            )

        else:

            # -------------------------
            # FILTRO PREDICCION
            # -------------------------

            if (
                prediction_filter != "TODAS"
                and "prediction" in df.columns
            ):
                df = df[
                    df["prediction"]
                    == int(prediction_filter)
                ]


            # -------------------------
            # FILTRO PD
            # -------------------------

            if "probability_default" in df.columns:

                df = df[
                    df["probability_default"]
                    >= min_pd / 100
                ]

                df = df.sort_values(
                    "probability_default",
                    ascending=False,
                )


            # -------------------------
            # PD EN PORCENTAJE
            # -------------------------

            if "probability_default" in df.columns:
                df["pd_percent"] = (
                    df["probability_default"]
                    * 100
                )


            columns = [
                "id",
                "pd_percent",
                "prediction",
                "risk_level",
                "limit_bal",
                "age",
                "pay_max_delay",
                "recent_delay_months",
                "consecutive_delay_months",
                "recommendation",
            ]

            columns = [
                c
                for c in columns
                if c in df.columns
            ]

            display_df = df[
                columns
            ].copy()


            display_df = display_df.rename(
                columns={
                    "id": "Cliente",
                    "pd_percent": "PD %",
                    "prediction": "Pred.",
                    "risk_level": "Riesgo",
                    "limit_bal": "Límite",
                    "age": "Edad",
                    "pay_max_delay": "Máx. atraso",
                    "recent_delay_months": "Atrasos recientes",
                    "consecutive_delay_months": "Atrasos consecutivos",
                    "recommendation": "Acción sugerida",
                }
            )


            st.caption(
                f"{len(display_df):,} clientes mostrados"
            )


            st.dataframe(
                display_df,
                use_container_width=True,
                hide_index=True,
                height=455,

                column_config={
                    "Cliente":
                        st.column_config.NumberColumn(
                            "Cliente",
                            format="%d",
                        ),

                    "PD %":
                        st.column_config.ProgressColumn(
                            "PD %",
                            min_value=0,
                            max_value=100,
                            format="%.1f%%",
                        ),

                    "Pred.":
                        st.column_config.NumberColumn(
                            "Pred.",
                            format="%d",
                        ),

                    "Límite":
                        st.column_config.NumberColumn(
                            "Límite",
                            format="%.0f",
                        ),
                },
            )


            csv = display_df.to_csv(
                index=False
            ).encode("utf-8-sig")


            st.download_button(
                "⬇ Descargar cartera filtrada",
                data=csv,
                file_name="cartera_filtrada_nexarisk.csv",
                mime="text/csv",
            )


    except Exception as exc:

        st.error(
            "No fue posible cargar la cartera."
        )

        with st.expander("Detalle técnico"):
            st.exception(exc)


# ============================================================
# CLIENTE 360
# ============================================================

if search_customer:

    st.divider()

    try:

        customer = load_customer(
            int(customer_id)
        )

        st.subheader(
            f"Cliente 360 · #{int(customer_id)}"
        )

        c1, c2, c3, c4 = st.columns(4)

        c1.metric(
            "PD",
            fmt_pct(
                customer.get(
                    "probability_default"
                )
            ),
        )

        c2.metric(
            "Nivel de riesgo",
            customer.get(
                "risk_level",
                "N/D",
            ),
        )

        c3.metric(
            "Clasificación",
            customer.get(
                "prediction",
                "N/D",
            ),
        )

        c4.metric(
            "Límite de crédito",
            fmt_num(
                customer.get(
                    "limit_bal"
                )
            ),
        )


        st.markdown(
            "#### Recomendación de gestión"
        )

        st.info(
            customer.get(
                "recommendation",
                "No disponible",
            )
        )


        s1, s2, s3, s4 = st.columns(4)

        s1.metric(
            "Edad",
            customer.get(
                "age",
                "N/D",
            ),
        )

        s2.metric(
            "Máximo atraso",
            customer.get(
                "pay_max_delay",
                "N/D",
            ),
        )

        s3.metric(
            "Atrasos recientes",
            customer.get(
                "recent_delay_months",
                "N/D",
            ),
        )

        s4.metric(
            "Atrasos consecutivos",
            customer.get(
                "consecutive_delay_months",
                "N/D",
            ),
        )


    except Exception as exc:

        st.error(
            "No fue posible consultar ese cliente."
        )

        with st.expander("Detalle técnico"):
            st.exception(exc)


# ============================================================
# PIE
# ============================================================

st.divider()

f1, f2, f3 = st.columns(
    [2, 1, 1]
)

with f1:
    st.caption(
        "NexaRisk · Proyecto Productivo IIIA"
    )

with f2:
    st.caption(
        f"Modelo: {summary.get('model_version', 'N/D')}"
    )

with f3:
    st.caption(
        "FastAPI · Supabase · Streamlit"
    )

