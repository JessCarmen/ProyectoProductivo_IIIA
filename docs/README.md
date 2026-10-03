# Documentacion del proyecto

La documentacion se concentra en esta carpeta para evitar archivos sueltos en la raiz.

## Documentos principales

- `data_dictionary.md`: diccionario y criterios de calidad.
- `ARCHITECTURE_V2.md`: arquitectura y flujo tecnico final.
- `V2_CHANGELOG.md`: cambios principales de la version 2.
- `V2_RUNBOOK_Cmder_Windows.md`: guia reproducible de ejecucion en Windows 11 y Cmder.
- `ESTRUCTURA_REPOSITORIO.md`: guia rapida del repositorio.
- `POWER_BI.md`: fuente, medidas y propuesta de paginas para Power BI.
- `FINALIZACION.md`: estado tecnico validado y limites de interpretacion.

## Referencia historica

`archive/database_sql_legacy/` contiene unicamente SQL historico de referencia procedente de versiones anteriores de `02_database/sql/`.

Los SQL historicos **no deben ejecutarse como pipeline alternativo**. La unica fuente oficial y ejecutable de cambios para Supabase es:

`supabase/migrations/`
