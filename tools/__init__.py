from mcp.server.fastmcp import FastMCP


def register_tools(mcp: FastMCP) -> None:
    """Registra todas las tools del servidor.

    Cada módulo de ``tools/`` expone una función ``register_XXX_tool(mcp)``.
    """
    from tools.buscar_casilla import register_buscar_casilla_tool
    from tools.buscar_deduccion import register_buscar_deduccion_tool
    from tools.calcular_ganancia_cripto_fifo import (
        register_calcular_ganancia_cripto_fifo_tool,
    )
    from tools.calcular_irpf import register_calcular_irpf_tool
    from tools.calcular_rendimiento_actividad import (
        register_calcular_rendimiento_actividad_tool,
    )
    from tools.calcular_retencion_nomina import (
        register_calcular_retencion_nomina_tool,
    )
    from tools.comprobar_obligacion_declarar import (
        register_comprobar_obligacion_declarar_tool,
    )
    from tools.consultar_minimos import register_consultar_minimos_tool
    from tools.consultar_plazos_campana import register_consultar_plazos_campana_tool
    from tools.consultar_tramos import register_consultar_tramos_tool
    from tools.evaluar_exencion_art_7p import register_evaluar_exencion_art_7p_tool
    from tools.evaluar_exit_tax import register_evaluar_exit_tax_tool
    from tools.evaluar_regimen_impatriados import (
        register_evaluar_regimen_impatriados_tool,
    )
    from tools.listar_casillas_modelo_100 import (
        register_listar_casillas_modelo_100_tool,
    )
    from tools.listar_deducciones_autonomicas import (
        register_listar_deducciones_autonomicas_tool,
    )
    from tools.preparar_payload_irpf import register_preparar_payload_irpf_tool
    from tools.validar_minimo_declarante import register_validar_minimo_declarante_tool
    from tools.validar_municipio_despoblacion import (
        register_validar_municipio_despoblacion_tool,
    )

    register_consultar_tramos_tool(mcp)
    register_calcular_irpf_tool(mcp)
    register_calcular_rendimiento_actividad_tool(mcp)
    register_preparar_payload_irpf_tool(mcp)
    register_calcular_ganancia_cripto_fifo_tool(mcp)
    register_calcular_retencion_nomina_tool(mcp)
    register_consultar_minimos_tool(mcp)
    register_consultar_plazos_campana_tool(mcp)
    register_comprobar_obligacion_declarar_tool(mcp)
    register_validar_minimo_declarante_tool(mcp)
    register_validar_municipio_despoblacion_tool(mcp)
    register_evaluar_regimen_impatriados_tool(mcp)
    register_evaluar_exencion_art_7p_tool(mcp)
    register_evaluar_exit_tax_tool(mcp)
    register_listar_casillas_modelo_100_tool(mcp)
    register_buscar_casilla_tool(mcp)
    register_listar_deducciones_autonomicas_tool(mcp)
    register_buscar_deduccion_tool(mcp)
