# ============================================================
# PROYECTO PRODUCTIVO IIIA
# ANÁLISIS EXPLORATORIO DE DATOS (EDA)
# CAPA SILVER
# ============================================================

import os
from pathlib import Path

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import psycopg2
from dotenv import load_dotenv


# ============================================================
# 1. CONFIGURACIÓN
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[2]

OUTPUT_DIR = BASE_DIR / "03_analysis" / "outputs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

load_dotenv(BASE_DIR / ".env")

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError(
        "No se encontró DATABASE_URL en el archivo .env"
    )


# ============================================================
# 2. CONEXIÓN A SUPABASE
# ============================================================

def get_connection():
    return psycopg2.connect(DATABASE_URL)


# ============================================================
# 3. LECTURA DE SILVER
# ============================================================

def load_silver_data():

    conn = get_connection()

    try:

        clientes = pd.read_sql_query(
            """
            SELECT
                id,
                limit_bal,
                sex,
                education,
                marriage,
                age,
                bronze_id,
                fecha_carga
            FROM silver.clientes_credito
            """,
            conn
        )

        comportamiento = pd.read_sql_query(
            """
            SELECT
                id,
                pay_0,
                pay_2,
                pay_3,
                pay_4,
                pay_5,
                pay_6,
                bill_amt1,
                bill_amt2,
                bill_amt3,
                bill_amt4,
                bill_amt5,
                bill_amt6,
                pay_amt1,
                pay_amt2,
                pay_amt3,
                pay_amt4,
                pay_amt5,
                pay_amt6,
                default_payment_next_month,
                bronze_id,
                fecha_carga
            FROM silver.comportamiento_crediticio
            """,
            conn
        )

    finally:
        conn.close()

    # ========================================================
    # UNIÓN DE LAS DOS TABLAS SILVER
    # ========================================================

    df = clientes.merge(
        comportamiento,
        on="id",
        how="inner",
        suffixes=("_cliente", "_comportamiento")
    )

    return clientes, comportamiento, df


# ============================================================
# 4. REPORTE GENERAL
# ============================================================

