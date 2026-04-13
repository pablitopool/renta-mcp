"""Resource MCP: ``irpf://deducciones/{año}/{territorio}``."""

import json

from mcp.server.fastmcp import FastMCP

from helpers.data_loader import load_territorio


def register_deducciones_resources(mcp: FastMCP) -> None:
    @mcp.resource(
        "irpf://deducciones/{año}/{territorio}",
        mime_type="application/json",
        description="Catálogo de deducciones autonómicas/forales por territorio.",
    )
    def deducciones(año: str, territorio: str) -> str:
        datos = load_territorio(int(año), territorio.lower())
        return json.dumps(
            {
                "territorio": datos["territorio"],
                "año": datos["año"],
                "deducciones": datos.get("deducciones", []),
                "fuente_boe": datos.get("fuente_boe"),
            },
            indent=2,
            ensure_ascii=False,
            default=str,
        )
