import os
import psycopg
from dotenv import load_dotenv

load_dotenv()


def get_connection():
    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        raise RuntimeError(
            "No se encontró DATABASE_URL en el archivo .env"
        )

    return psycopg.connect(database_url)


def main():

    print("=" * 60)
    print("VALIDACIÓN GOLD_ML")
    print("=" * 60)

    conn = get_connection()

    try:
        with conn.cursor() as cur:

            # -------------------------------------------------
            # 1. TOTAL DE REGISTROS
            # -------------------------------------------------

            print("\n[1/7] Validando cantidad de registros...")

            cur.execute("""
                SELECT COUNT(*)
                FROM gold.gold_ml;
            """)

            total = cur.fetchone()[0]

            print(f"Registros: {total}")

            # -------------------------------------------------
            # 2. IDS NULOS
            # -------------------------------------------------

            print("\n[2/7] Validando IDs nulos...")

            cur.execute("""
                SELECT COUNT(*)
                FROM gold.gold_ml
                WHERE id IS NULL;
            """)

            ids_nulos = cur.fetchone()[0]

            print(f"IDs nulos: {ids_nulos}")

            # -------------------------------------------------
            # 3. IDS DUPLICADOS
            # -------------------------------------------------

            print("\n[3/7] Validando IDs duplicados...")

            cur.execute("""
                SELECT COUNT(*)
                FROM (
                    SELECT id
                    FROM gold.gold_ml
                    GROUP BY id
                    HAVING COUNT(*) > 1
                ) duplicados;
            """)

            ids_duplicados = cur.fetchone()[0]

            print(f"IDs duplicados: {ids_duplicados}")

            # -------------------------------------------------
            # 4. TARGET
            # -------------------------------------------------

            print("\n[4/7] Validando target...")

            cur.execute("""
                SELECT
                    COUNT(*) FILTER (
                        WHERE target_default = 0
                    ),
                    COUNT(*) FILTER (
                        WHERE target_default = 1
                    ),
                    COUNT(*) FILTER (
                        WHERE target_default IS NULL
                    )
                FROM gold.gold_ml;
            """)

            target_0, target_1, target_null = cur.fetchone()

            print(f"Target 0: {target_0}")
            print(f"Target 1: {target_1}")
            print(f"Target nulo: {target_null}")

            # -------------------------------------------------
            # 5. VALORES DEL TARGET
            # -------------------------------------------------

            print("\n[5/7] Validando valores inesperados del target...")

            cur.execute("""
                SELECT COUNT(*)
                FROM gold.gold_ml
                WHERE target_default NOT IN (0, 1);
            """)

            target_invalidos = cur.fetchone()[0]

            print(f"Target inválidos: {target_invalidos}")

            # -------------------------------------------------
            # 6. NULOS EN VARIABLES
            # -------------------------------------------------

            print("\n[6/7] Validando nulos en variables...")

            columnas = [
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
                "pay_amt6"
            ]

            for columna in columnas:

                cur.execute(f"""
                    SELECT COUNT(*)
                    FROM gold.gold_ml
                    WHERE {columna} IS NULL;
                """)

                cantidad = cur.fetchone()[0]

                if cantidad > 0:
                    print(f"{columna}: {cantidad} nulos")

            print("Validación de nulos finalizada.")

            # -------------------------------------------------
            # 7. RANGO DE VARIABLES CATEGÓRICAS
            # -------------------------------------------------

            print("\n[7/7] Validando variables categóricas...")

            cur.execute("""
                SELECT COUNT(*)
                FROM gold.gold_ml
                WHERE sex NOT IN (1, 2, 3);
            """)

            sex_invalidos = cur.fetchone()[0]

            cur.execute("""
                SELECT COUNT(*)
                FROM gold.gold_ml
                WHERE education NOT IN (0, 1, 2, 3, 4, 5, 6, 7);
            """)

            education_invalidos = cur.fetchone()[0]

            cur.execute("""
                SELECT COUNT(*)
                FROM gold.gold_ml
                WHERE marriage NOT IN (0, 1, 2, 3, 4);
            """)

            marriage_invalidos = cur.fetchone()[0]

            print(f"SEX inválidos: {sex_invalidos}")
            print(f"EDUCATION inválidos: {education_invalidos}")
            print(f"MARRIAGE inválidos: {marriage_invalidos}")

            # -------------------------------------------------
            # RESULTADO FINAL
            # -------------------------------------------------

            print("\n" + "=" * 60)
            print("RESUMEN DE VALIDACIÓN")
            print("=" * 60)

            errores = (
                ids_nulos
                + ids_duplicados
                + target_null
                + target_invalidos
                + sex_invalidos
                + education_invalidos
                + marriage_invalidos
            )

            if total != 33377:
                print(f"⚠ Cantidad de registros inesperada: {total}")
            else:
                print("OK - cantidad de registros")

            if ids_nulos == 0:
                print("OK - IDs sin nulos")
            else:
                print("ERROR - existen IDs nulos")

            if ids_duplicados == 0:
                print("OK - IDs sin duplicados")
            else:
                print("ERROR - existen IDs duplicados")

            if target_null == 0:
                print("OK - target sin nulos")
            else:
                print("ERROR - target con nulos")

            if target_invalidos == 0:
                print("OK - target válido")
            else:
                print("ERROR - target inválido")

            if sex_invalidos == 0:
                print("OK - SEX válido")
            else:
                print("ERROR - SEX inválido")

            if education_invalidos == 0:
                print("OK - EDUCATION válido")
            else:
                print("ERROR - EDUCATION inválido")

            if marriage_invalidos == 0:
                print("OK - MARRIAGE válido")
            else:
                print("ERROR - MARRIAGE inválido")

            print("\n" + "=" * 60)

            if errores == 0 and total == 33377:
                print("VALIDACIÓN GOLD_ML: OK")
            else:
                print("VALIDACIÓN GOLD_ML: REVISAR")

            print("=" * 60)

    finally:
        conn.close()


if __name__ == "__main__":
    main()