def generate_general_report(clientes, comportamiento, df):

    report_path = OUTPUT_DIR / "silver_eda_report.txt"

    with open(report_path, "w", encoding="utf-8") as f:

        f.write("=" * 70 + "\n")
        f.write("PROYECTO PRODUCTIVO IIIA\n")
        f.write("ANÁLISIS EXPLORATORIO DE DATOS - CAPA SILVER\n")
        f.write("=" * 70 + "\n\n")

        # ----------------------------------------------------
        # Estructura
        # ----------------------------------------------------

        f.write("1. ESTRUCTURA DE LOS DATOS\n")
        f.write("-" * 70 + "\n")

        f.write(
            f"Clientes Silver: {len(clientes):,}\n"
        )

        f.write(
            f"Comportamientos Silver: {len(comportamiento):,}\n"
        )

        f.write(
            f"Dataset EDA: {len(df):,} registros\n"
        )

        f.write(
            f"Variables disponibles: {len(df.columns)}\n\n"
        )

        # ----------------------------------------------------
        # Duplicados
        # ----------------------------------------------------

        f.write("2. DUPLICADOS\n")
        f.write("-" * 70 + "\n")

        f.write(
            f"IDs duplicados: "
            f"{df['id'].duplicated().sum()}\n\n"
        )

        # ----------------------------------------------------
        # Nulos
        # ----------------------------------------------------

        f.write("3. VALORES FALTANTES\n")
        f.write("-" * 70 + "\n")

        nulls = df.isnull().sum()
        nulls = nulls[nulls > 0]

        if len(nulls) == 0:
            f.write("No se encontraron valores faltantes.\n\n")
        else:
            f.write(
                nulls.to_string()
            )
            f.write("\n\n")

        # ----------------------------------------------------
        # Target
        # ----------------------------------------------------

        f.write("4. DISTRIBUCIÓN DEL TARGET\n")
        f.write("-" * 70 + "\n")

        target = (
            df["default_payment_next_month"]
            .value_counts()
            .sort_index()
        )

        target_pct = (
            df["default_payment_next_month"]
            .value_counts(normalize=True)
            .sort_index() * 100
        )

        for value in target.index:

            f.write(
                f"Target {value}: "
                f"{target[value]:,} registros "
                f"({target_pct[value]:.2f}%)\n"
            )

        f.write("\n")

        # ----------------------------------------------------
        # Variables demográficas
        # ----------------------------------------------------

        f.write("5. VARIABLES DEMOGRÁFICAS\n")
        f.write("-" * 70 + "\n")

        f.write("\nSEX\n")
        f.write(
            df["sex"]
            .value_counts()
            .sort_index()
            .to_string()
        )

        f.write("\n\nEDUCATION\n")
        f.write(
            df["education"]
            .value_counts()
            .sort_index()
            .to_string()
        )

        f.write("\n\nMARRIAGE\n")
        f.write(
            df["marriage"]
            .value_counts()
            .sort_index()
            .to_string()
        )

        f.write("\n\nAGE\n")
        f.write(
            df["age"]
            .describe()
            .round(2)
            .to_string()
        )

        f.write("\n\n")

        # ----------------------------------------------------
        # LIMIT_BAL
        # ----------------------------------------------------

        f.write("6. LIMIT_BAL\n")
        f.write("-" * 70 + "\n")

        f.write(
            df["limit_bal"]
            .describe(
                percentiles=[
                    0.25,
                    0.50,
                    0.75,
                    0.90,
                    0.95,
                    0.99
                ]
            )
            .round(2)
            .to_string()
        )

        f.write("\n\n")

        # ----------------------------------------------------
        # Estados de pago
        # ----------------------------------------------------

        f.write("7. ESTADOS DE PAGO\n")
        f.write("-" * 70 + "\n")

        pay_status_cols = [
            "pay_0",
            "pay_2",
            "pay_3",
            "pay_4",
            "pay_5",
            "pay_6"
        ]

        for col in pay_status_cols:

            f.write(f"\n{col}\n")

            f.write(
                df[col]
                .value_counts()
                .sort_index()
                .to_string()
            )

            f.write("\n")

        f.write("\n")

        # ----------------------------------------------------
        # BILL_AMT
        # ----------------------------------------------------

        f.write("8. MONTOS FACTURADOS\n")
        f.write("-" * 70 + "\n")

        bill_cols = [
            f"bill_amt{i}"
            for i in range(1, 7)
        ]

        f.write(
            df[bill_cols]
            .describe()
            .round(2)
            .to_string()
        )

        f.write("\n\n")

        # ----------------------------------------------------
        # PAY_AMT
        # ----------------------------------------------------

        f.write("9. MONTOS PAGADOS\n")
        f.write("-" * 70 + "\n")

        pay_amt_cols = [
            f"pay_amt{i}"
            for i in range(1, 7)
        ]

        f.write(
            df[pay_amt_cols]
            .describe()
            .round(2)
            .to_string()
        )

        f.write("\n\n")

        # ----------------------------------------------------
        # Correlaciones numéricas
        # ----------------------------------------------------

        f.write("10. CORRELACIONES CON EL TARGET\n")
        f.write("-" * 70 + "\n")

        numeric_cols = df.select_dtypes(
            include=np.number
        ).columns

        correlations = (
            df[numeric_cols]
            .corr()["default_payment_next_month"]
            .drop("default_payment_next_month")
            .sort_values()
        )

        f.write(
            correlations.round(4).to_string()
        )

        f.write("\n\n")

        # ----------------------------------------------------
        # Default por variables categóricas
        # ----------------------------------------------------

        f.write("11. TASA DE DEFAULT POR VARIABLE CATEGÓRICA\n")
        f.write("-" * 70 + "\n")

        categorical_cols = [
            "sex",
            "education",
            "marriage"
        ]

        for col in categorical_cols:

            f.write(f"\n{col.upper()}\n")

            default_rate = (
                df.groupby(col)["default_payment_next_month"]
                .agg(["count", "mean"])
            )

            default_rate["default_pct"] = (
                default_rate["mean"] * 100
            )

            f.write(
                default_rate[
                    ["count", "default_pct"]
                ]
                .round(2)
                .to_string()
            )

            f.write("\n")

        # ----------------------------------------------------
        # Default por estado de pago
        # ----------------------------------------------------

        f.write("\n12. DEFAULT SEGÚN ESTADOS DE PAGO\n")
        f.write("-" * 70 + "\n")

        for col in pay_status_cols:

            f.write(f"\n{col.upper()}\n")

            default_rate = (
                df.groupby(col)["default_payment_next_month"]
                .agg(["count", "mean"])
            )

            default_rate["default_pct"] = (
                default_rate["mean"] * 100
            )

            f.write(
                default_rate[
                    ["count", "default_pct"]
                ]
                .round(2)
                .to_string()
            )

            f.write("\n")

    return report_path


# ============================================================
# 5. GRÁFICOS
# ============================================================

def create_target_chart(df):

    counts = (
        df["default_payment_next_month"]
        .value_counts()
        .sort_index()
    )

    plt.figure(figsize=(7, 5))

    plt.bar(
        counts.index.astype(str),
        counts.values
    )

    plt.title(
        "Distribución del Default"
    )

    plt.xlabel(
        "Default Payment Next Month"
    )

    plt.ylabel(
        "Cantidad de clientes"
    )

    plt.tight_layout()

    plt.savefig(
        OUTPUT_DIR / "target_distribution.png",
        dpi=150
    )

    plt.close()


# ============================================================

def create_age_chart(df):

    plt.figure(figsize=(8, 5))

    plt.hist(
        df["age"],
        bins=25
    )

    plt.title(
        "Distribución de Edad"
    )

    plt.xlabel("Edad")

    plt.ylabel("Cantidad de clientes")

    plt.tight_layout()

    plt.savefig(
        OUTPUT_DIR / "age_distribution.png",
        dpi=150
    )

    plt.close()


