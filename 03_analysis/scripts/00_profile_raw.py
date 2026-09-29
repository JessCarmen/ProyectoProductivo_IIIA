from pathlib import Path
import pandas as pd


# ============================================================
# PROYECTO PRODUCTIVO IIIA
# Perfilado de la fuente RAW
# ============================================================
#
# OBJETIVO:
#   Inspeccionar la fuente RAW sin modificarla.
#
# FLUJO:
#   CSV RAW
#      ↓
#   Perfilado
#      ↓
#   Resultados de análisis
#      ↓
#   Diseño Bronze / Silver / Gold
#
# IMPORTANTE:
#   Este script NO limpia ni transforma los datos.
#   La fuente RAW debe permanecer intacta.
# ============================================================


# ============================================================
# 1. CONFIGURACIÓN DE RUTAS
# ============================================================

# PROJECT_ROOT apunta a:
#
# ProyectoProductivo_IIIA/
#
# El script está ubicado en:
#
# 03_analysis/scripts/00_profile_raw.py
#
# parents[0] = scripts
# parents[1] = 03_analysis
# parents[2] = ProyectoProductivo_IIIA

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

PROFILE_FILE = OUTPUT_DIR / "raw_profile.txt"


# ============================================================
# 2. CONFIGURACIÓN DE LA VARIABLE OBJETIVO
# ============================================================

TARGET = "default payment next month"


# ============================================================
# 3. VARIABLES CODIFICADAS
# ============================================================

CODED_COLUMNS = [
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


# ============================================================
# 4. VARIABLES NUMÉRICAS
# ============================================================

NUMERIC_COLUMNS = [
    "LIMIT_BAL",
    "AGE",
    "BILL_AMT1",
    "BILL_AMT2",
    "BILL_AMT3",
    "BILL_AMT4",
    "BILL_AMT5",
    "BILL_AMT6",
    "PAY_AMT1",
    "PAY_AMT2",
    "PAY_AMT3",
    "PAY_AMT4",
    "PAY_AMT5",
    "PAY_AMT6",
]


# ============================================================
# 5. FUNCIÓN AUXILIAR PARA MOSTRAR TÍTULOS
# ============================================================

def print_section(title):
    """
    Imprime un título visual para separar las secciones
    del perfilado en la terminal.
    """

    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)


# ============================================================
# 6. INICIO
# ============================================================

print("=" * 70)
print("PROYECTO PRODUCTIVO IIIA")
print("PERFILADO DE LA FUENTE RAW")
print("=" * 70)

print("\nArchivo RAW:")
print(RAW_FILE)


# ============================================================
# 7. VALIDAR EXISTENCIA DEL ARCHIVO
# ============================================================

if not RAW_FILE.exists():

    raise FileNotFoundError(
        "\nNo se encontró el archivo RAW.\n\n"
        f"Ruta esperada:\n{RAW_FILE}\n\n"
        "Verifica que el archivo exista en:\n"
        "01_data/raw/credit_card_clients_raw.csv"
    )


# ============================================================
# 8. CREAR CARPETA DE OUTPUTS
# ============================================================

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# 9. CARGAR EL CSV
# ============================================================

print("\nCargando archivo RAW...")

df = pd.read_csv(
    RAW_FILE,
    sep=";"
)

print("Archivo cargado correctamente.")


# ============================================================
# 10. INFORMACIÓN GENERAL
# ============================================================

print_section("1. INFORMACIÓN GENERAL")

rows = df.shape[0]
columns = df.shape[1]

print(f"Cantidad de registros : {rows:,}")
print(f"Cantidad de columnas  : {columns:,}")


# ============================================================
# 11. LISTADO DE COLUMNAS
# ============================================================

print_section("2. COLUMNAS")

for position, column in enumerate(
    df.columns,
    start=1
):

    print(
        f"{position:02d}. {column}"
    )


# ============================================================
# 12. TIPOS DE DATOS
# ============================================================

print_section("3. TIPOS DE DATOS")

print(
    df.dtypes.to_string()
)


# ============================================================
# 13. INFORMACIÓN DE MEMORIA
# ============================================================

print_section("4. USO DE MEMORIA")

memory_mb = (
    df.memory_usage(deep=True).sum()
    / 1024
    / 1024
)

print(
    f"Memoria aproximada utilizada: "
    f"{memory_mb:.2f} MB"
)


# ============================================================
# 14. VALORES NULOS
# ============================================================

print_section("5. VALORES NULOS")

null_counts = (
    df.isna()
    .sum()
    .sort_values(
        ascending=False
    )
)

null_counts_positive = (
    null_counts[
        null_counts > 0
    ]
)

if null_counts_positive.empty:

    print(
        "No se encontraron valores nulos."
    )

