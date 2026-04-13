"""Parser del XSD oficial del Modelo 100 (AEAT).

Flujo:

1. Lee ``data/raw/{año}/disenos_registro_index.html`` descargado por
   ``descargar_datos_aeat.py``.
2. Localiza el enlace al ZIP con el diseño de registro del Modelo 100
   vigente para el ejercicio.
3. Descarga el ZIP, extrae el ``.xsd`` a ``data/raw/{año}/xsd/``.
4. Parsea el XSD con ``lxml.etree`` y genera ``data/{año}/casillas.yaml``.

Estado actual: v0.1 mantiene ``data/{año}/casillas.yaml`` curado manualmente
(subset de ~50 casillas). Este script se completará en v0.2 cuando se
automatice la extracción desde el XSD oficial.
"""

from __future__ import annotations

import argparse
import sys


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--año", type=int, required=True)
    parser.parse_args()

    print(
        "TODO v0.2: extracción automática del XSD Modelo 100 desde el ZIP "
        "enlazado en disenos_registro_index.html. En v0.1 usamos "
        "data/{año}/casillas.yaml curado manualmente.",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
