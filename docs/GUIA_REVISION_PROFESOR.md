# NexaRisk — Control de equidad y revisión humana (prototipo académico)

## Qué contiene

1. `04_ml/scripts/13_audit_fairness.py`: calcula TP, FP, FN, TN, FPR, FNR, precisión y Brier por grupo sobre el TEST reservado, y repite la auditoría únicamente con registros originales UCI.
2. `docs/fairness_by_group.csv` y `docs/fairness_summary.json`: resultados de la auditoría calculados con el ZIP entregado.
3. `supabase/migrations/20261029120000_scoring_human_reviews.sql`: tabla **aditiva** `gold.scoring_human_reviews`.
4. `05_api/main.py` y `05_api/reviews.py`: endpoints protegidos de escritura/lectura de revisiones.
5. `06_dashboard/app.py` y `06_dashboard/review_ui.py`: panel de validación humana integrado en Cliente 360.
6. `07_tests/test_review_validation.py`: pruebas unitarias de autenticación y esquema.

## Resultados verificables de TEST (sin reentrenar)

- Test consolidado: N=5,005; TP=919; FP=567; FN=582; TN=2,937; FPR=16.18%; FNR=38.77%.
- Entre las predicciones positivas, 567/1,486 = 38.16% fueron falsos positivos en el test. No extrapolar automáticamente esa proporción a la cartera productiva.
- En el test de registros originales UCI (N=4,500), la precisión positiva fue ~50.48% y la FNR ~41.97%.
- En los grupos SEX codificados 1 y 2, FPR fue 20.83% y 13.34% respectivamente (brecha 7.49 puntos porcentuales). El grupo código 3 solo tiene 3 observaciones: no interpretar.
- La alerta exploratoria de brecha >=5 pp NO es un umbral legal ni demuestra discriminación causal. Es un disparador de auditoría.
- El dataset contiene sexo/edad/estado civil/educación como variables del modelo. No se dispone de ingresos y cuotas verificados para probar capacidad de pago individual.

## Orden de instalación — no omitir pasos

1. Hacer copia/branch y revisar diff; NO reemplazar `.env`, modelo ni datos.
2. En Supabase SQL Editor, ejecutar SOLO la migración nueva `supabase/migrations/20261029120000_scoring_human_reviews.sql`. No reejecutar migraciones históricas.
3. En Render > Environment, crear `REVIEW_API_KEY` con un valor aleatorio largo (mínimo 24 caracteres). No publicarlo. Ejemplo de generación local: `python -c "import secrets; print(secrets.token_urlsafe(40))"`.
4. En Streamlit Cloud > Manage app > Settings > Secrets, añadir:

   ```toml
   REVIEW_API_KEY = "EL_MISMO_VALOR_SECRETO_DE_RENDER"
   REVIEW_ANALYST_PASSWORD = "OTRA_CLAVE_LARGA_DISTINTA"
   ```

   Conservar `API_BASE_URL` existente. **No guardar secretos en GitHub**.
5. Copiar los archivos del ZIP a las rutas relativas correspondientes en el repositorio y hacer `git add`/`commit`/`push`. Render y Streamlit deben desplegar los cambios.
6. Probar `/health` y `/portfolio/summary` (deben seguir funcionando), luego abrir Streamlit > Cliente 360 > Consultar > Validación humana. Entrar con la clave de analista.
7. Guardar una revisión de prueba en un cliente de demostración y verificar en Supabase:

   ```sql
   SELECT review_id, customer_id, score_output_id, review_status,
          proposed_prediction, reviewer_id, evidence_type,
          evidence_reference, created_at
   FROM gold.scoring_human_reviews
   ORDER BY review_id DESC LIMIT 10;
   ```

8. Verificar que `SELECT COUNT(*) FROM gold.score_output;` no cambió por guardar la revisión.
9. Ejecutar auditoría offline: `python 04_ml/scripts/13_audit_fairness.py`.
10. Ejecutar tests: `pytest 07_tests/test_review_validation.py -v` y la suite habitual con dependencias del proyecto instaladas.

## Qué hace y qué NO hace el formulario

- CONFIRMADO: el analista considera razonable la evaluación; no prueba resultado futuro.
- OBSERVADO: requiere revisión adicional.
- CORRECCION_PROPUESTA: propone otra clase (0/1), exige referencia de evidencia y justificación. **No cambia `gold.score_output`**. Se registra como evidencia y puede ser aprobado por un supervisor en un flujo futuro.
- Todos los eventos quedan en historial (append-only). No usar notas con datos personales.
- La contraseña compartida es solo un control básico para demostración académica; para datos reales se requiere autenticación individual, autorización por roles, registro de acceso y revisión legal.
- Un **falso positivo real** solo puede etiquetarse cuando existe resultado de pago observado para el horizonte de predicción y evidencia de verificación; la corrección propuesta no equivale a esa etiqueta.

## Control adicional recomendado (siguiente etapa)

- Incorporar tabla de resultados observados (`actual_default`, `observation_end`, `verified_at`, `evidence_ref`) y emparejar cada resultado con `score_output_id`.
- Calcular falsos positivos en producción únicamente sobre casos con ventana de observación completa.
- Crear panel de auditoría: tasa FP/FN por grupo, diferencias de FPR/FNR, Brier/calibración, alertas por tamaño de muestra, trazabilidad de revisiones y tasa de desacuerdos.
- Ejecutar comparación experimental con/sin variables sensibles y evaluación de proxies, validación temporal y recalibración con prevalencia representativa. No aplicar ajustes automáticos sin evaluación.
- Verificar normativa aplicable según jurisdicción, protección de datos, explicabilidad y revisión humana antes de usar para decisiones reales de crédito.

## Seguridad y limitaciones

- La API existente sigue teniendo endpoints de lectura públicos y errores que pueden revelar detalles de conexión. Es una deuda técnica previa, no resuelta por este paquete.
- Los endpoints nuevos `/reviews` requieren `X-Review-Key`; si `REVIEW_API_KEY` falta, se cierran con HTTP 503.
- La clave de analista protege la interfaz en Streamlit, pero no sustituye autenticación empresarial.
- No adjuntar documentos ni información sensible al campo de texto; usar una referencia interna ficticia o autorizada.
- La migración no elimina ni actualiza filas existentes.
