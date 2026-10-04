import os
import time
from typing import Any

import pandas as pd
import requests
import streamlit as st


# ============================================================
# CONFIGURACION
# ============================================================

st.set_page_config(
    page_title="NexaRisk | Supervisión de Riesgo",
    page_icon="NR",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# ============================================================
# PALETA
# ============================================================

NAVY = "#0B1F33"
TEAL = "#0E7490"
MINT = "#14B8A6"
GOLD = "#F4B942"

CLOUD = "#F5F8FB"
INK = "#172033"
MUTED = "#667085"

GREEN = "#2E8B57"
AMBER = "#D4A017"
ORANGE = "#E67E22"
RED = "#C62828"

WHITE = "#FFFFFF"
BORDER = "#E4EAF0"


# ============================================================
# CSS
# ============================================================

st.markdown(
    f"""
    <style>

    /* ------------------------------------------------------
       GLOBAL
    ------------------------------------------------------ */

    .stApp {{
        background-color: {CLOUD};
    }}

    [data-testid="stHeader"] {{
        background: transparent;
    }}

    [data-testid="stToolbar"] {{
        visibility: hidden;
    }}

    .block-container {{
        max-width: 1700px;
        padding-top: 1.1rem;
        padding-bottom: 2rem;
    }}

    h1, h2, h3 {{
        color: {INK};
    }}


    /* ------------------------------------------------------
       HEADER
    ------------------------------------------------------ */

    .nr-header {{
        background:
            linear-gradient(
                120deg,
                {NAVY} 0%,
                #123653 65%,
                {TEAL} 100%
            );

        border-radius: 14px;
        padding: 20px 25px;
        margin-bottom: 16px;

        box-shadow:
            0 7px 22px rgba(11,31,51,0.12);

        display: flex;
        align-items: center;
        justify-content: space-between;
    }}

    .nr-brand {{
        display: flex;
        align-items: center;
        gap: 16px;
    }}

    .nr-logo {{
        width: 58px;
        height: 58px;

        background:
            linear-gradient(
                135deg,
                {MINT},
                {TEAL}
            );

        border-radius: 12px;

        display: flex;
        align-items: center;
        justify-content: center;

        color: white;
        font-size: 23px;
        font-weight: 800;

        letter-spacing: -1px;

        box-shadow:
            inset 0 0 0 1px rgba(255,255,255,.18);
    }}

    .nr-title {{
        color: white;
        font-size: 27px;
        font-weight: 750;
        margin: 0;
    }}

    .nr-subtitle {{
        color: rgba(255,255,255,.75);
        font-size: 13px;
        margin-top: 3px;
    }}

    .nr-status {{
        background: rgba(255,255,255,.1);
        border: 1px solid rgba(255,255,255,.25);

        border-radius: 10px;
        padding: 9px 14px;

        color: white;
        font-size: 12px;
    }}

    .nr-online {{
        color: #51E3A4;
        font-weight: 700;
    }}


    /* ------------------------------------------------------
       KPI CARD
    ------------------------------------------------------ */

    .nr-card {{
        background: {WHITE};

        border: 1px solid {BORDER};
        border-radius: 12px;

        padding: 17px 18px;

        box-shadow:
            0 3px 12px rgba(16,24,40,.04);

        min-height: 112px;
    }}

    .nr-label {{
        color: {MUTED};

        font-size: 11px;
        font-weight: 700;

        text-transform: uppercase;
        letter-spacing: .6px;
    }}

    .nr-value {{
        color: {INK};

        font-size: 29px;
        font-weight: 760;

        margin-top: 4px;
    }}

    .nr-caption {{
        color: {MUTED};
        font-size: 11px;
        margin-top: 2px;
    }}

    .critical {{
        border-left: 5px solid {RED};
    }}

    .high {{
        border-left: 5px solid {ORANGE};
    }}

    .medium {{
        border-left: 5px solid {AMBER};
    }}

    .low {{
        border-left: 5px solid {GREEN};
    }}


    /* ------------------------------------------------------
       SECCIONES
    ------------------------------------------------------ */

    .nr-section {{
        background: white;

        border: 1px solid {BORDER};
        border-radius: 12px;

        padding: 17px;

        box-shadow:
            0 3px 12px rgba(16,24,40,.04);

        margin-bottom: 10px;
    }}

    .nr-section-title {{
        color: {INK};

        font-size: 15px;
        font-weight: 750;

        margin-bottom: 3px;
    }}

    .nr-section-subtitle {{
        color: {MUTED};
        font-size: 11px;
        margin-bottom: 12px;
    }}


    /* ------------------------------------------------------
       PANEL DERECHO
    ------------------------------------------------------ */

    .nr-filter-title {{
        color: white;
        font-size: 16px;
        font-weight: 750;
    }}

    .nr-filter-header {{
        background: {NAVY};

        padding: 13px 15px;

        border-radius: 10px 10px 0 0;

        margin-bottom: 10px;
    }}


    /* ------------------------------------------------------
       ALERTA EJECUTIVA
    ------------------------------------------------------ */

    .nr-alert {{
        background: #FFF7F5;
        border: 1px solid #FFD7D0;
        border-left: 5px solid {RED};

        border-radius: 10px;

        padding: 13px 15px;

        color: {INK};
        font-size: 12px;

        margin-top: 8px;
    }}


    /* ------------------------------------------------------
       BADGES
    ------------------------------------------------------ */

    .badge-critical {{
        color: {RED};
        font-weight: 700;
    }}

    .badge-high {{
        color: {ORANGE};
        font-weight: 700;
    }}

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# API
# ============================================================

def get_api_base_url():

    try:
        if "API_BASE_URL" in st.secrets:
            return str(
                st.secrets["API_BASE_URL"]
            ).rstrip("/")
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
    params=None,
    retries=2,
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
        f"No fue posible conectar con FastAPI: "
        f"{last_error}"
    )


@st.cache_data(ttl=60)
def load_summary():

    return api_get(
        "/portfolio/summary"
    )


@st.cache_data(ttl=60)
def load_portfolio(
    risk_level=None,
    limit=500,
):

    params = {
        "limit": limit,
    }

    if (
        risk_level
        and risk_level != "TODOS"
    ):
        params[
            "risk_level"
        ] = risk_level

    return api_get(
        "/portfolio",
        params=params,
    )


def load_customer(customer_id):

    return api_get(
        f"/portfolio/{customer_id}"
    )


# ============================================================
# HELPERS
# ============================================================

def extract_records(payload):

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


def normalize_df(payload):

    records = extract_records(
        payload
    )

    if not records:
        return pd.DataFrame()

    df = pd.DataFrame(
        records
    )

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


def format_integer(value):

    try:
        return f"{int(value):,}"

    except Exception:
        return "N/D"


def format_percent(value):

    try:
        return f"{float(value):.2%}"

    except Exception:
        return "N/D"


def format_money(value):

    try:
        return f"{float(value):,.0f}"

    except Exception:
        return "N/D"


# ============================================================
# DATOS
# ============================================================

try:

    summary = load_summary()

except Exception as exc:

    st.error(
        "No fue posible conectar con FastAPI."
    )

    st.info(
        "Render Free puede tardar unos segundos "
        "en despertar."
    )

    st.exception(exc)
    st.stop()


# ============================================================
# HEADER
# ============================================================

st.markdown(
    f"""
    <div class="nr-header">

        <div class="nr-brand">

            <div class="nr-logo">
                NR
            </div>

            <div>

                <div class="nr-title">
                    NexaRisk
                </div>

                <div class="nr-subtitle">
                    Centro de Supervisión de Riesgo Crediticio
                </div>

            </div>

        </div>

        <div class="nr-status">

            <span class="nr-online">
                ● API ONLINE
            </span>

            &nbsp;&nbsp;|&nbsp;&nbsp;

            Modelo
            {summary.get("model_version", "N/D")}

        </div>

    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# KPIs SUPERIORES
# ============================================================

total = int(
    summary.get("total", 0)
)

critical = int(
    summary.get("critico", 0)
)

high = int(
    summary.get("alto", 0)
)

priority = (
    critical
    + high
)

priority_pct = (
    priority / total
    if total > 0
    else 0
)


k1, k2, k3, k4 = st.columns(4)


with k1:

    st.markdown(
        f"""
        <div class="nr-card">
            <div class="nr-label">
                Cartera evaluada
            </div>

            <div class="nr-value">
                {format_integer(total)}
            </div>

            <div class="nr-caption">
                Clientes con scoring vigente
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


with k2:

    st.markdown(
        f"""
        <div class="nr-card">
            <div class="nr-label">
                PD promedio
            </div>

            <div class="nr-value">
                {
                    format_percent(
                        summary.get(
                            "pd_promedio"
                        )
                    )
                }
            </div>

            <div class="nr-caption">
                Probabilidad promedio de incumplimiento
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


with k3:

    st.markdown(
        f"""
        <div class="nr-card critical">
            <div class="nr-label">
                Gestión prioritaria
            </div>

            <div class="nr-value">
                {format_integer(priority)}
            </div>

            <div class="nr-caption">
                {
                    format_percent(
                        priority_pct
                    )
                }
                de la cartera en Alto + Crítico
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


with k4:

    st.markdown(
        f"""
        <div class="nr-card">
            <div class="nr-label">
                Predicción = 1
            </div>

            <div class="nr-value">
                {
                    format_integer(
                        summary.get(
                            "prediction_1"
                        )
                    )
                }
            </div>

            <div class="nr-caption">
                Clasificados como potencial incumplimiento
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


st.write("")


# ============================================================
# LAYOUT PRINCIPAL
# ============================================================

main_col, filter_col = st.columns(
    [4.8, 1.25],
    gap="large",
)


# ============================================================
# PANEL DERECHO DE FILTROS
# ============================================================

with filter_col:

    st.markdown(
        """
        <div class="nr-filter-header">
            <div class="nr-filter-title">
                Filtros de cartera
            </div>
        </div>
        """,
        unsafe_allow_html=True,
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
        "Clientes a mostrar",
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

    st.markdown(
        "**Consulta rápida**"
    )

    quick_customer = st.number_input(
        "ID cliente",
        min_value=1,
        value=1,
        step=1,
    )

    quick_search = st.button(
        "Consultar cliente",
        type="primary",
        use_container_width=True,
    )

    st.divider()

    st.caption(
        "Los filtros de clasificación y PD "
        "se aplican sobre la cartera cargada "
        "desde FastAPI."
    )


# ============================================================
# CONTENIDO PRINCIPAL
# ============================================================

with main_col:

    # --------------------------------------------------------
    # DISTRIBUCION DE RIESGO
    # --------------------------------------------------------

    chart1, chart2 = st.columns(
        [1.3, 1],
        gap="medium",
    )


    with chart1:

        st.markdown(
            """
            <div class="nr-section-title">
                Distribución de riesgo
            </div>

            <div class="nr-section-subtitle">
                Composición de la cartera según banda de riesgo
            </div>
            """,
            unsafe_allow_html=True,
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
                    int(
                        summary.get(
                            "bajo",
                            0,
                        )
                    ),

                    int(
                        summary.get(
                            "medio",
                            0,
                        )
                    ),

                    int(
                        summary.get(
                            "alto",
                            0,
                        )
                    ),

                    int(
                        summary.get(
                            "critico",
                            0,
                        )
                    ),
                ],
            }
        )

        st.bar_chart(
            risk_df.set_index(
                "Nivel"
            )
        )


    with chart2:

        st.markdown(
            """
            <div class="nr-section-title">
                Clasificación del modelo
            </div>

            <div class="nr-section-subtitle">
                Distribución de clientes 0 / 1
            </div>
            """,
            unsafe_allow_html=True,
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
            prediction_df.set_index(
                "Clase"
            )
        )


    # --------------------------------------------------------
    # ALERTA EJECUTIVA
    # --------------------------------------------------------

    st.markdown(
        f"""
        <div class="nr-alert">

            <b>Lectura ejecutiva:</b>

            actualmente
            <b>{format_integer(priority)}</b>
            clientes se encuentran en niveles

            <span class="badge-high">
                ALTO
            </span>

            o

            <span class="badge-critical">
                CRÍTICO
            </span>,

            equivalentes al

            <b>{format_percent(priority_pct)}</b>

            de la cartera evaluada.

            Esta población representa la principal
            cola de seguimiento preventivo.

        </div>
        """,
        unsafe_allow_html=True,
    )


    st.write("")


    # --------------------------------------------------------
    # CARTERA OPERATIVA
    # --------------------------------------------------------

    st.markdown(
        """
        <div class="nr-section-title">
            Cartera priorizada
        </div>

        <div class="nr-section-subtitle">
            Clientes ordenados por mayor probabilidad
            de incumplimiento
        </div>
        """,
        unsafe_allow_html=True,
    )


    try:

        payload = load_portfolio(
            risk_level=risk_filter,
            limit=row_limit,
        )

        df = normalize_df(
            payload
        )


        if df.empty:

            st.warning(
                "No existen registros "
                "para los filtros seleccionados."
            )

        else:

            # ------------------------------------------------
            # FILTRO PREDICCION
            # ------------------------------------------------

            if (
                prediction_filter
                != "TODAS"
                and "prediction" in df.columns
            ):

                df = df[
                    df["prediction"]
                    == int(
                        prediction_filter
                    )
                ]


            # ------------------------------------------------
            # FILTRO PD
            # ------------------------------------------------

            if (
                "probability_default"
                in df.columns
            ):

                df = df[
                    df[
                        "probability_default"
                    ]
                    >= (
                        min_pd / 100
                    )
                ]


                df = df.sort_values(
                    "probability_default",
                    ascending=False,
                )


            # ------------------------------------------------
            # COLUMNAS
            # ------------------------------------------------

            selected_cols = [
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
            ]

            selected_cols = [
                col
                for col in selected_cols
                if col in df.columns
            ]

            display_df = df[
                selected_cols
            ].copy()


            display_df = display_df.rename(
                columns={
                    "id":
                        "Cliente",

                    "probability_default":
                        "PD",

                    "prediction":
                        "Pred.",

                    "risk_level":
                        "Riesgo",

                    "limit_bal":
                        "Límite",

                    "age":
                        "Edad",

                    "pay_max_delay":
                        "Máx. atraso",

                    "recent_delay_months":
                        "Atrasos recientes",

                    "consecutive_delay_months":
                        "Atrasos consecutivos",

                    "recommendation":
                        "Acción sugerida",
                }
            )


            st.caption(
                f"{len(display_df):,} "
                "clientes mostrados"
            )


            st.dataframe(
                display_df,
                use_container_width=True,
                hide_index=True,

                column_config={

                    "PD":
                        st.column_config.ProgressColumn(
                            "PD",
                            min_value=0,
                            max_value=1,
                            format="%.1f%%",
                        ),

                    "Cliente":
                        st.column_config.NumberColumn(
                            "Cliente",
                            format="%d",
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


            # ------------------------------------------------
            # DESCARGA
            # ------------------------------------------------

            csv = display_df.to_csv(
                index=False
            ).encode(
                "utf-8-sig"
            )

            st.download_button(
                "Descargar cartera filtrada",
                data=csv,
                file_name=(
                    "cartera_riesgo_filtrada.csv"
                ),
                mime="text/csv",
            )


    except Exception as exc:

        st.error(
            "No fue posible cargar "
            "la cartera operativa."
        )

        with st.expander(
            "Detalle técnico"
        ):
            st.exception(exc)


# ============================================================
# CLIENTE 360
# ============================================================

if quick_search:

    st.divider()

    st.subheader(
        f"Cliente 360 · #{int(quick_customer)}"
    )

    try:

        customer = load_customer(
            int(
                quick_customer
            )
        )

        risk = customer.get(
            "risk_level",
            "N/D",
        )

        probability = customer.get(
            "probability_default"
        )


        c1, c2, c3, c4 = st.columns(4)

        c1.metric(
            "PD",
            format_percent(
                probability
            ),
        )

        c2.metric(
            "Riesgo",
            risk,
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
            format_money(
                customer.get(
                    "limit_bal"
                )
            ),
        )


        st.markdown(
            "### Recomendación de gestión"
        )

        st.info(
            customer.get(
                "recommendation",
                "No disponible",
            )
        )


        b1, b2, b3, b4 = st.columns(4)

        b1.metric(
            "Edad",
            customer.get(
                "age",
                "N/D",
            ),
        )

        b2.metric(
            "Máximo atraso",
            customer.get(
                "pay_max_delay",
                "N/D",
            ),
        )

        b3.metric(
            "Atrasos recientes",
            customer.get(
                "recent_delay_months",
                "N/D",
            ),
        )

        b4.metric(
            "Atrasos consecutivos",
            customer.get(
                "consecutive_delay_months",
                "N/D",
            ),
        )


    except Exception as exc:

        st.error(
            "No fue posible consultar "
            "el cliente."
        )

        with st.expander(
            "Detalle técnico"
        ):
            st.exception(exc)


# ============================================================
# PIE
# ============================================================

st.divider()

footer1, footer2, footer3 = st.columns(
    [2, 1, 1]
)

with footer1:

    st.caption(
        "NexaRisk · Proyecto Productivo IIIA"
    )

with footer2:

    st.caption(
        f"Modelo: "
        f"{summary.get('model_version', 'N/D')}"
    )

with footer3:

    st.caption(
        "FastAPI · Supabase · Streamlit"
    )

