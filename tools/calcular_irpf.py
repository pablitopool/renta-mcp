"""Tool MCP: ``calcular_irpf``. Cálculo completo de cuota IRPF."""

from decimal import Decimal
from typing import List, Literal, Optional

from mcp.server.fastmcp import FastMCP

from helpers.data_loader import load_estatal, load_territorio
from helpers.formatting import desglose_markdown
from helpers.logging import log_tool
from helpers.tax_engine import (
    Ascendiente,
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


def _decimal_dict(values: Optional[dict[str, float]]) -> dict[str, Decimal]:
    return {key: Decimal(str(value)) for key, value in (values or {}).items()}


def _decimal_nested_dict(
    values: Optional[dict[str, dict[str, float]]],
) -> dict[str, dict[str, Decimal]]:
    return {
        key: {subkey: Decimal(str(subvalue)) for subkey, subvalue in inner.items()}
        for key, inner in (values or {}).items()
    }


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
    ascendientes_edades: Optional[List[int]] = None,
    discapacidad_contribuyente: int = 0,
    aportaciones_planes_pensiones: float = 0.0,
    retenciones_practicadas: float = 0.0,
    donativos_ley_49_2002: float = 0.0,
    donativos_otros: float = 0.0,
    inversion_vivienda_transitoria: float = 0.0,
    obras_eficiencia_energetica: float = 0.0,
    obras_eficiencia_energetica_tipo: Literal[
        "calefaccion_refrigeracion", "consumo_primaria", "rehabilitacion"
    ] = "calefaccion_refrigeracion",
    familia_numerosa_categoria: Optional[Literal["general", "especial"]] = None,
    alquiler_vivienda_habitual: float = 0.0,
    inversion_vivienda_habitual: float = 0.0,
    inversion_vivienda_habitual_nacimiento_adopcion: float = 0.0,
    inversion_vivienda_habitual_municipio_despoblacion: float = 0.0,
    intereses_prestamo_adquisicion_vivienda_joven: float = 0.0,
    exceso_intereses_financiacion_vivienda: float = 0.0,
    donativos_autonomicos: float = 0.0,
    cotizaciones_empleados_hogar: float = 0.0,
    gastos_arrendamiento_viviendas: float = 0.0,
    gastos_guarderia: float = 0.0,
    gastos_educativos_descendientes: float = 0.0,
    gastos_material_escolar: float = 0.0,
    gastos_escolaridad: float = 0.0,
    gastos_idiomas: float = 0.0,
    gastos_uniformes: float = 0.0,
    gastos_estudios_descendientes: float = 0.0,
    cuotas_sindicales: float = 0.0,
    nacimientos_adopciones_o_acogimientos: int = 0,
    adopciones_internacionales: int = 0,
    acogimientos_menores: int = 0,
    acogimientos_mayores_o_discapacitados: int = 0,
    cambios_residencia_municipio_despoblacion: int = 0,
    viviendas_vacias_arrendadas: int = 0,
    deducciones_autonomicas_reclamadas: Optional[List[str]] = None,
    bases_deducciones_autonomicas: Optional[dict[str, float]] = None,
    componentes_deducciones_autonomicas: Optional[dict[str, dict[str, float]]] = None,
    meses_maternidad_por_hijo_menor_3: int = 12,
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
        ascendientes=[Ascendiente(edad=e) for e in (ascendientes_edades or [])],
        discapacidad_contribuyente=discapacidad_contribuyente,
        aportaciones_planes_pensiones=Decimal(str(aportaciones_planes_pensiones)),
        retenciones_practicadas=Decimal(str(retenciones_practicadas)),
        donativos_ley_49_2002=Decimal(str(donativos_ley_49_2002)),
        donativos_otros=Decimal(str(donativos_otros)),
        inversion_vivienda_transitoria=Decimal(str(inversion_vivienda_transitoria)),
        obras_eficiencia_energetica=Decimal(str(obras_eficiencia_energetica)),
        obras_eficiencia_energetica_tipo=obras_eficiencia_energetica_tipo,
        familia_numerosa_categoria=familia_numerosa_categoria,
        alquiler_vivienda_habitual=Decimal(str(alquiler_vivienda_habitual)),
        inversion_vivienda_habitual=Decimal(str(inversion_vivienda_habitual)),
        inversion_vivienda_habitual_nacimiento_adopcion=Decimal(
            str(inversion_vivienda_habitual_nacimiento_adopcion)
        ),
        inversion_vivienda_habitual_municipio_despoblacion=Decimal(
            str(inversion_vivienda_habitual_municipio_despoblacion)
        ),
        intereses_prestamo_adquisicion_vivienda_joven=Decimal(
            str(intereses_prestamo_adquisicion_vivienda_joven)
        ),
        exceso_intereses_financiacion_vivienda=Decimal(
            str(exceso_intereses_financiacion_vivienda)
        ),
        donativos_autonomicos=Decimal(str(donativos_autonomicos)),
        cotizaciones_empleados_hogar=Decimal(str(cotizaciones_empleados_hogar)),
        gastos_arrendamiento_viviendas=Decimal(str(gastos_arrendamiento_viviendas)),
        gastos_guarderia=Decimal(str(gastos_guarderia)),
        gastos_educativos_descendientes=Decimal(
            str(gastos_educativos_descendientes)
        ),
        gastos_material_escolar=Decimal(str(gastos_material_escolar)),
        gastos_escolaridad=Decimal(str(gastos_escolaridad)),
        gastos_idiomas=Decimal(str(gastos_idiomas)),
        gastos_uniformes=Decimal(str(gastos_uniformes)),
        gastos_estudios_descendientes=Decimal(str(gastos_estudios_descendientes)),
        cuotas_sindicales=Decimal(str(cuotas_sindicales)),
        nacimientos_adopciones_o_acogimientos=nacimientos_adopciones_o_acogimientos,
        adopciones_internacionales=adopciones_internacionales,
        acogimientos_menores=acogimientos_menores,
        acogimientos_mayores_o_discapacitados=acogimientos_mayores_o_discapacitados,
        cambios_residencia_municipio_despoblacion=(
            cambios_residencia_municipio_despoblacion
        ),
        viviendas_vacias_arrendadas=viviendas_vacias_arrendadas,
        deducciones_autonomicas_reclamadas=deducciones_autonomicas_reclamadas or [],
        bases_deducciones_autonomicas=_decimal_dict(bases_deducciones_autonomicas),
        componentes_deducciones_autonomicas=_decimal_nested_dict(
            componentes_deducciones_autonomicas
        ),
        meses_maternidad_por_hijo_menor_3=meses_maternidad_por_hijo_menor_3,
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
        ascendientes_edades: Optional[List[int]] = None,
        discapacidad_contribuyente: int = 0,
        aportaciones_planes_pensiones: float = 0.0,
        retenciones_practicadas: float = 0.0,
        donativos_ley_49_2002: float = 0.0,
        donativos_otros: float = 0.0,
        inversion_vivienda_transitoria: float = 0.0,
        obras_eficiencia_energetica: float = 0.0,
        obras_eficiencia_energetica_tipo: Literal[
            "calefaccion_refrigeracion", "consumo_primaria", "rehabilitacion"
        ] = "calefaccion_refrigeracion",
        familia_numerosa_categoria: Optional[Literal["general", "especial"]] = None,
        alquiler_vivienda_habitual: float = 0.0,
        inversion_vivienda_habitual: float = 0.0,
        inversion_vivienda_habitual_nacimiento_adopcion: float = 0.0,
        inversion_vivienda_habitual_municipio_despoblacion: float = 0.0,
        intereses_prestamo_adquisicion_vivienda_joven: float = 0.0,
        exceso_intereses_financiacion_vivienda: float = 0.0,
        donativos_autonomicos: float = 0.0,
        cotizaciones_empleados_hogar: float = 0.0,
        gastos_arrendamiento_viviendas: float = 0.0,
        gastos_guarderia: float = 0.0,
        gastos_educativos_descendientes: float = 0.0,
        gastos_material_escolar: float = 0.0,
        gastos_escolaridad: float = 0.0,
        gastos_idiomas: float = 0.0,
        gastos_uniformes: float = 0.0,
        gastos_estudios_descendientes: float = 0.0,
        cuotas_sindicales: float = 0.0,
        nacimientos_adopciones_o_acogimientos: int = 0,
        adopciones_internacionales: int = 0,
        acogimientos_menores: int = 0,
        acogimientos_mayores_o_discapacitados: int = 0,
        cambios_residencia_municipio_despoblacion: int = 0,
        viviendas_vacias_arrendadas: int = 0,
        deducciones_autonomicas_reclamadas: Optional[List[str]] = None,
        bases_deducciones_autonomicas: Optional[dict[str, float]] = None,
        componentes_deducciones_autonomicas: Optional[dict[str, dict[str, float]]] = None,
        meses_maternidad_por_hijo_menor_3: int = 12,
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
        - ``ascendientes_edades``: lista de edades de ascendientes a cargo.
        - Deducciones estatales soportadas: donativos, inversión vivienda
          transitoria, obras de eficiencia energética, familia numerosa y
          maternidad reembolsable.
        - Hechos fiscales para activación automática de deducciones
          autonómicas: alquiler, inversión/obras en vivienda habitual,
          vivienda en municipios en riesgo de despoblación, intereses
          hipotecarios de jóvenes, incremento de costes financieros,
          donativos autonómicos, cotizaciones de empleados de hogar,
          gastos de arrendador, guardería, gastos educativos, cuotas
          sindicales, nacimientos/adopciones y acogimientos.
        - Deducciones autonómicas/forales: pasa los IDs reclamados en
          ``deducciones_autonomicas_reclamadas`` y, si aplican porcentajes,
          sus bases en ``bases_deducciones_autonomicas``. Para fórmulas con
          varios componentes (p. ej. gastos educativos Madrid), usa
          ``componentes_deducciones_autonomicas``.
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
                ascendientes_edades=ascendientes_edades,
                discapacidad_contribuyente=discapacidad_contribuyente,
                aportaciones_planes_pensiones=aportaciones_planes_pensiones,
                retenciones_practicadas=retenciones_practicadas,
                donativos_ley_49_2002=donativos_ley_49_2002,
                donativos_otros=donativos_otros,
                inversion_vivienda_transitoria=inversion_vivienda_transitoria,
                obras_eficiencia_energetica=obras_eficiencia_energetica,
                obras_eficiencia_energetica_tipo=obras_eficiencia_energetica_tipo,
                familia_numerosa_categoria=familia_numerosa_categoria,
                alquiler_vivienda_habitual=alquiler_vivienda_habitual,
                inversion_vivienda_habitual=inversion_vivienda_habitual,
                inversion_vivienda_habitual_nacimiento_adopcion=(
                    inversion_vivienda_habitual_nacimiento_adopcion
                ),
                inversion_vivienda_habitual_municipio_despoblacion=(
                    inversion_vivienda_habitual_municipio_despoblacion
                ),
                intereses_prestamo_adquisicion_vivienda_joven=(
                    intereses_prestamo_adquisicion_vivienda_joven
                ),
                exceso_intereses_financiacion_vivienda=(
                    exceso_intereses_financiacion_vivienda
                ),
                donativos_autonomicos=donativos_autonomicos,
                cotizaciones_empleados_hogar=cotizaciones_empleados_hogar,
                gastos_arrendamiento_viviendas=gastos_arrendamiento_viviendas,
                gastos_guarderia=gastos_guarderia,
                gastos_educativos_descendientes=gastos_educativos_descendientes,
                gastos_material_escolar=gastos_material_escolar,
                gastos_escolaridad=gastos_escolaridad,
                gastos_idiomas=gastos_idiomas,
                gastos_uniformes=gastos_uniformes,
                gastos_estudios_descendientes=gastos_estudios_descendientes,
                cuotas_sindicales=cuotas_sindicales,
                nacimientos_adopciones_o_acogimientos=nacimientos_adopciones_o_acogimientos,
                adopciones_internacionales=adopciones_internacionales,
                acogimientos_menores=acogimientos_menores,
                acogimientos_mayores_o_discapacitados=acogimientos_mayores_o_discapacitados,
                cambios_residencia_municipio_despoblacion=(
                    cambios_residencia_municipio_despoblacion
                ),
                viviendas_vacias_arrendadas=viviendas_vacias_arrendadas,
                deducciones_autonomicas_reclamadas=deducciones_autonomicas_reclamadas,
                bases_deducciones_autonomicas=bases_deducciones_autonomicas,
                componentes_deducciones_autonomicas=componentes_deducciones_autonomicas,
                meses_maternidad_por_hijo_menor_3=meses_maternidad_por_hijo_menor_3,
            )
        except EntradaInvalida as exc:
            raise_entrada_invalida(exc)
        except DatosFiscalesNoDisponibles as exc:
            raise_datos_no_disponibles(exc)
        except Exception as exc:  # noqa: BLE001
            raise_unexpected(exc)
