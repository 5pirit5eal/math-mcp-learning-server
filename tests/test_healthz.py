"""Tests for the /healthz platform probe endpoint on the assembled server."""

import httpx
import pytest

from math_mcp.auth import SharedSecretTokenVerifier
from math_mcp.server import build_server

SECRET = "test-shared-secret"


def _asgi_client(app) -> httpx.AsyncClient:
    """Build an in-process HTTP client bound to the server's ASGI app."""
    return httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://testserver",
    )


@pytest.mark.parametrize("stateless_http", [True, False], ids=["stateless", "stateful"])
async def test_healthz_returns_ok_when_unconfigured(stateless_http: bool) -> None:
    """Without auth configuration, /healthz answers with a static ok payload."""
    server = build_server()
    async with _asgi_client(server.http_app(stateless_http=stateless_http)) as client:
        response = await client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.parametrize("stateless_http", [True, False], ids=["stateless", "stateful"])
async def test_healthz_is_exempt_from_shared_secret_auth(stateless_http: bool) -> None:
    """With auth configured, /healthz stays reachable for platform probes."""
    server = build_server(auth=SharedSecretTokenVerifier(SECRET))
    async with _asgi_client(server.http_app(stateless_http=stateless_http)) as client:
        response = await client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
