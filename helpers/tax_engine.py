"""Motor de cálculo del IRPF español.

Implementa el esquema de liquidación del IRPF definido en los artículos 63-79
de la Ley 35/2006 (LIRPF):

1. Rendimiento neto → reducción por rendimientos del trabajo (art. 20).
2. Base imponible general / base imponible del ahorro (arts. 47-49).
3. Reducciones sobre BI general → base liquidable general (art. 50).
4. Mínimo personal y familiar (arts. 56-61): NO resta de la base; se aplica
   como "tipo cero" descontando ``escala(min(BL, mínimo))`` de ``escala(BL)``.
5. Cuota íntegra estatal + autonómica (o escala foral única).
6. Deducciones estatales y autonómicas → cuota líquida.
7. Retenciones y pagos fraccionados → cuota diferencial.

Todos los cálculos se realizan en ``Decimal`` para evitar drift céntimo.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import ROUND_HALF_UP, Decimal
from typing import Literal

CENTIMOS = Decimal("0.01")


class EntradaInvalida(ValueError):
    """La entrada no pudo validarse (importes negativos, situación imposible, ...)."""


class DatosFiscalesNoDisponibles(LookupError):
    """No hay YAML curado para el (año, territorio) solicitado."""


@dataclass(frozen=True)
class Tramo:
    desde: Decimal
    hasta: Decimal | None
    tipo: Decimal
    cuota_acumulada: Decimal = Decimal(0)

    def contiene(self, base: Decimal) -> bool:
        if base < self.desde:
            return False
        if self.hasta is None:
            return True
        return base < self.hasta


@dataclass(frozen=True)
class Escala:
    tramos: tuple[Tramo, ...]

    @classmethod
    def desde_lista(cls, items: list[dict]) -> "Escala":
        tramos_con_cuota: list[Tramo] = []
        cuota_acumulada = Decimal(0)
        ultimo_desde = Decimal(0)
        for idx, item in enumerate(items):
            desde = Decimal(str(item["desde"]))
            hasta_raw = item.get("hasta")
            hasta = Decimal(str(hasta_raw)) if hasta_raw is not None else None
            tipo = Decimal(str(item["tipo"]))
            if idx == 0 and desde != 0:
                raise EntradaInvalida(
                    f"La escala debe comenzar en 0, encontrado {desde}"
                )
            if idx > 0 and desde != ultimo_desde:
                raise EntradaInvalida(
                    f"Discontinuidad en escala: tramo {idx} empieza en {desde}, "
                    f"anterior terminaba en {ultimo_desde}"
                )
            if hasta is not None and hasta <= desde:
                raise EntradaInvalida(f"Tramo inválido: desde={desde}, hasta={hasta}")
            tramos_con_cuota.append(
                Tramo(
                    desde=desde,
                    hasta=hasta,
                    tipo=tipo,
                    cuota_acumulada=cuota_acumulada,
                )
            )
            if hasta is not None:
                cuota_acumulada += (hasta - desde) * tipo
                ultimo_desde = hasta
        return cls(tramos=tuple(tramos_con_cuota))


def aplicar_escala(base: Decimal, escala: Escala) -> Decimal:
    """Aplica una escala progresiva marginal a ``base``.

    Devuelve la cuota sin redondear para permitir composiciones posteriores.
    """
    if base <= 0:
        return Decimal(0)
    for tramo in escala.tramos:
        if tramo.contiene(base):
            return tramo.cuota_acumulada + (base - tramo.desde) * tramo.tipo
    ultimo = escala.tramos[-1]
    return ultimo.cuota_acumulada + (base - ultimo.desde) * ultimo.tipo


def redondear(valor: Decimal) -> Decimal:
    """Redondeo a 2 decimales con ROUND_HALF_UP (criterio AEAT)."""
    return valor.quantize(CENTIMOS, rounding=ROUND_HALF_UP)


@dataclass
class Hijo:
    edad: int
    discapacidad_porcentaje: int = 0


@dataclass
class Ascendiente:
    edad: int
    discapacidad_porcentaje: int = 0


RegimenTipo = Literal["comun", "foral"]
SituacionFamiliar = Literal[
    "individual", "conjunta_biparental", "conjunta_monoparental"
]


FamiliaNumerosaCategoria = Literal["general", "especial"]


@dataclass
class InputIRPF:
    año: int
    territorio: str
    rendimiento_neto_trabajo: Decimal = Decimal(0)
    rendimiento_neto_capital_mobiliario: Decimal = Decimal(0)
    rendimiento_neto_capital_inmobiliario: Decimal = Decimal(0)
    rendimiento_neto_actividades: Decimal = Decimal(0)
    ganancias_patrimoniales_ahorro: Decimal = Decimal(0)
    situacion_familiar: SituacionFamiliar = "individual"
    edad_contribuyente: int = 40
    hijos: list[Hijo] = field(default_factory=list)
    ascendientes: list[Ascendiente] = field(default_factory=list)
    discapacidad_contribuyente: int = 0
    aportaciones_planes_pensiones: Decimal = Decimal(0)
    retenciones_practicadas: Decimal = Decimal(0)
    # Fase 7 — Deducciones estatales en cuota (arts. 68-81 bis LIRPF)
    donativos_ley_49_2002: Decimal = Decimal(0)
    donativos_otros: Decimal = Decimal(0)
    inversion_vivienda_transitoria: Decimal = Decimal(0)
    obras_eficiencia_energetica: Decimal = Decimal(0)
    obras_eficiencia_energetica_tipo: Literal[
        "calefaccion_refrigeracion", "consumo_primaria", "rehabilitacion"
    ] = "calefaccion_refrigeracion"
    familia_numerosa_categoria: FamiliaNumerosaCategoria | None = None
    alquiler_vivienda_habitual: Decimal = Decimal(0)
    inversion_vivienda_habitual: Decimal = Decimal(0)
    inversion_vivienda_habitual_nacimiento_adopcion: Decimal = Decimal(0)
    inversion_vivienda_habitual_municipio_despoblacion: Decimal = Decimal(0)
    intereses_prestamo_adquisicion_vivienda_joven: Decimal = Decimal(0)
    exceso_intereses_financiacion_vivienda: Decimal = Decimal(0)
    donativos_autonomicos: Decimal = Decimal(0)
    cotizaciones_empleados_hogar: Decimal = Decimal(0)
    gastos_arrendamiento_viviendas: Decimal = Decimal(0)
    gastos_guarderia: Decimal = Decimal(0)
    gastos_educativos_descendientes: Decimal = Decimal(0)
    gastos_material_escolar: Decimal = Decimal(0)
    gastos_escolaridad: Decimal = Decimal(0)
    gastos_idiomas: Decimal = Decimal(0)
    gastos_uniformes: Decimal = Decimal(0)
    gastos_estudios_descendientes: Decimal = Decimal(0)
    cuotas_sindicales: Decimal = Decimal(0)
    nacimientos_adopciones_o_acogimientos: int = 0
    adopciones_internacionales: int = 0
    acogimientos_menores: int = 0
    acogimientos_mayores_o_discapacitados: int = 0
    cambios_residencia_municipio_despoblacion: int = 0
    viviendas_vacias_arrendadas: int = 0
    deducciones_autonomicas_reclamadas: list[str] = field(default_factory=list)
    bases_deducciones_autonomicas: dict[str, Decimal] = field(default_factory=dict)
    componentes_deducciones_autonomicas: dict[str, dict[str, Decimal]] = field(
        default_factory=dict
    )
    # Maternidad: hijos menores de 3 años a efectos del art. 81 LIRPF.
    meses_maternidad_por_hijo_menor_3: int = 12


@dataclass
class PasoCalculo:
    concepto: str
    importe: Decimal
    detalle: str = ""


@dataclass
class ResultadoIRPF:
    base_imponible_general: Decimal
    base_imponible_ahorro: Decimal
    reduccion_rendimientos_trabajo: Decimal
    reduccion_tributacion_conjunta: Decimal
    reduccion_planes_pensiones: Decimal
    base_liquidable_general: Decimal
    base_liquidable_ahorro: Decimal
    minimo_personal_familiar: Decimal
    cuota_integra_estatal: Decimal
    cuota_integra_autonomica: Decimal
    cuota_integra_total: Decimal
    cuota_liquida: Decimal
    cuota_diferencial: Decimal
    retenciones: Decimal
    regimen: RegimenTipo
    desglose: list[PasoCalculo] = field(default_factory=list)
    # Fase 7 — detalle deducciones + maternidad reembolsable
    deducciones_estatales_total: Decimal = Decimal(0)
    deducciones_estatales_detalle: list[PasoCalculo] = field(default_factory=list)
    deducciones_autonomicas_total: Decimal = Decimal(0)
    deducciones_autonomicas_detalle: list[PasoCalculo] = field(default_factory=list)
    maternidad_reembolsable: Decimal = Decimal(0)
    devolucion_maternidad: Decimal = Decimal(0)


def _texto_deduccion(deduccion: dict) -> str:
    return " ".join(
        [
            str(deduccion.get("id", "")),
            str(deduccion.get("titulo", "")),
            str(deduccion.get("categoria", "")),
        ]
    ).lower()


def _validar_edad(etiqueta: str, edad: int) -> None:
    if edad < 0 or edad > 120:
        raise EntradaInvalida(f"{etiqueta} fuera de rango razonable: {edad}")


def validar_entrada_irpf(entrada: InputIRPF) -> None:
    if entrada.año <= 0:
        raise EntradaInvalida(f"Año inválido: {entrada.año}")
    if not entrada.territorio.strip():
        raise EntradaInvalida("territorio no puede estar vacío")

    _validar_edad("edad_contribuyente", entrada.edad_contribuyente)
    for i, hijo in enumerate(entrada.hijos, start=1):
        _validar_edad(f"edad hijo {i}", hijo.edad)
    for i, asc in enumerate(entrada.ascendientes, start=1):
        _validar_edad(f"edad ascendiente {i}", asc.edad)

    if entrada.discapacidad_contribuyente < 0 or entrada.discapacidad_contribuyente > 100:
        raise EntradaInvalida(
            "discapacidad_contribuyente debe estar entre 0 y 100"
        )
    if entrada.meses_maternidad_por_hijo_menor_3 < 0:
        raise EntradaInvalida("meses_maternidad_por_hijo_menor_3 no puede ser negativo")
    if entrada.nacimientos_adopciones_o_acogimientos < 0:
        raise EntradaInvalida("nacimientos_adopciones_o_acogimientos no puede ser negativo")
    if entrada.adopciones_internacionales < 0:
        raise EntradaInvalida("adopciones_internacionales no puede ser negativo")
    if entrada.acogimientos_menores < 0:
        raise EntradaInvalida("acogimientos_menores no puede ser negativo")
    if entrada.acogimientos_mayores_o_discapacitados < 0:
        raise EntradaInvalida(
            "acogimientos_mayores_o_discapacitados no puede ser negativo"
        )
    if entrada.cambios_residencia_municipio_despoblacion < 0:
        raise EntradaInvalida(
            "cambios_residencia_municipio_despoblacion no puede ser negativo"
        )
    if entrada.viviendas_vacias_arrendadas < 0:
        raise EntradaInvalida("viviendas_vacias_arrendadas no puede ser negativo")

    importes = {
        "rendimiento_neto_trabajo": entrada.rendimiento_neto_trabajo,
        "rendimiento_neto_capital_mobiliario": entrada.rendimiento_neto_capital_mobiliario,
        "rendimiento_neto_capital_inmobiliario": entrada.rendimiento_neto_capital_inmobiliario,
        "rendimiento_neto_actividades": entrada.rendimiento_neto_actividades,
        "ganancias_patrimoniales_ahorro": entrada.ganancias_patrimoniales_ahorro,
        "aportaciones_planes_pensiones": entrada.aportaciones_planes_pensiones,
        "retenciones_practicadas": entrada.retenciones_practicadas,
        "donativos_ley_49_2002": entrada.donativos_ley_49_2002,
        "donativos_otros": entrada.donativos_otros,
        "inversion_vivienda_transitoria": entrada.inversion_vivienda_transitoria,
        "obras_eficiencia_energetica": entrada.obras_eficiencia_energetica,
        "alquiler_vivienda_habitual": entrada.alquiler_vivienda_habitual,
        "inversion_vivienda_habitual": entrada.inversion_vivienda_habitual,
        "inversion_vivienda_habitual_nacimiento_adopcion": (
            entrada.inversion_vivienda_habitual_nacimiento_adopcion
        ),
        "inversion_vivienda_habitual_municipio_despoblacion": (
            entrada.inversion_vivienda_habitual_municipio_despoblacion
        ),
        "intereses_prestamo_adquisicion_vivienda_joven": (
            entrada.intereses_prestamo_adquisicion_vivienda_joven
        ),
        "exceso_intereses_financiacion_vivienda": (
            entrada.exceso_intereses_financiacion_vivienda
        ),
        "donativos_autonomicos": entrada.donativos_autonomicos,
        "cotizaciones_empleados_hogar": entrada.cotizaciones_empleados_hogar,
        "gastos_arrendamiento_viviendas": entrada.gastos_arrendamiento_viviendas,
        "gastos_guarderia": entrada.gastos_guarderia,
        "gastos_educativos_descendientes": entrada.gastos_educativos_descendientes,
        "gastos_material_escolar": entrada.gastos_material_escolar,
        "gastos_escolaridad": entrada.gastos_escolaridad,
        "gastos_idiomas": entrada.gastos_idiomas,
        "gastos_uniformes": entrada.gastos_uniformes,
        "gastos_estudios_descendientes": entrada.gastos_estudios_descendientes,
        "cuotas_sindicales": entrada.cuotas_sindicales,
    }
    for etiqueta, valor in importes.items():
        if valor < 0:
            raise EntradaInvalida(f"{etiqueta} no puede ser negativo")

    for ded_id, valor in entrada.bases_deducciones_autonomicas.items():
        if valor < 0:
            raise EntradaInvalida(
                f"Base negativa para deducción autonómica {ded_id}: {valor}"
            )
    for ded_id, componentes in entrada.componentes_deducciones_autonomicas.items():
        for componente, valor in componentes.items():
            if valor < 0:
                raise EntradaInvalida(
                    f"Componente negativo para {ded_id}.{componente}: {valor}"
                )


def calcular_reduccion_trabajo(rendimiento_neto: Decimal, parametros: dict) -> Decimal:
    """Reducción por rendimientos del trabajo (art. 20 LIRPF).

    Parametrizada desde ``data/{año}/estatal.yaml`` en el bloque
    ``reduccion_rendimientos_trabajo`` con claves ``umbral_maximo_base``,
    ``umbral_maximo``, ``importe_maximo`` y ``pendiente``.
    """
    if rendimiento_neto <= 0:
        return Decimal(0)
    umbral_base = Decimal(str(parametros["umbral_maximo_base"]))
    umbral_sup = Decimal(str(parametros["umbral_maximo"]))
    importe_max = Decimal(str(parametros["importe_maximo"]))
    pendiente = Decimal(str(parametros["pendiente"]))

    if rendimiento_neto <= umbral_base:
        return importe_max
    if rendimiento_neto <= umbral_sup:
        reducido = importe_max - pendiente * (rendimiento_neto - umbral_base)
        return max(reducido, Decimal(0))
    return Decimal(0)


def calcular_minimo_personal_familiar(entrada: InputIRPF, minimos: dict) -> Decimal:
    """Suma mínimo del contribuyente + descendientes + ascendientes + discapacidad."""
    total = Decimal(str(minimos["personal"]))

    if entrada.edad_contribuyente >= 65:
        total += Decimal(str(minimos.get("edad_mayor_65", 0)))
    if entrada.edad_contribuyente >= 75:
        total += Decimal(str(minimos.get("edad_mayor_75", 0)))

    por_descendiente = [Decimal(str(x)) for x in minimos.get("por_descendiente", [])]
    for i, hijo in enumerate(entrada.hijos):
        if i < len(por_descendiente):
            total += por_descendiente[i]
        else:
            total += por_descendiente[-1] if por_descendiente else Decimal(0)
        if hijo.edad < 3:
            total += Decimal(str(minimos.get("hijo_menor_3", 0)))

    for asc in entrada.ascendientes:
        if asc.edad >= 65:
            total += Decimal(str(minimos.get("por_ascendiente", 0)))
        if asc.edad >= 75:
            total += Decimal(str(minimos.get("ascendiente_mayor_75", 0)))

    if entrada.discapacidad_contribuyente >= 33:
        total += Decimal(str(minimos.get("discapacidad_33_65", 0)))
    if entrada.discapacidad_contribuyente >= 65:
        total += Decimal(str(minimos.get("discapacidad_65_mas", 0)))

    return total


def aplicar_deducciones_estatales(
    cuota_integra_estatal: Decimal,
    base_liquidable_general: Decimal,
    entrada: InputIRPF,
    datos_estatal: dict,
) -> tuple[Decimal, list[PasoCalculo]]:
    """Aplica las deducciones estatales en cuota (arts. 68-81 bis LIRPF).

    Devuelve (deducciones_totales, desglose). La deducción NO puede superar
    la cuota íntegra estatal (la maternidad se calcula aparte porque es
    reembolsable).
    """
    detalle: list[PasoCalculo] = []
    total = Decimal(0)
    ded_cfg = datos_estatal.get("deducciones_estatales") or {}

    # Donativos Ley 49/2002 — 80% primeros 250€, 40% sobre el exceso.
    if entrada.donativos_ley_49_2002 > 0:
        params = ded_cfg.get("donativos_ley_49_2002", {})
        tramo1 = Decimal(str(params.get("base_primer_tramo", 250)))
        pct1 = Decimal(str(params.get("porcentaje_primer_tramo", 0.80)))
        pct2 = Decimal(str(params.get("porcentaje_resto", 0.40)))
        base = entrada.donativos_ley_49_2002
        primer = min(base, tramo1) * pct1
        resto = max(base - tramo1, Decimal(0)) * pct2
        ded = primer + resto
        total += ded
        detalle.append(
            PasoCalculo(
                concepto="Deducción donativos Ley 49/2002",
                importe=ded,
                detalle=f"Base {base} € (80% primeros {tramo1} €, 40% resto)",
            )
        )

    # Donativos a otras fundaciones no declaradas de utilidad pública (10%).
    if entrada.donativos_otros > 0:
        pct = Decimal(str(ded_cfg.get("donativos_otros", {}).get("porcentaje", 0.10)))
        ded = entrada.donativos_otros * pct
        total += ded
        detalle.append(PasoCalculo(concepto="Deducción donativos otros", importe=ded))

    # Inversión vivienda habitual — régimen transitorio DT 18ª LIRPF.
    if entrada.inversion_vivienda_transitoria > 0:
        params = ded_cfg.get("vivienda_transitoria", {})
        base_max = Decimal(str(params.get("base_maxima", 9040)))
        pct = Decimal(str(params.get("porcentaje", 0.15)))
        ded = min(entrada.inversion_vivienda_transitoria, base_max) * pct
        total += ded
        detalle.append(
            PasoCalculo(
                concepto="Deducción vivienda habitual (régimen transitorio)",
                importe=ded,
                detalle=f"15% sobre máx. {base_max} €",
            )
        )

    # Familia numerosa o discapacidad a cargo (art. 81 bis).
    if entrada.familia_numerosa_categoria:
        params = ded_cfg.get("familia_numerosa", {})
        if entrada.familia_numerosa_categoria == "especial":
            ded = Decimal(str(params.get("especial", 2400)))
        else:
            ded = Decimal(str(params.get("general", 1200)))
        total += ded
        detalle.append(
            PasoCalculo(
                concepto=f"Deducción familia numerosa "
                f"{entrada.familia_numerosa_categoria}",
                importe=ded,
            )
        )

    # Obras eficiencia energética (DA 50ª).
    if entrada.obras_eficiencia_energetica > 0:
        params = ded_cfg.get("obras_eficiencia_energetica", {})
        porcentajes = {
            "calefaccion_refrigeracion": Decimal(
                str(params.get("calefaccion_refrigeracion", 0.20))
            ),
            "consumo_primaria": Decimal(str(params.get("consumo_primaria", 0.40))),
            "rehabilitacion": Decimal(str(params.get("rehabilitacion", 0.60))),
        }
        base_max = Decimal(str(params.get("base_maxima", 5000)))
        pct = porcentajes[entrada.obras_eficiencia_energetica_tipo]
        ded = min(entrada.obras_eficiencia_energetica, base_max) * pct
        total += ded
        detalle.append(
            PasoCalculo(
                concepto=f"Deducción obras eficiencia energética "
                f"({entrada.obras_eficiencia_energetica_tipo})",
                importe=ded,
            )
        )

    # El límite global de la deducción es la cuota íntegra estatal
    # (las deducciones no pueden generar cuota negativa, salvo maternidad).
    if total > cuota_integra_estatal and cuota_integra_estatal >= 0:
        total = max(cuota_integra_estatal, Decimal(0))
        detalle.append(
            PasoCalculo(
                concepto="Limitación por cuota íntegra estatal", importe=Decimal(0)
            )
        )
    return total, detalle


def calcular_maternidad_reembolsable(
    entrada: InputIRPF, datos_estatal: dict
) -> Decimal:
    """Deducción por maternidad (art. 81 LIRPF) como impuesto negativo.

    100 €/mes por cada hijo <3 años, máx. 1.200 €/año por hijo. Reembolsable
    aunque la cuota líquida sea 0.
    """
    params = datos_estatal.get("deducciones_estatales", {}).get("maternidad", {})
    euros_mes = Decimal(str(params.get("euros_mes", 100)))
    max_anual = Decimal(str(params.get("max_anual_por_hijo", 1200)))
    meses = min(max(entrada.meses_maternidad_por_hijo_menor_3, 0), 12)
    hijos_menores_3 = sum(1 for h in entrada.hijos if h.edad < 3)
    if hijos_menores_3 == 0:
        return Decimal(0)
    por_hijo = min(euros_mes * Decimal(meses), max_anual)
    return por_hijo * Decimal(hijos_menores_3)


def _count_hijos_relevantes(deduccion: dict, entrada: InputIRPF) -> int:
    if not entrada.hijos:
        texto = _texto_deduccion(deduccion)
        if (
            "nacimiento" in texto
            or "parto múltiple" in texto
            or ("adop" in texto and "internacional" not in texto)
        ):
            return max(entrada.nacimientos_adopciones_o_acogimientos, 0)
        return 0
    texto = _texto_deduccion(deduccion)
    if (
        "nacimiento" in texto
        or "parto múltiple" in texto
        or ("adop" in texto and "internacional" not in texto)
    ):
        return (
            entrada.nacimientos_adopciones_o_acogimientos
            if entrada.nacimientos_adopciones_o_acogimientos > 0
            else len(entrada.hijos)
        )
    if (
        "menores de 3" in texto
        or "menor de 3" in texto
        or "guarder" in texto
        or "cuidado-descendientes" in texto
    ):
        return sum(1 for h in entrada.hijos if h.edad < 3)
    return len(entrada.hijos)


def _count_unidades_deduccion(deduccion: dict, entrada: InputIRPF) -> int:
    por_unidad = deduccion.get("por_unidad")
    if por_unidad == "hijo":
        return _count_hijos_relevantes(deduccion, entrada)
    if por_unidad == "ascendiente":
        return sum(
            1
            for asc in entrada.ascendientes
            if asc.edad >= 65 or asc.discapacidad_porcentaje >= 33
        )
    if por_unidad == "acogimiento_menor":
        return entrada.acogimientos_menores
    if por_unidad == "acogimiento_mayor_discapacitado":
        return entrada.acogimientos_mayores_o_discapacitados
    if por_unidad == "adopcion_internacional":
        return entrada.adopciones_internacionales
    if por_unidad == "cambio_residencia_despoblacion":
        return entrada.cambios_residencia_municipio_despoblacion
    if por_unidad == "vivienda_vacia_arrendada":
        return entrada.viviendas_vacias_arrendadas
    return 1


def derivar_deducciones_autonomicas(
    entrada: InputIRPF,
    catalogo: list[dict],
) -> tuple[list[str], dict[str, Decimal], dict[str, dict[str, Decimal]]]:
    ids = list(entrada.deducciones_autonomicas_reclamadas)
    bases = dict(entrada.bases_deducciones_autonomicas)
    componentes = {
        ded_id: dict(values)
        for ded_id, values in entrada.componentes_deducciones_autonomicas.items()
    }

    def ensure_id(ded_id: str) -> None:
        if ded_id not in ids:
            ids.append(ded_id)

    for ded in catalogo:
        ded_id = ded["id"]
        texto = _texto_deduccion(ded)

        if any(
            token in texto for token in ("nacimiento", "parto múltiple")
        ) or ("adop" in texto and "internacional" not in texto):
            if entrada.nacimientos_adopciones_o_acogimientos > 0:
                ensure_id(ded_id)
            continue

        if "adopción internacional" in texto or "adopcion internacional" in texto:
            if entrada.adopciones_internacionales > 0:
                ensure_id(ded_id)
            continue

        if "cuidado de ascendientes" in texto or "cuidado-ascendientes" in ded_id:
            if any(
                asc.edad >= 65 or asc.discapacidad_porcentaje >= 33
                for asc in entrada.ascendientes
            ):
                ensure_id(ded_id)
            continue

        if "acogimiento familiar" in texto and "no remunerado" not in texto:
            if entrada.acogimientos_menores > 0:
                ensure_id(ded_id)
            continue

        if "acogimiento no remunerado" in texto:
            if entrada.acogimientos_mayores_o_discapacitados > 0:
                ensure_id(ded_id)
            continue

        if (
            "cambio de residencia" in texto
            and "riesgo de despoblación" in texto
        ):
            if entrada.cambios_residencia_municipio_despoblacion > 0:
                ensure_id(ded_id)
            continue

        if "familia numerosa" in texto:
            if entrada.familia_numerosa_categoria:
                ensure_id(ded_id)
            elif (
                "monoparental" in texto
                and entrada.situacion_familiar == "conjunta_monoparental"
            ):
                ensure_id(ded_id)
            continue

        if (
            "contribuyentes con discapacidad" in texto
            or ded.get("categoria") == "discapacidad"
        ):
            if entrada.discapacidad_contribuyente > 0:
                ensure_id(ded_id)
            continue

        if "donativ" in texto or "donacion" in texto:
            if entrada.donativos_autonomicos > 0:
                ensure_id(ded_id)
                if "porcentaje" in ded and ded_id not in bases:
                    bases[ded_id] = entrada.donativos_autonomicos
            continue

        if (
            "gastos derivados del arrendamiento de viviendas" in texto
            or "gastos-derivados-arrendamiento" in ded_id
        ):
            if entrada.gastos_arrendamiento_viviendas > 0:
                ensure_id(ded_id)
                if "porcentaje" in ded and ded_id not in bases:
                    bases[ded_id] = entrada.gastos_arrendamiento_viviendas
            continue

        if "arrendamiento de viviendas vacías" in texto or "arrendamiento-viviendas-vacias" in ded_id:
            if entrada.viviendas_vacias_arrendadas > 0:
                ensure_id(ded_id)
            continue

        if "alquiler" in texto or "arrendamiento" in texto:
            if entrada.alquiler_vivienda_habitual > 0:
                ensure_id(ded_id)
                if "porcentaje" in ded and ded_id not in bases:
                    bases[ded_id] = entrada.alquiler_vivienda_habitual
            continue

        if (
            "pago intereses de préstamos" in texto
            or "pago de intereses de préstamos" in texto
            or "pago intereses de prestamos" in texto
            or "pago de intereses de prestamos" in texto
        ):
            if entrada.intereses_prestamo_adquisicion_vivienda_joven > 0:
                ensure_id(ded_id)
                if "porcentaje" in ded and ded_id not in bases:
                    bases[ded_id] = entrada.intereses_prestamo_adquisicion_vivienda_joven
            continue

        if "incremento de los costes de la financiación ajena" in texto or "incremento-costes-financiacion" in ded_id:
            if entrada.exceso_intereses_financiacion_vivienda > 0:
                ensure_id(ded_id)
                if "porcentaje" in ded and ded_id not in bases:
                    bases[ded_id] = entrada.exceso_intereses_financiacion_vivienda
            continue

        if (
            "adquisición de vivienda habitual por nacimiento o adopción" in texto
            or "adquisicion-vivienda-habitual-nacimiento" in ded_id
        ):
            if (
                entrada.inversion_vivienda_habitual_nacimiento_adopcion > 0
                and entrada.nacimientos_adopciones_o_acogimientos > 0
            ):
                ensure_id(ded_id)
                if "porcentaje" in ded and ded_id not in bases:
                    bases[ded_id] = (
                        entrada.inversion_vivienda_habitual_nacimiento_adopcion
                    )
            continue

        if (
            "adquisición de vivienda habitual en municipios en riesgo de despoblación"
            in texto
            or "adquisicion-vivienda-habitual-municipios-riesgo-despoblacion" in ded_id
        ):
            if entrada.inversion_vivienda_habitual_municipio_despoblacion > 0:
                ensure_id(ded_id)
                if "porcentaje" in ded and ded_id not in bases:
                    bases[ded_id] = (
                        entrada.inversion_vivienda_habitual_municipio_despoblacion
                    )
            continue

        if (
            "guarder" in texto
            or "cuidado-descendientes" in texto
            or "cuidado de hijos menores" in texto
            or "empleados de hogar" in texto
        ):
            base_cuidado = max(
                entrada.gastos_guarderia,
                entrada.cotizaciones_empleados_hogar,
            )
            if base_cuidado > 0:
                ensure_id(ded_id)
                if "porcentaje" in ded and ded_id not in bases:
                    bases[ded_id] = base_cuidado
            continue

        if (
            "adquisición" in texto
            or "inversión en vivienda" in texto
            or "rehabilitación" in texto
            or "obras" in texto
            or "adecuación de vivienda" in texto
        ) and "vivienda" in texto and not any(
            token in texto
            for token in (
                "nacimiento o adopción",
                "riesgo de despoblación",
                "incremento de los costes de la financiación ajena",
                "pago intereses de préstamos",
                "pago intereses de prestamos",
            )
        ):
            if entrada.inversion_vivienda_habitual > 0:
                ensure_id(ded_id)
                if "porcentaje" in ded and ded_id not in bases:
                    bases[ded_id] = entrada.inversion_vivienda_habitual
            continue

        if "cuota" in texto and "sindical" in texto:
            if entrada.cuotas_sindicales > 0:
                ensure_id(ded_id)
                if "porcentaje" in ded and ded_id not in bases:
                    bases[ded_id] = entrada.cuotas_sindicales
            continue

        if "gastos educativos" in texto and (
            entrada.gastos_escolaridad > 0
            or entrada.gastos_idiomas > 0
            or entrada.gastos_uniformes > 0
        ):
            ensure_id(ded_id)
            if ded_id not in componentes:
                componentes[ded_id] = {
                    "escolaridad": entrada.gastos_escolaridad,
                    "idiomas": entrada.gastos_idiomas,
                    "uniformes": entrada.gastos_uniformes,
                }
            continue

        if (
            "material escolar" in texto
            or "libros de texto" in texto
            or "gastos escolares" in texto
            or "gastos educativos de descendientes" in texto
        ):
            base_educacion = max(
                entrada.gastos_material_escolar,
                entrada.gastos_educativos_descendientes,
            )
            if base_educacion > 0:
                ensure_id(ded_id)
                if "porcentaje" in ded and ded_id not in bases:
                    bases[ded_id] = base_educacion
            continue

        if "gastos de estudios" in texto or "estudios de descendientes" in texto:
            if entrada.gastos_estudios_descendientes > 0:
                ensure_id(ded_id)
                if "porcentaje" in ded and ded_id not in bases:
                    bases[ded_id] = entrada.gastos_estudios_descendientes

    return ids, bases, componentes


def _cumple_requisitos_deduccion_autonomica(
    deduccion: dict,
    entrada: InputIRPF,
    base_liquidable_general: Decimal,
    base_liquidable_ahorro: Decimal,
) -> bool:
    requisitos = deduccion.get("requisitos") or {}
    if not requisitos:
        return True

    edad_maxima = requisitos.get("edad_maxima")
    if edad_maxima is not None and entrada.edad_contribuyente > int(edad_maxima):
        return False
    edad_maxima_exclusiva = requisitos.get("edad_maxima_exclusiva")
    if (
        edad_maxima_exclusiva is not None
        and entrada.edad_contribuyente >= int(edad_maxima_exclusiva)
    ):
        return False

    grado_minimo = requisitos.get("grado_minimo")
    if grado_minimo is not None and entrada.discapacidad_contribuyente < int(
        grado_minimo
    ):
        return False

    renta_total = base_liquidable_general + base_liquidable_ahorro
    renta_max_individual = requisitos.get("renta_maxima_individual")
    if (
        renta_max_individual is not None
        and entrada.situacion_familiar == "individual"
        and renta_total > Decimal(str(renta_max_individual))
    ):
        return False

    renta_max_conjunta = requisitos.get("renta_maxima_conjunta")
    if (
        renta_max_conjunta is not None
        and entrada.situacion_familiar != "individual"
        and renta_total > Decimal(str(renta_max_conjunta))
    ):
        return False

    renta_por_miembro = requisitos.get("renta_maxima_por_miembro_unidad_familiar")
    if renta_por_miembro is not None:
        miembros = Decimal(1 + len(entrada.hijos))
        if entrada.situacion_familiar == "conjunta_biparental":
            miembros += Decimal(1)
        limite = Decimal(str(renta_por_miembro)) * miembros
        if renta_total > limite:
            return False

    return True


def aplicar_deducciones_autonomicas(
    cuota_integra_autonomica: Decimal,
    base_liquidable_general: Decimal,
    base_liquidable_ahorro: Decimal,
    entrada: InputIRPF,
    datos_territorio: dict,
) -> tuple[Decimal, list[PasoCalculo]]:
    """Aplica deducciones autonómicas o forales declaradas en el YAML del territorio.

    El cálculo se activa únicamente para los IDs reclamados por el llamante o
    para aquellos con bases/componentes explícitamente informados.
    """
    catalogo = datos_territorio.get("deducciones") or []
    if not catalogo:
        return Decimal(0), []

    (
        ids_reclamados,
        bases_deducciones,
        componentes_deducciones,
    ) = derivar_deducciones_autonomicas(entrada, catalogo)

    if not ids_reclamados:
        return Decimal(0), []

    por_id = {d["id"]: d for d in catalogo}
    detalle: list[PasoCalculo] = []
    total = Decimal(0)

    for ded_id in ids_reclamados:
        ded = por_id.get(ded_id)
        if ded is None:
            raise EntradaInvalida(
                f"Deducción autonómica desconocida para {entrada.territorio}: {ded_id}"
            )
        if not _cumple_requisitos_deduccion_autonomica(
            ded, entrada, base_liquidable_general, base_liquidable_ahorro
        ):
            continue

        importe = Decimal(0)
        detalle_linea = ""
        titulo = ded["titulo"]

        if "porcentaje_cuota" in ded:
            porcentaje = Decimal(str(ded["porcentaje_cuota"]))
            importe = cuota_integra_autonomica * porcentaje
            if entrada.familia_numerosa_categoria == "especial" and ded.get(
                "limite_especial"
            ) is not None:
                importe = min(importe, Decimal(str(ded["limite_especial"])))
            elif ded.get("limite_general") is not None:
                importe = min(importe, Decimal(str(ded["limite_general"])))
            detalle_linea = f"{porcentaje * 100:.2f}% sobre cuota autonómica"
        elif any(
            key in ded
            for key in (
                "porcentaje_escolaridad",
                "porcentaje_idiomas",
                "porcentaje_uniformes",
            )
        ):
            componentes = componentes_deducciones.get(ded_id) or {}
            subtotal = Decimal(0)
            partes: list[str] = []
            for componente in ("escolaridad", "idiomas", "uniformes"):
                pct_key = f"porcentaje_{componente}"
                if pct_key not in ded:
                    continue
                base = Decimal(str(componentes.get(componente, 0)))
                porcentaje = Decimal(str(ded[pct_key]))
                subtotal += base * porcentaje
                if base > 0:
                    partes.append(f"{componente} {base} € x {porcentaje * 100:.2f}%")
            if ded.get("limite_por_hijo") is not None:
                hijos_relevantes = _count_hijos_relevantes(ded, entrada)
                limite = Decimal(str(ded["limite_por_hijo"])) * Decimal(
                    hijos_relevantes
                )
                subtotal = min(subtotal, limite)
            importe = subtotal
            detalle_linea = " + ".join(partes)
        elif "importe_fijo" in ded:
            importe = Decimal(str(ded["importe_fijo"]))
            unidades = _count_unidades_deduccion(ded, entrada)
            if ded.get("por_unidad") is not None:
                importe *= Decimal(unidades)
                detalle_linea = f"{ded['importe_fijo']} € x {unidades}"
        elif "importes_por_orden" in ded:
            unidades = _count_unidades_deduccion(ded, entrada)
            importes = [Decimal(str(valor)) for valor in ded["importes_por_orden"]]
            subtotal = Decimal(0)
            for idx in range(unidades):
                subtotal += importes[min(idx, len(importes) - 1)]
            importe = subtotal
            detalle_linea = f"{unidades} unidades según orden"
        elif "porcentaje" in ded:
            if ded_id not in bases_deducciones:
                raise EntradaInvalida(
                    f"Falta base para la deducción autonómica {ded_id}"
                )
            base = bases_deducciones[ded_id]
            base_aplicable = base
            if ded.get("base_maxima") is not None:
                base_aplicable = min(base_aplicable, Decimal(str(ded["base_maxima"])))
            if ded.get("limite_base_liquidable") is not None:
                limite_base = (
                    base_liquidable_general + base_liquidable_ahorro
                ) * Decimal(str(ded["limite_base_liquidable"]))
                base_aplicable = min(base_aplicable, limite_base)
            porcentaje = Decimal(str(ded["porcentaje"]))
            limite = (
                Decimal(str(ded["limite"])) if ded.get("limite") is not None else None
            )
            if (
                entrada.familia_numerosa_categoria
                and ded.get("porcentaje_familia_numerosa") is not None
            ):
                porcentaje = Decimal(str(ded["porcentaje_familia_numerosa"]))
                if ded.get("limite_familia_numerosa") is not None:
                    limite = Decimal(str(ded["limite_familia_numerosa"]))
            importe = base_aplicable * porcentaje
            if limite is not None:
                importe = min(importe, limite)
            if ded.get("limite_por_hijo") is not None:
                hijos_relevantes = _count_hijos_relevantes(ded, entrada)
                limite = Decimal(str(ded["limite_por_hijo"])) * Decimal(
                    hijos_relevantes
                )
                importe = min(importe, limite)
            detalle_linea = f"Base {base_aplicable} € x {porcentaje * 100:.2f}%"

        if importe <= 0:
            continue

        total += importe
        detalle.append(
            PasoCalculo(
                concepto=f"Deducción autonómica {titulo}",
                importe=importe,
                detalle=f"id={ded_id}" + (f" · {detalle_linea}" if detalle_linea else ""),
            )
        )

    if total > cuota_integra_autonomica and cuota_integra_autonomica >= 0:
        total = max(cuota_integra_autonomica, Decimal(0))
        detalle.append(
            PasoCalculo(
                concepto="Limitación por cuota íntegra autonómica",
                importe=Decimal(0),
            )
        )
    return total, detalle


def calcular_irpf(
    entrada: InputIRPF,
    datos_estatal: dict,
    datos_territorio: dict,
) -> ResultadoIRPF:
    """Calcula la liquidación completa del IRPF para una entrada dada.

    ``datos_estatal`` y ``datos_territorio`` son los dicts ya cargados y
    validados por :func:`helpers.data_loader.load_estatal` /
    :func:`helpers.data_loader.load_territorio`.
    """
    validar_entrada_irpf(entrada)
    desglose: list[PasoCalculo] = []

    reduc_trabajo = calcular_reduccion_trabajo(
        entrada.rendimiento_neto_trabajo,
        datos_estatal["reduccion_rendimientos_trabajo"],
    )
    rn_trabajo_reducido = max(
        entrada.rendimiento_neto_trabajo - reduc_trabajo, Decimal(0)
    )
    desglose.append(
        PasoCalculo(
            concepto="Reducción rendimientos del trabajo (art. 20 LIRPF)",
            importe=reduc_trabajo,
        )
    )

    base_imponible_general = (
        rn_trabajo_reducido
        + entrada.rendimiento_neto_capital_inmobiliario
        + entrada.rendimiento_neto_actividades
    )
    base_imponible_ahorro = (
        entrada.rendimiento_neto_capital_mobiliario
        + entrada.ganancias_patrimoniales_ahorro
    )

    reduc_conjunta = Decimal(0)
    if entrada.situacion_familiar == "conjunta_biparental":
        reduc_conjunta = Decimal(
            str(datos_estatal.get("reduccion_conjunta_biparental", 3400))
        )
    elif entrada.situacion_familiar == "conjunta_monoparental":
        reduc_conjunta = Decimal(
            str(datos_estatal.get("reduccion_conjunta_monoparental", 2150))
        )

    tope_pp = Decimal(str(datos_estatal.get("planes_pensiones_tope", 1500)))
    reduc_pp = min(entrada.aportaciones_planes_pensiones, tope_pp)

    base_liquidable_general = max(
        base_imponible_general - reduc_conjunta - reduc_pp, Decimal(0)
    )
    base_liquidable_ahorro = base_imponible_ahorro

    regimen: RegimenTipo = datos_territorio["territorio"]["regimen"]

    minimos = dict(datos_estatal["minimos"])
    overrides = datos_territorio.get("minimos") or {}
    for k, v in overrides.items():
        if v is not None:
            minimos[k] = v
    minimo = calcular_minimo_personal_familiar(entrada, minimos)

    escala_estatal = Escala.desde_lista(datos_estatal["escala_general"])
    escala_ahorro = Escala.desde_lista(datos_estatal["escala_ahorro"])
    escala_territorio = Escala.desde_lista(
        datos_territorio.get("escala_general")
        or datos_territorio.get("escala_autonomica")
    )

    if regimen == "comun":
        cuota_est_bg = aplicar_escala(
            base_liquidable_general, escala_estatal
        ) - aplicar_escala(min(base_liquidable_general, minimo), escala_estatal)
        cuota_ccaa_bg = aplicar_escala(
            base_liquidable_general, escala_territorio
        ) - aplicar_escala(min(base_liquidable_general, minimo), escala_territorio)

        minimo_remanente = max(minimo - base_liquidable_general, Decimal(0))
        cuota_est_ba = aplicar_escala(
            base_liquidable_ahorro, escala_ahorro
        ) - aplicar_escala(min(base_liquidable_ahorro, minimo_remanente), escala_ahorro)
        escala_ahorro_auton = Escala.desde_lista(
            datos_estatal.get(
                "escala_ahorro_autonomica", datos_estatal["escala_ahorro"]
            )
        )
        cuota_ccaa_ba = aplicar_escala(
            base_liquidable_ahorro, escala_ahorro_auton
        ) - aplicar_escala(
            min(base_liquidable_ahorro, minimo_remanente), escala_ahorro_auton
        )

        cuota_integra_estatal = cuota_est_bg + cuota_est_ba
        cuota_integra_autonomica = cuota_ccaa_bg + cuota_ccaa_ba
    else:
        cuota_foral_bg = aplicar_escala(
            base_liquidable_general, escala_territorio
        ) - aplicar_escala(min(base_liquidable_general, minimo), escala_territorio)
        escala_ahorro_foral = Escala.desde_lista(
            datos_territorio.get("escala_ahorro") or datos_estatal["escala_ahorro"]
        )
        cuota_foral_ba = aplicar_escala(base_liquidable_ahorro, escala_ahorro_foral)
        cuota_integra_estatal = Decimal(0)
        cuota_integra_autonomica = cuota_foral_bg + cuota_foral_ba

    cuota_integra_total = cuota_integra_estatal + cuota_integra_autonomica

    # Fase 7 — deducciones estatales y autonómicas en cuota
    deducciones_estatales_total, deducciones_detalle = aplicar_deducciones_estatales(
        cuota_integra_estatal, base_liquidable_general, entrada, datos_estatal
    )
    deducciones_autonomicas_total, deducciones_autonomicas_detalle = (
        aplicar_deducciones_autonomicas(
            cuota_integra_autonomica,
            base_liquidable_general,
            base_liquidable_ahorro,
            entrada,
            datos_territorio,
        )
    )
    cuota_liquida = max(
        cuota_integra_total
        - deducciones_estatales_total
        - deducciones_autonomicas_total,
        Decimal(0),
    )

    # Fase 7 — maternidad reembolsable (art. 81 LIRPF): impuesto negativo
    maternidad_reembolsable = calcular_maternidad_reembolsable(entrada, datos_estatal)
    devolucion_maternidad = maternidad_reembolsable

    cuota_diferencial = (
        cuota_liquida - entrada.retenciones_practicadas - devolucion_maternidad
    )

    desglose.append(
        PasoCalculo(concepto="Base imponible general", importe=base_imponible_general)
    )
    desglose.append(
        PasoCalculo(concepto="Base imponible del ahorro", importe=base_imponible_ahorro)
    )
    desglose.append(
        PasoCalculo(concepto="Base liquidable general", importe=base_liquidable_general)
    )
    desglose.append(PasoCalculo(concepto="Mínimo personal y familiar", importe=minimo))
    desglose.append(
        PasoCalculo(concepto="Cuota íntegra estatal", importe=cuota_integra_estatal)
    )
    desglose.append(
        PasoCalculo(
            concepto="Cuota íntegra autonómica",
            importe=cuota_integra_autonomica,
        )
    )
    desglose.append(PasoCalculo(concepto="Cuota líquida", importe=cuota_liquida))
    desglose.append(
        PasoCalculo(
            concepto="Retenciones practicadas", importe=entrada.retenciones_practicadas
        )
    )
    desglose.append(
        PasoCalculo(concepto="Cuota diferencial", importe=cuota_diferencial)
    )

    return ResultadoIRPF(
        base_imponible_general=redondear(base_imponible_general),
        base_imponible_ahorro=redondear(base_imponible_ahorro),
        reduccion_rendimientos_trabajo=redondear(reduc_trabajo),
        reduccion_tributacion_conjunta=redondear(reduc_conjunta),
        reduccion_planes_pensiones=redondear(reduc_pp),
        base_liquidable_general=redondear(base_liquidable_general),
        base_liquidable_ahorro=redondear(base_liquidable_ahorro),
        minimo_personal_familiar=redondear(minimo),
        cuota_integra_estatal=redondear(cuota_integra_estatal),
        cuota_integra_autonomica=redondear(cuota_integra_autonomica),
        cuota_integra_total=redondear(cuota_integra_total),
        cuota_liquida=redondear(cuota_liquida),
        cuota_diferencial=redondear(cuota_diferencial),
        retenciones=redondear(entrada.retenciones_practicadas),
        regimen=regimen,
        deducciones_estatales_total=redondear(deducciones_estatales_total),
        deducciones_estatales_detalle=[
            PasoCalculo(
                concepto=p.concepto, importe=redondear(p.importe), detalle=p.detalle
            )
            for p in deducciones_detalle
        ],
        deducciones_autonomicas_total=redondear(deducciones_autonomicas_total),
        deducciones_autonomicas_detalle=[
            PasoCalculo(
                concepto=p.concepto, importe=redondear(p.importe), detalle=p.detalle
            )
            for p in deducciones_autonomicas_detalle
        ],
        maternidad_reembolsable=redondear(maternidad_reembolsable),
        devolucion_maternidad=redondear(devolucion_maternidad),
        desglose=[
            PasoCalculo(
                concepto=p.concepto, importe=redondear(p.importe), detalle=p.detalle
            )
            for p in desglose
        ],
    )
