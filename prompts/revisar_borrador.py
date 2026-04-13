"""Prompt MCP: ``revisar_borrador``. Flujo guiado para revisar una declaración."""

from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.prompts import base


def register_revisar_borrador_prompt(mcp: FastMCP) -> None:
    @mcp.prompt(
        description=(
            "Flujo guiado paso a paso para revisar un borrador de la "
            "declaración del IRPF: pregunta por datos personales, ingresos, "
            "deducciones aplicables y calcula la cuota."
        )
    )
    def revisar_borrador() -> list[base.Message]:
        return [
            base.UserMessage(
                "Voy a ayudarte a revisar tu borrador del IRPF paso a paso.\n\n"
                "Por favor, dime:\n"
                "1. Año del ejercicio a revisar (p. ej. 2024 o 2025).\n"
                "2. Tu Comunidad Autónoma de residencia (Madrid, Cataluña, "
                "Andalucía...).\n"
                "3. Rendimiento neto del trabajo antes de la reducción del "
                "art. 20 LIRPF (si solo tienes salario bruto, indícalo "
                "como aproximación y lo trataré como tal).\n"
                "4. Situación familiar: individual, conjunta biparental o "
                "conjunta monoparental.\n"
                "5. Edad + hijos a cargo (con sus edades) + ascendientes a "
                "cargo.\n"
                "6. Aportaciones a planes de pensiones (si las hay).\n"
                "7. Retenciones practicadas en nómina.\n"
                "8. ¿Has hecho donativos, inversión en vivienda (régimen "
                "transitorio), eres familia numerosa, tienes derecho a "
                "maternidad reembolsable u obras de mejora energética en "
                "vivienda?\n"
                "9. Para deducciones autonómicas: alquiler de vivienda, "
                "guardería, gastos educativos/escolares, cuotas sindicales, "
                "donativos autonómicos, inversión u obras en vivienda "
                "habitual, y nacimientos/adopciones/acogimientos del año.\n\n"
                "Cuando tenga todos los datos, usaré `calcular_irpf` para "
                "calcular la cuota, cruzaré con las deducciones autonómicas "
                "aplicables y te daré un desglose completo con "
                "recomendaciones."
            )
        ]
