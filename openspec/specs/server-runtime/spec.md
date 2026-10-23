# Server Runtime Specification

## Purpose

Assemble the FastMCP server from tool and resource sub-servers, apply
middleware, select the transport from the environment, and expose a health
endpoint for platform probes. `build_server()` is the composition root; the
module-level `mcp` instance and `main()` are the entry points.

## Requirements

### Requirement: Sub-Server Composition

`build_server()` SHALL create a FastMCP instance named `Math Learning Server`
with usage instructions, mount the five sub-servers (calculate, matrix,
persistence, visualization, resources), and return it without starting it. The
assembler SHALL accept an injected token verifier as a test seam.

#### Scenario: Assembly

- **WHEN** `build_server()` is called
- **THEN** the returned server exposes the tools and resources of all five sub-servers

### Requirement: Middleware Stack

The server SHALL apply StructuredLoggingMiddleware (with payloads included)
before ErrorHandlingMiddleware, so every request is logged before other
processing.

#### Scenario: Ordering

- **WHEN** a request traverses the middleware stack
- **THEN** structured logging observes the request before error handling acts on it

### Requirement: Transport Selection

The server SHALL select its transport from the `MCP_TRANSPORT` environment
variable: `stdio` (the default, for local clients) or `http`, which binds
`0.0.0.0:$PORT` (default 8080, Cloud Run convention). The HTTP transport SHALL
serve statelessly unless `MCP_STATELESS_HTTP` is set to a case-insensitive
`false`.

#### Scenario: Default transport

- **WHEN** `MCP_TRANSPORT` is unset and `main()` runs
- **THEN** the server starts on stdio

#### Scenario: HTTP transport

- **WHEN** `MCP_TRANSPORT=http` and `PORT=9090`
- **THEN** the server binds to `0.0.0.0:9090` statelessly

#### Scenario: Stateful opt-out

- **WHEN** `MCP_TRANSPORT=http` and `MCP_STATELESS_HTTP=false`
- **THEN** the HTTP transport runs statefully; stdio is unaffected by the variable

### Requirement: Health Endpoint

The server SHALL expose an unauthenticated `GET /healthz` route returning the
static JSON `{"status": "ok"}`, deliberately checking no dependencies so
platform startup probes can gate traffic on it.

#### Scenario: Probe

- **WHEN** an unauthenticated client requests `/healthz`
- **THEN** it receives `{"status": "ok"}` regardless of authentication configuration
