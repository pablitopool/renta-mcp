"""Contratos de superficie pública entre motor, tools y documentación."""

from dataclasses import fields
from inspect import signature
from pathlib import Path

from helpers.tax_engine import InputIRPF
from tools.calcular_irpf import calcular_irpf_impl
from tools.calcular_retencion_nomina import calcular_retencion_nomina_impl

README = Path("README.md").read_text(encoding="utf-8")
ESTATAL_2024 = Path("data/2024/estatal.yaml").read_text(encoding="utf-8")
ESTATAL_2025 = Path("data/2025/estatal.yaml").read_text(encoding="utf-8")


def test_calcular_irpf_expone_todos_los_hechos_del_motor():
    alias = {
        "hijos": "hijos_edades",
        "ascendientes": "ascendientes_edades",
    }
    firma = set(signature(calcular_irpf_impl).parameters)
    for field in fields(InputIRPF):
        publico = alias.get(field.name, field.name)
        assert publico in firma, f"Falta exponer `{field.name}` como `{publico}`"


def test_readme_documenta_nuevas_tools_gaps_funcionales():
    assert "calcular_rendimiento_actividad" in README
    assert "preparar_payload_irpf" in README
    assert "calcular_ganancia_cripto_fifo" in README
    assert "validar_municipio_despoblacion" in README


def test_calcular_retencion_nomina_expone_ascendientes():
    firma = signature(calcular_retencion_nomina_impl)
    assert "ascendientes_edades" in firma.parameters


def test_readme_alinea_retencion_procedimental_y_modo_experto():
    assert "Estimación procedimental de la retención IRPF en nómina" in README
    assert "casos avanzados o flujos guiados" in README


def test_readme_y_tools_no_arrastran_marcas_de_parcialidad():
    assert "subset v0.1" not in README
    assert "subset curado v0.1" not in README
    assert "pendiente confirmación" not in README


def test_estatal_no_arrastra_mensajes_de_pendiente_confirmacion():
    assert "pendiente confirmación" not in ESTATAL_2024
    assert "pendiente confirmación" not in ESTATAL_2025
