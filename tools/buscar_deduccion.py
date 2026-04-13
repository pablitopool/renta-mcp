"""Tool MCP: ``buscar_deduccion`` (búsqueda fuzzy en catálogo autonómico + estatal)."""

from difflib import SequenceMatcher
from typing import Optional

from mcp.server.fastmcp import FastMCP
from pydantic import ValidationError

try:
    from rapidfuzz import fuzz, process
except ModuleNotFoundError:  # pragma: no cover - fallback de entorno
    fuzz = None
    process = None

from helpers.data_loader import listar_territorios, load_territorio
from helpers.logging import log_tool
from helpers.tax_engine import DatosFiscalesNoDisponibles
from tools.error_handling import raise_unexpected


def _extraer_resultados(
    query: str, choices: list[str], limite: int
) -> list[tuple[str, float, int]]:
    if process is not None and fuzz is not None:
        return process.extract(query, choices, scorer=fuzz.WRatio, limit=limite)

    resultados: list[tuple[str, float, int]] = []
    query_norm = query.lower()
    for idx, choice in enumerate(choices):
        choice_norm = choice.lower()
        ratio = SequenceMatcher(None, query_norm, choice_norm).ratio() * 100
        if query_norm in choice_norm:
            ratio = max(ratio, 90.0)
        resultados.append((choice, ratio, idx))
    resultados.sort(key=lambda item: item[1], reverse=True)
    return resultados[:limite]


async def buscar_deduccion_impl(
    query: str,
    año: int,
    ccaa: Optional[str] = None,
    limite: int = 10,
) -> str:
    deducciones: list[tuple[str, str, dict]] = []

    if ccaa:
        try:
            datos = load_territorio(año, ccaa.lower())
            nombre_cc = datos["territorio"]["nombre"]
            for d in datos.get("deducciones", []) or []:
                deducciones.append((nombre_cc, d["titulo"], d))
        except DatosFiscalesNoDisponibles:
            pass
    else:
        for slug in listar_territorios(año):
            try:
                datos = load_territorio(año, slug)
            except (DatosFiscalesNoDisponibles, ValidationError):
                continue
            nombre_cc = datos["territorio"]["nombre"]
            for d in datos.get("deducciones", []) or []:
                deducciones.append((nombre_cc, d["titulo"], d))

    if not deducciones:
        return f"Sin deducciones registradas para año={año} ccaa={ccaa or 'todas'}"

    titulos = [t for _, t, _ in deducciones]
    resultados = _extraer_resultados(query, titulos, limite)
    lineas = [f"## Deducciones que coinciden con «{query}» — {año}", ""]
    for titulo, score, idx in resultados:
        nombre_cc, _, d = deducciones[idx]
        detalles = []
        if d.get("porcentaje"):
            detalles.append(f"{float(d['porcentaje']) * 100:.1f}%")
        if d.get("importe_fijo"):
            detalles.append(f"{d['importe_fijo']} €")
        extra = f" — {' · '.join(detalles)}" if detalles else ""
        lineas.append(
            f"- **{titulo}** (`{d['id']}`) ({score:.0f}%) · _{nombre_cc}_{extra}"
        )
    return "\n".join(lineas)


def register_buscar_deduccion_tool(mcp: FastMCP) -> None:
    @mcp.tool()
    @log_tool
    async def buscar_deduccion(
        query: str,
        año: int,
        ccaa: Optional[str] = None,
        limite: int = 10,
    ) -> str:
        """Busca deducciones por concepto en una o todas las CCAA (fuzzy match)."""
        try:
            return await buscar_deduccion_impl(query, año, ccaa, limite)
        except Exception as exc:  # noqa: BLE001
            raise_unexpected(exc)
