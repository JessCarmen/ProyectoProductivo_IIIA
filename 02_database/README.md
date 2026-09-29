# 02_database - SQL de referencia

Contiene los scripts SQL de referencia para crear y validar la arquitectura de datos.

La **fuente oficial de cambios desplegados en Supabase** es `supabase/migrations/`.

La arquitectura es:

`Bronze -> Silver Maestros/Hechos -> Gold`

Los procedimientos de limpieza se ejecutan en Silver y los procedimientos de construcción de Gold preparan `gold_ml`.
