"""Registro controlado de decisiones de supervisor; no modifica score_output.

Ejemplo:
 python 04_ml/scripts/16_review_decision_cli.py --review-id 1 --decision RECHAZADA --supervisor SUP_01 --note "Prueba academica, no existe evidencia verificada." --confirm
"""
from __future__ import annotations
import argparse
import os
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")


def main():
    p=argparse.ArgumentParser(description="Decision de supervisor NexaRisk")
    p.add_argument("--review-id", type=int, required=True)
    p.add_argument("--decision", choices=["APROBADA","RECHAZADA"], required=True)
    p.add_argument("--supervisor", required=True)
    p.add_argument("--note", required=True)
    p.add_argument("--confirm", action="store_true", help="Autoriza escribir en Supabase")
    a=p.parse_args()
    if a.review_id < 1 or len(a.supervisor.strip()) < 3 or len(a.note.strip()) < 20:
        p.error("ID positivo, supervisor >=3 y nota >=20 caracteres")
    if not a.confirm:
        print("SIMULACION: se registraria", a.decision, "para review_id", a.review_id)
        print("Agrega --confirm solo tras verificar evidencia y datos.")
        return 0
    url=os.getenv("DATABASE_URL")
    if not url:
        p.error("Falta DATABASE_URL")
    if url.startswith("postgresql://"):
        url="postgresql+psycopg://"+url[len("postgresql://"):]
    engine=create_engine(url,pool_pre_ping=True,connect_args={"connect_timeout":10})
    try:
        with engine.begin() as conn:
            row=conn.execute(text("""
                SELECT review_id, review_status, evidence_reference
                FROM gold.scoring_human_reviews WHERE review_id=:id FOR SHARE
            """),{"id":a.review_id}).mappings().first()
            if row is None:
                raise ValueError("La revision no existe")
            if a.decision == "APROBADA" and row["review_status"] == "CORRECCION_PROPUESTA" and not row["evidence_reference"]:
                raise ValueError("La correccion no tiene referencia de evidencia")
            inserted=conn.execute(text("""
                INSERT INTO gold.scoring_review_decisions
                    (review_id, decision_status, supervisor_id, decision_note)
                VALUES (:review_id,:status,:supervisor,:note)
                ON CONFLICT (review_id) DO NOTHING
                RETURNING decision_id
            """),{"review_id":a.review_id,"status":a.decision,
                  "supervisor":a.supervisor.strip(),"note":a.note.strip()}).scalar_one_or_none()
            if inserted is None:
                raise ValueError("Esta revision ya tiene decision; no se sobrescribe")
            print("Decision registrada:", inserted)
        return 0
    except (ValueError, SQLAlchemyError) as exc:
        print("NO SE GUARDO:", str(exc).splitlines()[0])
        return 1
    finally:
        engine.dispose()

if __name__=="__main__":
    raise SystemExit(main())
