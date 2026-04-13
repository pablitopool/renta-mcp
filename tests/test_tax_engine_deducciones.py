"""Tests de deducciones estatales + maternidad (Fase 7)."""

from decimal import Decimal

import pytest

from helpers.data_loader import load_estatal, load_territorio
from helpers.tax_engine import (
    Hijo,
    InputIRPF,
    aplicar_deducciones_estatales,
    calcular_irpf,
    calcular_maternidad_reembolsable,
)


@pytest.fixture
def datos_estatal_2025():
    return load_estatal(2025)


@pytest.fixture
def datos_madrid_2025():
    return load_territorio(2025, "madrid")


def test_deduccion_donativos_ley_49_2002_tramo_bajo(datos_estatal_2025):
    entrada = InputIRPF(
        año=2025, territorio="madrid", donativos_ley_49_2002=Decimal(200)
    )
    # 200€ está todo en el primer tramo → 200 * 0.80 = 160
    total, _ = aplicar_deducciones_estatales(
        Decimal(5000), Decimal(20000), entrada, datos_estatal_2025
    )
    assert total == Decimal(160)


def test_deduccion_donativos_ley_49_2002_dos_tramos(datos_estatal_2025):
    entrada = InputIRPF(
        año=2025, territorio="madrid", donativos_ley_49_2002=Decimal(500)
    )
    # 250 * 0.80 + 250 * 0.40 = 200 + 100 = 300
    total, _ = aplicar_deducciones_estatales(
        Decimal(5000), Decimal(20000), entrada, datos_estatal_2025
    )
    assert total == Decimal(300)


def test_deduccion_familia_numerosa_general(datos_estatal_2025):
    entrada = InputIRPF(
        año=2025, territorio="madrid", familia_numerosa_categoria="general"
    )
    total, _ = aplicar_deducciones_estatales(
        Decimal(5000), Decimal(20000), entrada, datos_estatal_2025
    )
    assert total == Decimal(1200)


def test_deduccion_familia_numerosa_especial(datos_estatal_2025):
    entrada = InputIRPF(
        año=2025, territorio="madrid", familia_numerosa_categoria="especial"
    )
    total, _ = aplicar_deducciones_estatales(
        Decimal(5000), Decimal(20000), entrada, datos_estatal_2025
    )
    assert total == Decimal(2400)


def test_deduccion_vivienda_transitoria(datos_estatal_2025):
    entrada = InputIRPF(
        año=2025,
        territorio="madrid",
        inversion_vivienda_transitoria=Decimal(10000),
    )
    # Base máxima 9040 * 15% = 1356
    total, _ = aplicar_deducciones_estatales(
        Decimal(5000), Decimal(20000), entrada, datos_estatal_2025
    )
    assert total == Decimal(1356)


def test_deduccion_obras_eficiencia_consumo_primaria(datos_estatal_2025):
    entrada = InputIRPF(
        año=2025,
        territorio="madrid",
        obras_eficiencia_energetica=Decimal(3000),
        obras_eficiencia_energetica_tipo="consumo_primaria",
    )
    # 3000 * 0.40 = 1200
    total, _ = aplicar_deducciones_estatales(
        Decimal(5000), Decimal(20000), entrada, datos_estatal_2025
    )
    assert total == Decimal(1200)


def test_deducciones_limitadas_por_cuota_integra_estatal(datos_estatal_2025):
    # Donativos 10.000€ generarían ~4.000€ de deducción, pero cuota íntegra
    # estatal sólo de 200€; la deducción queda limitada.
    entrada = InputIRPF(
        año=2025,
        territorio="madrid",
        donativos_ley_49_2002=Decimal(10000),
    )
    total, _ = aplicar_deducciones_estatales(
        Decimal(200), Decimal(5000), entrada, datos_estatal_2025
    )
    assert total == Decimal(200)


def test_maternidad_1_hijo_menor_3_año_completo(datos_estatal_2025):
    entrada = InputIRPF(
        año=2025,
        territorio="madrid",
        hijos=[Hijo(edad=1)],
        meses_maternidad_por_hijo_menor_3=12,
    )
    assert calcular_maternidad_reembolsable(entrada, datos_estatal_2025) == Decimal(
        1200
    )


def test_maternidad_2_hijos_menores_3(datos_estatal_2025):
    entrada = InputIRPF(
        año=2025,
        territorio="madrid",
        hijos=[Hijo(edad=1), Hijo(edad=2)],
        meses_maternidad_por_hijo_menor_3=12,
    )
    assert calcular_maternidad_reembolsable(entrada, datos_estatal_2025) == Decimal(
        2400
    )


def test_maternidad_sin_hijos_menores_3(datos_estatal_2025):
    entrada = InputIRPF(
        año=2025, territorio="madrid", hijos=[Hijo(edad=5), Hijo(edad=8)]
    )
    assert calcular_maternidad_reembolsable(entrada, datos_estatal_2025) == Decimal(0)


def test_maternidad_parcial_6_meses(datos_estatal_2025):
    entrada = InputIRPF(
        año=2025,
        territorio="madrid",
        hijos=[Hijo(edad=1)],
        meses_maternidad_por_hijo_menor_3=6,
    )
    # 100 * 6 = 600
    assert calcular_maternidad_reembolsable(entrada, datos_estatal_2025) == Decimal(600)


def test_calculo_irpf_con_maternidad_devuelve_incluso_si_cuota_cero(
    datos_estatal_2025, datos_madrid_2025
):
    # Madre con 1 hijo <3, renta muy baja → cuota líquida 0 → debe devolver 1200
    entrada = InputIRPF(
        año=2025,
        territorio="madrid",
        rendimiento_neto_trabajo=Decimal(10000),
        hijos=[Hijo(edad=1)],
        meses_maternidad_por_hijo_menor_3=12,
    )
    resultado = calcular_irpf(entrada, datos_estatal_2025, datos_madrid_2025)
    assert resultado.devolucion_maternidad == Decimal(1200)
    # Cuota diferencial debe ser negativa (devolución)
    assert resultado.cuota_diferencial <= Decimal(-1200) + Decimal("0.01")


def test_calculo_irpf_con_deducciones_reduce_cuota_liquida(
    datos_estatal_2025, datos_madrid_2025
):
    entrada_base = InputIRPF(
        año=2025, territorio="madrid", rendimiento_neto_trabajo=Decimal(35000)
    )
    entrada_con_donativo = InputIRPF(
        año=2025,
        territorio="madrid",
        rendimiento_neto_trabajo=Decimal(35000),
        donativos_ley_49_2002=Decimal(500),
    )
    base = calcular_irpf(entrada_base, datos_estatal_2025, datos_madrid_2025)
    con_donativo = calcular_irpf(
        entrada_con_donativo, datos_estatal_2025, datos_madrid_2025
    )
    assert con_donativo.deducciones_estatales_total > 0
    assert con_donativo.cuota_liquida < base.cuota_liquida
