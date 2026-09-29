# V2 - Runbook de ejecucion en Windows 11 + Cmder

## 1. Preparar el repositorio

```bash
git clone https://github.com/JessCarmen/ProyectoProductivo_IIIA.git
cd ProyectoProductivo_IIIA
```

Crear o activar el entorno virtual y copiar `.env.example` a `.env`. Completar `DATABASE_URL` con el acceso de Supabase.

## 2. Aplicar migraciones de Supabase

```bash
npx supabase db push --include-all
```

La migracion V2 agrega el lineage `source_parent_id` a Gold y relaciona `score_output` con `score_input`.

## 3. Verificar Bronze y cargar solo si corresponde

Antes de ejecutar una nueva carga, revisar en Supabase cuántos registros existen:

```sql
SELECT COUNT(*) FROM bronze.raw_credit_card_clients;
```

Si Bronze ya contiene los 33,377 registros de esta fuente, **no volver a ejecutar el loader**, porque el script actual agrega un nuevo lote. Solo cargar cuando Bronze este vacio o cuando se este incorporando un lote nuevo de forma intencional:

```bash
python 03_analysis/scripts/02_load_bronze.py
```

## 4. Construir Silver y Gold

Los Stored Procedures existentes hacen la limpieza y carga de Silver. Luego ejecutar:

```bash
python 04_ml/scripts/01_feature_engineering.py
```

El script refresca `source_parent_id` despues de reconstruir Gold y GOLD_ML.

## 5. Validar GOLD_ML

```bash
python 04_ml/scripts/02_validate_gold_ml.py
python 04_ml/scripts/03_validate_features.py
```

## 6. Entrenar y evaluar V2

```bash
python 04_ml/scripts/04_train.py
python 04_ml/scripts/05_evaluate.py
```

El entrenamiento genera `model.pkl`, `model_metadata.json`, `evaluation_metrics.json`, `model_comparison.json`, `split_manifest.csv` y `test_predictions.csv`.

La division es por `source_parent_id`, aproximadamente 70/15/15. El modelo se selecciona sobre validation y test queda reservado para la evaluacion final.

## 7. Verificar que no exista leakage

```bash
python 04_ml/scripts/11_validate_split_integrity.py
```

La salida debe indicar cero `source_parent_id` compartidos entre train, validation y test.

## 8. Probar prediccion individual

```bash
python 04_ml/scripts/06_predict.py --id 1
python 04_ml/scripts/07_recommendation.py --id 1
```

## 9. Probar el ciclo score_input -> score_output

```bash
python 04_ml/scripts/09_load_score_input.py --id 1
python 04_ml/scripts/10_score_input_to_output.py
```

Revisar en Supabase:

```sql
SELECT * FROM gold.score_input ORDER BY score_input_id DESC;
SELECT * FROM gold.score_output ORDER BY score_output_id DESC;
```

## 10. Subir cambios a GitHub

Revisar primero:

```bash
git status
git diff
```

Luego:

```bash
git add .
git commit -m "V2 corrige split por cliente y automatiza scoring"
git push origin main
```

### Git LFS para model.pkl

```bash
git lfs install
git lfs track "04_ml/models/model.pkl"
git add .gitattributes 04_ml/models/model.pkl
git commit -m "Actualiza model.pkl V2"
git push origin main
```

No subir `.env`.
