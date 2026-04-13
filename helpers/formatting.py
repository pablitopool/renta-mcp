"""Utilidades de formateo de salidas markdown para las tools MCP."""

from __future__ import annotations

from decimal import Decimal


def _fmt_eur(valor: Decimal | float | int | None) -> str:
    if valor is None:
        return "—"
    d = Decimal(str(valor))
    return f"{d:,.2f} €".replace(",", "_").replace(".", ",").replace("_", ".")


def tabla_tramos(tramos: list[dict], titulo: str) -> str:
    """Formatea una lista de tramos como tabla markdown."""
    lineas = [
        f"## {titulo}",
        "",
        "| Desde | Hasta | Tipo marginal |",
        "| --- | --- | --- |",
    ]
    for t in tramos:
        desde = _fmt_eur(t["desde"])
        hasta = _fmt_eur(t.get("hasta")) if t.get("hasta") is not None else "—"
        tipo = Decimal(str(t["tipo"])) * 100
        lineas.append(f"| {desde} | {hasta} | {tipo:.2f} % |")
    return "\n".join(lineas)


def desglose_markdown(resultado) -> str:
    """Renderiza un :class:`ResultadoIRPF` como bloque markdown."""
    lineas = ["## Desglose del cálculo", ""]
    for paso in resultado.desglose:
        lineas.append(f"- **{paso.concepto}**: {_fmt_eur(paso.importe)}")
        if paso.detalle:
            lineas.append(f"  - {paso.detalle}")
    return "\n".join(lineas)
