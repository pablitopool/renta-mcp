"""Tool MCP: ``evaluar_exencion_art_7p`` (estimacion orientativa)."""

from decimal import Decimal

from mcp.server.fastmcp import FastMCP

from helpers.logging import log_tool
from helpers.tax_engine import EntradaInvalida
from tools.error_handling import raise_entrada_invalida, raise_unexpected

LIMITE_ANUAL = Decimal("60100")


async def evaluar_exencion_art_7p_impl(
    rendimiento_trabajo_anual: float,
    dias_trabajados_extranjero: int,
    total_dias_anuales: int = 365,
) -> str:
    salario = Decimal(str(rendimiento_trabajo_anual))
    if salario < 0:
        raise EntradaInvalida("rendimiento_trabajo_anual no puede ser negativo")
    if dias_trabajados_extranjero < 0 or total_dias_anuales <= 0:
        raise EntradaInvalida("dias_trabajados_extranjero/total_dias_anuales invalidos")
    if dias_trabajados_extranjero > total_dias_anuales:
        raise EntradaInvalida(
            "dias_trabajados_extranjero no puede superar total_dias_anuales"
        )

    prorrata = Decimal(dias_trabajados_extranjero) / Decimal(total_dias_anuales)
    exencion_teorica = salario * prorrata
    exencion_aplicable = min(exencion_teorica, LIMITE_ANUAL)

    return (
        "## Evaluacion orientativa exencion art. 7.p LIRPF\n\n"
        f"- **Rendimiento anual**: {salario:.2f} EUR\n"
        f"- **Dias en extranjero**: {dias_trabajados_extranjero}/{total_dias_anuales}\n"
        f"- **Exencion teorica prorrateada**: {exencion_teorica:.2f} EUR\n"
        f"- **Exencion aplicable (tope 60.100 EUR)**: {exencion_aplicable:.2f} EUR\n\n"
        "_Estimacion orientativa. La aplicacion real requiere verificar requisitos legales y documentales._"
    )


def register_evaluar_exencion_art_7p_tool(mcp: FastMCP) -> None:
    @mcp.tool()
    @log_tool
    async def evaluar_exencion_art_7p(
        rendimiento_trabajo_anual: float,
        dias_trabajados_extranjero: int,
        total_dias_anuales: int = 365,
    ) -> str:
        """Estima orientativamente la exencion por trabajos en el extranjero (art. 7.p)."""
        try:
            return await evaluar_exencion_art_7p_impl(
                rendimiento_trabajo_anual=rendimiento_trabajo_anual,
                dias_trabajados_extranjero=dias_trabajados_extranjero,
                total_dias_anuales=total_dias_anuales,
            )
        except EntradaInvalida as exc:
            raise_entrada_invalida(exc)
        except Exception as exc:  # noqa: BLE001
            raise_unexpected(exc)
