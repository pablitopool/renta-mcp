"""Tests rápidos de cobertura del ejercicio 2024."""

from decimal import Decimal

import pytest

from helpers.data_loader import listar_territorios, load_estatal, load_territorio
from helpers.tax_engine import InputIRPF, calcular_irpf
from tools.calcular_irpf import calcular_irpf_impl
from tools.consultar_plazos_campana import consultar_plazos_campana_impl
from tools.consultar_tramos import consultar_tramos_impl


def test_carga_estatal_2024():
    estatal = load_estatal(2024)
    assert estatal["año"] == 2024


def test_territorios_2024_incluye_madrid_y_bizkaia():
    territorios = listar_territorios(2024)
    assert "madrid" in territorios
    assert "bizkaia" in territorios


def test_calculo_irpf_madrid_2024_soltero_30k():
    estatal = load_estatal(2024)
    madrid = load_territorio(2024, "madrid")
    entrada = InputIRPF(
        año=2024,
        territorio="madrid",
        rendimiento_neto_trabajo=Decimal(30000),
    )
    resultado = calcular_irpf(entrada, estatal, madrid)
    assert Decimal(4000) <= resultado.cuota_liquida <= Decimal(6500)


@pytest.mark.asyncio
async def test_tool_calcular_irpf_2024():
    salida = await calcular_irpf_impl(
        año=2024,
        territorio="madrid",
        rendimiento_neto_trabajo=30000.0,
    )
    assert "Liquidación IRPF 2024" in salida


@pytest.mark.asyncio
async def test_tool_consultar_tramos_2024():
    salida = await consultar_tramos_impl(2024, "cataluna", "general")
    assert "Cataluña" in salida


@pytest.mark.asyncio
async def test_tool_plazos_2024():
    salida = await consultar_plazos_campana_impl(2024)
    assert "Plazos Campaña Renta 2024" in salida
    assert "2025-" in salida  # fechas de presentación en 2025
