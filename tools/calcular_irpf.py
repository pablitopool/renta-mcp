"""Tool MCP: ``calcular_irpf``. Cálculo completo de cuota IRPF."""

from decimal import Decimal
from typing import List, Literal, Optional

from mcp.server.fastmcp import FastMCP

from helpers.data_loader import load_estatal, load_territorio
from helpers.formatting import desglose_markdown
from helpers.logging import log_tool
from helpers.tax_engine import (
    DatosFiscalesNoDisponibles,
    EntradaInvalida,
    Hijo,
    InputIRPF,
    calcular_irpf,
)
from tools.error_handling import (
    raise_datos_no_disponibles,
    raise_entrada_invalida,
    raise_unexpected,
)

DISCLAIMER = (
    "⚠️ Herramienta informativa no vinculante. Para declarar oficialmente "
    "usa Renta WEB AEAT."
)


async def calcular_irpf_impl(
    año: int,
    territorio: str,
    rendimiento_neto_trabajo: float = 0.0,
    rendimiento_neto_capital_mobiliario: float = 0.0,
    rendimiento_neto_capital_inmobiliario: float = 0.0,
    rendimiento_neto_actividades: float = 0.0,
    ganancias_patrimoniales_ahorro: float = 0.0,
    situacion_familiar: Literal[
        "individual", "conjunta_biparental", "conjunta_monoparental"
    ] = "individual",
    edad_contribuyente: int = 40,
    hijos_edades: Optional[List[int]] = None,
    discapacidad_contribuyente: int = 0,
    aportaciones_planes_pensiones: float = 0.0,
    retenciones_practicadas: float = 0.0,
) -> str:
    entrada = InputIRPF(
        año=año,
        territorio=territorio.lower(),
        rendimiento_neto_trabajo=Decimal(str(rendimiento_neto_trabajo)),
        rendimiento_neto_capital_mobiliario=Decimal(
            str(rendimiento_neto_capital_mobiliario)
        ),
        rendimiento_neto_capital_inmobiliario=Decimal(
            str(rendimiento_neto_capital_inmobiliario)
        ),
        rendimiento_neto_actividades=Decimal(str(rendimiento_neto_actividades)),
        ganancias_patrimoniales_ahorro=Decimal(str(ganancias_patrimoniales_ahorro)),
        situacion_familiar=situacion_familiar,
        edad_contribuyente=edad_contribuyente,
        hijos=[Hijo(edad=e) for e in (hijos_edades or [])],
        discapacidad_contribuyente=discapacidad_contribuyente,
        aportaciones_planes_pensiones=Decimal(str(aportaciones_planes_pensiones)),
        retenciones_practicadas=Decimal(str(retenciones_practicadas)),
    )

    estatal = load_estatal(año)
    territorio_datos = load_territorio(año, entrada.territorio)
    resultado = calcular_irpf(entrada, estatal, territorio_datos)

    nombre = territorio_datos["territorio"]["nombre"]
    resumen = (
        f"# Liquidación IRPF {año} — {nombre}\n\n"
        f"- **Cuota íntegra total**: {resultado.cuota_integra_total} €\n"
        f"- **Cuota líquida**: {resultado.cuota_liquida} €\n"
        f"- **Cuota diferencial**: {resultado.cuota_diferencial} € "
        f"({'a devolver' if resultado.cuota_diferencial < 0 else 'a ingresar'})\n\n"
    )
    return resumen + desglose_markdown(resultado) + f"\n\n{DISCLAIMER}"


def register_calcular_irpf_tool(mcp: FastMCP) -> None:
    @mcp.tool()
    @log_tool
    async def calcular_irpf_tool(
        año: int,
        territorio: str,
        rendimiento_neto_trabajo: float = 0.0,
        rendimiento_neto_capital_mobiliario: float = 0.0,
        rendimiento_neto_capital_inmobiliario: float = 0.0,
        rendimiento_neto_actividades: float = 0.0,
        ganancias_patrimoniales_ahorro: float = 0.0,
        situacion_familiar: Literal[
            "individual", "conjunta_biparental", "conjunta_monoparental"
        ] = "individual",
        edad_contribuyente: int = 40,
        hijos_edades: Optional[List[int]] = None,
        discapacidad_contribuyente: int = 0,
        aportaciones_planes_pensiones: float = 0.0,
        retenciones_practicadas: float = 0.0,
    ) -> str:
        """Calcula la liquidación completa del IRPF español.

        Devuelve un markdown con cuota íntegra, líquida, diferencial y
        desglose paso a paso. HERRAMIENTA INFORMATIVA, NO VINCULANTE.

        Parámetros clave:
        - ``año``: ejercicio fiscal (p. ej. 2025).
        - ``territorio``: slug (``madrid``, ``cataluna``, ``bizkaia``, ...).
        - ``rendimiento_neto_trabajo``: rendimiento neto del trabajo antes
          de la reducción del art. 20 LIRPF (el motor la aplica).
        - ``situacion_familiar``: ``individual`` |
          ``conjunta_biparental`` | ``conjunta_monoparental``.
        - ``hijos_edades``: lista de edades de hijos a cargo.
        """
        try:
            return await calcular_irpf_impl(
                año=año,
                territorio=territorio,
                rendimiento_neto_trabajo=rendimiento_neto_trabajo,
                rendimiento_neto_capital_mobiliario=rendimiento_neto_capital_mobiliario,
                rendimiento_neto_capital_inmobiliario=rendimiento_neto_capital_inmobiliario,
                rendimiento_neto_actividades=rendimiento_neto_actividades,
                ganancias_patrimoniales_ahorro=ganancias_patrimoniales_ahorro,
                situacion_familiar=situacion_familiar,
                edad_contribuyente=edad_contribuyente,
                hijos_edades=hijos_edades,
                discapacidad_contribuyente=discapacidad_contribuyente,
                aportaciones_planes_pensiones=aportaciones_planes_pensiones,
                retenciones_practicadas=retenciones_practicadas,
            )
        except EntradaInvalida as exc:
            raise_entrada_invalida(exc)
        except DatosFiscalesNoDisponibles as exc:
            raise_datos_no_disponibles(exc)
        except Exception as exc:  # noqa: BLE001
            raise_unexpected(exc)
