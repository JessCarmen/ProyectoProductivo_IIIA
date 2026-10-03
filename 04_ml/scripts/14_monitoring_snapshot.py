import json
import os
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()
ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "04_ml" / "models" / "monitoring_snapshot.json"

url = os.getenv("DATABASE_URL")
if not url:
    raise RuntimeError("No se encontro DATABASE_URL")
engine = create_engine(url, pool_pre_ping=True)
query = text("""
SELECT probability_default::float AS probability_default, prediction, risk_level
FROM gold.vw_portfolio_scoring_current
""")
try:
    df = pd.read_sql_query(query, engine)
finally:
    engine.dispose()

risk_counts = {str(k): int(v) for k, v in df["risk_level"].value_counts().to_dict().items()}
pred_counts = {str(k): int(v) for k, v in df["prediction"].value_counts().to_dict().items()}
payload = {
    "created_at_utc": datetime.now(timezone.utc).isoformat(),
    "records": int(len(df)),
    "pd_min": float(df["probability_default"].min()),
    "pd_mean": float(df["probability_default"].mean()),
    "pd_max": float(df["probability_default"].max()),
    "prediction_counts": pred_counts,
    "risk_counts": risk_counts,
    "note": "Baseline operativo. Comparar snapshots futuros para prediction drift; no afirmar data drift sin datos de periodos futuros.",
}
OUT.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
print(json.dumps(payload, indent=2, ensure_ascii=False))
print("Snapshot guardado en:", OUT)
