# NexaRisk — supervisor, primera etapa del ciclo V3

Este paquete fue construido sobre `ProyectoProductivo_IIIA-main(5).zip`.
Rutas exactas modificadas:
- `05_api/main.py`
- `05_api/reviews.py`
- `06_dashboard/app.py`
- `06_dashboard/review_ui.py`
- `07_tests/test_supervisor.py` (nuevo)

**No modifica** `supabase/migrations/`, `04_ml/models/model.pkl`,
`gold.score_output` ni el scoring de cartera.

## Qué hace
- Muestra revisiones pendientes en panel supervisor dentro de Streamlit.
- Permite aprobar o rechazar una revisión con justificación.
- Exige que supervisor y analista tengan identificadores diferentes.
- Impide decidir dos veces la misma revisión (`ON CONFLICT DO NOTHING`).
- Conserva el historial y las predicciones originales.
- Las correcciones aprobadas NO son etiquetas reales ni reentrenan el modelo.

## Windows / Cmder
1. Abrir proyecto:
   `cd /d D:\ICONTINENTAL\Proyecto_Productivo_IIIA\ProyectoProductivo_IIIA_`
2. Activar:
   `.venv\Scripts\activate.bat`
3. `git status`; si hay cambios, conservarlos antes de reemplazar.
4. Crear rama de respaldo: `git branch respaldo-antes-supervisor`
5. Copiar los cinco archivos en las rutas anteriores.
6. Generar dos claves distintas, sin pegarlas en el chat:
   `python -c "import secrets; print(secrets.token_urlsafe(40))"`
   Ejecutar dos veces.
7. Render → Environment: `SUPERVISOR_API_KEY` = primera clave.
8. Streamlit Cloud → Secrets: `SUPERVISOR_API_KEY` = primera clave,
   `SUPERVISOR_PASSWORD` = segunda clave. Mantener `REVIEW_API_KEY`
   y `REVIEW_ANALYST_PASSWORD` existentes.
9. `python -m pytest 07_tests -v`
10. `python -m compileall -q 05_api 06_dashboard 07_tests`
11. `git diff --check`
12. `git add 05_api/main.py 05_api/reviews.py 06_dashboard/app.py 06_dashboard/review_ui.py 07_tests/test_supervisor.py`
13. `git commit -m "Incorpora aprobacion supervisada de revisiones NexaRisk"`
14. `git push origin main`
15. Comprobar Render `/health`, `/docs` y Streamlit.

## Prueba segura
- En Streamlit, abrir "Administración · Supervisor".
- Consultar pendientes. Rechazar un registro **de prueba** con motivo explícito.
- Verificar en Supabase:
  `SELECT review_id, decision, supervisor_id, decided_at FROM gold.scoring_review_decisions ORDER BY decision_id DESC LIMIT 10;`
- No aprobar una corrección de prueba como si fuera evidencia real.
- No registrar resultados de pago ficticios como observados.

## Límites y seguridad
Es un prototipo académico: clave compartida + ID escrito manualmente.
No es identidad verificable ni autorización individual. Para uso financiero
real se requieren usuarios autenticados, permisos por rol, auditoría
independiente y políticas de acceso. No poner secretos en GitHub.

## Siguiente etapa
Registrar resultados reales verificados, construir snapshots de 47 features
anteriores al resultado, filtrar splits y entrenar V3 en un artefacto nuevo.
No reutilizar el test histórico ni sobrescribir `model.pkl`.
