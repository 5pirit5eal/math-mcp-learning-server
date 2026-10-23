# Matrix Tools Specification

## Purpose

Expose linear-algebra operations over NumPy as FastMCP tools: multiplication,
transpose, determinant, inverse, and eigenvalues. NumPy is an optional
(`scientific`) dependency; the tools fail with actionable guidance when it is
absent and degrade singular-matrix and complex-eigenvalue cases to structured
results instead of raising.

## Requirements

### Requirement: Matrix Input Validation

Every matrix tool SHALL validate its matrix input before computation: the
matrix MUST be non-empty, a list of lists, rectangular (uniform row lengths),
contain only numeric elements, and not exceed 100x100 dimensions. Violations
raise `ValueError` with a descriptive message.

#### Scenario: Ragged matrix

- **WHEN** a tool receives `[[1, 2], [3]]`
- **THEN** it raises `ValueError` because row lengths differ

#### Scenario: Oversized matrix

- **WHEN** a tool receives a matrix larger than 100x100
- **THEN** it raises `ValueError` naming the maximum size

### Requirement: Optional NumPy Dependency

Matrix tools SHALL raise `ValueError` with the install hint
(`math-mcp-learning-server[scientific]`) when NumPy is not installed, instead of
crashing on `ImportError`.

#### Scenario: NumPy absent

- **WHEN** NumPy is not installed and a client invokes any matrix tool
- **THEN** the tool raises `ValueError` instructing how to install the `scientific` extra

### Requirement: Matrix Multiplication

The `matrix_multiply` tool SHALL compute A x B, raise `ValueError` when the
column count of A does not equal the row count of B, and return the dimensions
of both inputs alongside the result matrix.

#### Scenario: Dimension mismatch

- **WHEN** the client multiplies a 2x3 matrix by a 2x2 matrix
- **THEN** the tool raises `ValueError` explaining the incompatible dimensions

### Requirement: Square-Matrix Operations

`matrix_determinant` SHALL reject non-square matrices with `ValueError` and
return the determinant as a float for square input.

#### Scenario: Non-square determinant

- **WHEN** the client requests the determinant of a 2x3 matrix
- **THEN** the tool raises `ValueError` stating a square matrix is required

### Requirement: Singular-Matrix Degradation

The `matrix_inverse` tool SHALL return a structured result with `success: false`
and an explanatory `error` (rather than raising) when the matrix is singular
(determinant magnitude below 1e-10) or non-square.

#### Scenario: Singular matrix

- **WHEN** the client requests the inverse of `[[1, 2], [2, 4]]`
- **THEN** the tool returns `success: false` with an error explaining the matrix is singular

### Requirement: Complex Eigenvalue Handling

The `matrix_eigenvalues` tool SHALL return eigenvalues as their real parts and,
when imaginary parts exceed 1e-10, additionally return string representations
of the complex values and a warning that imaginary parts were truncated.
Non-square input SHALL return `success: false` with an error instead of raising.

#### Scenario: Complex eigenvalues

- **WHEN** the client requests eigenvalues of a rotation-like matrix with complex eigenvalues
- **THEN** the result includes real-part floats, a `complex_eigenvalues_warning`, and `complex_values` strings

#### Scenario: Real eigenvalues

- **WHEN** the client requests eigenvalues of `[[4, 2], [1, 3]]`
- **THEN** the result includes the eigenvalues with no complex warning or complex values
