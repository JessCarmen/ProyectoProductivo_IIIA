"""Panel de revisión humana para NexaRisk (demo académica con clave de analista)."""
import hmac
import os

import pandas as pd
import requests
import streamlit as st


def _secret(name):
    try:
        return str(st.secrets.get(name, "")).strip()
    except Exception:
        return os.getenv(name, "").strip()


def render_review_panel(customer, api_base_url):
    st.divider()
    st.subheader("Validación humana del scoring")
    st.caption("Revisión supervisada. No modifica la predicción original ni demuestra por sí sola un falso positivo.")

    api_key = _secret("REVIEW_API_KEY")
    analyst_password = _secret("REVIEW_ANALYST_PASSWORD")
    if len(api_key) < 24 or len(analyst_password) < 12:
        st.info("Módulo de revisión no habilitado. El dashboard público sigue en modo consulta.")
        return

    if not st.session_state.get("nexarisk_review_authenticated", False):
        with st.form("login_analyst"):
            password = st.text_input("Clave de acceso para analistas", type="password")
            login = st.form_submit_button("Acceder a revisión")
        if login:
            if hmac.compare_digest(password, analyst_password):
                st.session_state["nexarisk_review_authenticated"] = True
                st.rerun()
            else:
                st.error("Clave incorrecta")
        return

    score_id = customer.get("score_output_id")
    prediction = customer.get("prediction")
    if score_id is None or prediction not in (0, 1):
        st.warning("El registro no contiene los identificadores necesarios para registrar una revisión.")
        return

    st.write(f"**Cliente:** {customer['id']} · **Scoring:** {score_id} · **Predicción original:** {prediction}")
    st.warning("No pegues DNI, teléfonos, direcciones, contraseñas ni documentos personales en los comentarios.")

    with st.form(f"review_form_{score_id}", clear_on_submit=True):
        reviewer_id = st.text_input("Código del analista", max_chars=80, placeholder="Ej. ANALISTA_01")
        decision = st.radio("Resultado de la revisión", [
            "CONFIRMADO", "OBSERVADO", "CORRECCION_PROPUESTA"
        ], format_func=lambda x: {
            "CONFIRMADO": "Confirmo la evaluación del modelo",
            "OBSERVADO": "Requiere revisión adicional",
            "CORRECCION_PROPUESTA": "Propongo corregir la clasificación binaria"
        }[x])
        proposed = None
        if decision == "CORRECCION_PROPUESTA":
            proposed = st.selectbox("Clasificación propuesta", [1 - int(prediction)])
        evidence_type = st.selectbox("Tipo de evidencia", [
            "HISTORIAL_PAGOS", "INGRESOS_VERIFICADOS", "OBLIGACIONES",
            "DATOS_INCORRECTOS", "OTRO"
        ])
        evidence_reference = st.text_input(
            "Referencia interna de evidencia (obligatoria si propone corrección)",
            max_chars=160,
            placeholder="Ej. expediente académico DEMO-004"
        )
        review_note = st.text_area(
            "Justificación de la revisión (20 a 500 caracteres)", max_chars=500
        )
        attest = st.checkbox("Confirmo que revisé la información y que no estoy incorporando datos personales en el texto.")
        submit = st.form_submit_button("Guardar revisión en Supabase", type="primary")

    if submit:
        if not attest:
            st.error("Debes confirmar la revisión antes de guardarla.")
        elif len(reviewer_id.strip()) < 3 or len(review_note.strip()) < 20:
            st.error("Completa el código del analista y una justificación de al menos 20 caracteres.")
        else:
            payload = {
                "customer_id": int(customer["id"]),
                "score_output_id": int(score_id),
                "review_status": decision,
                "proposed_prediction": proposed,
                "reviewer_id": reviewer_id.strip(),
                "evidence_type": evidence_type,
                "evidence_reference": evidence_reference.strip() or None,
                "review_note": review_note.strip(),
            }
            try:
                response = requests.post(
                    f"{api_base_url}/reviews", json=payload,
                    headers={"X-Review-Key": api_key}, timeout=90,
                )
                if response.status_code == 201:
                    st.success("Revisión guardada. La predicción original permanece intacta.")
                else:
                    st.error(f"No se guardó la revisión (HTTP {response.status_code}).")
            except requests.RequestException:
                st.error("No se pudo conectar con el servicio de revisiones.")

    if st.button("Ver historial de revisiones", key=f"review_history_{score_id}"):
        try:
            response = requests.get(
                f"{api_base_url}/reviews/{customer['id']}",
                headers={"X-Review-Key": api_key}, timeout=90,
            )
            response.raise_for_status()
            records = response.json().get("results", [])
            if records:
                st.dataframe(pd.DataFrame(records), hide_index=True, use_container_width=True)
            else:
                st.info("Aún no existen revisiones para este cliente.")
        except requests.RequestException:
            st.error("No fue posible recuperar el historial.")
