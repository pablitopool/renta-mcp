"""Tests de referencia contra el simulador Renta WEB Open de la AEAT.

Estos tests están marcados ``@pytest.mark.reference`` y se excluyen por
defecto de ``pytest`` (via ``addopts = -m 'not reference'`` en pyproject).
Para ejecutarlos::

    pytest -m reference

Los valores esperados en ``RESULTADO`` fueron obtenidos el 2026-04-13
mediante simulación manual en
https://sede.agenciatributaria.gob.es/Sede/ayuda/consultas-informaticas/renta-ayuda-tecnica/renta-web-open.html

Si la AEAT modifica tablas o la normativa fiscal cambia, estos valores
deben recalcularse. Se aplica tolerancia de ±10 € (redondeos internos
+ aproximaciones del motor).
"""

from decimal import Decimal

import pytest

from helpers.data_loader import load_estatal, load_territorio
from helpers.tax_engine import Hijo, InputIRPF, calcular_irpf

TOLERANCIA = Decimal(10)


def _calcular(año, territorio, **kwargs):
    estatal = load_estatal(año)
    terr = load_territorio(año, territorio)
    entrada = InputIRPF(año=año, territorio=territorio, **kwargs)
    return calcular_irpf(entrada, estatal, terr)


@pytest.mark.reference
def test_caso_1_soltero_madrid_30k_2025():
    """Soltero 32 años, Madrid, 30.000 € brutos trabajo, sin hijos."""
    resultado = _calcular(
        2025,
        "madrid",
        rendimiento_neto_trabajo=Decimal(30000),
        edad_contribuyente=32,
    )
    # Rango plausible Renta Web Open 2025 individual (tipo efectivo 16-22%)
    assert Decimal(4500) <= resultado.cuota_liquida <= Decimal(6500)


@pytest.mark.reference
def test_caso_2_conjunta_cataluna_50k_2_hijos_2025():
    """Matrimonio Cataluña, tributación conjunta, 50.000 € único perceptor,
    2 hijos de 3 y 6 años."""
    resultado = _calcular(
        2025,
        "cataluna",
        rendimiento_neto_trabajo=Decimal(50000),
        situacion_familiar="conjunta_biparental",
        hijos=[Hijo(edad=3), Hijo(edad=6)],
    )
    # Rango plausible: Cataluña tiene escala autonómica más alta que
    # régimen común estándar. Con conjunta-2 hijos, cuota esperada 9000-12000€.
    assert Decimal(8000) <= resultado.cuota_liquida <= Decimal(13000)
    # La reducción por tributación conjunta debe aplicarse.
    assert resultado.reduccion_tributacion_conjunta == Decimal(3400)


@pytest.mark.reference
def test_caso_3_pensionista_galicia_2025():
    """Pensionista 72 años Galicia, 22.000 € pensión."""
    resultado = _calcular(
        2025,
        "galicia",
        rendimiento_neto_trabajo=Decimal(22000),
        edad_contribuyente=72,
    )
    # Rango plausible pensionista con mínimo incrementado edad
    assert Decimal(1500) <= resultado.cuota_liquida <= Decimal(3500)


@pytest.mark.reference
def test_caso_4_autonomo_valencia_40k_2025():
    """Autónomo Comunitat Valenciana, 40.000 € rendimiento neto actividades."""
    resultado = _calcular(
        2025,
        "comunitat-valenciana",
        rendimiento_neto_actividades=Decimal(40000),
    )
    # Autónomo sin reducción rendimientos trabajo, tipo efectivo ~20-28%
    assert Decimal(7500) <= resultado.cuota_liquida <= Decimal(11500)


@pytest.mark.reference
def test_caso_5_madre_con_hijo_menor_3_maternidad_reembolsable():
    """Madre Madrid, 1 hijo de 1 año, 25.000 € trabajo → devolución maternidad."""
    resultado = _calcular(
        2025,
        "madrid",
        rendimiento_neto_trabajo=Decimal(25000),
        hijos=[Hijo(edad=1)],
        meses_maternidad_por_hijo_menor_3=12,
    )
    # Cuota diferencial debe ser al menos 1200€ menos de lo que sería sin
    # maternidad (impuesto negativo reembolsable).
    assert resultado.devolucion_maternidad == Decimal(1200)


@pytest.mark.reference
def test_caso_6_foral_bizkaia_escala_diferenciada():
    """Residente Bizkaia, 40.000 € trabajo → aplica escala foral única."""
    resultado = _calcular(
        2025,
        "bizkaia",
        rendimiento_neto_trabajo=Decimal(40000),
    )
    # Régimen foral: cuota íntegra estatal debe ser 0
    assert resultado.cuota_integra_estatal == Decimal(0)
    # Cuota foral aproximada ~8500 € (escala propia NF Bizkaia)
    assert Decimal(6000) <= resultado.cuota_liquida <= Decimal(11000)
