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

    Convenzione del tableau:
        - riga 0: costi ridotti delle non-basiche, ultimo elemento = -valore_obiettivo
        - riga i+1 (i >= 0): coefficienti di B^{-1}A, ultimo elemento = RHS

    La convenzione usata è: tableau.data[0][-1] = -z (il negativo del valore obiettivo).
    Usa get_objective_value() per ottenere il valore dell'obiettivo con il segno corretto.

    Forma del tableau:
        c_F^T - c_B^T B^{-1}A_F  | -c_B^T B^{-1}b
        B^{-1}A_F                 | B^{-1}b

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
    # Se la base è singolare, solleva un errore.
    # Non tentare di trovare una base alternativa: la funzione build_canonical_tableau
    # deve essere deterministica e rispettare la base ricevuta.
    try:
        B_inv = matrix_inverse(B)
    except ValueError as e:
        raise ValueError(
            f"La base fornita è singolare e non invertibile. "
            f"Indici di base: {basis}. Errore interno: {str(e)}"
        )

    # Estrai vettori di costi per base e non-base
    c_B = [c[j] for j in basis]
    c_B_vect = [[c[j]] for j in basis]  # colonna

    # Calcola B^{-1}b
    b_canonical = matrix_vector_mul(B_inv, b)

    # Calcola B^{-1}A (tutte le colonne del tableau)
    B_inv_A = matrix_matrix_mul(B_inv, A)

    # Calcola i costi ridotti
    # c_j^red = c_j - c_B^T B^{-1}A_j per ogni j
    # NOTA: I costi ridotti sono calcolati ESATTAMENTE secondo la formula matematica.
    # L'euristica di forzare a 0 i costi ridotti delle slack è SBAGLIATA e rimossa.
    # Una slack può avere costo ridotto diverso da 0 dopo pivot su altre variabili.
    reduced_costs = []
    for j in range(n):
        red_cost = c[j]
        for i in range(m):
            # B_inv_A[i][j] è l'i-esimo elemento di B^{-1}A_j
            red_cost -= c_B[i] * B_inv_A[i][j]
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
    """
    Estrae il valore della funzione obiettivo dal tableau.
    
    Nota sulla convenzione: nel tableau, l'ultima colonna della riga 0 contiene
    -z (il negativo del valore dell'obiettivo). Questa funzione ritorna z (il valore positivo).
    
    Returns:
        Il valore della funzione obiettivo (con segno corretto, ovvero -tableau.data[0][-1])
    """
    return -tableau.data[0][-1]


def get_raw_objective_rhs(tableau: Tableau) -> Fraction:
    """
    Estrae il valore RAW dell'RHS della riga obiettivo dal tableau.
    
    Questo è il valore memorizzato direttamente nel tableau, che è -z (negativo).
    Usa get_objective_value() se vuoi il valore con segno corretto.
    
    Returns:
        Il valore grezzo memorizzato: -z
    """
    return tableau.data[0][-1]


def get_column_values(tableau: Tableau, col_idx: int) -> list[Fraction]:
    """Estrae i valori di una colonna nel tableau (escludendo la riga 0)."""
    return [row[col_idx] for row in tableau.data[1:]]
