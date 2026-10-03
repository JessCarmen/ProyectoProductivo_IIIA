import os

import pandas as pd
import requests
import streamlit as st

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000").rstrip("/")

st.set_page_config(page_title="Riesgo Crediticio", page_icon="📊", layout="wide")
st.title("Cartera de Riesgo Crediticio")
st.caption("Vista operativa basada en el scoring real almacenado en Gold")


def api_get(path, params=None):
    response = requests.get(f"{API_BASE_URL}{path}", params=params, timeout=30)
    response.raise_for_status()
    return response.json()

try:
    summary = api_get("/portfolio/summary")
except Exception as exc:
    st.error(f"No se pudo conectar con FastAPI: {exc}")
    st.stop()

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Cartera", f"{summary['total']:,}")
c2.metric("PD promedio", f"{summary['pd_promedio']:.2%}")
c3.metric("Predicción 1", f"{summary['prediccion_1']:,}")
c4.metric("Alto", f"{summary['alto']:,}")
c5.metric("Crítico", f"{summary['critico']:,}")

st.subheader("Semáforo general")
risk_df = pd.DataFrame({
    "Nivel": ["BAJO", "MEDIO", "ALTO", "CRITICO"],
    "Clientes": [summary["bajo"], summary["medio"], summary["alto"], summary["critico"]],
}).set_index("Nivel")
st.bar_chart(risk_df)

st.subheader("Consulta por cliente")
customer_id = st.number_input("ID del cliente", min_value=1, step=1, value=1)
if st.button("Consultar"):
    try:
        customer = api_get(f"/portfolio/{int(customer_id)}")
        a, b, c = st.columns(3)
        a.metric("Probabilidad de incumplimiento", f"{float(customer['probability_default']):.2%}")
        b.metric("Clasificación", int(customer["prediction"]))
        c.metric("Nivel de riesgo", customer["risk_level"])
        st.write("**Recomendación**")
        st.info(customer["recommendation"])
        st.write("**Señales principales**")
        cols = ["limit_bal", "age", "pay_0", "pay_max_delay", "recent_delay_months", "consecutive_delay_months", "payment_bill_ratio_total"]
        visible = {k: customer.get(k) for k in cols if k in customer}
        st.dataframe(pd.DataFrame([visible]), width="stretch", hide_index=True)
    except requests.HTTPError as exc:
        st.error(f"No se pudo consultar el cliente: {exc}")

st.subheader("Tabla operativa")
risk_filter = st.selectbox("Nivel de riesgo", ["TODOS", "BAJO", "MEDIO", "ALTO", "CRITICO"])
params = {"limit": 200}
if risk_filter != "TODOS":
    params["risk"] = risk_filter
try:
    rows = api_get("/portfolio", params=params)
    df = pd.DataFrame(rows)
    preferred = ["id", "probability_default", "prediction", "risk_level", "limit_bal", "age", "pay_max_delay", "recent_delay_months", "recommendation"]
    cols = [c for c in preferred if c in df.columns]
    st.dataframe(df[cols], width="stretch", hide_index=True)
except Exception as exc:
    st.warning(f"No se pudo cargar la tabla: {exc}")
