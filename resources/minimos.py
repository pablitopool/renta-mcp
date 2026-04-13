"""Resource MCP: ``irpf://minimos/{año}``."""

import json

from mcp.server.fastmcp import FastMCP

from helpers.data_loader import load_estatal


def register_minimos_resources(mcp: FastMCP) -> None:
    @mcp.resource(
        "irpf://minimos/{año}",
        mime_type="application/json",
        description="Mínimo personal y familiar estatal (arts. 56-61 LIRPF).",
    )
    def minimos(año: str) -> str:
        datos = load_estatal(int(año))
        return json.dumps(
            {
                "año": datos["año"],
                "minimos": {
                    k: str(v) if v is not None else None
                    for k, v in datos["minimos"].items()
                },
                "fuente_boe": datos.get("fuente_boe"),
            },
            indent=2,
            ensure_ascii=False,
            default=str,
        )
