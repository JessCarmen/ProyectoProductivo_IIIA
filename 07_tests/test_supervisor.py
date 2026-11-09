import importlib
import os
import pytest
from fastapi import HTTPException
from pydantic import ValidationError

reviews = importlib.import_module("05_api.reviews")


def test_supervisor_key_fails_closed(monkeypatch):
    monkeypatch.delenv("SUPERVISOR_API_KEY", raising=False)
    with pytest.raises(HTTPException) as exc:
        reviews.require_supervisor_key("x" * 40)
    assert exc.value.status_code == 503


def test_supervisor_key_rejects_invalid(monkeypatch):
    monkeypatch.setenv("SUPERVISOR_API_KEY", "s" * 40)
    with pytest.raises(HTTPException) as exc:
        reviews.require_supervisor_key("bad")
    assert exc.value.status_code == 401


def test_supervisor_payload_validation():
    with pytest.raises(ValidationError):
        reviews.SupervisorDecision(
            review_id=0, decision="APROBADA", supervisor_id="S",
            decision_reason="corto",
        )
