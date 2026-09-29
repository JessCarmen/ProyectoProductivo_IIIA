# 02_database - Referencia de base de datos

Esta carpeta documenta la arquitectura lógica de datos del proyecto.

## Fuente oficial de Supabase

La fuente oficial y ejecutable de los cambios de base de datos es:

`supabase/migrations/`

Las migraciones son las que se aplican mediante:

```bash
npx supabase db push --include-all
```

## Arquitectura

`Bronze -> Silver Maestros/Hechos -> Gold`

Los Stored Procedures de limpieza y transformación se implementan dentro de las migraciones de Supabase y dejan Silver preparado para el análisis posterior.

## SQL históricos

Los antiguos scripts de `02_database/sql/` se conservaron únicamente como referencia histórica en:

`docs/archive/database_sql_legacy/`

No deben ejecutarse como un segundo pipeline ni considerarse una fuente alternativa al historial de `supabase/migrations/`.
