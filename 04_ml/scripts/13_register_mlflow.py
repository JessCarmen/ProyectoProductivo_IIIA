import json
from pathlib import Path

import mlflow
from dotenv import load_dotenv


# ============================================================
# CONFIGURACION
# ============================================================

load_dotenv()

ROOT = Path(__file__).resolve().parents[2]

MODEL_DIR = ROOT / "04_ml" / "models"
MODEL_PATH = MODEL_DIR / "model.pkl"
METADATA_PATH = MODEL_DIR / "model_metadata.json"
EVALUATION_PATH = MODEL_DIR / "evaluation_metrics.json"
COMPARISON_PATH = MODEL_DIR / "model_comparison.json"
MANIFEST_PATH = MODEL_DIR / "split_manifest.csv"

# MLflow moderno: usar backend SQLite en vez del antiguo FileStore.
MLFLOW_DB_PATH = ROOT / "mlflow.db"
MLFLOW_TRACKING_URI = f"sqlite:///{MLFLOW_DB_PATH.as_posix()}"

EXPERIMENT_NAME = "credit-risk-v2"


# ============================================================
# UTILIDADES
# ============================================================

def load_json(path: Path, required: bool = True):
    if not path.exists():
        if required:
            raise FileNotFoundError(f"No existe el archivo requerido: {path}")
        return {}

    return json.loads(path.read_text(encoding="utf-8"))


def numeric_metrics(data: dict) -> dict:
    """Devuelve solo metricas numericas compatibles con mlflow.log_metrics()."""
    metrics = {}

    for key, value in data.items():
        if isinstance(value, bool):
            continue

        if isinstance(value, (int, float)):
            metrics[key] = float(value)

    return metrics


def safe_log_artifact(path: Path):
    if path.exists():
        mlflow.log_artifact(str(path))


# ============================================================
# MAIN
# ============================================================

def main():
    print("=" * 72)
    print("REGISTRO DE MODELO EN MLFLOW")
    print("=" * 72)

    # --------------------------------------------------------
    # 1. Validar artefactos principales
    # --------------------------------------------------------

    for required_path in [MODEL_PATH, METADATA_PATH]:
        if not required_path.exists():
            raise FileNotFoundError(
                f"No existe {required_path}. "
                "Verifica que el modelo V2 y su metadata esten disponibles."
            )

    metadata = load_json(METADATA_PATH)
    evaluation = load_json(EVALUATION_PATH, required=False)

    # --------------------------------------------------------
    # 2. Configurar MLflow con SQLite
    # --------------------------------------------------------

    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    mlflow.set_experiment(EXPERIMENT_NAME)

    print(f"Tracking URI : {MLFLOW_TRACKING_URI}")
    print(f"Experimento  : {EXPERIMENT_NAME}")

    model_version = metadata.get("model_version", "unknown")
    algorithm = metadata.get("algorithm", "unknown")
    risk_threshold = metadata.get("risk_threshold")
    n_features = metadata.get("n_features")
    split_strategy = metadata.get("split_strategy", "unknown")

    run_name = f"{algorithm}-{model_version}"

    # --------------------------------------------------------
    # 3. Registrar ejecucion
    # --------------------------------------------------------

    with mlflow.start_run(run_name=run_name) as run:

        # ---------------- PARAMETROS ----------------

        params = {
            "model_version": model_version,
            "algorithm": algorithm,
            "target": metadata.get("target", "target_default"),
            "group_column": metadata.get("group_column", "source_parent_id"),
            "split_strategy": split_strategy,
            "random_state": metadata.get("random_state"),
            "risk_threshold": risk_threshold,
            "n_features": n_features,
            "train_records": metadata.get("train_records"),
            "validation_records": metadata.get("validation_records"),
            "test_records": metadata.get("test_records"),
        }

        calibration = metadata.get("calibration", {})
        if isinstance(calibration, dict):
            params["calibration_method"] = calibration.get("method")
            params["calibration_cv"] = calibration.get("cv")

        # MLflow no acepta None como valor de parametro.
        params = {
            key: value
            for key, value in params.items()
            if value is not None
        }

        mlflow.log_params(params)

        # ---------------- METRICAS ----------------

        # Prioridad:
        # 1) evaluation_metrics.json, si existe.
        # 2) final_test_metrics dentro de model_metadata.json.
        test_metrics = {}

        if evaluation:
            test_metrics.update(numeric_metrics(evaluation))

        metadata_test_metrics = metadata.get("final_test_metrics", {})
        if isinstance(metadata_test_metrics, dict):
            for key, value in numeric_metrics(metadata_test_metrics).items():
                test_metrics.setdefault(key, value)

        if test_metrics:
            mlflow.log_metrics(
                {
                    f"test_{key}": value
                    for key, value in test_metrics.items()
                }
            )

        validation_metrics = metadata.get("selection_metrics_validation", {})
        if isinstance(validation_metrics, dict):
            validation_numeric = numeric_metrics(validation_metrics)

            if validation_numeric:
                mlflow.log_metrics(
                    {
                        f"validation_{key}": value
                        for key, value in validation_numeric.items()
                    }
                )

        # ---------------- TAGS ----------------

        mlflow.set_tags(
            {
                "project": "ProyectoProductivo_IIIA",
                "solution": "credit-risk-behavioral-scoring",
                "stage": "V2",
                "model_role": "predictive_model",
                "scoring_output": "gold.score_output",
            }
        )

        # ---------------- ARTEFACTOS ----------------

        safe_log_artifact(MODEL_PATH)
        safe_log_artifact(METADATA_PATH)
        safe_log_artifact(EVALUATION_PATH)
        safe_log_artifact(COMPARISON_PATH)
        safe_log_artifact(MANIFEST_PATH)

        # Guardar lista de features como artefacto adicional.
        features = metadata.get("features", [])
        if features:
            features_path = MODEL_DIR / "mlflow_features.json"
            features_path.write_text(
                json.dumps(
                    {
                        "model_version": model_version,
                        "n_features": len(features),
                        "features": features,
                    },
                    indent=2,
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            safe_log_artifact(features_path)

        print("\nRegistro MLflow creado correctamente.")
        print(f"Run ID        : {run.info.run_id}")
        print(f"Modelo        : {algorithm}")
        print(f"Version       : {model_version}")
        print(f"Threshold     : {risk_threshold}")
        print(f"Features      : {n_features}")
        print(f"Tracking DB   : {MLFLOW_DB_PATH}")
        print("=" * 72)
        print("REGISTRO MLFLOW FINALIZADO")
        print("=" * 72)


if __name__ == "__main__":
    main()
