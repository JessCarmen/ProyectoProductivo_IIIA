# Proyecto Productivo IIIA - Riesgo Crediticio

## Objetivo

Desarrollar un sistema de **Behavioral Scoring** que utilice seis meses de comportamiento financiero para estimar la probabilidad de incumplimiento del siguiente periodo, clasificar el nivel de riesgo y generar una recomendación preventiva.

## Flujo del proyecto

**XLS/CSV -> Bronze -> Silver -> EDA -> Feature Engineering -> Gold -> gold_ml -> Entrenamiento -> Evaluacion -> model.pkl -> Prediccion -> Nivel de riesgo -> Motor prescriptivo -> score_output -> FastAPI/Docker -> Streamlit/Power BI -> MLOps.**

## Herramientas

- **Supabase/PostgreSQL:** almacenamiento y pipeline Medallion.
- **Google Colab / Python:** EDA, feature engineering, entrenamiento y evaluación.
- **GitHub:** código, SQL, notebooks y documentación.
- **FastAPI:** servicio de scoring.
- **Docker:** empaquetado y despliegue.
- **Streamlit:** interfaz operativa.
- **Power BI:** visualización de cartera.
- **MLflow:** seguimiento de experimentos/modelos.

## Estructura

- `01_data/`: fuente RAW.
- `02_database/`: SQL de referencia del modelo de datos.
- `03_analysis/`: perfilado, calidad y EDA.
- `04_ml/`: features, entrenamiento, evaluación, predicción y prescripción.
- `05_api/`: API FastAPI.
- `06_dashboard/`: aplicación Streamlit.
- `07_tests/`: pruebas.
- `supabase/migrations/`: **fuente oficial de cambios de base de datos**.

## Modelo y evaluación

La versión 2 corrige la separación de entrenamiento mediante `source_parent_id` para evitar que registros derivados del mismo cliente aparezcan en diferentes particiones. El proceso utiliza aproximadamente 70% train, 15% validation y 15% test, con separación por grupo.

El test se reserva para la evaluación final. La comparación y el ajuste del umbral se realizan sobre validation.

Métricas: ROC-AUC, PR-AUC (Average Precision), Precision, Recall, F1, matriz de confusión y Brier Score/calibración.

## Scoring

El flujo de inferencia es:

`gold.score_input -> model.pkl -> probabilidad -> prediccion 0/1 -> nivel de riesgo -> recomendacion -> gold.score_output`

## Importante

El `model.pkl` de esta versión debe generarse nuevamente después de aplicar el nuevo esquema de partición. Los resultados del modelo de la versión anterior no deben considerarse resultados finales.

## Inicio rápido

1. Configurar `.env` a partir de `.env.example`.
2. Aplicar las migraciones de Supabase.
3. Cargar/actualizar Bronze y ejecutar el pipeline hacia Gold.
4. Ejecutar `04_ml/scripts/04_train.py`.
5. Ejecutar `04_ml/scripts/05_evaluate.py`.
6. Cargar casos en `gold.score_input` y ejecutar `10_score_input_to_output.py`.

Consulta el README de cada carpeta para el detalle.
