"""Tool MCP: ``consultar_plazos_campana``."""

from mcp.server.fastmcp import FastMCP

from helpers.env_config import get_data_dir
from helpers.logging import log_tool
from helpers.tax_engine import DatosFiscalesNoDisponibles
from tools.error_handling import raise_datos_no_disponibles, raise_unexpected


def _cargar_plazos(año: int) -> dict:
    import yaml

    path = get_data_dir() / str(año) / "plazos.yaml"
    if not path.exists():
        raise DatosFiscalesNoDisponibles(f"No existe {path}")
    with path.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


async def consultar_plazos_campana_impl(año: int) -> str:
    plazos = _cargar_plazos(año)
    campana = plazos["campaña"]
    lineas = [f"## Plazos Campaña Renta {año}", ""]
    etiquetas = {
        "borrador_datos_fiscales_disponibles": "Borrador y datos fiscales disponibles",
        "inicio_presentacion_internet": "Inicio presentación por internet",
        "inicio_cita_previa_telefonica": "Inicio cita previa telefónica",
        "inicio_cita_previa_presencial": "Inicio cita previa presencial",
        "domiciliacion_bancaria_hasta": "Fin domiciliación bancaria",
        "fin_plazo_general": "**Fin plazo general**",
    }
    for clave, etiqueta in etiquetas.items():
        if clave in campana:
            lineas.append(f"- {etiqueta}: `{campana[clave]}`")
    if plazos.get("nota"):
        lineas.append(f"\n_{plazos['nota']}_")
    if plazos.get("fuente_boe"):
        lineas.append(f"\n_Fuente: {plazos['fuente_boe']}_")
    return "\n".join(lineas)


def register_consultar_plazos_campana_tool(mcp: FastMCP) -> None:
    @mcp.tool()
    @log_tool
    async def consultar_plazos_campana(año: int) -> str:
        """Fechas clave de la campaña Renta para el ejercicio indicado."""
        try:
            return await consultar_plazos_campana_impl(año)
        except DatosFiscalesNoDisponibles as exc:
            raise_datos_no_disponibles(exc)
        except Exception as exc:  # noqa: BLE001
            raise_unexpected(exc)
