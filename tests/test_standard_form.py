"""
Test per la trasformazione in forma standard.
"""

import pytest
from fractions import Fraction
from core.models import LinearProblem
from core.standard_form import to_standard_form


class TestToStandardForm:
    """Test della funzione to_standard_form."""

    def test_max_to_min(self):
        """Test trasformazione da massimizzazione a minimizzazione."""
        problem = LinearProblem(
            sense="max",
            c=[Fraction(1), Fraction(2)],
            A=[[Fraction(1), Fraction(1)]],
            signs=["<="],
            b=[Fraction(10)],
            var_names=["x1", "x2"],
        )

        std, steps = to_standard_form(problem)

        # I coefficienti di c dovrebbero essere negati
        assert std.c[0] == Fraction(-1)
        assert std.c[1] == Fraction(-2)

    def test_slack_variables(self):
        """Test aggiunta di variabili slack."""
        problem = LinearProblem(
            sense="min",
            c=[Fraction(1), Fraction(2)],
            A=[[Fraction(1), Fraction(1)]],
            signs=["<="],
            b=[Fraction(10)],
            var_names=["x1", "x2"],
        )

        std, steps = to_standard_form(problem)

        # Dovrebbe avere una variabile slack
        assert len(std.var_names) == 3  # x1, x2, s1
        assert std.var_names[2] == "s1"
        assert len(std.slack_vars) == 1

    def test_surplus_variables(self):
        """Test aggiunta di variabili surplus."""
        problem = LinearProblem(
            sense="min",
            c=[Fraction(1), Fraction(2)],
            A=[[Fraction(1), Fraction(1)]],
            signs=[">="],
            b=[Fraction(10)],
            var_names=["x1", "x2"],
        )

        std, steps = to_standard_form(problem)

        # Dovrebbe avere una variabile surplus
        assert len(std.var_names) == 3  # x1, x2, e1
        assert std.var_names[2] == "e1"
        assert len(std.surplus_vars) == 1

    def test_equality_constraints(self):
        """Test vincoli di uguaglianza."""
        problem = LinearProblem(
            sense="min",
            c=[Fraction(1), Fraction(2)],
            A=[[Fraction(1), Fraction(1)]],
            signs=["="],
            b=[Fraction(10)],
            var_names=["x1", "x2"],
        )

        std, steps = to_standard_form(problem)

        # Non dovrebbe avere variabili slack o surplus
        assert len(std.var_names) == 2
        assert len(std.slack_vars) == 0
        assert len(std.surplus_vars) == 0

    def test_mixed_constraints(self):
        """Test vincoli misti."""
        problem = LinearProblem(
            sense="min",
            c=[Fraction(1), Fraction(2), Fraction(3)],
            A=[
                [Fraction(1), Fraction(2), Fraction(3)],
                [Fraction(1), Fraction(1), Fraction(1)],
                [Fraction(2), Fraction(1), Fraction(0)],
            ],
            signs=["<=", "=", ">="],
            b=[Fraction(10), Fraction(5), Fraction(3)],
            var_names=["x1", "x2", "x3"],
        )

        std, steps = to_standard_form(problem)

        # x1, x2, x3 (originali) + s1 (slack) + e1 (surplus) = 5 variabili
        assert len(std.var_names) == 5
        assert len(std.slack_vars) == 1
        assert len(std.surplus_vars) == 1

    def test_negative_b(self):
        """Test gestione di termini noti negativi."""
        problem = LinearProblem(
            sense="min",
            c=[Fraction(1), Fraction(2)],
            A=[[Fraction(1), Fraction(1)]],
            signs=["<="],
            b=[Fraction(-10)],
            var_names=["x1", "x2"],
        )

        std, steps = to_standard_form(problem)

        # Il termine noto dovrebbe essere positivo
        assert std.b[0] == Fraction(10)

    def test_objective_value_zero(self):
        """Test con coefficienti di costo nulli."""
        problem = LinearProblem(
            sense="min",
            c=[Fraction(0), Fraction(0)],
            A=[[Fraction(1), Fraction(1)]],
            signs=["<="],
            b=[Fraction(10)],
            var_names=["x1", "x2"],
        )

        std, steps = to_standard_form(problem)

        assert std.c == [Fraction(0), Fraction(0), Fraction(0)]
