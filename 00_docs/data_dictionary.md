# Diccionario de Datos

## Proyecto Productivo IIIA

## 1. Fuente

Archivo:

`01_data/raw/credit_card_clients_raw.csv`

Registros analizados:

33,377

Columnas:

30

Separador:

`;`

Variable objetivo:

`default payment next month`

---

# 2. Identificadores

| Campo | Tipo RAW | Descripción | Tratamiento inicial |
|---|---|---|---|
| bronze_record_id | int64 | Identificador técnico del registro Bronze | Se conserva |
| ID | int64 | Identificador del cliente | Se conserva como identificador de negocio |
| source_parent_id | int64 | Identificador de trazabilidad de origen | Se conserva |
| source_type | str | Tipo de fuente | Se conserva |
| record_origin | str | Origen del registro | Se conserva |

---

# 3. Datos del cliente

| Campo | Tipo RAW | Descripción | Observación |
|---|---|---|---|
| LIMIT_BAL | float64 | Límite de crédito | Presenta 90 nulos y valores extremos |
| SEX | int64 | Código categórico | Existen valores 1, 2 y 3 |
| EDUCATION | int64 | Código categórico | Existen valores 0 a 7 |
| MARRIAGE | int64 | Código categórico | Existen valores 0 a 4 |
| AGE | float64 | Edad | Presenta 80 nulos; rango observado 21-95 |

---

# 4. Comportamiento de pago

| Campo | Tipo RAW | Descripción | Observación |
|---|---|---|---|
| PAY_0 | int64 | Estado de pago del periodo | Valores -2 a 8 |
| PAY_2 | int64 | Estado de pago del periodo | Valores -2 a 8 |
| PAY_3 | int64 | Estado de pago del periodo | Valores -2 a 8 |
| PAY_4 | int64 | Estado de pago del periodo | Valores -2 a 8 |
| PAY_5 | int64 | Estado de pago del periodo | Valores -2 a 8 |
| PAY_6 | int64 | Estado de pago del periodo | Valores -2 a 8 |

Los códigos de estas variables deben conservarse inicialmente y documentarse antes de aplicar transformaciones.

---

# 5. Montos facturados

| Campo | Tipo RAW | Descripción | Observación |
|---|---|---|---|
| BILL_AMT1 | float64 | Monto facturado periodo 1 | Presenta valores negativos |
| BILL_AMT2 | float64 | Monto facturado periodo 2 | Presenta valores negativos |
| BILL_AMT3 | float64 | Monto facturado periodo 3 | Presenta 110 nulos y valores negativos |
| BILL_AMT4 | float64 | Monto facturado periodo 4 | Presenta valores negativos |
| BILL_AMT5 | float64 | Monto facturado periodo 5 | Presenta valores negativos |
| BILL_AMT6 | float64 | Monto facturado periodo 6 | Presenta valores negativos |

Los valores negativos no serán eliminados automáticamente.

---

# 6. Montos pagados

| Campo | Tipo RAW | Descripción | Observación |
|---|---|---|---|
| PAY_AMT1 | float64 | Monto pagado periodo 1 | Presenta valores extremos |
| PAY_AMT2 | float64 | Monto pagado periodo 2 | Presenta 100 nulos y valores extremos |
| PAY_AMT3 | float64 | Monto pagado periodo 3 | Presenta valores extremos |
| PAY_AMT4 | float64 | Monto pagado periodo 4 | Presenta valores extremos |
| PAY_AMT5 | float64 | Monto pagado periodo 5 | Presenta valores extremos |
| PAY_AMT6 | float64 | Monto pagado periodo 6 | Presenta valores extremos |

Los valores extremos no serán eliminados automáticamente.

---

# 7. Variable objetivo

| Campo | Tipo RAW | Descripción |
|---|---|---|
| default payment next month | int64 | Indicador de incumplimiento en el siguiente periodo |

Distribución observada:

- 0: 23,364 registros (70.00%)
- 1: 10,013 registros (30.00%)

---

# 8. Calidad de datos observada

## Valores nulos

| Campo | Nulos |
|---|---:|
| raw_quality_flags | 32,853 |
| BILL_AMT3 | 110 |
| PAY_AMT2 | 100 |
| LIMIT_BAL | 90 |
| AGE | 80 |

## Duplicados

Duplicados exactos:

`0`

IDs duplicados:

`0`

---

# 9. Criterios iniciales de transformación

Las siguientes reglas quedan pendientes de validación:

1. No modificar la fuente RAW.
2. Bronze conservará la información de origen.
3. Silver realizará tipificación, validación y limpieza documentada.
4. No convertir automáticamente valores negativos de BILL_AMT a cero.
5. No eliminar automáticamente outliers de PAY_AMT.
6. No establecer límites arbitrarios para LIMIT_BAL.
7. No recodificar automáticamente SEX, EDUCATION o MARRIAGE.
8. No transformar PAY_0 a PAY_6 sin documentar primero el significado de sus códigos.
9. Las decisiones de imputación de nulos serán documentadas.
10. Las transformaciones orientadas específicamente al modelo pertenecerán a Gold/Feature Engineering.

---

# 10. Regla de trazabilidad

Toda transformación aplicada a los datos debe poder responder:

- qué columna fue modificada;
- qué regla se aplicó;
- por qué se aplicó;
- cuántos registros fueron afectados;
- cuándo se ejecutó;
- qué proceso la ejecutó.