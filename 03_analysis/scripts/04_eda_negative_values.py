import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine


# ============================================================
# CONFIGURACIÓN
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[2]

OUTPUT_DIR = BASE_DIR / "03_analysis" / "outputs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_FILE = OUTPUT_DIR / "negative_values_eda_report.txt"

load_dotenv(BASE_DIR / ".env")

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError(
        "No se encontró DATABASE_URL en el archivo .env"
    )


# ============================================================
# CONEXIÓN
# ============================================================

engine = create_engine(DATABASE_URL)


# ============================================================
# CARGA DE SILVER
# ============================================================

query = """
SELECT
    c.id,
    c.limit_bal,
    c.sex,
    c.education,
    c.marriage,
    c.age,

    h.pay_0,
    h.pay_2,
    h.pay_3,
    h.pay_4,
    h.pay_5,
    h.pay_6,

    h.bill_amt1,
    h.bill_amt2,
    h.bill_amt3,
    h.bill_amt4,
    h.bill_amt5,
    h.bill_amt6,

    h.pay_amt1,
    h.pay_amt2,
    h.pay_amt3,
    h.pay_amt4,
    h.pay_amt5,
    h.pay_amt6,

    h.default_payment_next_month,

    h.bronze_id

FROM silver.clientes_credito c
INNER JOIN silver.comportamiento_crediticio h
    ON c.id = h.id
ORDER BY c.id;
"""

df = pd.read_sql(query, engine)


# ============================================================
# VARIABLES
# ============================================================

pay_status_cols = [
    "pay_0",
    "pay_2",
    "pay_3",
    "pay_4",
    "pay_5",
    "pay_6",
]

bill_cols = [
    "bill_amt1",
    "bill_amt2",
    "bill_amt3",
    "bill_amt4",
    "bill_amt5",
    "bill_amt6",
]

pay_amt_cols = [
    "pay_amt1",
    "pay_amt2",
    "pay_amt3",
    "pay_amt4",
    "pay_amt5",
    "pay_amt6",
]


# ============================================================
# REPORTE
# ============================================================

report = []

report.append("=" * 70)
report.append("EDA — SEGUNDA PARTE")
report.append("ANÁLISIS DE CÓDIGOS Y VALORES NEGATIVOS")
report.append("=" * 70)
report.append("")

report.append(f"Registros analizados: {len(df):,}")
report.append("")


# ============================================================
# 1. CÓDIGOS NEGATIVOS EN PAY_*
# ============================================================

report.append("=" * 70)
report.append("1. CÓDIGOS NEGATIVOS EN PAY_*")
report.append("=" * 70)
report.append("")

for col in pay_status_cols:

    negative = df[df[col] < 0]

    report.append(f"{col}")
    report.append("-" * 40)

    report.append(
        f"Total valores negativos: {len(negative):,}"
    )

    if len(negative) > 0:

        counts = (
            negative[col]
            .value_counts()
            .sort_index()
        )

        for value, count in counts.items():

            pct = count / len(df) * 100

            report.append(
                f"  {value}: {count:,} "
                f"({pct:.2f}%)"
            )

    report.append("")


# ============================================================
# 2. ANÁLISIS ESPECÍFICO DEL CÓDIGO -2
# ============================================================

report.append("=" * 70)
report.append("2. ANÁLISIS ESPECÍFICO DEL CÓDIGO -2")
report.append("=" * 70)
report.append("")

for col in pay_status_cols:

    mask = df[col] == -2

    count = mask.sum()

    report.append(f"{col} = -2")
    report.append("-" * 40)
    report.append(f"Registros: {count:,}")

    if count > 0:

        subset = df.loc[mask]

        default_rate = (
            subset["default_payment_next_month"]
            .mean() * 100
        )

        report.append(
            f"Default dentro del grupo: "
            f"{default_rate:.2f}%"
        )

        month_number = {
            "pay_0": 1,
            "pay_2": 2,
            "pay_3": 3,
            "pay_4": 4,
            "pay_5": 5,
            "pay_6": 6,
        }[col]

        bill_col = f"bill_amt{month_number}"
        pay_amt_col = f"pay_amt{month_number}"

        report.append(
            f"Promedio {bill_col}: "
            f"{subset[bill_col].mean():,.2f}"
        )

        report.append(
            f"Mediana {bill_col}: "
            f"{subset[bill_col].median():,.2f}"
        )

        report.append(
            f"Promedio {pay_amt_col}: "
            f"{subset[pay_amt_col].mean():,.2f}"
        )

        report.append(
            f"Mediana {pay_amt_col}: "
            f"{subset[pay_amt_col].median():,.2f}"
        )

    report.append("")


# ============================================================
# 3. VALORES NEGATIVOS EN BILL_AMT
# ============================================================

report.append("=" * 70)
report.append("3. VALORES NEGATIVOS EN BILL_AMT")
report.append("=" * 70)
report.append("")

