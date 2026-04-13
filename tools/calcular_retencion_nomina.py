"""Tool MCP: ``calcular_retencion_nomina``.

Estimación procedimental de la retención sobre rendimientos del trabajo
(art. 80 RIRPF y concordantes). Parte del salario bruto anual y explicita las
hipótesis usadas para llegar a una retención anual y por paga estables.
"""

from decimal import Decimal
from typing import List, Literal, Optional

from mcp.server.fastmcp import FastMCP

from helpers.data_loader import load_estatal, load_territorio
from helpers.logging import log_tool
from helpers.tax_engine import (
    Ascendiente,
    DatosFiscalesNoDisponibles,
    EntradaInvalida,
    Hijo,
    InputIRPF,
    calcular_irpf,
)
from tools.error_handling import (
    raise_datos_no_disponibles,
    raise_entrada_invalida,
    raise_unexpected,
)

GASTOS_DEDUCIBLES_TRABAJO_ESTANDAR = Decimal("2000")
TIPO_SS_EMPLEADO_ESTIMADO = Decimal("0.0648")
DECIMALES = Decimal("0.01")


def _estimar_cotizaciones_seguridad_social(bruto: Decimal) -> Decimal:
    return bruto * TIPO_SS_EMPLEADO_ESTIMADO


def _redondear_euros(valor: Decimal) -> Decimal:
    return valor.quantize(DECIMALES)


async def calcular_retencion_nomina_impl(
    año: int,
    territorio: str,
    salario_bruto_anual: float,
    situacion_familiar: Literal[
        "individual", "conjunta_biparental", "conjunta_monoparental"
    ] = "individual",
    hijos_edades: Optional[List[int]] = None,
    ascendientes_edades: Optional[List[int]] = None,
    edad_contribuyente: int = 40,
    discapacidad_contribuyente: int = 0,
    meses_pago: int = 14,
    cotizaciones_seguridad_social: Optional[float] = None,
    otros_gastos_deducibles: float = 0.0,
) -> str:
    if salario_bruto_anual <= 0:
        raise EntradaInvalida("El salario bruto anual debe ser positivo")
    if meses_pago not in (12, 14):
        raise EntradaInvalida("meses_pago debe ser 12 o 14")
    if otros_gastos_deducibles < 0:
        raise EntradaInvalida("otros_gastos_deducibles no puede ser negativo")
    if (
        cotizaciones_seguridad_social is not None
        and cotizaciones_seguridad_social < 0
    ):
        raise EntradaInvalida("cotizaciones_seguridad_social no puede ser negativo")

    bruto = Decimal(str(salario_bruto_anual))
    if (
        cotizaciones_seguridad_social is not None
        and Decimal(str(cotizaciones_seguridad_social)) > bruto
    ):
        raise EntradaInvalida(
            "cotizaciones_seguridad_social no puede superar el salario bruto anual"
        )
    cotizaciones_estimadas = cotizaciones_seguridad_social is None
    cotizaciones = (
        Decimal(str(cotizaciones_seguridad_social))
        if not cotizaciones_estimadas
        else _estimar_cotizaciones_seguridad_social(bruto)
    )
    otros_gastos = Decimal(str(otros_gastos_deducibles))
    gastos_trabajo = GASTOS_DEDUCIBLES_TRABAJO_ESTANDAR + otros_gastos
    rendimiento_neto_trabajo = max(bruto - cotizaciones - gastos_trabajo, Decimal(0))

    entrada = InputIRPF(
        año=año,
        territorio=territorio.lower(),
        rendimiento_neto_trabajo=rendimiento_neto_trabajo,
        situacion_familiar=situacion_familiar,
        hijos=[Hijo(edad=e) for e in (hijos_edades or [])],
        ascendientes=[Ascendiente(edad=e) for e in (ascendientes_edades or [])],
        edad_contribuyente=edad_contribuyente,
        discapacidad_contribuyente=discapacidad_contribuyente,
    )
    estatal = load_estatal(año)
    territorio_datos = load_territorio(año, entrada.territorio)
    resultado = calcular_irpf(entrada, estatal, territorio_datos)

    minimo_personal_familiar = resultado.minimo_personal_familiar
    base_sometida_retencion = max(
        rendimiento_neto_trabajo - minimo_personal_familiar, Decimal(0)
    )
    cuota_anual_estimada = resultado.cuota_liquida
    tipo_retencion = _redondear_euros((cuota_anual_estimada / bruto) * Decimal(100))
    retencion_anual = cuota_anual_estimada
    retencion_por_paga = _redondear_euros(retencion_anual / Decimal(meses_pago))
    neto_anual_estimado = bruto - cotizaciones - retencion_anual
    neto_por_paga = _redondear_euros(neto_anual_estimado / Decimal(meses_pago))
    hipotesis_cotizaciones = (
        "Cotizaciones informadas por el usuario."
        if not cotizaciones_estimadas
        else (
            "Cotizaciones estimadas al "
            f"{_redondear_euros(TIPO_SS_EMPLEADO_ESTIMADO * Decimal(100))} % "
            "del salario bruto anual."
        )
    )

    nombre = territorio_datos["territorio"]["nombre"]
    return (
        f"## Retención IRPF estimada — {nombre} {año}\n\n"
        f"- **Salario bruto anual**: {_redondear_euros(bruto)} €\n"
        f"- **Cotizaciones Seguridad Social usadas**: {_redondear_euros(cotizaciones)} €\n"
        f"- **Gastos deducibles del trabajo usados**: {_redondear_euros(gastos_trabajo)} €\n"
        f"- **Rendimiento neto del trabajo estimado**: {_redondear_euros(rendimiento_neto_trabajo)} €\n"
        f"- **Mínimo personal y familiar aplicado**: {_redondear_euros(minimo_personal_familiar)} €\n"
        f"- **Base sometida a retención estimada**: {_redondear_euros(base_sometida_retencion)} €\n"
        f"- **Cuota anual estimada**: {_redondear_euros(cuota_anual_estimada)} €\n"
        f"- **Tipo de retención efectivo**: {tipo_retencion} %\n"
        f"- **Retención anual estimada**: {_redondear_euros(retencion_anual)} €\n"
        f"- **Retención por paga** ({meses_pago} pagas): {retencion_por_paga} €\n"
        f"- **Neto por paga** ({meses_pago} pagas): {neto_por_paga} €\n\n"
        f"_Hipótesis SS: {hipotesis_cotizaciones}_\n\n"
        "_Estimación procedimental no vinculante: parte del bruto anual, "
        "resta cotizaciones del trabajador y gastos deducibles del trabajo, "
        "aplica el mínimo personal y familiar relevante y reutiliza el motor "
        "IRPF para aproximar la cuota anual. El procedimiento real del art. 80 "
        "RIRPF sigue incluyendo regularizaciones y reglas del pagador que "
        "pueden mover el resultado._"
    )


