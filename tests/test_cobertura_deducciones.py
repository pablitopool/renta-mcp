"""Tests de cobertura de deducciones autonómicas y forales (Fase 8)."""

import pytest
import yaml

from helpers.env_config import get_data_dir

CCAA_COMUN = [
    "andalucia",
    "aragon",
    "asturias",
    "cantabria",
    "castilla-la-mancha",
    "castilla-leon",
    "cataluna",
    "canarias",
    "comunitat-valenciana",
    "extremadura",
    "galicia",
    "illes-balears",
    "madrid",
    "murcia",
    "rioja",
]
FORALES = ["alava", "bizkaia", "gipuzkoa", "navarra"]


def _cargar(año: int, sub: str, slug: str) -> dict:
    path = get_data_dir() / str(año) / sub / f"{slug}.yaml"
    with path.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


@pytest.mark.parametrize("slug", CCAA_COMUN)
@pytest.mark.parametrize("año", [2024, 2025])
def test_ccaa_comun_tiene_minimo_3_deducciones(año, slug):
    datos = _cargar(año, "ccaa", slug)
    ded = datos.get("deducciones") or []
    assert len(ded) >= 3, f"{slug} {año}: sólo {len(ded)} deducciones"


@pytest.mark.parametrize("slug", FORALES)
@pytest.mark.parametrize("año", [2024, 2025])
def test_foral_tiene_minimo_3_deducciones(año, slug):
    datos = _cargar(año, "forales", slug)
    ded = datos.get("deducciones") or []
    assert len(ded) >= 3, f"{slug} foral {año}: sólo {len(ded)} deducciones"


@pytest.mark.parametrize("slug", CCAA_COMUN + FORALES)
@pytest.mark.parametrize("año", [2024, 2025])
def test_cada_deduccion_tiene_parametros_numericos(año, slug):
    sub = "forales" if slug in FORALES else "ccaa"
    datos = _cargar(año, sub, slug)
    ded = datos.get("deducciones") or []
    campos_numericos = {
        "porcentaje",
        "porcentaje_cuota",
        "porcentaje_escolaridad",
        "porcentaje_idiomas",
        "porcentaje_uniformes",
        "importe_fijo",
        "base_maxima",
        "limite",
        "limite_por_hijo",
        "limite_general",
    }
    for d in ded:
        tiene_numerico = any(d.get(k) is not None for k in campos_numericos)
        assert tiene_numerico, (
            f"{slug} {año}: deducción {d.get('id', d.get('titulo'))} "
            f"carece de parámetro numérico"
        )


def test_las_4_escalas_forales_no_son_identicas():
    escalas = {}
    for slug in FORALES:
        datos = _cargar(2025, "forales", slug)
        escalas[slug] = tuple(
            (str(t["desde"]), str(t.get("hasta")), str(t["tipo"]))
            for t in datos.get("escala_autonomica") or []
        )
    # No debe haber duplicados exactos (los 4 forales son territorios con
    # normativa independiente).
    unicos = set(escalas.values())
    assert len(unicos) >= 3, (
        "Al menos 3 de 4 escalas forales deben diferir: "
        "detectado copia-pega entre territorios"
    )


@pytest.mark.parametrize("año", [2024, 2025])
def test_casillas_modelo_100_cobertura_minima(año):
    path = get_data_dir() / str(año) / "casillas.yaml"
    with path.open("r", encoding="utf-8") as fh:
        datos = yaml.safe_load(fh)
    casillas = datos.get("casillas") or []
    assert len(casillas) >= 100, (
        f"casillas.yaml {año}: sólo {len(casillas)} (esperaba >= 100)"
    )
