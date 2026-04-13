"""Descarga idempotente de la documentación oficial AEAT/BOE a ``data/raw/``.

Lee ``data/fuentes.yaml`` y trae al disco los PDFs, XSDs y páginas HTML que
sirven de fuente canónica para los YAML curados de ``data/{año}/``.

Flujo por entrada:

1. Comprueba si el archivo existe y coincide con el checksum esperado.
2. Si coincide → omite (idempotente).
3. Si no → descarga con httpx async, calcula SHA-256, actualiza
   ``data/checksums.json``.

Uso::

    python -m scripts.descargar_datos_aeat --año 2025
    python -m scripts.descargar_datos_aeat --todos
    python -m scripts.descargar_datos_aeat --verificar
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

import httpx
import yaml

from helpers.env_config import get_data_dir, get_raw_data_dir
from helpers.user_agent import USER_AGENT

CONCURRENCIA = 3
DELAY_ENTRE_REQUESTS = 0.5


def _cargar_fuentes() -> dict[str, Any]:
    fuentes_path = get_data_dir() / "fuentes.yaml"
    if not fuentes_path.exists():
        raise FileNotFoundError(f"No existe {fuentes_path}")
    with fuentes_path.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def _leer_checksums() -> dict[str, str]:
    path = get_data_dir() / "checksums.json"
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def _escribir_checksums(data: dict[str, str]) -> None:
    path = get_data_dir() / "checksums.json"
    with path.open("w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, sort_keys=True, ensure_ascii=False)
        fh.write("\n")


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _expand_entradas(fuentes: dict[str, Any], años: list[str]) -> list[dict[str, str]]:
    entradas: list[dict[str, str]] = []

    for año, bloque in (fuentes.get("ejercicios") or {}).items():
        if año not in años:
            continue
        for clave, item in bloque.items():
            if item.get("tipo") == "multiple":
                base_url = item["base_url"].rstrip("/") + "/"
                destino_pattern = item["destino_pattern"]
                for slug, ruta in item["territorios"].items():
                    entradas.append(
                        {
                            "id": f"{año}.{clave}.{slug}",
                            "url": base_url + ruta,
                            "destino": destino_pattern.format(slug=slug),
                        }
                    )
            else:
                entradas.append(
                    {
                        "id": f"{año}.{clave}",
                        "url": item["url"],
                        "destino": item["destino"],
                    }
                )

    for clave, item in (fuentes.get("normativa") or {}).items():
        entradas.append(
            {
                "id": f"normativa.{clave}",
                "url": item["url"],
                "destino": item["destino"],
            }
        )

    return entradas


async def _descargar_una(
    cliente: httpx.AsyncClient,
    entrada: dict[str, str],
    semaforo: asyncio.Semaphore,
    checksums: dict[str, str],
    raw_dir: Path,
) -> tuple[str, str | None, str]:
    destino_absoluto = raw_dir / entrada["destino"]

    if destino_absoluto.exists() and entrada["id"] in checksums:
        actual = _sha256(destino_absoluto)
        if actual == checksums[entrada["id"]]:
            return entrada["id"], actual, "omitido (checksum OK)"

    async with semaforo:
        try:
            respuesta = await cliente.get(entrada["url"])
            respuesta.raise_for_status()
        except httpx.HTTPError as exc:
            return entrada["id"], None, f"ERROR: {exc}"
        destino_absoluto.parent.mkdir(parents=True, exist_ok=True)
        destino_absoluto.write_bytes(respuesta.content)
        nuevo_hash = _sha256(destino_absoluto)
        await asyncio.sleep(DELAY_ENTRE_REQUESTS)
        return entrada["id"], nuevo_hash, f"descargado ({len(respuesta.content)} bytes)"


async def descargar(años: list[str]) -> int:
    fuentes = _cargar_fuentes()
    entradas = _expand_entradas(fuentes, años)
    if not entradas:
        print(f"No hay entradas para los años {años}", file=sys.stderr)
        return 1

    raw_dir = get_raw_data_dir()
    raw_dir.mkdir(parents=True, exist_ok=True)
    checksums = _leer_checksums()

    semaforo = asyncio.Semaphore(CONCURRENCIA)
    headers = {"User-Agent": USER_AGENT}
    async with httpx.AsyncClient(
        timeout=60.0, follow_redirects=True, headers=headers
    ) as cliente:
        tareas = [
            _descargar_una(cliente, entrada, semaforo, checksums, raw_dir)
            for entrada in entradas
        ]
        resultados = await asyncio.gather(*tareas)

    errores = 0
    for item_id, nuevo_hash, estado in resultados:
        print(f"  {item_id}: {estado}")
        if nuevo_hash is None:
            errores += 1
            continue
        checksums[item_id] = nuevo_hash

    _escribir_checksums(checksums)
    print(f"\nChecksums actualizados: {len(checksums)} entradas")
    return 0 if errores == 0 else 1


def verificar() -> int:
    raw_dir = get_raw_data_dir()
    checksums = _leer_checksums()
    faltantes: list[str] = []
    divergentes: list[str] = []

    for item_id, esperado in checksums.items():
        destino = None
        for sub in raw_dir.rglob("*"):
            if sub.is_file() and _sha256(sub) == esperado:
                destino = sub
                break
        if destino is None:
            faltantes.append(item_id)
            continue
    if not faltantes and not divergentes:
        print("OK: todos los archivos raw coinciden con checksums.json")
        return 0
    print(f"Faltan {len(faltantes)} archivos: {faltantes}", file=sys.stderr)
    return 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    grupo = parser.add_mutually_exclusive_group(required=True)
    grupo.add_argument("--año", help="Ejercicio fiscal concreto (p. ej. 2025)")
    grupo.add_argument("--todos", action="store_true", help="Todos los ejercicios")
    grupo.add_argument(
        "--verificar",
        action="store_true",
        help="Verifica checksums sin descargar",
    )

    args = parser.parse_args()

    if args.verificar:
        return verificar()

    fuentes = _cargar_fuentes()
    todos_los_años = list((fuentes.get("ejercicios") or {}).keys())
    años = todos_los_años if args.todos else [args.año]
    return asyncio.run(descargar(años))


if __name__ == "__main__":
    sys.exit(main())
