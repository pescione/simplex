"""
Test per la ricerca della base iniziale.
"""

import pytest
from fractions import Fraction
from core.basis import is_unit_column, find_identity_basis, basis_is_feasible


class TestIsUnitColumn:
    """Test della funzione is_unit_column."""

    def test_unit_column_first(self):
        A = [
            [Fraction(1), Fraction(0)],
            [Fraction(0), Fraction(1)],
        ]
        is_unit, row_idx = is_unit_column(A, 0)
        assert is_unit is True
        assert row_idx == 0

    def test_unit_column_second(self):
        A = [
            [Fraction(1), Fraction(0)],
            [Fraction(0), Fraction(1)],
        ]
        is_unit, row_idx = is_unit_column(A, 1)
        assert is_unit is True
        assert row_idx == 1

    def test_not_unit_column(self):
        # Testa che una colonna con due 1 non è una unit column
        A = [
            [Fraction(1), Fraction(1)],
            [Fraction(1), Fraction(1)],
        ]
        is_unit, row_idx = is_unit_column(A, 0)
        assert is_unit is False
        assert row_idx is None

    def test_not_unit_multiple_ones(self):
        A = [
            [Fraction(1), Fraction(0)],
            [Fraction(1), Fraction(0)],
        ]
        is_unit, row_idx = is_unit_column(A, 0)
        assert is_unit is False
        assert row_idx is None

    def test_not_unit_nonzero_element(self):
        A = [
            [Fraction(1), Fraction(0)],
            [Fraction(2), Fraction(1)],
        ]
        is_unit, row_idx = is_unit_column(A, 0)
        assert is_unit is False
        assert row_idx is None


class TestFindIdentityBasis:
    """Test della funzione find_identity_basis."""

    def test_identity_basis_found(self):
        A = [
            [Fraction(1), Fraction(0), Fraction(2)],
            [Fraction(0), Fraction(1), Fraction(3)],
        ]
        basis = find_identity_basis(A)
        assert basis == [0, 1]

    def test_identity_basis_reordered(self):
        A = [
            [Fraction(2), Fraction(0), Fraction(1)],
            [Fraction(3), Fraction(1), Fraction(0)],
        ]
        basis = find_identity_basis(A)
        assert basis == [2, 1]

    def test_identity_basis_not_found(self):
        A = [
            [Fraction(1), Fraction(1)],
            [Fraction(1), Fraction(0)],
        ]
        basis = find_identity_basis(A)
        assert basis is None

    def test_single_row_single_column(self):
        A = [[Fraction(1)]]
        basis = find_identity_basis(A)
        assert basis == [0]

    def test_larger_matrix(self):
        A = [
            [Fraction(1), Fraction(0), Fraction(0), Fraction(2)],
            [Fraction(0), Fraction(1), Fraction(0), Fraction(3)],
            [Fraction(0), Fraction(0), Fraction(1), Fraction(4)],
        ]
        basis = find_identity_basis(A)
        assert basis == [0, 1, 2]


class TestBasisIsFeasible:
    """Test della funzione basis_is_feasible."""

    def test_feasible_identity_basis(self):
        A = [
            [Fraction(1), Fraction(0)],
            [Fraction(0), Fraction(1)],
        ]
        b = [Fraction(5), Fraction(3)]
        basis = [0, 1]

        assert basis_is_feasible(A, b, basis) is True

    def test_infeasible_negative_b(self):
        A = [
            [Fraction(1), Fraction(0)],
            [Fraction(0), Fraction(1)],
        ]
        b = [Fraction(5), Fraction(-3)]
        basis = [0, 1]

        assert basis_is_feasible(A, b, basis) is False

    def test_feasible_zero_b(self):
        A = [
            [Fraction(1), Fraction(0)],
            [Fraction(0), Fraction(1)],
        ]
        b = [Fraction(0), Fraction(0)]
        basis = [0, 1]

        assert basis_is_feasible(A, b, basis) is True
