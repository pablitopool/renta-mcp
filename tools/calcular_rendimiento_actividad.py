"""Tool MCP: ``calcular_rendimiento_actividad`` (autonomos, MVP)."""

from decimal import Decimal
from typing import Literal

from mcp.server.fastmcp import FastMCP

from helpers.logging import log_tool
from helpers.tax_engine import EntradaInvalida
from tools.error_handling import raise_entrada_invalida, raise_unexpected

DECIMALES = Decimal("0.01")


def _euros(valor: Decimal) -> Decimal:
    return valor.quantize(DECIMALES)


async def calcular_rendimiento_actividad_impl(
    regimen: Literal[
        "estimacion_directa_simplificada",
        "estimacion_directa_normal",
        "modulos_mvp",
    ],
    ingresos_integros: float,
    gastos_deducibles: float = 0.0,
    amortizaciones: float = 0.0,
    provisiones_y_gastos_justificados: float = 0.0,
    porcentaje_provisiones_eds: float = 0.05,
    limite_provisiones_eds: float = 2000.0,
    pagos_fraccionados_modelo_130_131: float = 0.0,
) -> str:
    ingresos = Decimal(str(ingresos_integros))
    gastos = Decimal(str(gastos_deducibles))
    amort = Decimal(str(amortizaciones))
    provisiones = Decimal(str(provisiones_y_gastos_justificados))
    pct_eds = Decimal(str(porcentaje_provisiones_eds))
    limite_eds = Decimal(str(limite_provisiones_eds))
    pagos = Decimal(str(pagos_fraccionados_modelo_130_131))

    if ingresos <= 0:
        raise EntradaInvalida("ingresos_integros debe ser mayor que 0")
    if gastos < 0 or amort < 0 or provisiones < 0 or pagos < 0:
        raise EntradaInvalida(
            "gastos, amortizaciones, provisiones y pagos no pueden ser negativos"
        )
    if pct_eds < 0 or pct_eds > 1:
        raise EntradaInvalida("porcentaje_provisiones_eds debe estar entre 0 y 1")
    if limite_eds < 0:
        raise EntradaInvalida("limite_provisiones_eds no puede ser negativo")

    rendimiento_previo = ingresos - gastos - amort
    if regimen == "estimacion_directa_simplificada":
        provisiones_aplicables = min(rendimiento_previo * pct_eds, limite_eds)
        provisiones_aplicables = max(provisiones_aplicables, Decimal(0))
        rendimiento_neto = max(rendimiento_previo - provisiones_aplicables, Decimal(0))
        nota = (
            "MVP EDS: aplica provisiones/gastos dificil justificacion como "
            f"{(pct_eds * Decimal(100))}% del rendimiento previo con limite "
            f"{_euros(limite_eds)} EUR."
        )
    elif regimen == "estimacion_directa_normal":
        rendimiento_neto = max(rendimiento_previo - provisiones, Decimal(0))
        provisiones_aplicables = provisiones
        nota = (
            "MVP EDN: usa provisiones y gastos justificados informados por el usuario."
        )
    else:
        rendimiento_neto = max(rendimiento_previo, Decimal(0))
        provisiones_aplicables = Decimal(0)
        nota = (
            "MVP modulos: aproximacion simplificada desde ingresos y gastos declarados. "
            "Para calculo oficial en modulos usa AEAT con datos censales completos."
        )

    return (
        "## Rendimiento neto de actividad estimado\n\n"
        f"- **Regimen**: {regimen}\n"
        f"- **Ingresos integros**: {_euros(ingresos)} EUR\n"
        f"- **Gastos deducibles**: {_euros(gastos)} EUR\n"
        f"- **Amortizaciones**: {_euros(amort)} EUR\n"
        f"- **Provisiones aplicadas**: {_euros(provisiones_aplicables)} EUR\n"
        f"- **Rendimiento neto actividad**: {_euros(rendimiento_neto)} EUR\n"
        f"- **Pagos fraccionados 130/131**: {_euros(pagos)} EUR\n\n"
        "Puedes reutilizar este resultado en `calcular_irpf` con:\n"
        f"- `rendimiento_neto_actividades={_euros(rendimiento_neto)}`\n"
        f"- `pagos_fraccionados={_euros(pagos)}`\n\n"
        f"_Nota: {nota}_"
    )


def register_calcular_rendimiento_actividad_tool(mcp: FastMCP) -> None:
    @mcp.tool()
    @log_tool
    async def calcular_rendimiento_actividad(
        regimen: Literal[
            "estimacion_directa_simplificada",
            "estimacion_directa_normal",
            "modulos_mvp",
        ],
        ingresos_integros: float,
        gastos_deducibles: float = 0.0,
        amortizaciones: float = 0.0,
        provisiones_y_gastos_justificados: float = 0.0,
        porcentaje_provisiones_eds: float = 0.05,
        limite_provisiones_eds: float = 2000.0,
        pagos_fraccionados_modelo_130_131: float = 0.0,
    ) -> str:
        """Calcula el rendimiento neto estimado para autonomos (MVP)."""
        try:
            return await calcular_rendimiento_actividad_impl(
                regimen=regimen,
                ingresos_integros=ingresos_integros,
                gastos_deducibles=gastos_deducibles,
                amortizaciones=amortizaciones,
                provisiones_y_gastos_justificados=provisiones_y_gastos_justificados,
                porcentaje_provisiones_eds=porcentaje_provisiones_eds,
                limite_provisiones_eds=limite_provisiones_eds,
                pagos_fraccionados_modelo_130_131=pagos_fraccionados_modelo_130_131,
            )
        except EntradaInvalida as exc:
            raise_entrada_invalida(exc)
        except Exception as exc:  # noqa: BLE001
            raise_unexpected(exc)
