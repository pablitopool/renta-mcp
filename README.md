# renta-mcp

> [!TIP]
> ¿Tienes feedback? Abre una issue en este repositorio.

[![CI](https://img.shields.io/badge/CI-GitHub%20Actions-blue.svg)](.github/workflows/ci.yml)
[![Licencia: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Servidor no oficial de Model Context Protocol (MCP) que permite a chatbots de IA (Claude, ChatGPT, Gemini, etc.) **calcular la cuota del IRPF español**, consultar tramos autonómicos y forales, buscar deducciones e interpretar casillas del Modelo 100 directamente mediante conversación.

En lugar de navegar manualmente por el [Manual Práctico de Renta de la AEAT](https://sede.agenciatributaria.gob.es/Sede/Ayuda/25Manual/100.html), puedes hacer preguntas como "¿Cuánto pago de IRPF con 30.000 € en Madrid si soy soltero?" o "Lista las deducciones autonómicas de Cataluña para alquiler de vivienda" y obtener respuestas al instante.

> ⚠️ **Herramienta informativa no vinculante.** No está asociada a la AEAT ni al Ministerio de Hacienda. Véase [`DISCLAIMER.md`](./DISCLAIMER.md).

> [!TIP]
> Si despliegas este servidor públicamente, puedes conectar cualquier cliente compatible con MCP a tu endpoint.
> Para conectar tu chatbot favorito, sigue las instrucciones de conexión de más abajo.

## 🌐 Conecta tu chatbot al servidor MCP

Usa el endpoint alojado `https://renta-mcp.vercel.app/mcp` para conectar clientes MCP al despliegue público.

La configuración del servidor MCP depende del cliente. Usa el formato adecuado para tu cliente:

[AnythingLLM](#anythingllm) | [ChatGPT](#chatgpt) | [Claude Code](#claude-code) | [Claude Desktop](#claude-desktop) | [Cursor](#cursor) | [Gemini CLI](#gemini-cli) | [HuggingChat](#huggingchat) | [IBM Bob](#ibm-bob) | [Kiro CLI](#kiro-cli) | [Kiro IDE](#kiro-ide) | [Le Chat (Mistral)](#le-chat-mistral) | [Mistral Vibe CLI](#mistral-vibe-cli) | [OpenCode](#opencode) | [VS Code](#vs-code) | [Windsurf](#windsurf)

### AnythingLLM

1. Localiza el archivo `anythingllm_mcp_servers.json` en el directorio de plugins de almacenamiento de AnythingLLM:
   - **Linux**: `~/.config/anythingllm-desktop/storage/plugins/anythingllm_mcp_servers.json`
   - **MacOS**: `~/Library/Application Support/anythingllm-desktop/storage/plugins/anythingllm_mcp_servers.json`
   - **Windows**: `C:\Users\<username>\AppData\Roaming\anythingllm-desktop\storage\plugins\anythingllm_mcp_servers.json`

2. Añade esta configuración:

```json
{
  "mcpServers": {
    "renta-mcp": {
      "type": "streamable",
      "url": "https://renta-mcp.vercel.app/mcp"
    }
  }
}
```

Para más detalles, consulta la [documentación MCP de AnythingLLM](https://docs.anythingllm.com/mcp-compatibility/overview).

### ChatGPT

*Disponible solo en planes de pago (Plus, Pro, Team y Enterprise).*

1. **Abre Ajustes**: Entra en ChatGPT desde el navegador, ve a `Settings` y luego a `Apps and connectors`.
2. **Activa el modo desarrollador**: Abre `Advanced settings` y habilita **Developer mode**.
3. **Añade el conector**: Vuelve a `Settings` > `Connectors` > `Browse connectors` y haz clic en **Add a new connector**.
4. **Configura el conector**: Indica la URL `https://renta-mcp.vercel.app/mcp` y guarda para activar las herramientas.

### Claude Code

Usa el comando `claude mcp` para añadir el servidor MCP:

```shell
claude mcp add --transport http renta-mcp https://renta-mcp.vercel.app/mcp
```

### Claude Desktop

Añade lo siguiente a tu archivo de configuración de Claude Desktop (normalmente `~/.config/Claude/claude_desktop_config.json` en Linux, `~/Library/Application Support/Claude/claude_desktop_config.json` en MacOS, o `%APPDATA%\Claude\claude_desktop_config.json` en Windows):

```json
{
  "mcpServers": {
    "renta-mcp": {
      "command": "npx",
      "args": [
        "mcp-remote",
        "https://renta-mcp.vercel.app/mcp"
      ]
    }
  }
}
```

**Claude Desktop en Windows:** Si el servidor aparece en la lista pero nunca conecta (sin handshake o sin herramientas), Claude puede estar usando su runtime integrado de Node.js, que no ve los paquetes instalados con tu `npm` del sistema, incluido un `mcp-remote` global. Configura `isUsingBuiltInNodeForMcp` en `false` en la **raíz** del mismo archivo para que `npx` use tu Node instalado y reinicia Claude Desktop:

```json
{
  "isUsingBuiltInNodeForMcp": false,
  "mcpServers": {
    "renta-mcp": {
      "command": "npx",
      "args": [
        "mcp-remote",
        "https://renta-mcp.vercel.app/mcp"
      ]
    }
  }
}
```

### Cursor

Cursor soporta servidores MCP desde su configuración. Para configurar el servidor:

1. Abre los ajustes de Cursor.
2. Busca "MCP" o "Model Context Protocol".
3. Añade un nuevo servidor MCP con esta configuración:

```json
{
  "mcpServers": {
    "renta-mcp": {
      "url": "https://renta-mcp.vercel.app/mcp",
      "transport": "http"
    }
  }
}
```

### Gemini CLI

Añade lo siguiente a `~/.gemini/settings.json` (Linux: `~/.gemini/settings.json`, MacOS: `~/.gemini/settings.json`, Windows: `%USERPROFILE%\.gemini\settings.json`):

```json
{
  "mcpServers": {
    "renta-mcp": {
      "httpUrl": "https://renta-mcp.vercel.app/mcp"
    }
  }
}
```

### HuggingChat

1. **Abre Ajustes:** En la interfaz de chat, haz clic en el icono `+`, selecciona `MCP Servers` y luego `Manage MCP Servers`.
2. **Añade el servidor:** Haz clic en `+ Add Server` en la ventana de gestión.
3. **Configúralo:** Introduce un **Server Name** (por ejemplo, "Renta IRPF") y define `https://renta-mcp.vercel.app/mcp` como **Server URL**. Haz clic en `Add Server` para guardarlo.
4. **Verifica la conexión:** Pulsa `Health Check` en la tarjeta del servidor y confirma que aparece como **Connected**. Asegúrate de que el interruptor esté activado para usar las herramientas en el chat.

### IBM Bob

IBM Bob soporta servidores MCP desde su configuración. Para configurarlo:

1. Haz clic en el icono de ajustes del panel de Bob.
2. Selecciona la pestaña MCP.
3. Haz clic en el botón correspondiente:
   - Edit Global MCP: abre el archivo global `mcp_settings.json`
   - Edit Project MCP: abre el archivo específico del proyecto `.bob/mcp.json` (Bob lo crea si no existe)

Ambos archivos usan JSON con un objeto `mcpServers` que contiene las configuraciones nombradas.

```json
{
  "mcpServers": {
    "renta-mcp": {
      "url": "https://renta-mcp.vercel.app/mcp",
      "type": "streamable-http"
    }
  }
}
```

### Kiro CLI

Añade lo siguiente a `~/.kiro/settings/mcp.json` (Linux: `~/.kiro/settings/mcp.json`, MacOS: `~/.kiro/settings/mcp.json`, Windows: `%USERPROFILE%\.kiro\settings\mcp.json`):

```json
{
  "mcpServers": {
    "renta-mcp": {
      "url": "https://renta-mcp.vercel.app/mcp"
    }
  }
}
```

### Kiro IDE

Añade lo siguiente a tu archivo de configuración MCP de Kiro (`.kiro/settings/mcp.json` en el workspace o, para la configuración global: Linux: `~/.kiro/settings/mcp.json`, MacOS: `~/.kiro/settings/mcp.json`, Windows: `%USERPROFILE%\.kiro\settings\mcp.json`):

```json
{
  "mcpServers": {
    "renta-mcp": {
      "url": "https://renta-mcp.vercel.app/mcp"
    }
  }
}
```

### Le Chat (Mistral)

*Disponible en todos los planes, incluido el gratuito.*

1. **Ve a Connectors**: Abre Mistral en el navegador y entra en `Intelligence` > `Connectors`.
2. **Añade un conector personalizado**: Haz clic en `Add connector` > `Custom MCP Connector`, asígnale un nombre (por ejemplo `RentaIRPF`) y define la URL del servidor como `https://renta-mcp.vercel.app/mcp`.
3. **Sin autenticación**: Deja la autenticación desactivada.
4. **Crear**: Haz clic en **Create**.

### Mistral Vibe CLI

Edita la configuración de Vibe (por defecto: Linux: `~/.vibe/config.toml`, MacOS: `~/.vibe/config.toml`, Windows: `%USERPROFILE%\.vibe\config.toml`) y añade el servidor MCP:

```toml
[[mcp_servers]]
name = "renta-mcp"
transport = "streamable-http"
url = "https://renta-mcp.vercel.app/mcp"
```

Consulta todas las opciones de MCP para Vibe en la documentación oficial: [MCP server configuration](https://github.com/mistralai/mistral-vibe?tab=readme-ov-file#mcp-server-configuration).

### OpenCode

Añade esto a `opencode.json` (por ejemplo `~/.config/opencode/opencode.json` o en la raíz del proyecto). Los servidores remotos usan el objeto `mcp` de nivel superior con `type: "remote"`. Consulta [OpenCode MCP servers](https://opencode.ai/docs/mcp-servers/).

```json
{
  "$schema": "https://opencode.ai/config.json",
  "mcp": {
    "renta-mcp": {
      "type": "remote",
      "url": "https://renta-mcp.vercel.app/mcp",
      "enabled": true
    }
  }
}
```

### VS Code

Añade lo siguiente a tu archivo `mcp.json` de VS Code (Linux: `~/.config/Code/User/mcp.json`, MacOS: `~/Library/Application Support/Code/User/mcp.json`, Windows: `%APPDATA%\Code\User\mcp.json`). Ejecuta **MCP: Open User Configuration** desde la paleta de comandos para abrirlo.

```json
{
  "servers": {
    "renta-mcp": {
      "url": "https://renta-mcp.vercel.app/mcp",
      "type": "http"
    }
  }
}
```

### Windsurf

Añade lo siguiente a `~/.codeium/windsurf/mcp_config.json` (Linux: `~/.codeium/windsurf/mcp_config.json`, MacOS: `~/.codeium/windsurf/mcp_config.json`, Windows: `%USERPROFILE%\.codeium\windsurf\mcp_config.json`):

```json
{
  "mcpServers": {
    "renta-mcp": {
      "command": "npx",
      "args": [
        "-y",
        "mcp-remote",
        "https://renta-mcp.vercel.app/mcp"
      ]
    }
  }
}
```

**Notas:**
- Endpoint público actual: `https://renta-mcp.vercel.app/mcp`.
- Si ejecutas el servidor tú mismo, también puedes usar el endpoint local mostrado en [Ejecución local](#️-ejecución-local).
- Este servidor MCP expone sólo herramientas de cálculo local y consulta de datos fiscales curados, así que no hace falta API key ni credenciales de la AEAT.

## 🖥️ Ejecución local

### 1. Ejecuta el servidor MCP

Antes de empezar, clona este repositorio y entra en el directorio:

```shell
git clone https://github.com/pablitopool/renta-mcp.git
cd renta-mcp
```

Docker es necesario para la configuración recomendada. Instálalo con [Docker Desktop](https://www.docker.com/products/docker-desktop/) o con cualquier Docker Engine compatible antes de continuar.

#### 🐳 Con Docker (recomendado)

```shell
# Con la configuración por defecto (puerto 8000, entorno local)
docker compose up -d

# Con variables de entorno personalizadas
MCP_PORT=8007 LOG_LEVEL=DEBUG docker compose up -d

# Detener
docker compose down
```

**Variables de entorno:**
- `MCP_HOST`: host al que se enlaza el servidor (por defecto `127.0.0.1`). Usa `0.0.0.0` dentro de contenedores o despliegues remotos.
- `MCP_PORT`: puerto del servidor MCP HTTP (por defecto `8000` si no se define).
- `MCP_ENV`: nombre del entorno que se expone en `/health` y en Sentry (por defecto `local` si no se define).
- `MCP_PUBLIC_HOST`: hostname público añadido a las listas de seguridad del transporte cuando expones el servidor en remoto.
- `MCP_ALLOWED_HOSTS`: override opcional, separado por comas, para los hosts permitidos.
- `MCP_ALLOWED_ORIGINS`: override opcional, separado por comas, para los orígenes permitidos.
- `RENTA_DATA_DIR`: directorio alternativo con los YAML de datos fiscales (por defecto `./data/` del proyecto).
- `LOG_LEVEL`: nivel de logging de Python para la aplicación (por defecto `INFO`). Valores habituales: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`.
- `SENTRY_DSN`: DSN de Sentry para activar monitorización de errores y rendimiento. Si no se define, la monitorización queda desactivada.
- `SENTRY_SAMPLE_RATE`: tasa de muestreo para trazas y perfiles de Sentry (float `0.0`–`1.0`, por defecto `1.0`).

#### ⚙️ Instalación manual

Necesitarás Python 3.10+ para instalar las dependencias y ejecutar el servidor.

1. **Crea el entorno virtual e instala las dependencias**

  ```shell
  python3 -m venv .venv
  source .venv/bin/activate
  .venv/bin/pip install --upgrade pip
  .venv/bin/pip install -e '.[dev]'
  ```

2. **Prepara el archivo de entorno**

  Copia el [archivo de ejemplo](.env.example) para crear tu `.env`:

  ```shell
  cp .env.example .env
  ```

  Después, si quieres, edita `.env` y define las variables relevantes para tu ejecución:

  ```dotenv
  MCP_HOST=127.0.0.1
  MCP_PORT=8000
  MCP_ENV=local
  LOG_LEVEL=INFO
  ```

  Carga las variables con el método que prefieras, por ejemplo:

  ```shell
  set -a && source .env && set +a
  ```

3. **Arranca el servidor MCP HTTP**

  ```shell
  .venv/bin/python main.py
  ```

### 2. Conecta tu chatbot al servidor MCP local

Sigue los pasos de [Conecta tu chatbot al servidor MCP](#-conecta-tu-chatbot-al-servidor-mcp) y sustituye la URL alojada por tu endpoint local (por defecto: `http://127.0.0.1:${MCP_PORT:-8000}/mcp`).

## 🚚 Soporte de transporte

El servidor MCP está construido con el [SDK oficial de Python para servidores y clientes MCP](https://github.com/modelcontextprotocol/python-sdk) y usa **solo transporte Streamable HTTP**.

**STDIO y SSE no están soportados**.

## 📋 Endpoints disponibles

**Transporte Streamable HTTP (compatible con el estándar):**
- `POST /mcp` - mensajes JSON-RPC (cliente -> servidor)
- `GET /health` - sonda JSON simple de salud

## 🛠️ Herramientas disponibles

El servidor MCP ofrece herramientas para calcular el IRPF, consultar normativa autonómica y foral, y navegar el Modelo 100 de la AEAT.

**Nota:** Este servidor NO se conecta a los servicios SOAP de la AEAT (que requieren certificado electrónico). Todos los cálculos son locales y se basan en YAML curados a partir de la Ley 35/2006 (LIRPF), el Reglamento (RD 439/2007), las órdenes HAC anuales y los textos refundidos autonómicos.

### Cálculo fiscal

- **`calcular_irpf`** - Liquidación completa del IRPF: aplica reducciones, mínimo personal/familiar, escalas estatal y autonómica (o foral única), deducciones estatales, deducciones autonómicas/forales reclamadas y maternidad reembolsable. Devuelve cuota íntegra, líquida, diferencial y desglose paso a paso.

  Parámetros: `año` (obligatorio), `territorio` (obligatorio), `rendimiento_neto_trabajo` (opcional, por defecto 0), `rendimiento_neto_capital_mobiliario` (opcional), `rendimiento_neto_capital_inmobiliario` (opcional), `rendimiento_neto_actividades` (opcional), `ganancias_patrimoniales_ahorro` (opcional), `situacion_familiar` (`individual` | `conjunta_biparental` | `conjunta_monoparental`), `edad_contribuyente` (opcional), `hijos_edades` (opcional, lista de edades), `ascendientes_edades` (opcional), `discapacidad_contribuyente` (opcional), `aportaciones_planes_pensiones` (opcional), `retenciones_practicadas` (opcional), `donativos_ley_49_2002` (opcional), `donativos_otros` (opcional), `inversion_vivienda_transitoria` (opcional), `obras_eficiencia_energetica` (opcional), `obras_eficiencia_energetica_tipo` (opcional), `familia_numerosa_categoria` (opcional), `alquiler_vivienda_habitual` (opcional), `inversion_vivienda_habitual` (opcional), `inversion_vivienda_habitual_nacimiento_adopcion` (opcional), `inversion_vivienda_habitual_municipio_despoblacion` (opcional), `intereses_prestamo_adquisicion_vivienda_joven` (opcional), `exceso_intereses_financiacion_vivienda` (opcional), `donativos_autonomicos` (opcional), `cotizaciones_empleados_hogar` (opcional), `gastos_arrendamiento_viviendas` (opcional), `gastos_guarderia` (opcional), `gastos_educativos_descendientes` (opcional), `gastos_material_escolar` (opcional), `gastos_escolaridad` (opcional), `gastos_idiomas` (opcional), `gastos_uniformes` (opcional), `gastos_estudios_descendientes` (opcional), `cuotas_sindicales` (opcional), `nacimientos_adopciones_o_acogimientos` (opcional), `adopciones_internacionales` (opcional), `acogimientos_menores` (opcional), `acogimientos_mayores_o_discapacitados` (opcional), `cambios_residencia_municipio_despoblacion` (opcional), `viviendas_vacias_arrendadas` (opcional), `deducciones_autonomicas_reclamadas` (opcional, lista de IDs), `bases_deducciones_autonomicas` (opcional, mapa `id -> base`), `componentes_deducciones_autonomicas` (opcional, mapa `id -> {componente: base}`), `meses_maternidad_por_hijo_menor_3` (opcional)

  Nota: para la mayoría de deducciones autonómicas ya no hace falta pasar IDs manualmente si proporcionas los hechos fiscales básicos (alquiler, vivienda en municipios en riesgo de despoblación, intereses hipotecarios de jóvenes, incremento de costes financieros, donativos autonómicos, cotizaciones de empleados de hogar, gastos de arrendador, gastos educativos, nacimientos, adopciones y acogimientos, etc.). Los IDs siguen disponibles para casos avanzados o flujos guiados.

  Además, acepta `pagos_fraccionados` (por ejemplo, modelos 130/131) para ajustar la cuota diferencial de forma más realista en perfiles de actividad económica.

- **`calcular_rendimiento_actividad`** - Estima rendimiento neto para autónomos (MVP) en estimación directa simplificada/normal o módulos simplificados, e informa importes listos para reutilizar en `calcular_irpf` (`rendimiento_neto_actividades` y `pagos_fraccionados`).

  Parámetros: `regimen` (obligatorio), `ingresos_integros` (obligatorio), `gastos_deducibles` (opcional), `amortizaciones` (opcional), `provisiones_y_gastos_justificados` (opcional), `porcentaje_provisiones_eds` (opcional), `limite_provisiones_eds` (opcional), `pagos_fraccionados_modelo_130_131` (opcional)

- **`preparar_payload_irpf`** - Normaliza datos fiscales básicos y genera un payload estructurado para `calcular_irpf` (modo preparación/híbrido).

  Parámetros: `año` (obligatorio), `territorio` (obligatorio), rendimientos por bloque (opcionales), `retenciones_practicadas` (opcional), `pagos_fraccionados` (opcional), `situacion_familiar` (opcional), `edad_contribuyente` (opcional), `hijos_edades` (opcional), `ascendientes_edades` (opcional)

- **`calcular_ganancia_cripto_fifo`** - Calcula ganancias/pérdidas de cripto con criterio FIFO (MVP) y devuelve importe neto trasladable a `ganancias_patrimoniales_ahorro`.

  Parámetros: `compras` (obligatorio, formato `cantidad@precio_unitario`), `ventas` (obligatorio, formato `cantidad@precio_unitario`), `comisiones_totales` (opcional)

- **`validar_municipio_despoblacion`** - Verifica si un municipio figura en el catálogo orientativo de despoblación para una CCAA y muestra deducciones relacionadas.

  Parámetros: `año` (obligatorio), `ccaa` (obligatorio), `municipio` (obligatorio)

- **`evaluar_regimen_impatriados`** - Evaluación orientativa de elegibilidad al régimen de impatriados (art. 93 LIRPF).

  Parámetros: `anos_desde_desplazamiento` (obligatorio), `residencia_fiscal_5_anos_previos_en_espana` (obligatorio), `existe_relacion_laboral_o_nombramiento` (obligatorio), `trabaja_principalmente_en_espana` (obligatorio)

- **`evaluar_exencion_art_7p`** - Estimación orientativa de la posible exención por trabajos en el extranjero (art. 7.p LIRPF).

  Parámetros: `rendimiento_trabajo_anual` (obligatorio), `dias_trabajados_extranjero` (obligatorio), `total_dias_anuales` (opcional)

- **`evaluar_exit_tax`** - Diagnóstico orientativo de umbrales básicos de exit tax.

  Parámetros: `valor_mercado_participaciones` (obligatorio), `porcentaje_participacion` (obligatorio), `anos_residencia_fiscal_espana_ultimos_15` (obligatorio)

- **`calcular_retencion_nomina`** - Estimación procedimental de la retención IRPF en nómina a partir del salario bruto anual, cotizaciones del trabajador, gastos deducibles del trabajo, mínimo personal y familiar relevante y cuota anual estimada.

  Parámetros: `año` (obligatorio), `territorio` (obligatorio), `salario_bruto_anual` (obligatorio), `situacion_familiar` (opcional), `hijos_edades` (opcional), `ascendientes_edades` (opcional), `edad_contribuyente` (opcional), `discapacidad_contribuyente` (opcional), `meses_pago` (opcional, 12 o 14 — por defecto 14), `cotizaciones_seguridad_social` (opcional, override explícito; si no se informa se estiman y la hipótesis queda reflejada en la salida), `otros_gastos_deducibles` (opcional, adicionales al mínimo general de 2.000 €)

- **`validar_minimo_declarante`** - Verifica que la reducción por rendimientos del trabajo (art. 20 LIRPF) no genere base liquidable negativa.

  Parámetros: `año` (obligatorio), `rendimiento_neto_trabajo` (obligatorio)

### Escalas y mínimos

- **`consultar_tramos`** - Devuelve la escala IRPF aplicable para un año y territorio: estatal o autonómica (régimen común) o única (foral), en base general o del ahorro.

  Parámetros: `año` (obligatorio), `territorio` (opcional, por defecto `estatal`), `tipo` (opcional, `general` | `ahorro`, por defecto `general`)

- **`consultar_minimos`** - Calcula el mínimo personal y familiar aplicable según edad, hijos a cargo, ascendientes y discapacidad (arts. 56-61 LIRPF).

  Parámetros: `año` (obligatorio), `territorio` (opcional), `edad_contribuyente` (opcional), `hijos_edades` (opcional), `ascendientes_edades` (opcional), `discapacidad_contribuyente` (opcional)

### Deducciones autonómicas

- **`listar_deducciones_autonomicas`** - Lista las deducciones autonómicas vigentes para una CCAA, opcionalmente filtradas por categoría (familia, vivienda, educación, donativos, inversión, discapacidad, cultura, otros). Cada línea incluye el `id` reclamable en `calcular_irpf`.

  Parámetros: `ccaa` (obligatorio), `año` (obligatorio), `categoria` (opcional)

- **`buscar_deduccion`** - Búsqueda fuzzy (rapidfuzz) en el catálogo de deducciones autonómicas — en una CCAA concreta o en todas. Devuelve también el `id` de cada deducción para poder aplicarla después en `calcular_irpf`.

  Parámetros: `query` (obligatorio), `año` (obligatorio), `ccaa` (opcional), `limite` (opcional, por defecto 10)

### Modelo 100 (casillas)

- **`listar_casillas_modelo_100`** - Lista las casillas del Modelo 100 agrupadas por apartado operativo (identificación, rendimientos trabajo, capital, actividades económicas, ganancias/pérdidas, reducciones, mínimos, cuota, deducciones, retenciones, resultado).

  Parámetros: `año` (obligatorio), `seccion` (opcional)

- **`buscar_casilla`** - Búsqueda fuzzy de casillas del Modelo 100 por concepto (nombre/descripción).

  Parámetros: `query` (obligatorio), `año` (obligatorio), `limite` (opcional, por defecto 5)

### Campaña Renta

- **`consultar_plazos_campana`** - Fechas clave de la campaña Renta del ejercicio: inicio de presentación online, cita previa telefónica y presencial, domiciliación bancaria y fin de plazo general.

  Parámetros: `año` (obligatorio)

- **`comprobar_obligacion_declarar`** - Determina si el contribuyente está obligado a presentar declaración según los umbrales del art. 96 LIRPF (rendimientos del trabajo con uno o varios pagadores, capital, inmobiliarias, actividades económicas).

  Parámetros: `año` (obligatorio), `rendimientos_trabajo_brutos` (opcional), `numero_pagadores` (opcional, por defecto 1), `rendimientos_segundo_pagador` (opcional), `rendimientos_capital_y_ganancias_con_retencion` (opcional), `rentas_inmobiliarias_imputadas` (opcional), `actividades_economicas` (opcional)

## 📚 Recursos disponibles

El servidor expone también **Resources MCP** con URI canónicos para los datos fiscales estáticos. Úsalos cuando tu cliente soporta `resources/read` (son datos que cambian 1 vez al año, perfectos para cachearlos):

- `irpf://tramos/{año}/estatal` — escala general estatal (JSON).
- `irpf://tramos/{año}/{territorio}` — escala autonómica o foral por slug (`madrid`, `cataluna`, `bizkaia`, `navarra`…).
- `irpf://tramos-ahorro/{año}` — escala de la base del ahorro.
- `irpf://minimos/{año}` — mínimos personales y familiares.
- `irpf://deducciones/{año}/{territorio}` — catálogo de deducciones autonómicas/forales.
- `irpf://casillas/{año}` — casillas del Modelo 100.
- `irpf://plazos/{año}` — fechas de la campaña Renta.
- `irpf://obligacion-declarar/{año}` — umbrales del art. 96 LIRPF.
- `irpf://municipios-despoblacion/{año}/{territorio}` — catálogo orientativo de municipios en riesgo de despoblación por territorio.

## 💬 Prompts disponibles

Flujos conversacionales predefinidos que el cliente puede invocar como slash-commands:

- **`/revisar-borrador`** — guía paso a paso para revisar un borrador del IRPF: pregunta datos personales, ingresos, deducciones aplicables y calcula la cuota.
- **`/preparar_declaracion`** — flujo para normalizar datos y preparar un payload limpio antes del cálculo final.
- **`/optimizar-deducciones`** — dado un perfil de contribuyente, sugiere qué deducciones autonómicas y estatales podrían aplicarse y estima el ahorro máximo.
- **`/simular-declaracion`** — simulación completa con escenarios (individual vs conjunta; con/sin aportación a planes de pensiones) y recomendación final.

## 🧪 Tests

### ✅ Tests automatizados con pytest

Ejecuta los tests con pytest (cubren motor fiscal, data loader, tools, resources, trazabilidad de fuentes legales, cobertura territorial y property-based):

```shell
# Ejecutar todos los tests
.venv/bin/pytest

# Ejecutar con salida detallada
.venv/bin/pytest -v

# Ejecutar un archivo de test concreto
.venv/bin/pytest tests/test_tax_engine.py

# Ejecutar los tests de referencia contra Renta WEB Open (AEAT)
.venv/bin/pytest -m reference
```

Los tests `@pytest.mark.reference` no forman parte de la suite por defecto ni de la CI principal de PRs. Sirven para validar rangos plausibles de cuota líquida contra el simulador oficial de la AEAT sin volver inestable la verificación local.

### 🎲 Property-based tests

`tests/test_tax_engine_properties.py` usa [hypothesis](https://hypothesis.readthedocs.io/) para verificar invariantes del motor fiscal sobre cientos de casos generados automáticamente: monotonía de la escala progresiva, no-negatividad de la cuota líquida, ventaja de la tributación conjunta y generación de devolución por sobre-retención.

### 🔍 Testing interactivo con MCP Inspector

Usa el [MCP Inspector oficial](https://modelcontextprotocol.io/docs/tools/inspector) para probar las herramientas del servidor de forma interactiva.

Requisitos previos:
- Node.js con `npx` disponible

Pasos:
1. Arranca el servidor MCP.
2. En otra terminal, lanza el inspector:

   ```shell
   npx @modelcontextprotocol/inspector --http-url "http://127.0.0.1:${MCP_PORT:-8000}/mcp"
   ```

Ajusta la URL si has expuesto el servidor en otro host o puerto.

### 📝 Evaluaciones MCP

`evaluations/renta_mcp_eval.xml` contiene 10 preguntas verificables (formato del skill `mcp-builder` de Claude Code) para medir si un LLM cliente usa el servidor correctamente — cubren cuota, conjunta, base del ahorro, maternidad, obligación declarar, deducciones autonómicas, casillas, plazos, retenciones y comparativa común vs foral.

## 🤝 Contribuir

Se aceptan contribuciones. Para mantener el proyecto estable y facilitar las revisiones, respeta estas reglas antes de enviar cambios:

- **Revisión humana y responsabilidad:** No envíes código generado por IA sin revisar. Todo cambio debe leerse, entenderse, probarse y validarse por una persona antes de abrir una PR. **Al enviar una pull request, certificas que entiendes completamente el código propuesto y que podrías explicarlo y defenderlo en revisión sin depender de un asistente de IA.**
- **Cambios pequeños:** Seguimos estrictamente el flujo **1 funcionalidad = 1 PR**.
- **Conventional commits:** Usa el formato [Conventional Commits](https://www.conventionalcommits.org/) para los **mensajes de commit** y los **títulos de PR** (por ejemplo `feat: add deducciones-galicia`, `fix: corregir minimo familia numerosa especial`). Consulta la especificación para los tipos, scopes y marcadores de breaking change permitidos.
- **Trazabilidad legal:** toda deducción o escala que añadas debe declarar su `fuente_boe` en el YAML (Ley, Decreto Legislativo, Norma Foral o Ley de Presupuestos autonómica). El test `test_trazabilidad_fuentes` prohíbe marcas `TODO` en ese campo.

Seguimos un proceso estándar de revisión y despliegue:

1. **Envía una PR:** Propón tus cambios mediante una Pull Request contra la rama `master`.
2. **Integración continua:** La CI se ejecuta automáticamente sobre la pull request. **Todos los checks requeridos deben pasar** antes de hacer merge. Ejecuta los mismos checks en local para evitar sorpresas en CI.
3. **Revisión:** Todas las PR deben revisarse y aprobarse antes del merge.
4. **Despliegue:** Una vez integrado en `master`, despliega los cambios en el entorno que corresponda y verifica `/health`, el handshake MCP y una llamada real a `calcular_irpf` con un caso conocido.

### 🧹 Linting y formateo

Este proyecto sigue las guías de estilo PEP 8 usando [Ruff](https://astral.sh/ruff/) para linting, ordenación de imports y formateo.

**Es obligatorio ejecutar estos comandos manualmente o [instalar el hook de pre-commit](#-pre-commit-hooks) antes de enviar contribuciones.**

```shell
# Lint (incluida la ordenación de imports) y formateo
.venv/bin/ruff check --fix && .venv/bin/ruff format
```

### 🔗 Hooks de pre-commit

Este repositorio usa un hook de [pre-commit](https://pre-commit.com/) para hacer lint y limpiar archivos antes de cada commit. Instalarlo es muy recomendable para que las comprobaciones se ejecuten automáticamente.

**Instalar los hooks de pre-commit:**

```shell
.venv/bin/pre-commit install
```

El hook de pre-commit hace automáticamente lo siguiente:
- Comprueba la sintaxis YAML
- Corrige finales de archivo
- Elimina espacios en blanco sobrantes
- Comprueba archivos demasiado grandes
- Ejecuta linting y formateo con Ruff

### 📥 Ingesta de documentación oficial (opcional)

Para regenerar o actualizar los YAML curados desde la documentación oficial AEAT/BOE:

```shell
# Descarga manuales prácticos, XSD, órdenes HAC, deducciones por CCAA y normativa consolidada
.venv/bin/python -m scripts.descargar_datos_aeat --año 2025

# Verifica SHA-256 frente a data/checksums.json
.venv/bin/python -m scripts.verificar_checksums

# Regenera casillas.yaml parseando el manual parte 1 PDF
.venv/bin/python -m scripts.extraer_casillas_manual --año 2025 --merge
```

Los documentos descargados se guardan en `data/raw/` (gitignored) con checksums en `data/checksums.json` (versionado) para auditabilidad.

### 🏷️ Releases y versionado

El proceso de release usa el script [`tag_version.sh`](tag_version.sh) para actualizar `pyproject.toml`, crear una etiqueta git y añadir una entrada en [CHANGELOG.md](CHANGELOG.md).

**Requisitos previos**: [GitHub CLI](https://cli.github.com/) es opcional, pero `git` debe estar instalado y debes estar en la rama principal con el directorio de trabajo limpio antes de etiquetar una release.

```shell
# Crear una nueva release
./tag_version.sh <version>

# Ejemplo
./tag_version.sh 0.2.0

# Simulación para ver qué ocurriría
./tag_version.sh 0.2.0 --dry-run
```

## 📄 Licencia

MIT
