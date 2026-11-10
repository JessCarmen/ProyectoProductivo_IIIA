# Guion breve de defensa NexaRisk

## 1. Problema y objetivo
Apoyar la priorizacion de gestion crediticia mediante scoring reproducible y revision humana auditada. No sustituir decisiones humanas por clasificaciones automaticas.

## 2. Arquitectura
Datos historicos -> Bronze/Silver/Gold/Gold_ML -> XGBoost V2 -> score_output en Supabase -> FastAPI en Render -> Streamlit NexaRisk.

## 3. Metodologia
Variables historicas, separacion train/validation/test, evaluacion de discriminacion, precision, recall, calibracion y matriz de confusion. Evitar filtracion de etiquetas del conjunto de prueba.

## 4. Demostracion
Mostrar resumen de cartera, Cliente 360, formulario de observacion del analista y decision independiente del supervisor. No modificar registros en vivo solo para la presentacion.

## 5. Revision humana
Cinco observaciones aprobadas segun el registro reportado por el usuario. Aprobacion significa validacion del flujo, no prueba de que el modelo mejoro ni que la prediccion debia invertirse.

## 6. V2 vs V3
Usar la tabla de docs/CIERRE_TECNICO_NEXARISK.md y el JSON como fuente. V3 mejora ligeramente recall, empeora otras metricas; se decide no promoverlo.

## 7. Limitaciones y trabajo futuro
No hay outcomes operativos verificados para aprender de revisiones. Hacen falta correcciones de variables respaldadas, seguimiento temporal, evaluacion independiente, auditoria de sesgos y controles de acceso. Power BI se abordara posteriormente.

## 8. Cierre
El aporte es un sistema integrado con gobierno humano y experimentacion controlada; no se afirma mejora estadistica por cinco aprobaciones.
