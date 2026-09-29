# Supabase

Esta carpeta contiene la configuración local de Supabase y las migraciones versionadas.

## Fuente oficial

`supabase/migrations/` es la fuente de verdad para el esquema desplegado.

## Aplicar migraciones

```bash
npx supabase db push --include-all
```
