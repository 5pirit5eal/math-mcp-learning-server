#!/usr/bin/env python3
"""
Math MCP Server - FastMCP Implementation
Educational MCP server demonstrating all three MCP pillars: Tools, Resources, and Prompts.
Uses FastMCP patterns with structured output and multi-transport support.
"""

import os

from fastmcp import FastMCP
from fastmcp.server.auth import TokenVerifier
from fastmcp.server.middleware.error_handling import ErrorHandlingMiddleware
from fastmcp.server.middleware.logging import StructuredLoggingMiddleware
from mcp.types import Completion, ResourceTemplateReference
from starlette.requests import Request
from starlette.responses import JSONResponse

from math_mcp.auth import create_token_verifier
from math_mcp.resources import resources_mcp
from math_mcp.tools import calculate_mcp, matrix_mcp, persistence_mcp, visualization_mcp

MCP_TRANSPORT = "MCP_TRANSPORT"
MCP_STATELESS_HTTP = "MCP_STATELESS_HTTP"
PORT = "PORT"
DEFAULT_PORT = "8080"

# Constants list must match resources.py get_math_constant keys
_CONSTANTS = ["pi", "e", "golden_ratio", "euler_gamma", "sqrt2", "sqrt3"]


def resolve_stateless_http() -> bool:
    """Resolve whether the HTTP transport serves requests statelessly.

    Unset or any value other than case-insensitive ``false`` means stateless;
    only ``MCP_STATELESS_HTTP=false`` restores stateful HTTP behavior. The
    stdio transport is unaffected by this setting.

    Returns:
        bool: True when the HTTP transport should be stateless.
    """
    return os.environ.get(MCP_STATELESS_HTTP, "").strip().lower() != "false"


# === SERVER ASSEMBLY ===


def build_server(auth: TokenVerifier | None = None) -> FastMCP:
    """Assemble the FastMCP server from all tool and resource sub-servers.

    ``auth`` supplies the token verifier directly (test seam); by default it
    comes from the ``MCP_AUTH_TOKEN`` environment variable, which yields no
    authentication when unconfigured.

    Args:
        auth: Token verifier for the HTTP transport; None resolves it from
        the MCP_AUTH_TOKEN environment variable (None means no auth when
        the variable is unset or blank).

    Returns:
        FastMCP: Fully assembled server instance.
    """
    if auth is None:
        auth = create_token_verifier()
    mcp = FastMCP(
        name="Math Learning Server",
        auth=auth,
        instructions=(
            "Math Learning Server - use these tools for mathematical computation:\n\n"
            "CALCULATE: Use `calculate` for arithmetic/algebra, `statistics` for lists, "
            "`compound_interest` for finance (rate as decimal: 0.05 = 5%), "
            "`convert_units` for unit conversion (length/weight/temperature).\n\n"
            "MATRIX: Use `matrix_multiply`, `matrix_determinant`, `matrix_inverse`, "
            "`matrix_transpose`, `matrix_eigenvalues` for linear algebra.\n\n"
            "VISUALIZE: Use `plot_function`, `plot_histogram`, `plot_scatter`, "
            "`plot_line_chart`, `plot_box_plot`, `plot_financial_line` for charts.\n\n"
            "WORKSPACE: Use `save_calculation` to persist results, `load_variable` to retrieve. "
            "Results survive server restarts. View all via math://workspace resource.\n\n"
            "RESOURCES: math://functions (syntax reference), math://constants/{name} "
            "(pi/e/golden_ratio/euler_gamma/sqrt2/sqrt3), math://catalog/tools (tool index)."
        ),
    )

    # Mount sub-server tools using FastMCP composition pattern
    mcp.mount(calculate_mcp)
    mcp.mount(matrix_mcp)
    mcp.mount(persistence_mcp)
    mcp.mount(visualization_mcp)
    mcp.mount(resources_mcp)

    # Add middleware in correct order: StructuredLogging -> ErrorHandling
    # Logging middleware placed first to capture all requests before other processing
    mcp.add_middleware(StructuredLoggingMiddleware(include_payloads=True))
    mcp.add_middleware(ErrorHandlingMiddleware())

    # === ARGUMENT COMPLETIONS ===

    @mcp.completion
    async def handle_completion(
        ref: object,
        argument: object,
        context: object = None,
    ) -> Completion | None:
        """Provide tab-completions for math://constants/{constant} resource template."""
        if not isinstance(ref, ResourceTemplateReference):
            return None
        if ref.uri != "math://constants/{constant}":
            return None
        prefix = getattr(argument, "value", "") or ""
        matches = [c for c in _CONSTANTS if c.startswith(prefix)]
        return Completion(values=matches)

    # === HEALTH ENDPOINT ===

    @mcp.custom_route("/healthz", methods=["GET"])
    async def healthz(request: Request) -> JSONResponse:
        """Unauthenticated health endpoint for platform startup probes.

        Intentionally checks no dependencies; Cloud Run holds back traffic
        until the probe succeeds.

        Args:
            request: Starlette Request object (unused but required by route handler).

        Returns:
            JSONResponse: Static {"status": "ok"} payload.
        """
        return JSONResponse({"status": "ok"})

    return mcp


mcp = build_server()


# === MAIN ENTRY POINT ===


def main() -> None:
    """Main entry point supporting multiple transports.

    The transport is selected via ``MCP_TRANSPORT``: ``stdio`` (default) or
    ``http``. The HTTP transport binds to ``0.0.0.0:$PORT`` (Cloud Run
    convention, default 8080) and serves statelessly unless
    ``MCP_STATELESS_HTTP=false``.
    """
    if os.environ.get(MCP_TRANSPORT, "stdio") == "http":
        mcp.run(
            transport="http",
            host="0.0.0.0",  # noqa: S104 - Cloud Run requires binding all interfaces
            port=int(os.environ.get(PORT, DEFAULT_PORT)),
            stateless_http=resolve_stateless_http(),
        )
    else:
        mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
