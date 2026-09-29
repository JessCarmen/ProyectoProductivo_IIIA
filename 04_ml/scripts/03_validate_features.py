import os
import psycopg
from dotenv import load_dotenv

load_dotenv()

FEATURES = [
    "pay_max_delay",
    "pay_avg_delay_positive",
    "pay_positive_months",
    "pay_on_time_months",
    "pay_duly_paid_months",
    "pay_no_activity_months",
    "pay_negative_code_months",
    "bill_avg",
    "bill_max",
    "bill_min",
    "bill_std",
    "bill_negative_months",
    "bill_zero_months",
    "bill_positive_months",
    "bill_positive_total",
    "pay_amt_avg",
    "pay_amt_max",
    "pay_amt_min",
    "pay_amt_total",
    "payment_bill_ratio_avg",
    "payment_bill_ratio_max",
    "payment_bill_ratio_total",
    "payment_bill_positive_months",
    "high_delay_months",
    "recent_delay_months",
    "consecutive_delay_months",
]


def get_connection():
    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        raise RuntimeError("No se encontró DATABASE_URL en el archivo .env")

    return psycopg.connect(database_url)


def main():
    print("=" * 60)
    print("VALIDACIÓN DE FEATURES - GOLD_ML")
    print("=" * 60)

    conn = get_connection()

    try:
        with conn.cursor() as cur:
            print("\n[1/10] Validando existencia de features...")

            cur.execute(
                """
                SELECT column_name
                FROM information_schema.columns
                WHERE table_schema = 'gold'
                  AND table_name = 'gold_ml';
                """
            )

            existing = {row[0] for row in cur.fetchall()}
            missing = [f for f in FEATURES if f not in existing]

            if missing:
                raise RuntimeError(
                    "Faltan features: " + ", ".join(missing)
                )

            print(f"OK - {len(FEATURES)} features encontradas")

            print("\n[2/10] Validando cantidad de registros...")
            cur.execute("SELECT COUNT(*) FROM gold.gold_ml;")
            total = cur.fetchone()[0]
            print(f"Registros: {total}")

            if total != 33377:
                raise RuntimeError(f"Cantidad inesperada: {total}")

            print("OK - cantidad de registros")

            print("\n[3/10] Validando nulos esperados...")

            checks = {
                "pay_avg_delay_positive": "pay_positive_months = 0",
                "payment_bill_ratio_avg": "payment_bill_positive_months = 0",
                "payment_bill_ratio_max": "payment_bill_positive_months = 0",
                "payment_bill_ratio_total": "payment_bill_positive_months = 0",
            }

            for feature, condition in checks.items():
                cur.execute(
                    f"""
                    SELECT COUNT(*)
                    FROM gold.gold_ml
                    WHERE {feature} IS NULL
                      AND NOT ({condition});
                    """
                )
                unexpected = cur.fetchone()[0]

                cur.execute(
                    f"""
                    SELECT COUNT(*)
                    FROM gold.gold_ml
                    WHERE {feature} IS NULL;
                    """
                )
                nulls = cur.fetchone()[0]

                print(f"{feature}: {nulls} nulos; inesperados: {unexpected}")

                if unexpected > 0:
                    raise RuntimeError(
                        f"Nulos inesperados en {feature}: {unexpected}"
                    )

            print("OK - nulos compatibles con la semántica de las features")

            print("\n[4/10] Validando conteos mensuales...")

            count_features = [
                "pay_positive_months",
                "pay_on_time_months",
                "pay_duly_paid_months",
                "pay_no_activity_months",
                "pay_negative_code_months",
                "bill_negative_months",
                "bill_zero_months",
                "bill_positive_months",
                "payment_bill_positive_months",
                "high_delay_months",
                "recent_delay_months",
                "consecutive_delay_months",
            ]

            for feature in count_features:
                cur.execute(
                    f"""
                    SELECT COUNT(*)
                    FROM gold.gold_ml
                    WHERE {feature} < 0 OR {feature} > 6;
                    """
                )
                invalid = cur.fetchone()[0]
                print(f"{feature}: inválidos = {invalid}")

                if invalid > 0:
                    raise RuntimeError(
                        f"{feature} fuera de rango 0-6"
                    )

            print("OK - conteos 0-6")

            print("\n[5/10] Validando pay_max_delay...")

            cur.execute(
                """
                SELECT COUNT(*)
                FROM gold.gold_ml
                WHERE pay_max_delay < -2
                   OR pay_max_delay > 8;
                """
            )
            invalid = cur.fetchone()[0]
            print(f"Inválidos: {invalid}")

            if invalid > 0:
                raise RuntimeError("pay_max_delay fuera de rango")

            print("OK - pay_max_delay")

            print("\n[6/10] Validando coherencia de BILL...")

            cur.execute(
                """
                SELECT COUNT(*)
                FROM gold.gold_ml
                WHERE bill_negative_months
                    + bill_zero_months
                    + bill_positive_months <> 6;
                """
            )
            invalid = cur.fetchone()[0]
            print(f"Distribuciones BILL inválidas: {invalid}")

            if invalid > 0:
                raise RuntimeError("La clasificación de BILL no suma 6 meses")

            print("OK - BILL negativo + cero + positivo = 6")

            print("\n[7/10] Validando coherencia del ratio robusto...")

            cur.execute(
                """
                SELECT COUNT(*)
                FROM gold.gold_ml
                WHERE payment_bill_ratio_total < 0;
                """
            )
            invalid = cur.fetchone()[0]
            print(f"Ratios robustos negativos: {invalid}")

            if invalid > 0:
                raise RuntimeError("payment_bill_ratio_total negativo")

            cur.execute(
                """
                SELECT COUNT(*)
                FROM gold.gold_ml
                WHERE payment_bill_positive_months = 0
                  AND payment_bill_ratio_total IS NOT NULL;
                """
            )
            invalid = cur.fetchone()[0]
            print(f"Ratio definido sin meses positivos: {invalid}")

            if invalid > 0:
                raise RuntimeError("Inconsistencia en payment_bill_ratio_total")

            print("OK - ratio robusto")

            print("\n[8/10] Validando totales...")

            cur.execute(
                """
                SELECT COUNT(*)
                FROM gold.gold_ml
                WHERE bill_positive_total < 0
                   OR pay_amt_total < 0;
                """
            )
            invalid = cur.fetchone()[0]
            print(f"Totales negativos: {invalid}")

            if invalid > 0:
                raise RuntimeError("Totales negativos detectados")

            print("OK - totales")

            print("\n[9/10] Revisando distribución de ratios...")

            cur.execute(
                """
                SELECT
                    COUNT(*) FILTER (WHERE payment_bill_ratio_total IS NULL),
                    COUNT(*) FILTER (WHERE payment_bill_ratio_total > 1),
                    COUNT(*) FILTER (WHERE payment_bill_ratio_total > 10),
                    COUNT(*) FILTER (WHERE payment_bill_ratio_total > 100),
                    MAX(payment_bill_ratio_total)
                FROM gold.gold_ml;
                """
            )

            nulls, gt1, gt10, gt100, max_ratio = cur.fetchone()

            print(f"Ratio total NULL: {nulls}")
            print(f"Ratio total > 1: {gt1}")
            print(f"Ratio total > 10: {gt10}")
            print(f"Ratio total > 100: {gt100}")
            print(f"Ratio total máximo: {max_ratio}")

            print("OK - distribución reportada")

            print("\n[10/10] Resumen...")
            print("Features validadas:", len(FEATURES))

            print("\n" + "=" * 60)
            print("VALIDACIÓN DE FEATURES: OK")
            print("=" * 60)

    finally:
        conn.close()


if __name__ == "__main__":
    main()
