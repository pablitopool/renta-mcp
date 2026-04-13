"""Parser de HTML de la guía de deducciones autonómicas del IRPF (AEAT).

Lee ``data/raw/{año}/deducciones/{slug}.html`` (descargado por
``descargar_datos_aeat.py``) y extrae los títulos de las deducciones
agrupados por categoría. Genera un YAML SEED que el mantenedor completa
manualmente con porcentajes, importes fijos, bases máximas y requisitos.

Uso::

    python -m scripts.parsear_deducciones_aeat --año 2025 --territorio madrid
    python -m scripts.parsear_deducciones_aeat --año 2025 --todos
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import yaml
from bs4 import BeautifulSoup

from helpers.env_config import get_data_dir, get_raw_data_dir


def _slugify(texto: str) -> str:
    texto = texto.lower().strip().replace(".", "").replace(",", "")
    texto = re.sub(r"[áàä]", "a", texto)
    texto = re.sub(r"[éèë]", "e", texto)
    texto = re.sub(r"[íìï]", "i", texto)
    texto = re.sub(r"[óòö]", "o", texto)
    texto = re.sub(r"[úùü]", "u", texto)
    texto = re.sub(r"ñ", "n", texto)
    texto = re.sub(r"[^a-z0-9]+", "-", texto)
    return texto.strip("-")[:80]


CATEGORIA_MAP = {
    "circunstancias personales": "familia",
    "familia": "familia",
    "vivienda": "vivienda",
    "donativ": "donativos",
    "educaci": "educacion",
    "inversi": "inversion",
    "otros": "otros",
    "cultura": "cultura",
    "medio ambient": "medioambiente",
    "discapacid": "discapacidad",
}


def _categoria_desde_cabecera(cabecera: str) -> str:
    lower = cabecera.lower()
    for clave, cat in CATEGORIA_MAP.items():
        if clave in lower:
            return cat
    return "otros"


def extraer_deducciones_de_html(html: str, territorio_slug: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    deducciones: list[dict] = []

    # La página AEAT usa <table> con <thead> de categorías y <tbody> con
    # listas <ul><li> por categoría.
    tabla = soup.find("table")
    if not tabla:
        return deducciones
    encabezados = [th.get_text(strip=True) for th in tabla.select("thead th")]
    filas = tabla.select("tbody tr")
    for fila in filas:
        celdas = fila.find_all("td")
        for idx, celda in enumerate(celdas):
            if idx >= len(encabezados):
                continue
            categoria = _categoria_desde_cabecera(encabezados[idx])
            for li in celda.select("li"):
                titulo = li.get_text(strip=True).rstrip(".")
                if not titulo:
                    continue
                slug_id = f"{territorio_slug}-{_slugify(titulo)}"
                deducciones.append(
                    {
                        "id": slug_id,
                        "categoria": categoria,
                        "titulo": titulo,
                        "TODO": "completar: porcentaje/importe/requisitos desde manual Parte 2",
                    }
                )
    return deducciones


def procesar_territorio(año: int, slug: str) -> Path:
    raw = get_raw_data_dir() / str(año) / "deducciones" / f"{slug}.html"
    if not raw.exists():
        raise FileNotFoundError(f"No existe {raw}")
    html = raw.read_text(encoding="utf-8")
    deducciones = extraer_deducciones_de_html(html, slug)

    destino = get_data_dir() / str(año) / "ccaa" / f"{slug}.seed.yaml"
    destino.parent.mkdir(parents=True, exist_ok=True)
    contenido = {
        "_generado_por": "scripts/parsear_deducciones_aeat.py",
        "_nota": (
            "SEED automático. Este archivo lista los TÍTULOS de las "
            "deducciones autonómicas extraídos del índice HTML de la AEAT. "
            "Los importes, porcentajes y requisitos concretos deben "
            "completarse manualmente consultando el Manual Práctico "
            "Parte 2 del ejercicio correspondiente. Para activar, renombra "
            "a {slug}.yaml (reemplaza el existente sólo si confirmas)."
        ),
        "deducciones": deducciones,
    }
    destino.write_text(
        yaml.safe_dump(contenido, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )
    return destino


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--año", type=int, required=True)
    g = parser.add_mutually_exclusive_group(required=True)
    g.add_argument("--territorio", help="Slug concreto (p. ej. madrid)")
    g.add_argument("--todos", action="store_true")
    args = parser.parse_args()

    if args.todos:
        base = get_raw_data_dir() / str(args.año) / "deducciones"
        if not base.exists():
            print(f"No existe {base}", file=sys.stderr)
            return 1
        slugs = [p.stem for p in base.glob("*.html")]
    else:
        slugs = [args.territorio]

    for slug in slugs:
        try:
            destino = procesar_territorio(args.año, slug)
            print(f"  {slug}: {destino}")
        except Exception as exc:  # noqa: BLE001
            print(f"  {slug}: ERROR {exc}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
