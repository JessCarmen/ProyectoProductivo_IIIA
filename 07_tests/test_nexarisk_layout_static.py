"""Static regression checks for the dashboard patch; no remote services required."""
import ast
from pathlib import Path

APP = Path(__file__).resolve().parents[1] / '06_dashboard' / 'app.py'
SOURCE = APP.read_text(encoding='utf-8')
TREE = ast.parse(SOURCE)


def test_source_compiles():
    compile(SOURCE, str(APP), 'exec')


def test_existing_api_endpoints_preserved():
    for endpoint in ('/portfolio/summary', '/portfolio/analytics', '/portfolio'):
        assert endpoint in SOURCE


def test_human_review_functions_preserved():
    assert 'render_review_panel(customer, API_BASE_URL)' in SOURCE
    assert 'render_supervisor_panel(API_BASE_URL)' in SOURCE


def test_pages_exist():
    for page in ('Cartera', 'Cliente 360', 'Revisión de casos', 'Supervisión', 'Resultados'):
        assert f'"{page}"' in SOURCE


def test_charts_disable_streamlit_dark_theme():
    assert SOURCE.count('st.altair_chart(') == 8
    assert SOURCE.count('theme=None') == 8
    assert 'background="#FFFFFF"' in SOURCE


def test_export_and_table_preserved():
    assert 'st.download_button(' in SOURCE
    assert 'st.dataframe(' in SOURCE
    assert 'cartera_filtrada_nexarisk.csv' in SOURCE


def test_model_and_db_unchanged():
    assert 'joblib.dump' not in SOURCE
    assert 'UPDATE gold.' not in SOURCE
    assert 'DELETE FROM gold.' not in SOURCE
