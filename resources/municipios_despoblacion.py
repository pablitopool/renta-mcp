"""Resource MCP: ``irpf://municipios-despoblacion/{año}/{territorio}``."""

import json

from mcp.server.fastmcp import FastMCP

from helpers.env_config import get_data_dir


def _cargar_catalogo(año: int) -> dict:
    import yaml

    path = get_data_dir() / str(año) / "municipios_despoblacion.yaml"
    if not path.exists():
        return {"año": año, "territorios": {}}
    with path.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def register_municipios_despoblacion_resources(mcp: FastMCP) -> None:
    @mcp.resource(
        "irpf://municipios-despoblacion/{año}/{territorio}",
        mime_type="application/json",
        description="Catalogo orientativo de municipios en riesgo de despoblacion por territorio.",
    )
    def municipios_despoblacion(año: str, territorio: str) -> str:
        catalogo = _cargar_catalogo(int(año))
        territorios = catalogo.get("territorios") or {}
        data = territorios.get(territorio.lower(), {})
        return json.dumps(
            {
                "año": int(año),
                "territorio": territorio.lower(),
                "nombre": data.get("nombre"),
                "aliases": data.get("aliases", []),
                "deducciones_relacionadas": data.get("deducciones_relacionadas", []),
                "municipios": data.get("municipios", []),
            },
            indent=2,
            ensure_ascii=False,
        )
