"""
Test per l'operazione di pivot.
"""

import pytest
from fractions import Fraction
from core.tableau import build_canonical_tableau
from core.pivot import pivot


class TestPivot:
    """Test dell'operazione di pivot."""

    def test_simple_pivot(self):
        """Test un semplice pivot."""
        A = [
            [Fraction(1), Fraction(0), Fraction(1)],
            [Fraction(0), Fraction(1), Fraction(1)],
        ]
        b = [Fraction(4), Fraction(3)]
        c = [Fraction(-2), Fraction(-3), Fraction(0)]
        basis = [0, 1]
        var_names = ["x1", "x2", "s1"]

        tableau = build_canonical_tableau(A, b, c, basis, var_names)

        # Effettua un pivot: x1 entra, x1 esce (no, questo non ha senso)
        # Proviamo: s1 (indice 2) entra, x1 (indice 0 in base, riga 0) esce
        new_tableau = pivot(tableau, 0, 2)

        assert new_tableau.basis == [2, 1]
        assert len(new_tableau.data) == 3

    def test_pivot_updates_basis(self):
        """Test che il pivot aggiorna la base correttamente."""
        A = [
            [Fraction(1), Fraction(1), Fraction(1)],
            [Fraction(1), Fraction(1), Fraction(0)],
        ]
        b = [Fraction(5), Fraction(2)]
        c = [Fraction(-1), Fraction(-1), Fraction(0)]
        basis = [2, 1]  # s1 e x2 in base. Matrice B = [[1,1],[0,1]], det = 1
        var_names = ["x1", "x2", "s1"]

        tableau = build_canonical_tableau(A, b, c, basis, var_names)

        # x1 entra in base, x2 esce
        new_tableau = pivot(tableau, 1, 0)

        assert new_tableau.basis == [2, 0]

    def test_pivot_zero_element(self):
        """Test che il pivot fallisce con elemento pivot zero."""
        A = [
            [Fraction(1), Fraction(0)],
            [Fraction(0), Fraction(1)],
        ]
        b = [Fraction(5), Fraction(3)]
        c = [Fraction(-1), Fraction(-1)]
        basis = [0, 1]
        var_names = ["x1", "x2"]

        tableau = build_canonical_tableau(A, b, c, basis, var_names)

        # Prova a fare pivot su elemento zero
        with pytest.raises(ValueError):
            pivot(tableau, 1, 0)  # Elemento (2,0) nel tableau è 0

    def test_pivot_normalization(self):
        """Test che il pivot normalizza la riga pivot."""
        A = [
            [Fraction(2), Fraction(0), Fraction(1)],
            [Fraction(0), Fraction(1), Fraction(0)],
        ]
        b = [Fraction(4), Fraction(3)]
        c = [Fraction(-1), Fraction(-1), Fraction(0)]
        basis = [0, 1]
        var_names = ["x1", "x2", "s1"]

        tableau = build_canonical_tableau(A, b, c, basis, var_names)

        # Effettua pivot
        new_tableau = pivot(tableau, 0, 2)

        # La riga del pivot dovrebbe essere normalizzata
        # L'elemento (1, 2) dovrebbe essere 1
        assert new_tableau.data[1][2] == Fraction(1)
