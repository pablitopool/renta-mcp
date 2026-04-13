"""Verifica que los documentos en ``data/raw/`` coincidan con ``checksums.json``.

Úsese en CI para detectar que alguien ha actualizado datos oficiales sin regenerar
los YAML derivados. Si se lanza con ``--opcional`` y ``data/raw/`` está vacío
(el caso en un clone limpio sin ejecutar descarga), el script sale con código 0.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

from helpers.env_config import get_data_dir, get_raw_data_dir


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--opcional",
        action="store_true",
        help="Si data/raw/ está vacío, salir con código 0 (útil en CI sin ingesta).",
    )
    args = parser.parse_args()

    raw_dir = get_raw_data_dir()
    checksums_path = get_data_dir() / "checksums.json"

    if not raw_dir.exists() or not any(raw_dir.rglob("*")):
        if args.opcional:
            print("data/raw/ vacío — verificación omitida (--opcional)")
            return 0
        print("ERROR: data/raw/ no existe o está vacío", file=sys.stderr)
        return 1

    if not checksums_path.exists():
        print(f"ERROR: no existe {checksums_path}", file=sys.stderr)
        return 1

    with checksums_path.open("r", encoding="utf-8") as fh:
        checksums: dict[str, str] = json.load(fh)

    if not checksums:
        print("checksums.json vacío — nada que verificar")
        return 0

    esperados = set(checksums.values())
    encontrados: set[str] = set()
    for archivo in raw_dir.rglob("*"):
        if archivo.is_file():
            encontrados.add(_sha256(archivo))

    faltantes = esperados - encontrados
    if faltantes:
        print(
            f"ERROR: {len(faltantes)} checksums esperados NO aparecen en data/raw/",
            file=sys.stderr,
        )
        print(f"Hashes faltantes: {sorted(faltantes)[:3]}...", file=sys.stderr)
        return 1

    print(f"OK: {len(encontrados)} archivos raw verificados")
    return 0


if __name__ == "__main__":
    sys.exit(main())
