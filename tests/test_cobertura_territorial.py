"""Tests de cobertura territorial (Fase 5)."""

from decimal import Decimal

import pytest

from helpers.data_loader import listar_territorios, load_estatal, load_territorio
from helpers.tax_engine import InputIRPF, calcular_irpf

CCAA_COMUN = {
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
    "ceuta",
    "melilla",
}
FORALES = {"alava", "bizkaia", "gipuzkoa", "navarra"}


def test_listar_territorios_2025_cobertura_completa():
    territorios = set(listar_territorios(2025))
    assert CCAA_COMUN.issubset(territorios), f"Faltan CCAA: {CCAA_COMUN - territorios}"
    assert FORALES.issubset(territorios), f"Faltan forales: {FORALES - territorios}"


@pytest.mark.parametrize("slug", sorted(CCAA_COMUN))
def test_ccaa_comun_carga_ok_y_regimen_correcto(slug):
    datos = load_territorio(2025, slug)
    assert datos["territorio"]["regimen"] == "comun"
    assert datos["año"] == 2025
    escala = datos.get("escala_autonomica") or datos.get("escala_general")
    assert escala and escala[0]["desde"] == 0


@pytest.mark.parametrize("slug", sorted(FORALES))
def test_forales_carga_ok_y_regimen_foral(slug):
    datos = load_territorio(2025, slug)
    assert datos["territorio"]["regimen"] == "foral"
    assert datos["año"] == 2025
    escala = datos.get("escala_autonomica") or datos.get("escala_general")
    assert escala and escala[0]["desde"] == 0


@pytest.mark.parametrize("slug", sorted(CCAA_COMUN))
def test_calculo_irpf_funciona_para_cada_ccaa(slug):
    estatal = load_estatal(2025)
    territorio = load_territorio(2025, slug)
    entrada = InputIRPF(
        año=2025,
        territorio=slug,
        rendimiento_neto_trabajo=Decimal(25000),
    )
    resultado = calcular_irpf(entrada, estatal, territorio)
    assert resultado.cuota_liquida > 0
    assert resultado.regimen == "comun"


@pytest.mark.parametrize("slug", sorted(FORALES))
def test_calculo_irpf_funciona_para_cada_foral(slug):
    estatal = load_estatal(2025)
    territorio = load_territorio(2025, slug)
    entrada = InputIRPF(
        año=2025,
        territorio=slug,
        rendimiento_neto_trabajo=Decimal(30000),
    )
    resultado = calcular_irpf(entrada, estatal, territorio)
    assert resultado.cuota_liquida > 0
    assert resultado.regimen == "foral"
    # Régimen foral: cuota estatal = 0 (todo va por la escala foral).
    assert resultado.cuota_integra_estatal == 0
