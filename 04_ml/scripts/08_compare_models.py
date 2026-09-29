import json
import os
from pathlib import Path

import pandas as pd
import psycopg
from dotenv import load_dotenv
from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import Pipeline
from sklearn.base import clone

from modeling_utils import EXCLUDED_FEATURES, RANDOM_STATE, TARGET, build_calibrated, build_preprocessor, find_threshold, group_split

try:
    from xgboost import XGBClassifier
except ImportError as exc:
    raise RuntimeError("XGBoost no esta instalado. Ejecuta: pip install xgboost") from exc

load_dotenv()
ROOT = Path(__file__).resolve().parents[2]
OUTPUT_PATH = ROOT / "04_ml/models/model_comparison.json"


def get_connection():
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("No se encontro DATABASE_URL en .env")
    return psycopg.connect(database_url)


def load_gold_ml():
    with get_connection() as conn:
        return pd.read_sql_query("SELECT * FROM gold.gold_ml ORDER BY id;", conn)


def main():
    df = load_gold_ml()
    train, validation, _, manifest = group_split(df)
    X_cols = [c for c in df.columns if c not in EXCLUDED_FEATURES]
    X_train, y_train = train[X_cols], train[TARGET].astype(int)
    X_val, y_val = validation[X_cols], validation[TARGET].astype(int)

    pre, _, _ = build_preprocessor(X_train)
    rf = Pipeline([
        ("preprocessor", pre),
        ("model", RandomForestClassifier(n_estimators=400, random_state=RANDOM_STATE, n_jobs=-1, class_weight="balanced", min_samples_leaf=2)),
    ])
    pre_xgb, _, _ = build_preprocessor(X_train)
    scale_pos_weight = (y_train == 0).sum() / max((y_train == 1).sum(), 1)
    xgb = Pipeline([
        ("preprocessor", pre_xgb),
        ("model", XGBClassifier(n_estimators=400, max_depth=5, learning_rate=0.05, subsample=0.85, colsample_bytree=0.85, min_child_weight=2, reg_lambda=1.0, objective="binary:logistic", eval_metric="logloss", random_state=RANDOM_STATE, n_jobs=-1, tree_method="hist", scale_pos_weight=float(scale_pos_weight))),
    ])

    results = []
    for name, model in [("Random Forest", rf), ("XGBoost", xgb)]:
        calibrated = build_calibrated(clone(model))
        calibrated.fit(X_train, y_train)
        prob = calibrated.predict_proba(X_val)[:, 1]
        threshold, metrics = find_threshold(y_val, prob)
        results.append({"model": name, "validation_threshold": threshold, **metrics})

    selected = max(results, key=lambda r: (r["roc_auc"], r["pr_auc"], r["f1_default"]))
    payload = {
        "selection_stage": "validation",
        "selection_criterion": ["roc_auc", "pr_auc", "f1_default"],
        "calibration": {"method": "sigmoid", "cv": 5},
        "results": results,
        "selected_model": selected["model"],
        "selected_threshold": selected["validation_threshold"],
    }
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(payload, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
