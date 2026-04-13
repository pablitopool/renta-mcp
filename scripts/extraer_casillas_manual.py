"""Extrae casillas del Modelo 100 del manual práctico Parte 1 (AEAT).

Parsea ``data/raw/{año}/manual_parte_1.pdf`` buscando patrones ``casilla 0XXX``
o ``Casilla [0XXX]`` y genera ``data/{año}/casillas.yaml`` con al menos ~300
casillas agrupadas por sección.

Uso::

    python -m scripts.extraer_casillas_manual --año 2025 --merge

``--merge`` fusiona con el casillas.yaml existente sin eliminar entradas
curadas manualmente.
"""

from __future__ import annotations

import argparse
import re
import sys

import pypdf
import yaml

from helpers.env_config import get_data_dir, get_raw_data_dir

CASILLA_RE = re.compile(r"\b[Cc]asilla\s+\[?(\d{4})\]?", re.MULTILINE)
# Identifica cambios de sección por cabeceras tipo "Apartado X" / "A. Rendimientos..."
SECCION_RE = re.compile(
    r"^(Apartado\s+([A-Z])|Rendimientos del trabajo|"
    r"Rendimientos del capital (inmobiliario|mobiliario)|"
    r"Actividades económicas|Ganancias y pérdidas patrimoniales|"
    r"Reducciones de la base imponible|Mínimo personal y familiar|"
    r"Adecuación del impuesto|Cuota íntegra|Deducciones generales|"
    r"Cuota líquida|Cuota resultante|Retenciones e ingresos a cuenta|"
    r"Resultado de la declaración)",
    re.IGNORECASE | re.MULTILINE,
)

SECCION_A_CLAVE = {
    "rendimientos del trabajo": "rendimientos_trabajo",
    "rendimientos del capital inmobiliario": "capital_inmobiliario",
    "rendimientos del capital mobiliario": "capital_mobiliario",
    "actividades económicas": "actividades_economicas",
    "ganancias y pérdidas": "ganancias_perdidas",
    "reducciones": "reducciones",
    "mínimo personal y familiar": "minimos",
    "cuota íntegra": "cuota",
    "cuota líquida": "cuota",
    "deducciones generales": "deducciones_estatales",
    "retenciones": "retenciones",
    "resultado": "resultado",
    "adecuación": "minimos",
}


def _clave_seccion(texto: str) -> str:
    t = texto.lower()
    for clave, valor in SECCION_A_CLAVE.items():
        if clave in t:
            return valor
    return "otros"


def extraer_casillas(año: int) -> list[dict]:
    pdf_path = get_raw_data_dir() / str(año) / "manual_parte_1.pdf"
    if not pdf_path.exists():
        raise FileNotFoundError(pdf_path)

    lector = pypdf.PdfReader(str(pdf_path))
    texto_total = "\n".join(p.extract_text() or "" for p in lector.pages)

    casillas_vistas: dict[str, dict] = {}
    seccion_actual = "otros"

    for linea in texto_total.splitlines():
        m_sec = SECCION_RE.search(linea)
        if m_sec:
            seccion_actual = _clave_seccion(m_sec.group(0))

        for m in CASILLA_RE.finditer(linea):
            numero = m.group(1)
            # Tomar contexto (palabras siguientes en la línea) como nombre
            idx = m.end()
            contexto = linea[idx : idx + 120].strip().strip(".:;")
            # Limpiar el contexto
            contexto = re.sub(r"\s+", " ", contexto)
            nombre = contexto[:80] if contexto else f"Casilla {numero}"

            if numero in casillas_vistas:
                continue
            casillas_vistas[numero] = {
                "numero": numero,
                "seccion": seccion_actual,
                "nombre": nombre,
            }

    return sorted(casillas_vistas.values(), key=lambda c: c["numero"])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--año", type=int, required=True)
    parser.add_argument(
        "--merge",
        action="store_true",
        help="Fusiona con casillas.yaml existente preservando descripciones curadas.",
    )
    parser.add_argument(
        "--min-casillas",
        type=int,
        default=100,
        help="Falla si se extraen menos de N casillas (detecta regresión).",
    )
    args = parser.parse_args()

    casillas_extraidas = extraer_casillas(args.año)
    print(f"Extraídas {len(casillas_extraidas)} casillas únicas del PDF")

    if len(casillas_extraidas) < args.min_casillas:
        print(
            f"ERROR: sólo {len(casillas_extraidas)} casillas; esperaba >= "
            f"{args.min_casillas}. ¿Cambió el formato del PDF?",
            file=sys.stderr,
        )
        return 1

    destino = get_data_dir() / str(args.año) / "casillas.yaml"

    if args.merge and destino.exists():
        with destino.open("r", encoding="utf-8") as fh:
            existente = yaml.safe_load(fh) or {}
        casillas_curadas = {c["numero"]: c for c in existente.get("casillas", [])}
        for nueva in casillas_extraidas:
            if nueva["numero"] not in casillas_curadas:
                casillas_curadas[nueva["numero"]] = nueva
        lista_final = sorted(casillas_curadas.values(), key=lambda c: c["numero"])
    else:
        lista_final = casillas_extraidas

    contenido = {
        "año": args.año,
        "fuente": "Manual Práctico Renta AEAT Parte 1 (parseo automático)",
        "revisado_en": "2026-04-13",
        "generado_por": "scripts/extraer_casillas_manual.py",
        "casillas": lista_final,
    }
    with destino.open("w", encoding="utf-8") as fh:
        yaml.safe_dump(
            contenido, fh, allow_unicode=True, sort_keys=False, default_flow_style=False
        )
    print(f"OK: {len(lista_final)} casillas escritas a {destino}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
