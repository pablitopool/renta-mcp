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
    maternidad_reembolsable: Decimal = Decimal(0)
    devolucion_maternidad: Decimal = Decimal(0)


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

    # Fase 7 — deducciones estatales en cuota (art. 68 ss. LIRPF)
    deducciones_estatales_total, deducciones_detalle = aplicar_deducciones_estatales(
        cuota_integra_estatal, base_liquidable_general, entrada, datos_estatal
    )
    cuota_liquida = max(cuota_integra_total - deducciones_estatales_total, Decimal(0))

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
        maternidad_reembolsable=redondear(maternidad_reembolsable),
        devolucion_maternidad=redondear(devolucion_maternidad),
        desglose=[
            PasoCalculo(
                concepto=p.concepto, importe=redondear(p.importe), detalle=p.detalle
            )
            for p in desglose
        ],
    )
