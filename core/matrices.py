"""
Operazioni su matrici con aritmetica razionale (Fraction).
"""

from fractions import Fraction
from typing import Optional


def dot(u: list[Fraction], v: list[Fraction]) -> Fraction:
    """Prodotto scalare tra due vettori."""
    if len(u) != len(v):
        raise ValueError("I vettori devono avere la stessa lunghezza")
    return sum(u[i] * v[i] for i in range(len(u)))


def matrix_vector_mul(A: list[list[Fraction]], v: list[Fraction]) -> list[Fraction]:
    """Prodotto fra matrice e vettore: A @ v"""
    if len(A) == 0:
        return []
    if len(v) == 0:
        return []
    if len(A[0]) != len(v):
        raise ValueError(
            f"Dimensioni incompatibili: matrice {len(A)}x{len(A[0])}, vettore {len(v)}"
        )
    return [dot(A[i], v) for i in range(len(A))]


def matrix_matrix_mul(
    A: list[list[Fraction]], B: list[list[Fraction]]
) -> list[list[Fraction]]:
    """Prodotto fra matrici: A @ B"""
    if len(A) == 0 or len(B) == 0:
        return []
    if len(A[0]) != len(B):
        raise ValueError(
            f"Dimensioni incompatibili: prima matrice ha {len(A[0])} colonne, "
            f"seconda ha {len(B)} righe"
        )

    rows_A = len(A)
    cols_A = len(A[0])
    cols_B = len(B[0]) if len(B) > 0 else 0

    result = [[Fraction(0) for _ in range(cols_B)] for _ in range(rows_A)]

    for i in range(rows_A):
        for j in range(cols_B):
            for k in range(cols_A):
                result[i][j] += A[i][k] * B[k][j]

    return result


def matrix_transpose(A: list[list[Fraction]]) -> list[list[Fraction]]:
    """Trasposizione di una matrice."""
    if len(A) == 0:
        return []
    rows = len(A)
    cols = len(A[0]) if rows > 0 else 0
    return [[A[i][j] for i in range(rows)] for j in range(cols)]


def matrix_inverse(M: list[list[Fraction]]) -> list[list[Fraction]]:
    """
    Calcola l'inversa di una matrice usando l'algoritmo di Gauss-Jordan.
    La matrice deve essere quadrata e invertibile.
    """
    n = len(M)
    if n == 0:
        raise ValueError("Matrice vuota")

    # Verifica che sia quadrata
    for row in M:
        if len(row) != n:
            raise ValueError("La matrice deve essere quadrata")

    # Crea la matrice aumentata [M | I]
    augmented = []
    for i in range(n):
        row = [Fraction(M[i][j]) for j in range(n)]
        for j in range(n):
            row.append(Fraction(1) if i == j else Fraction(0))
        augmented.append(row)

    # Gauss-Jordan
    for i in range(n):
        # Trova il pivot (elemento non nullo nella colonna i)
        pivot_row = -1
        for k in range(i, n):
            if augmented[k][i] != 0:
                pivot_row = k
                break

        if pivot_row == -1:
            raise ValueError("La matrice non è invertibile (determinante = 0)")

        # Scambia le righe i e pivot_row
        augmented[i], augmented[pivot_row] = augmented[pivot_row], augmented[i]

        # Normalizza la riga i
        pivot = augmented[i][i]
        for j in range(2 * n):
            augmented[i][j] /= pivot

        # Azzera tutti gli elementi nella colonna i al di fuori della riga i
        for k in range(n):
            if k != i and augmented[k][i] != 0:
                factor = augmented[k][i]
                for j in range(2 * n):
                    augmented[k][j] -= factor * augmented[i][j]

    # Estrae l'inversa (parte destra della matrice aumentata)
    inverse = []
    for i in range(n):
        inverse.append(augmented[i][n:])

    return inverse


def matrix_inverse_safe(M: list[list[Fraction]]) -> Optional[list[list[Fraction]]]:
    """
    Calcola l'inversa di una matrice. Restituisce None se la matrice non è invertibile.
    """
    try:
        return matrix_inverse(M)
    except ValueError:
        return None


def extract_submatrix(
    A: list[list[Fraction]], basis_cols: list[int]
) -> list[list[Fraction]]:
    """
    Estrae una submatrice dalle colonne specificate.
    
    Args:
        A: matrice originale
        basis_cols: lista di indici di colonna
    
    Returns:
        Matrice formata dalle colonne specificate
    """
    if len(A) == 0:
        return []

    submatrix = []
    for row in A:
        new_row = [row[j] for j in basis_cols]
        submatrix.append(new_row)

    return submatrix


def extract_non_basis_submatrix(
    A: list[list[Fraction]], basis_cols: list[int]
) -> list[list[Fraction]]:
    """
    Estrae una submatrice dalle colonne NON in base.
    
    Args:
        A: matrice originale
        basis_cols: lista di indici di colonna in base
    
    Returns:
        Matrice formata dalle colonne non in base
    """
    if len(A) == 0:
        return []

    num_cols = len(A[0]) if len(A) > 0 else 0
    non_basis_cols = [j for j in range(num_cols) if j not in basis_cols]

    return extract_submatrix(A, non_basis_cols)


def normalize_row(row: list[Fraction], pivot_col: int) -> list[Fraction]:
    """
    Normalizza una riga dividendo per l'elemento pivot.
    
    Args:
        row: riga da normalizzare
        pivot_col: indice della colonna pivot
    
    Returns:
        Riga normalizzata
    """
    pivot = row[pivot_col]
    if pivot == 0:
        raise ValueError(f"Elemento pivot è zero nella colonna {pivot_col}")

    return [row[j] / pivot for j in range(len(row))]


def eliminate_column(
    tableau: list[list[Fraction]],
    pivot_row: int,
    pivot_col: int,
    normalized_pivot_row: list[Fraction],
) -> list[list[Fraction]]:
    """
    Elimina una colonna da un tableau usando la riga pivot normalizzata.
    
    Args:
        tableau: matrice del tableau
        pivot_row: indice della riga pivot
        pivot_col: indice della colonna pivot
        normalized_pivot_row: riga pivot già normalizzata
    
    Returns:
        Tableau con la colonna eliminata
    """
    new_tableau = [row[:] for row in tableau]

    for i in range(len(new_tableau)):
        if i != pivot_row:
            factor = new_tableau[i][pivot_col]
            for j in range(len(new_tableau[i])):
                new_tableau[i][j] -= factor * normalized_pivot_row[j]

    # Sostituisci la riga pivot
    new_tableau[pivot_row] = normalized_pivot_row

    return new_tableau


def is_feasible(b: list[Fraction]) -> bool:
    """Controlla se tutti i termini noti sono >= 0."""
    return all(x >= 0 for x in b)


def is_zero_row(row: list[Fraction], tolerance: int = 10) -> bool:
    """
    Controlla se una riga è praticamente zero.
    (Utile per rilevare vincoli ridondanti dopo manipolazioni.)
    """
    for x in row:
        if x != 0:
            return False
    return True


def get_column(A: list[list[Fraction]], col_idx: int) -> list[Fraction]:
    """Estrae una colonna dalla matrice."""
    return [row[col_idx] for row in A]


def set_column(A: list[list[Fraction]], col_idx: int, col: list[Fraction]) -> None:
    """Modifica una colonna della matrice in place."""
    if len(col) != len(A):
        raise ValueError("La lunghezza della colonna non corrisponde al numero di righe")
    for i in range(len(A)):
        A[i][col_idx] = col[i]
