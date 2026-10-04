import os
from importlib import util
from pathlib import Path

from fastapi.testclient import TestClient


ROOT = Path(__file__).resolve().parents[1]
API_PATH = ROOT / "05_api" / "main.py"


# ------------------------------------------------------------
# La API necesita DATABASE_URL al importarse.
# Para este test unitario usamos temporalmente una URL dummy,
# pero NO la dejamos en os.environ después del import.
# ------------------------------------------------------------

_previous_database_url = os.environ.get("DATABASE_URL")

os.environ["DATABASE_URL"] = (
    "postgresql+psycopg://user:password@localhost:5432/testdb"
)

spec = util.spec_from_file_location(
    "api_main_health_test",
    API_PATH,
)

api_main = util.module_from_spec(spec)
spec.loader.exec_module(api_main)

# Restaurar el entorno inmediatamente.
if _previous_database_url is None:
    os.environ.pop("DATABASE_URL", None)
else:
    os.environ["DATABASE_URL"] = _previous_database_url


class FakeConnection:
    def execute(self, *_args, **_kwargs):
        return None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class FakeEngine:
    def connect(self):
        return FakeConnection()


def test_health_endpoint(monkeypatch):

    monkeypatch.setattr(
        api_main,
        "engine",
        FakeEngine(),
    )

    client = TestClient(api_main.app)

    response = client.get("/health")

    assert response.status_code == 200

    payload = response.json()

    assert payload["status"] == "ok"
    assert payload["database"] == "connected"
    assert payload["mode"] == "portfolio_scoring"
    assert (
        payload["model_version"]
        == "v20260929_064028"
    )
