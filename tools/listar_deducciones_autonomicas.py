"""Tool MCP: ``listar_deducciones_autonomicas``."""

from typing import Optional

from mcp.server.fastmcp import FastMCP

from helpers.data_loader import load_territorio
from helpers.logging import log_tool
from helpers.tax_engine import DatosFiscalesNoDisponibles
from tools.error_handling import raise_datos_no_disponibles, raise_unexpected


async def listar_deducciones_autonomicas_impl(
    ccaa: str,
    año: int,
    categoria: Optional[str] = None,
) -> str:
    datos = load_territorio(año, ccaa.lower())
    deducciones = datos.get("deducciones", []) or []
    if categoria:
        deducciones = [d for d in deducciones if d.get("categoria") == categoria]

    nombre = datos["territorio"]["nombre"]
    if not deducciones:
        return (
            f"Sin deducciones registradas para {nombre} ({año})"
            f"{f' en categoría {categoria}' if categoria else ''}."
        )

    por_cat: dict[str, list[dict]] = {}
    for d in deducciones:
        por_cat.setdefault(d.get("categoria", "otros"), []).append(d)

    lineas = [f"## Deducciones autonómicas — {nombre} {año}", ""]
    for cat, items in por_cat.items():
        lineas.append(f"### {cat.title()}")
        lineas.append("")
        for d in items:
            encabezado = f"- **{d['titulo']}** (`{d['id']}`)"
            if d.get("porcentaje"):
                encabezado += f" — {float(d['porcentaje']) * 100:.1f} %"
            if d.get("importe_fijo"):
                encabezado += f" — {d['importe_fijo']} €"
            if d.get("articulo"):
                encabezado += f" _({d['articulo']})_"
            lineas.append(encabezado)
        lineas.append("")
    return "\n".join(lineas)


def register_listar_deducciones_autonomicas_tool(mcp: FastMCP) -> None:
    @mcp.tool()
    @log_tool
    async def listar_deducciones_autonomicas(
        ccaa: str,
        año: int,
        categoria: Optional[str] = None,
    ) -> str:
        """Lista las deducciones autonómicas vigentes para una CCAA.

        Categorías: ``familia``, ``vivienda``, ``educacion``, ``donativos``,
        ``inversion``, ``discapacidad``, ``cultura``, ``otros``.
        """
        try:
            return await listar_deducciones_autonomicas_impl(ccaa, año, categoria)
        except DatosFiscalesNoDisponibles as exc:
            raise_datos_no_disponibles(exc)
        except Exception as exc:  # noqa: BLE001
            raise_unexpected(exc)
