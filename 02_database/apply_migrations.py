"""Aplica migraciones oficiales de supabase/migrations con Supabase CLI.

Uso desde la raíz:
    python 02_database/apply_migrations.py --check
    python 02_database/apply_migrations.py --apply

Requiere: npm install (package.json contiene supabase), npx supabase login
y npx supabase link --project-ref <ref> ejecutados previamente.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
MIGRATIONS = ROOT / "supabase" / "migrations"
TARGET = MIGRATIONS / "20261108120000_verified_outcomes_and_approvals.sql"


def run_cli(*args: str) -> int:
    if not shutil.which("npx"):
        print("ERROR: No se encontró npx. Instala Node.js y ejecuta npm install.", file=sys.stderr)
        return 2
    command = ["npx", "--no-install", "supabase", *args]
    print("Ejecutando:", " ".join(command), flush=True)
    try:
        result = subprocess.run(command, cwd=ROOT, check=False)
        return result.returncode
    except OSError as exc:
        print(f"ERROR: No se pudo ejecutar Supabase CLI: {exc}", file=sys.stderr)
        return 2


def main() -> int:
    parser = argparse.ArgumentParser(description="Migraciones oficiales Supabase de NexaRisk")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--check", action="store_true", help="Listar estado de migraciones (solo lectura)")
    group.add_argument("--apply", action="store_true", help="Aplicar migraciones pendientes")
    args = parser.parse_args()

    if not TARGET.is_file():
        print(f"ERROR: Falta la migración V3: {TARGET}", file=sys.stderr)
        return 2
    if not (ROOT / "package.json").is_file() or not (ROOT / "supabase" / "config.toml").is_file():
        print("ERROR: Ejecuta dentro del repositorio NexaRisk original.", file=sys.stderr)
        return 2

    # La CLI usa su propio historial supabase_migrations.schema_migrations.
    # No creamos una segunda tabla de control.
    if args.check:
        return run_cli("migration", "list")
    return run_cli("db", "push", "--include-all")


if __name__ == "__main__":
    raise SystemExit(main())
