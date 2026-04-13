"""Tests de las tools derivadas (Fase 3)."""

import pytest

from tools.calcular_retencion_nomina import calcular_retencion_nomina_impl
from tools.comprobar_obligacion_declarar import comprobar_obligacion_declarar_impl
from tools.consultar_minimos import consultar_minimos_impl
from tools.consultar_plazos_campana import consultar_plazos_campana_impl
from tools.validar_minimo_declarante import validar_minimo_declarante_impl


@pytest.mark.asyncio
async def test_calcular_retencion_nomina_madrid_30k():
    salida = await calcular_retencion_nomina_impl(
        año=2025,
        territorio="madrid",
        salario_bruto_anual=30000.0,
        meses_pago=14,
    )
    assert "Retención IRPF estimada" in salida
    assert "Tipo de retención efectivo" in salida
    assert "Neto por paga" in salida


@pytest.mark.asyncio
async def test_consultar_minimos_soltero():
    salida = await consultar_minimos_impl(
        año=2025,
        territorio="madrid",
        edad_contribuyente=35,
    )
    assert "Mínimo total aplicable" in salida


@pytest.mark.asyncio
async def test_consultar_minimos_con_hijos():
    salida = await consultar_minimos_impl(
        año=2025,
        territorio="madrid",
        edad_contribuyente=40,
        hijos_edades=[2, 6],
    )
    assert "Mínimo total aplicable" in salida


@pytest.mark.asyncio
async def test_consultar_plazos_2025():
    salida = await consultar_plazos_campana_impl(2025)
    assert "Plazos Campaña Renta 2025" in salida
    assert "Fin plazo general" in salida


@pytest.mark.asyncio
async def test_obligacion_declarar_no_obligado():
    salida = await comprobar_obligacion_declarar_impl(
        año=2025,
        rendimientos_trabajo_brutos=15000.0,
        numero_pagadores=1,
    )
    assert "NO obligado a declarar" in salida


@pytest.mark.asyncio
async def test_obligacion_declarar_obligado_un_pagador():
    salida = await comprobar_obligacion_declarar_impl(
        año=2025,
        rendimientos_trabajo_brutos=25000.0,
        numero_pagadores=1,
    )
    assert "OBLIGADO a declarar" in salida


@pytest.mark.asyncio
async def test_obligacion_declarar_varios_pagadores():
    # 20.000€ con 2 pagadores y 5.000€ del segundo → baja a umbral 15.876
    salida = await comprobar_obligacion_declarar_impl(
        año=2025,
        rendimientos_trabajo_brutos=20000.0,
        numero_pagadores=2,
        rendimientos_segundo_pagador=5000.0,
    )
    assert "OBLIGADO a declarar" in salida


@pytest.mark.asyncio
async def test_obligacion_declarar_actividades_economicas():
    salida = await comprobar_obligacion_declarar_impl(
        año=2025,
        actividades_economicas=1000.0,
    )
    assert "OBLIGADO a declarar" in salida


@pytest.mark.asyncio
async def test_validar_minimo_declarante_ok():
    salida = await validar_minimo_declarante_impl(
        año=2025,
        rendimiento_neto_trabajo=20000.0,
    )
    assert "Reducción correctamente aplicada" in salida
