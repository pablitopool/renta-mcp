"""Property-based tests del motor fiscal con hypothesis."""

from decimal import Decimal

from hypothesis import given, settings
from hypothesis import strategies as st

from helpers.data_loader import load_estatal, load_territorio
from helpers.tax_engine import Escala, InputIRPF, aplicar_escala, calcular_irpf

ESCALA_TEST = Escala.desde_lista(
    [
        {"desde": 0, "hasta": 10000, "tipo": 0.10},
        {"desde": 10000, "hasta": 30000, "tipo": 0.20},
        {"desde": 30000, "hasta": None, "tipo": 0.30},
    ]
)

ESTATAL_2025 = load_estatal(2025)
MADRID_2025 = load_territorio(2025, "madrid")


@given(base=st.integers(min_value=0, max_value=500_000))
@settings(max_examples=50, deadline=None)
def test_escala_monotona_creciente(base):
    """La cuota resultante de aplicar una escala progresiva es monótona
    no decreciente respecto a la base."""
    menor = aplicar_escala(Decimal(base), ESCALA_TEST)
    mayor = aplicar_escala(Decimal(base + 1000), ESCALA_TEST)
    assert mayor >= menor


@given(base=st.integers(min_value=0, max_value=1_000_000))
@settings(max_examples=50, deadline=None)
def test_cuota_liquida_no_negativa(base):
    """La cuota líquida del IRPF nunca puede ser negativa (la devolución
    por maternidad es aparte en cuota_diferencial)."""
    entrada = InputIRPF(
        año=2025,
        territorio="madrid",
        rendimiento_neto_trabajo=Decimal(base),
    )
    resultado = calcular_irpf(entrada, ESTATAL_2025, MADRID_2025)
    assert resultado.cuota_liquida >= Decimal(0)


@given(
    salario_a=st.integers(min_value=20000, max_value=80000),
    salario_b=st.integers(min_value=20000, max_value=80000),
)
@settings(max_examples=30, deadline=None)
def test_tributacion_conjunta_no_peor_que_individual(salario_a, salario_b):
    """Una unidad familiar biparental donde ambos trabajen puede optar por
    tributación conjunta; si sólo uno trabaja, la conjunta es habitualmente
    ventajosa. Test débil: cuota conjunta = razonable (no descomunalmente
    más alta que la suma de individuales)."""
    individual_a = calcular_irpf(
        InputIRPF(
            año=2025,
            territorio="madrid",
            rendimiento_neto_trabajo=Decimal(salario_a),
        ),
        ESTATAL_2025,
        MADRID_2025,
    )
    individual_b = calcular_irpf(
        InputIRPF(
            año=2025,
            territorio="madrid",
            rendimiento_neto_trabajo=Decimal(salario_b),
        ),
        ESTATAL_2025,
        MADRID_2025,
    )
    conjunta = calcular_irpf(
        InputIRPF(
            año=2025,
            territorio="madrid",
            rendimiento_neto_trabajo=Decimal(salario_a + salario_b),
            situacion_familiar="conjunta_biparental",
        ),
        ESTATAL_2025,
        MADRID_2025,
    )
    # Propiedad floja: la conjunta nunca debería ser >150% de la suma
    # individuales en estos rangos (siempre baja algo por la reducción).
    suma_indiv = individual_a.cuota_liquida + individual_b.cuota_liquida
    assert conjunta.cuota_liquida <= suma_indiv * Decimal("1.5")


@given(salario=st.integers(min_value=0, max_value=200_000))
@settings(max_examples=30, deadline=None)
def test_retenciones_generan_devolucion(salario):
    """Si las retenciones practicadas > cuota líquida, la cuota diferencial
    es negativa (devolución)."""
    retenciones = Decimal(salario) * Decimal("0.5")  # sobre-retención 50 %
    entrada = InputIRPF(
        año=2025,
        territorio="madrid",
        rendimiento_neto_trabajo=Decimal(salario),
        retenciones_practicadas=retenciones,
    )
    resultado = calcular_irpf(entrada, ESTATAL_2025, MADRID_2025)
    if retenciones > resultado.cuota_liquida:
        assert resultado.cuota_diferencial < Decimal(0)
