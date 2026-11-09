"""Registrar un resultado REAL de pago verificado, nunca una opinion del analista.

Ejemplo:
 python 04_ml/scripts/17_verified_outcome_cli.py --score-output-id 123 --end-date 2027-04-30 --actual-default 0 --evidence REF-INTERNA --verifier SUP_01 --confirm
"""
from __future__ import annotations
import argparse
import os
from datetime import date
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

ROOT=Path(__file__).resolve().parents[2]
load_dotenv(ROOT/".env")


def main():
    p=argparse.ArgumentParser(description="Resultados de pago verificados")
    p.add_argument("--score-output-id",type=int,required=True)
    p.add_argument("--end-date",required=True,help="AAAA-MM-DD")
    p.add_argument("--actual-default",type=int,choices=[0,1],required=True)
    p.add_argument("--evidence",required=True)
    p.add_argument("--verifier",required=True)
    p.add_argument("--confirm",action="store_true")
    a=p.parse_args()
    try:
        end=date.fromisoformat(a.end_date)
    except ValueError:
        p.error("Fecha invalida, usa AAAA-MM-DD")
    if a.score_output_id<1 or len(a.evidence.strip())<3 or len(a.verifier.strip())<3:
        p.error("Campos invalidos")
    if end>date.today():
        p.error("No se puede verificar un resultado futuro")
    if not a.confirm:
        print("SIMULACION: NO se escribio ningun resultado.")
        print("Usa --confirm solo con evidencia de pago REAL y horizonte cumplido.")
        return 0
    url=os.getenv("DATABASE_URL")
    if not url:p.error("Falta DATABASE_URL")
    if url.startswith("postgresql://"):
        url="postgresql+psycopg://"+url[len("postgresql://"):]
    engine=create_engine(url,pool_pre_ping=True,connect_args={"connect_timeout":10})
    try:
        with engine.begin() as conn:
            score=conn.execute(text("""
                SELECT score_output_id, fecha_score FROM gold.score_output
                WHERE score_output_id=:id FOR SHARE
            """),{"id":a.score_output_id}).mappings().first()
            if score is None:raise ValueError("score_output_id inexistente")
            if score["fecha_score"] and end < score["fecha_score"].date():
                raise ValueError("El resultado no puede preceder al scoring")
            inserted=conn.execute(text("""
                INSERT INTO gold.credit_outcomes_verified
                    (score_output_id,observation_end_date,actual_default,
                     evidence_reference,verified_by)
                VALUES (:id,:end,:actual,:evidence,:verifier)
                ON CONFLICT (score_output_id,observation_end_date) DO NOTHING
                RETURNING outcome_id
            """),{"id":a.score_output_id,"end":end,"actual":a.actual_default,
                  "evidence":a.evidence.strip(),"verifier":a.verifier.strip()}).scalar_one_or_none()
            if inserted is None:raise ValueError("Ya existe resultado para ese score y fecha")
            print("Resultado verificado registrado:",inserted)
        return 0
    except (ValueError,SQLAlchemyError) as exc:
        print("NO SE GUARDO:",str(exc).splitlines()[0])
        return 1
    finally:engine.dispose()

if __name__=="__main__":
    raise SystemExit(main())
