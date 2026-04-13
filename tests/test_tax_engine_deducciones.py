"""Tests de deducciones estatales + maternidad (Fase 7)."""

from decimal import Decimal

import pytest

from helpers.data_loader import load_estatal, load_territorio
from helpers.tax_engine import (
    Ascendiente,
    EntradaInvalida,
    Hijo,
    InputIRPF,
    aplicar_deducciones_autonomicas,
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


@pytest.fixture
def datos_cv_2025():
    return load_territorio(2025, "comunitat-valenciana")


@pytest.fixture
def datos_bizkaia_2025():
    return load_territorio(2025, "bizkaia")


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


def test_deduccion_autonomica_cv_alquiler_aplica_limite(datos_cv_2025):
    entrada = InputIRPF(
        año=2025,
        territorio="comunitat-valenciana",
        hijos=[Hijo(edad=4)],
        deducciones_autonomicas_reclamadas=["cv-alquiler-vivienda-habitual"],
        bases_deducciones_autonomicas={"cv-alquiler-vivienda-habitual": Decimal(5000)},
    )
    total, detalle = aplicar_deducciones_autonomicas(
        Decimal(4000), Decimal(25000), Decimal(0), entrada, datos_cv_2025
    )
    assert total == Decimal(550)
    assert any("cv-alquiler-vivienda-habitual" in p.detalle for p in detalle)


def test_deduccion_autonomica_madrid_familia_numerosa_porcentaje_cuota(
    datos_madrid_2025,
):
    entrada = InputIRPF(
        año=2025,
        territorio="madrid",
        familia_numerosa_categoria="general",
        deducciones_autonomicas_reclamadas=["mad-familia-numerosa"],
    )
    total, _ = aplicar_deducciones_autonomicas(
        Decimal(3000), Decimal(30000), Decimal(0), entrada, datos_madrid_2025
    )
    assert total == Decimal(300)


def test_calculo_irpf_foral_con_deduccion_autonomica_reduce_cuota(
    datos_estatal_2025, datos_bizkaia_2025
):
    entrada_base = InputIRPF(
        año=2025,
        territorio="bizkaia",
        rendimiento_neto_trabajo=Decimal(40000),
    )
    entrada_con_deduccion = InputIRPF(
        año=2025,
        territorio="bizkaia",
        rendimiento_neto_trabajo=Decimal(40000),
        deducciones_autonomicas_reclamadas=["biz-donativos"],
        bases_deducciones_autonomicas={"biz-donativos": Decimal(1000)},
    )
    base = calcular_irpf(entrada_base, datos_estatal_2025, datos_bizkaia_2025)
    con_deduccion = calcular_irpf(
        entrada_con_deduccion, datos_estatal_2025, datos_bizkaia_2025
    )
    assert con_deduccion.deducciones_autonomicas_total == Decimal(300)
    assert con_deduccion.cuota_liquida < base.cuota_liquida


def test_deduccion_autonomica_desconocida_lanza_error(datos_cv_2025):
    entrada = InputIRPF(
        año=2025,
        territorio="comunitat-valenciana",
        deducciones_autonomicas_reclamadas=["cv-no-existe"],
    )
    with pytest.raises(Exception):
        aplicar_deducciones_autonomicas(
            Decimal(1000), Decimal(10000), Decimal(0), entrada, datos_cv_2025
        )


def test_calculo_irpf_auto_aplica_guarderia_cv(datos_estatal_2025, datos_cv_2025):
    entrada = InputIRPF(
        año=2025,
        territorio="comunitat-valenciana",
        rendimiento_neto_trabajo=Decimal(32000),
        hijos=[Hijo(edad=2)],
        gastos_guarderia=Decimal(3000),
    )
    resultado = calcular_irpf(entrada, datos_estatal_2025, datos_cv_2025)
    assert resultado.deducciones_autonomicas_total == Decimal(270)
    assert any(
        "cv-gastos-guarderia" in p.detalle
        for p in resultado.deducciones_autonomicas_detalle
    )


def test_calculo_irpf_auto_aplica_madrid_gastos_educacion(
    datos_estatal_2025, datos_madrid_2025
):
    entrada = InputIRPF(
        año=2025,
        territorio="madrid",
        rendimiento_neto_trabajo=Decimal(34000),
        hijos=[Hijo(edad=8)],
        gastos_escolaridad=Decimal(1000),
        gastos_idiomas=Decimal(500),
        gastos_uniformes=Decimal(400),
    )
    resultado = calcular_irpf(entrada, datos_estatal_2025, datos_madrid_2025)
    assert resultado.deducciones_autonomicas_total == Decimal(220)
    assert any(
        "mad-gastos-educacion" in p.detalle
        for p in resultado.deducciones_autonomicas_detalle
    )


def test_calculo_irpf_auto_aplica_familia_numerosa_madrid(
    datos_estatal_2025, datos_madrid_2025
):
    entrada = InputIRPF(
        año=2025,
        territorio="madrid",
        rendimiento_neto_trabajo=Decimal(30000),
        familia_numerosa_categoria="general",
    )
    resultado = calcular_irpf(entrada, datos_estatal_2025, datos_madrid_2025)
    assert resultado.deducciones_autonomicas_total > 0
    assert any(
        "mad-familia-numerosa" in p.detalle
        for p in resultado.deducciones_autonomicas_detalle
    )


def test_calculo_irpf_auto_aplica_cuidado_ascendientes_madrid(
    datos_estatal_2025, datos_madrid_2025
):
    entrada = InputIRPF(
        año=2025,
        territorio="madrid",
        rendimiento_neto_trabajo=Decimal(28000),
        ascendientes=[Ascendiente(edad=70), Ascendiente(edad=80)],
    )
    resultado = calcular_irpf(entrada, datos_estatal_2025, datos_madrid_2025)
    assert resultado.deducciones_autonomicas_total == Decimal("1031.00")
    assert any(
        "mad-cuidado-ascendientes" in p.detalle
        for p in resultado.deducciones_autonomicas_detalle
    )


def test_calculo_irpf_auto_aplica_acogimiento_familiar_menores_madrid(
    datos_estatal_2025, datos_madrid_2025
):
    entrada = InputIRPF(
        año=2025,
        territorio="madrid",
        acogimientos_menores=3,
    )
    total, detalle = aplicar_deducciones_autonomicas(
        Decimal(5000), Decimal(24000), Decimal(0), entrada, datos_madrid_2025
    )
    assert total == Decimal("2319.75")
    assert any("mad-acogimiento-familiar-menores" in p.detalle for p in detalle)


def test_calculo_irpf_auto_aplica_cuidado_dependientes_madrid(
    datos_estatal_2025, datos_madrid_2025
):
    entrada = InputIRPF(
        año=2025,
        territorio="madrid",
        rendimiento_neto_trabajo=Decimal(30000),
        hijos=[Hijo(edad=2)],
        cotizaciones_empleados_hogar=Decimal(2000),
    )
    resultado = calcular_irpf(entrada, datos_estatal_2025, datos_madrid_2025)
    assert resultado.deducciones_autonomicas_total == Decimal("463.95")
    assert any(
        "mad-cuidado-hijos-menores-mayores-discapacidad" in p.detalle
        for p in resultado.deducciones_autonomicas_detalle
    )


def test_calculo_irpf_auto_aplica_cuidado_dependientes_madrid_familia_numerosa(
    datos_estatal_2025, datos_madrid_2025
):
    entrada = InputIRPF(
        año=2025,
        territorio="madrid",
        rendimiento_neto_trabajo=Decimal(30000),
        hijos=[Hijo(edad=2)],
        familia_numerosa_categoria="general",
        cotizaciones_empleados_hogar=Decimal(2000),
    )
    resultado = calcular_irpf(entrada, datos_estatal_2025, datos_madrid_2025)
    paso = next(
        p
        for p in resultado.deducciones_autonomicas_detalle
        if "mad-cuidado-hijos-menores-mayores-discapacidad" in p.detalle
    )
    assert paso.importe == Decimal("618.60")


def test_deduccion_autonomica_madrid_gastos_arrendamiento_viviendas(
    datos_madrid_2025,
):
    entrada = InputIRPF(
        año=2025,
        territorio="madrid",
        gastos_arrendamiento_viviendas=Decimal(2000),
    )
    total, detalle = aplicar_deducciones_autonomicas(
        Decimal(5000), Decimal(30000), Decimal(0), entrada, datos_madrid_2025
    )
    assert total == Decimal("154.65")
    assert any("mad-gastos-arrendamiento-viviendas" in p.detalle for p in detalle)


def test_deduccion_autonomica_madrid_intereses_prestamo_vivienda_joven(
    datos_madrid_2025,
):
    entrada = InputIRPF(
        año=2025,
        territorio="madrid",
        edad_contribuyente=29,
        intereses_prestamo_adquisicion_vivienda_joven=Decimal(5000),
    )
    total, detalle = aplicar_deducciones_autonomicas(
        Decimal(5000), Decimal(30000), Decimal(0), entrada, datos_madrid_2025
    )
    assert total == Decimal("1031.00")
    assert any("mad-intereses-prestamo-vivienda-joven" in p.detalle for p in detalle)


def test_deduccion_autonomica_madrid_intereses_prestamo_vivienda_joven_no_aplica_por_edad(
    datos_madrid_2025,
):
    entrada = InputIRPF(
        año=2025,
        territorio="madrid",
        edad_contribuyente=30,
        intereses_prestamo_adquisicion_vivienda_joven=Decimal(5000),
    )
    total, _ = aplicar_deducciones_autonomicas(
        Decimal(5000), Decimal(30000), Decimal(0), entrada, datos_madrid_2025
    )
    assert total == Decimal("0")


def test_deduccion_autonomica_madrid_cambio_residencia_despoblacion(
    datos_madrid_2025,
):
    entrada = InputIRPF(
        año=2025,
        territorio="madrid",
        edad_contribuyente=34,
        cambios_residencia_municipio_despoblacion=1,
        hijos=[Hijo(edad=5)],
    )
    total, detalle = aplicar_deducciones_autonomicas(
        Decimal(5000), Decimal(40000), Decimal(0), entrada, datos_madrid_2025
    )
    assert total == Decimal("1000")
    assert any("mad-cambio-residencia-despoblacion" in p.detalle for p in detalle)


def test_deduccion_autonomica_madrid_adquisicion_vivienda_despoblacion(
    datos_madrid_2025,
):
    entrada = InputIRPF(
        año=2025,
        territorio="madrid",
        edad_contribuyente=30,
        inversion_vivienda_habitual_municipio_despoblacion=Decimal(100000),
    )
    total, detalle = aplicar_deducciones_autonomicas(
        Decimal(5000), Decimal(25000), Decimal(0), entrada, datos_madrid_2025
    )
    assert total == Decimal("1000")
    assert any("mad-adquisicion-vivienda-despoblacion" in p.detalle for p in detalle)


def test_deduccion_autonomica_madrid_incremento_costes_financiacion(
    datos_madrid_2025,
):
    entrada = InputIRPF(
        año=2025,
        territorio="madrid",
        exceso_intereses_financiacion_vivienda=Decimal(1400),
        hijos=[Hijo(edad=4)],
    )
    total, detalle = aplicar_deducciones_autonomicas(
        Decimal(5000), Decimal(30000), Decimal(0), entrada, datos_madrid_2025
    )
    assert total == Decimal("300")
    assert any("mad-incremento-costes-financiacion" in p.detalle for p in detalle)


def test_deduccion_autonomica_madrid_arrendamiento_viviendas_vacias(
    datos_madrid_2025,
):
    entrada = InputIRPF(
        año=2025,
        territorio="madrid",
        viviendas_vacias_arrendadas=2,
    )
    total, detalle = aplicar_deducciones_autonomicas(
        Decimal(5000), Decimal(30000), Decimal(0), entrada, datos_madrid_2025
    )
    assert total == Decimal("2000")
    assert any("mad-arrendamiento-viviendas-vacias" in p.detalle for p in detalle)


def test_calculo_irpf_valida_importes_negativos(datos_estatal_2025, datos_cv_2025):
    entrada = InputIRPF(
        año=2025,
        territorio="comunitat-valenciana",
        rendimiento_neto_trabajo=Decimal(30000),
        alquiler_vivienda_habitual=Decimal(-1),
    )
    with pytest.raises(EntradaInvalida):
        calcular_irpf(entrada, datos_estatal_2025, datos_cv_2025)


def test_calculo_irpf_valida_acogimientos_negativos(
    datos_estatal_2025, datos_madrid_2025
):
    entrada = InputIRPF(
        año=2025,
        territorio="madrid",
        rendimiento_neto_trabajo=Decimal(30000),
        acogimientos_menores=-1,
    )
    with pytest.raises(EntradaInvalida):
        calcular_irpf(entrada, datos_estatal_2025, datos_madrid_2025)
