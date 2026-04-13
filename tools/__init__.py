from mcp.server.fastmcp import FastMCP

from tools.calcular_irpf import register_calcular_irpf_tool
from tools.consultar_tramos import register_consultar_tramos_tool


def register_tools(mcp: FastMCP) -> None:
    """Registra todas las tools del servidor.

    Cada módulo de ``tools/`` expone una función ``register_XXX_tool(mcp)``.
    """
    register_consultar_tramos_tool(mcp)
    register_calcular_irpf_tool(mcp)
