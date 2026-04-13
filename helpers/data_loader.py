"""Carga y validación de los YAML fiscales en ``data/{año}/``.

Usa Pydantic v2 para validar estructura y ``functools.lru_cache`` para
evitar leer YAML más de una vez por (año, territorio).
"""

from __future__ import annotations

from decimal import Decimal
from functools import lru_cache
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator

from helpers.env_config import get_data_dir
from helpers.tax_engine import DatosFiscalesNoDisponibles


class TramoSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")
    desde: Decimal
    hasta: Decimal | None
    tipo: Decimal = Field(ge=0, le=1)


class ReduccionRendimientosTrabajoSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")
    umbral_maximo_base: Decimal
    umbral_maximo: Decimal
    importe_maximo: Decimal
    pendiente: Decimal


class EstatalSchema(BaseModel):
    model_config = ConfigDict(extra="allow")
    año: int
    fuente_boe: str
    escala_general: list[TramoSchema]
    escala_ahorro: list[TramoSchema]
    escala_ahorro_autonomica: list[TramoSchema] | None = None
    reduccion_rendimientos_trabajo: ReduccionRendimientosTrabajoSchema
    reduccion_conjunta_biparental: Decimal | None = None
    reduccion_conjunta_monoparental: Decimal | None = None
    planes_pensiones_tope: Decimal | None = None
    minimos: dict[str, Any]

    @field_validator("escala_general", "escala_ahorro")
    @classmethod
    def _validar_escala_comienza_en_cero(
        cls, v: list[TramoSchema]
    ) -> list[TramoSchema]:
        if not v:
            raise ValueError("Escala vacía")
        if v[0].desde != 0:
            raise ValueError("La escala debe comenzar en 0")
        return v


class TerritorioMetaSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")
    slug: str
    nombre: str
    regimen: Literal["comun", "foral"]


class TerritorioSchema(BaseModel):
    model_config = ConfigDict(extra="allow")
    territorio: TerritorioMetaSchema
    año: int
    fuente_boe: str | None = None
    revisado_en: str | None = None
    escala_autonomica: list[TramoSchema] | None = None
    escala_general: list[TramoSchema] | None = None
    escala_ahorro: list[TramoSchema] | None = None
    minimos: dict[str, Any] | None = None
    deducciones: list[dict[str, Any]] = Field(default_factory=list)


def _es_yaml_publico_territorial(path: Path) -> bool:
    return path.is_file() and path.suffix == ".yaml" and not path.name.endswith(
        ".seed.yaml"
    )


def _resolver_archivo(año: int, slug: str) -> Path:
    base = get_data_dir() / str(año)
    candidatos = [
        base / "ccaa" / f"{slug}.yaml",
        base / "forales" / f"{slug}.yaml",
    ]
    for c in candidatos:
        if c.exists():
            return c
    raise DatosFiscalesNoDisponibles(
        f"No hay datos para año={año}, territorio={slug}. "
        f"Rutas probadas: {[str(c) for c in candidatos]}"
    )


@lru_cache(maxsize=128)
def load_estatal(año: int) -> dict[str, Any]:
    path = get_data_dir() / str(año) / "estatal.yaml"
    if not path.exists():
        raise DatosFiscalesNoDisponibles(f"No existe {path}")
    with path.open("r", encoding="utf-8") as fh:
        raw = yaml.safe_load(fh)
    validado = EstatalSchema.model_validate(raw)
    return validado.model_dump(mode="python")


@lru_cache(maxsize=128)
def load_territorio(año: int, slug: str) -> dict[str, Any]:
    path = _resolver_archivo(año, slug)
    with path.open("r", encoding="utf-8") as fh:
        raw = yaml.safe_load(fh)
    validado = TerritorioSchema.model_validate(raw)
    datos = validado.model_dump(mode="python")
    fuente_boe = datos.get("fuente_boe")
    revisado_en = datos.get("revisado_en")
    for deduccion in datos.get("deducciones") or []:
        if fuente_boe and not deduccion.get("fuente_boe"):
            deduccion["fuente_boe"] = fuente_boe
        if revisado_en and not deduccion.get("revisado_en"):
            deduccion["revisado_en"] = revisado_en
    return datos


def listar_territorios(año: int) -> list[str]:
    base = get_data_dir() / str(año)
    territorios: list[str] = []
    for sub in ("ccaa", "forales"):
        carpeta = base / sub
        if carpeta.exists():
            territorios.extend(
                sorted(
                    p.stem for p in carpeta.glob("*.yaml") if _es_yaml_publico_territorial(p)
                )
            )
    return territorios
