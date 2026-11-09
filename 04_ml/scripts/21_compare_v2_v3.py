"""Compara V2 guardado contra candidato experimental en test NO entrenado."""
import json
import pandas as pd
import numpy as np
from sklearn.metrics import confusion_matrix
from modeling_utils import metrics_from_probabilities
from v3_experiment_utils import MODELS,EXPERIMENT,metadata,write_json

def group_fpr(frame,group):
    results=[]
    for value,subset in frame.groupby(group,dropna=False):
        negative=subset[subset["target"]==0]
        if len(negative)<30:continue
        fpr=float((negative["prediction"]==1).mean())
        results.append({"group":group,"value":str(value),"n":len(subset),
                        "negatives":len(negative),"fpr":fpr})
    return results

def main():
    old=pd.read_csv(MODELS/"test_predictions.csv")
    new_path=EXPERIMENT/"candidate_test_predictions.csv"
    if not new_path.is_file():
        raise RuntimeError("Falta candidato: ejecutar 20_train_v3_candidate.py")
    new=pd.read_csv(new_path)
    if old["id"].duplicated().any() or new["id"].duplicated().any():
        raise RuntimeError("IDs duplicados en test")
    both=old.merge(new,on="id",validate="one_to_one",suffixes=("_v2","_v3"))
    if len(both)!=len(old) or len(both)!=len(new):
        raise RuntimeError("Test no coincide entre versiones")
    if not (both["target_v2"]==both["target_v3"]).all():
        raise RuntimeError("Etiquetas test diferentes")
    if not (both["source_parent_id_v2"].astype(str)==both["source_parent_id_v3"].astype(str)).all():
        raise RuntimeError("Grupos test diferentes")
    threshold=float(metadata()["risk_threshold"])
    y=both["target_v2"].astype(int).to_numpy()
    metrics={}
    for version in ["v2","v3"]:
        prob=both[f"probability_{version}"].to_numpy()
        metrics[version]=metrics_from_probabilities(y,prob,threshold)
        metrics[version]["false_positives"]=int(((y==0)&(prob>=threshold)).sum())
        metrics[version]["false_negatives"]=int(((y==1)&(prob<threshold)).sum())
    fair=[]
    for version in ["v2","v3"]:
        frame=pd.DataFrame({"target":y,"prediction":(both[f"probability_{version}"]>=threshold).astype(int)})
        for group in ["sex","education","marriage"]:
            frame[group]=both[group]
            fair.extend([{"version":version,**x} for x in group_fpr(frame,group)])
    report={"experiment_type":"ACADEMIC_SIMULATION_NOT_VERIFIED",
            "test_records":len(both),"threshold":threshold,
            "metrics":metrics,"fairness_exploratory":fair,
            "production_approval":"BLOCKED",
            "reason":"Etiquetas de correccion son simuladas; no hay nuevos outcomes verificados ni holdout temporal"}
    write_json("comparison_report.json",report)
    print(json.dumps({"test_records":len(both),"metrics":metrics,
                      "production_approval":"BLOCKED"},indent=2))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
