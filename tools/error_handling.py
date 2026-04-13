"""Conversión de excepciones de dominio a :class:`ToolError` para MCP."""

from __future__ import annotations

from typing import NoReturn

from mcp.server.fastmcp.exceptions import ToolError

from helpers.tax_engine import DatosFiscalesNoDisponibles, EntradaInvalida


def raise_entrada_invalida(exc: Exception) -> NoReturn:
    raise ToolError(f"Entrada inválida: {exc}") from exc


def raise_datos_no_disponibles(exc: DatosFiscalesNoDisponibles) -> NoReturn:
    raise ToolError(str(exc)) from exc


def raise_unexpected(exc: Exception) -> NoReturn:
    raise ToolError(f"Error inesperado ({type(exc).__name__}): {exc}") from exc


__all__ = [
    "EntradaInvalida",
    "DatosFiscalesNoDisponibles",
    "raise_entrada_invalida",
    "raise_datos_no_disponibles",
    "raise_unexpected",
]
