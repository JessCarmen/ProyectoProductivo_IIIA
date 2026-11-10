"""Pruebas de regresion del endpoint de agregacion, sin Supabase remoto."""
import ast
import re
from pathlib import Path
from types import SimpleNamespace


def load_endpoint():
    source = Path(__file__).resolve().parents[1] / '05_api' / 'main.py'
    tree = ast.parse(source.read_text(encoding='utf-8'))
    fn = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'portfolio_analytics')
    fn.decorator_list = []
    # Quitar defaults Query() para ejecutar el codigo aislado.
    fn.args.defaults = [ast.Constant(value=None), ast.Constant(value=None), ast.Constant(value=0.0)]
    module = ast.fix_missing_locations(ast.Module(body=[fn], type_ignores=[]))
    queries = []

    class Result:
        def mappings(self): return self
        def all(self): return [{'clientes': 33377, 'pd_promedio': 0.3842}]

    class Connection:
        def execute(self, sql, params):
            queries.append((str(sql), dict(params)))
            return Result()

    class Engine:
        def connect(self):
            class Ctx:
                def __enter__(self): return Connection()
                def __exit__(self, *args): return False
            return Ctx()

    class HTTPException(Exception):
        def __init__(self, status_code, detail):
            self.status_code = status_code
            super().__init__(detail)

    ns = {
        'engine': Engine(), 'text': lambda sql: sql,
        'serialize_row': dict, 'serialize_rows': lambda rows: list(rows),
        'VALID_RISK_LEVELS': {'BAJO','MEDIO','ALTO','CRITICO'},
        'HTTPException': HTTPException,
        'logger': SimpleNamespace(exception=lambda *a: None),
    }
    exec(compile(module, str(source), 'exec'), ns)
    return ns['portfolio_analytics'], queries, HTTPException


def test_analytics_uses_full_population_not_top_n():
    endpoint, queries, _ = load_endpoint()
    result = endpoint()
    assert result['scope'] == 'cartera_filtrada_completa'
    assert len(queries) == 6
    assert all(not re.search(r'\b(LIMIT|OFFSET)\s+\d+|\b(LIMIT|OFFSET)\s+:', sql, re.I) for sql, _ in queries)
    assert all('gold.vw_portfolio_scoring_current' in sql for sql, _ in queries)


def test_analytics_applies_all_filters_consistently():
    endpoint, queries, _ = load_endpoint()
    endpoint('CRITICO', 1, 0.6)
    for sql, params in queries:
        assert 'risk_level = :risk_level' in sql
        assert 'prediction = :prediction' in sql
        assert 'probability_default >= :min_pd' in sql
        assert params == {'risk_level': 'CRITICO', 'prediction': 1, 'min_pd': 0.6}


def test_analytics_rejects_invalid_risk():
    endpoint, queries, error = load_endpoint()
    try:
        endpoint('NO_VALIDO', None, 0.0)
        assert False, 'Debe rechazar riesgo invalido'
    except error as exc:
        assert exc.status_code == 400
    assert not queries
