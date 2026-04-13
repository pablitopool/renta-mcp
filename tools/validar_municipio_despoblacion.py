"""Tool MCP: ``validar_municipio_despoblacion``."""

from __future__ import annotations

import unicodedata

from mcp.server.fastmcp import FastMCP

from helpers.env_config import get_data_dir
from helpers.logging import log_tool
from helpers.tax_engine import DatosFiscalesNoDisponibles, EntradaInvalida
from tools.error_handling import (
    raise_datos_no_disponibles,
    raise_entrada_invalida,
    raise_unexpected,
)


def _normalizar(texto: str) -> str:
    cleaned = unicodedata.normalize("NFKD", texto)
    cleaned = "".join(ch for ch in cleaned if not unicodedata.combining(ch))
    return " ".join(cleaned.lower().strip().split())


def _cargar_catalogo(año: int) -> dict:
    import yaml

    path = get_data_dir() / str(año) / "municipios_despoblacion.yaml"
    if not path.exists():
        raise DatosFiscalesNoDisponibles(f"No existe {path}")
    with path.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


async def validar_municipio_despoblacion_impl(
    año: int, ccaa: str, municipio: str
) -> str:
    if año <= 0:
        raise EntradaInvalida("año debe ser mayor que 0")
    if not ccaa.strip() or not municipio.strip():
        raise EntradaInvalida("ccaa y municipio no pueden estar vacios")

    catalogo = _cargar_catalogo(año)
    ccaa_norm = _normalizar(ccaa)
    mun_norm = _normalizar(municipio)

    territorios = catalogo.get("territorios") or {}
    target = None
    for slug, data in territorios.items():
        aliases = [_normalizar(slug)] + [
            _normalizar(alias) for alias in (data.get("aliases") or [])
        ]
        if ccaa_norm in aliases:
            target = data
            break

    if target is None:
        disponibles = ", ".join(sorted(territorios.keys()))
        return (
            "## Validacion de municipio en riesgo de despoblacion\n\n"
            f"No hay catalogo para `{ccaa}` en {año}.\n"
            f"Territorios disponibles: {disponibles}."
        )

    municipios = target.get("municipios") or []
    deducciones = target.get("deducciones_relacionadas") or []
    es_eligible = any(_normalizar(m) == mun_norm for m in municipios)

    lineas = ["## Validacion de municipio en riesgo de despoblacion", ""]
    lineas.append(f"- **CCAA**: {target.get('nombre', ccaa)}")
    lineas.append(f"- **Municipio consultado**: {municipio}")
    lineas.append(
        f"- **Resultado**: {'incluido en catalogo' if es_eligible else 'no incluido'}"
    )
    if deducciones:
        lineas.append("")
        lineas.append("Deducciones potencialmente relacionadas:")
        for deduccion in deducciones:
            lineas.append(f"- `{deduccion}`")
    if not es_eligible and municipios:
        muestra = ", ".join(municipios[:10])
        lineas.append("")
        lineas.append(f"Ejemplos en catalogo: {muestra}")
    return "\n".join(lineas)


def register_validar_municipio_despoblacion_tool(mcp: FastMCP) -> None:
    @mcp.tool()
    @log_tool
    async def validar_municipio_despoblacion(
        año: int, ccaa: str, municipio: str
    ) -> str:
        """Valida si un municipio aparece en el catalogo de despoblacion del ano."""
        try:
            return await validar_municipio_despoblacion_impl(año, ccaa, municipio)
        except EntradaInvalida as exc:
            raise_entrada_invalida(exc)
        except DatosFiscalesNoDisponibles as exc:
            raise_datos_no_disponibles(exc)
        except Exception as exc:  # noqa: BLE001
            raise_unexpected(exc)
