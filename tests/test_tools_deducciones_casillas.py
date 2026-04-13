"""Tests de las tools de deducciones y casillas (Fase 4)."""

import pytest

from tools.buscar_casilla import buscar_casilla_impl
from tools.buscar_deduccion import buscar_deduccion_impl
from tools.listar_casillas_modelo_100 import listar_casillas_modelo_100_impl
from tools.listar_deducciones_autonomicas import (
    listar_deducciones_autonomicas_impl,
)


@pytest.mark.asyncio
async def test_listar_casillas_completo():
    salida = await listar_casillas_modelo_100_impl(2025)
    assert "Casillas Modelo 100" in salida
    assert "0025" in salida or "**0025**" in salida  # rendimiento neto trabajo


@pytest.mark.asyncio
async def test_listar_casillas_filtrado_seccion():
    salida = await listar_casillas_modelo_100_impl(2025, seccion="cuota")
    assert "Cuota íntegra estatal" in salida
    assert "Rendimientos Trabajo" not in salida


@pytest.mark.asyncio
async def test_buscar_casilla_por_concepto():
    salida = await buscar_casilla_impl("rendimiento neto del trabajo", 2025)
    assert "0025" in salida


@pytest.mark.asyncio
async def test_buscar_casilla_maternidad():
    salida = await buscar_casilla_impl("maternidad", 2025)
    assert "maternidad" in salida.lower()


@pytest.mark.asyncio
async def test_listar_deducciones_madrid():
    salida = await listar_deducciones_autonomicas_impl("madrid", 2025)
    assert "Comunidad de Madrid" in salida
    assert "nacimiento" in salida.lower()


@pytest.mark.asyncio
async def test_listar_deducciones_madrid_categoria_vivienda():
    salida = await listar_deducciones_autonomicas_impl(
        "madrid", 2025, categoria="vivienda"
    )
    assert "Arrendamiento" in salida


@pytest.mark.asyncio
async def test_buscar_deduccion_alquiler():
    salida = await buscar_deduccion_impl("alquiler vivienda", 2025, ccaa="madrid")
    assert "Arrendamiento" in salida or "alquiler" in salida.lower()
