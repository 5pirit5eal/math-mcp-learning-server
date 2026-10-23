# Expression Evaluation Specification

## Purpose

Provide a defense-in-depth sandbox for evaluating mathematical expression strings
submitted by MCP clients. The evaluator is the only place in the codebase where
`eval()` is permitted; every other module MUST NOT use `eval()`. The sandbox
combines syntax screening, dangerous-pattern rejection, an AST allowlist, and a
restricted evaluation scope, and enforces an execution timeout so that hostile or
pathological input cannot compromise the server.

## Requirements

### Requirement: Restricted Evaluation Scope

The evaluator SHALL execute validated expressions with `eval()` restricted to a
scope containing only the `math` module and the builtin `abs`, and SHALL coerce
every successful result to a `float`.

#### Scenario: Basic arithmetic

- **WHEN** the evaluator receives `"2 + 3 * 4"`
- **THEN** it returns the float `14.0`

#### Scenario: Math functions and constants

- **WHEN** the evaluator receives `"2 * sin(pi/4) + sqrt(16)"`
- **THEN** it returns approximately `5.414`

#### Scenario: Domain and range errors

- **WHEN** the evaluator receives an expression that divides by zero, overflows, or hits a math domain error (e.g. `sqrt(-1)`)
- **THEN** it raises `ValueError` with a human-readable mathematical error message instead of propagating the raw interpreter error

### Requirement: Dangerous-Pattern Screening

The evaluator SHALL reject any expression containing one of the dangerous
substrings (`import`, `exec`, `__`, `eval`, `open`, `file`) and any character
outside digits, arithmetic operators, parentheses, `%`, `.`, `,`, and letters.

#### Scenario: Injection attempt

- **WHEN** the evaluator receives `"__import__('os').system('rm -rf /')"`
- **THEN** it raises `ValueError` explaining that only mathematical expressions are allowed

### Requirement: AST Node Allowlist

Before evaluation, the evaluator SHALL parse the expression into an AST and
reject any node type outside an explicit allowlist covering only numeric
constants, whitelisted identifier names (`sin`, `cos`, `tan`, `log`, `sqrt`,
`abs`, `pow`, `exp`, `pi`, `e`, `tau`), calls to whitelisted names, unary and
binary arithmetic operations, and load contexts. Non-numeric constants
(including booleans and strings) SHALL be rejected.

#### Scenario: Attribute access

- **WHEN** the evaluator receives `"x.__class__"`
- **THEN** it raises `ValueError` because Attribute nodes are not in the allowlist

#### Scenario: Comparison or conditional expression

- **WHEN** the evaluator receives `"1 if True else 2"` or `"1 < 2"`
- **THEN** it raises `ValueError` because those node types are not in the allowlist

### Requirement: Function and Constant Rewriting

The evaluator SHALL rewrite whitelisted function and constant names to their
`math.`-prefixed forms using word-boundary matching, so that embedded substrings
(e.g. `logical` containing `log`) and scientific notation markers (e.g. `1e5`)
are never rewritten.

#### Scenario: Scientific notation preserved

- **WHEN** the evaluator receives `"1e5 * 2"`
- **THEN** the exponent marker is untouched and it returns `200000.0`

### Requirement: Execution Timeout

The evaluator SHALL run each expression in a worker thread wrapped in
`asyncio.wait_for` with the timeout configured by the `math_timeout` setting
(default 5.0 seconds), and SHALL raise `ValueError` with a suggestion to simplify
the expression when the timeout expires. `ProcessPoolExecutor` MUST NOT be used
because it breaks on serverless runtimes.

#### Scenario: Timeout exceeded

- **WHEN** an expression takes longer than the configured timeout to evaluate
- **THEN** the caller receives `ValueError` naming the timeout limit instead of hanging

### Requirement: Educational Classification

The evaluator SHALL classify each expression with a difficulty level
(`basic`, `intermediate`, `advanced` — functions or exponents imply `advanced`)
and a topic (`finance`, `geometry`, `trigonometry`, `logarithms`, defaulting to
`arithmetic`), for use as educational metadata on tool results.

#### Scenario: Difficulty escalation

- **WHEN** the evaluator classifies `"2 + 3"` and `"sqrt(16) + 2**8"`
- **THEN** the first is `basic` and the second is `advanced`

### Requirement: Filesystem-Safe Variable Names

The evaluator SHALL validate workspace variable names by rejecting empty names
and names containing characters other than letters, numbers, underscores, and
hyphens, so that names are safe to use as persistent workspace keys.

#### Scenario: Unsafe name rejected

- **WHEN** a variable name contains `/` or whitespace
- **THEN** validation raises `ValueError` listing the allowed character classes
