"""Resource MCP: ``irpf://plazos/{año}``."""

import json

import yaml
from mcp.server.fastmcp import FastMCP

from helpers.env_config import get_data_dir
from helpers.tax_engine import DatosFiscalesNoDisponibles


def register_plazos_resources(mcp: FastMCP) -> None:
    @mcp.resource(
        "irpf://plazos/{año}",
        mime_type="application/json",
        description="Fechas clave de la campaña Renta para el ejercicio.",
    )
    def plazos(año: str) -> str:
        path = get_data_dir() / str(int(año)) / "plazos.yaml"
        if not path.exists():
            raise DatosFiscalesNoDisponibles(f"No existe {path}")
        with path.open("r", encoding="utf-8") as fh:
            return json.dumps(yaml.safe_load(fh), indent=2, ensure_ascii=False)
