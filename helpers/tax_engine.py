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
            datos_territorio.get("escala_ahorro", datos_estatal["escala_ahorro"])
        )
        cuota_foral_ba = aplicar_escala(base_liquidable_ahorro, escala_ahorro_foral)
        cuota_integra_estatal = Decimal(0)
        cuota_integra_autonomica = cuota_foral_bg + cuota_foral_ba

    cuota_integra_total = cuota_integra_estatal + cuota_integra_autonomica
    cuota_liquida = max(cuota_integra_total, Decimal(0))
    cuota_diferencial = cuota_liquida - entrada.retenciones_practicadas

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
        desglose=[
            PasoCalculo(
                concepto=p.concepto, importe=redondear(p.importe), detalle=p.detalle
            )
            for p in desglose
        ],
    )
