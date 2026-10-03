# 07_tests - Pruebas automatizadas

El proyecto incluye pruebas unitarias e integracion opcional con Supabase.

## Cobertura actual

- existencia y lectura de `model_metadata.json`;
- disponibilidad/carga de `model.pkl` cuando Git LFS esta materializado;
- algoritmo XGBoost;
- 47 features;
- threshold 0.38;
- limites de las bandas BAJO, MEDIO, ALTO y CRITICO;
- generacion no vacia de recomendaciones;
- endpoint `/health` de FastAPI;
- integridad de `gold.score_output`: 33,377 filas, 33,377 IDs unicos y 0 nulos criticos, cuando `DATABASE_URL` esta disponible.

La integridad del split por `source_parent_id` se valida adicionalmente con:

```bash
python 04_ml/scripts/11_validate_split_integrity.py
```

## Ejecucion

```bash
pytest 07_tests -v
```

Si se ejecuta sin `DATABASE_URL`, el test de integracion contra Supabase se omite de forma explicita.