for col in bill_cols:

    mask = df[col] < 0
    count = mask.sum()

    report.append(f"{col}")
    report.append("-" * 40)

    report.append(
        f"Negativos: {count:,}"
    )

    report.append(
        f"Porcentaje: {count / len(df) * 100:.2f}%"
    )

    if count > 0:

        subset = df.loc[mask]

        report.append(
            f"Mínimo: {subset[col].min():,.2f}"
        )

        report.append(
            f"Promedio: {subset[col].mean():,.2f}"
        )

        report.append(
            f"Mediana: {subset[col].median():,.2f}"
        )

        report.append(
            f"Default: "
            f"{subset['default_payment_next_month'].mean() * 100:.2f}%"
        )

    report.append("")


# ============================================================
# 4. VALORES NEGATIVOS EN PAY_AMT
# ============================================================

report.append("=" * 70)
report.append("4. VALORES NEGATIVOS EN PAY_AMT")
report.append("=" * 70)
report.append("")

total_negative_pay_amt = 0

for col in pay_amt_cols:

    mask = df[col] < 0
    count = mask.sum()

    total_negative_pay_amt += count

    report.append(f"{col}")
    report.append("-" * 40)

    report.append(
        f"Negativos: {count:,}"
    )

    report.append(
        f"Porcentaje: {count / len(df) * 100:.2f}%"
    )

    if count > 0:

        subset = df.loc[mask]

        report.append(
            f"Mínimo: {subset[col].min():,.2f}"
        )

        report.append(
            f"Promedio: {subset[col].mean():,.2f}"
        )

        report.append(
            f"Mediana: {subset[col].median():,.2f}"
        )

        report.append(
            f"Default: "
            f"{subset['default_payment_next_month'].mean() * 100:.2f}%"
        )

    report.append("")


report.append(
    f"TOTAL DE VALORES NEGATIVOS EN PAY_AMT: "
    f"{total_negative_pay_amt:,}"
)

report.append("")


# ============================================================
# 5. BILL_AMT NEGATIVO VS PAY_* CORRESPONDIENTE
# ============================================================

report.append("=" * 70)
report.append("5. BILL_AMT NEGATIVO VS PAY_* CORRESPONDIENTE")
report.append("=" * 70)
report.append("")

mapping = {
    "bill_amt1": "pay_0",
    "bill_amt2": "pay_2",
    "bill_amt3": "pay_3",
    "bill_amt4": "pay_4",
    "bill_amt5": "pay_5",
    "bill_amt6": "pay_6",
}

for bill_col, pay_col in mapping.items():

    mask = df[bill_col] < 0

    subset = df.loc[mask]

    report.append(
        f"{bill_col} < 0 → {pay_col}"
    )
    report.append("-" * 40)

    if len(subset) == 0:

        report.append("No existen registros.")
        report.append("")
        continue

    counts = (
        subset[pay_col]
        .value_counts()
        .sort_index()
    )

    for value, count in counts.items():

        pct = count / len(subset) * 100

        report.append(
            f"{value}: {count:,} "
            f"({pct:.2f}%)"
        )

    report.append("")


# ============================================================
# 6. CLIENTES CON MÚLTIPLES BILL_AMT NEGATIVOS
# ============================================================

report.append("=" * 70)
report.append("6. NÚMERO DE MESES CON BILL_AMT NEGATIVO")
report.append("=" * 70)
report.append("")

df["negative_bill_months"] = (
    df[bill_cols] < 0
).sum(axis=1)

distribution = (
    df["negative_bill_months"]
    .value_counts()
    .sort_index()
)

for months, count in distribution.items():

    pct = count / len(df) * 100

    report.append(
        f"{months} meses negativos: "
        f"{count:,} ({pct:.2f}%)"
    )

report.append("")


# ============================================================
# 7. CLIENTES CON MÚLTIPLES PAY_* = -2
# ============================================================

report.append("=" * 70)
report.append("7. NÚMERO DE MESES CON PAY_* = -2")
report.append("=" * 70)
report.append("")

df["pay_minus2_months"] = (
    df[pay_status_cols] == -2
).sum(axis=1)

distribution = (
    df["pay_minus2_months"]
    .value_counts()
    .sort_index()
)

for months, count in distribution.items():

    pct = count / len(df) * 100

    report.append(
        f"{months} meses con -2: "
        f"{count:,} ({pct:.2f}%)"
    )

report.append("")


# ============================================================
# 8. CORROBORACIÓN DE LA HIPÓTESIS PAY_* = -2
# ============================================================

report.append("=" * 70)
report.append("8. CORROBORACIÓN DE LA HIPÓTESIS PAY_* = -2")
report.append("=" * 70)
report.append("")

period_mapping = {
    "pay_0": ("bill_amt1", "pay_amt1"),
    "pay_2": ("bill_amt2", "pay_amt2"),
    "pay_3": ("bill_amt3", "pay_amt3"),
    "pay_4": ("bill_amt4", "pay_amt4"),
    "pay_5": ("bill_amt5", "pay_amt5"),
    "pay_6": ("bill_amt6", "pay_amt6"),
}

