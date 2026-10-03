# 04_ml - Machine Learning y prescripcion

## Secuencia principal

1. Construir/actualizar `gold.gold_ml`.
2. Validar `gold_ml` y las features.
3. Entrenar candidatos con `04_train.py`.
4. Evaluar el modelo final con `05_evaluate.py`.
5. Probar prediccion y prescripcion individual.
6. Validar integridad del split por `source_parent_id`.
7. Ejecutar scoring por `score_input -> score_output` cuando corresponda.
8. Ejecutar scoring masivo de cartera con `12_score_portfolio.py`.
9. Registrar el modelo en MLflow con `13_register_mlflow.py`.
10. Generar el baseline operativo con `14_monitoring_snapshot.py`.

## Division de datos

Se utiliza `source_parent_id` para impedir que registros relacionados queden en particiones distintas. El entrenamiento V2 utiliza `StratifiedGroupKFold` con 20 folds: 14 para train, 3 para validation y 3 para test.

El conjunto test permanece reservado hasta la evaluacion final.

## Modelos evaluados

- Random Forest.
- XGBoost.

La seleccion se realiza sobre validation con el siguiente orden de criterio:

1. ROC-AUC.
2. PR-AUC.
3. F1 de la clase default.

El modelo final seleccionado es XGBoost calibrado mediante sigmoid (`CalibratedClassifierCV`, cv=5).

## Umbral

El umbral binario se selecciona en validation sobre una grilla de 0.10 a 0.90. El objetivo principal es F1 de default, con Recall como desempate y cercania a 0.50 como segundo desempate.

Umbral operativo actual: **0.38**.

## Features

- 23 variables explicativas originales.
- 26 variables derivadas en Gold.
- 2 variables derivadas excluidas del modelo por sensibilidad a denominadores pequenos: `payment_bill_ratio_avg` y `payment_bill_ratio_max`.
- Total final utilizado por el modelo: **47 features**.

## Artefactos principales

- `model.pkl`: modelo final.
- `model_metadata.json`: version, features, threshold, split y metricas.
- `evaluation_metrics.json`: metricas finales.
- `model_comparison.json`: comparacion de candidatos.
- `split_manifest.csv`: trazabilidad del split.
- `test_predictions.csv`: predicciones del test reservado de 5,005 registros.
- `monitoring_snapshot.json`: baseline operativo de la cartera puntuada.

`model.pkl` se versiona mediante Git LFS.
