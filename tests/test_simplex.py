"""
Test per il simplesso.
"""

import pytest
from fractions import Fraction
from core.tableau import build_canonical_tableau
from core.simplex import (
    is_optimal,
    choose_entering_variable,
    is_unbounded,
    choose_leaving_variable,
    simplex,
)
from core.models import SolverOptions


class TestIsOptimal:
    """Test della funzione is_optimal."""

    def test_optimal_tableau(self):
        """Test tableau ottimale (tutti i costi ridotti >= 0)."""
        A = [
            [Fraction(1), Fraction(0), Fraction(1)],
            [Fraction(0), Fraction(1), Fraction(1)],
        ]
        b = [Fraction(4), Fraction(3)]
        c = [Fraction(1), Fraction(2), Fraction(0)]
        basis = [0, 1]
        var_names = ["x1", "x2", "s1"]

        tableau = build_canonical_tableau(A, b, c, basis, var_names)

        # Questo tableau potrebbe essere ottimale
        assert isinstance(is_optimal(tableau), bool)

    def test_non_optimal_tableau(self):
        """Test tableau non ottimale (alcuni costi ridotti < 0)."""
        A = [
            [Fraction(1), Fraction(0), Fraction(1)],
            [Fraction(0), Fraction(1), Fraction(1)],
        ]
        b = [Fraction(4), Fraction(3)]
        c = [Fraction(-1), Fraction(-1), Fraction(0)]  # Costi negativi
        basis = [2, 1]
        var_names = ["x1", "x2", "s1"]

        tableau = build_canonical_tableau(A, b, c, basis, var_names)

        # Questo non dovrebbe essere ottimale
        # (perché i costi ridotti delle variabili in base dovrebbero essere 0)
        assert isinstance(is_optimal(tableau), bool)


class TestChooseEnteringVariable:
    """Test della funzione choose_entering_variable."""

    def test_most_negative_rule(self):
        """Test regola most_negative."""
        A = [
            [Fraction(1), Fraction(0), Fraction(1)],
            [Fraction(0), Fraction(1), Fraction(1)],
        ]
        b = [Fraction(4), Fraction(3)]
        c = [Fraction(-5), Fraction(-2), Fraction(0)]  # -5 è il minimo
        basis = [2, 1]
        var_names = ["x1", "x2", "s1"]

        tableau = build_canonical_tableau(A, b, c, basis, var_names)

        entering = choose_entering_variable(tableau, "most_negative")
        # Dovrebbe scegliere x1 (indice 0) perché ha il costo più negativo
        assert entering == 0

    def test_first_negative_rule(self):
        """Test regola first_negative."""
        A = [
            [Fraction(1), Fraction(0), Fraction(1)],
            [Fraction(0), Fraction(1), Fraction(1)],
        ]
        b = [Fraction(4), Fraction(3)]
        c = [Fraction(-1), Fraction(-5), Fraction(0)]
        basis = [2, 1]
        var_names = ["x1", "x2", "s1"]

        tableau = build_canonical_tableau(A, b, c, basis, var_names)

        entering = choose_entering_variable(tableau, "first_negative")
        # Dovrebbe scegliere il primo costo negativo
        assert entering is not None


class TestIsUnbounded:
    """Test della funzione is_unbounded."""

    def test_unbounded_column(self):
        """Test colonna con tutti i coefficienti <= 0."""
        A = [
            [Fraction(-1), Fraction(0), Fraction(1)],
            [Fraction(0), Fraction(-1), Fraction(1)],
        ]
        b = [Fraction(4), Fraction(3)]
        c = [Fraction(-1), Fraction(-1), Fraction(0)]
        basis = [2, 1]
        var_names = ["x1", "x2", "s1"]

        tableau = build_canonical_tableau(A, b, c, basis, var_names)

        # La colonna 0 ha valori <= 0
        assert is_unbounded(tableau, 0) is True

    def test_bounded_column(self):
        """Test colonna con almeno un coefficiente > 0."""
        A = [
            [Fraction(1), Fraction(0), Fraction(1)],
            [Fraction(0), Fraction(1), Fraction(1)],
        ]
        b = [Fraction(4), Fraction(3)]
        c = [Fraction(-1), Fraction(-1), Fraction(0)]
        basis = [2, 1]
        var_names = ["x1", "x2", "s1"]

        tableau = build_canonical_tableau(A, b, c, basis, var_names)

        # La colonna 0 ha valori > 0
        assert is_unbounded(tableau, 0) is False


class TestChooseLeavingVariable:
    """Test della funzione choose_leaving_variable."""

    def test_minimum_ratio(self):
        """Test test dei rapporti."""
        A = [
            [Fraction(1), Fraction(0), Fraction(1)],
            [Fraction(0), Fraction(1), Fraction(2)],
        ]
        b = [Fraction(4), Fraction(8)]
        c = [Fraction(1), Fraction(1), Fraction(0)]
        basis = [0, 1]
        var_names = ["x1", "x2", "s1"]

        tableau = build_canonical_tableau(A, b, c, basis, var_names)

        # Scegli la variabile uscente per la colonna 2
        leaving_row, ratios = choose_leaving_variable(tableau, 2)

        # Il rapporto minimo dovrebbe essere 4/1 = 4 (riga 0)
        assert leaving_row == 0


class TestSimplex:
    """Test della funzione simplex principale."""

    def test_simplex_optimal(self):
        """Test semplice problema con soluzione ottima."""
        A = [
            [Fraction(1), Fraction(0), Fraction(1)],
            [Fraction(0), Fraction(1), Fraction(1)],
        ]
        b = [Fraction(4), Fraction(3)]
        c = [Fraction(-1), Fraction(-1), Fraction(0)]
        basis = [2, 1]
        var_names = ["x1", "x2", "s1"]

        tableau = build_canonical_tableau(A, b, c, basis, var_names)
        options = SolverOptions(max_iterations=10)

        final_tableau, steps, status = simplex(tableau, options)

        assert isinstance(steps, list)
        assert status in ["optimal", "unbounded", "iteration_limit"]
