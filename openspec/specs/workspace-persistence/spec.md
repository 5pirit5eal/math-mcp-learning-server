# Workspace Persistence Specification

## Purpose

Persist named calculation results to a per-user workspace file so that data
survives server restarts and is shared across transports. The layer is
thread-safe, writes atomically, and degrades gracefully on corrupt files. On
Cloud Run the filesystem is instance-local, so persistence is ephemeral there by
design.

## Requirements

### Requirement: Workspace Storage Location

The workspace SHALL be stored as `workspace.json` under `~/.math-mcp/` on
macOS/Linux and under `%LOCALAPPDATA%/math-mcp/` on Windows, with the directory
created automatically on first access.

#### Scenario: First use

- **WHEN** the workspace is accessed and no directory exists
- **THEN** the storage layer creates the directory and the workspace file path is resolvable

### Requirement: Atomic and Thread-Safe Writes

The workspace manager SHALL serialize all mutations with a reentrant lock and
write updates atomically (write to a temporary file, then replace), so a crash
mid-write cannot corrupt the workspace. A single manager instance SHALL be
shared per server process.

#### Scenario: Crash during save

- **WHEN** the process dies between writing the temporary file and the replace
- **THEN** the previous `workspace.json` remains intact and loadable

### Requirement: Corrupt File Recovery

The workspace manager SHALL fall back to a new empty workspace (with fresh
statistics) when loading fails due to JSON corruption or I/O errors, and SHALL
log a warning instead of raising.

#### Scenario: Corrupted workspace

- **WHEN** `workspace.json` contains invalid JSON
- **THEN** the next operation starts from an empty workspace rather than failing

### Requirement: Save Tool

The `workspace_save` tool SHALL validate the variable name (letters, numbers,
underscores, hyphens), store expression, result, and educational metadata
(difficulty, topic, session ID) with an ISO timestamp, overwrite an existing
variable of the same name, and report whether the variable was new and the
total variable count.

#### Scenario: Overwrite existing variable

- **WHEN** the client saves a variable name that already exists
- **THEN** the tool reports `is_new: false` and the workspace contains one variable under that name

### Requirement: Load Tool

The `workspace_load` tool SHALL return the stored expression, result, timestamp,
and metadata for an existing variable, and SHALL return a structured failure
(with `success: false`, the error, and the available variable names) for a
missing one instead of raising.

#### Scenario: Load missing variable

- **WHEN** the client loads a name that was never saved
- **THEN** the tool returns `success: false` with the list of available variables

### Requirement: Survival Across Restarts

Saved variables SHALL be readable after the server process restarts, because the
workspace is filesystem-backed rather than in-memory.

#### Scenario: Restart

- **WHEN** a variable is saved, the server restarts, and the client loads the variable
- **THEN** the stored expression, result, and metadata are returned

### Requirement: Session Identification

When an MCP context is provided, the save flow SHALL attach a UUID session ID
from session-scoped context state; for sessionless clients it SHALL degrade to
a fresh UUID per call without affecting persistence.

#### Scenario: Sessionless client

- **WHEN** a sessionless client saves two variables
- **THEN** both saves succeed and persistence is unaffected by per-call UUIDs
