# Cierre tecnico de NexaRisk (sin Power BI)

## Alcance
Arquitectura Medallion, scoring XGBoost V2, API FastAPI, persistencia Supabase, dashboard Streamlit, revision humana y aprobacion supervisora. El ZIP documenta la implementacion; el funcionamiento remoto no se volvio a verificar en esta auditoria.

## Resultados de V2 y V3
Fuente: `08_experimentos/v3/nexarisk_v3_experimento/comparacion_v2_v3.json`.

| Metrica | V2 | V3 |
|---|---:|---:|
| ROC-AUC | 0.7999 | 0.7911 |
| PR-AUC | 0.6915 | 0.6809 |
| Precision clase 1 | 0.6184 | 0.6023 |
| Recall clase 1 | 0.6123 | 0.6216 |
| F1 | 0.6153 | 0.6118 |
| FP | 567 | 616 |
| FN | 582 | 568 |

**Decision:** conservar V2; V3 no aprobado.

## Revision humana
El usuario reporto cinco observaciones y aprobaciones de supervision. Las observaciones no contienen resultados de incumplimiento observados verificados ni correcciones validadas de las 47 variables; no deben usarse para cambiar etiquetas. La base remota reporto cero registros en `credit_outcomes_verified`.

## Pruebas ejecutadas sobre el ZIP
- 13 pruebas locales superadas de 14 en el subconjunto de seis archivos (v3_gate, review_validation, supervisor, v3_experiment, artifacts, scoring_rules).
- `test_artifacts.py` no pudo cargar `model.pkl`: el ZIP incluye un puntero Git LFS de 134 bytes, no el modelo binario. Recuperar el objeto LFS en la computadora con `git lfs pull` antes de probar. No reemplazar el modelo por un artefacto experimental.
- Suite completa bloqueada durante recoleccion por ausencia de `psycopg` en el entorno de auditoria.
- Integracion remota con Render/Supabase no ejecutada en esta auditoria.

## Criterios de cierre
1. Sincronizar documentacion y JSON (incluido en el parche).
2. Proteger exportaciones y binarios experimentales (incluido en el parche).
3. En Windows: recuperar LFS, instalar dependencias y ejecutar pruebas; registrar resultados reales.
4. Verificar que Git no incluya datos exportados ni secretos.
5. Mantener V2 en produccion. Power BI fuera de alcance por decision del usuario.
