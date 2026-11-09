"""Diagnostico SOLO LECTURA del flujo de reentrenamiento NexaRisk V3.

Ejecutar desde la raiz:
    python 04_ml/scripts/15_check_retraining_readiness.py
"""
from __future__ import annotations
import os
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")


def main() -> int:
    url = os.getenv("DATABASE_URL")
    if not url:
        print("ERROR: DATABASE_URL no configurada en .env")
        return 2
    if url.startswith("postgresql://"):
        url = "postgresql+psycopg://" + url[len("postgresql://"):]

    engine = create_engine(
        url, pool_pre_ping=True, pool_timeout=10,
        connect_args={"connect_timeout": 10, "options": "-c statement_timeout=15000"},
    )
    objects = [
        "gold.scoring_human_reviews",
        "gold.scoring_review_decisions",
        "gold.credit_outcomes_verified",
        "gold.model_training_runs",
        "gold.vw_verified_retraining_cases",
    ]
    try:
        with engine.connect() as conn:
            for name in objects:
                exists = conn.execute(
                    text("SELECT to_regclass(:name) IS NOT NULL"),
                    {"name": name},
                ).scalar_one()
                print(f"{name}: {'OK' if exists else 'PENDIENTE'}")
            required = objects[1:]
            present = {
                name: conn.execute(
                    text("SELECT to_regclass(:name) IS NOT NULL"), {"name": name}
                ).scalar_one()
                for name in objects
            }
            if not all(present.values()):
                print("V3 NO LISTA: faltan estructuras. No reentrenar.")
                return 1
            queries = {
                "revisiones": "SELECT COUNT(*) FROM gold.scoring_human_reviews",
                "correcciones_propuestas": """SELECT COUNT(*) FROM gold.scoring_human_reviews
                                            WHERE review_status='CORRECCION_PROPUESTA'""",
                "decisiones_aprobadas": """SELECT COUNT(*) FROM gold.scoring_review_decisions
                                            WHERE decision='APROBADA'""",
                "resultados_observados": "SELECT COUNT(*) FROM gold.credit_outcomes_verified",
                "casos_vinculados": "SELECT COUNT(DISTINCT outcome_id) FROM gold.vw_verified_retraining_cases",
            }
            print("\nCONTEOS:")
            for label, sql in queries.items():
                print(f"  {label}: {conn.execute(text(sql)).scalar_one()}")
            print("\nAVISO: caso vinculado NO equivale a caso entrenable.")
            print("Falta comprobar horizonte, snapshot de variables, split y evidencia.")
        return 0
    except SQLAlchemyError as exc:
        print(f"ERROR de conexion/consulta: {type(exc).__name__}")
        return 2
    finally:
        engine.dispose()


if __name__ == "__main__":
    raise SystemExit(main())
