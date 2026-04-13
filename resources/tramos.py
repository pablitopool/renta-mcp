"""Resources MCP para escalas IRPF (``irpf://tramos/...``)."""

from __future__ import annotations

import json

from mcp.server.fastmcp import FastMCP

from helpers.data_loader import load_estatal, load_territorio


def register_tramos_resources(mcp: FastMCP) -> None:
    # Regla crítica: literales ANTES que templates genéricos.

    @mcp.resource(
        "irpf://tramos/{año}/estatal",
        mime_type="application/json",
        description="Escala general estatal del IRPF para el ejercicio indicado.",
    )
    def tramos_estatal(año: str) -> str:
        datos = load_estatal(int(año))
        return json.dumps(
            {
                "año": datos["año"],
                "escala_general": [
                    {
                        "desde": str(t["desde"]),
                        "hasta": str(t["hasta"]) if t["hasta"] is not None else None,
                        "tipo": str(t["tipo"]),
                    }
                    for t in datos["escala_general"]
                ],
                "fuente_boe": datos.get("fuente_boe"),
            },
            indent=2,
            ensure_ascii=False,
        )

    @mcp.resource(
        "irpf://tramos-ahorro/{año}",
        mime_type="application/json",
        description="Escala de la base del ahorro (única nacional).",
    )
    def tramos_ahorro(año: str) -> str:
        datos = load_estatal(int(año))
        return json.dumps(
            {
                "año": datos["año"],
                "escala_ahorro": [
                    {
                        "desde": str(t["desde"]),
                        "hasta": str(t["hasta"]) if t["hasta"] is not None else None,
                        "tipo": str(t["tipo"]),
                    }
                    for t in datos["escala_ahorro"]
                ],
            },
            indent=2,
            ensure_ascii=False,
        )

    @mcp.resource(
        "irpf://tramos/{año}/{territorio}",
        mime_type="application/json",
        description="Escala autonómica o foral IRPF por territorio (slug).",
    )
    def tramos_territorio(año: str, territorio: str) -> str:
        datos = load_territorio(int(año), territorio.lower())
        escala = datos.get("escala_autonomica") or datos.get("escala_general") or []
        return json.dumps(
            {
                "territorio": datos["territorio"],
                "año": datos["año"],
                "escala": [
                    {
                        "desde": str(t["desde"]),
                        "hasta": str(t["hasta"]) if t["hasta"] is not None else None,
                        "tipo": str(t["tipo"]),
                    }
                    for t in escala
                ],
                "fuente_boe": datos.get("fuente_boe"),
            },
            indent=2,
            ensure_ascii=False,
        )
