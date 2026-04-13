"""Tests de Resources MCP (URI templates)."""

from __future__ import annotations

import json

import pytest
from mcp.server.fastmcp import FastMCP

from resources import register_resources


@pytest.fixture
def mcp_con_resources():
    mcp = FastMCP("renta-mcp-test")
    register_resources(mcp)
    return mcp


@pytest.mark.asyncio
async def test_resource_tramos_estatal(mcp_con_resources):
    contenido_iter = await mcp_con_resources.read_resource("irpf://tramos/2025/estatal")
    contenido = list(contenido_iter)
    assert contenido, "El resource estatal no devolvió contenido"
    payload = json.loads(contenido[0].content)
    assert payload["año"] == 2025
    assert len(payload["escala_general"]) >= 5


@pytest.mark.asyncio
async def test_resource_tramos_madrid(mcp_con_resources):
    contenido_iter = await mcp_con_resources.read_resource("irpf://tramos/2025/madrid")
    contenido = list(contenido_iter)
    assert contenido
    payload = json.loads(contenido[0].content)
    assert payload["territorio"]["slug"] == "madrid"


@pytest.mark.asyncio
async def test_resource_tramos_ahorro(mcp_con_resources):
    contenido_iter = await mcp_con_resources.read_resource("irpf://tramos-ahorro/2025")
    contenido = list(contenido_iter)
    assert contenido
    payload = json.loads(contenido[0].content)
    assert "escala_ahorro" in payload


@pytest.mark.asyncio
async def test_resource_municipios_despoblacion_madrid(mcp_con_resources):
    contenido_iter = await mcp_con_resources.read_resource(
        "irpf://municipios-despoblacion/2025/madrid"
    )
    contenido = list(contenido_iter)
    assert contenido
    payload = json.loads(contenido[0].content)
    assert payload["territorio"] == "madrid"
    assert "municipios" in payload
