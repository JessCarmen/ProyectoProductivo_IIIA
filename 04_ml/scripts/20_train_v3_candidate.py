"""Entrena candidato experimental V3 sin sobrescribir el modelo V2.

No promueve a produccion; NO usa los ejemplos como resultados reales.
"""
import argparse
import json
from datetime import datetime,timezone
import joblib
import numpy as np
from sklearn.pipeline import Pipeline
from sklearn.base import clone
from xgboost import XGBClassifier
from modeling_utils import build_preprocessor,build_calibrated,metrics_from_probabilities
from v3_experiment_utils import EXPERIMENT,metadata,prepare_frame,write_json

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--confirm-simulation",action="store_true")
    parser.add_argument("--estimators",type=int,default=200)
    args=parser.parse_args()
    if not args.confirm_simulation:
        parser.error("Requiere --confirm-simulation: etiquetas hipoteticas, NO reales")
    plan_path=EXPERIMENT/"simulation_plan.json"
    if not plan_path.is_file():
        parser.error("Ejecuta primero 19_prepare_v3_dataset.py --write")
    plan=json.loads(plan_path.read_text(encoding="utf-8"))
    if plan.get("experiment_type")!="ACADEMIC_SIMULATION_NOT_VERIFIED":
        raise RuntimeError("Plan no es simulacion")
    df,features=prepare_frame()
    train=df[df["split"]=="train"].copy()
    val=df[df["split"]=="validation"].copy()
    test=df[df["split"]=="test"].copy()
    y=train["target_default"].astype(int).copy()
    for item in plan["simulated_labels"]:
        mask=train["id"]==item["id"]
        if mask.sum()!=1:raise RuntimeError("ID simulado no pertenece a train")
        y.loc[mask]=int(item["hypothetical_target"])
    if y.nunique()!=2:raise RuntimeError("Target degenerado")
    pre,_,_=build_preprocessor(train[features])
    weight=float((y==0).sum()/max((y==1).sum(),1))
    base=Pipeline([("preprocessor",pre),("model",XGBClassifier(
        n_estimators=args.estimators,max_depth=5,learning_rate=.05,
        subsample=.85,colsample_bytree=.85,min_child_weight=2,
        reg_lambda=1,objective="binary:logistic",eval_metric="logloss",
        random_state=42,n_jobs=2,tree_method="hist",scale_pos_weight=weight))])
    calibrated=build_calibrated(base)
    print("Entrenando SOLO TRAIN con 2 etiquetas hipoteticas; validacion y test intactos.")
    calibrated.fit(train[features],y)
    threshold=float(metadata()["risk_threshold"])
    pval=calibrated.predict_proba(val[features])[:,1]
    ptest=calibrated.predict_proba(test[features])[:,1]
    metrics={
        "validation":metrics_from_probabilities(val["target_default"].astype(int).to_numpy(),pval,threshold),
        "test":metrics_from_probabilities(test["target_default"].astype(int).to_numpy(),ptest,threshold),
    }
    EXPERIMENT.mkdir(parents=True,exist_ok=True)
    joblib.dump(calibrated,EXPERIMENT/"model_candidate.pkl")
    write_json("candidate_metrics.json",{
        "experiment_type":"ACADEMIC_SIMULATION_NOT_VERIFIED",
        "base_model_version":metadata()["model_version"],
        "threshold":threshold,
        "train_rows":len(train),"validation_rows":len(val),"test_rows":len(test),
        "simulated_labels":plan["simulated_labels"],
        "metrics":metrics,
        "promotable":False,
        "warning":"NO usar para decisiones crediticias ni reemplazar model.pkl",
    })
    import pandas as pd
    pd.DataFrame({"id":test["id"].astype(int),"source_parent_id":test["source_parent_id"].astype(str),
                  "target":test["target_default"].astype(int),"probability":ptest,
                  "prediction":(ptest>=threshold).astype(int),
                  "sex":test["sex"],"education":test["education"],
                  "age":test["age"],"marriage":test["marriage"]}).to_csv(
                      EXPERIMENT/"candidate_test_predictions.csv",index=False)
    print("Candidato experimental guardado:",EXPERIMENT)
    return 0

if __name__=="__main__":
    raise SystemExit(main())
