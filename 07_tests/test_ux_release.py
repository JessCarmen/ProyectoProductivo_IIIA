from pathlib import Path
import ast
import tomllib

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / '06_dashboard' / 'app.py').read_text(encoding='utf-8')
CFG = tomllib.loads((ROOT / '.streamlit' / 'config.toml').read_text(encoding='utf-8'))

def test_python_syntax():
    ast.parse(APP)

def test_light_theme_is_explicit():
    assert CFG['theme']['base'] == 'light'
    assert CFG['theme']['backgroundColor'] == '#F3F6FA'
    assert CFG['theme']['secondaryBackgroundColor'] == '#FFFFFF'

def test_all_workflows_remain():
    for marker in ('render_review_panel(customer, API_BASE_URL)',
                   'render_supervisor_panel(API_BASE_URL)',
                   '"Cliente 360"', '"Revisión de casos"', '"Supervisión"',
                   '"Resultados"', 'st.download_button('):
        assert marker in APP, marker

def test_api_endpoints_preserved():
    for endpoint in ('/portfolio/summary', '/portfolio/analytics', '/portfolio', '/portfolio/{customer_id}'):
        assert endpoint in APP

def test_kpis_before_charts_and_table():
    assert APP.index('kpi_card("Cartera evaluada"') < APP.index('section("Distribución de riesgo"')
    assert APP.index('section("Distribución de riesgo"') < APP.index('section("Cartera priorizada"')

def test_chart_and_table_contrast():
    assert 'background="#FFFFFF"' in APP
    assert 'theme=None' in APP
    assert '[data-testid="stDataFrame"]' in APP
    assert 'stDataFrame' in APP

def test_analytics_are_full_population():
    assert 'load_analytics(risk_filter, prediction_filter, min_pd)' in APP
    assert 'analytics_frame("exposure")' in APP
    assert 'analytics_frame("delay")' in APP
