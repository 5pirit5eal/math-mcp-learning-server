"""Isolated unit tests for the AST-based expression validation layer.

Tests cover the _ASTValidator node allowlist and the _validate_ast function
added to eval.py as defense-in-depth.  Existing coverage in test_math_operations.py
is preserved; these tests verify the new AST layer only (behaviors not already
covered by existing tests).
"""

import pytest

from math_mcp.eval import safe_eval_expression

# =============================================================================
# Happy path: AST layer accepts valid mathematical expressions
# =============================================================================


class TestHappyPathAST:
    """Verify that legitimate arithmetic and math-function expressions pass."""

    @pytest.mark.parametrize(
        "expr, expected",
        [
            ("10 % 3", 1.0),
            ("15 // 4", 3.0),
            ("2 + 3 % 4", 5.0),
            ("10 - 5 // 2", 8.0),
        ],
    )
    def test_mod_and_floordiv(self, expr: str, expected: float) -> None:
        """Mod and FloorDiv operators are accepted by the AST layer."""
        assert safe_eval_expression(expr) == expected

    @pytest.mark.parametrize(
        "expr, expected",
        [
            ("cos(0)", 1.0),
            ("log(1)", 0.0),
            ("exp(0)", 1.0),
            ("pow(2, 3)", 8.0),
        ],
    )
    def test_whitelisted_math_functions(self, expr: str, expected: float) -> None:
        """Whitelisted math functions (cos, log, exp, pow) are accepted."""
        import math

        assert abs(safe_eval_expression(expr) - expected) < 1e-10

    @pytest.mark.parametrize(
        "expr, expected",
        [
            ("-1", -1.0),
            ("-3.14", -3.14),
            ("--5", 5.0),
            ("-0.5", -0.5),
        ],
    )
    def test_negative_constants(self, expr: str, expected: float) -> None:
        """Negative constant expressions via UnaryOp USub are accepted."""
        assert safe_eval_expression(expr) == expected


# =============================================================================
# Edge case: AST layer rejects non-whitelisted AST node types
# =============================================================================


class TestEdgeCaseAST:
    """Verify that the AST layer rejects disallowed node types.

    Note: Many of these expressions are caught by the security layer
    (_check_expression_security) before reaching the AST validator.  The
    tests just verify that a ValueError is raised -- the specific error
    message depends on which layer catches it first.
    """

    @pytest.mark.parametrize(
        "expr",
        [
            "math.__class__",
            "math.__class__.__name__",
        ],
    )
    def test_rejects_attribute(self, expr: str) -> None:
        """ast.Attribute expression (math.__class__) is rejected."""
        with pytest.raises(ValueError):
            safe_eval_expression(expr)

    @pytest.mark.parametrize(
        "expr, desc",
        [
            ("x[0]", "Subscript"),
        ],
    )
    def test_rejects_subscript(self, expr: str, desc: str) -> None:
        """ast.Subscript expression is rejected."""
        with pytest.raises(ValueError):
            safe_eval_expression(expr)

    @pytest.mark.parametrize(
        "expr, desc",
        [
            ("True", "bool constant"),
            ("False", "bool constant"),
            ('"hello"', "str literal"),
            ("None", "None constant"),
        ],
    )
    def test_rejects_non_numeric_constant(self, expr: str, desc: str) -> None:
        """Non-numeric constants (bool, str, None) are rejected."""
        with pytest.raises(ValueError):
            safe_eval_expression(expr)

    @pytest.mark.parametrize(
        "expr, desc",
        [
            ("1 < 2", "Compare"),
            ("1 == 2", "Compare"),
        ],
    )
    def test_rejects_compare(self, expr: str, desc: str) -> None:
        """ast.Compare expression is rejected."""
        with pytest.raises(ValueError):
            safe_eval_expression(expr)

    @pytest.mark.parametrize(
        "expr, desc",
        [
            ("1 and 0", "BoolOp"),
            ("1 or 0", "BoolOp"),
        ],
    )
    def test_rejects_boolop(self, expr: str, desc: str) -> None:
        """ast.BoolOp expression is rejected."""
        with pytest.raises(ValueError):
            safe_eval_expression(expr)

    @pytest.mark.parametrize(
        "expr, desc",
        [
            ("1 if True else 2", "IfExp ternary"),
        ],
    )
    def test_rejects_ifexp(self, expr: str, desc: str) -> None:
        """ast.IfExp ternary expression is rejected."""
        with pytest.raises(ValueError):
            safe_eval_expression(expr)

    @pytest.mark.parametrize(
        "expr, desc",
        [
            ("lambda x: x + 1", "Lambda"),
        ],
    )
    def test_rejects_lambda(self, expr: str, desc: str) -> None:
        """ast.Lambda expression is rejected."""
        with pytest.raises(ValueError):
            safe_eval_expression(expr)

    @pytest.mark.parametrize(
        "expr, desc",
        [
            ("[1, 2, 3]", "list literal"),
            ("{1, 2, 3}", "set literal"),
            ("(1, 2)", "tuple literal"),
            ('{"a": 1}', "dict literal"),
        ],
    )
    def test_rejects_collection_literals(self, expr: str, desc: str) -> None:
        """Collection literals (list, set, tuple, dict) are rejected."""
        with pytest.raises(ValueError):
            safe_eval_expression(expr)

    @pytest.mark.parametrize(
        "expr, desc",
        [
            ("(x := 1)", "NamedExpr walrus"),
        ],
    )
    def test_rejects_namedexpr(self, expr: str, desc: str) -> None:
        """ast.NamedExpr walrus operator is rejected."""
        with pytest.raises(ValueError):
            safe_eval_expression(expr)

    @pytest.mark.parametrize(
        "expr, desc",
        [
            ('f"{1+1}"', "f-string JoinedStr"),
        ],
    )
    def test_rejects_fstring(self, expr: str, desc: str) -> None:
        """f-string (JoinedStr) expression is rejected."""
        with pytest.raises(ValueError):
            safe_eval_expression(expr)

    @pytest.mark.parametrize(
        "expr, desc",
        [
            ("~1", "Invert operator"),
            ("not True", "Not operator"),
        ],
    )
    def test_rejects_unary_operators(self, expr: str, desc: str) -> None:
        """ast.Invert and ast.Not operators are rejected."""
        with pytest.raises(ValueError):
            safe_eval_expression(expr)

    @pytest.mark.parametrize(
        "expr, desc",
        [
            ("x", "unknown identifier"),
            ("foo", "unknown identifier"),
            ("abc", "unknown identifier"),
        ],
    )
    def test_rejects_non_whitelisted_name(self, expr: str, desc: str) -> None:
        """Non-whitelisted Name identifiers are rejected."""
        with pytest.raises(ValueError, match="disallowed construct"):
            safe_eval_expression(expr)

    @pytest.mark.parametrize(
        "expr, desc",
        [
            ("math.__class__()", "Attribute-based call"),
            ("math.__name__", "Attribute access"),
        ],
    )
    def test_rejects_attribute_based_call(self, expr: str, desc: str) -> None:
        """Attribute-based calls (math.__class__()) are rejected."""
        with pytest.raises(ValueError):
            safe_eval_expression(expr)


