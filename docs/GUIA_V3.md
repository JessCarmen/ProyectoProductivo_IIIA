# NexaRisk V3 — revisión humana y reentrenamiento responsable

## Objetivo y límites

El formulario registra una opinión humana, NO la etiqueta verdadera. La migración añade decisiones de supervisión y resultados observados verificables; no altera score_output ni model.pkl. La vista `gold.vw_verified_retraining_cases` solo devuelve casos con revisión aprobada y resultado observado con horizonte vencido. No es suficiente por sí sola para reentrenar: hace falta verificar partición, evidencia, no filtración temporal y datos originales de las 47 features.

## Instalación

1. Desde Cmder: `cd /d D:\ICONTINENTAL\Proyecto_Productivo_IIIA\ProyectoProductivo_IIIA_`; activar `.venv\Scripts\activate.bat` si no está activo.
2. `git status`; si limpio: `git pull --ff-only origin main`; `git branch respaldo-antes-v3`.
3. Copiar las rutas de este paquete a la raíz del proyecto sin sobrescribir archivos existentes.
4. En Supabase SQL Editor ejecutar `supabase/migrations/20261108120000_verified_outcomes_and_approvals.sql` una vez. Es aditiva, no borra scoring.
5. Verificar `SELECT COUNT(*) FROM gold.scoring_human_reviews;` y `SELECT COUNT(*) FROM gold.vw_verified_retraining_cases;`.
6. No aprobar automáticamente los dos registros de prueba; primero documentar su naturaleza de demo. Para una corrección de datos, arreglar la fuente y reconstruir features; para una discrepancia de etiqueta, esperar el resultado real y su horizonte.
7. En el backend de confianza (no Streamlit público) registrar decisión de supervisor y resultado observado solo tras validación. Se requiere autenticación individual real antes de exponer endpoints de aprobación o resultados.
8. Ejecutar `python 04_ml/scripts/14_check_retraining_readiness.py` con DATABASE_URL privada en `.env`.
9. No entrenar si hay cero resultados observados independientes, si no se ha fijado la ventana de observación o si las revisiones proceden de test/validation reservado. Una muestra de dos casos demo no permite un reentrenamiento válido.
10. Cuando existan nuevos casos suficientes: congelar snapshot, recuperar 47 features disponibles al tiempo de predicción, aplicar split por `source_parent_id` y tiempo, reservar holdout independiente, entrenar candidato en ruta versionada, comparar ROC-AUC, PR-AUC, FPR/FNR por grupo, calibración y tasas de falsos positivos. Exigir aprobación humana documentada antes de activarlo.
11. No ejecutar `12_score_portfolio.py --replace-existing`: puede intentar borrar scoring enlazado a revisiones. Para publicar V3 diseñar scoring append-only con versionado, nueva vista vigente y rollback.
12. Ejecutar tests y hacer commit únicamente tras comprobar los cambios: `python -m pytest 07_tests -v`, `git diff --check`, `git status`, `git add supabase/migrations/20261108120000_verified_outcomes_and_approvals.sql 04_ml/scripts/14_check_retraining_readiness.py docs/GUIA_V3.md`, `git commit -m "Prepara validacion de outcomes y control de reentrenamiento V3"`, `git push origin main`.

## SQL de inspección

```sql
SELECT review_status, COUNT(*) FROM gold.scoring_human_reviews GROUP BY 1;
SELECT decision, COUNT(*) FROM gold.scoring_review_decisions GROUP BY 1;
SELECT COUNT(*) FROM gold.credit_outcomes_verified;
SELECT COUNT(DISTINCT outcome_id) FROM gold.vw_verified_retraining_cases;
```

## Evidencia y equidad

No se debe afirmar que la PD demuestra incapacidad de pago, ni que la auditoría prueba ausencia de discriminación. Registrar fuente de evidencia, fechas y responsables; analizar grupos con tamaños muestrales y tasas base, errores y calibración. El acceso mediante una clave compartida es prototipo académico, no autorización bancaria de producción.
