"""Utilidades V3 experimental. No escribe en Supabase."""
from pathlib import Path
import json
import os
import sys
import pandas as pd

ROOT=Path(__file__).resolve().parents[2]
MODELS=ROOT/"04_ml/models"
EXPERIMENT=MODELS/"v3_experimental"
sys.path.insert(0,str(ROOT/"04_ml/scripts"))
from modeling_utils import EXCLUDED_FEATURES, TARGET, GROUP_COLUMN

def metadata():
    return json.loads((MODELS/"model_metadata.json").read_text(encoding="utf-8"))

def manifest():
    m=pd.read_csv(MODELS/"split_manifest.csv",dtype={"source_parent_id":str})
    required={"id","source_parent_id","split"}
    if not required.issubset(m.columns) or m["id"].duplicated().any():
        raise RuntimeError("Manifiesto invalido")
    if m.groupby("source_parent_id")["split"].nunique().max()!=1:
        raise RuntimeError("Leakage por source_parent_id")
    return m

def load_gold():
    from dotenv import load_dotenv
    import psycopg
    load_dotenv(ROOT/".env")
    url=os.getenv("DATABASE_URL")
    if not url:
        raise RuntimeError("Falta DATABASE_URL privada en .env")
    with psycopg.connect(url,connect_timeout=15) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM gold.gold_ml ORDER BY id")
            cols=[c.name for c in cur.description]
            return pd.DataFrame(cur.fetchall(),columns=cols)

def prepare_frame():
    df=load_gold()
    m=manifest()
    if df["id"].duplicated().any() or len(df)!=len(m):
        raise RuntimeError("IDs/numero de registros no coinciden con split original")
    df=df.merge(m[["id","source_parent_id","split"]],on="id",validate="one_to_one",suffixes=("","_manifest"))
    if (df["source_parent_id"].astype(str)!=df["source_parent_id_manifest"].astype(str)).any():
        raise RuntimeError("Grupos inconsistentes")
    meta=metadata()
    features=meta["features"]
    if len(features)!=47 or not set(features).issubset(df.columns):
        raise RuntimeError("No se encuentran las 47 features del modelo V2")
    if df[TARGET].isna().any():
        raise RuntimeError("Targets nulos")
    return df, features

def write_json(name,obj):
    EXPERIMENT.mkdir(parents=True,exist_ok=True)
    (EXPERIMENT/name).write_text(json.dumps(obj,indent=2,ensure_ascii=False,default=str),encoding="utf-8")
