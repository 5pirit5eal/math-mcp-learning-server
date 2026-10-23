# Tool Contract Specification

## Purpose

Capture the repository-wide patterns every MCP tool follows. These conventions
are load-bearing: they keep tool inputs validated, tool contexts optional,
blocking work off the event loop, and failure behavior predictable. New tools
MUST conform to this contract.

## Requirements

### Requirement: Pydantic Input Validation

Every tool SHALL validate its inputs with Pydantic field constraints
(`Field` limits on lengths and array sizes, numeric bounds) via the
`validated_tool` wrapper (Pydantic `validate_call` with arbitrary types
allowed), so invalid input is rejected before the tool body runs.

#### Scenario: Overlong input

- **WHEN** a client passes an expression longer than the configured length limit
- **THEN** validation fails before the tool body executes

### Requirement: Optional Context Parameter

Every tool SHALL accept an optional MCP context typed
`ctx: SkipValidation[Context | None] = None`, never require it, and guard all
context usage (progress reporting, session state) with `if ctx:`.

#### Scenario: Context-free client

- **WHEN** a client calls a tool without providing a context
- **THEN** the tool runs successfully and skips all progress reporting

### Requirement: Non-Blocking Execution

Tools SHALL offload synchronous or potentially long work through
`asyncio.to_thread` (expression evaluation, timeout enforcement) so the event
loop is never blocked by client-supplied computation.

#### Scenario: Long evaluation

- **WHEN** a client submits a slow expression
- **THEN** the server remains responsive to other requests while the evaluation runs in a worker thread

### Requirement: Environment-Configured Limits

Cross-module configuration values (environment variable names, secret names,
size and timeout limits) SHALL be defined once as named constants in the module
that owns them (`settings.py`), derived from environment-overridable
`MathMCPSettings` fields, and imported elsewhere rather than duplicated.

#### Scenario: Limit override

- **WHEN** the operator sets the `math_timeout` environment variable
- **THEN** expression evaluation enforces the overridden timeout without code changes

### Requirement: Optional Heavy Dependencies

Heavy dependencies (NumPy for matrix tools, matplotlib for plot tools) SHALL be
optional extras. Tools SHALL detect their absence and respond with actionable
guidance naming the installable extra, instead of raising an import error at
call time or at import time.

#### Scenario: Lean installation

- **WHEN** the package is installed without the `plotting` and `scientific` extras
- **THEN** the server imports and starts, and affected tools return install guidance on invocation

### Requirement: Educational Metadata

Every tool result model SHALL carry educational annotations (`difficulty` and
`topic` fields) alongside its payload, consistent with the server's purpose as a
learning tool.

#### Scenario: Result inspection

- **WHEN** any tool returns a structured result
- **THEN** the result model includes difficulty and topic fields

### Requirement: MCP Tool Annotations

Every tool SHALL declare MCP `ToolAnnotations` hints (`title`, `read_only_hint`,
`idempotent_hint`) so clients can reason about side effects; mutating tools
(workspace save) MUST declare non-read-only, non-idempotent hints.

#### Scenario: Annotation parity

- **WHEN** a tool that only computes is registered
- **THEN** its annotations declare it read-only and idempotent
