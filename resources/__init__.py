from mcp.server.fastmcp import FastMCP

from resources.casillas import register_casillas_resources
from resources.deducciones import register_deducciones_resources
from resources.minimos import register_minimos_resources
from resources.obligacion import register_obligacion_resources
from resources.plazos import register_plazos_resources
from resources.tramos import register_tramos_resources


def register_resources(mcp: FastMCP) -> None:
    """Registra los Resources (URI templates) del servidor.

    Regla crítica: registrar rutas literales (p. ej. ``.../estatal``) ANTES
    que templates genéricos (``.../{territorio}``) — el matcher captura la
    primera coincidencia y puede interpretar ``"estatal"`` como slug de
    territorio si el orden está invertido.
    """
    register_tramos_resources(mcp)
    register_minimos_resources(mcp)
    register_plazos_resources(mcp)
    register_obligacion_resources(mcp)
    register_casillas_resources(mcp)
    register_deducciones_resources(mcp)
