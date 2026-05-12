"""
Test per il metodo delle due fasi.
"""

import pytest
from fractions import Fraction
from core.models import StandardProblem
from core.two_phase import build_artificial_problem


class TestBuildArtificialProblem:
    """Test della funzione build_artificial_problem."""

    def test_artificial_problem_structure(self):
        """Test che il problema artificiale abbia la struttura corretta."""
        std = StandardProblem(
            c=[Fraction(1), Fraction(2), Fraction(3)],
            A=[
                [Fraction(1), Fraction(0), Fraction(1)],
                [Fraction(0), Fraction(1), Fraction(1)],
            ],
            b=[Fraction(5), Fraction(4)],
            var_names=["x1", "x2", "x3"],
            original_var_count=3,
            slack_vars=[],
            surplus_vars=[],
            artificial_vars=[],
            constraint_auxiliary_var=[-1, -1],  # Entrambi i vincoli sono "="
        )

        artificial_prob, artificial_indices, steps = build_artificial_problem(std)

        # Il problema artificiale dovrebbe avere 2 variabili artificiali
        assert len(artificial_indices) == 2
        assert artificial_prob.original_var_count == 3
        # Numero totale variabili: 3 originali + 2 artificiali = 5
        assert len(artificial_prob.c) == 5

    def test_artificial_objective(self):
        """Test che la funzione obiettivo sia corretta."""
        std = StandardProblem(
            c=[Fraction(1), Fraction(2)],
            A=[
                [Fraction(1), Fraction(0)],
                [Fraction(0), Fraction(1)],
            ],
            b=[Fraction(3), Fraction(2)],
            var_names=["x1", "x2"],
            original_var_count=2,
            slack_vars=[],
            surplus_vars=[],
            artificial_vars=[],
            constraint_auxiliary_var=[-1, -1],  # Entrambi i vincoli sono "="
        )

        artificial_prob, artificial_indices, steps = build_artificial_problem(std)

        # I costi originali dovrebbero rimanere gli stessi
        assert artificial_prob.c[0] == Fraction(1)
        assert artificial_prob.c[1] == Fraction(2)

        # I costi delle variabili artificiali dovrebbero essere 1
        for idx in artificial_indices:
            assert artificial_prob.c[idx] == Fraction(1)

    def test_artificial_matrix(self):
        """Test che la matrice A abbia la struttura corretta."""
        std = StandardProblem(
            c=[Fraction(1), Fraction(2)],
            A=[
                [Fraction(1), Fraction(0)],
                [Fraction(0), Fraction(1)],
            ],
            b=[Fraction(3), Fraction(2)],
            var_names=["x1", "x2"],
            original_var_count=2,
            slack_vars=[],
            surplus_vars=[],
            artificial_vars=[],
            constraint_auxiliary_var=[-1, -1],  # Entrambi i vincoli sono "="
        )

        artificial_prob, artificial_indices, steps = build_artificial_problem(std)

        # La matrice A dovrebbe avere colonne aggiuntive per le variabili artificiali
        # (identità)
        assert len(artificial_prob.A[0]) == 4  # 2 originali + 2 artificiali
        assert artificial_prob.A[0][2] == Fraction(1)  # Prima artificiale, primo vincolo
        assert artificial_prob.A[0][3] == Fraction(0)  # Seconda artificiale, primo vincolo
        assert artificial_prob.A[1][2] == Fraction(0)  # Prima artificiale, secondo vincolo
        assert artificial_prob.A[1][3] == Fraction(1)  # Seconda artificiale, secondo vincolo
