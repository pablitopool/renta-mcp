"""Tool MCP: ``comprobar_obligacion_declarar`` (art. 96 LIRPF)."""

from mcp.server.fastmcp import FastMCP

from helpers.env_config import get_data_dir
from helpers.logging import log_tool
from helpers.tax_engine import DatosFiscalesNoDisponibles
from tools.error_handling import raise_datos_no_disponibles, raise_unexpected


def _cargar_obligacion(año: int) -> dict:
    import yaml

    path = get_data_dir() / str(año) / "obligacion.yaml"
    if not path.exists():
        raise DatosFiscalesNoDisponibles(f"No existe {path}")
    with path.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


async def comprobar_obligacion_declarar_impl(
    año: int,
    rendimientos_trabajo_brutos: float = 0.0,
    numero_pagadores: int = 1,
    rendimientos_segundo_pagador: float = 0.0,
    rendimientos_capital_y_ganancias_con_retencion: float = 0.0,
    rentas_inmobiliarias_imputadas: float = 0.0,
    actividades_economicas: float = 0.0,
) -> str:
    umbrales = _cargar_obligacion(año)
    razones: list[str] = []

    if actividades_economicas > 0 and umbrales["actividades_economicas_y_otras"].get(
        "siempre_obliga_declarar"
    ):
        razones.append(
            "Cualquier rendimiento de actividades económicas obliga a declarar"
        )

    trabajo = umbrales["rendimientos_trabajo"]
    sin_efecto = trabajo["umbral_segundo_pagador_sin_efecto"]
    if numero_pagadores > 1 and rendimientos_segundo_pagador > sin_efecto:
        limite = trabajo["umbral_varios_pagadores_principal"]
    else:
        limite = trabajo["umbral_un_pagador"]
    if rendimientos_trabajo_brutos > limite:
        razones.append(
            f"Rendimientos del trabajo ({rendimientos_trabajo_brutos} €) "
            f"superan el umbral aplicable de {limite} €"
        )

    cap_limite = umbrales["rendimientos_capital_y_ganancias_con_retencion"][
        "umbral_total"
    ]
    if rendimientos_capital_y_ganancias_con_retencion > cap_limite:
        razones.append(
            f"Rendimientos capital/ganancias con retención "
            f"({rendimientos_capital_y_ganancias_con_retencion} €) "
            f"superan {cap_limite} €"
        )

    inmuebles_limite = umbrales["rentas_inmobiliarias_y_similares"]["umbral_total"]
    if rentas_inmobiliarias_imputadas > inmuebles_limite:
        razones.append(
            f"Rentas inmobiliarias imputadas ({rentas_inmobiliarias_imputadas} €) "
            f"superan {inmuebles_limite} €"
        )

    obligado = bool(razones)
    titulo = "OBLIGADO a declarar" if obligado else "NO obligado a declarar"
    salida = [f"## {titulo} — ejercicio {año}", ""]
    if razones:
        for r in razones:
            salida.append(f"- {r}")
    else:
        salida.append("Ninguno de los umbrales del art. 96 LIRPF se supera.")
    salida.append(f"\n_Fuente: {umbrales['fuente_legal']}_")
    salida.append(
        "\n_Nota: aunque no se esté obligado, puede interesar declarar para "
        "obtener devolución de retenciones o aplicar deducciones (maternidad, "
        "familia numerosa, inversión vivienda régimen transitorio)._"
    )
    return "\n".join(salida)


def register_comprobar_obligacion_declarar_tool(mcp: FastMCP) -> None:
    @mcp.tool()
    @log_tool
    async def comprobar_obligacion_declarar(
        año: int,
        rendimientos_trabajo_brutos: float = 0.0,
        numero_pagadores: int = 1,
        rendimientos_segundo_pagador: float = 0.0,
        rendimientos_capital_y_ganancias_con_retencion: float = 0.0,
        rentas_inmobiliarias_imputadas: float = 0.0,
        actividades_economicas: float = 0.0,
    ) -> str:
        """Determina si el contribuyente está obligado a declarar (art. 96 LIRPF)."""
        try:
            return await comprobar_obligacion_declarar_impl(
                año=año,
                rendimientos_trabajo_brutos=rendimientos_trabajo_brutos,
                numero_pagadores=numero_pagadores,
                rendimientos_segundo_pagador=rendimientos_segundo_pagador,
                rendimientos_capital_y_ganancias_con_retencion=rendimientos_capital_y_ganancias_con_retencion,
                rentas_inmobiliarias_imputadas=rentas_inmobiliarias_imputadas,
                actividades_economicas=actividades_economicas,
            )
        except DatosFiscalesNoDisponibles as exc:
            raise_datos_no_disponibles(exc)
        except Exception as exc:  # noqa: BLE001
            raise_unexpected(exc)
