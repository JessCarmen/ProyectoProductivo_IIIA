# 04_ml - Machine Learning y prescripción

## Secuencia

1. Construir/actualizar `gold.gold_ml`.
2. Validar `gold_ml` y las features.
3. Ejecutar `04_train.py`.
4. Ejecutar `05_evaluate.py`.
5. Probar `06_predict.py`.
6. Probar `07_recommendation.py`.
7. Ejecutar `09_load_score_input.py`.
8. Ejecutar `10_score_input_to_output.py`.
9. Ejecutar `11_validate_split_integrity.py`.

## División de datos

Se usa `source_parent_id` para impedir que un cliente original y sus registros derivados queden en particiones diferentes. Se trabaja con una división aproximada de 70/15/15.

## Modelos

- Regresión Logística como baseline.
- Random Forest.
- XGBoost.

La selección se realiza en validation. Test se reserva para la evaluación final.

## Artefactos

`model.pkl` es el modelo final entrenado. `model_metadata.json` guarda las features, versión, umbral y parámetros.
