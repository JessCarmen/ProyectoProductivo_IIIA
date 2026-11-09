"""Puerta de seguridad antes de iniciar entrenamiento V3.

No entrena. Evita afirmar que opiniones son etiquetas verificadas.
"""
from __future__ import annotations
import csv
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
MANIFEST=ROOT/"04_ml/models/split_manifest.csv"

def main():
    if not MANIFEST.is_file():
        print("BLOQUEADO: no existe split_manifest.csv")
        return 2
    with MANIFEST.open(encoding="utf-8-sig",newline="") as handle:
        rows=list(csv.DictReader(handle))
    if not rows or not {"id","source_parent_id","split"}.issubset(rows[0]):
        print("BLOQUEADO: manifiesto incompleto")
        return 2
    groups={}
    for row in rows:
        group=row["source_parent_id"]
        split=row["split"]
        if group in groups and groups[group]!=split:
            print("BLOQUEADO: leakage de source_parent_id",group)
            return 2
        groups[group]=split
    print("Integridad del split: OK. Registros:",len(rows))
    print("AUN NO LISTO para entrenar V3 con revisiones.")
    print("Requisitos: resultados reales nuevos, fecha/horizonte verificados,")
    print("snapshot de las 47 features previo al resultado, separacion temporal")
    print("y test independiente. No modificar model.pkl ni usar el test historico.")
    return 1

if __name__=="__main__":
    raise SystemExit(main())
