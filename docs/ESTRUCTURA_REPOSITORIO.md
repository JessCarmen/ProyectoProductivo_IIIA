# Estructura del repositorio

La organización sigue la secuencia de trabajo del proyecto y separa datos, análisis, Machine Learning, despliegue y documentación.

```text
01_data
   ↓
02_database
   ↓
03_analysis
   ↓
04_ml
   ↓
05_api
   ↓
06_dashboard
   ↓
07_tests

supabase/migrations = fuente oficial del esquema de Supabase
```

## Carpetas principales

`01_data/`: fuente RAW y muestras.

`02_database/`: referencia de la arquitectura de base de datos. No es una segunda fuente ejecutable.

`03_analysis/`: perfilado, controles de calidad y EDA.

`04_ml/`: construcción de features, entrenamiento, evaluación, predicción, prescripción y scoring.

`05_api/`: API FastAPI, pendiente de implementación.

`06_dashboard/`: interfaz Streamlit, pendiente de implementación.

`07_tests/`: pruebas automatizadas, pendientes de implementación.

`docs/`: documentación centralizada y archivo histórico de referencia.

`supabase/`: configuración y migraciones versionadas. `supabase/migrations/` es la fuente oficial de cambios de base de datos.

## Archivos de raíz

La raíz se reserva para configuración y archivos de entrada del proyecto: `README.md`, dependencias, variables de entorno de ejemplo, configuración de Git y archivos de Docker cuando se incorporen.
