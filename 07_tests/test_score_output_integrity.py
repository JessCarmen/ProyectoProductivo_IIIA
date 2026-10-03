import os

import pytest
from sqlalchemy import create_engine, text


@pytest.mark.integration
def test_score_output_integrity():
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        pytest.skip("DATABASE_URL no configurada; se omite prueba de integracion con Supabase")

    engine = create_engine(database_url, pool_pre_ping=True)
    query = text("""
        SELECT
            COUNT(*)::int AS total,
            COUNT(DISTINCT id)::int AS ids_unicos,
            COUNT(*) FILTER (WHERE probability_default IS NULL)::int AS pd_nulos,
            COUNT(*) FILTER (WHERE prediction IS NULL)::int AS prediction_nulos,
            COUNT(*) FILTER (WHERE risk_level IS NULL)::int AS risk_nulos,
            COUNT(*) FILTER (WHERE recommendation IS NULL)::int AS recommendation_nulos
        FROM gold.score_output
    """)

    try:
        with engine.connect() as conn:
            row = conn.execute(query).mappings().one()
    finally:
        engine.dispose()

    assert row["total"] == 33377
    assert row["ids_unicos"] == 33377
    assert row["pd_nulos"] == 0
    assert row["prediction_nulos"] == 0
    assert row["risk_nulos"] == 0
    assert row["recommendation_nulos"] == 0
