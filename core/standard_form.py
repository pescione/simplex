"""
Conversione di un problema in forma standard.
"""

from fractions import Fraction
from .models import LinearProblem, StandardProblem, Step


def to_standard_form(problem: LinearProblem) -> tuple[StandardProblem, list[Step]]:
    """
    Trasforma un problema generico in forma standard:
    min c^T x
    Ax = b
    x >= 0

    Args:
        problem: problema originale

    Returns:
        (problema in forma standard, lista di step descrittivi)
    """
    steps = []

    # Step 1: Trasformazione da max a min
    c = list(problem.c)
    A = [row[:] for row in problem.A]
    b = list(problem.b)
    signs = list(problem.signs)

    if problem.sense == "max":
        c = [-coeff for coeff in c]
        step = Step(
            title="Trasformazione da massimo a minimo",
            description="Il problema è di massimo. Moltiplico la funzione obiettivo per -1 per ottenere un problema di minimo.",
            notes=[f"Nuova c: {c}"],
        )
        steps.append(step)

    # Step 2: Normalizzazione di b_i < 0
    num_constraints = len(b)
    for i in range(num_constraints):
        if b[i] < 0:
            # Moltiplica la riga i per -1 e inverti il segno
            A[i] = [-coeff for coeff in A[i]]
            b[i] = -b[i]

            # Inverti il segno del vincolo
            if signs[i] == "<=":
                signs[i] = ">="
            elif signs[i] == ">=":
                signs[i] = "<="
            # Se è "=", rimane "="

            step = Step(
                title=f"Normalizzazione vincolo {i + 1}",
                description=f"Il termine noto b[{i}] era negativo. Ho moltiplicato il vincolo per -1 e invertito il verso.",
                notes=[f"Nuovo vincolo {i + 1}: {signs[i]}"],
            )
            steps.append(step)

    # Step 3: Aggiunta di variabili slack e surplus
    var_names = list(problem.var_names)
    slack_vars = []
    surplus_vars = []
    artificial_vars = []
    constraint_auxiliary_var = []  # Per ogni vincolo, l'indice della variabile ausiliaria o -1

    num_original_vars = len(c)
    num_new_vars = num_original_vars

    for i in range(num_constraints):
        if signs[i] == "<=":
            # Aggiungi variabile slack
            slack_var_idx = num_new_vars
            slack_vars.append(slack_var_idx)
            constraint_auxiliary_var.append(slack_var_idx)
            num_new_vars += 1

            # Aggiungi colonna alla matrice A
            for row in A:
                row.append(Fraction(0))
            A[i][-1] = Fraction(1)

            # Aggiungi nome variabile
            var_names.append(f"s{len(slack_vars)}")

            step = Step(
                title=f"Aggiunta variabile slack al vincolo {i + 1}",
                description=f"Vincolo {i + 1}: <= diventa = con variabile slack {var_names[-1]}",
                notes=[],
            )
            steps.append(step)

        elif signs[i] == ">=":
            # Aggiungi variabile surplus
            surplus_var_idx = num_new_vars
            surplus_vars.append(surplus_var_idx)
            constraint_auxiliary_var.append(surplus_var_idx)
            num_new_vars += 1

            # Aggiungi colonna alla matrice A
            for row in A:
                row.append(Fraction(0))
            A[i][-1] = Fraction(-1)

            # Aggiungi nome variabile
            var_names.append(f"e{len(surplus_vars)}")

            step = Step(
                title=f"Aggiunta variabile surplus al vincolo {i + 1}",
                description=f"Vincolo {i + 1}: >= diventa = con variabile surplus {var_names[-1]}",
                notes=[],
            )
            steps.append(step)

        else:
            # Vincolo =, nessuna variabile ausiliaria
            constraint_auxiliary_var.append(-1)

    # Aggiungi valori zero per le nuove variabili nella funzione obiettivo
    while len(c) < num_new_vars:
        c.append(Fraction(0))

    # Step 4: Crea il problema in forma standard
    standard_problem = StandardProblem(
        c=c,
        A=A,
        b=b,
        var_names=var_names,
        original_var_count=num_original_vars,
        slack_vars=slack_vars,
        surplus_vars=surplus_vars,
        artificial_vars=artificial_vars,
        constraint_auxiliary_var=constraint_auxiliary_var,
        transformation_log=[step.description for step in steps],
    )

    step_summary = Step(
        title="Forma standard ottenuta",
        description=f"Problema trasformato in forma standard: min c^T x, Ax = b, x >= 0",
        notes=[
            f"Numero variabili originali: {num_original_vars}",
            f"Numero variabili slack: {len(slack_vars)}",
            f"Numero variabili surplus: {len(surplus_vars)}",
            f"Numero variabili totali: {len(var_names)}",
        ],
    )
    steps.append(step_summary)

    return standard_problem, steps
