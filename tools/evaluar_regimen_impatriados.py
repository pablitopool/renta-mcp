"""Tool MCP: ``evaluar_regimen_impatriados`` (art. 93 LIRPF, orientativo)."""

from mcp.server.fastmcp import FastMCP

from helpers.logging import log_tool
from helpers.tax_engine import EntradaInvalida
from tools.error_handling import raise_entrada_invalida, raise_unexpected


async def evaluar_regimen_impatriados_impl(
    anos_desde_desplazamiento: int,
    residencia_fiscal_5_anos_previos_en_espana: bool,
    existe_relacion_laboral_o_nombramiento: bool,
    trabaja_principalmente_en_espana: bool,
) -> str:
    if anos_desde_desplazamiento < 0:
        raise EntradaInvalida("anos_desde_desplazamiento no puede ser negativo")

    condiciones = {
        "desplazamiento_reciente": anos_desde_desplazamiento <= 1,
        "no_residente_5_previos": not residencia_fiscal_5_anos_previos_en_espana,
        "relacion_laboral": existe_relacion_laboral_o_nombramiento,
        "trabajo_en_espana": trabaja_principalmente_en_espana,
    }
    elegible = all(condiciones.values())

    lineas = ["## Evaluacion orientativa regimen de impatriados (art. 93 LIRPF)", ""]
    for clave, cumple in condiciones.items():
        lineas.append(f"- {clave}: {'cumple' if cumple else 'no cumple'}")
    lineas.append("")
    lineas.append(
        f"**Resultado orientativo**: {'posible elegibilidad' if elegible else 'no elegible con datos actuales'}"
    )
    lineas.append(
        "_Aviso: esta tool es informativa y no sustituye analisis profesional ni comprobacion con AEAT._"
    )
    return "\n".join(lineas)


def register_evaluar_regimen_impatriados_tool(mcp: FastMCP) -> None:
    @mcp.tool()
    @log_tool
    async def evaluar_regimen_impatriados(
        anos_desde_desplazamiento: int,
        residencia_fiscal_5_anos_previos_en_espana: bool,
        existe_relacion_laboral_o_nombramiento: bool,
        trabaja_principalmente_en_espana: bool,
    ) -> str:
        """Evalua elegibilidad orientativa al regimen de impatriados."""
        try:
            return await evaluar_regimen_impatriados_impl(
                anos_desde_desplazamiento=anos_desde_desplazamiento,
                residencia_fiscal_5_anos_previos_en_espana=residencia_fiscal_5_anos_previos_en_espana,
                existe_relacion_laboral_o_nombramiento=existe_relacion_laboral_o_nombramiento,
                trabaja_principalmente_en_espana=trabaja_principalmente_en_espana,
            )
        except EntradaInvalida as exc:
            raise_entrada_invalida(exc)
        except Exception as exc:  # noqa: BLE001
            raise_unexpected(exc)
