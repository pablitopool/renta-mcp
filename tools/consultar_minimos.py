"""Tool MCP: ``consultar_minimos``. Devuelve el mínimo personal y familiar."""

from typing import List, Optional

from mcp.server.fastmcp import FastMCP

from helpers.data_loader import load_estatal, load_territorio
from helpers.logging import log_tool
from helpers.tax_engine import (
    Ascendiente,
    DatosFiscalesNoDisponibles,
    Hijo,
    InputIRPF,
    calcular_minimo_personal_familiar,
)
from tools.error_handling import raise_datos_no_disponibles, raise_unexpected


async def consultar_minimos_impl(
    año: int,
    territorio: str = "estatal",
    edad_contribuyente: int = 40,
    hijos_edades: Optional[List[int]] = None,
    ascendientes_edades: Optional[List[int]] = None,
    discapacidad_contribuyente: int = 0,
) -> str:
    estatal = load_estatal(año)
    minimos = dict(estatal["minimos"])

    if territorio.lower() != "estatal":
        datos = load_territorio(año, territorio.lower())
        overrides = datos.get("minimos") or {}
        for k, v in overrides.items():
            if v is not None:
                minimos[k] = v

    entrada = InputIRPF(
        año=año,
        territorio=territorio.lower(),
        edad_contribuyente=edad_contribuyente,
        hijos=[Hijo(edad=e) for e in (hijos_edades or [])],
        ascendientes=[Ascendiente(edad=e) for e in (ascendientes_edades or [])],
        discapacidad_contribuyente=discapacidad_contribuyente,
    )
    total = calcular_minimo_personal_familiar(entrada, minimos)

    return (
        f"## Mínimo personal y familiar — {territorio} {año}\n\n"
        f"- Edad contribuyente: {edad_contribuyente}\n"
        f"- Hijos a cargo: {hijos_edades or '—'}\n"
        f"- Ascendientes a cargo: {ascendientes_edades or '—'}\n"
        f"- Discapacidad contribuyente: {discapacidad_contribuyente}%\n\n"
        f"**Mínimo total aplicable**: {total} €\n\n"
        "_Se aplica como tipo 0 sobre la base liquidable (art. 56-61 LIRPF)._"
    )


def register_consultar_minimos_tool(mcp: FastMCP) -> None:
    @mcp.tool()
    @log_tool
    async def consultar_minimos(
        año: int,
        territorio: str = "estatal",
        edad_contribuyente: int = 40,
        hijos_edades: Optional[List[int]] = None,
        ascendientes_edades: Optional[List[int]] = None,
        discapacidad_contribuyente: int = 0,
    ) -> str:
        """Calcula el mínimo personal y familiar aplicable (arts. 56-61 LIRPF)."""
        try:
            return await consultar_minimos_impl(
                año=año,
                territorio=territorio,
                edad_contribuyente=edad_contribuyente,
                hijos_edades=hijos_edades,
                ascendientes_edades=ascendientes_edades,
                discapacidad_contribuyente=discapacidad_contribuyente,
            )
        except DatosFiscalesNoDisponibles as exc:
            raise_datos_no_disponibles(exc)
        except Exception as exc:  # noqa: BLE001
            raise_unexpected(exc)
