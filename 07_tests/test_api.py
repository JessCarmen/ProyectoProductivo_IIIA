from fastapi.testclient import TestClient

from importlib import util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
API_PATH = ROOT / "05_api" / "main.py"
spec = util.spec_from_file_location("api_main_health_test", API_PATH)
api_main = util.module_from_spec(spec)
spec.loader.exec_module(api_main)


def test_health_endpoint(monkeypatch):
    metadata = {
        "model_version": "v20260929_064028",
        "algorithm": "XGBoost",
    }

    monkeypatch.setattr(api_main, "get_model_bundle", lambda: (object(), metadata))

    client = TestClient(api_main.app)
    response = client.get("/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["model_loaded"] is True
    assert payload["model_version"] == "v20260929_064028"
    assert payload["algorithm"] == "XGBoost"
