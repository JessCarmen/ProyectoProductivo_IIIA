"""Revisiones humanas protegidas. No modifica el scoring persistido."""
import hmac
import logging
import os
from typing import Literal

from fastapi import APIRouter, Header, HTTPException
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, Field
from sqlalchemy import text

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Revisión humana"])


class ReviewRequest(BaseModel):
    customer_id: int = Field(gt=0)
    score_output_id: int = Field(gt=0)
    review_status: Literal["CONFIRMADO", "OBSERVADO", "CORRECCION_PROPUESTA"]
    proposed_prediction: int | None = Field(default=None, ge=0, le=1)
    reviewer_id: str = Field(min_length=3, max_length=80)
    evidence_type: Literal[
        "HISTORIAL_PAGOS", "INGRESOS_VERIFICADOS", "OBLIGACIONES",
        "DATOS_INCORRECTOS", "OTRO"
    ]
    evidence_reference: str | None = Field(default=None, max_length=160)
    review_note: str = Field(min_length=20, max_length=500)


def require_review_key(x_review_key: str | None) -> None:
    configured = os.getenv("REVIEW_API_KEY", "")
    if len(configured) < 24:
        raise HTTPException(status_code=503, detail="Revision humana no habilitada")
    if not x_review_key or not hmac.compare_digest(x_review_key, configured):
        raise HTTPException(status_code=401, detail="No autorizado")


def register_review_routes(engine):
    """Se llama desde main.py usando el engine existente."""

    @router.post("/reviews", status_code=201)
    def create_review(payload: ReviewRequest, x_review_key: str | None = Header(default=None)):
        require_review_key(x_review_key)
        status = payload.review_status
        proposed = payload.proposed_prediction
        evidence_ref = (payload.evidence_reference or "").strip() or None
        note = payload.review_note.strip()
        reviewer = payload.reviewer_id.strip()

        if len(note) < 20 or len(reviewer) < 3:
            raise HTTPException(status_code=422, detail="Identificador o justificación insuficiente")
        if status == "CORRECCION_PROPUESTA":
            if proposed is None or not evidence_ref or len(evidence_ref) < 3:
                raise HTTPException(status_code=422, detail="La corrección requiere clase propuesta y referencia de evidencia")
        elif proposed is not None:
            raise HTTPException(status_code=422, detail="Solo una corrección puede proponer otra clase")

        # INSERT ... SELECT: solo acepta el score_output vigente de ese cliente.
        query = text("""
            INSERT INTO gold.scoring_human_reviews (
                score_output_id, customer_id, model_version,
                model_probability, model_prediction, review_status,
                proposed_prediction, reviewer_id, evidence_type,
                evidence_reference, review_note
            )
            SELECT v.score_output_id, v.id, v.modelo_version,
                   v.probability_default, v.prediction, :review_status,
                   :proposed_prediction, :reviewer_id, :evidence_type,
                   :evidence_reference, :review_note
            FROM gold.vw_portfolio_scoring_current v
            WHERE v.id = :customer_id AND v.score_output_id = :score_output_id
              AND (
                    CAST(:proposed_prediction AS INTEGER) IS NULL
                    OR CAST(:proposed_prediction AS INTEGER) <> v.prediction
                )
            RETURNING review_id, customer_id, score_output_id, review_status, created_at
        """)
        try:
            with engine.begin() as conn:
                row = conn.execute(query, {
                    "customer_id": payload.customer_id,
                    "score_output_id": payload.score_output_id,
                    "review_status": status,
                    "proposed_prediction": proposed,
                    "reviewer_id": reviewer,
                    "evidence_type": payload.evidence_type,
                    "evidence_reference": evidence_ref,
                    "review_note": note,
                }).mappings().first()
            if row is None:
                raise HTTPException(status_code=409, detail="El scoring cambió o la corrección no difiere del modelo. Actualiza el cliente.")
            return jsonable_encoder(dict(row))
        except HTTPException:
            raise
        except Exception:
            logger.exception("Error registrando revisión")
            raise HTTPException(status_code=503, detail="No se pudo registrar la revisión. Consulta los logs del servidor.")

    @router.get("/reviews/{customer_id}")
    def list_reviews(customer_id: int, x_review_key: str | None = Header(default=None)):
        require_review_key(x_review_key)
        if customer_id <= 0:
            raise HTTPException(status_code=422, detail="Cliente inválido")
        query = text("""
            SELECT review_id, customer_id, score_output_id, model_version,
                   model_probability, model_prediction, review_status,
                   proposed_prediction, reviewer_id, evidence_type,
                   evidence_reference, review_note, created_at
            FROM gold.scoring_human_reviews
            WHERE customer_id = :customer_id
            ORDER BY created_at DESC, review_id DESC LIMIT 30
        """)
        try:
            with engine.connect() as conn:
                rows = conn.execute(query, {"customer_id": customer_id}).mappings().all()
            return {"results": [jsonable_encoder(dict(row)) for row in rows]}
        except Exception:
            logger.exception("Error leyendo revisiones")
            raise HTTPException(status_code=503, detail="No se pudo consultar el historial de revisiones")

    return router


