"""Tests de las tools MCP (a través de las funciones ``*_impl``)."""

from __future__ import annotations

import pytest

from tools.calcular_irpf import calcular_irpf_impl
from tools.consultar_tramos import consultar_tramos_impl


@pytest.mark.asyncio
async def test_consultar_tramos_estatal_2025():
    salida = await consultar_tramos_impl(2025, "estatal", "general")
    assert "Escala general ESTATAL" in salida
    assert "9,50 %" in salida or "9.50 %" in salida


@pytest.mark.asyncio
async def test_consultar_tramos_madrid_2025():
    salida = await consultar_tramos_impl(2025, "madrid", "general")
    assert "AUTONÓMICA" in salida
    assert "Comunidad de Madrid" in salida


@pytest.mark.asyncio
async def test_consultar_tramos_ahorro_2025():
    salida = await consultar_tramos_impl(2025, "estatal", "ahorro")
    assert "ahorro" in salida.lower()


@pytest.mark.asyncio
async def test_calcular_irpf_soltero_madrid_30k():
    salida = await calcular_irpf_impl(
        año=2025,
        territorio="madrid",
        rendimiento_neto_trabajo=30000.0,
        edad_contribuyente=35,
    )
    assert "Liquidación IRPF 2025" in salida
    assert "Comunidad de Madrid" in salida
    assert "Cuota líquida" in salida
    assert "informativa no vinculante" in salida


@pytest.mark.asyncio
async def test_calcular_irpf_conjunta_biparental_50k_2_hijos():
    salida = await calcular_irpf_impl(
        año=2025,
        territorio="madrid",
        rendimiento_neto_trabajo=50000.0,
        situacion_familiar="conjunta_biparental",
        hijos_edades=[2, 24],
    )
    assert "Liquidación IRPF" in salida
    assert "Desglose del cálculo" in salida
