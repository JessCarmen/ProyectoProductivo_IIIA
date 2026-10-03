import json
import os
from datetime import datetime, timezone
from pathlib import Path

import joblib
import pandas as pd
import psycopg
from dotenv import load_dotenv
from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import Pipeline
from sklearn.base import clone

from modeling_utils import (
    EXCLUDED_FEATURES,
    GROUP_COLUMN,
    ID_COLUMN,
    TARGET,
    RANDOM_STATE,
    build_calibrated,
    build_preprocessor,
    find_threshold,
    group_split,
    json_dump,
    metrics_from_probabilities,
)

try:
    from xgboost import XGBClassifier
except ImportError as exc:
    raise RuntimeError("XGBoost no esta instalado. Ejecuta: pip install xgboost") from exc

load_dotenv()

ROOT = Path(__file__).resolve().parents[2]
MODELS_DIR = ROOT / "04_ml" / "models"
MODEL_PATH = MODELS_DIR / "model.pkl"
METADATA_PATH = MODELS_DIR / "model_metadata.json"
COMPARISON_PATH = MODELS_DIR / "model_comparison.json"
MANIFEST_PATH = MODELS_DIR / "split_manifest.csv"


def get_connection():
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("No se encontro DATABASE_URL en .env")
    return psycopg.connect(database_url)


def load_gold_ml():
    query = "SELECT * FROM gold.gold_ml ORDER BY id;"
    with get_connection() as conn:
        return pd.read_sql_query(query, conn)


def build_candidate_pipelines(X, y_train):
    scale_pos_weight = (y_train == 0).sum() / max((y_train == 1).sum(), 1)
    candidates = {}

    pre, _, _ = build_preprocessor(X)
    candidates["Random Forest"] = Pipeline([
        ("preprocessor", pre),
        ("model", RandomForestClassifier(
            n_estimators=400,
            random_state=RANDOM_STATE,
            n_jobs=-1,
            class_weight="balanced",
            min_samples_leaf=2,
        )),
    ])

    pre_xgb, _, _ = build_preprocessor(X)
    candidates["XGBoost"] = Pipeline([
        ("preprocessor", pre_xgb),
        ("model", XGBClassifier(
            n_estimators=400,
            max_depth=5,
            learning_rate=0.05,
            subsample=0.85,
            colsample_bytree=0.85,
            min_child_weight=2,
            reg_lambda=1.0,
            objective="binary:logistic",
            eval_metric="logloss",
            random_state=RANDOM_STATE,
            n_jobs=-1,
            tree_method="hist",
            scale_pos_weight=float(scale_pos_weight),
        )),
    ])
    return candidates


def main():
    print("=" * 72)
    print("ENTRENAMIENTO V2 - SPLIT POR CLIENTE / SOURCE_PARENT_ID")
    print("=" * 72)

    df = load_gold_ml()
    if TARGET not in df.columns:
        raise RuntimeError(f"No existe la variable objetivo: {TARGET}")

    train, validation, test, manifest = group_split(df)
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    manifest.to_csv(MANIFEST_PATH, index=False)

    X_columns = [c for c in df.columns if c not in EXCLUDED_FEATURES]
    X_train, y_train = train[X_columns], train[TARGET].astype(int)
    X_val, y_val = validation[X_columns], validation[TARGET].astype(int)
    X_test, y_test = test[X_columns], test[TARGET].astype(int)

    candidates = build_candidate_pipelines(X_train, y_train)
    results = []
    fitted = {}

    for name, pipeline in candidates.items():
        print(f"\nEvaluando {name} sobre VALIDATION...")
        calibrated = build_calibrated(clone(pipeline))
        calibrated.fit(X_train, y_train)
        probability = calibrated.predict_proba(X_val)[:, 1]
        threshold, threshold_metrics = find_threshold(y_val, probability)
        row = {
            "model": name,
            "validation_threshold": threshold,
            **threshold_metrics,
        }
        results.append(row)
        fitted[name] = calibrated
        print(
            f"PR-AUC={row['pr_auc']:.4f} | ROC-AUC={row['roc_auc']:.4f} | "
            f"Recall={row['recall_default']:.4f} | F1={row['f1_default']:.4f} | "
            f"Brier={row['brier_score']:.4f} | threshold={threshold:.3f}"
        )

    # Primary selection: ROC-AUC, then PR-AUC, then F1.
    selected = max(results, key=lambda r: (r["roc_auc"], r["pr_auc"], r["f1_default"]))
    selected_name = selected["model"]
    selected_threshold = selected["validation_threshold"]

    # Retrain the selected pipeline on TRAIN + VALIDATION and calibrate with internal CV.
    combined = pd.concat([train, validation], ignore_index=True)
    X_combined = combined[X_columns]
    y_combined = combined[TARGET].astype(int)
    selected_base = candidates[selected_name]
    final_model = build_calibrated(clone(selected_base))
    print(f"\nReentrenando modelo final: {selected_name}")
    final_model.fit(X_combined, y_combined)

    # Report a clean final holdout result using the selected validation threshold.
    test_probability = final_model.predict_proba(X_test)[:, 1]
    final_metrics = metrics_from_probabilities(y_test, test_probability, selected_threshold)

    version = datetime.now(timezone.utc).strftime("v%Y%m%d_%H%M%S")
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(final_model, MODEL_PATH)

    comparison_payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "selection_stage": "validation",
        "selection_criterion": ["roc_auc", "pr_auc", "f1_default"],
        "results": results,
        "selected_model": selected_name,
        "selected_threshold": selected_threshold,
    }
    json_dump(COMPARISON_PATH, comparison_payload)

    metadata = {
        "model_version": version,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_table": "gold.gold_ml",
        "target": TARGET,
        "group_column": GROUP_COLUMN,
        "algorithm": selected_name,
        "random_state": RANDOM_STATE,
        "split_strategy": "StratifiedGroupKFold by source_parent_id (14/3/3 of 20 folds)",
        "calibration": {"method": "sigmoid", "cv": 5},
        "train_records": int(len(train)),
        "validation_records": int(len(validation)),
        "test_records": int(len(test)),
        "train_target_rate": float(y_train.mean()),
        "validation_target_rate": float(y_val.mean()),
        "test_target_rate": float(y_test.mean()),
        "n_features": int(len(X_columns)),
        "features": list(X_columns),
        "excluded_features": sorted(EXCLUDED_FEATURES),
        "risk_threshold": selected_threshold,
        "selection_metrics_validation": selected,
        "final_test_metrics": final_metrics,
        "artifact": "04_ml/models/model.pkl",
        "manifest": "04_ml/models/split_manifest.csv",
    }
    json_dump(METADATA_PATH, metadata)
    json_dump(MODELS_DIR / "evaluation_metrics.json", {**final_metrics, "test_records": int(len(y_test)), "risk_threshold": selected_threshold})

    # Persist test predictions for audit; not a training input.
    pd.DataFrame({
        "id": test[ID_COLUMN].astype(int),
        "source_parent_id": test[GROUP_COLUMN].astype(str),
        "target": y_test.to_numpy(),
        "probability": test_probability,
        "prediction": (test_probability >= selected_threshold).astype(int),
    }).to_csv(MODELS_DIR / "test_predictions.csv", index=False)

    print("\nModelo final guardado en:", MODEL_PATH)
    print("Version:", version)
    print("Umbral seleccionado:", f"{selected_threshold:.3f}")
    print("Test final:", final_metrics)
    print("Manifest:", MANIFEST_PATH)
    print("ENTRENAMIENTO V2 FINALIZADO")


if __name__ == "__main__":
    main()
