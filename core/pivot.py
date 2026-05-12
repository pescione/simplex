"""
Operazione di pivot sul tableau del simplesso.
"""

from fractions import Fraction
from .models import Tableau
from .matrices import normalize_row, eliminate_column


def pivot(tableau: Tableau, pivot_row: int, pivot_col: int) -> Tableau:
    """
    Esegue l'operazione di pivot sul tableau.

    Convenzione:
        - pivot_row: indice della riga dei vincoli (0 = prima riga dei vincoli, che è riga 1 nel tableau)
        - pivot_col: indice della colonna della variabile (0 = prima variabile)

    Algoritmo:
        1. Normalizza la riga pivot
        2. Azzera la colonna pivot in tutte le altre righe (inclusa riga 0)
        3. Aggiorna la base

    Args:
        tableau: tableau originale
        pivot_row: indice della riga del pivot (relativo ai vincoli, non al tableau completo)
        pivot_col: indice della colonna del pivot

    Returns:
        Nuovo tableau dopo il pivot

    Raises:
        ValueError: se l'elemento pivot è zero
    """
    # Converte gli indici: pivot_row relativo ai vincoli → indice assoluto nel tableau
    absolute_pivot_row = pivot_row + 1

    if absolute_pivot_row < 1 or absolute_pivot_row >= len(tableau.data):
        raise ValueError(f"Riga pivot {absolute_pivot_row} fuori dai limiti del tableau")

    if pivot_col < 0 or pivot_col >= len(tableau.data[0]) - 1:
        raise ValueError(f"Colonna pivot {pivot_col} fuori dai limiti del tableau")

    # Estrai l'elemento pivot
    pivot_element = tableau.data[absolute_pivot_row][pivot_col]

    if pivot_element == 0:
        raise ValueError(
            f"Elemento pivot è zero: riga {absolute_pivot_row}, colonna {pivot_col}"
        )

    # Crea una copia del tableau
    new_data = [row[:] for row in tableau.data]

    # Normalizza la riga pivot
    normalized_pivot_row = normalize_row(new_data[absolute_pivot_row], pivot_col)

    # Azzera la colonna pivot in tutte le altre righe
    new_data = eliminate_column(new_data, absolute_pivot_row, pivot_col, normalized_pivot_row)

    # Aggiorna la base
    new_basis = tableau.basis[:]
    new_basis[pivot_row] = pivot_col

    return Tableau(
        data=new_data,
        basis=new_basis,
        var_names=tableau.var_names,
        phase=tableau.phase,
        objective_name=tableau.objective_name,
    )


def get_entering_variable_index(pivot_col: int) -> int:
    """Restituisce l'indice della variabile che entra in base (indice della colonna)."""
    return pivot_col


def get_leaving_variable_index(tableau: Tableau, pivot_row: int) -> int:
    """Restituisce l'indice della variabile che esce dalla base."""
    return tableau.basis[pivot_row]
