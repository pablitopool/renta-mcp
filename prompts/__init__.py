from mcp.server.fastmcp import FastMCP

from prompts.optimizar_deducciones import register_optimizar_deducciones_prompt
from prompts.revisar_borrador import register_revisar_borrador_prompt
from prompts.simular_declaracion import register_simular_declaracion_prompt


def register_prompts(mcp: FastMCP) -> None:
    """Registra los Prompts MCP del servidor."""
    register_revisar_borrador_prompt(mcp)
    register_optimizar_deducciones_prompt(mcp)
    register_simular_declaracion_prompt(mcp)
