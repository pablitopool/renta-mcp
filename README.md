# renta-mcp

Servidor **MCP (Model Context Protocol)** no oficial para el **IRPF español** (Modelo 100 AEAT).

Permite a clientes LLM compatibles con MCP (Claude Desktop, Cursor, Claude Code, ChatGPT, etc.) calcular la cuota del IRPF, consultar tramos autonómicos, buscar deducciones e interpretar casillas del Modelo 100 de forma estructurada — sin depender de la API SOAP de la AEAT.

> ⚠️ **Herramienta informativa no vinculante.** Véase [`DISCLAIMER.md`](./DISCLAIMER.md).

## Estado

Versión `0.1.0` — **v0.1 funcionalmente completo**. 237 tests pasan (231 unit + 6 reference). Motor aplica deducciones estatales + maternidad reembolsable. 15 CCAA + 4 forales cubiertos para ejercicios 2024 y 2025.

## Cobertura v0.1

- **Ejercicios fiscales**: 2024 y 2025
- **Territorios**: 15 CCAA de régimen común + 4 forales (Álava, Bizkaia, Gipuzkoa, Navarra)
- **Primitivas MCP**: 11 Tools + 6 Resources + 3 Prompts
- **Datos fiscales**: escalas, mínimos personales/familiares, deducciones autonómicas (≥3/CCAA), 149 casillas del Modelo 100, plazos campaña, umbrales obligación declarar

## Tools MCP

| Tool | Descripción |
|---|---|
| `calcular_irpf` | Liquidación IRPF completa con desglose |
| `calcular_retencion_nomina` | Estimación retención IRPF en nómina |
| `consultar_tramos` | Escala estatal/autonómica/foral por año y territorio |
| `consultar_minimos` | Mínimo personal y familiar aplicable |
| `listar_deducciones_autonomicas` | Catálogo deducciones por CCAA y categoría |
| `buscar_deduccion` | Búsqueda fuzzy en catálogo de deducciones |
| `listar_casillas_modelo_100` | Casillas del Modelo 100 por sección |
| `buscar_casilla` | Búsqueda fuzzy de casilla por concepto |
| `consultar_plazos_campana` | Fechas de la Campaña Renta |
| `comprobar_obligacion_declarar` | Test obligación declarar (art. 96 LIRPF) |
| `validar_minimo_declarante` | Verifica art. 20 LIRPF no genere base negativa |

## Resources MCP

- `irpf://tramos/{año}/estatal` — escala general estatal.
- `irpf://tramos/{año}/{territorio}` — escala autonómica o foral.
- `irpf://tramos-ahorro/{año}` — escala base del ahorro.
- `irpf://minimos/{año}` — mínimos personales y familiares.
- `irpf://deducciones/{año}/{territorio}` — catálogo autonómico.
- `irpf://casillas/{año}` — casillas del Modelo 100.
- `irpf://plazos/{año}` — fechas campaña.
- `irpf://obligacion-declarar/{año}` — umbrales art. 96.

## Prompts MCP

- `/revisar-borrador` — flujo guiado paso a paso para revisar borrador.
- `/optimizar-deducciones` — sugiere deducciones aplicables según perfil.
- `/simular-declaracion` — compara individual vs conjunta con/sin plan de pensiones.

## Ejemplos de prompts para LLM cliente

El servidor está diseñado para que un LLM cliente responda consultas como las siguientes combinando múltiples tools. Inclúyelos en el system prompt de tu agente para sugerir patrones de uso:

