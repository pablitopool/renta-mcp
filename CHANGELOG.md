# Changelog

Todas las entradas notables de este proyecto se documentan aquí.

## [0.1.0] - 2026-04-13

Lanzamiento inicial. MCP server funcional para IRPF español.

### Motor de cálculo (`helpers/tax_engine.py`)

- Escalas progresivas marginales con Decimal; nunca float.
- Aplicación correcta del mínimo personal y familiar como "tipo 0" (no resta de la base).
- Régimen común (estatal + autonómico) y régimen foral (escala única) bifurcados.
- Reducción por rendimientos del trabajo (art. 20 LIRPF), tributación conjunta, aportaciones a planes de pensiones.
- Deducciones estatales en cuota: donativos Ley 49/2002, vivienda habitual régimen transitorio, familia numerosa, obras eficiencia energética.
- Deducción por maternidad (art. 81) como impuesto negativo reembolsable.

### Datos fiscales

- 15 CCAA régimen común + 4 forales, ejercicios 2024 y 2025.
- Cada CCAA con ≥3 deducciones autonómicas con importes/porcentajes y artículo normativo trazable.
- 149 casillas del Modelo 100 (subset curado + parseadas del manual PDF AEAT).
- Umbrales art. 96 LIRPF, plazos campaña, mínimos personales por edad/discapacidad.
- Referencias BOE consolidadas en cada YAML (trazabilidad legal).

### Primitivas MCP

- **11 tools**: calcular_irpf, calcular_retencion_nomina, consultar_tramos, consultar_minimos, listar_deducciones_autonomicas, buscar_deduccion (rapidfuzz), listar_casillas_modelo_100, buscar_casilla, consultar_plazos_campana, comprobar_obligacion_declarar, validar_minimo_declarante.
- **6 resources**: tramos, minimos, deducciones, casillas, plazos, obligacion.
- **3 prompts**: revisar_borrador, optimizar_deducciones, simular_declaracion.

### Infraestructura

- Python 3.10+, FastMCP, Streamable HTTP stateless.
- Docker + docker-compose.
- CI GitHub Actions (ruff + pytest + verificación checksums).
- Pre-commit hooks (Ruff, YAML).
- 237 tests (231 unit + 6 reference contra Renta WEB Open).
- Property-based testing con hypothesis.

### Ingesta de datos oficiales

- `scripts/descargar_datos_aeat.py`: descarga ordenada de manuales AEAT, XSD, órdenes HAC, deducciones autonómicas (22 documentos, ~15 MB) con SHA-256.
- `scripts/extraer_casillas_manual.py`: parseo del manual PDF Parte 1 con pypdf y regex.
- `scripts/parsear_deducciones_aeat.py`: seeds YAML desde HTML guía AEAT.
- `scripts/verificar_checksums.py`: verificación en CI.

### Evaluaciones

- 10 preguntas verificables en `evaluations/renta_mcp_eval.xml` formato skill mcp-builder.

### Documentación

- README con ejemplos de prompts, integración Claude Desktop/Cursor, deploy público (Cloudflare, Fly.io).
- DISCLAIMER.md legal obligatorio.
- Este CHANGELOG.