# =============================================================================
# Math constants: bare pi/e/tau resolve to their math-module values
# =============================================================================


class TestMathConstants:
    """Verify that whitelisted math constants are usable as bare identifiers."""

    @pytest.mark.parametrize(
        "expr, expected",
        [
            ("pi", 3.141592653589793),
            ("e", 2.718281828459045),
            ("tau", 6.283185307179586),
            ("2 * pi", 6.283185307179586),
            ("e ** 2", 7.389056098930650),
            ("pi * 2", 6.283185307179586),
            ("cos(pi)", -1.0),
            ("log(e)", 1.0),
            ("2 * sin(pi/4) + sqrt(16)", 5.414213562373095),
        ],
    )
    def test_constants_evaluate(self, expr: str, expected: float) -> None:
        """Whitelisted constants evaluate to their math-module values."""
        assert abs(safe_eval_expression(expr) - expected) < 1e-12

    @pytest.mark.parametrize(
        "expr, expected",
        [
            ("1e2", 100.0),
            ("2E3", 2000.0),
            ("1.5e-2", 0.015),
            ("exp(1)", 2.718281828459045),
        ],
    )
    def test_scientific_notation_not_mangled(self, expr: str, expected: float) -> None:
        """Exponent markers inside float literals are never treated as constants."""
        assert abs(safe_eval_expression(expr) - expected) < 1e-12

    def test_constant_substitution_leaves_functions_intact(self) -> None:
        """Substituted constant inside an already-prefixed function is not re-mangled."""
        # exp(1) becomes math.exp(1); the 'e' inside 'math.exp' must stay put.
        assert abs(safe_eval_expression("exp(pi)") - 23.140692632779267) < 1e-12

    @pytest.mark.parametrize(
        "expr",
        [
            "pie",
            "eta",
            "tau2",
            "PI",
            "E",
        ],
    )
    def test_non_whitelisted_lookalikes_rejected(self, expr: str) -> None:
        """Identifiers that merely contain or resemble constants are rejected."""
        with pytest.raises(ValueError):
            safe_eval_expression(expr)
