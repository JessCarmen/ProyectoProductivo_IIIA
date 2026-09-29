import json
import os
from pathlib import Path

import joblib
import pandas as pd
import psycopg
from dotenv import load_dotenv
from sklearn.metrics import classification_report, confusion_matrix

from modeling_utils import EXCLUDED_FEATURES, GROUP_COLUMN, ID_COLUMN, TARGET, metrics_from_probabilities

load_dotenv()
ROOT = Path(__file__).resolve().parents[2]
MODEL_PATH = ROOT / "04_ml/models/model.pkl"
METADATA_PATH = ROOT / "04_ml/models/model_metadata.json"
MANIFEST_PATH = ROOT / "04_ml/models/split_manifest.csv"
OUTPUT_PATH = ROOT / "04_ml/models/evaluation_metrics.json"


def get_connection():
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("No se encontro DATABASE_URL en .env")
    return psycopg.connect(database_url)


def load_gold_ml():
    with get_connection() as conn:
        return pd.read_sql_query("SELECT * FROM gold.gold_ml ORDER BY id;", conn)


def main():
    print("=" * 72)
    print("EVALUACION V2 - TEST RESERVADO")
    print("=" * 72)

    for path in [MODEL_PATH, METADATA_PATH, MANIFEST_PATH]:
        if not path.exists():
            raise FileNotFoundError(f"No existe {path}. Ejecuta 04_train.py primero.")

    model = joblib.load(MODEL_PATH)
    metadata = json.loads(METADATA_PATH.read_text(encoding="utf-8"))
    manifest = pd.read_csv(MANIFEST_PATH)
    df = load_gold_ml()

    if manifest["source_parent_id"].duplicated().any():
        # A parent may have many records, so this is expected. We validate split purity below.
        pass

    id_to_split = manifest.set_index("id")["split"].to_dict()
    split_series = df[ID_COLUMN].map(id_to_split)
    if split_series.isna().any():
        raise RuntimeError("Hay IDs en gold_ml sin particion asignada.")

    test = df[split_series == "test"].copy()
    train_groups = set(manifest.loc[manifest["split"] == "train", "source_parent_id"].astype(str))
    val_groups = set(manifest.loc[manifest["split"] == "validation", "source_parent_id"].astype(str))
    test_groups = set(manifest.loc[manifest["split"] == "test", "source_parent_id"].astype(str))

    if train_groups & val_groups or train_groups & test_groups or val_groups & test_groups:
        raise RuntimeError("Se detectaron source_parent_id compartidos entre particiones.")

    features = metadata["features"]
    missing = [c for c in features + [TARGET] if c not in test.columns]
    if missing:
        raise RuntimeError(f"Faltan columnas en gold.gold_ml: {missing}")

    X_test = test[features]
    y_test = test[TARGET].astype(int).to_numpy()
    probability = model.predict_proba(X_test)[:, 1]
    threshold = float(metadata["risk_threshold"])
    metrics = metrics_from_probabilities(y_test, probability, threshold)

    print(f"Test records: {len(test):,}")
    print(f"Threshold: {threshold:.4f}")
    for key, value in metrics.items():
        print(f"{key}: {value:.4f}")
    prediction = (probability >= threshold).astype(int)
    print("\nMatriz de confusion:")
    print(confusion_matrix(y_test, prediction))
    print("\nClassification report:")
    print(classification_report(y_test, prediction, target_names=["No default", "Default"], digits=4, zero_division=0))

    payload = {
        **metrics,
        "test_records": int(len(test)),
        "risk_threshold": threshold,
        "model_version": metadata.get("model_version"),
        "validation_selection": metadata.get("selection_metrics_validation"),
        "test_group_purity": True,
    }
    OUTPUT_PATH.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print("\nEvaluacion guardada en:", OUTPUT_PATH)
    print("EVALUACION V2 FINALIZADA")


if __name__ == "__main__":
    main()
