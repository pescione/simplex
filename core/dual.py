"""
Trasformazione di un problema in forma duale e costruzione del tableau per il simplesso duale.

Teoria:
    Problema primale: min c^T x, Ax ≥ b, x ≥ 0
    Problema duale:   max b^T y, A^T y ≤ c, y ≥ 0
    
    Nel caso standard (con =):
    Primale: min c^T x, Ax = b, x ≥ 0
    Duale:   max b^T y, A^T y ≤ c (y senza vincoli di segno)

L'idea del simplesso duale è di partire dal tableau primale con:
- Costi ridotti ≥ 0 (ottimalità duale)
- RHS potenzialmente negativa (inammissibilità primale)
E iterare fino a trovare una soluzione primale ammissibile (e quindi ottimale).
"""

from fractions import Fraction
from .models import LinearProblem, StandardProblem, Tableau, Step
from .tableau import build_canonical_tableau, get_rhs_values


def compute_dual_problem(problem: LinearProblem) -> tuple[LinearProblem, list[Step]]:
    """
    Trasforma un problema primale nel suo duale.

    Convenzioni usate:
    - Le variabili non elencate in problem.free_vars sono considerate >= 0.
    - Un vincolo primale '=' genera una variabile duale libera.
    - Una variabile primale libera genera un vincolo duale '='.
    - Un vincolo primale con verso opposto genera una variabile duale <= 0,
      rappresentata tramite cambio di segno: y = -y_neg, con y_neg >= 0.
    """

    steps = []

    m = len(problem.b)      # numero vincoli primali = numero variabili duali
    n = len(problem.c)      # numero variabili primali = numero vincoli duali

    primal_free_vars = set(getattr(problem, "free_vars", []))

    if problem.sense == "max":
        dual_sense = "min"
        default_dual_constraint_sign = ">="
    elif problem.sense == "min":
        dual_sense = "max"
        default_dual_constraint_sign = "<="
    else:
        raise ValueError(f"Senso problema non riconosciuto: {problem.sense}")

    transformed_rows = []
    dual_c = []
    dual_var_names = []
    dual_free_vars = []

    for i in range(m):
        sign = problem.signs[i]
        row = list(problem.A[i])
        b_i = problem.b[i]

        y_name = f"y_{i + 1}"

        if sign == "=":
            # Vincolo primale di uguaglianza:
            # la variabile duale corrispondente è libera.
            multiplier = Fraction(1)
            dual_var_name = y_name
            dual_free_vars.append(dual_var_name)

        elif problem.sense == "max":
            # Primale max:
            # vincolo <=  => y_i >= 0
            # vincolo >=  => y_i <= 0, quindi y_i = -y_i_neg
            if sign == "<=":
                multiplier = Fraction(1)
                dual_var_name = y_name
            elif sign == ">=":
                multiplier = Fraction(-1)
                dual_var_name = f"{y_name}_neg"
            else:
                raise ValueError(f"Segno vincolo non supportato: {sign}")

        else:
            # Primale min:
            # vincolo >=  => y_i >= 0
            # vincolo <=  => y_i <= 0, quindi y_i = -y_i_neg
            if sign == ">=":
                multiplier = Fraction(1)
                dual_var_name = y_name
            elif sign == "<=":
                multiplier = Fraction(-1)
                dual_var_name = f"{y_name}_neg"
            else:
                raise ValueError(f"Segno vincolo non supportato: {sign}")

        transformed_rows.append([multiplier * a for a in row])
        dual_c.append(multiplier * b_i)
        dual_var_names.append(dual_var_name)

    # A_dual = A^T, dopo eventuali cambi di segno per variabili duali <= 0
    dual_A = [
        [transformed_rows[i][j] for i in range(m)]
        for j in range(n)
    ]

    # RHS dei vincoli duali = coefficienti dell'obiettivo primale
    dual_b = list(problem.c)

    # Ogni variabile primale genera un vincolo duale.
    # Se x_j è libera, il vincolo duale corrispondente è '='.
    dual_signs = []
    for j in range(n):
        primal_var_name = problem.var_names[j]

        if primal_var_name in primal_free_vars:
            dual_signs.append("=")
        else:
            dual_signs.append(default_dual_constraint_sign)

    dual_problem = LinearProblem(
        sense=dual_sense,
        c=dual_c,
        A=dual_A,
        signs=dual_signs,
        b=dual_b,
        var_names=dual_var_names,
        free_vars=dual_free_vars,
    )

    step = Step(
        title="Problema duale calcolato",
        description=(
            f"Problema primale ({problem.sense}) trasformato "
            f"nel suo duale ({dual_sense})."
        ),
        notes=[
            f"Variabili primali: {n}",
            f"Vincoli primali: {m}",
            f"Variabili duali: {m}",
            f"Vincoli duali: {n}",
            f"Variabili duali libere: {dual_free_vars}",
            f"Senso duale: {dual_sense}",
        ],
    )
    steps.append(step)

    return dual_problem, steps

def can_use_dual_simplex(standard_problem: StandardProblem) -> bool:
    """
    Determina se il problema può essere risolto direttamente con il simplesso duale.
    
    Il simplesso duale è applicabile se il tableau può essere inizializzato con:
    - Costi ridotti ≥ 0 (condizione di ottimalità duale)
    - RHS potenzialmente negativa (ammissibilità primale non richiesta)
    
    In pratica, possiamo sempre riportare il tableau a questa forma se esiste
    una base iniziale, quindi il simplesso duale è sempre un'opzione alternativa.
    
    Args:
        standard_problem: problema in forma standard
        
    Returns:
        True se il simplesso duale è una scelta ragionevole
    """
    # Per ora, sempre True: il simplesso duale è sempre un'alternativa valida
    return True


def identify_dual_infeasibility(
    standard_problem: StandardProblem,
) -> list[Step]:
    """
    Identifica quali RHS sono negativi (inammissibilità primale = ottimalità duale).
    
    Args:
        standard_problem: problema in forma standard
        
    Returns:
        lista di step descrittivi
    """
    steps = []
    
    negative_indices = [i for i, b_val in enumerate(standard_problem.b) if b_val < 0]
    
    if negative_indices:
        notes = [
            f"Vincoli con RHS negativa (indici): {negative_indices}",
            f"Numero: {len(negative_indices)}",
        ]
        step = Step(
            title="Inammissibilità primale rilevata",
            description="Trovati vincoli con termine noto negativo. Il simplesso duale è applicabile.",
            notes=notes,
        )
        steps.append(step)
    
    return steps
