# HTTP Authentication Specification

## Purpose

Protect the HTTP transport with optional shared-secret bearer token
authentication, configured purely through the environment. The server is for
private use; when no secret is configured it runs without authentication.

## Requirements

### Requirement: Environment-Driven Activation

The server SHALL enable authentication on the HTTP transport only when the
`MCP_AUTH_TOKEN` environment variable is set to a non-blank value; unset or
blank SHALL yield no authentication. The stdio transport SHALL never
authenticate regardless of configuration.

#### Scenario: No token configured

- **WHEN** `MCP_AUTH_TOKEN` is unset or blank
- **THEN** HTTP requests are served without authentication

#### Scenario: Token configured

- **WHEN** `MCP_AUTH_TOKEN` is set to a non-blank value
- **THEN** every HTTP MCP request requires the secret in the `Authorization: Bearer` header

### Requirement: Constant-Time Verification

The verifier SHALL compare the presented bearer token against the configured
secret using `hmac.compare_digest` over the UTF-8 encodings, after stripping
surrounding whitespace from the configured secret, so callers cannot recover
the secret through timing side channels and stray whitespace cannot lock
clients out.

#### Scenario: Wrong token

- **WHEN** a client presents a token that does not match the configured secret
- **THEN** verification returns no access token and the request is rejected

#### Scenario: Padded configuration

- **WHEN** the configured secret carries accidental surrounding whitespace
- **THEN** the stripped value is used, so the clean token still authenticates

### Requirement: Pseudo-Token Principal

A successful verification SHALL return an access token with client ID
`shared-secret`, no scopes, and no claims, since all holders of the secret are
indistinguishable.

#### Scenario: Authenticated principal

- **WHEN** a client presents the correct bearer token
- **THEN** the request proceeds as the `shared-secret` principal
