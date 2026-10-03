# 05_api - FastAPI

API operativa del sistema de Behavioral Scoring.

## Funciones

- comprobar estado del servicio y carga del modelo;
- consultar resumen de la cartera puntuada;
- listar cartera con filtro por nivel de riesgo;
- consultar un cliente ya puntuado;
- ejecutar una prediccion real con `model.pkl` sobre un cliente disponible en `gold.gold_ml`.

## Endpoints

- `GET /health`
- `GET /portfolio/summary`
- `GET /portfolio`
- `GET /portfolio/{customer_id}`
- `POST /predict/{customer_id}`

## Flujo de inferencia

`gold.gold_ml -> 47 features -> model.pkl -> PD -> threshold 0.38 -> prediction -> risk_level -> recommendation -> response`

La consulta de cartera existente usa `gold.vw_portfolio_scoring_current`.

## Ejecucion

Desde la raiz del proyecto:

```bash
uvicorn 05_api.main:app --reload
```

Swagger:

`http://127.0.0.1:8000/docs`
