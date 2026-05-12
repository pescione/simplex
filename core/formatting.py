"""
Funzioni di formattazione per la visualizzazione dei dati in Streamlit.
"""

import pandas as pd
from fractions import Fraction
from .models import Tableau


def fraction_to_str(x: Fraction) -> str:
    """
    Converte una Fraction in stringa leggibile.

    Esempi:
        1/1 → "1"
        1/2 → "1/2"
        -3/4 → "-3/4"
    """
    if x.denominator == 1:
        return str(x.numerator)
    else:
        return f"{x.numerator}/{x.denominator}"


def tableau_to_dataframe(tableau: Tableau) -> pd.DataFrame:
    """
    Converte un tableau del simplesso in un pandas DataFrame.

    Formato:
        Base | x1 | x2 | ... | xn | RHS
        z    | c1 | c2 | ... | cn | obj_val
        v1   | a11| a12| ... | a1n| b1
        v2   | a21| a22| ... | a2n| b2
        ...

    Args:
        tableau: tableau da convertire

    Returns:
        DataFrame formattato
    """
    if not tableau.data:
        return pd.DataFrame()

    # Crea il dizionario dei dati
    data = {}

    # Colonna "Base"
    base_names = [tableau.objective_name] + [
        tableau.var_names[tableau.basis[i]] for i in range(len(tableau.basis))
    ]
    data["Base"] = base_names

    # Colonne per ogni variabile
    num_cols = len(tableau.data[0]) - 1  # Escludiamo l'ultima colonna (RHS)

    for j in range(num_cols):
        col_name = tableau.var_names[j] if j < len(tableau.var_names) else f"x{j + 1}"
        col_values = [fraction_to_str(row[j]) for row in tableau.data]
        data[col_name] = col_values

    # Colonna "RHS" (Right-Hand Side)
    rhs_values = [fraction_to_str(row[-1]) for row in tableau.data]
    data["RHS"] = rhs_values

    # Crea il DataFrame
    df = pd.DataFrame(data)

    return df


def linear_problem_to_display(problem) -> str:
    """
    Formatta un problema lineare per la visualizzazione.

    Args:
        problem: oggetto LinearProblem

    Returns:
        Stringa formattata
    """
    lines = []
    lines.append(f"{problem.sense}imizza")

    # Funzione obiettivo
    obj_terms = []
    for i, (var, coeff) in enumerate(zip(problem.var_names, problem.c)):
        if coeff == 0:
            continue
        sign = "+" if coeff > 0 and i > 0 else ""
        obj_terms.append(f"{sign} {fraction_to_str(coeff)} {var}")

    lines.append("c^T x = " + " ".join(obj_terms))
    lines.append("")

    # Vincoli
    lines.append("Soggetto a:")
    for i, (sign, b_val) in enumerate(zip(problem.signs, problem.b)):
        constraint_terms = []
        for var, coeff in zip(problem.var_names, problem.A[i]):
            if coeff == 0:
                continue
            sign_char = "+" if coeff > 0 and len(constraint_terms) > 0 else ""
            constraint_terms.append(f"{sign_char} {fraction_to_str(coeff)} {var}")

        constraint_str = " ".join(constraint_terms)
        lines.append(f"  {constraint_str} {sign} {fraction_to_str(b_val)}")

    lines.append("")
    lines.append("x ≥ 0")

    return "\n".join(lines)


def solution_to_table(solution: dict, var_names: list[str]) -> pd.DataFrame:
    """
    Converte una soluzione in un DataFrame.

    Args:
        solution: dizionario {nome_var: valore}
        var_names: lista dei nomi delle variabili

    Returns:
        DataFrame con le colonne "Variabile" e "Valore"
    """
    data = {
        "Variabile": [],
        "Valore": [],
    }

    for var in var_names:
        if var in solution:
            data["Variabile"].append(var)
            data["Valore"].append(fraction_to_str(solution[var]))

    return pd.DataFrame(data)
