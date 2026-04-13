"""Tool MCP: ``consultar_tramos``. Devuelve la escala IRPF para un territorio."""

from typing import Literal

from mcp.server.fastmcp import FastMCP

from helpers.data_loader import load_estatal, load_territorio
from helpers.formatting import tabla_tramos
from helpers.logging import log_tool
from tools.error_handling import (
    DatosFiscalesNoDisponibles,
    raise_datos_no_disponibles,
    raise_unexpected,
)


async def consultar_tramos_impl(
    año: int,
    territorio: str,
    tipo: Literal["general", "ahorro"] = "general",
) -> str:
    if tipo == "ahorro":
        estatal = load_estatal(año)
        return tabla_tramos(
            estatal["escala_ahorro"],
            f"Escala de la base del ahorro — ejercicio {año}",
        )

    estatal = load_estatal(año)
    bloques = [
        tabla_tramos(
            estatal["escala_general"],
            f"Escala general ESTATAL — ejercicio {año}",
        )
    ]

    if territorio.lower() == "estatal":
        return "\n\n".join(bloques)

    datos = load_territorio(año, territorio.lower())
    escala = datos.get("escala_autonomica") or datos.get("escala_general")
    nombre = datos["territorio"]["nombre"]
    regimen = datos["territorio"]["regimen"]
    etiqueta = "FORAL" if regimen == "foral" else "AUTONÓMICA"
    bloques.append(
        tabla_tramos(
            escala,
            f"Escala {etiqueta} — {nombre} — ejercicio {año}",
        )
    )
    if datos.get("fuente_boe"):
        bloques.append(f"_Fuente: {datos['fuente_boe']}_")
    return "\n\n".join(bloques)


def register_consultar_tramos_tool(mcp: FastMCP) -> None:
    @mcp.tool()
    @log_tool
    async def consultar_tramos(
        año: int,
        territorio: str = "estatal",
        tipo: Literal["general", "ahorro"] = "general",
    ) -> str:
        """Devuelve la escala IRPF aplicable para un año y territorio.

        Parámetros:
        - ``año``: ejercicio fiscal (p. ej. 2025).
        - ``territorio``: slug (``"estatal"``, ``"madrid"``, ``"cataluna"``,
          ``"bizkaia"``, ``"navarra"``, ...). Por defecto ``"estatal"``.
        - ``tipo``: ``"general"`` (base general) o ``"ahorro"`` (base del
          ahorro, única nacional). Por defecto ``"general"``.
        """
        try:
            return await consultar_tramos_impl(año, territorio, tipo)
        except DatosFiscalesNoDisponibles as exc:
            raise_datos_no_disponibles(exc)
        except Exception as exc:  # noqa: BLE001
            raise_unexpected(exc)
