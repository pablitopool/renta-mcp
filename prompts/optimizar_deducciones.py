"""Prompt MCP: ``optimizar_deducciones``. Sugiere deducciones aplicables."""

from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.prompts import base


def register_optimizar_deducciones_prompt(mcp: FastMCP) -> None:
    @mcp.prompt(
        description=(
            "Dado un perfil de contribuyente (CCAA, situación familiar, "
            "renta), sugiere qué deducciones autonómicas y estatales podrían "
            "aplicarse y estima el ahorro máximo."
        )
    )
    def optimizar_deducciones() -> list[base.Message]:
        return [
            base.UserMessage(
                "Voy a ayudarte a identificar las deducciones del IRPF que "
                "podrías aprovechar para reducir tu cuota.\n\n"
                "Cuéntame:\n"
                "1. Comunidad Autónoma de residencia.\n"
                "2. Año fiscal (2024 o 2025).\n"
                "3. Base imponible aproximada y situación familiar.\n"
                "4. Circunstancias personales: edad, número y edad de hijos, "
                "si tienes discapacidad (grado), ascendientes a cargo, "
                "familia numerosa (general o especial) y si aplica "
                "maternidad reembolsable.\n"
                "5. Vivienda: ¿alquilada o en propiedad? Si propiedad "
                "¿adquirida antes de 2013? ¿Has hecho obras de eficiencia "
                "energética?\n"
                "6. ¿Has hecho donativos a ONGs, fundaciones o partidos "
                "políticos?\n"
                "7. ¿Tienes guardería, material escolar, escolaridad, "
                "idiomas, uniformes, estudios fuera de tu isla/provincia o "
                "cuotas sindicales?\n"
                "8. ¿Inviertes en empresas (business angel, MAB)?\n\n"
                "Usaré `listar_deducciones_autonomicas` y "
                "`buscar_deduccion` para cruzar tu perfil con el catálogo "
                "de tu CCAA, más las deducciones estatales del motor. "
                "Cuando tenga los IDs y las bases aplicables, podré llamar "
                "a `calcular_irpf` para estimar el ahorro real.\n"
            )
        ]
