# NexaRisk V3 — continuación verificada

## Estado del ZIP (7)
- `04_ml/scripts/04_train.py` **sobrescribe** `04_ml/models/model.pkl`. No ejecutar para V3.
- `04_ml/scripts/12_score_portfolio.py --replace-existing` elimina score_input/score_output. No ejecutar.
- `04_ml/scripts/15_check_retraining_readiness.py` tenía una consulta a `decision` pero la migración define `decision_status`. Corregido.
- `supabase/migrations/20261029120000_scoring_human_reviews.sql` existe; su historial remoto debe conciliarse si aparece sin aplicar.
- `supabase/migrations/20261108120000_verified_outcomes_and_approvals.sql` define estructuras V3; no prueba que estén instaladas.
- `06_dashboard/review_ui.py` y `05_api/reviews.py` registran revisiones, pero no resultados reales ni aprobaciones.
- `04_ml/scripts/13_audit_fairness.py` sí existe y puede ejecutarse.

## Instalación en Windows / Cmder
1. `cd /d D:\ICONTINENTAL\Proyecto_Productivo_IIIA\ProyectoProductivo_IIIA_`
2. `.venv\Scripts\activate.bat`
3. `git status` (guardar antes cambios propios).
4. Copiar **solo** los archivos de este ZIP respetando rutas. No borrar nada.
5. `python -m pytest 07_tests/test_v3_gate.py -v`
6. `python 02_database/apply_migrations.py --check`
7. Si 20261029120000 figura local pero no remoto, **no reparar sin comparar** estructura real y SQL.
8. Cuando se concilie historial: `python 02_database/apply_migrations.py --apply`
9. `python 04_ml/scripts/15_check_retraining_readiness.py`
10. `python 04_ml/scripts/18_retraining_gate.py` (salida 1 es BLOQUEO esperado, no error inesperado).

## Decisiones y resultados: comandos de demostración (SIN escritura)
`python 04_ml/scripts/16_review_decision_cli.py --review-id 1 --decision RECHAZADA --supervisor SUP_01 --note "Registro de prueba sin evidencia verificable."`
`python 04_ml/scripts/17_verified_outcome_cli.py --score-output-id 1 --end-date 2026-10-01 --actual-default 0 --evidence DEMO --verifier SUP_01`

Solo si tienes evidencias **reales** y autorizacion, agrega `--confirm`. 
La clave publicable de Supabase NO se usa para escribir resultados verificados.
No pongas contraseñas, datos personales ni credenciales en GitHub.

## Por qué todavía NO reentrenamos
El modelo actual usa `gold.gold_ml` y un `split_manifest.csv` de 33,377 registros.
No existe un dataset verificado de nuevas observaciones con snapshots de features
anteriores al resultado, horizonte de pago homogéneo y test independiente.
No se debe convertir una opinión humana en `target_default` automáticamente.

## Siguiente entregable después de contar con evidencia
- Versionar snapshots de features y targets con fecha de corte.
- Dataset elegible con control de leakage y aprobación.
- Entrenar XGBoost candidato en directorio NUEVO, no `model.pkl`.
- Comparar contra V2 en holdout temporal independiente.
- Ejecutar auditoría de equidad por grupos con intervalos de confianza.
- Aprobar/promover versión y re-scorear sin DELETE de score_output.
