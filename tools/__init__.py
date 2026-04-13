from mcp.server.fastmcp import FastMCP

from tools.buscar_casilla import register_buscar_casilla_tool
from tools.buscar_deduccion import register_buscar_deduccion_tool
from tools.calcular_irpf import register_calcular_irpf_tool
from tools.calcular_retencion_nomina import register_calcular_retencion_nomina_tool
from tools.comprobar_obligacion_declarar import (
    register_comprobar_obligacion_declarar_tool,
)
from tools.consultar_minimos import register_consultar_minimos_tool
from tools.consultar_plazos_campana import register_consultar_plazos_campana_tool
from tools.consultar_tramos import register_consultar_tramos_tool
from tools.listar_casillas_modelo_100 import register_listar_casillas_modelo_100_tool
from tools.listar_deducciones_autonomicas import (
    register_listar_deducciones_autonomicas_tool,
)
from tools.validar_minimo_declarante import register_validar_minimo_declarante_tool


def register_tools(mcp: FastMCP) -> None:
    """Registra todas las tools del servidor.

    Cada módulo de ``tools/`` expone una función ``register_XXX_tool(mcp)``.
    """
    register_consultar_tramos_tool(mcp)
    register_calcular_irpf_tool(mcp)
    register_calcular_retencion_nomina_tool(mcp)
    register_consultar_minimos_tool(mcp)
    register_consultar_plazos_campana_tool(mcp)
    register_comprobar_obligacion_declarar_tool(mcp)
    register_validar_minimo_declarante_tool(mcp)
    register_listar_casillas_modelo_100_tool(mcp)
    register_buscar_casilla_tool(mcp)
    register_listar_deducciones_autonomicas_tool(mcp)
    register_buscar_deduccion_tool(mcp)
