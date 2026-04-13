"""Prompt MCP: ``preparar_declaracion``. Modo preparacion de datos."""

from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.prompts import base


def register_preparar_declaracion_prompt(mcp: FastMCP) -> None:
    @mcp.prompt(
        description=(
            "Guia para preparar un payload estructurado antes de calcular el IRPF "
            "(modo preparacion/hibrido)."
        )
    )
    def preparar_declaracion() -> list[base.Message]:
        return [
            base.UserMessage(
                "Vamos a preparar tu declaracion en modo estructurado.\n\n"
                "1) Comparte ano y territorio fiscal.\n"
                "2) Resume ingresos netos por bloque: trabajo, actividades, capital mobiliario/inmobiliario y ganancias del ahorro.\n"
                "3) Indica retenciones y, si eres autonomo, pagos fraccionados (130/131).\n"
                "4) Indica situacion familiar, edad, hijos y ascendientes.\n"
                "5) Si aplica, pasamos por `preparar_payload_irpf` para normalizar datos y despues ejecutamos `calcular_irpf`."
            )
        ]
