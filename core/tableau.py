"""
Costruzione del tableau canonico del simplesso.
"""

from fractions import Fraction
from .models import Tableau
from .matrices import (
    matrix_inverse,
    matrix_matrix_mul,
    matrix_vector_mul,
    dot,
    extract_submatrix,
    extract_non_basis_submatrix,
)


def build_canonical_tableau(
    A: list[list[Fraction]],
    b: list[Fraction],
    c: list[Fraction],
    basis: list[int],
    var_names: list[str],
    phase: int = 2,
    objective_name: str = "z",
) -> Tableau:
    """
    Costruisce il tableau canonico del simplesso rispetto a una base data.

    Forma del tableau:
        0^T         c_F^T - c_B^T B^{-1}F     | -c_B^T B^{-1}b
        I           B^{-1}F                    | B^{-1}b

    Args:
        A: matrice dei vincoli (m x n)
        b: vettore dei termini noti (m)
        c: vettore dei costi (n)
        basis: lista degli indici delle variabili in base (m elementi)
        var_names: nomi delle variabili
        phase: numero della fase (1 o 2)
        objective_name: nome della riga obiettivo ("z" o "w")

    Returns:
        Oggetto Tableau

    Raises:
        ValueError: se la base è singolare o le dimensioni sono incompatibili
    """
    m = len(A)  # numero di vincoli
    n = len(c)  # numero di variabili

    if len(basis) != m:
        raise ValueError(
            f"Numero di variabili in base ({len(basis)}) diverso da numero vincoli ({m})"
        )

    if len(b) != m:
        raise ValueError(f"Lunghezza di b ({len(b)}) diversa da numero vincoli ({m})")

    if len(c) != n:
        raise ValueError(
            f"Lunghezza di c ({len(c)}) diversa da numero variabili di A ({n})"
        )

    # Estrai la matrice di base B
    B = extract_submatrix(A, basis)

    # Calcola B^{-1}
    try:
        B_inv = matrix_inverse(B)
    except ValueError as e:
        raise ValueError(f"La matrice di base è singolare: {e}")

    # Estrai vettori di costi per base e non-base
    c_B = [c[j] for j in basis]
    c_B_vect = [[c[j]] for j in basis]  # colonna

    # Calcola B^{-1}b
    b_canonical = matrix_vector_mul(B_inv, b)

    # Calcola B^{-1}A (tutte le colonne del tableau)
    B_inv_A = matrix_matrix_mul(B_inv, A)

    # Calcola i costi ridotti
    # c_j^red = c_j - c_B^T B^{-1}A_j per ogni j
    c_B_T_B_inv = []
    for j in range(m):
        val = Fraction(0)
        for i in range(m):
            val += c_B[i] * B_inv[i][j]
        c_B_T_B_inv.append(val)

    reduced_costs = []
    for j in range(n):
        red_cost = c[j]
        for i in range(m):
            red_cost -= c_B_T_B_inv[i] * B_inv_A[i][j]
        reduced_costs.append(red_cost)

    # Calcola il valore della funzione obiettivo
    # obj_val = -c_B^T B^{-1}b
    obj_val = -dot(c_B, b_canonical)

    # Costruisci il tableau
    # Riga 0: [reduced_costs | obj_val]
    # Righe 1..m: [B_inv_A | b_canonical]

    tableau_data = []

    # Riga della funzione obiettivo (riga 0)
    obj_row = reduced_costs + [obj_val]
    tableau_data.append(obj_row)

    # Righe dei vincoli
    for i in range(m):
        constraint_row = list(B_inv_A[i]) + [b_canonical[i]]
        tableau_data.append(constraint_row)

    return Tableau(
        data=tableau_data, basis=basis, var_names=var_names, phase=phase, objective_name=objective_name
    )


def get_reduced_costs(tableau: Tableau) -> list[Fraction]:
    """Estrae i costi ridotti dalla prima riga del tableau."""
    if len(tableau.data) == 0:
        return []
    # L'ultima colonna è il termine noto, quindi escludila
    return tableau.data[0][:-1]


def get_rhs_values(tableau: Tableau) -> list[Fraction]:
    """Estrae i termini noti dal tableau (ultima colonna, escludendo la riga 0)."""
    return [row[-1] for row in tableau.data[1:]]


def get_objective_value(tableau: Tableau) -> Fraction:
    """Estrae il valore della funzione obiettivo dal tableau."""
    return tableau.data[0][-1]


def get_column_values(tableau: Tableau, col_idx: int) -> list[Fraction]:
    """Estrae i valori di una colonna nel tableau (escludendo la riga 0)."""
    return [row[col_idx] for row in tableau.data[1:]]
