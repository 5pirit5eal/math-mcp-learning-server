"""Shared-secret bearer token authentication, driven by the environment."""

import hmac
import os
from collections.abc import Mapping

from fastmcp.server.auth import AccessToken, TokenVerifier

__all__ = ["MCP_AUTH_TOKEN", "SharedSecretTokenVerifier", "create_token_verifier"]

MCP_AUTH_TOKEN = "MCP_AUTH_TOKEN"  # noqa: S105 - environment variable name, not a secret


class SharedSecretTokenVerifier(TokenVerifier):
    """Token verifier that grants access to holders of the shared secret.

    Every MCP request over the HTTP transport must carry the secret in the
    ``Authorization: Bearer <token>`` header. The comparison is constant-time
    (``hmac.compare_digest`` on the UTF-8 encodings) so callers cannot
    recover the secret through response-timing side channels. Tokens are
    compared after ``str.strip()``, so accidental surrounding whitespace in
    the configuration does not lock clients out.
    """

    def __init__(self, token: str) -> None:
        super().__init__()
        self.token = token

    async def verify_token(self, token: str) -> AccessToken | None:
        """Return an access token if the presented bearer token matches.

        Args:
            token: Bearer token extracted from the Authorization header.

        Returns:
            AccessToken: Pseudo-token describing the shared-secret principal,
            or None when the presented token does not match.
        """
        if not token or not hmac.compare_digest(token.encode(), self.token.encode()):
            return None
        return AccessToken(
            token=token,
            client_id="shared-secret",
            scopes=[],
            claims={},
        )


def create_token_verifier(env: Mapping[str, str] | None = None) -> TokenVerifier | None:
    """Build the shared-secret token verifier from the environment.

    Returns ``None`` when ``MCP_AUTH_TOKEN`` is unset or blank, in which case
    the server runs without authentication (stdio transport never
    authenticates regardless). ``env`` overrides the environment for tests.

    Args:
        env: Environment mapping; defaults to ``os.environ``.

    Returns:
        TokenVerifier | None: Verifier accepting exactly the configured
        secret, or None when no secret is configured.
    """
    env_map = os.environ if env is None else env
    token = env_map.get(MCP_AUTH_TOKEN, "").strip()
    if not token:
        return None
    return SharedSecretTokenVerifier(token)
