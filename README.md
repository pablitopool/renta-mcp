# renta-mcp

Servidor **MCP (Model Context Protocol)** no oficial para el **IRPF español** (Modelo 100 AEAT).

Permite a clientes LLM compatibles con MCP (Claude Desktop, Cursor, Claude Code, ChatGPT, etc.) calcular la cuota del IRPF, consultar tramos autonómicos, buscar deducciones y interpretar casillas del Modelo 100 de forma estructurada — sin depender de la API SOAP de la AEAT.

> ⚠️ **Herramienta informativa no vinculante.** Véase [`DISCLAIMER.md`](./DISCLAIMER.md).

## Estado

Versión `0.1.0` — **en construcción**. Scaffold completado; el motor de cálculo y los datos fiscales se implementan por fases (véase el plan interno en `/Users/.../plans/greedy-soaring-engelbart.md`).

## Cobertura prevista (v0.1)

- **Ejercicios fiscales**: 2024 y 2025
- **Territorios**: 15 CCAA de régimen común + 4 forales (Álava, Bizkaia, Gipuzkoa, Navarra)
- **Primitivas MCP**: 11 Tools + 8 Resources (URI templates)

## Arquitectura

```
renta-mcp/
├── main.py              # ASGI entrypoint (Streamable HTTP /mcp + /health)
├── helpers/             # Motor de cálculo, data loader, formateo, logging
├── data/
│   ├── fuentes.yaml     # Catálogo de URLs oficiales (BOE, AEAT)
│   ├── checksums.json   # SHA-256 de los documentos descargados
│   ├── raw/             # GITIGNORED: PDFs, XSD, HTML descargados
│   ├── 2024/, 2025/     # YAML curados (tramos, mínimos, deducciones, casillas)
├── scripts/             # descargar_datos_aeat, parsear_xsd_modelo_100, ...
├── tools/               # MCP tools (calcular_irpf, consultar_tramos, ...)
├── resources/           # MCP resources (irpf://tramos/{año}/{territorio}, ...)
└── tests/
```

## Ejecución local

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
cp .env.example .env
python main.py
```

El servidor queda en `http://127.0.0.1:8000/mcp` y expone `GET /health`.

### Descarga de documentación oficial (Fase 0.5)

```bash
python -m scripts.descargar_datos_aeat --año 2025
python -m scripts.verificar_checksums
```

### Docker

```bash
docker compose up -d
curl http://localhost:8000/health
```

## Tests

```bash
pytest                  # unit tests
pytest -m reference     # tests que validan contra calculadoras externas (requiere red)
```

## Linting

```bash
ruff check --fix && ruff format
```

## Licencia

MIT — véase [`LICENSE`](./LICENSE).
