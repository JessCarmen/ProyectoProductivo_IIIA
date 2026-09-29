import json
import os
from pathlib import Path

import joblib
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sklearn.metrics import classification_report, confusion_matrix

from modeling_utils import (
    EXCLUDED_FEATURES,
    GROUP_COLUMN,
    ID_COLUMN,
    TARGET,
    metrics_from_probabilities,
)


# ============================================================
# CONFIGURACION
# ============================================================

load_dotenv()

ROOT = Path(__file__).resolve().parents[2]

MODEL_PATH = ROOT / "04_ml/models/model.pkl"
METADATA_PATH = ROOT / "04_ml/models/model_metadata.json"
MANIFEST_PATH = ROOT / "04_ml/models/split_manifest.csv"
OUTPUT_PATH = ROOT / "04_ml/models/evaluation_metrics.json"


# ============================================================
# CONEXION A SUPABASE
# ============================================================

def get_engine():
    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        raise RuntimeError("No se encontro DATABASE_URL en .env")

    return create_engine(
        database_url,
        pool_pre_ping=True,
    )


# ============================================================
# CARGA DE GOLD_ML
# ============================================================

def load_gold_ml():
    engine = get_engine()

    query = """
        SELECT *
        FROM gold.gold_ml
        ORDER BY id;
    """

    try:
        return pd.read_sql_query(query, engine)
    finally:
        engine.dispose()


# ============================================================
# PROCESO PRINCIPAL
# ============================================================

def main():
    print("=" * 72)
    print("EVALUACION V2 - TEST RESERVADO")
    print("=" * 72)

    # --------------------------------------------------------
    # Verificar archivos necesarios
    # --------------------------------------------------------

    for path in [MODEL_PATH, METADATA_PATH, MANIFEST_PATH]:
        if not path.exists():
            raise FileNotFoundError(
                f"No existe {path}. Ejecuta 04_train.py primero."
            )

    # --------------------------------------------------------
    # Cargar modelo, metadata y manifest
    # --------------------------------------------------------

    print("\n[1/6] Cargando modelo y archivos de control...")

    model = joblib.load(MODEL_PATH)

    metadata = json.loads(
        METADATA_PATH.read_text(encoding="utf-8")
    )

    manifest = pd.read_csv(MANIFEST_PATH)

    # --------------------------------------------------------
    # Cargar GOLD_ML
    # --------------------------------------------------------

    print("[2/6] Cargando GOLD_ML desde Supabase...")

    df = load_gold_ml()

    print(f"Registros GOLD_ML: {len(df):,}")

    # --------------------------------------------------------
    # Validar columnas necesarias
    # --------------------------------------------------------

    features = metadata["features"]

    missing = [
        column
        for column in features + [TARGET, ID_COLUMN, GROUP_COLUMN]
        if column not in df.columns
    ]

    if missing:
        raise RuntimeError(
            f"Faltan columnas en gold.gold_ml: {missing}"
        )

    # --------------------------------------------------------
    # Validar manifest
    # --------------------------------------------------------

    print("[3/6] Validando manifest y particiones...")

    required_manifest_columns = [
        ID_COLUMN,
        GROUP_COLUMN,
        "split",
    ]

    missing_manifest = [
        column
        for column in required_manifest_columns
        if column not in manifest.columns
    ]

    if missing_manifest:
        raise RuntimeError(
            f"Faltan columnas en split_manifest.csv: {missing_manifest}"
        )

    # La duplicidad de source_parent_id es esperada cuando
    # un mismo origen tiene varios registros derivados.
    # Lo importante es que no aparezca en más de un split.

    id_to_split = (
        manifest
        .set_index(ID_COLUMN)["split"]
        .to_dict()
    )

    split_series = df[ID_COLUMN].map(id_to_split)

    if split_series.isna().any():
        missing_ids = df.loc[
            split_series.isna(),
            ID_COLUMN
        ].tolist()[:10]

        raise RuntimeError(
            "Hay IDs en gold.gold_ml sin particion asignada. "
            f"Ejemplos: {missing_ids}"
        )

    # --------------------------------------------------------
    # Validar pureza de grupos
    # --------------------------------------------------------

    train_groups = set(
        manifest.loc[
            manifest["split"] == "train",
            GROUP_COLUMN
        ].astype(str)
    )

    validation_groups = set(
        manifest.loc[
            manifest["split"] == "validation",
            GROUP_COLUMN
        ].astype(str)
    )

    test_groups = set(
        manifest.loc[
            manifest["split"] == "test",
            GROUP_COLUMN
        ].astype(str)
    )

    overlap_train_validation = train_groups & validation_groups
    overlap_train_test = train_groups & test_groups
    overlap_validation_test = validation_groups & test_groups

    if (
        overlap_train_validation
        or overlap_train_test
        or overlap_validation_test
    ):
        raise RuntimeError(
            "Se detectaron source_parent_id compartidos entre particiones."
        )

    print("OK - grupos sin interseccion entre particiones.")

    # --------------------------------------------------------
    # Extraer TEST reservado
    # --------------------------------------------------------

    print("[4/6] Extrayendo TEST reservado...")

    test = df[split_series == "test"].copy()

    if test.empty:
        raise RuntimeError(
            "El conjunto TEST esta vacio."
        )

    print(f"Registros TEST: {len(test):,}")

    # --------------------------------------------------------
    # Preparar X / y
    # --------------------------------------------------------

    X_test = test[features]

    y_test = (
        test[TARGET]
        .astype(int)
        .to_numpy()
    )

    # --------------------------------------------------------
    # Obtener probabilidades
    # --------------------------------------------------------

    print("[5/6] Generando probabilidades de incumplimiento...")

    probability = model.predict_proba(X_test)[:, 1]

    threshold = float(
        metadata["risk_threshold"]
    )

    # --------------------------------------------------------
    # Calcular métricas
    # --------------------------------------------------------

    metrics = metrics_from_probabilities(
        y_test,
        probability,
        threshold,
    )

    prediction = (
        probability >= threshold
    ).astype(int)

    # --------------------------------------------------------
    # Resultados
    # --------------------------------------------------------

    print("\n" + "=" * 72)
    print("RESULTADOS TEST")
    print("=" * 72)

    print(f"Test records: {len(test):,}")
    print(f"Threshold: {threshold:.4f}")

    for key, value in metrics.items():
        print(f"{key}: {value:.4f}")

    print("\nMatriz de confusion:")
    print(
        confusion_matrix(
            y_test,
            prediction
        )
    )

    print("\nClassification report:")
    print(
        classification_report(
            y_test,
            prediction,
            target_names=[
                "No default",
                "Default",
            ],
            digits=4,
            zero_division=0,
        )
    )

    # --------------------------------------------------------
    # Guardar resultados
    # --------------------------------------------------------

    payload = {
        **metrics,
        "test_records": int(len(test)),
        "risk_threshold": threshold,
        "model_version": metadata.get(
            "model_version"
        ),
        "validation_selection": metadata.get(
            "selection_metrics_validation"
        ),
        "test_group_purity": True,
    }

    OUTPUT_PATH.write_text(
        json.dumps(
            payload,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    print("\n" + "=" * 72)
    print("EVALUACION V2 FINALIZADA")
    print("=" * 72)

    print(
        f"Resultados guardados en: {OUTPUT_PATH}"
    )


if __name__ == "__main__":
    main()