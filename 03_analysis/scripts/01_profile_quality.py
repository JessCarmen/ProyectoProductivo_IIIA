from pathlib import Path
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]

RAW_FILE = (
    PROJECT_ROOT
    / "01_data"
    / "raw"
    / "credit_card_clients_raw.csv"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "03_analysis"
    / "outputs"
)

OUTPUT_FILE = OUTPUT_DIR / "raw_quality_analysis.txt"


CATEGORICAL_COLUMNS = [
    "SEX",
    "EDUCATION",
    "MARRIAGE",
    "PAY_0",
    "PAY_2",
    "PAY_3",
    "PAY_4",
    "PAY_5",
    "PAY_6",
]

BILL_COLUMNS = [
    "BILL_AMT1",
    "BILL_AMT2",
    "BILL_AMT3",
    "BILL_AMT4",
    "BILL_AMT5",
    "BILL_AMT6",
]

PAYMENT_COLUMNS = [
    "PAY_AMT1",
    "PAY_AMT2",
    "PAY_AMT3",
    "PAY_AMT4",
    "PAY_AMT5",
    "PAY_AMT6",
]


def section(title):
    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)


print("=" * 70)
print("PROYECTO PRODUCTIVO IIIA")
print("ANÁLISIS DE CALIDAD DE LA FUENTE RAW")
print("=" * 70)

if not RAW_FILE.exists():
    raise FileNotFoundError(
        f"No se encontró el archivo:\n{RAW_FILE}"
    )

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

print("\nCargando RAW...")
df = pd.read_csv(RAW_FILE, sep=";")
print("RAW cargado correctamente.")


# ==========================================================
# 1. DISTRIBUCIÓN DE VARIABLES CODIFICADAS
# ==========================================================

section("1. DISTRIBUCIÓN DE VARIABLES CODIFICADAS")

for column in CATEGORICAL_COLUMNS:

    print(f"\n{column}")
    print("-" * 50)

    counts = (
        df[column]
        .value_counts(dropna=False)
        .sort_index()
    )

    total = len(df)

    print(
        f"{'Valor':>10} "
        f"{'Registros':>15} "
        f"{'Porcentaje':>15}"
    )

    print("-" * 45)

    for value, count in counts.items():

        percentage = count / total * 100

        print(
            f"{str(value):>10} "
            f"{count:15,} "
            f"{percentage:14.2f}%"
        )


# ==========================================================
# 2. VALORES NEGATIVOS EN BILL_AMT
# ==========================================================

section("2. VALORES NEGATIVOS EN BILL_AMT")

for column in BILL_COLUMNS:

    negative_count = (df[column] < 0).sum()

    zero_count = (df[column] == 0).sum()

    positive_count = (df[column] > 0).sum()

    total = df[column].notna().sum()

    print(f"\n{column}")

    print(f"Negativos : {negative_count:,}")
    print(f"Ceros     : {zero_count:,}")
    print(f"Positivos : {positive_count:,}")
    print(f"No nulos  : {total:,}")


# ==========================================================
# 3. VALORES EXTREMOS EN PAY_AMT
# ==========================================================

section("3. VALORES EXTREMOS EN PAY_AMT")

for column in PAYMENT_COLUMNS:

    print(f"\n{column}")

    print(
        f"Máximo: "
        f"{df[column].max():,.2f}"
    )

    print(
        f"Percentil 99: "
        f"{df[column].quantile(0.99):,.2f}"
    )

    print(
        f"Percentil 99.5: "
        f"{df[column].quantile(0.995):,.2f}"
    )

    print(
        f"Percentil 99.9: "
        f"{df[column].quantile(0.999):,.2f}"
    )


# ==========================================================
# 4. VALORES EXTREMOS DE LIMIT_BAL
# ==========================================================

section("4. VALORES EXTREMOS DE LIMIT_BAL")

print(
    df["LIMIT_BAL"]
    .describe(
        percentiles=[
            0.01,
            0.05,
            0.25,
            0.50,
            0.75,
            0.95,
            0.99,
            0.995,
            0.999,
        ]
    )
    .to_string()
)


# ==========================================================
# 5. DISTRIBUCIÓN DE AGE
# ==========================================================

section("5. DISTRIBUCIÓN DE AGE")

print(
    df["AGE"]
    .describe(
        percentiles=[
            0.01,
            0.05,
            0.25,
            0.50,
            0.75,
            0.95,
            0.99,
            0.995,
            0.999,
        ]
    )
    .to_string()
)


# ==========================================================
# 6. TARGET PORCENTUAL
# ==========================================================

section("6. DISTRIBUCIÓN DE LA VARIABLE OBJETIVO")

target = "default payment next month"

target_counts = (
    df[target]
    .value_counts()
    .sort_index()
)

total = len(df)

for value, count in target_counts.items():

    percentage = count / total * 100

    print(
        f"Valor {value}: "
        f"{count:,} registros "
        f"({percentage:.2f}%)"
    )


# ==========================================================
# 7. GUARDAR RESULTADO
# ==========================================================

section("7. GUARDANDO RESULTADO")

with open(
    OUTPUT_FILE,
    "w",
    encoding="utf-8"
) as file:

    file.write(
        "PROYECTO PRODUCTIVO IIIA\n"
    )

    file.write(
        "ANÁLISIS DE CALIDAD DE LA FUENTE RAW\n"
    )

    file.write(
        "=" * 70 + "\n\n"
    )

    for column in CATEGORICAL_COLUMNS:

        file.write(
            f"\n{column}\n"
        )

        file.write(
            "-" * 50 + "\n"
        )

        counts = (
            df[column]
            .value_counts(dropna=False)
            .sort_index()
        )

        for value, count in counts.items():

            percentage = (
                count / len(df) * 100
            )

            file.write(
                f"{value}: "
                f"{count:,} "
                f"({percentage:.2f}%)\n"
            )

    file.write(
        "\n\nVALORES NEGATIVOS EN BILL_AMT\n"
    )

    file.write(
        "-" * 70 + "\n"
    )

    for column in BILL_COLUMNS:

        negative_count = (
            df[column] < 0
        ).sum()

        zero_count = (
            df[column] == 0
        ).sum()

        positive_count = (
            df[column] > 0
        ).sum()

        file.write(
            f"\n{column}\n"
        )

        file.write(
            f"Negativos: {negative_count:,}\n"
        )

        file.write(
            f"Ceros: {zero_count:,}\n"
        )

        file.write(
            f"Positivos: {positive_count:,}\n"
        )

    file.write(
        "\n\nVALORES EXTREMOS EN PAY_AMT\n"
    )

    file.write(
        "-" * 70 + "\n"
    )

    for column in PAYMENT_COLUMNS:

        file.write(
            f"\n{column}\n"
        )

        file.write(
            f"Máximo: "
            f"{df[column].max():,.2f}\n"
        )

        file.write(
            f"P99: "
            f"{df[column].quantile(0.99):,.2f}\n"
        )

        file.write(
            f"P99.5: "
            f"{df[column].quantile(0.995):,.2f}\n"
        )

        file.write(
            f"P99.9: "
            f"{df[column].quantile(0.999):,.2f}\n"
        )

print(
    f"\nResultado guardado en:\n"
    f"{OUTPUT_FILE}"
)

print(
    "\nLa fuente RAW no fue modificada."
)