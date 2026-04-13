"""Tool MCP: ``calcular_ganancia_cripto_fifo``."""

from __future__ import annotations

from collections import deque
from decimal import Decimal

from mcp.server.fastmcp import FastMCP

from helpers.logging import log_tool
from helpers.tax_engine import EntradaInvalida
from tools.error_handling import raise_entrada_invalida, raise_unexpected

DECIMALES = Decimal("0.01")


def _eur(valor: Decimal) -> Decimal:
    return valor.quantize(DECIMALES)


def _parse_lote(texto: str) -> tuple[Decimal, Decimal]:
    # formato: "cantidad@precio_unitario"; ejemplo "0.4@25000"
    if "@" not in texto:
        raise EntradaInvalida(
            "Formato de lote invalido. Usa cantidad@precio_unitario, ej. 0.4@25000"
        )
    raw_qty, raw_price = texto.split("@", 1)
    qty = Decimal(raw_qty.strip())
    price = Decimal(raw_price.strip())
    if qty <= 0 or price < 0:
        raise EntradaInvalida("Cantidad y precio deben ser positivos")
    return qty, price


async def calcular_ganancia_cripto_fifo_impl(
    compras: list[str],
    ventas: list[str],
    comisiones_totales: float = 0.0,
) -> str:
    if not compras or not ventas:
        raise EntradaInvalida("Debes indicar al menos una compra y una venta")
    if len(compras) > 500 or len(ventas) > 500:
        raise EntradaInvalida("Limite de 500 operaciones por bloque")

    cola: deque[tuple[Decimal, Decimal]] = deque()
    for lote in compras:
        cola.append(_parse_lote(lote))

    ganancia_total = Decimal(0)
    detalle: list[str] = []

    for venta in ventas:
        qty_venta, precio_venta = _parse_lote(venta)
        pendiente = qty_venta
        coste = Decimal(0)

        while pendiente > 0:
            if not cola:
                raise EntradaInvalida(
                    "Ventas superiores al inventario de compras (FIFO insuficiente)"
                )
            qty_compra, precio_compra = cola[0]
            tomada = min(qty_compra, pendiente)
            coste += tomada * precio_compra
            pendiente -= tomada
            qty_restante = qty_compra - tomada
            if qty_restante == 0:
                cola.popleft()
            else:
                cola[0] = (qty_restante, precio_compra)

        ingreso = qty_venta * precio_venta
        ganancia_venta = ingreso - coste
        ganancia_total += ganancia_venta
        detalle.append(
            f"- Venta {qty_venta} u @ {precio_venta} EUR -> ingreso {_eur(ingreso)} EUR, coste FIFO {_eur(coste)} EUR, ganancia {_eur(ganancia_venta)} EUR"
        )

    comisiones = Decimal(str(comisiones_totales))
    if comisiones < 0:
        raise EntradaInvalida("comisiones_totales no puede ser negativo")
    ganancia_neta = ganancia_total - comisiones

    return (
        "## Ganancias/pérdidas cripto por metodo FIFO\n\n"
        + "\n".join(detalle)
        + "\n\n"
        + f"- **Ganancia bruta total**: {_eur(ganancia_total)} EUR\n"
        + f"- **Comisiones totales**: {_eur(comisiones)} EUR\n"
        + f"- **Ganancia neta imputable ahorro**: {_eur(ganancia_neta)} EUR\n\n"
        + "Puedes trasladar este resultado a `calcular_irpf` como `ganancias_patrimoniales_ahorro`."
    )


def register_calcular_ganancia_cripto_fifo_tool(mcp: FastMCP) -> None:
    @mcp.tool()
    @log_tool
    async def calcular_ganancia_cripto_fifo(
        compras: list[str],
        ventas: list[str],
        comisiones_totales: float = 0.0,
    ) -> str:
        """Calcula ganancia/pérdida de cripto con criterio FIFO (MVP)."""
        try:
            return await calcular_ganancia_cripto_fifo_impl(
                compras=compras,
                ventas=ventas,
                comisiones_totales=comisiones_totales,
            )
        except EntradaInvalida as exc:
            raise_entrada_invalida(exc)
        except Exception as exc:  # noqa: BLE001
            raise_unexpected(exc)
