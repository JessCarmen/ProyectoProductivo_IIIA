# 03_analysis - EDA y calidad

Esta carpeta contiene el perfilado y el análisis exploratorio.

Orden recomendado:

1. `00_profile_raw.py`: describe la fuente RAW sin modificarla.
2. `01_profile_quality.py`: identifica nulos, categorías y valores extremos.
3. `02_load_bronze.py`: carga la fuente en Bronze.
4. Ejecutar la limpieza SQL para producir Silver.
5. `03_eda_silver.py`: analiza Silver limpio.
6. `04_eda_negative_values.py`: revisa valores negativos que requieren interpretación.

El EDA orienta las decisiones de feature engineering; no sustituye la limpieza SQL.
