# Arquitectura V2

## Secuencia de datos y ML

1. `01_data/raw` contiene la fuente original de 33,377 registros.
2. Supabase Bronze conserva la fuente RAW.
3. Supabase Silver Maestros/Hechos recibe los datos despues de crear sus tablas y ejecutar los Stored Procedures de limpieza.
4. Google Colab realiza el EDA sobre Silver limpio.
5. La logica de feature engineering se materializa en Gold mediante los procedimientos SQL actuales; Colab documenta y valida las variables.
6. `gold.gold_ml` es el dataset que alimenta el entrenamiento.
7. El entrenamiento usa split por `source_parent_id` y produce train/validation/test.
8. La seleccion ocurre en validation; test queda reservado.
9. El modelo final se guarda en `04_ml/models/model.pkl`.
10. `gold.score_input` recibe casos y `10_score_input_to_output.py` genera `gold.score_output`.

## Responsabilidades

- Supabase: datos, Medallion, procedimientos y persistencia de scoring.
- Google Colab/Python: EDA, validaciones, modelado y pruebas.
- GitHub: codigo, SQL, documentacion y versionado.
- FastAPI/Docker: despliegue del servicio.
- Streamlit/Power BI: consumo.
- MLflow/Python: monitoreo y ciclo de vida del modelo.
