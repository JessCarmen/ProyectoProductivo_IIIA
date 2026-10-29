"""Pruebas unitarias de controles de revisión sin conexión a Supabase."""
import importlib.util
from pathlib import Path
import pytest
from fastapi import HTTPException

PATH = Path(__file__).resolve().parents[1] / "05_api/reviews.py"
spec = importlib.util.spec_from_file_location("review_module_test", PATH)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_review_requires_api_key(monkeypatch):
    monkeypatch.setenv("REVIEW_API_KEY", "test-key-long-enough-for-secure-demo-123")
    with pytest.raises(HTTPException) as exc:
        module.require_review_key("incorrecta")
    assert exc.value.status_code == 401
    module.require_review_key("test-key-long-enough-for-secure-demo-123")


def test_review_fails_closed_when_not_configured(monkeypatch):
    monkeypatch.delenv("REVIEW_API_KEY", raising=False)
    with pytest.raises(HTTPException) as exc:
        module.require_review_key("anything")
    assert exc.value.status_code == 503


def test_invalid_prediction_rejected():
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        module.ReviewRequest(
            customer_id=1, score_output_id=1, review_status="CORRECCION_PROPUESTA",
            proposed_prediction=3, reviewer_id="ANALISTA_1",
            evidence_type="HISTORIAL_PAGOS", evidence_reference="REF001",
            review_note="Justificación suficientemente larga para la revisión",
        )
