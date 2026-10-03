import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
API_PATH = ROOT / "05_api" / "main.py"
spec = importlib.util.spec_from_file_location("api_main", API_PATH)
api_main = importlib.util.module_from_spec(spec)
spec.loader.exec_module(api_main)


def test_risk_boundaries():
    assert api_main.risk_level(0.0) == "BAJO"
    assert api_main.risk_level(0.1999) == "BAJO"
    assert api_main.risk_level(0.20) == "MEDIO"
    assert api_main.risk_level(0.3999) == "MEDIO"
    assert api_main.risk_level(0.40) == "ALTO"
    assert api_main.risk_level(0.6999) == "ALTO"
    assert api_main.risk_level(0.70) == "CRITICO"
    assert api_main.risk_level(1.0) == "CRITICO"


def test_recommendation_is_nonempty():
    features = {"recent_delay_months": 3, "pay_max_delay": 3, "consecutive_delay_months": 2, "payment_bill_ratio_total": 0.2}
    rec = api_main.recommendation(features, "CRITICO")
    assert isinstance(rec, str)
    assert len(rec) > 20