# ============================================================

def create_limit_chart(df):

    plt.figure(figsize=(8, 5))

    plt.hist(
        df["limit_bal"],
        bins=40
    )

    plt.title(
        "Distribución de LIMIT_BAL"
    )

    plt.xlabel(
        "Límite de crédito"
    )

    plt.ylabel(
        "Cantidad de clientes"
    )

    plt.tight_layout()

    plt.savefig(
        OUTPUT_DIR / "limit_bal_distribution.png",
        dpi=150
    )

    plt.close()


# ============================================================

def create_pay_status_chart(df):

    pay_cols = [
        "pay_0",
        "pay_2",
        "pay_3",
        "pay_4",
        "pay_5",
        "pay_6"
    ]

    totals = [
        (df[col] > 0).sum()
        for col in pay_cols
    ]

    plt.figure(figsize=(9, 5))

    plt.bar(
        pay_cols,
        totals
    )

    plt.title(
        "Cantidad de clientes con estado de pago > 0"
    )

    plt.xlabel(
        "Mes"
    )

    plt.ylabel(
        "Cantidad"
    )

    plt.tight_layout()

    plt.savefig(
        OUTPUT_DIR / "pay_status_distribution.png",
        dpi=150
    )

    plt.close()


# ============================================================

def create_bill_chart(df):

    bill_cols = [
        f"bill_amt{i}"
        for i in range(1, 7)
    ]

    means = [
        df[col].mean()
        for col in bill_cols
    ]

    plt.figure(figsize=(9, 5))

    plt.bar(
        bill_cols,
        means
    )

    plt.title(
        "Promedio de Montos Facturados"
    )

    plt.xlabel(
        "Mes"
    )

    plt.ylabel(
        "Promedio BILL_AMT"
    )

    plt.xticks(rotation=45)

    plt.tight_layout()

    plt.savefig(
        OUTPUT_DIR / "bill_amount_distribution.png",
        dpi=150
    )

    plt.close()


# ============================================================

def create_payment_chart(df):

    pay_cols = [
        f"pay_amt{i}"
        for i in range(1, 7)
    ]

    means = [
        df[col].mean()
        for col in pay_cols
    ]

    plt.figure(figsize=(9, 5))

    plt.bar(
        pay_cols,
        means
    )

    plt.title(
        "Promedio de Montos Pagados"
    )

    plt.xlabel(
        "Mes"
    )

    plt.ylabel(
        "Promedio PAY_AMT"
    )

    plt.xticks(rotation=45)

    plt.tight_layout()

    plt.savefig(
        OUTPUT_DIR / "payment_amount_distribution.png",
        dpi=150
    )

    plt.close()


# ============================================================

def create_correlation_chart(df):

    columns = [
        "limit_bal",
        "sex",
        "education",
        "marriage",
        "age",
        "pay_0",
        "pay_2",
        "pay_3",
        "pay_4",
        "pay_5",
        "pay_6",
        "bill_amt1",
        "bill_amt2",
        "bill_amt3",
        "bill_amt4",
        "bill_amt5",
        "bill_amt6",
        "pay_amt1",
        "pay_amt2",
        "pay_amt3",
        "pay_amt4",
        "pay_amt5",
        "pay_amt6",
        "default_payment_next_month"
    ]

    corr = df[columns].corr()

    plt.figure(figsize=(14, 11))

    plt.imshow(
        corr,
        aspect="auto"
    )

    plt.colorbar()

    plt.xticks(
        range(len(columns)),
        columns,
        rotation=90
    )

    plt.yticks(
        range(len(columns)),
        columns
    )

    plt.title(
        "Matriz de Correlación"
    )

    plt.tight_layout()

    plt.savefig(
        OUTPUT_DIR / "correlation_matrix.png",
        dpi=150
    )

    plt.close()


# ============================================================
# 6. EJECUCIÓN PRINCIPAL
# ============================================================

def main():

    print("=" * 60)
    print("EDA — SILVER")
    print("=" * 60)

    clientes, comportamiento, df = load_silver_data()

    print(
        f"Clientes leídos: {len(clientes):,}"
    )

    print(
        f"Registros de comportamiento: "
        f"{len(comportamiento):,}"
    )

    print(
        f"Dataset EDA: {len(df):,} registros"
    )

    print(
        f"Columnas: {len(df.columns)}"
    )

    print("\nGenerando reporte...")

    report_path = generate_general_report(
        clientes,
        comportamiento,
        df
    )

    print(
        f"Reporte generado: {report_path}"
    )

    print("\nGenerando gráficos...")

    create_target_chart(df)
    create_age_chart(df)
    create_limit_chart(df)
    create_pay_status_chart(df)
    create_bill_chart(df)
    create_payment_chart(df)
    create_correlation_chart(df)

    print("\nGráficos generados correctamente.")

    print("\nEDA FINALIZADO")
    print("=" * 60)


if __name__ == "__main__":
    main()