import json

import pytest

from main import asgi_app


@pytest.mark.asyncio
async def test_health_endpoint_returns_ok_payload():
    received: list[dict] = []

    async def receive():
        return {"type": "http.request", "body": b"", "more_body": False}

    async def send(message):
        received.append(message)

    scope = {
        "type": "http",
        "path": "/health",
        "method": "GET",
        "headers": [],
    }

    await asgi_app(scope, receive, send)

    start = next(m for m in received if m["type"] == "http.response.start")
    body = next(m for m in received if m["type"] == "http.response.body")

    assert start["status"] == 200
    payload = json.loads(body["body"])
    assert payload["status"] == "ok"
    assert payload["portal"] == "AEAT-modelo-100"
    assert "uptime_since" in payload
    assert "version" in payload
