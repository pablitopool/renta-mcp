"""Tool MCP: ``evaluar_exit_tax`` (diagnostico de umbrales, MVP)."""

from decimal import Decimal

from mcp.server.fastmcp import FastMCP

from helpers.logging import log_tool
from helpers.tax_engine import EntradaInvalida
from tools.error_handling import raise_entrada_invalida, raise_unexpected

UMBRAL_PARTICIPACION_EUR = Decimal("4000000")
UMBRAL_ALTO_PORCENTAJE_EUR = Decimal("1000000")


async def evaluar_exit_tax_impl(
    valor_mercado_participaciones: float,
    porcentaje_participacion: float,
    anos_residencia_fiscal_espana_ultimos_15: int,
) -> str:
    valor = Decimal(str(valor_mercado_participaciones))
    porcentaje = Decimal(str(porcentaje_participacion))

    if valor < 0:
        raise EntradaInvalida("valor_mercado_participaciones no puede ser negativo")
    if porcentaje < 0 or porcentaje > 100:
        raise EntradaInvalida("porcentaje_participacion debe estar entre 0 y 100")
    if anos_residencia_fiscal_espana_ultimos_15 < 0:
        raise EntradaInvalida(
            "anos_residencia_fiscal_espana_ultimos_15 no puede ser negativo"
        )

    condicion_residencia = anos_residencia_fiscal_espana_ultimos_15 >= 10
    condicion_valor_alto = valor > UMBRAL_PARTICIPACION_EUR
    condicion_valor_y_porcentaje = (
        porcentaje >= 25 and valor > UMBRAL_ALTO_PORCENTAJE_EUR
    )
    potencial = condicion_residencia and (
        condicion_valor_alto or condicion_valor_y_porcentaje
    )

    return (
        "## Evaluacion orientativa exit tax\n\n"
        f"- **Residencia >=10/15**: {'si' if condicion_residencia else 'no'}\n"
        f"- **Valor participaciones > 4M EUR**: {'si' if condicion_valor_alto else 'no'}\n"
        f"- **>=25% y valor > 1M EUR**: {'si' if condicion_valor_y_porcentaje else 'no'}\n\n"
        f"**Resultado orientativo**: {'riesgo potencial de exit tax' if potencial else 'sin riesgo aparente por umbrales base'}\n\n"
        "_Tool informativa. Requiere analisis fiscal especializado del caso concreto._"
    )


def register_evaluar_exit_tax_tool(mcp: FastMCP) -> None:
    @mcp.tool()
    @log_tool
    async def evaluar_exit_tax(
        valor_mercado_participaciones: float,
        porcentaje_participacion: float,
        anos_residencia_fiscal_espana_ultimos_15: int,
    ) -> str:
        """Evalua umbrales basicos orientativos de exit tax."""
        try:
            return await evaluar_exit_tax_impl(
                valor_mercado_participaciones=valor_mercado_participaciones,
                porcentaje_participacion=porcentaje_participacion,
                anos_residencia_fiscal_espana_ultimos_15=anos_residencia_fiscal_espana_ultimos_15,
            )
        except EntradaInvalida as exc:
            raise_entrada_invalida(exc)
        except Exception as exc:  # noqa: BLE001
            raise_unexpected(exc)
