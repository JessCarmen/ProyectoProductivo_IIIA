# NexaRisk V3 — Migración automatizada, ajustada al repositorio real

## Estructura verificada del ZIP (4)
- `02_database/README.md` documenta, no contiene scripts ejecutables.
- `supabase/migrations/` es la **única fuente oficial de SQL**.
- `package.json` ya contiene `supabase` como dependencia de desarrollo.
- La migración existente `20261029120000_scoring_human_reviews.sql` ya creó la tabla de revisiones.

No creamos `02_database/sql`, ni un segundo historial `meta.*`, ni conectamos con una clave publicable.
El script Python llama a **Supabase CLI** para mantener el historial oficial de migraciones.

## Pasos en Cmder (Windows)

```bat
cd /d D:\ICONTINENTAL\Proyecto_Productivo_IIIA\ProyectoProductivo_IIIA_
.venv\Scripts\activate.bat
git status
npm install
npx supabase login
npx supabase link --project-ref juoybkynizmsbscinlpv
python 02_database/apply_migrations.py --check
python 02_database/apply_migrations.py --apply
python 02_database/apply_migrations.py --check
```

`npx supabase login` abrirá autenticación interactiva. No pegues tokens aquí.
Antes de aplicar, revisa la lista de migraciones pendientes: `--include-all`
puede aplicar **otras migraciones antiguas** que no estén registradas en remoto.
Si la lista no coincide con lo esperado, NO ejecutes `--apply`.
Si el proyecto está pausado, primero reanúdalo.

## Validación

Desde Python se puede consultar el catálogo de Supabase con la conexión privada
DATABASE_URL (no se incluye en este paquete). La ejecución SQL se registra en
`supabase_migrations.schema_migrations`, gestionado por la CLI.

Las nuevas tablas estarán inicialmente vacías; eso es normal.
Este paquete NO implementa aprobaciones en FastAPI/Streamlit ni reentrena el modelo.
No modifica `gold.score_output` ni `04_ml/models/model.pkl`.

## Git

```bat
python -m py_compile 02_database/apply_migrations.py
git add 02_database/apply_migrations.py supabase/migrations/20261108120000_verified_outcomes_and_approvals.sql
git commit -m "Prepara migraciones V3 con Supabase CLI desde Python"
git push origin main
```
