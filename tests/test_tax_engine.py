"""Tests del motor fiscal ``helpers/tax_engine.py``."""

from __future__ import annotations

from decimal import Decimal

import pytest

from helpers.tax_engine import (
    Escala,
    Hijo,
    InputIRPF,
    aplicar_escala,
    calcular_irpf,
    calcular_minimo_personal_familiar,
    calcular_reduccion_trabajo,
)

ESCALA_SIMPLE = Escala.desde_lista(
    [
        {"desde": 0, "hasta": 10000, "tipo": 0.10},
        {"desde": 10000, "hasta": 20000, "tipo": 0.20},
        {"desde": 20000, "hasta": None, "tipo": 0.30},
    ]
)


def test_aplicar_escala_base_cero():
    assert aplicar_escala(Decimal(0), ESCALA_SIMPLE) == Decimal(0)


def test_aplicar_escala_dentro_primer_tramo():
    # 5.000 * 10% = 500
    assert aplicar_escala(Decimal(5000), ESCALA_SIMPLE) == Decimal(500)


def test_aplicar_escala_en_limite_segundo_tramo():
    # 10.000 * 10% = 1.000 (el límite exacto se mantiene en el tramo anterior)
    assert aplicar_escala(Decimal(10000), ESCALA_SIMPLE) == Decimal(1000)


def test_aplicar_escala_dentro_segundo_tramo():
    # 15.000: 1.000 (primer tramo) + 5.000 * 20% = 1.000 + 1.000 = 2.000
    assert aplicar_escala(Decimal(15000), ESCALA_SIMPLE) == Decimal(2000)


def test_aplicar_escala_tercer_tramo_infinito():
    # 50.000: 1.000 + 2.000 + 30.000 * 30% = 3.000 + 9.000 = 12.000
    assert aplicar_escala(Decimal(50000), ESCALA_SIMPLE) == Decimal(12000)


def test_aplicar_escala_monotonia():
    anterior = Decimal(-1)
    for base in range(0, 100000, 1000):
        actual = aplicar_escala(Decimal(base), ESCALA_SIMPLE)
        assert actual >= anterior
        anterior = actual


def test_reduccion_rendimientos_trabajo_rn_bajo():
    params = {
        "umbral_maximo_base": 14852,
        "umbral_maximo": 17673.52,
        "importe_maximo": 7302,
        "pendiente": 1.75,
    }
    assert calcular_reduccion_trabajo(Decimal(10000), params) == Decimal(7302)


def test_reduccion_rendimientos_trabajo_zona_decreciente():
    params = {
        "umbral_maximo_base": 14852,
        "umbral_maximo": 17673.52,
        "importe_maximo": 7302,
        "pendiente": 1.75,
    }
    # 16.000: 7302 - 1.75 * (16000 - 14852) = 7302 - 2009 = 5293
    resultado = calcular_reduccion_trabajo(Decimal(16000), params)
    assert resultado == Decimal("5293")


def test_reduccion_rendimientos_trabajo_por_encima_umbral():
    params = {
        "umbral_maximo_base": 14852,
        "umbral_maximo": 17673.52,
        "importe_maximo": 7302,
        "pendiente": 1.75,
    }
    assert calcular_reduccion_trabajo(Decimal(25000), params) == Decimal(0)


def test_minimo_personal_base():
    minimos = {
        "personal": 5550,
        "edad_mayor_65": 1150,
        "por_descendiente": [2400, 2700, 4000, 4500],
        "hijo_menor_3": 2800,
        "por_ascendiente": 1150,
        "discapacidad_33_65": 3000,
    }
    entrada = InputIRPF(año=2025, territorio="madrid", edad_contribuyente=40)
    assert calcular_minimo_personal_familiar(entrada, minimos) == Decimal(5550)


def test_minimo_personal_con_hijos():
    minimos = {
        "personal": 5550,
        "edad_mayor_65": 1150,
        "por_descendiente": [2400, 2700, 4000, 4500],
        "hijo_menor_3": 2800,
        "por_ascendiente": 1150,
        "discapacidad_33_65": 3000,
    }
    entrada = InputIRPF(
        año=2025,
        territorio="madrid",
        edad_contribuyente=40,
        hijos=[Hijo(edad=2), Hijo(edad=5)],
    )
    # 5550 (personal) + 2400 (1º hijo) + 2800 (menor 3) + 2700 (2º hijo) = 13450
    assert calcular_minimo_personal_familiar(entrada, minimos) == Decimal(13450)


@pytest.fixture
def datos_estatal_2025():
    from helpers.data_loader import load_estatal

    return load_estatal(2025)


@pytest.fixture
def datos_madrid_2025():
    from helpers.data_loader import load_territorio

    return load_territorio(2025, "madrid")


def test_calcular_irpf_soltero_madrid_30k(datos_estatal_2025, datos_madrid_2025):
    entrada = InputIRPF(
        año=2025,
        territorio="madrid",
        rendimiento_neto_trabajo=Decimal(30000),
        edad_contribuyente=35,
    )
    resultado = calcular_irpf(entrada, datos_estatal_2025, datos_madrid_2025)

    assert resultado.regimen == "comun"
    assert resultado.cuota_integra_total > 0
    assert resultado.cuota_liquida > 0
    assert resultado.base_liquidable_general > 0
    # La cuota líquida debe estar en un rango razonable para 30k€ en Madrid
    # (≈4.800–6.200€ según tipo efectivo 16-20%).
    assert Decimal(4000) <= resultado.cuota_liquida <= Decimal(6500)


def test_calcular_irpf_sin_ingresos(datos_estatal_2025, datos_madrid_2025):
    entrada = InputIRPF(año=2025, territorio="madrid")
    resultado = calcular_irpf(entrada, datos_estatal_2025, datos_madrid_2025)
    assert resultado.cuota_liquida == Decimal(0)


def test_calcular_irpf_aplica_pagos_fraccionados_en_cuota_diferencial(
    datos_estatal_2025, datos_madrid_2025
):
    entrada = InputIRPF(
        año=2025,
        territorio="madrid",
        rendimiento_neto_trabajo=Decimal(30000),
        retenciones_practicadas=Decimal(1000),
        pagos_fraccionados=Decimal(500),
    )
    resultado = calcular_irpf(entrada, datos_estatal_2025, datos_madrid_2025)
    assert resultado.pagos_fraccionados == Decimal(500)
    assert resultado.cuota_diferencial < resultado.cuota_liquida


def test_calcular_irpf_base_ahorro_pura(datos_estatal_2025, datos_madrid_2025):
    entrada = InputIRPF(
        año=2025,
        territorio="madrid",
        rendimiento_neto_capital_mobiliario=Decimal(10000),
    )
    resultado = calcular_irpf(entrada, datos_estatal_2025, datos_madrid_2025)
    assert resultado.base_liquidable_ahorro == Decimal(10000)
    assert resultado.cuota_integra_total > 0
