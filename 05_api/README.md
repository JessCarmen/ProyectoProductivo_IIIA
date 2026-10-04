# 05_api - FastAPI

API operativa para exponer públicamente la cartera puntuada del sistema de Behavioral Scoring.

## Modo público actual

El despliegue gratuito de Render funciona en modo **consulta de scoring persistido**. La API **no carga `model.pkl` en memoria** en Render para mantenerse dentro del límite del plan gratuito. Los resultados consultados fueron generados previamente por el XGBoost V2 y persistidos en `gold.score_output`.

## Funciones

- comprobar estado del servicio y conexión a Supabase;
- consultar resumen de la cartera puntuada;
- listar cartera con filtros por nivel de riesgo y clasificación;
- consultar un cliente ya puntuado;
- devolver mediante `POST /predict/{customer_id}` el scoring XGBoost ya persistido para compatibilidad con clientes de la API.

## Endpoints

- `GET /`
- `GET /health`
- `GET /portfolio/summary`
- `GET /portfolio`
- `GET /portfolio/{customer_id}`
- `POST /predict/{customer_id}`

## Flujo público

`gold.score_output -> gold.vw_portfolio_scoring_current -> FastAPI -> Streamlit`

El flujo de inferencia real del proyecto sigue siendo:

`gold.gold_ml -> model.pkl -> PD -> threshold 0.38 -> prediction -> risk_level -> recommendation -> gold.score_output`

## Ejecución local

```bash
uvicorn 05_api.main:app --reload
```

Swagger:

`http://127.0.0.1:8000/docs`
