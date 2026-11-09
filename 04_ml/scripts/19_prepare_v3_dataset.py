"""Prepara experimento local V3: correcciones hipoteticas SOLO para train.

No toca tablas, target real, V2, ni split test.
"""
import argparse
import hashlib
import json
from datetime import datetime,timezone
from v3_experiment_utils import ROOT,EXPERIMENT,manifest,write_json

SIMULATED = {100:0,200:0}

def build_plan():
    m=manifest()
    selected=m[m["id"].isin(SIMULATED)]
    if len(selected)!=len(SIMULATED) or set(selected["split"])!={"train"}:
        raise RuntimeError("Correcciones simuladas fuera de TRAIN; experimento bloqueado")
    return {
        "experiment_type":"ACADEMIC_SIMULATION_NOT_VERIFIED",
        "base_model_version":"v20260929_064028",
        "simulated_labels":[{"id":int(x["id"]),"source_parent_id":str(x["source_parent_id"]),
                             "split":x["split"],"hypothetical_target":SIMULATED[int(x["id"])]}
                            for _,x in selected.iterrows()],
        "source":"Dos revisiones humanas aprobadas en la demostracion, SIN resultados observados",
        "warning":"NO es evidencia real ni apto para produccion",
        "test_records_untouched":int((m["split"]=="test").sum()),
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--write",action="store_true",help="Guardar plan local de simulacion")
    a=p.parse_args()
    plan=build_plan()
    print(json.dumps(plan,indent=2,ensure_ascii=False))
    if a.write:
        write_json("simulation_plan.json",plan)
        print("Plan guardado en",EXPERIMENT)
    return 0

if __name__=="__main__":
    raise SystemExit(main())
