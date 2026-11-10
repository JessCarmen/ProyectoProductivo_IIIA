import json
import sys
import pathlib
import time

import numpy as np
import pandas as pd
import joblib

from xgboost import XGBClassifier
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import confusion_matrix

# ============================================================
# RUTAS WINDOWS
# ============================================================

SCRIPT_DIR = pathlib.Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parents[2]

sys.path.insert(0, str(ROOT / "04_ml" / "scripts"))

from modeling_utils import (
    build_preprocessor,
    metrics_from_probabilities,
    find_threshold,
)

# ============================================================
# CARGAR DATOS
# ============================================================

meta = json.loads(
    (ROOT / "04_ml" / "models" / "model_metadata.json").read_text(
        encoding="utf-8"
    )
)

features = meta["features"]

gold_path = SCRIPT_DIR.parent / "gold_ml_rows.csv"

gold = pd.read_csv(gold_path)

manifest = pd.read_csv(
    ROOT / "04_ml" / "models" / "split_manifest.csv",
    dtype={"source_parent_id": str},
)

assert len(gold) == len(manifest) == 33377
assert gold.id.is_unique
assert manifest.id.is_unique

frame = gold.merge(
    manifest[["id", "source_parent_id", "split"]],
    on="id",
    suffixes=("", "_manifest"),
    validate="one_to_one",
)

assert (
    frame.source_parent_id.astype(str)
    == frame.source_parent_id_manifest.astype(str)
).all()

assert set(features).issubset(frame.columns)

assert frame.groupby("source_parent_id")["split"].nunique().max() == 1

train = frame[frame.split == "train"]
val = frame[frame.split == "validation"]
test = frame[frame.split == "test"]

print("SPLITS:", len(train), len(val), len(test), flush=True)

# ============================================================
# ENTRENAR XGBOOST V3
# ============================================================

pre, _, _ = build_preprocessor(train[features])

weight = (
    (train.target_default == 0).sum()
    / (train.target_default == 1).sum()
)

model = Pipeline([
    ("preprocessor", pre),
    (
        "model",
        XGBClassifier(
            n_estimators=240,
            max_depth=4,
            learning_rate=0.04,
            subsample=0.85,
            colsample_bytree=0.85,
            min_child_weight=4,
            reg_lambda=4,
            objective="binary:logistic",
            eval_metric="logloss",
            random_state=42,
            n_jobs=2,
            tree_method="hist",
            scale_pos_weight=weight,
        ),
    ),
])

print("Entrenando XGBoost V3...", flush=True)

start = time.time()

model.fit(
    train[features],
    train.target_default.astype(int),
)

print(
    "TRAIN_SECONDS:",
    round(time.time() - start, 1),
    flush=True,
)

# ============================================================
# CALIBRACION Y UMBRAL
# ============================================================

pval_raw = model.predict_proba(val[features])[:, 1]

cal = LogisticRegression(random_state=42).fit(
    pval_raw.reshape(-1, 1),
    val.target_default.astype(int),
)

pval = cal.predict_proba(
    pval_raw.reshape(-1, 1)
)[:, 1]

threshold, validation_metrics = find_threshold(
    val.target_default.astype(int).to_numpy(),
    pval,
)

# ============================================================
# EVALUACION TEST
# ============================================================

ptest = cal.predict_proba(
    model.predict_proba(test[features])[:, 1].reshape(-1, 1)
)[:, 1]

old = pd.read_csv(
    ROOT / "04_ml" / "models" / "test_predictions.csv"
)

new = pd.DataFrame({
    "id": test.id.to_numpy(),
    "target": test.target_default.astype(int).to_numpy(),
    "probability": ptest,
})

both = old[["id", "target", "probability"]].merge(
    new,
    on="id",
    suffixes=("_v2", "_v3"),
    validate="one_to_one",
)

assert len(both) == 5005
assert (both.target_v2 == both.target_v3).all()

y = both.target_v2.to_numpy()

old_thr = float(meta["risk_threshold"])

m2 = metrics_from_probabilities(
    y,
    both.probability_v2.to_numpy(),
    old_thr,
)

m3 = metrics_from_probabilities(
    y,
    both.probability_v3.to_numpy(),
    threshold,
)

cm2 = confusion_matrix(
    y,
    both.probability_v2.to_numpy() >= old_thr,
).tolist()

cm3 = confusion_matrix(
    y,
    both.probability_v3.to_numpy() >= threshold,
).tolist()

# ============================================================
# GUARDAR RESULTADOS
# ============================================================

out = SCRIPT_DIR
out.mkdir(parents=True, exist_ok=True)

report = {
    "experiment": "V3 historical retraining without changing labels",
    "training_uses_human_approvals": False,
    "reason": (
        "Five supervisor approvals are observations, "
        "not verified outcomes or corrected input variables"
    ),
    "source": "exported gold_ml_rows.csv and original split_manifest.csv",
    "train_rows": len(train),
    "validation_rows": len(val),
    "test_rows": len(test),
    "features": len(features),
    "validation_selected_threshold_v3": threshold,
    "v2_threshold": old_thr,
    "v2_test": m2,
    "v3_test": m3,
    "v2_confusion": cm2,
    "v3_confusion": cm3,
    "promotion": "NOT_APPROVED",
    "caution": (
        "Historical test reused for comparison; "
        "further independent evaluation required before deployment."
    ),
}

(out / "comparacion_v2_v3.json").write_text(
    json.dumps(report, indent=2, ensure_ascii=False),
    encoding="utf-8",
)

joblib.dump(
    {
        "pipeline": model,
        "calibrator": cal,
        "threshold": threshold,
        "features": features,
    },
    out / "v3_candidate.joblib",
)

both.to_csv(
    out / "predicciones_test_comparadas.csv",
    index=False,
)

print(
    json.dumps(report, indent=2, ensure_ascii=False),
    flush=True,
)

print("EXPERIMENTO V3 FINALIZADO", flush=True)
