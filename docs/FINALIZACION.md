# Cierre tecnico del proyecto

## Estado validado
- score_output: 33,377 registros
- IDs unicos: 33,377
- nulos en PD/prediction/risk/recommendation: 0
- PD min: 0.001919
- PD media: 0.3841617924
- PD max: 1.0
- BAJO: 15,043 (45.07%)
- MEDIO: 6,328 (18.96%)
- ALTO: 3,453 (10.35%)
- CRITICO: 8,553 (25.63%)
- prediction 0: 21,073
- prediction 1: 12,304

## Arquitectura final
Gold/GOLD_ML -> model.pkl -> score_output -> vista de cartera -> FastAPI -> Streamlit/Power BI -> Docker.
MLflow registra modelo/metricas. Monitoring snapshot crea la linea base operativa para comparaciones futuras.

## No hacer
- No recalcular PD con formulas manuales.
- No usar target_default como input de inferencia.
- No presentar PSI simulado como drift real.
- No incluir credenciales en codigo o notebooks.
