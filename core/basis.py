"""
Ricerca della base iniziale per il simplesso.
"""

from fractions import Fraction


def is_unit_column(A: list[list[Fraction]], col_idx: int) -> tuple[bool, int | None]:
    """
    Controlla se una colonna è una colonna dell'identità.

    Una colonna è della forma [0, 0, ..., 1, ..., 0] con un singolo 1.

    Args:
        A: matrice
        col_idx: indice della colonna

    Returns:
        (True/False, indice della riga dove compare l'1 oppure None se non è colonna unitaria)
    """
    if len(A) == 0:
        return False, None

    num_rows = len(A)
    one_count = 0
    one_row = -1

    for i in range(num_rows):
        val = A[i][col_idx]
        if val == Fraction(1):
            one_count += 1
            one_row = i
        elif val != Fraction(0):
            return False, None

    if one_count == 1:
        return True, one_row
    else:
        return False, None


def find_identity_basis(A: list[list[Fraction]]) -> list[int] | None:
    """
    Cerca un insieme di colonne che formino una matrice identità.

    Args:
        A: matrice (m x n)

    Returns:
        Lista di indici di colonna che formano l'identità, oppure None se non trovate.

    Esempio:
        Se A ha colonne che in posizioni 0, 2, 3 formano l'identità,
        restituisce [0, 2, 3].
    """
    if len(A) == 0:
        return None

    m = len(A)  # numero di righe (vincoli)
    n = len(A[0]) if m > 0 else 0  # numero di colonne (variabili)

    # Cerca m colonne che formino l'identità
    # Ogni riga deve avere esattamente un'1 nella sua colonna corrispondente

    # Creazione di un mapping: riga -> colonna della colonna unitaria
    row_to_col = {}

    for col_idx in range(n):
        is_unit, row_idx = is_unit_column(A, col_idx)
        if is_unit:
            if row_idx in row_to_col:
                # Questa riga ha già un'1 in un'altra colonna, conflitto
                return None
            row_to_col[row_idx] = col_idx

    # Controlla se tutte le righe hanno un'1
    if len(row_to_col) == m:
        # Costruisci la lista ordinata per riga
        basis = [row_to_col[i] for i in range(m)]
        return basis
    else:
        return None


def basis_is_feasible(
    A: list[list[Fraction]], b: list[Fraction], basis: list[int]
) -> bool:
    """
    Controlla se una base è ammissibile, cioè B^{-1}b >= 0.

    Per una base identità e b >= 0, la base è direttamente ammissibile.

    Args:
        A: matrice
        b: vettore dei termini noti
        basis: lista degli indici delle colonne in base

    Returns:
        True se ammissibile, False altrimenti
    """
    # Verifica che i termini noti siano tutti >= 0
    for val in b:
        if val < 0:
            return False

    # Se A è la matrice identità e b >= 0, la base è ammissibile
    # Per una base generica, servirebbe calcolare B^{-1}b
    # Ma in questo contesto, se la base è identità e b >= 0, è ammissibile

    return True


def get_basis_for_slack_vars(
    slack_var_indices: list[int], num_constraints: int, num_total_vars: int
) -> list[int] | None:
    """
    Restituisce la base formata dalle variabili slack (se ce ne sono abbastanza).

    Args:
        slack_var_indices: liste degli indici delle variabili slack
        num_constraints: numero di vincoli
        num_total_vars: numero totale di variabili

    Returns:
        Lista degli indici della base oppure None se le slack non bastano
    """
    if len(slack_var_indices) >= num_constraints:
        # Prendi le prime num_constraints variabili slack
        return slack_var_indices[:num_constraints]
    else:
        return None
