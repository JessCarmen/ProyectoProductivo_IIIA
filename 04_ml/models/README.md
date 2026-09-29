# Artefactos del modelo

Despues de ejecutar `04_ml/scripts/04_train.py` se generan los artefactos usados por el scoring:

- `model.pkl`: modelo final entrenado y calibrado para inferencia. Debe gestionarse con Git LFS si se versiona.
- `model_metadata.json`: version, features, split, umbral y metricas.
- `evaluation_metrics.json`: resultado final sobre TEST.
- `model_comparison.json`: comparacion de candidatos sobre VALIDATION.
- `split_manifest.csv`: asignacion de cada cliente a train/validation/test.

Los resultados del modelo anterior al split por `source_parent_id` no deben reutilizarse como resultados finales.