else:

    print(
        f"{'Columna':30} "
        f"{'Nulos':>10} "
        f"{'%':>10}"
    )

    print("-" * 55)

    for column, count in (
        null_counts_positive.items()
    ):

        percentage = (
            count / rows * 100
        )

        print(
            f"{column:30} "
            f"{count:10,} "
            f"{percentage:9.2f}%"
        )


# ============================================================
# 15. DUPLICADOS EXACTOS
# ============================================================

print_section("6. DUPLICADOS EXACTOS")

duplicate_count = (
    df.duplicated()
    .sum()
)

print(
    f"Duplicados exactos: "
    f"{duplicate_count:,}"
)


# ============================================================
# 16. DUPLICADOS POR ID
# ============================================================

print_section("7. DUPLICADOS POR ID")

if "ID" in df.columns:

    duplicate_ids = (
        df["ID"]
        .duplicated()
        .sum()
    )

    unique_ids = (
        df["ID"]
        .nunique()
    )

    print(
        f"IDs únicos: {unique_ids:,}"
    )

    print(
        f"IDs duplicados: "
        f"{duplicate_ids:,}"
    )

else:

    print(
        "La columna ID no existe."
    )


# ============================================================
# 17. VARIABLE OBJETIVO
# ============================================================

print_section("8. VARIABLE OBJETIVO")

if TARGET in df.columns:

    print(
        f"Variable objetivo: {TARGET}"
    )

    target_counts = (
        df[TARGET]
        .value_counts(
            dropna=False
        )
        .sort_index()
    )

    print()

    print(
        f"{'Valor':>10} "
        f"{'Registros':>15} "
        f"{'Porcentaje':>15}"
    )

    print("-" * 45)

    for value, count in (
        target_counts.items()
    ):

        percentage = (
            count / rows * 100
        )

        print(
            f"{str(value):>10} "
            f"{count:15,} "
            f"{percentage:14.2f}%"
        )

else:

    print(
        f"No se encontró la variable "
        f"objetivo: {TARGET}"
    )


# ============================================================
# 18. VALORES ÚNICOS DE VARIABLES CODIFICADAS
# ============================================================

print_section(
    "9. VALORES ÚNICOS DE VARIABLES CODIFICADAS"
)

for column in CODED_COLUMNS:

    if column in df.columns:

        values = (
            df[column]
            .dropna()
            .unique()
            .tolist()
        )

        try:

            values = sorted(values)

        except TypeError:

            pass

        print(
            f"\n{column}:"
        )

        print(values)

    else:

        print(
            f"\n{column}: "
            f"NO EXISTE EN EL DATASET"
        )


# ============================================================
# 19. ESTADÍSTICAS DE VARIABLES NUMÉRICAS
# ============================================================

print_section(
    "10. ESTADÍSTICAS DE VARIABLES NUMÉRICAS"
)

existing_numeric_columns = [
    column
    for column in NUMERIC_COLUMNS
    if column in df.columns
]

if existing_numeric_columns:

    numeric_summary = (
        df[existing_numeric_columns]
        .describe()
        .T
    )

    print(
        numeric_summary.to_string()
    )

else:

    print(
        "No se encontraron variables "
        "numéricas configuradas."
    )


# ============================================================
# 20. VALORES NEGATIVOS
# ============================================================

print_section(
    "11. VALORES NEGATIVOS"
)

for column in existing_numeric_columns:

    negative_count = (
        df[column] < 0
    ).sum()

    if negative_count > 0:

        percentage = (
            negative_count / rows * 100
        )

        print(
            f"{column:15} "
            f"{negative_count:8,} "
            f"({percentage:6.2f}%)"
        )


# ============================================================
# 21. VALORES CERO
# ============================================================

print_section(
    "12. VALORES CERO"
)

for column in existing_numeric_columns:

    zero_count = (
        df[column] == 0
    ).sum()

    if zero_count > 0:

        percentage = (
            zero_count / rows * 100
        )

        print(
            f"{column:15} "
            f"{zero_count:8,} "
            f"({percentage:6.2f}%)"
        )


# ============================================================
# 22. RANGOS DE VARIABLES NUMÉRICAS
# ============================================================

print_section(
    "13. RANGOS DE VARIABLES NUMÉRICAS"
)

for column in existing_numeric_columns:

    minimum = df[column].min()
    maximum = df[column].max()
    mean = df[column].mean()
    median = df[column].median()

    print(
        f"\n{column}"
    )

    print(
        f"  Mínimo : {minimum:,.2f}"
    )

    print(
        f"  Máximo : {maximum:,.2f}"
    )

    print(
        f"  Media  : {mean:,.2f}"
    )

    print(
        f"  Mediana: {median:,.2f}"
    )


# ============================================================
# 23. MUESTRA DE DATOS
# ============================================================

print_section(
    "14. PRIMEROS 5 REGISTROS"
)

print(
    df.head(5).to_string()
)


