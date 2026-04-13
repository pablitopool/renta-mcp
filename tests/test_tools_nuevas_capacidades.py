"""Tests de nuevas tools para cierre de gaps funcionales."""

from __future__ import annotations

import pytest

from tools.calcular_ganancia_cripto_fifo import calcular_ganancia_cripto_fifo_impl
from tools.calcular_rendimiento_actividad import calcular_rendimiento_actividad_impl
from tools.evaluar_exencion_art_7p import evaluar_exencion_art_7p_impl
from tools.evaluar_exit_tax import evaluar_exit_tax_impl
from tools.evaluar_regimen_impatriados import evaluar_regimen_impatriados_impl
from tools.preparar_payload_irpf import preparar_payload_irpf_impl
from tools.validar_municipio_despoblacion import validar_municipio_despoblacion_impl


@pytest.mark.asyncio
async def test_calcular_rendimiento_actividad_eds():
    salida = await calcular_rendimiento_actividad_impl(
        regimen="estimacion_directa_simplificada",
        ingresos_integros=50000,
        gastos_deducibles=10000,
        amortizaciones=2000,
        pagos_fraccionados_modelo_130_131=1500,
    )
    assert "Rendimiento neto de actividad estimado" in salida
    assert "pagos_fraccionados" in salida.lower()


@pytest.mark.asyncio
async def test_preparar_payload_irpf_renderiza_json():
    salida = await preparar_payload_irpf_impl(
        año=2025,
        territorio="madrid",
        rendimiento_neto_trabajo=30000,
        retenciones_practicadas=3000,
    )
    assert "Payload normalizado" in salida
    assert '"territorio": "madrid"' in salida


@pytest.mark.asyncio
async def test_validar_municipio_despoblacion_match():
    salida = await validar_municipio_despoblacion_impl(2025, "madrid", "Somosierra")
    assert "incluido en catalogo" in salida


@pytest.mark.asyncio
async def test_calcular_ganancia_cripto_fifo_basico():
    salida = await calcular_ganancia_cripto_fifo_impl(
        compras=["1@10000", "1@20000"],
        ventas=["1.5@30000"],
        comisiones_totales=100,
    )
    assert "Ganancias/pérdidas cripto" in salida
    assert "Ganancia neta imputable ahorro" in salida


@pytest.mark.asyncio
async def test_evaluar_regimen_impatriados_orientativo():
    salida = await evaluar_regimen_impatriados_impl(
        anos_desde_desplazamiento=1,
        residencia_fiscal_5_anos_previos_en_espana=False,
        existe_relacion_laboral_o_nombramiento=True,
        trabaja_principalmente_en_espana=True,
    )
    assert "posible elegibilidad" in salida


@pytest.mark.asyncio
async def test_evaluar_exencion_art_7p_orientativo():
    salida = await evaluar_exencion_art_7p_impl(
        rendimiento_trabajo_anual=80000,
        dias_trabajados_extranjero=200,
    )
    assert "Exencion aplicable" in salida


@pytest.mark.asyncio
async def test_evaluar_exit_tax_orientativo():
    salida = await evaluar_exit_tax_impl(
        valor_mercado_participaciones=5000000,
        porcentaje_participacion=10,
        anos_residencia_fiscal_espana_ultimos_15=12,
    )
    assert "riesgo potencial" in salida
