# Calculation Tools Specification

## Purpose

Expose arithmetic, statistics, finance, and unit-conversion capabilities as
FastMCP tools that return structured, Pydantic-modeled results annotated with
educational metadata. All tools are read-only and idempotent; none require
optional dependencies.

## Requirements

### Requirement: Expression Calculation Tool

The `calc_expression` tool SHALL evaluate a single mathematical expression
through the sandboxed evaluator and return a structured result containing the
original expression, the numeric result, a difficulty level, and a topic.

#### Scenario: Evaluate an expression

- **WHEN** the client calls `calc_expression` with `"2 * sin(pi/4) + sqrt(16)"`
- **THEN** the tool returns a result model with `result` approximately `5.414`, difficulty, and topic `arithmetic`

### Requirement: Descriptive Statistics Tool

The `calc_statistics` tool SHALL compute one of `mean`, `median`, `mode`,
`std_dev`, or `variance` over a list of numbers, reject empty lists and unknown
operations with `ValueError`, and return the operation, numeric result, and
sample size. `std_dev` and `variance` on a single-element list SHALL return `0`.

#### Scenario: Mean of a list

- **WHEN** the client calls `calc_statistics` with `[1.0, 2.5, 3.0, 4.5, 5.0]` and operation `mean`
- **THEN** the tool returns `3.2` with `sample_size` 5

#### Scenario: Unknown operation

- **WHEN** the client calls `calc_statistics` with operation `average`
- **THEN** the tool raises `ValueError` listing the allowed operations

### Requirement: Compound Interest Tool

The `calc_interest` tool SHALL compute compound interest as
`A = P(1 + r/n)^(nt)` with `compounds_per_year` defaulting to 12, and SHALL
return the final amount, total interest, and the formula string. Inputs SHALL
be validated: principal > 0, rate in [0, 1] as a decimal, time > 0,
compounds_per_year > 0.

#### Scenario: Monthly compounding

- **WHEN** the client calls `calc_interest` with principal `10000`, rate `0.05`, time `5`
- **THEN** the tool returns a final amount of approximately `12833.59` and topic `finance`

#### Scenario: Percentage rate rejected

- **WHEN** the client calls `calc_interest` with rate `5.0` (a percentage, not a decimal)
- **THEN** input validation rejects the value because rate must be at most 1.0

### Requirement: Unit Conversion Tool

The `calc_units` tool SHALL convert values within three unit categories:
length (`mm`, `cm`, `m`, `km`, `in`, `ft`, `yd`, `mi`), weight (`g`, `kg`,
`oz`, `lb`), and temperature (`c`, `f`, `k`). Length and weight SHALL convert
via base-unit factors; temperature SHALL convert through Celsius as the pivot.
Unknown unit types or units SHALL raise `ValueError` naming the problem unit.

#### Scenario: Length conversion

- **WHEN** the client calls `calc_units` with value `5`, from `km`, to `mi`, type `length`
- **THEN** the tool returns approximately `3.11` miles

#### Scenario: Temperature conversion

- **WHEN** the client calls `calc_units` with value `100`, from `c`, to `f`, type `temperature`
- **THEN** the tool returns `212.0`

#### Scenario: Unknown unit

- **WHEN** the client calls `calc_units` with an unrecognized `from_unit`
- **THEN** the tool raises `ValueError` naming the invalid unit

### Requirement: Educational Annotations on Results

Every calculation tool result SHALL carry a `difficulty` and a `topic` field so
clients can present results with educational context.

#### Scenario: Annotations present

- **WHEN** any calculation tool returns a result
- **THEN** the result model includes non-empty `difficulty` and `topic` values
