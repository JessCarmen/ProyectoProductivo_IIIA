import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

RECOMMENDATION_PATH = (
    ROOT
    / "04_ml"
    / "scripts"
    / "07_recommendation.py"
)


spec = importlib.util.spec_from_file_location(
    "recommendation_module",
    RECOMMENDATION_PATH,
)

recommendation_module = (
    importlib.util.module_from_spec(spec)
)

spec.loader.exec_module(
    recommendation_module
)


def test_risk_boundaries():

    classify_risk = (
        recommendation_module.classify_risk
    )

    assert classify_risk(0.0) == "BAJO"
    assert classify_risk(0.1999) == "BAJO"

    assert classify_risk(0.20) == "MEDIO"
    assert classify_risk(0.3999) == "MEDIO"

    assert classify_risk(0.40) == "ALTO"
    assert classify_risk(0.6999) == "ALTO"

    assert classify_risk(0.70) == "CRITICO"
    assert classify_risk(1.0) == "CRITICO"


def test_recommendation_is_nonempty():

    features = {
        "recent_delay_months": 3,
        "pay_max_delay": 3,
        "consecutive_delay_months": 2,
        "payment_bill_ratio_total": 0.2,
    }

    recommendations = (
        recommendation_module
        .build_recommendations(
            features,
            probability=0.80,
        )
    )

    assert isinstance(
        recommendations,
        list,
    )

    assert len(recommendations) > 0

    assert all(
        isinstance(item, str)
        and len(item.strip()) > 10
        for item in recommendations
    )
