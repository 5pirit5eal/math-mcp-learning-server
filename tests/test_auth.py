"""Unit tests for the shared-secret bearer token authentication."""

import pytest
from fastmcp.server.auth import TokenVerifier

from math_mcp.auth import MCP_AUTH_TOKEN, SharedSecretTokenVerifier, create_token_verifier

SECRET = "test-shared-secret"


async def test_create_token_verifier_returns_none_when_unset() -> None:
    """An empty environment disables authentication."""
    assert create_token_verifier(env={}) is None


@pytest.mark.parametrize("value", ["", "   ", "\t\n"])
async def test_create_token_verifier_returns_none_when_blank(value: str) -> None:
    """A blank MCP_AUTH_TOKEN is treated as unconfigured."""
    assert create_token_verifier(env={MCP_AUTH_TOKEN: value}) is None


async def test_create_token_verifier_strips_whitespace() -> None:
    """Surrounding whitespace in the configured secret is ignored."""
    verifier = create_token_verifier(env={MCP_AUTH_TOKEN: f"  {SECRET}  "})
    assert isinstance(verifier, SharedSecretTokenVerifier)
    assert verifier.token == SECRET


async def test_create_token_verifier_uses_os_environ_by_default(monkeypatch) -> None:
    """Without an explicit env mapping, the real environment is read."""
    monkeypatch.setenv(MCP_AUTH_TOKEN, SECRET)
    verifier = create_token_verifier()
    assert isinstance(verifier, SharedSecretTokenVerifier)
    assert verifier.token == SECRET


async def test_verify_token_accepts_matching_token() -> None:
    """The configured secret verifies and yields an access token."""
    verifier = SharedSecretTokenVerifier(SECRET)
    access = await verifier.verify_token(SECRET)
    assert access is not None
    assert access.token == SECRET


@pytest.mark.parametrize("presented", ["", "wrong-token", SECRET + "x", SECRET.upper()])
async def test_verify_token_rejects_non_matching_tokens(presented: str) -> None:
    """Any deviation from the secret is rejected."""
    verifier = SharedSecretTokenVerifier(SECRET)
    assert await verifier.verify_token(presented) is None


async def test_created_verifier_is_a_token_verifier() -> None:
    """The verifier integrates with FastMCP's auth interface."""
    verifier = create_token_verifier(env={MCP_AUTH_TOKEN: SECRET})
    assert isinstance(verifier, TokenVerifier)
