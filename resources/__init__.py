from mcp.server.fastmcp import FastMCP

from resources.tramos import register_tramos_resources


def register_resources(mcp: FastMCP) -> None:
    """Registra los Resources (URI templates) del servidor.

    Regla crítica: registrar rutas literales (p. ej. ``.../estatal``) ANTES
    que templates genéricos (``.../{territorio}``) — el matcher captura la
    primera coincidencia y puede interpretar ``"estatal"`` como slug de
    territorio si el orden está invertido.
    """
    register_tramos_resources(mcp)
