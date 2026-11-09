import ast
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def test_new_scripts_compile():
    for name in ["v3_experiment_utils.py","19_prepare_v3_dataset.py",
                 "20_train_v3_candidate.py","21_compare_v2_v3.py"]:
        ast.parse((ROOT/"04_ml/scripts"/name).read_text(encoding="utf-8"))

def test_no_database_writes():
    for name in ["19_prepare_v3_dataset.py","20_train_v3_candidate.py","21_compare_v2_v3.py"]:
        source=(ROOT/"04_ml/scripts"/name).read_text(encoding="utf-8")
        assert "DELETE FROM" not in source
        assert "UPDATE gold." not in source
        assert "INSERT INTO gold." not in source

def test_original_model_not_targeted():
    source=(ROOT/"04_ml/scripts/20_train_v3_candidate.py").read_text(encoding="utf-8")
    assert 'joblib.dump(calibrated,EXPERIMENT/"model_candidate.pkl")' in source