```
1. "¿Cuánto pago de IRPF en Madrid con 30.000 € brutos si soy soltero, 2025?"
   → usa calcular_irpf(año=2025, territorio="madrid", rendimiento_neto_trabajo=30000)

2. "Lista todas las deducciones autonómicas de Cataluña para el alquiler de vivienda en 2025."
   → usa listar_deducciones_autonomicas(ccaa="cataluna", año=2025, categoria="vivienda")

3. "¿Cuál es la casilla del Modelo 100 para 'planes de pensiones'?"
   → usa buscar_casilla(query="planes de pensiones", año=2025)

4. "Soy madre con un bebé de 1 año en Madrid, mis rentas son bajas (15k). ¿Tengo derecho a algo?"
   → usa calcular_irpf con hijos_edades=[1] para ver la devolución por maternidad
   → usa comprobar_obligacion_declarar para el umbral
   → usa listar_deducciones_autonomicas(ccaa="madrid", categoria="familia")

5. "Comparar la cuota IRPF que pagaría un autónomo de 40k€ en Madrid vs Cataluña vs Bizkaia."
   → tres llamadas a calcular_irpf variando territorio

6. "¿Cuándo termina el plazo para presentar la Renta 2025?"
   → usa consultar_plazos_campana(año=2025)

7. "Si gano 22k€ con un único pagador, ¿estoy obligado a declarar?"
   → usa comprobar_obligacion_declarar

8. "Muéstrame la escala autonómica de La Rioja para 2024 y 2025 y compáralas."
   → dos llamadas a consultar_tramos

9. "¿Qué deducción estatal aplica si compré mi vivienda habitual en 2010?"
   → el motor la aplica automáticamente (DT 18ª LIRPF). Consultar
     resource irpf://minimos/2025 o tool calcular_irpf con
     inversion_vivienda_transitoria

10. "Simula si me compensa tributación conjunta o individual para mi pareja y yo, ambos con 30k€."
    → usa el prompt /simular-declaracion
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

### Descarga de documentación oficial (opcional)

```bash
python -m scripts.descargar_datos_aeat --año 2025
python -m scripts.verificar_checksums
python -m scripts.extraer_casillas_manual --año 2025 --merge
```

### Docker

```bash
docker compose up -d
curl http://localhost:8000/health
```

## Tests

```bash
pytest                  # 231 unit tests
pytest -m reference     # 6 tests validando rangos vs Renta WEB Open
```

## Property-based testing

Tests con `hypothesis` en `tests/test_tax_engine_properties.py` verifican monotonía de la escala, no-negatividad de la cuota líquida, y relaciones razonables entre tributación individual y conjunta.

## Linting y pre-commit

```bash
ruff check --fix && ruff format
pre-commit install  # instala hooks (ruff + checks estándar)
pre-commit run --all-files
```

## Integración con clientes MCP

### Claude Desktop / Claude Code / Cursor

Añade a tu configuración de cliente MCP:

```json
{
  "mcpServers": {
    "renta-mcp": {
      "command": "npx",
      "args": ["mcp-remote", "http://localhost:8000/mcp"]
    }
  }
}
```

Si despliegas el servidor públicamente (ver sección siguiente), sustituye `http://localhost:8000/mcp` por tu URL pública.

## Deploy público

Patrón de despliegue idéntico al repo hermano [`madrid-opendata-mcp`](https://github.com/pablitopool/madrid-opendata-mcp):

### Opción 1 — Cloudflare Tunnel

```bash
docker compose up -d
cloudflared tunnel --url http://localhost:8000
# O con tunnel permanente:
cloudflared tunnel create renta-mcp
cloudflared tunnel route dns renta-mcp renta-mcp.pmgallardodev.com
```

### Opción 2 — Fly.io

```bash
fly launch --name renta-mcp --dockerfile Dockerfile
fly secrets set MCP_PUBLIC_HOST=renta-mcp.fly.dev
fly deploy
```

### Variables de entorno a configurar en producción

```
MCP_ENV=production
MCP_HOST=0.0.0.0
MCP_PORT=8000          # o el que imponga tu plataforma
MCP_PUBLIC_HOST=renta-mcp.tudominio.com
LOG_LEVEL=INFO
SENTRY_DSN=<opcional>
```

El servidor valida en arranque que estas variables estén presentes cuando detecta entorno de despliegue (`PORT` definido). Ver `main.py::_validate_transport_security_env`.

## Evaluaciones MCP

10 preguntas verificables en `evaluations/renta_mcp_eval.xml` (formato del skill mcp-builder) para validar que LLMs cliente usan el servidor correctamente.

## Casos NO soportados en v0.1 (fuera de alcance)

- **Régimen especial trabajadores desplazados (Beckham)** — art. 93 LIRPF.
- **IRNR** (Impuesto sobre la Renta de No Residentes).
- **Rendimientos irregulares con reducción 30%** — prometido en adendum, uso en `calcular_irpf` flag `periodo_generacion_anos` (v0.2).
- **Optimización automática individual vs conjunta** — cubierto parcialmente en `/simular-declaracion`, falta análisis automático.

## Licencia

MIT — véase [`LICENSE`](./LICENSE).
