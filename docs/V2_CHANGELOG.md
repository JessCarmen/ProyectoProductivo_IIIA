# V2 - Cambios principales

## Prioridad 1 - Modelo

- Split por `source_parent_id` con `StratifiedGroupKFold`.
- Train/Validation/Test aproximadamente 70/15/15.
- Selección de modelos en validation.
- Test reservado para evaluación final.
- PR-AUC (Average Precision) y Brier Score incorporados.
- Calibración del modelo final mediante `CalibratedClassifierCV`.
- Umbral de clasificación seleccionado en validation.
- Nuevo `model.pkl` debe generarse ejecutando `04_train.py`.

## Prioridad 2 - Gold

- `source_parent_id` se propaga a `gold.dim_cliente`, `gold.fact_comportamiento_crediticio` y `gold.gold_ml`.
- Se añade migración `20260929100000_v2_priority_1_2_3.sql`.
- `supabase/migrations/` se mantiene como fuente oficial del esquema desplegado.

## Prioridad 3 - Scoring

- Se agrega `09_load_score_input.py`.
- Se agrega `10_score_input_to_output.py`.
- Se agrega `11_validate_split_integrity.py`.
- `score_output.score_input_id` relaciona cada salida con su entrada.
- `model_version` se registra en los resultados.

## Limpieza de la V2

- Se eliminan del repositorio activo los resultados generados por el split anterior.
- Se mantienen README por carpeta.
- Se refuerza `.gitignore` para evitar caches y outputs temporales.

## Control de Bronze

- Se documenta que `02_load_bronze.py` trabaja por insercion de lote y no debe ejecutarse dos veces sobre la misma fuente sin control.
- Los SQL de `supabase/migrations/` quedan como fuente oficial del esquema; el SQL histórico de referencia se conserva en `docs/archive/database_sql_legacy/` sin duplicar migraciones.
