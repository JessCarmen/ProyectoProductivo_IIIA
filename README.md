# Proyecto Productivo IIIA - Riesgo Crediticio

## Objetivo

Desarrollar un sistema de **Behavioral Scoring** que utilice seis meses de comportamiento financiero para estimar la probabilidad de incumplimiento del siguiente periodo, clasificar el nivel de riesgo y generar una recomendacion preventiva.

## Flujo principal

**XLS/CSV -> Bronze -> Silver (Maestros y Hechos) -> Stored Procedures de limpieza y transformacion -> Silver limpio y validado -> EDA -> ingenieria de variables -> Gold -> gold_ml -> entrenamiento y evaluacion -> model.pkl -> scoring -> clasificacion -> nivel de riesgo -> motor prescriptivo -> score_output -> vista de cartera -> FastAPI/Docker -> Streamlit/Power BI -> MLflow/monitoreo.**

## Estado actual

- Dataset de trabajo: **33,377 registros**.
- Modelo final: **XGBoost V2** calibrado.
- Inputs del modelo: **47 features**.
- Umbral de clasificacion: **0.38**.
- Test reservado: **5,005 registros**.
- ROC-AUC test: **0.7999**.
- PR-AUC test: **0.6915**.
- F1 de default test: **0.6153**.
- `gold.score_output`: **33,377 registros**, **33,377 IDs unicos** y **0 nulos criticos**.
- Vista operativa: `gold.vw_portfolio_scoring_current`.
- FastAPI: implementado.
- Streamlit: implementado.
- Docker Compose: implementado.
- MLflow: registro del modelo, parametros, metricas y artefactos implementado.
- Monitoreo: baseline operativo implementado; la comparacion temporal se realiza cuando exista un nuevo periodo real.

## Herramientas

- **Supabase/PostgreSQL:** almacenamiento, arquitectura Medallion y persistencia del scoring.
- **Python / Google Colab:** EDA, validacion, feature engineering, entrenamiento, evaluacion y scoring.
- **GitHub:** codigo, migraciones, documentacion y artefactos versionados.
- **FastAPI:** servicio de consulta y scoring.
- **Docker / Docker Compose:** empaquetado de API y dashboard.
- **Streamlit:** interfaz operativa para consulta de cartera.
- **Power BI:** visualizacion ejecutiva y operativa sobre la vista Gold.
- **MLflow:** trazabilidad del modelo y sus metricas.
- **Pytest:** pruebas automatizadas de artefactos, reglas, API e integridad de scoring.

## Estructura del repositorio

- `01_data/`: fuente RAW y muestras.
- `02_database/`: referencia de la arquitectura de base de datos.
- `03_analysis/`: perfilado, calidad y EDA.
- `04_ml/`: features, entrenamiento, evaluacion, prediccion, prescripcion, scoring masivo, MLflow y monitoreo.
- `05_api/`: API FastAPI operativa.
- `06_dashboard/`: dashboard Streamlit.
- `07_tests/`: pruebas automatizadas.
- `docs/`: documentacion centralizada.
- `supabase/migrations/`: **fuente oficial de los cambios desplegados en Supabase**.

## SQL y Supabase

Los SQL historicos conservados en `docs/archive/database_sql_legacy/` son solo referencia. No deben ejecutarse como un segundo pipeline. Para actualizar Supabase se utiliza exclusivamente `supabase/migrations/`.

## Modelo V2

La version 2 usa `source_parent_id` como grupo para evitar leakage entre train, validation y test. El split utiliza `StratifiedGroupKFold` con 20 folds: 14 para train, 3 para validation y 3 para test.

Se evaluan **Random Forest y XGBoost**. La seleccion se realiza sobre validation con el orden de criterio **ROC-AUC -> PR-AUC -> F1 de default**. El conjunto test se mantiene reservado para la evaluacion final.

El modelo final es XGBoost calibrado con `CalibratedClassifierCV` (sigmoid, cv=5). El umbral binario se optimiza sobre validation y queda en 0.38.

## Scoring y prescripcion

`gold.gold_ml -> model.pkl -> probabilidad -> prediccion 0/1 -> nivel de riesgo -> recomendacion -> gold.score_output`

Bandas operativas actuales:

- BAJO: PD < 0.20
- MEDIO: 0.20 <= PD < 0.40
- ALTO: 0.40 <= PD < 0.70
- CRITICO: PD >= 0.70

La recomendacion es generada por un motor prescriptivo basado en reglas de negocio; no se presenta como una decision automatica de un LLM.

## Cartera puntuada

Resultado validado del scoring masivo:

- total: 33,377
- IDs unicos: 33,377
- prediction 0: 21,073
- prediction 1: 12,304
- BAJO: 15,043
- MEDIO: 6,328
- ALTO: 3,453
- CRITICO: 8,553
- PD promedio: 0.3841617924

La fuente recomendada para Streamlit y Power BI es `gold.vw_portfolio_scoring_current`.

## Ejecucion operativa rapida

1. Configurar `.env` a partir de `.env.example`.
2. Instalar dependencias: `pip install -r requirements-prod.txt`.
3. Aplicar migraciones: `npx supabase db push --include-all`.
4. Asegurar el artefacto LFS: `git lfs install && git lfs pull`.
5. Levantar API: `uvicorn 05_api.main:app --reload`.
6. Levantar dashboard: `streamlit run 06_dashboard/app.py`.
7. Ejecutar pruebas: `pytest 07_tests -v`.
8. Registrar en MLflow: `python 04_ml/scripts/13_register_mlflow.py`.
9. Crear baseline operativo: `python 04_ml/scripts/14_monitoring_snapshot.py`.

Para reproducir todo el pipeline desde datos hasta despliegue, consulta `docs/V2_RUNBOOK_Cmder_Windows.md`.
