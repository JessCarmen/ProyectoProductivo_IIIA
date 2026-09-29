# Proyecto Productivo IIIA - Riesgo Crediticio

## Objetivo

Desarrollar un sistema de **Behavioral Scoring** que utilice seis meses de comportamiento financiero para estimar la probabilidad de incumplimiento del siguiente periodo, clasificar el nivel de riesgo y generar una recomendación preventiva.

## Flujo principal

**XLS/CSV -> Bronze -> Silver (Maestros y Hechos) -> limpieza y transformación mediante Stored Procedures -> Silver limpio y validado -> EDA -> ingeniería de variables -> Gold -> gold_ml -> entrenamiento y evaluación -> model.pkl -> predicción -> clasificación -> nivel de riesgo -> motor prescriptivo -> score_output -> FastAPI/Docker -> Streamlit/Power BI -> MLOps.**

## Herramientas

- **Supabase/PostgreSQL:** almacenamiento y arquitectura Medallion.
- **Google Colab / Python:** EDA, análisis, entrenamiento y evaluación durante el desarrollo.
- **GitHub:** código, scripts, migraciones, documentación y artefactos versionados.
- **FastAPI:** servicio de scoring.
- **Docker:** empaquetado y despliegue.
- **Streamlit:** interfaz operativa.
- **Power BI:** visualización de cartera.
- **MLflow:** seguimiento de experimentos y modelos, pendiente de implementación final.

## Estructura del repositorio

- `01_data/`: fuente RAW y muestras.
- `02_database/`: referencia de la arquitectura de base de datos.
- `03_analysis/`: perfilado, calidad y EDA.
- `04_ml/`: features, entrenamiento, evaluación, predicción y prescripción.
- `05_api/`: FastAPI (pendiente de implementación).
- `06_dashboard/`: Streamlit (pendiente de implementación).
- `07_tests/`: pruebas automatizadas (pendientes de implementación).
- `docs/`: documentación centralizada.
- `supabase/migrations/`: **fuente oficial de los cambios desplegados en Supabase**.

## SQL y Supabase

Los scripts históricos de `02_database/sql/` se conservan solamente en `docs/archive/database_sql_legacy/`. No deben ejecutarse como un segundo pipeline. Para actualizar Supabase se utiliza exclusivamente `supabase/migrations/`.

## Modelo V2

La versión 2 utiliza `source_parent_id` para mantener juntos los registros originales y sus derivados al realizar la división de datos. Se trabaja aproximadamente con 70% train, 15% validation y 15% test.

La selección del modelo se realiza con validation y el test queda reservado para la evaluación final.

Métricas: ROC-AUC, PR-AUC, Precision, Recall, F1, matriz de confusión y Brier Score/calibración.

## Scoring

`gold.score_input -> model.pkl -> probabilidad -> predicción 0/1 -> nivel de riesgo -> recomendación -> gold.score_output`

## Inicio rápido

1. Configurar `.env` a partir de `.env.example`.
2. Vincular el proyecto local con Supabase.
3. Aplicar las migraciones con `npx supabase db push --include-all`.
4. Construir y validar Gold/GOLD_ML.
5. Entrenar el modelo con `04_ml/scripts/04_train.py`.
6. Evaluar con `04_ml/scripts/05_evaluate.py`.
7. Probar el flujo `score_input -> score_output`.

Consulta `docs/V2_RUNBOOK_Cmder_Windows.md` para el procedimiento detallado.
