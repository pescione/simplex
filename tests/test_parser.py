"""
Test per il parser.
"""

import pytest
from fractions import Fraction
from core.parser import (
    parse_fraction,
    parse_fraction_list,
    parse_matrix,
    parse_signs_list,
    parse_problem,
    validate_dimensions,
)


class TestParseFraction:
    """Test della funzione parse_fraction."""

    def test_integer(self):
        assert parse_fraction("3") == Fraction(3)
        assert parse_fraction("-2") == Fraction(-2)
        assert parse_fraction("0") == Fraction(0)

    def test_fraction(self):
        assert parse_fraction("1/2") == Fraction(1, 2)
        assert parse_fraction("-3/4") == Fraction(-3, 4)
        assert parse_fraction("5/1") == Fraction(5)

    def test_decimal(self):
        assert parse_fraction("0.5") == Fraction(1, 2)
        assert parse_fraction("0.25") == Fraction(1, 4)
        assert parse_fraction("-1.5") == Fraction(-3, 2)

    def test_invalid(self):
        with pytest.raises(ValueError):
            parse_fraction("invalid")
        with pytest.raises(ValueError):
            parse_fraction("1/0")


class TestParseFractionList:
    """Test della funzione parse_fraction_list."""

    def test_simple_list(self):
        result = parse_fraction_list("[1, 2, 3]")
        assert result == [Fraction(1), Fraction(2), Fraction(3)]

    def test_mixed_numbers(self):
        result = parse_fraction_list("[1, -1/2, 0.5]")
        assert result == [Fraction(1), Fraction(-1, 2), Fraction(1, 2)]

    def test_empty_list(self):
        result = parse_fraction_list("[]")
        assert result == []

    def test_single_element(self):
        result = parse_fraction_list("[5]")
        assert result == [Fraction(5)]

    def test_invalid_brackets(self):
        with pytest.raises(ValueError):
            parse_fraction_list("(1, 2, 3)")


class TestParseMatrix:
    """Test della funzione parse_matrix."""

    def test_simple_matrix(self):
        result = parse_matrix("[[1, 2], [3, 4]]")
        assert result == [
            [Fraction(1), Fraction(2)],
            [Fraction(3), Fraction(4)],
        ]

    def test_single_row(self):
        result = parse_matrix("[[1, 2, 3]]")
        assert result == [[Fraction(1), Fraction(2), Fraction(3)]]

    def test_single_column(self):
        result = parse_matrix("[[1], [2], [3]]")
        assert result == [[Fraction(1)], [Fraction(2)], [Fraction(3)]]

    def test_mixed_numbers(self):
        result = parse_matrix("[[1, -1/2], [0.5, 3]]")
        assert result == [
            [Fraction(1), Fraction(-1, 2)],
            [Fraction(1, 2), Fraction(3)],
        ]


class TestParseSignsList:
    """Test della funzione parse_signs_list."""

    def test_simple_signs(self):
        result = parse_signs_list('["<=", ">=", "="]')
        assert result == ["<=", ">=", "="]

    def test_single_sign(self):
        result = parse_signs_list('["<="]')
        assert result == ["<="]

    def test_invalid_sign(self):
        with pytest.raises(ValueError):
            parse_signs_list('["<"]')


class TestValidateDimensions:
    """Test della funzione validate_dimensions."""

    def test_valid_dimensions(self):
        c = [Fraction(1), Fraction(2)]
        A = [[Fraction(1), Fraction(2)], [Fraction(3), Fraction(4)]]
        signs = ["<=", "<="]
        b = [Fraction(5), Fraction(6)]

        # Non solleva eccezioni
        validate_dimensions(c, A, signs, b)

    def test_dimension_mismatch_c_a(self):
        c = [Fraction(1), Fraction(2)]
        A = [[Fraction(1), Fraction(2), Fraction(3)]]
        signs = ["<="]
        b = [Fraction(5)]

        with pytest.raises(ValueError):
            validate_dimensions(c, A, signs, b)

    def test_dimension_mismatch_b(self):
        c = [Fraction(1), Fraction(2)]
        A = [[Fraction(1), Fraction(2)], [Fraction(3), Fraction(4)]]
        signs = ["<=", "<="]
        b = [Fraction(5)]

        with pytest.raises(ValueError):
            validate_dimensions(c, A, signs, b)

    def test_dimension_mismatch_signs(self):
        c = [Fraction(1), Fraction(2)]
        A = [[Fraction(1), Fraction(2)], [Fraction(3), Fraction(4)]]
        signs = ["<="]
        b = [Fraction(5), Fraction(6)]

        with pytest.raises(ValueError):
            validate_dimensions(c, A, signs, b)


class TestParseProblem:
    """Test della funzione parse_problem."""

    def test_simple_problem(self):
        text = """min
c = [3, 4, 6]
A = [
  [1, 3, 4],
  [2, 1, 3]
]
signs = ["=", "="]
b = [1, 2]
"""
        problem = parse_problem(text)

        assert problem.sense == "min"
        assert problem.c == [Fraction(3), Fraction(4), Fraction(6)]
        assert len(problem.A) == 2
        assert len(problem.var_names) == 3
        assert problem.b == [Fraction(1), Fraction(2)]
        assert problem.signs == ["=", "="]

    def test_max_problem(self):
        text = """max
c = [1, 2]
A = [[1, 1]]
signs = ["<="]
b = [10]
"""
        problem = parse_problem(text)
        assert problem.sense == "max"

    def test_missing_sense(self):
        text = """c = [1, 2]
A = [[1, 1]]
signs = ["<="]
b = [10]
"""
        with pytest.raises(ValueError):
            parse_problem(text)

    def test_missing_c(self):
        text = """min
A = [[1, 1]]
signs = ["<="]
b = [10]
"""
        with pytest.raises(ValueError):
            parse_problem(text)
