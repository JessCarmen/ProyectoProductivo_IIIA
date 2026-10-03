import json
from pathlib import Path

import joblib

ROOT = Path(__file__).resolve().parents[1]


def test_model_and_metadata_load():
    model_path = ROOT / "04_ml" / "models" / "model.pkl"
    metadata_path = ROOT / "04_ml" / "models" / "model_metadata.json"
    assert model_path.exists()
    assert metadata_path.exists()
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    assert metadata["algorithm"] == "XGBoost"
    assert len(metadata["features"]) == 47
    assert float(metadata["risk_threshold"]) == 0.38
    assert joblib.load(model_path) is not None
