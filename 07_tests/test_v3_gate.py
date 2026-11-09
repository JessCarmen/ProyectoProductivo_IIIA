from pathlib import Path
import ast

ROOT=Path(__file__).resolve().parents[1]

def test_scripts_parse():
    for name in [
        "15_check_retraining_readiness.py",
        "16_review_decision_cli.py",
        "17_verified_outcome_cli.py",
        "18_retraining_gate.py",
    ]:
        source=(ROOT/"04_ml"/"scripts"/name).read_text(encoding="utf-8")
        ast.parse(source)

def test_gate_never_writes_model():
    source=(ROOT/"04_ml/scripts/18_retraining_gate.py").read_text(encoding="utf-8")
    assert "joblib.dump(" not in source
    assert "DELETE FROM" not in source
