"""Tool MCP: ``preparar_payload_irpf`` (modo preparacion/hibrido)."""

import json
from decimal import Decimal
from typing import Any

from mcp.server.fastmcp import FastMCP

from helpers.logging import log_tool
from helpers.tax_engine import EntradaInvalida
from tools.error_handling import raise_entrada_invalida, raise_unexpected


def _to_decimal(value: Any, field_name: str) -> Decimal:
    try:
        parsed = Decimal(str(value))
    except Exception as exc:  # noqa: BLE001
        raise EntradaInvalida(f"{field_name} debe ser numerico") from exc
    if parsed < 0:
        raise EntradaInvalida(f"{field_name} no puede ser negativo")
    return parsed


async def preparar_payload_irpf_impl(
    año: int,
    territorio: str,
    rendimiento_neto_trabajo: float = 0.0,
    rendimiento_neto_actividades: float = 0.0,
    rendimiento_neto_capital_mobiliario: float = 0.0,
    rendimiento_neto_capital_inmobiliario: float = 0.0,
    ganancias_patrimoniales_ahorro: float = 0.0,
    retenciones_practicadas: float = 0.0,
    pagos_fraccionados: float = 0.0,
    situacion_familiar: str = "individual",
    edad_contribuyente: int = 40,
    hijos_edades: list[int] | None = None,
    ascendientes_edades: list[int] | None = None,
) -> str:
    if año <= 0:
        raise EntradaInvalida("año debe ser mayor que 0")
    if not territorio.strip():
        raise EntradaInvalida("territorio no puede estar vacio")
    if situacion_familiar not in {
        "individual",
        "conjunta_biparental",
        "conjunta_monoparental",
    }:
        raise EntradaInvalida("situacion_familiar invalida")
    if edad_contribuyente < 0 or edad_contribuyente > 120:
        raise EntradaInvalida("edad_contribuyente fuera de rango")

    payload = {
        "año": año,
        "territorio": territorio.lower(),
        "rendimiento_neto_trabajo": float(
            _to_decimal(rendimiento_neto_trabajo, "rendimiento_neto_trabajo")
        ),
        "rendimiento_neto_actividades": float(
            _to_decimal(rendimiento_neto_actividades, "rendimiento_neto_actividades")
        ),
        "rendimiento_neto_capital_mobiliario": float(
            _to_decimal(
                rendimiento_neto_capital_mobiliario,
                "rendimiento_neto_capital_mobiliario",
            )
        ),
        "rendimiento_neto_capital_inmobiliario": float(
            _to_decimal(
                rendimiento_neto_capital_inmobiliario,
                "rendimiento_neto_capital_inmobiliario",
            )
        ),
        "ganancias_patrimoniales_ahorro": float(
            _to_decimal(
                ganancias_patrimoniales_ahorro,
                "ganancias_patrimoniales_ahorro",
            )
        ),
        "retenciones_practicadas": float(
            _to_decimal(retenciones_practicadas, "retenciones_practicadas")
        ),
        "pagos_fraccionados": float(
            _to_decimal(pagos_fraccionados, "pagos_fraccionados")
        ),
        "situacion_familiar": situacion_familiar,
        "edad_contribuyente": edad_contribuyente,
        "hijos_edades": hijos_edades or [],
        "ascendientes_edades": ascendientes_edades or [],
    }

    faltantes: list[str] = []
    if (
        payload["retenciones_practicadas"] == 0
        and payload["rendimiento_neto_trabajo"] > 0
    ):
        faltantes.append(
            "retenciones_practicadas (recomendado para cuota diferencial realista)"
        )

    return (
        "## Payload normalizado para `calcular_irpf`\n\n"
        "```json\n"
        f"{json.dumps(payload, ensure_ascii=False, indent=2)}\n"
        "```\n\n"
        + (
            "Campos recomendados pendientes:\n"
            + "\n".join([f"- {item}" for item in faltantes])
            if faltantes
            else "No se detectan campos criticos pendientes para una simulacion basica."
        )
    )


def register_preparar_payload_irpf_tool(mcp: FastMCP) -> None:
    @mcp.tool()
    @log_tool
    async def preparar_payload_irpf(
        año: int,
        territorio: str,
        rendimiento_neto_trabajo: float = 0.0,
        rendimiento_neto_actividades: float = 0.0,
        rendimiento_neto_capital_mobiliario: float = 0.0,
        rendimiento_neto_capital_inmobiliario: float = 0.0,
        ganancias_patrimoniales_ahorro: float = 0.0,
        retenciones_practicadas: float = 0.0,
        pagos_fraccionados: float = 0.0,
        situacion_familiar: str = "individual",
        edad_contribuyente: int = 40,
        hijos_edades: list[int] | None = None,
        ascendientes_edades: list[int] | None = None,
    ) -> str:
        """Normaliza un bloque de datos para alimentar `calcular_irpf`."""
        try:
            return await preparar_payload_irpf_impl(
                año=año,
                territorio=territorio,
                rendimiento_neto_trabajo=rendimiento_neto_trabajo,
                rendimiento_neto_actividades=rendimiento_neto_actividades,
                rendimiento_neto_capital_mobiliario=rendimiento_neto_capital_mobiliario,
                rendimiento_neto_capital_inmobiliario=rendimiento_neto_capital_inmobiliario,
                ganancias_patrimoniales_ahorro=ganancias_patrimoniales_ahorro,
                retenciones_practicadas=retenciones_practicadas,
                pagos_fraccionados=pagos_fraccionados,
                situacion_familiar=situacion_familiar,
                edad_contribuyente=edad_contribuyente,
                hijos_edades=hijos_edades,
                ascendientes_edades=ascendientes_edades,
            )
        except EntradaInvalida as exc:
            raise_entrada_invalida(exc)
        except Exception as exc:  # noqa: BLE001
            raise_unexpected(exc)
