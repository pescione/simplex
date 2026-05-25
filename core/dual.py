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
    
    Trasformazioni:
    - min c^T x → max b^T y
    - max c^T x → min b^T y
    - Vincoli "<=": A_i x ≤ b_i → y_i ≥ 0
    - Vincoli ">=": A_i x ≥ b_i → y_i ≤ 0
    - Vincoli "=": A_i x = b_i → y_i senza vincoli
    - Matrice A → A^T (trasposta)
    - Coefficienti c → b (termini noti)
    - Termini noti b → c (coefficienti)
    
    Args:
        problem: LinearProblem del problema primale
        
    Returns:
        (problema duale come LinearProblem, lista di step descrittivi)
    """
    steps = []
    
    m = len(problem.b)  # numero vincoli primali = numero variabili duali
    n = len(problem.c)  # numero variabili primali
    
    # Trasforma la funzione obiettivo
    # Primal: min → Dual: max (max b^T y)
    # Primal: max → Dual: min (min b^T y)
    if problem.sense == "min":
        dual_sense = "max"
        dual_c = list(problem.b)  # coefficienti = b primale
    else:  # "max"
        dual_sense = "min"
        dual_c = [-coeff for coeff in problem.b]
    
    # Trasforma la matrice (A → A^T)
    dual_A = [[problem.A[i][j] for i in range(m)] for j in range(n)]
    
    # Trasforma i termini noti (c primale → b duale)
    dual_b = list(problem.c)
    
    # Trasforma i vincoli in base ai segni
    # Primal: min c^T x
    #         A_<= x ≤ b_<= → y_<= ≥ 0
    #         A_>= x ≥ b_>= → y_>= ≤ 0
    #         A_= x = b_=  → y_= free
    # 
    # Duale: max b^T y
    #        A_<= ^T y ≤ c_<= + (slack primale)
    #        A_>= ^T y ≤ c_>= - (surplus primale) → A_>= ^T y + (surplus) ≤ c_>=
    #        A_= ^T y ≤ c_=
    #        A_= ^T y ≥ c_=
    #
    # Nel duale standard (forma min, ≤):
    # min c_dual^T y
    # A_dual y ≥ b_dual
    # y ≥ 0 per vincoli primali <=
    # y ≤ 0 per vincoli primali >=
    # y free per vincoli primali =
    
    dual_signs = []
    dual_var_names = []
    
    for i in range(m):
        if problem.signs[i] == "<=":
            # Vincolo primale ≤: variabile duale y_i ≥ 0
            # Nel duale min: A^T y ≥ b diventa >= per mantenere y ≥ 0
            dual_signs.append(">=")
            dual_var_names.append(f"y_{i+1}+")  # y ≥ 0
        elif problem.signs[i] == ">=":
            # Vincolo primale ≥: variabile duale y_i ≤ 0
            # Nel duale min: A^T y ≥ b, ma y ≤ 0
            # Equivalente: -A^T (-y) ≥ b, dove -y ≥ 0
            dual_signs.append(">=")
            dual_var_names.append(f"y_{i+1}-")  # y ≤ 0 (rappresentato come -y ≥ 0)
        else:  # "="
            # Vincolo primale =: variabile duale y_i free (≤ 0 e ≥ 0)
            # Rappresentiamo come due vincoli: uno ≥ e uno ≤
            # Per semplicità, nel duale mettiamo =
            dual_signs.append("=")
            dual_var_names.append(f"y_{i+1}")  # y free
    
    dual_problem = LinearProblem(
        sense=dual_sense,
        c=dual_c,
        A=dual_A,
        signs=dual_signs,
        b=dual_b,
        var_names=dual_var_names,
    )
    
    step = Step(
        title="Problema duale calcolato",
        description=f"Problema primale ({problem.sense}) trasformato nel suo duale ({dual_sense})",
        notes=[
            f"Variabili primali: {n}, Variabili duali: {m}",
            f"Vincoli primali: {m}, Vincoli duali: {n}",
            f"Nuovo senso: {dual_sense}",
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
