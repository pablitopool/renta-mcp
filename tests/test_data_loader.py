"""Tests del cargador de datos fiscales."""

from __future__ import annotations

import pytest

from helpers.data_loader import (
    listar_territorios,
    load_estatal,
    load_territorio,
)
from helpers.tax_engine import DatosFiscalesNoDisponibles


def test_load_estatal_2025():
    datos = load_estatal(2025)
    assert datos["año"] == 2025
    assert len(datos["escala_general"]) >= 5
    assert datos["escala_general"][0]["desde"] == 0
    assert "minimos" in datos
    assert datos["minimos"]["personal"] > 0


def test_load_territorio_madrid_2025():
    datos = load_territorio(2025, "madrid")
    assert datos["territorio"]["slug"] == "madrid"
    assert datos["territorio"]["regimen"] == "comun"
    assert datos["año"] == 2025
    assert len(datos["escala_autonomica"]) >= 3


def test_load_territorio_desconocido_lanza_excepcion():
    with pytest.raises(DatosFiscalesNoDisponibles):
        load_territorio(2025, "atlantida")


def test_load_estatal_año_no_disponible_lanza_excepcion():
    with pytest.raises(DatosFiscalesNoDisponibles):
        load_estatal(1999)


def test_listar_territorios_2025_incluye_madrid():
    territorios = listar_territorios(2025)
    assert "madrid" in territorios
