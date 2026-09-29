import json
from pathlib import Path
from typing import Dict, Tuple

import numpy as np
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.metrics import (
    average_precision_score,
    brier_score_loss,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)

RANDOM_STATE = 42
TRAIN_FOLDS = 14
VALIDATION_FOLDS = 3
TEST_FOLDS = 3
N_SPLITS = TRAIN_FOLDS + VALIDATION_FOLDS + TEST_FOLDS

TARGET = "target_default"
GROUP_COLUMN = "source_parent_id"
ID_COLUMN = "id"
EXCLUDED_FEATURES = {
    "ml_record_id",
    ID_COLUMN,
    TARGET,
    GROUP_COLUMN,
    "fecha_carga",
    "bronze_id",
    "source_type",
    "record_origin",
    "raw_quality_flags",
    "payment_bill_ratio_avg",
    "payment_bill_ratio_max",
}


def build_preprocessor(X: pd.DataFrame):
    categorical = [c for c in ["sex", "education", "marriage"] if c in X.columns]
    numeric = [c for c in X.columns if c not in categorical]

    numeric_pipe = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
    ])
    categorical_pipe = Pipeline([
        ("imputer", SimpleImputer(strategy="most_frequent")),
        ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=True)),
    ])

    preprocessor = ColumnTransformer([
        ("num", numeric_pipe, numeric),
        ("cat", categorical_pipe, categorical),
    ])
    return preprocessor, numeric, categorical


def group_split(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    required = {GROUP_COLUMN, TARGET, ID_COLUMN}
    missing = required - set(df.columns)
    if missing:
        raise RuntimeError(f"Faltan columnas para split por grupo: {sorted(missing)}")

    if df[GROUP_COLUMN].isna().any():
        raise RuntimeError("source_parent_id contiene nulos; no se puede garantizar la integridad del split.")
    if df[ID_COLUMN].duplicated().any():
        raise RuntimeError("id contiene duplicados; no se puede construir un manifiesto de split seguro.")

    splitter = StratifiedGroupKFold(
        n_splits=N_SPLITS,
        shuffle=True,
        random_state=RANDOM_STATE,
    )

    fold_by_id: Dict[int, int] = {}
    X_dummy = df.drop(columns=[TARGET])
    y = df[TARGET].astype(int)
    groups = df[GROUP_COLUMN].astype(str)

    # Assign one fold per row. StratifiedGroupKFold guarantees that a group is only present in one fold.
    for fold_id, (_, test_idx) in enumerate(splitter.split(X_dummy, y, groups)):
        for idx in test_idx:
            fold_by_id[int(df.iloc[idx][ID_COLUMN])] = fold_id

    if len(fold_by_id) != len(df):
        raise RuntimeError("No se pudo asignar una partición a todos los registros.")

    manifest = pd.DataFrame({
        "id": df[ID_COLUMN].astype(int),
        "source_parent_id": df[GROUP_COLUMN].astype(str),
        "fold": df[ID_COLUMN].map(fold_by_id).astype(int),
    })
    manifest["split"] = np.select(
        [
            manifest["fold"] < TRAIN_FOLDS,
            manifest["fold"] < TRAIN_FOLDS + VALIDATION_FOLDS,
        ],
        ["train", "validation"],
        default="test",
    )

    train_ids = set(manifest.loc[manifest["split"] == "train", "id"])
    val_ids = set(manifest.loc[manifest["split"] == "validation", "id"])
    test_ids = set(manifest.loc[manifest["split"] == "test", "id"])

    train = df[df[ID_COLUMN].isin(train_ids)].copy()
    validation = df[df[ID_COLUMN].isin(val_ids)].copy()
    test = df[df[ID_COLUMN].isin(test_ids)].copy()
    return train, validation, test, manifest


def build_calibrated(estimator):
    # Calibrate using internal CV when final model is retrained.
    return CalibratedClassifierCV(
        estimator=estimator,
        method="sigmoid",
        cv=5,
        n_jobs=-1,
    )


def metrics_from_probabilities(y_true, probability, threshold=0.50):
    prediction = (probability >= threshold).astype(int)
    return {
        "accuracy": float((prediction == y_true).mean()),
        "precision_default": float(precision_score(y_true, prediction, zero_division=0)),
        "recall_default": float(recall_score(y_true, prediction, zero_division=0)),
        "f1_default": float(f1_score(y_true, prediction, zero_division=0)),
        "roc_auc": float(roc_auc_score(y_true, probability)),
        "pr_auc": float(average_precision_score(y_true, probability)),
        "brier_score": float(brier_score_loss(y_true, probability)),
    }


def find_threshold(y_true, probability):
    thresholds = np.linspace(0.10, 0.90, 161)
    best = None
    for threshold in thresholds:
        m = metrics_from_probabilities(y_true, probability, threshold)
        # Primary: F1; tie-breaker: Recall; finally prefer lower threshold only if all equal.
        key = (m["f1_default"], m["recall_default"], -abs(threshold - 0.50))
        if best is None or key > best[0]:
            best = (key, threshold, m)
    return float(best[1]), best[2]


def json_dump(path: Path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
