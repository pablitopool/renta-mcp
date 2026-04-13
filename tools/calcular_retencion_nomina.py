"""Tool MCP: ``calcular_retencion_nomina``.

Aproximación del procedimiento general de retenciones sobre rendimientos del
trabajo (art. 80 RIRPF y concordantes). Calcula el tipo de retención
aplicando el motor IRPF y dividiendo la cuota resultante entre el
rendimiento neto previsto, para obtener un porcentaje anual.
"""

from decimal import Decimal
from typing import List, Literal, Optional

from mcp.server.fastmcp import FastMCP

from helpers.data_loader import load_estatal, load_territorio
from helpers.logging import log_tool
from helpers.tax_engine import (
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


async def calcular_retencion_nomina_impl(
    año: int,
    territorio: str,
    salario_bruto_anual: float,
    situacion_familiar: Literal[
        "individual", "conjunta_biparental", "conjunta_monoparental"
    ] = "individual",
    hijos_edades: Optional[List[int]] = None,
    edad_contribuyente: int = 40,
    discapacidad_contribuyente: int = 0,
    meses_pago: int = 14,
) -> str:
    if salario_bruto_anual <= 0:
        raise EntradaInvalida("El salario bruto anual debe ser positivo")
    if meses_pago not in (12, 14):
        raise EntradaInvalida("meses_pago debe ser 12 o 14")

    entrada = InputIRPF(
        año=año,
        territorio=territorio.lower(),
        rendimiento_neto_trabajo=Decimal(str(salario_bruto_anual)),
        situacion_familiar=situacion_familiar,
        hijos=[Hijo(edad=e) for e in (hijos_edades or [])],
        edad_contribuyente=edad_contribuyente,
        discapacidad_contribuyente=discapacidad_contribuyente,
    )
    estatal = load_estatal(año)
    territorio_datos = load_territorio(año, entrada.territorio)
    resultado = calcular_irpf(entrada, estatal, territorio_datos)

    bruto = Decimal(str(salario_bruto_anual))
    tipo_retencion = (resultado.cuota_liquida / bruto * Decimal(100)).quantize(
        Decimal("0.01")
    )
    retencion_por_paga = (resultado.cuota_liquida / Decimal(meses_pago)).quantize(
        Decimal("0.01")
    )
    neto_por_paga = ((bruto - resultado.cuota_liquida) / Decimal(meses_pago)).quantize(
        Decimal("0.01")
    )

    nombre = territorio_datos["territorio"]["nombre"]
    return (
        f"## Retención IRPF estimada — {nombre} {año}\n\n"
        f"- **Salario bruto anual**: {bruto} €\n"
        f"- **Cuota IRPF anual (aprox.)**: {resultado.cuota_liquida} €\n"
        f"- **Tipo de retención efectivo**: {tipo_retencion} %\n"
        f"- **Retención por paga** ({meses_pago} pagas): {retencion_por_paga} €\n"
        f"- **Neto por paga** ({meses_pago} pagas): {neto_por_paga} €\n\n"
        "_Aproximación basada en el cálculo IRPF completo. El procedimiento "
        "real del art. 80 RIRPF incluye ajustes (regularizaciones, situación "
        "familiar comunicada al pagador, etc.) que pueden variar el resultado._"
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
        edad_contribuyente: int = 40,
        discapacidad_contribuyente: int = 0,
        meses_pago: int = 14,
    ) -> str:
        """Calcula la retención IRPF estimada sobre la nómina.

        Parámetros clave:
        - ``salario_bruto_anual``: retribución bruta anual (sin descontar SS).
        - ``meses_pago``: 12 o 14 (pagas prorrateadas vs. extras).

        Devuelve tipo de retención, retención mensual y neto estimado.
        """
        try:
            return await calcular_retencion_nomina_impl(
                año=año,
                territorio=territorio,
                salario_bruto_anual=salario_bruto_anual,
                situacion_familiar=situacion_familiar,
                hijos_edades=hijos_edades,
                edad_contribuyente=edad_contribuyente,
                discapacidad_contribuyente=discapacidad_contribuyente,
                meses_pago=meses_pago,
            )
        except EntradaInvalida as exc:
            raise_entrada_invalida(exc)
        except DatosFiscalesNoDisponibles as exc:
            raise_datos_no_disponibles(exc)
        except Exception as exc:  # noqa: BLE001
            raise_unexpected(exc)