for pay_col, (bill_col, pay_amt_col) in period_mapping.items():

    subset = df[df[pay_col] == -2].copy()

    report.append(f"{pay_col} = -2")
    report.append("-" * 40)

    total = len(subset)

    if total == 0:

        report.append("No existen registros.")
        report.append("")
        continue

    # --------------------------------------------------------
    # Las categorías son mutuamente excluyentes y exhaustivas
    # para valores no nulos.
    # --------------------------------------------------------

    conditions = {
        "A: BILL_AMT <= 0 y PAY_AMT = 0":
            (subset[bill_col] <= 0) &
            (subset[pay_amt_col] == 0),

        "B: BILL_AMT <= 0 y PAY_AMT > 0":
            (subset[bill_col] <= 0) &
            (subset[pay_amt_col] > 0),

        "C: BILL_AMT > 0 y PAY_AMT = 0":
            (subset[bill_col] > 0) &
            (subset[pay_amt_col] == 0),

        "D: BILL_AMT > 0 y PAY_AMT > 0":
            (subset[bill_col] > 0) &
            (subset[pay_amt_col] > 0),
    }

    categorized = pd.Series(False, index=subset.index)

    for label, condition in conditions.items():

        count = condition.sum()
        pct = count / total * 100

        categorized = categorized | condition

        report.append(
            f"{label}: {count:,} ({pct:.2f}%)"
        )

    # --------------------------------------------------------
    # Verificación de registros no clasificados
    # --------------------------------------------------------

    not_categorized = (~categorized).sum()

    report.append(
        f"Registros no clasificados: "
        f"{not_categorized:,}"
    )

    report.append("")

    # --------------------------------------------------------
    # Estadísticos descriptivos
    # --------------------------------------------------------

    report.append(
        f"Promedio {bill_col}: "
        f"{subset[bill_col].mean():,.2f}"
    )

    report.append(
        f"Mediana {bill_col}: "
        f"{subset[bill_col].median():,.2f}"
    )

    report.append(
        f"Promedio {pay_amt_col}: "
        f"{subset[pay_amt_col].mean():,.2f}"
    )

    report.append(
        f"Mediana {pay_amt_col}: "
        f"{subset[pay_amt_col].median():,.2f}"
    )

    report.append("")


# ============================================================
# 9. CLIENTES CON PAY_* = -2 EN LOS 6 MESES
# ============================================================

report.append("=" * 70)
report.append("9. CLIENTES CON PAY_* = -2 EN LOS 6 MESES")
report.append("=" * 70)
report.append("")

all_minus2 = (
    df[pay_status_cols] == -2
).all(axis=1)

subset_all_minus2 = df[all_minus2].copy()

report.append(
    f"Clientes con -2 en los 6 meses: "
    f"{len(subset_all_minus2):,}"
)

if len(subset_all_minus2) > 0:

    # Convertimos los seis meses a una sola serie para
    # obtener estadísticos globales sobre BILL_AMT y PAY_AMT.

    bill_values = subset_all_minus2[bill_cols].stack()
    pay_values = subset_all_minus2[pay_amt_cols].stack()

    report.append(
        f"Promedio BILL_AMT1-6: "
        f"{bill_values.mean():,.2f}"
    )

    report.append(
        f"Mediana BILL_AMT1-6: "
        f"{bill_values.median():,.2f}"
    )

    report.append(
        f"Promedio PAY_AMT1-6: "
        f"{pay_values.mean():,.2f}"
    )

    report.append(
        f"Mediana PAY_AMT1-6: "
        f"{pay_values.median():,.2f}"
    )

    report.append(
        f"Default: "
        f"{subset_all_minus2['default_payment_next_month'].mean() * 100:.2f}%"
    )

report.append("")


# ============================================================
# 10. INTERPRETACIÓN DE LA CORROBORACIÓN
# ============================================================

report.append("=" * 70)
report.append("10. INTERPRETACIÓN DE LA CORROBORACIÓN")
report.append("=" * 70)
report.append("")

report.append(
    "Este análisis cruza cada código PAY_* = -2 con "
    "su BILL_AMT y PAY_AMT correspondiente."
)

report.append(
    "Las categorías de la sección 8 permiten identificar "
    "la combinación observada entre el importe de factura "
    "y el importe pagado."
)

report.append(
    "La evidencia obtenida se utiliza para evaluar si "
    "el patrón observado es compatible con la hipótesis "
    "de baja o nula actividad."
)

report.append(
    "Esta evidencia no constituye una definición oficial "
    "del código -2 en la documentación UCI."
)

report.append(
    "El código -2 se conserva en Silver y no se transforma "
    "automáticamente a 0."
)

report.append(
    "Su representación definitiva para el modelo se "
    "evaluará durante Feature Engineering."
)

report.append("")

report.append(
    "Los valores negativos de BILL_AMT tampoco se transforman "
    "automáticamente a cero en esta etapa."
)

report.append(
    "Su tratamiento para el modelo se evaluará posteriormente "
    "mediante Feature Engineering."
)

report.append("")


# ============================================================
# GUARDAR REPORTE
# ============================================================

OUTPUT_FILE.write_text(
    "\n".join(report),
    encoding="utf-8"
)

print("EDA SEGUNDA PARTE FINALIZADO")
print(f"Reporte generado en: {OUTPUT_FILE}")