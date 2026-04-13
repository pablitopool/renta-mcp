"""Tool MCP: ``validar_minimo_declarante`` (art. 20 LIRPF)."""

from decimal import Decimal

from mcp.server.fastmcp import FastMCP

from helpers.data_loader import load_estatal
from helpers.logging import log_tool
from helpers.tax_engine import (
    DatosFiscalesNoDisponibles,
    calcular_reduccion_trabajo,
)
from tools.error_handling import raise_datos_no_disponibles, raise_unexpected


async def validar_minimo_declarante_impl(
    año: int,
    rendimiento_neto_trabajo: float,
) -> str:
    estatal = load_estatal(año)
    params = estatal["reduccion_rendimientos_trabajo"]
    rn = Decimal(str(rendimiento_neto_trabajo))
    reduccion = calcular_reduccion_trabajo(rn, params)
    base = rn - reduccion

    salida = [
        f"## Validación art. 20 LIRPF — ejercicio {año}",
        "",
        f"- Rendimiento neto trabajo: {rn} €",
        f"- Reducción aplicable: {reduccion} €",
        f"- Rendimiento neto reducido: {base} €",
    ]
    if base < 0:
        salida.append(
            "\n⚠️ **ERROR CONCEPTUAL**: la reducción genera base negativa. "
            "Debe limitarse al propio rendimiento (art. 20 LIRPF)."
        )
    else:
        salida.append("\n✅ Reducción correctamente aplicada; base no negativa.")
    return "\n".join(salida)


def register_validar_minimo_declarante_tool(mcp: FastMCP) -> None:
    @mcp.tool()
    @log_tool
    async def validar_minimo_declarante(
        año: int,
        rendimiento_neto_trabajo: float,
    ) -> str:
        """Comprueba que la reducción art. 20 LIRPF no genere base negativa."""
        try:
            return await validar_minimo_declarante_impl(año, rendimiento_neto_trabajo)
        except DatosFiscalesNoDisponibles as exc:
            raise_datos_no_disponibles(exc)
        except Exception as exc:  # noqa: BLE001
            raise_unexpected(exc)
