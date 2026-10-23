# MCP Resources Specification

## Purpose

Expose read-only reference material (mathematical constants, function syntax,
tool catalog, workspace views) as MCP resources, argument completions for
templated URIs, and two educational prompt templates. Resources give clients
self-service discovery without invoking tools.

## Requirements

### Requirement: Mathematical Constants Resource

The server SHALL expose a `math://constants/{constant}` resource template
serving six constants (`pi`, `e`, `golden_ratio`, `euler_gamma`, `sqrt2`,
`sqrt3`), each with value and description. An unknown constant SHALL return a
message listing the available constants rather than raising.

#### Scenario: Known constant

- **WHEN** the client reads `math://constants/pi`
- **THEN** the resource returns the value of pi and its description

#### Scenario: Unknown constant

- **WHEN** the client reads `math://constants/tau2`
- **THEN** the resource returns a message naming the available constants

### Requirement: Constant Name Completion

The server SHALL provide argument completions for the constants resource
template, returning the constant names that match the typed prefix.

#### Scenario: Prefix completion

- **WHEN** a client types `math://constants/eu` and requests completion
- **THEN** the server offers `euler_gamma`

### Requirement: Function Syntax Reference

The server SHALL expose `math://functions` with usage documentation for the
supported mathematical functions, including examples.

#### Scenario: Syntax lookup

- **WHEN** the client reads `math://functions`
- **THEN** the resource returns the reference for `abs`, `sin`, `cos`, `tan`, `sqrt`, `log`, and `pow` with examples

### Requirement: Workspace Views

The server SHALL expose three workspace views: `math://workspace` (a formatted
summary of all variables and statistics, truncated at 4000 characters with a
truncation notice), `math://variables` (a lightweight list of variable names),
and `math://history` (the ten most recently saved calculations, with an
overflow count when more exist).

#### Scenario: Oversized workspace summary

- **WHEN** the workspace summary exceeds 4000 characters
- **THEN** `math://workspace` returns the first 4000 characters plus a truncation notice pointing to `math://variables`

#### Scenario: Empty history

- **WHEN** no variables are saved and the client reads `math://history`
- **THEN** the resource explains the workspace is empty and names the save tool

### Requirement: Tool Catalog Resource

The server SHALL expose `math://catalog/tools` as a JSON catalog of the
available tools with category, read-only flag, and an example invocation for
each.

#### Scenario: Catalog request

- **WHEN** the client reads `math://catalog/tools`
- **THEN** the resource returns JSON with a `tools` array and a `count` field

### Requirement: Educational Prompt Templates

The server SHALL expose a `Math Tutor` prompt (topic, difficulty level,
optional worked examples) and a `Formula Explainer` prompt (formula, mathematical
context), both generating structured tutoring prompts.

#### Scenario: Tutor prompt

- **WHEN** the client gets the `Math Tutor` prompt with topic `derivatives` and level `beginner`
- **THEN** the returned prompt instructs the tutor model to define, break down, and apply the concept at that level
