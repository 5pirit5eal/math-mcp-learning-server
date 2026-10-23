"""Shared test fixtures for all tests."""

import os

# Tests exercise the unauthenticated server. A locally exported MCP_AUTH_TOKEN
# must not flip the module-level server instance into auth mode at import time.
os.environ.pop("MCP_AUTH_TOKEN", None)

import asyncio
from collections.abc import AsyncGenerator

import pytest
from fastmcp import Client
from fastmcp.client.transports import StreamableHttpTransport
from fastmcp.utilities.tests import find_available_port

from math_mcp.server import mcp


@pytest.fixture
async def http_server() -> AsyncGenerator[str]:
    """Start MCP server in-process with HTTP transport for testing.

    This fixture creates a real HTTP server instance, allowing tests
    to verify behavior over the actual HTTP transport layer.
    Mimics how fastmcp.cloud deploys the server.

    Yields:
        str: Server URL (e.g., "http://127.0.0.1:8000/mcp")
    """
    port = find_available_port()
    host = "127.0.0.1"
    url = f"http://{host}:{port}/mcp"

    # Start server in background task
    server_task = asyncio.create_task(
        mcp.run_http_async(host=host, port=port, show_banner=False, log_level="error")
    )

    # Give server time to start
    await asyncio.sleep(0.5)

    try:
        yield url
    finally:
        # Cleanup: cancel server task
        server_task.cancel()
        try:
            await server_task
        except asyncio.CancelledError:
            pass


@pytest.fixture
async def http_client(http_server: str) -> AsyncGenerator[Client]:
    """Connect to HTTP server via StreamableHttpTransport.

    Args:
        http_server: Server URL from http_server fixture

    Yields:
        Client: Connected MCP client instance
    """
    async with Client(transport=StreamableHttpTransport(http_server)) as client:
        yield client


@pytest.fixture
def mock_context():
    """Standard mock MCP context for tools (visualization, matrix, math operations)."""
    from unittest.mock import AsyncMock

    ctx = AsyncMock()
    ctx.info_logs = []
    ctx.progress_reports = []

    async def mock_info(msg):
        ctx.info_logs.append(msg)

    async def mock_warning(msg):
        ctx.info_logs.append(f"WARNING: {msg}")

    async def mock_error(msg):
        ctx.info_logs.append(f"ERROR: {msg}")

    async def mock_report_progress(current, total, message=""):
        ctx.progress_reports.append((current, total, message))

    ctx.info = mock_info
    ctx.warning = mock_warning
    ctx.error = mock_error
    ctx.report_progress = mock_report_progress
    return ctx


@pytest.fixture
def mock_persistence_context():
    """Extended mock MCP context for persistence tools (adds lifespan state management)."""
    from unittest.mock import AsyncMock

    ctx = AsyncMock()
    ctx.info_logs = []
    ctx.progress_reports = []
    ctx._state = {}
    ctx.lifespan_context = {}

    async def mock_info(msg):
        ctx.info_logs.append(msg)

    async def mock_warning(msg):
        ctx.info_logs.append(f"WARNING: {msg}")

    async def mock_error(msg):
        ctx.info_logs.append(f"ERROR: {msg}")

    async def mock_report_progress(current, total, message=""):
        ctx.progress_reports.append((current, total, message))

    async def set_state(key, value):
        ctx._state[key] = value

    async def get_state(key, default=None):
        return ctx._state.get(key, default)

    ctx.info = mock_info
    ctx.warning = mock_warning
    ctx.error = mock_error
    ctx.report_progress = mock_report_progress
    ctx.set_state = set_state
    ctx.get_state = get_state
    return ctx
