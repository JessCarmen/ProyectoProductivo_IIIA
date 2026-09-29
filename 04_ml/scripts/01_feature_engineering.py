import os
import psycopg
from dotenv import load_dotenv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")


def get_connection():
    return psycopg.connect(
        os.getenv("DATABASE_URL")
    )


def main():

    print("=" * 60)
    print("FEATURE ENGINEERING")
    print("=" * 60)

    conn = get_connection()

    try:
        with conn.cursor() as cur:

            print("\n[1/3] Construyendo tablas GOLD...")

            cur.execute(
                "CALL gold.sp_construir_gold();"
            )

            print("OK - GOLD construido")

            print("\n[2/3] Construyendo GOLD_ML...")

            cur.execute(
                "CALL gold.sp_construir_gold_ml();"
            )

            print("OK - GOLD_ML construido")

            print("\n[3/4] Actualizando trazabilidad source_parent_id...")

            cur.execute("CALL gold.sp_refrescar_gold_lineage();")

            print("OK - lineage Gold actualizado")

            print("\n[4/4] Validando GOLD_ML...")

            cur.execute(
                """
                SELECT
                    COUNT(*) AS registros,
                    COUNT(*) FILTER (
                        WHERE target_default = 0
                    ) AS target_0,
                    COUNT(*) FILTER (
                        WHERE target_default = 1
                    ) AS target_1,
                    COUNT(*) FILTER (
                        WHERE id IS NULL
                    ) AS ids_nulos
                FROM gold.gold_ml;
                """
            )

            result = cur.fetchone()

            print(f"Registros: {result[0]}")
            print(f"Target 0: {result[1]}")
            print(f"Target 1: {result[2]}")
            print(f"IDs nulos: {result[3]}")

            conn.commit()

            print("\n" + "=" * 60)
            print("FEATURE ENGINEERING FINALIZADO")
            print("=" * 60)

    except Exception as e:

        conn.rollback()

        print("\nERROR:")
        print(e)

        raise

    finally:
        conn.close()


if __name__ == "__main__":
    main()