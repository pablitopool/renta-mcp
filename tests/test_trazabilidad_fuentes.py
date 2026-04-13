"""Tests de trazabilidad de fuentes legales en los YAMLs de datos fiscales.

Garantiza que cada archivo curado referencia una norma concreta — no se
admiten cadenas ``TODO`` en ``fuente_boe`` de ficheros CCAA / estatal /
forales. Los forales pueden usar textos tipo "Norma Foral ..." sin BOE.
"""

from pathlib import Path

import pytest
import yaml

from helpers.env_config import get_data_dir


def _archivos_yaml_curados() -> list[Path]:
    base = get_data_dir()
    archivos: list[Path] = []
    for año_dir in sorted(base.glob("20*")):
        archivos.extend(año_dir.glob("estatal.yaml"))
        archivos.extend(año_dir.glob("ccaa/*.yaml"))
        archivos.extend(año_dir.glob("forales/*.yaml"))
    return [a for a in archivos if not a.name.endswith(".seed.yaml")]


@pytest.mark.parametrize("archivo", _archivos_yaml_curados(), ids=lambda p: p.name)
def test_archivo_declara_fuente_legal(archivo: Path):
    with archivo.open("r", encoding="utf-8") as fh:
        datos = yaml.safe_load(fh)
    fuente = datos.get("fuente_boe")
    assert fuente, f"{archivo} carece de fuente_boe"
    assert "TODO" not in fuente, (
        f"{archivo} mantiene marca TODO en fuente_boe: {fuente!r}"
    )


def test_fuentes_yaml_orden_hac_url_correcta():
    fuentes_path = get_data_dir() / "fuentes.yaml"
    with fuentes_path.open("r", encoding="utf-8") as fh:
        fuentes = yaml.safe_load(fh)
    url_orden_hac = fuentes["ejercicios"]["2025"]["orden_hac"]["url"]
    assert "2026/03/27" in url_orden_hac, (
        f"URL Orden HAC 2025 debe apuntar a la publicación del 27/03/2026: "
        f"encontrado {url_orden_hac!r}"
    )
