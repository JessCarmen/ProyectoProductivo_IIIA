"""Read-only readiness report. Never trains, updates or deletes data."""
import os
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()
ROOT = Path(__file__).resolve().parents[2]

def main():
    url = os.getenv('DATABASE_URL')
    if not url:
        raise SystemExit('Falta DATABASE_URL en .env (no la publiques).')
    if url.startswith('postgresql://'):
        url = 'postgresql+psycopg://' + url[len('postgresql://'):]
    engine = create_engine(url, connect_args={'connect_timeout': 10}, pool_pre_ping=True)
    queries = {
        'revisiones': 'SELECT COUNT(*) FROM gold.scoring_human_reviews',
        'decisiones_aprobadas': "SELECT COUNT(*) FROM gold.scoring_review_decisions WHERE decision='APROBADA'",
        'resultados_observados': 'SELECT COUNT(*) FROM gold.credit_outcomes_verified',
        'casos_elegibles': 'SELECT COUNT(DISTINCT outcome_id) FROM gold.vw_verified_retraining_cases',
    }
    with engine.connect() as con:
        for label, sql in queries.items():
            print(f'{label}: {con.execute(text(sql)).scalar_one()}')
        print('Nota: elegible no implica admisible para train; verificar split, fuente, calidad y fecha.')
    engine.dispose()

if __name__ == '__main__':
    main()
