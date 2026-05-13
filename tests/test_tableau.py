"""
Test per la costruzione del tableau.
"""

import pytest
from fractions import Fraction
from core.tableau import build_canonical_tableau, get_reduced_costs, get_rhs_values
from core.models import Tableau


class TestBuildCanonicalTableau:
    """Test della funzione build_canonical_tableau."""

    def test_simple_identity_basis(self):
        """Test con base identità."""
        A = [
            [Fraction(1), Fraction(0), Fraction(2)],
            [Fraction(0), Fraction(1), Fraction(3)],
        ]
        b = [Fraction(4), Fraction(5)]
        c = [Fraction(1), Fraction(2), Fraction(3)]
        basis = [0, 1]
        var_names = ["x1", "x2", "x3"]

        tableau = build_canonical_tableau(A, b, c, basis, var_names)

        assert isinstance(tableau, Tableau)
        assert len(tableau.data) == 3  # 1 riga obiettivo + 2 vincoli
        assert tableau.basis == basis
        assert tableau.objective_name == "z"
        assert tableau.phase == 2

    def test_tableau_values_identity(self):
        """Test che i valori nel tableau siano corretti."""
        A = [
            [Fraction(1), Fraction(0), Fraction(1)],
            [Fraction(0), Fraction(1), Fraction(-1)],
        ]
        b = [Fraction(10), Fraction(5)]
        c = [Fraction(2), Fraction(3), Fraction(0)]
        basis = [0, 1]
        var_names = ["x1", "x2", "s1"]

        tableau = build_canonical_tableau(A, b, c, basis, var_names)

        # Controlla i costi ridotti (riga 0)
        reduced_costs = get_reduced_costs(tableau)
        # Per la variabile s1 (colonna 2):
        # c_reduced = c[2] - [c_B]^T * B^{-1} * A[:, 2]
        # = 0 - [2, 3]^T · [1, -1]^T = 0 - (2*1 + 3*(-1)) = 0 - (-1) = 1
        assert reduced_costs[2] == Fraction(1)

        # Controlla i termini noti (RHS)
        rhs = get_rhs_values(tableau)
        assert rhs == [Fraction(10), Fraction(5)]

    def test_singular_matrix(self):
        """Test con matrice singolare."""
        A = [
            [Fraction(1), Fraction(2)],
            [Fraction(2), Fraction(4)],  # Riga proporzionale
        ]
        b = [Fraction(5), Fraction(10)]
        c = [Fraction(1), Fraction(2)]
        basis = [0, 1]
        var_names = ["x1", "x2"]

        with pytest.raises(ValueError):
            build_canonical_tableau(A, b, c, basis, var_names)

    def test_basis_dimension_mismatch(self):
        """Test con dimensione di base scorretta."""
        A = [[Fraction(1), Fraction(0)], [Fraction(0), Fraction(1)]]
        b = [Fraction(5), Fraction(3)]
        c = [Fraction(1), Fraction(2)]
        basis = [0]  # Dovrebbero esserci 2 elementi
        var_names = ["x1", "x2"]

        with pytest.raises(ValueError):
            build_canonical_tableau(A, b, c, basis, var_names)


class TestGetReducedCosts:
    """Test della funzione get_reduced_costs."""

    def test_get_reduced_costs(self):
        """Test estrazione dei costi ridotti."""
        A = [
            [Fraction(1), Fraction(0), Fraction(1)],
            [Fraction(0), Fraction(1), Fraction(-1)],
        ]
        b = [Fraction(10), Fraction(5)]
        c = [Fraction(1), Fraction(2), Fraction(0)]
        basis = [0, 1]
        var_names = ["x1", "x2", "s1"]

        tableau = build_canonical_tableau(A, b, c, basis, var_names)
        reduced_costs = get_reduced_costs(tableau)

        assert len(reduced_costs) == 3


class TestGetRhsValues:
    """Test della funzione get_rhs_values."""

    def test_get_rhs_values(self):
        """Test estrazione dei termini noti."""
        A = [
            [Fraction(1), Fraction(0), Fraction(1)],
            [Fraction(0), Fraction(1), Fraction(-1)],
        ]
        b = [Fraction(10), Fraction(5)]
        c = [Fraction(1), Fraction(2), Fraction(0)]
        basis = [0, 1]
        var_names = ["x1", "x2", "s1"]

        tableau = build_canonical_tableau(A, b, c, basis, var_names)
        rhs = get_rhs_values(tableau)

        assert rhs == b
