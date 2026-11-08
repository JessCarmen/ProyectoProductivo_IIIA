"""Consulta y aplica migraciones Supabase desde Windows/Cmder.

No crea un historial paralelo. Utiliza Supabase CLI.
Bloquea la aplicacion si encuentra migraciones antiguas sin registrar.
"""
from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MIGRATIONS = ROOT / "supabase" / "migrations"
TARGET_VERSION = "20261108120000"
TARGET = MIGRATIONS / f"{TARGET_VERSION}_verified_outcomes_and_approvals.sql"


def cli_executable() -> str:
    # En Windows subprocess necesita el lanzador .cmd, no el alias npx.
    name = "npx.cmd" if sys.platform == "win32" else "npx"
    executable = shutil.which(name)
    if executable is None:
        raise RuntimeError(
            f"No se encontro {name}. Verifica Node.js y npm en PATH."
        )
    return executable


def supabase(*args: str) -> subprocess.CompletedProcess[str]:
    command = [cli_executable(), "--no-install", "supabase", *args]
    print("Ejecutando:", "npx --no-install supabase", " ".join(args), flush=True)
    return subprocess.run(
        command,
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )


def show(result: subprocess.CompletedProcess[str]) -> None:
    if result.stdout:
        print(result.stdout, end="" if result.stdout.endswith("\n") else "\n")
    if result.stderr:
        print(result.stderr, file=sys.stderr)


def local_versions() -> set[str]:
    return {
        file.name[:14]
        for file in MIGRATIONS.glob("*.sql")
        if re.match(r"^\d{14}_.*\.sql$", file.name)
    }


def parse_migration_list(output: str) -> tuple[set[str], set[str]]:
    """Lee filas 'Local | Remote | Time' de Supabase CLI v2."""
    local, remote = set(), set()
    for line in output.splitlines():
        columns = [col.strip().strip("`") for col in line.split("|")]
        if len(columns) < 2:
            continue
        if re.fullmatch(r"\d{14}", columns[0]):
            local.add(columns[0])
        if re.fullmatch(r"\d{14}", columns[1]):
            remote.add(columns[1])
    return local, remote


def main() -> int:
    parser = argparse.ArgumentParser(description="Migraciones NexaRisk")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--check", action="store_true", help="Consultar estado (solo lectura)")
    group.add_argument("--apply", action="store_true", help="Aplicar V3 si el historial es seguro")
    args = parser.parse_args()

    if not TARGET.is_file():
        print(f"ERROR: No existe {TARGET}", file=sys.stderr)
        return 2
    if not (ROOT / "package.json").is_file():
        print("ERROR: No se encontro package.json en la raiz.", file=sys.stderr)
        return 2

    try:
        result = supabase("migration", "list")
    except (RuntimeError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    show(result)
    if result.returncode != 0:
        print("ERROR: No se pudo consultar el historial remoto.", file=sys.stderr)
        return result.returncode

    local, remote = parse_migration_list(result.stdout + "\n" + result.stderr)
    if not local or not remote:
        print("ERROR: No se pudo interpretar el historial. No se aplicara nada.", file=sys.stderr)
        return 2

    pending = sorted(local_versions() - remote)
    print("\nMigraciones locales pendientes:", ", ".join(pending) or "ninguna")

    if args.check:
        if any(version < TARGET_VERSION for version in pending):
            print(
                "AVISO: Hay migraciones anteriores a V3 sin registrar. "
                "Revisalas antes de aplicar V3."
            )
        return 0

    unexpected = [v for v in pending if v != TARGET_VERSION]
    if unexpected:
        print(
            "BLOQUEADO: Existen migraciones pendientes distintas de V3: "
            + ", ".join(unexpected),
            file=sys.stderr,
        )
        print(
            "No ejecutes db push --include-all hasta conciliar "
            "el historial de migraciones con los objetos existentes.",
            file=sys.stderr,
        )
        return 3

    if TARGET_VERSION in remote:
        print("V3 ya esta registrada como aplicada. No hay cambios.")
        return 0

    print("Aplicando la migracion V3 mediante Supabase CLI...")
    apply_result = supabase("db", "push")
    show(apply_result)
    if apply_result.returncode != 0:
        print("ERROR: La migracion no se aplico correctamente.", file=sys.stderr)
        return apply_result.returncode

    print("La CLI termino correctamente. Verifica las tablas y el historial remoto.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
