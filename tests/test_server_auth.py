"""HTTP bearer token enforcement tests for the assembled server."""

import asyncio
import json
import socket
import threading
import time

import pytest
import uvicorn
from fastmcp import Client
from mcp import MCPError

from math_mcp.auth import MCP_AUTH_TOKEN, SharedSecretTokenVerifier
from math_mcp.server import build_server

SECRET = "test-shared-secret"


def _free_port() -> int:
    """Reserve an ephemeral port for the test server."""
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


async def _serve(server):
    """Start the server's HTTP app on a background uvicorn thread."""
    port = _free_port()
    uvicorn_server = uvicorn.Server(
        uvicorn.Config(server.http_app(), host="127.0.0.1", port=port, log_level="critical")
    )
    thread = threading.Thread(target=uvicorn_server.run, daemon=True)
    thread.start()
    deadline = time.monotonic() + 10.0
    while not uvicorn_server.started:
        if time.monotonic() > deadline or not thread.is_alive():
            uvicorn_server.should_exit = True
            raise RuntimeError("test server did not start")
        await asyncio.sleep(0.05)
    return f"http://127.0.0.1:{port}", uvicorn_server, thread


def _stop(uvicorn_server, thread) -> None:
    """Shut down the background uvicorn thread."""
    uvicorn_server.should_exit = True
    thread.join(timeout=10)


@pytest.fixture
async def auth_server():
    """Serve the assembled server with shared-secret auth enabled."""
    server = build_server(auth=SharedSecretTokenVerifier(SECRET))
    base_url, uvicorn_server, thread = await _serve(server)
    yield f"{base_url}/mcp"
    _stop(uvicorn_server, thread)


async def test_http_request_without_token_is_rejected(auth_server: str) -> None:
    """With a configured secret, unauthenticated MCP requests fail."""
    with pytest.raises(MCPError):
        async with Client(auth_server) as client:
            await client.list_tools()


async def test_http_request_with_wrong_token_is_rejected(auth_server: str) -> None:
    """A bearer token that is not the shared secret fails."""
    with pytest.raises(MCPError):
        async with Client(auth_server, auth="wrong-token") as client:
            await client.list_tools()


async def test_authenticated_client_lists_tools(auth_server: str) -> None:
    """The shared secret authenticates the MCP handshake and tool listing."""
    async with Client(auth_server, auth=SECRET) as client:
        tools = await client.list_tools()
    assert "calc_expression" in {tool.name for tool in tools}


async def test_authenticated_client_calls_tool(auth_server: str) -> None:
    """An authenticated client can invoke tools over HTTP."""
    async with Client(auth_server, auth=SECRET) as client:
        result = await client.call_tool("calc_expression", {"expression": "2 + 2"})
    data = json.loads(result.content[0].text)
    assert data["result"] == 4.0


async def test_unconfigured_server_serves_without_authentication(monkeypatch) -> None:
    """Without MCP_AUTH_TOKEN, the server serves MCP requests unauthenticated."""
    monkeypatch.delenv(MCP_AUTH_TOKEN, raising=False)
    server = build_server()
    async with Client(server) as client:
        tools = await client.list_tools()
    assert "calc_expression" in {tool.name for tool in tools}


async def test_env_configured_server_enforces_authentication(monkeypatch) -> None:
    """build_server picks up MCP_AUTH_TOKEN from the environment by default."""
    monkeypatch.setenv(MCP_AUTH_TOKEN, SECRET)
    server = build_server()
    base_url, uvicorn_server, thread = await _serve(server)
    try:
        with pytest.raises(MCPError):
            async with Client(f"{base_url}/mcp") as client:
                await client.list_tools()
        async with Client(f"{base_url}/mcp", auth=SECRET) as client:
            tools = await client.list_tools()
    finally:
        _stop(uvicorn_server, thread)
    assert "calc_expression" in {tool.name for tool in tools}
