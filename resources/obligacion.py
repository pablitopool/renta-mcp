"""Resource MCP: ``irpf://obligacion-declarar/{año}``."""

import json

import yaml
from mcp.server.fastmcp import FastMCP

from helpers.env_config import get_data_dir
from helpers.tax_engine import DatosFiscalesNoDisponibles


def register_obligacion_resources(mcp: FastMCP) -> None:
    @mcp.resource(
        "irpf://obligacion-declarar/{año}",
        mime_type="application/json",
        description="Umbrales de obligación de declarar (art. 96 LIRPF).",
    )
    def obligacion(año: str) -> str:
        path = get_data_dir() / str(int(año)) / "obligacion.yaml"
        if not path.exists():
            raise DatosFiscalesNoDisponibles(f"No existe {path}")
        with path.open("r", encoding="utf-8") as fh:
            return json.dumps(yaml.safe_load(fh), indent=2, ensure_ascii=False)
