# 06_dashboard - Streamlit

Interfaz operativa para consulta de la cartera puntuada.

## Fuente

Streamlit no recalcula la PD. Consume FastAPI, que a su vez consulta `gold.vw_portfolio_scoring_current` o ejecuta el modelo real cuando se solicita scoring.

## Contenido actual

- total de cartera;
- PD promedio;
- cantidad de predicciones positivas;
- clientes en riesgo Alto y Critico;
- semaforo por nivel de riesgo;
- consulta individual por cliente;
- principales senales de comportamiento;
- recomendacion prescriptiva;
- tabla operativa con filtro de riesgo.

## Ejecucion

```bash
streamlit run 06_dashboard/app.py
```

Por defecto consume FastAPI en `http://localhost:8000`. En Docker Compose utiliza `API_BASE_URL=http://api:8000`.
