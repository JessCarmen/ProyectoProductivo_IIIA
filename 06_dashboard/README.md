# 06_dashboard - Streamlit

Dashboard operativo para supervisión de la cartera puntuada.

## Fuente

Streamlit no recalcula la PD. Consume FastAPI, que consulta `gold.vw_portfolio_scoring_current`.

## Vista actual

La interfaz está orientada a un supervisor de créditos e incluye:

- resumen ejecutivo de cartera;
- PD promedio;
- cartera Alto + Crítico como cola prioritaria;
- distribución por nivel de riesgo;
- priorización de clientes por PD;
- consulta Cliente 360;
- señales de atraso y recomendación prescriptiva;
- filtros de cartera por riesgo y clasificación;
- exportación CSV;
- ficha técnica del modelo con métricas del test reservado.

## Identidad visual

Se usa la marca académica ficticia **NexaRisk**. No representa una institución financiera real.

## Ejecución

```bash
streamlit run 06_dashboard/app.py
```

Por defecto consume FastAPI en `http://127.0.0.1:8000`. En Streamlit Community Cloud se configura `API_BASE_URL` como secret.
