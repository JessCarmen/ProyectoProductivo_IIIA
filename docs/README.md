# Documentacion del proyecto

La documentación se concentra en esta carpeta para evitar archivos sueltos en la raíz.

## Documentos principales

- `data_dictionary.md`: diccionario de datos.
- `ARCHITECTURE_V2.md`: arquitectura y flujo técnico.
- `V2_CHANGELOG.md`: cambios principales de la versión 2.
- `V2_RUNBOOK_Cmder_Windows.md`: guía de ejecución en Windows 11 y Cmder.
- `ESTRUCTURA_REPOSITORIO.md`: guía rápida para entender el repositorio.

## Referencia histórica

`archive/database_sql_legacy/` contiene únicamente SQL histórico de referencia procedente de versiones anteriores de `02_database/sql/`.

Los SQL históricos **no deben ejecutarse como un pipeline alternativo**. La única fuente oficial y ejecutable de cambios para Supabase es:

`supabase/migrations/`
