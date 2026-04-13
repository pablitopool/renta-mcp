import json
import logging
import os
import sys
from datetime import datetime, timezone
from importlib.metadata import PackageNotFoundError, version
from urllib.parse import urlsplit

import uvicorn
from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings

from helpers.logging import MAIN_LOGGER_NAME, UVICORN_LOGGING_CONFIG
from helpers.sentry import init_sentry
from resources import register_resources
from tools import register_tools

init_sentry()

SERVER_START_TIME = datetime.now(timezone.utc)
logger = logging.getLogger(MAIN_LOGGER_NAME)


def _parse_allowed_values(raw: str, defaults: list[str]) -> list[str]:
    values = [item.strip() for item in raw.split(",") if item.strip()]
    return values or defaults


def _normalize_public_host(raw: str | None) -> str:
    value = (raw or "").strip()
    if not value:
        return ""
    parsed = urlsplit(value)
    if parsed.netloc:
        return parsed.netloc
    return value.split("/", 1)[0]


def _public_deployment_requires_explicit_transport_security() -> bool:
    return bool(os.getenv("PORT"))


def _validate_transport_security_env() -> None:
    if not _public_deployment_requires_explicit_transport_security():
        return
    if os.getenv("MCP_PUBLIC_HOST", "").strip():
        return
    has_custom_hosts = bool(os.getenv("MCP_ALLOWED_HOSTS", "").strip())
    has_custom_origins = bool(os.getenv("MCP_ALLOWED_ORIGINS", "").strip())
    if has_custom_hosts and has_custom_origins:
        return
    raise RuntimeError(
        "Public MCP deployments must configure MCP_PUBLIC_HOST "
        "(host or full URL) or both MCP_ALLOWED_HOSTS and MCP_ALLOWED_ORIGINS. "
        "Example: MCP_PUBLIC_HOST=example.com"
    )


def _default_allowed_hosts() -> list[str]:
    public_host = _normalize_public_host(os.getenv("MCP_PUBLIC_HOST"))
    return [
        "localhost:*",
        "127.0.0.1:*",
        *([public_host] if public_host else []),
    ]


def _default_allowed_origins() -> list[str]:
    public_host = _normalize_public_host(os.getenv("MCP_PUBLIC_HOST"))
    return [
        "http://localhost:*",
        "http://127.0.0.1:*",
        *([f"https://{public_host}"] if public_host else []),
    ]


def _build_transport_security() -> TransportSecuritySettings:
    _validate_transport_security_env()
    return TransportSecuritySettings(
        enable_dns_rebinding_protection=True,
        allowed_hosts=_parse_allowed_values(
            os.getenv("MCP_ALLOWED_HOSTS", ""),
            _default_allowed_hosts(),
        ),
        allowed_origins=_parse_allowed_values(
            os.getenv("MCP_ALLOWED_ORIGINS", ""),
            _default_allowed_origins(),
        ),
    )


transport_security = _build_transport_security()

mcp = FastMCP(
    "renta-mcp",
    transport_security=transport_security,
    stateless_http=True,
)
register_tools(mcp)
register_resources(mcp)
streamable_http_app = mcp.streamable_http_app()


async def asgi_app(scope, receive, send):
    if scope["type"] == "http" and scope.get("path") == "/health":
        try:
            app_version = version("renta-mcp")
        except PackageNotFoundError:
            app_version = "unknown"

        body = json.dumps(
            {
                "status": "ok",
                "uptime_since": SERVER_START_TIME.isoformat(),
                "version": app_version,
                "env": os.getenv("MCP_ENV", "unknown"),
                "portal": "AEAT-modelo-100",
            }
        ).encode("utf-8")
        headers = [
            (b"content-type", b"application/json"),
            (b"content-length", str(len(body)).encode("utf-8")),
        ]
        await send({"type": "http.response.start", "status": 200, "headers": headers})
        await send({"type": "http.response.body", "body": body})
        return

    await streamable_http_app(scope, receive, send)


if __name__ == "__main__":
    port_str = os.getenv("MCP_PORT") or os.getenv("PORT", "8000")
    try:
        port = int(port_str)
    except ValueError:
        print(
            f"Error: Invalid MCP_PORT/PORT environment variable: {port_str}",
            file=sys.stderr,
        )
        sys.exit(1)

    host = os.getenv("MCP_HOST") or ("0.0.0.0" if os.getenv("PORT") else "127.0.0.1")
    uvicorn.run(
        asgi_app,
        host=host,
        port=port,
        log_level="info",
        log_config=UVICORN_LOGGING_CONFIG,
    )
