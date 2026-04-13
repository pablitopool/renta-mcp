"""Tool MCP: ``buscar_casilla`` (búsqueda fuzzy por concepto)."""

from difflib import SequenceMatcher

import yaml
from mcp.server.fastmcp import FastMCP

try:
    from rapidfuzz import fuzz, process
except ModuleNotFoundError:  # pragma: no cover - fallback de entorno
    fuzz = None
    process = None

from helpers.env_config import get_data_dir
from helpers.logging import log_tool
from helpers.tax_engine import DatosFiscalesNoDisponibles
from tools.error_handling import raise_datos_no_disponibles, raise_unexpected


def _cargar_casillas(año: int) -> list[dict]:
    path = get_data_dir() / str(año) / "casillas.yaml"
    if not path.exists():
        raise DatosFiscalesNoDisponibles(f"No existe {path}")
    with path.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh).get("casillas", [])


def _extraer_resultados(query: str, choices: list[str], limite: int) -> list[tuple[str, float, int]]:
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


async def buscar_casilla_impl(query: str, año: int, limite: int = 5) -> str:
    casillas = _cargar_casillas(año)
    candidatos = [(c["nombre"], c) for c in casillas]
    resultados = _extraer_resultados(query, [n for n, _ in candidatos], limite)
    lineas = [f"## Resultados para «{query}» en casillas Modelo 100 {año}", ""]
    for nombre, score, idx in resultados:
        _, casilla = candidatos[idx]
        lineas.append(
            f"- **{casilla['numero']}** ({score:.0f}%) · {casilla['nombre']} "
            f"_[{casilla['seccion']}]_"
        )
    if not resultados:
        lineas.append("Sin coincidencias.")
    return "\n".join(lineas)


def register_buscar_casilla_tool(mcp: FastMCP) -> None:
    @mcp.tool()
    @log_tool
    async def buscar_casilla(
        query: str,
        año: int,
        limite: int = 5,
    ) -> str:
        """Busca casillas del Modelo 100 por concepto (fuzzy match rapidfuzz)."""
        try:
            return await buscar_casilla_impl(query, año, limite)
        except DatosFiscalesNoDisponibles as exc:
            raise_datos_no_disponibles(exc)
        except Exception as exc:  # noqa: BLE001
            raise_unexpected(exc)
