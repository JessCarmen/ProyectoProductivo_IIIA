# 05_api - FastAPI

Esta carpeta alojará la API del scoring.

Flujo esperado:

`request -> model.pkl -> PD -> riesgo -> recomendación -> response`

La API se implementa después de validar el flujo batch `score_input -> score_output`.