class SupervisorDecision(BaseModel):
    review_id: int = Field(gt=0)
    decision: Literal["APROBADA", "RECHAZADA"]
    supervisor_id: str = Field(min_length=3, max_length=80)
    decision_reason: str = Field(min_length=20, max_length=1000)


def require_supervisor_key(value: str | None) -> None:
    configured = os.getenv("SUPERVISOR_API_KEY", "")
    if len(configured) < 24:
        raise HTTPException(status_code=503, detail="Modulo supervisor no habilitado")
    if not value or not hmac.compare_digest(value, configured):
        raise HTTPException(status_code=401, detail="No autorizado")


def register_supervisor_routes(engine):
    """Rutas adicionales: nunca alteran gold.score_output."""

    @router.get("/supervisor/reviews/pending")
    def pending_reviews(
        x_review_key: str | None = Header(default=None),
        x_supervisor_key: str | None = Header(default=None),
    ):
        require_review_key(x_review_key)
        require_supervisor_key(x_supervisor_key)
        query = text("""
            SELECT r.review_id, r.customer_id, r.score_output_id,
                   r.review_status, r.model_prediction,
                   r.proposed_prediction, r.reviewer_id,
                   r.evidence_type, r.evidence_reference,
                   r.review_note, r.created_at
            FROM gold.scoring_human_reviews r
            LEFT JOIN gold.scoring_review_decisions d
              ON d.review_id = r.review_id
            WHERE d.review_id IS NULL
            ORDER BY r.created_at ASC, r.review_id ASC
            LIMIT 100
        """)
        try:
            with engine.connect() as conn:
                rows = conn.execute(query).mappings().all()
            return {"results": [jsonable_encoder(dict(row)) for row in rows]}
        except Exception:
            logger.exception("Error consultando pendientes")
            raise HTTPException(status_code=503, detail="No se pudo consultar pendientes")

    @router.post("/supervisor/reviews/decision", status_code=201)
    def decide_review(
        payload: SupervisorDecision,
        x_review_key: str | None = Header(default=None),
        x_supervisor_key: str | None = Header(default=None),
    ):
        require_review_key(x_review_key)
        require_supervisor_key(x_supervisor_key)
        supervisor = payload.supervisor_id.strip()
        reason = payload.decision_reason.strip()
        if len(supervisor) < 3 or len(reason) < 20:
            raise HTTPException(status_code=422, detail="Supervisor o justificacion insuficiente")
        try:
            with engine.begin() as conn:
                review = conn.execute(text("""
                    SELECT reviewer_id, review_status, evidence_reference
                    FROM gold.scoring_human_reviews
                    WHERE review_id = :id FOR SHARE
                """), {"id": payload.review_id}).mappings().first()
                if review is None:
                    raise HTTPException(status_code=404, detail="Revision no encontrada")
                if supervisor.casefold() == review["reviewer_id"].strip().casefold():
                    raise HTTPException(status_code=422, detail="El supervisor debe ser diferente del analista")
                if payload.decision == "APROBADA" and review["review_status"] == "CORRECCION_PROPUESTA":
                    if not review["evidence_reference"] or len(review["evidence_reference"].strip()) < 3:
                        raise HTTPException(status_code=422, detail="Falta referencia de evidencia")
                row = conn.execute(text("""
                    INSERT INTO gold.scoring_review_decisions
                        (review_id, decision, supervisor_id, decision_reason)
                    VALUES (:id, :decision, :supervisor, :reason)
                    ON CONFLICT (review_id) DO NOTHING
                    RETURNING decision_id, review_id, decision, decided_at
                """), {
                    "id": payload.review_id, "decision": payload.decision,
                    "supervisor": supervisor, "reason": reason,
                }).mappings().first()
                if row is None:
                    raise HTTPException(status_code=409, detail="La revision ya fue decidida")
            return jsonable_encoder(dict(row))
        except HTTPException:
            raise
        except Exception:
            logger.exception("Error registrando decision")
            raise HTTPException(status_code=503, detail="No se pudo registrar la decision")

    return router