# ============================================================
# 24. ÚLTIMOS 5 REGISTROS
# ============================================================

print_section(
    "15. ÚLTIMOS 5 REGISTROS"
)

print(
    df.tail(5).to_string()
)


# ============================================================
# 25. RESUMEN FINAL
# ============================================================

print_section(
    "16. RESUMEN FINAL"
)

print(
    f"Registros           : {rows:,}"
)

print(
    f"Columnas            : {columns:,}"
)

print(
    f"Duplicados exactos  : {duplicate_count:,}"
)

if "ID" in df.columns:

    print(
        f"IDs únicos          : "
        f"{df['ID'].nunique():,}"
    )

print(
    f"Archivo fuente      : "
    f"{RAW_FILE.name}"
)


# ============================================================
# 26. GUARDAR PERFIL EN TXT
# ============================================================

print_section(
    "17. GUARDANDO PERFIL"
)

with open(
    PROFILE_FILE,
    "w",
    encoding="utf-8"
) as file:

    file.write(
        "PROYECTO PRODUCTIVO IIIA\n"
    )

    file.write(
        "PERFIL DE LA FUENTE RAW\n"
    )

    file.write(
        "=" * 70 + "\n\n"
    )

    file.write(
        f"Archivo: {RAW_FILE}\n"
    )

    file.write(
        f"Registros: {rows:,}\n"
    )

    file.write(
        f"Columnas: {columns:,}\n\n"
    )

    # --------------------------------------------------------
    # Columnas
    # --------------------------------------------------------

    file.write(
        "COLUMNAS\n"
    )

    file.write(
        "-" * 70 + "\n"
    )

    for position, column in enumerate(
        df.columns,
        start=1
    ):

        file.write(
            f"{position:02d}. {column}\n"
        )

    # --------------------------------------------------------
    # Tipos
    # --------------------------------------------------------

    file.write(
        "\nTIPOS DE DATOS\n"
    )

    file.write(
        "-" * 70 + "\n"
    )

    file.write(
        df.dtypes.to_string()
    )

    # --------------------------------------------------------
    # Nulos
    # --------------------------------------------------------

    file.write(
        "\n\nVALORES NULOS\n"
    )

    file.write(
        "-" * 70 + "\n"
    )

    file.write(
        null_counts.to_string()
    )

    # --------------------------------------------------------
    # Duplicados
    # --------------------------------------------------------

    file.write(
        "\n\nDUPLICADOS EXACTOS\n"
    )

    file.write(
        "-" * 70 + "\n"
    )

    file.write(
        f"{duplicate_count:,}\n"
    )

    # --------------------------------------------------------
    # ID
    # --------------------------------------------------------

    if "ID" in df.columns:

        file.write(
            "\n\nDUPLICADOS POR ID\n"
        )

        file.write(
            "-" * 70 + "\n"
        )

        file.write(
            f"IDs únicos: "
            f"{df['ID'].nunique():,}\n"
        )

        file.write(
            f"IDs duplicados: "
            f"{df['ID'].duplicated().sum():,}\n"
        )

    # --------------------------------------------------------
    # Target
    # --------------------------------------------------------

    file.write(
        "\n\nVARIABLE OBJETIVO\n"
    )

    file.write(
        "-" * 70 + "\n"
    )

    if TARGET in df.columns:

        file.write(
            f"Variable: {TARGET}\n\n"
        )

        file.write(
            df[TARGET]
            .value_counts(
                dropna=False
            )
            .sort_index()
            .to_string()
        )

    # --------------------------------------------------------
    # Estadísticas
    # --------------------------------------------------------

    file.write(
        "\n\nESTADÍSTICAS NUMÉRICAS\n"
    )

    file.write(
        "-" * 70 + "\n"
    )

    if existing_numeric_columns:

        file.write(
            df[existing_numeric_columns]
            .describe()
            .T
            .to_string()
        )

    # --------------------------------------------------------
    # Valores codificados
    # --------------------------------------------------------

    file.write(
        "\n\nVALORES ÚNICOS DE VARIABLES CODIFICADAS\n"
    )

    file.write(
        "-" * 70 + "\n"
    )

    for column in CODED_COLUMNS:

        if column in df.columns:

            values = (
                df[column]
                .dropna()
                .unique()
                .tolist()
            )

            try:
                values = sorted(values)
            except TypeError:
                pass

            file.write(
                f"\n{column}: {values}\n"
            )


# ============================================================
# 27. FINAL
# ============================================================

print(
    f"\nPerfil guardado correctamente en:"
)

print(
    PROFILE_FILE
)

print_section(
    "PERFILADO FINALIZADO"
)

print(
    "La fuente RAW NO fue modificada."
)

print(
    "Los resultados fueron guardados "
    "en 03_analysis/outputs/raw_profile.txt"
)