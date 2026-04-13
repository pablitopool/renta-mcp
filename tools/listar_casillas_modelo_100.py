"""Tool MCP: ``listar_casillas_modelo_100``."""

from typing import Optional

import yaml
from mcp.server.fastmcp import FastMCP

from helpers.env_config import get_data_dir
from helpers.logging import log_tool
from helpers.tax_engine import DatosFiscalesNoDisponibles
from tools.error_handling import raise_datos_no_disponibles, raise_unexpected


def _cargar_casillas(año: int) -> list[dict]:
    path = get_data_dir() / str(año) / "casillas.yaml"
    if not path.exists():
        raise DatosFiscalesNoDisponibles(f"No existe {path}")
    with path.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    return data.get("casillas", [])


async def listar_casillas_modelo_100_impl(
    año: int,
    seccion: Optional[str] = None,
) -> str:
    casillas = _cargar_casillas(año)
    if seccion:
        filtradas = [c for c in casillas if c["seccion"] == seccion]
    else:
        filtradas = casillas

    if not filtradas:
        return f"Sin casillas para año={año}, sección={seccion}"

    # Agrupar por sección
    por_seccion: dict[str, list[dict]] = {}
    for c in filtradas:
        por_seccion.setdefault(c["seccion"], []).append(c)

    lineas = [f"## Casillas Modelo 100 — ejercicio {año}", ""]
    for sec, items in por_seccion.items():
        lineas.append(f"### {sec.replace('_', ' ').title()}")
        lineas.append("")
        for c in items:
            lineas.append(f"- **{c['numero']}** · {c['nombre']}")
        lineas.append("")
    lineas.append(f"_Total: {len(filtradas)} casillas_")
    return "\n".join(lineas)


def register_listar_casillas_modelo_100_tool(mcp: FastMCP) -> None:
    @mcp.tool()
    @log_tool
    async def listar_casillas_modelo_100(
        año: int,
        seccion: Optional[str] = None,
    ) -> str:
        """Lista las casillas del Modelo 100 por sección.

        Secciones disponibles: ``identificacion``,
        ``rendimientos_trabajo``, ``capital_inmobiliario``, ``capital_mobiliario``,
        ``actividades_economicas``, ``rentas_imputadas``, ``ganancias_perdidas``,
        ``reducciones``, ``minimos``, ``cuota``, ``deducciones_estatales``,
        ``deducciones_autonomicas``, ``retenciones``, ``resultado``.
        """
        try:
            return await listar_casillas_modelo_100_impl(año, seccion)
        except DatosFiscalesNoDisponibles as exc:
            raise_datos_no_disponibles(exc)
        except Exception as exc:  # noqa: BLE001
            raise_unexpected(exc)
