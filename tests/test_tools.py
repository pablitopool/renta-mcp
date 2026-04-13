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


@pytest.mark.asyncio
async def test_calcular_irpf_muestra_deducciones_estatales_y_maternidad():
    salida = await calcular_irpf_impl(
        año=2025,
        territorio="madrid",
        rendimiento_neto_trabajo=35000.0,
        hijos_edades=[1],
        donativos_ley_49_2002=500.0,
        meses_maternidad_por_hijo_menor_3=6,
    )
    assert "Deducciones estatales aplicadas" in salida
    assert "donativos ley 49/2002" in salida.lower()
    assert "Maternidad reembolsable" in salida


@pytest.mark.asyncio
async def test_calcular_irpf_muestra_deducciones_autonomicas():
    salida = await calcular_irpf_impl(
        año=2025,
        territorio="comunitat-valenciana",
        rendimiento_neto_trabajo=32000.0,
        hijos_edades=[2],
        deducciones_autonomicas_reclamadas=["cv-gastos-guarderia"],
        bases_deducciones_autonomicas={"cv-gastos-guarderia": 3000.0},
    )
    assert "Deducciones autonómicas aplicadas" in salida
    assert "cv-gastos-guarderia" in salida


@pytest.mark.asyncio
async def test_calcular_irpf_auto_muestra_deducciones_autonomicas():
    salida = await calcular_irpf_impl(
        año=2025,
        territorio="comunitat-valenciana",
        rendimiento_neto_trabajo=32000.0,
        hijos_edades=[2],
        gastos_guarderia=3000.0,
    )
    assert "Deducciones autonómicas aplicadas" in salida
    assert "cv-gastos-guarderia" in salida


@pytest.mark.asyncio
async def test_calcular_irpf_auto_muestra_nuevas_deducciones_madrid():
    salida = await calcular_irpf_impl(
        año=2025,
        territorio="madrid",
        rendimiento_neto_trabajo=30000.0,
        hijos_edades=[2],
        ascendientes_edades=[70],
        cotizaciones_empleados_hogar=2000.0,
    )
    assert "Deducciones autonómicas aplicadas" in salida
    assert "mad-cuidado-ascendientes" in salida
    assert "mad-cuidado-hijos-menores-mayores-discapacidad" in salida


@pytest.mark.asyncio
async def test_calcular_irpf_auto_muestra_deducciones_vivienda_madrid():
    salida = await calcular_irpf_impl(
        año=2025,
        territorio="madrid",
        rendimiento_neto_trabajo=30000.0,
        edad_contribuyente=29,
        intereses_prestamo_adquisicion_vivienda_joven=5000.0,
        gastos_arrendamiento_viviendas=2000.0,
        viviendas_vacias_arrendadas=1,
    )
    assert "Deducciones autonómicas aplicadas" in salida
    assert "mad-intereses-prestamo-vivienda-joven" in salida
    assert "mad-gastos-arrendamiento-viviendas" in salida
    assert "mad-arrendamiento-viviendas-vacias" in salida
