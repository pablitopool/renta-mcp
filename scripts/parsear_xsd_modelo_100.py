"""Parser de diseño de registro del Modelo 100 (AEAT).

NOTA IMPORTANTE: contrario a lo asumido inicialmente, la AEAT NO publica un
XSD para el Modelo 100. La declaración del IRPF se presenta exclusivamente
vía el servicio web **Renta WEB** (con autenticación), no admite carga de
ficheros estructurados.

Lo que sí publica la AEAT en
https://sede.agenciatributaria.gob.es/Sede/ayuda/disenos-registro/modelos-100-199.html
son PDFs de diseño de registro, pero para otros modelos (182, 184, 187,
192, 193, 194, 195, 198, 199 — modelos informativos), no para el 100.

Por tanto, el listado de casillas del Modelo 100 en
``data/{año}/casillas.yaml`` se mantiene CURADO MANUALMENTE a partir del
Manual Práctico de Renta (Parte 1) y de la Orden HAC/{NNN}/{YYYY} que
aprueba el modelo cada ejercicio. Este subset se amplía en cada revisión.

Este script busca DR_Modelo_100_*.pdf en la página índice por si en una
futura campaña la AEAT decidiera publicarlo. Si lo encuentra, lo descarga.

Uso::

    python -m scripts.parsear_xsd_modelo_100 --año 2025
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import httpx
from bs4 import BeautifulSoup

from helpers.env_config import get_raw_data_dir
from helpers.user_agent import USER_AGENT


def buscar_dr_modelo_100(año: int) -> str | None:
    index_path = get_raw_data_dir() / str(año) / "disenos_registro_index.html"
    if not index_path.exists():
        print(f"No existe {index_path}", file=sys.stderr)
        return None

    soup = BeautifulSoup(index_path.read_text(encoding="utf-8"), "html.parser")
    for a in soup.find_all("a", href=True):
        if "DR_Modelo_100" in a["href"]:
            return a["href"]
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--año", type=int, required=True)
    args = parser.parse_args()

    href = buscar_dr_modelo_100(args.año)
    if href is None:
        print(
            "No se encontró DR_Modelo_100 en la página índice. "
            "Es el comportamiento esperado — la AEAT no publica diseño de "
            "registro del Modelo 100. Usa data/{año}/casillas.yaml curado "
            "manualmente a partir del Manual Práctico y la Orden HAC."
        )
        return 0

    if href.startswith("/"):
        href = "https://sede.agenciatributaria.gob.es" + href
    destino = get_raw_data_dir() / str(args.año) / Path(href).name
    print(f"Descargando {href} -> {destino}")

    with httpx.Client(
        timeout=60.0, follow_redirects=True, headers={"User-Agent": USER_AGENT}
    ) as c:
        r = c.get(href)
        r.raise_for_status()
        destino.write_bytes(r.content)
    print(f"OK ({len(r.content)} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