def register_calcular_retencion_nomina_tool(mcp: FastMCP) -> None:
    @mcp.tool()
    @log_tool
    async def calcular_retencion_nomina(
        año: int,
        territorio: str,
        salario_bruto_anual: float,
        situacion_familiar: Literal[
            "individual", "conjunta_biparental", "conjunta_monoparental"
        ] = "individual",
        hijos_edades: Optional[List[int]] = None,
        ascendientes_edades: Optional[List[int]] = None,
        edad_contribuyente: int = 40,
        discapacidad_contribuyente: int = 0,
        meses_pago: int = 14,
        cotizaciones_seguridad_social: Optional[float] = None,
        otros_gastos_deducibles: float = 0.0,
    ) -> str:
        """Calcula una estimación procedimental de la retención IRPF en nómina.

        Parámetros clave:
        - ``salario_bruto_anual``: retribución bruta anual (sin descontar SS).
        - ``meses_pago``: 12 o 14 (pagas prorrateadas vs. extras).
        - ``cotizaciones_seguridad_social``: override explícito; si no se
          informa, se estima y la hipótesis queda reflejada en la salida.
        - ``otros_gastos_deducibles``: gastos adicionales del trabajo, sobre
          el mínimo general de 2.000 €.
        - ``ascendientes_edades``: ascendientes a cargo a considerar en el
          mínimo personal y familiar.

        Devuelve bruto, cotizaciones usadas, gastos deducibles usados,
        rendimiento neto estimado, mínimo relevante, base sometida a
        retención, cuota anual, tipo efectivo, retención por paga y neto
        por paga.
        """
        try:
            return await calcular_retencion_nomina_impl(
                año=año,
                territorio=territorio,
                salario_bruto_anual=salario_bruto_anual,
                situacion_familiar=situacion_familiar,
                hijos_edades=hijos_edades,
                ascendientes_edades=ascendientes_edades,
                edad_contribuyente=edad_contribuyente,
                discapacidad_contribuyente=discapacidad_contribuyente,
                meses_pago=meses_pago,
                cotizaciones_seguridad_social=cotizaciones_seguridad_social,
                otros_gastos_deducibles=otros_gastos_deducibles,
            )
        except EntradaInvalida as exc:
            raise_entrada_invalida(exc)
        except DatosFiscalesNoDisponibles as exc:
            raise_datos_no_disponibles(exc)
        except Exception as exc:  # noqa: BLE001
            raise_unexpected(exc)
