"""Auditoría reproducible de errores por grupo sobre TEST reservado.

No prueba cumplimiento legal ni ausencia de discriminación. No reentrena el modelo.
Uso: python 04_ml/scripts/13_audit_fairness.py
"""
from pathlib import Path
import json

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
TEST_PATH = ROOT / "04_ml/models/test_predictions.csv"
RAW_PATH = ROOT / "01_data/raw/credit_card_clients_raw.csv"
OUT_DIR = ROOT / "04_ml/models/fairness_audit"
MIN_GROUP_N = 100


def evaluate(df):
    n = len(df)
    tp = int(((df.prediction == 1) & (df.target == 1)).sum())
    fp = int(((df.prediction == 1) & (df.target == 0)).sum())
    fn = int(((df.prediction == 0) & (df.target == 1)).sum())
    tn = int(((df.prediction == 0) & (df.target == 0)).sum())
    neg = fp + tn
    pos = tp + fn
    return {
        "n": n, "TP": tp, "FP": fp, "FN": fn, "TN": tn,
        "prevalencia": pos / n if n else None,
        "tasa_prediccion_positiva": (tp + fp) / n if n else None,
        "fpr": fp / neg if neg else None,
        "fnr": fn / pos if pos else None,
        "precision": tp / (tp + fp) if tp + fp else None,
        "recall": tp / pos if pos else None,
        "brier": float(((df.probability - df.target) ** 2).mean()) if n else None,
    }


def main():
    test = pd.read_csv(TEST_PATH)
    raw = pd.read_csv(RAW_PATH, sep=";", encoding="utf-8-sig", low_memory=False)
    cols = ["ID", "SEX", "AGE", "EDUCATION", "MARRIAGE", "record_origin"]
    df = test.merge(raw[cols], left_on="id", right_on="ID", how="left", validate="one_to_one")
    if df["ID"].isna().any():
        raise ValueError("Hay IDs de test sin correspondencia en los datos originales")
    if not (df["target"].isin([0, 1]) & df["prediction"].isin([0, 1])).all():
        raise ValueError("Target/prediction fuera de 0 y 1")
    df["grupo_edad"] = pd.cut(
        pd.to_numeric(df.AGE, errors="coerce"),
        bins=[0, 29, 39, 49, 59, 200],
        labels=["<=29", "30-39", "40-49", "50-59", "60+"],
    ).astype("string").fillna("NO_INFORMADO")
    df["grupo_sexo_codificado"] = df.SEX.astype("string").fillna("NO_INFORMADO")
    df["grupo_educacion_codificado"] = df.EDUCATION.astype("string").fillna("NO_INFORMADO")
    df["grupo_estado_civil_codificado"] = df.MARRIAGE.astype("string").fillna("NO_INFORMADO")

    rows = []
    for population, part in [("test_consolidado", df), ("test_solo_originales", df[df.record_origin == "public_original"])]:
        for attribute in ["grupo_sexo_codificado", "grupo_edad", "grupo_educacion_codificado", "grupo_estado_civil_codificado"]:
            for group, subset in part.groupby(attribute, dropna=False):
                metrics = evaluate(subset)
                rows.append({"poblacion": population, "atributo": attribute, "grupo": str(group), **metrics})

    out = pd.DataFrame(rows)
    out["muestra_suficiente"] = out.n >= MIN_GROUP_N
    out["alerta_muestra"] = out["muestra_suficiente"].map({True: "", False: "N<100: no comparar"})
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT_DIR / "fairness_by_group.csv", index=False, encoding="utf-8-sig")
    summary = {
        "nota": "Auditoría descriptiva sobre test. No demuestra causalidad ni cumplimiento normativo.",
        "test_consolidado": evaluate(df),
        "test_solo_originales": evaluate(df[df.record_origin == "public_original"]),
        "criterio_alerta_exploratorio": "Revisar diferencias absolutas de FPR >= 0.05 entre grupos con N>=100. No es umbral legal.",
        "comparaciones": [],
    }
    for population in out.poblacion.unique():
        for attribute in out.atributo.unique():
            s = out[(out.poblacion == population) & (out.atributo == attribute) & out.muestra_suficiente]
            values = s.fpr.dropna()
            if len(values) >= 2:
                gap = float(values.max() - values.min())
                summary["comparaciones"].append({
                    "poblacion": population, "atributo": attribute,
                    "brecha_fpr": gap, "alerta_exploratoria": gap >= 0.05,
                })
    (OUT_DIR / "fairness_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print("Auditoría terminada:", OUT_DIR)
    print("Test consolidado:", summary["test_consolidado"])
    print("Test solo originales:", summary["test_solo_originales"])
    print("Brechas FPR:", summary["comparaciones"])


if __name__ == "__main__":
    main()
