"""Prompt MCP: ``simular_declaracion``. Simulación completa con variantes."""

from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.prompts import base


def register_simular_declaracion_prompt(mcp: FastMCP) -> None:
    @mcp.prompt(
        description=(
            "Simulación completa de la declaración del IRPF con varios "
            "escenarios: individual vs conjunta, con y sin aportación a "
            "planes de pensiones."
        )
    )
    def simular_declaracion() -> list[base.Message]:
        return [
            base.UserMessage(
                "Vamos a simular tu declaración del IRPF con varios "
                "escenarios para ver cuál te conviene más.\n\n"
                "Necesito estos datos (si hay cónyuge, dímelo de ambos):\n"
                "1. Comunidad Autónoma de residencia (de ambos si es "
                "unidad familiar).\n"
                "2. Año fiscal.\n"
                "3. Rendimientos netos del trabajo, capital mobiliario, "
                "capital inmobiliario y actividades económicas.\n"
                "4. Edades, hijos y ascendientes a cargo.\n"
                "5. Retenciones practicadas.\n\n"
                "Haré las siguientes simulaciones con `calcular_irpf`:\n"
                "- **A**: Declaración individual.\n"
                "- **B**: Tributación conjunta biparental (si hay cónyuge).\n"
                "- **C**: Mismo escenario con una aportación de 1.500 € "
                "al plan de pensiones (tope estatal 2025).\n\n"
                "Al final compararé las tres cuotas líquidas y te "
                "recomendaré la más ventajosa con el desglose completo."
            )
        ]
