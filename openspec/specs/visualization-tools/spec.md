# Visualization Tools Specification

## Purpose

Generate PNG chart images (function plots, histograms, line charts, scatter
plots, box plots, synthetic financial charts) via matplotlib and return them as
MCP `Image` content. Matplotlib is an optional (`plotting`) dependency; every
tool degrades missing-dependency and failure cases to a structured
`VisualizationError` result instead of raising.

## Requirements

### Requirement: PNG Image Output

Every visualization tool SHALL render its chart with matplotlib into an
in-memory PNG and return it as an `Image` with format `png`.

#### Scenario: Successful plot

- **WHEN** the client calls `plot_function` with `"x**2"` over range `(-5, 5)`
- **THEN** the tool returns a PNG image of the parabola

### Requirement: Optional Matplotlib Dependency

Every visualization tool SHALL check matplotlib availability before doing work
and return a `VisualizationError` with `error_type` `missing_dependency` and an
install hint for the `plotting` extra when it is not installed.

#### Scenario: Matplotlib absent

- **WHEN** matplotlib is not installed and the client calls any plot tool
- **THEN** the tool returns a structured error telling the client how to install the `plotting` extra, rather than raising

### Requirement: Structured Error Results

Visualization tools SHALL report validation and execution failures as
`VisualizationError` results (message plus `error_type`) instead of raising
exceptions, including unexpected errors (`error_type` `unexpected_error`).

#### Scenario: Invalid parameter

- **WHEN** the client calls `plot_histogram` with `bins` less than 1
- **THEN** the tool returns a `VisualizationError` with `error_type` `validation_error`

### Requirement: Function Plotting

The `plot_function` tool SHALL sample the expression over `x_range` at
`num_points` points (at least 2, at most the configured array limit), validate
that the range minimum is less than the maximum, and treat points whose
evaluation fails as `NaN` (skipped by matplotlib) rather than aborting the
plot. The variable in the expression SHALL be `x`.

#### Scenario: Partial domain failure

- **WHEN** the client plots `"log(x)"` over `(-5, 5)`
- **THEN** negative points evaluate to NaN and the tool still returns a plot of the valid region

### Requirement: Data Plotting Limits

`plot_histogram` SHALL require at least 2 data points and overlay mean,
median, and standard deviation. `plot_box_plot` SHALL reject groups exceeding
the configured per-group size limit. `plot_financial_line` SHALL reject trend
values outside the whitelist (`bullish`, `bearish`, `volatile`) and generate
synthetic (not real-market) price data over 2 to the configured day limit.

#### Scenario: Financial trend whitelist

- **WHEN** the client calls `plot_financial_line` with trend `sideways`
- **THEN** the tool returns a `VisualizationError` listing the allowed trends

#### Scenario: Histogram with one data point

- **WHEN** the client calls `plot_histogram` with a single-element list
- **THEN** the tool returns a `VisualizationError` because at least 2 points are required

### Requirement: Progress Reporting

Visualization tools SHALL report stage-by-stage progress through the optional
MCP context when one is provided, and SHALL skip progress reporting entirely
when it is not.

#### Scenario: Progress with context

- **WHEN** the client provides a context and calls `plot_financial_line`
- **THEN** the tool reports progress at validation, generation, rendering, and completion stages
