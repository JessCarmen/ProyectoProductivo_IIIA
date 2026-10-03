# Power BI - fuente oficial de visualizacion

Usar `gold.vw_portfolio_scoring_current` como fuente de cartera. No recalcular la PD en Power BI.

## Campos principales
- id
- probability_default
- prediction
- risk_level
- recommendation
- fecha_score
- modelo_version
- limit_bal, age, pay_0, pay_max_delay, recent_delay_months, consecutive_delay_months

## Visuales recomendados
1. KPIs: total cartera, PD promedio, prediction=1, Alto, Critico.
2. Semaforo: cantidad por risk_level.
3. Tabla operativa: ID, PD, riesgo, limite, atrasos, recomendacion.
4. Distribucion de PD.
5. Riesgo por edad / limite de credito.

La cartera validada actualmente tiene 33,377 IDs unicos y 0 nulos criticos en score_output.
