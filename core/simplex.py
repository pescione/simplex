"""
Algoritmo del simplesso - Fase II.
"""

from fractions import Fraction
from .models import Tableau, Step, SolverOptions
from .tableau import get_reduced_costs, get_column_values, get_rhs_values
from .pivot import pivot


def is_optimal(tableau: Tableau) -> bool:
    """
    Controlla se il tableau è ottimale per un problema di minimo.
    
    Per un problema di minimo, il tableau è ottimo se tutti i costi ridotti
    delle variabili fuori base sono >= 0.
    """
    reduced_costs = get_reduced_costs(tableau)
    return all(cost >= 0 for cost in reduced_costs)


def choose_entering_variable(
    tableau: Tableau, rule: str = "most_negative"
) -> int | None:
    """
    Sceglie la variabile entrante in base alla regola specificata.

    Args:
        tableau: tableau corrente
        rule: "most_negative", "first_negative", "bland"

    Returns:
        Indice della colonna (variabile entrante) o None se nessuna variabile è ammissibile
    """
    reduced_costs = get_reduced_costs(tableau)

    if rule == "most_negative":
        # Scegli il costo ridotto più negativo
        min_cost = Fraction(0)
        min_col = None
        for j, cost in enumerate(reduced_costs):
            if cost < min_cost:
                min_cost = cost
                min_col = j
        return min_col

    elif rule == "first_negative":
        # Scegli la prima colonna con costo ridotto negativo
        for j, cost in enumerate(reduced_costs):
            if cost < 0:
                return j
        return None

    elif rule == "bland":
        # Scegli il costo ridotto più negativo, in caso di pareggio scegli il più piccolo indice
        candidates = [j for j, cost in enumerate(reduced_costs) if cost < 0]
        if candidates:
            return min(candidates)
        return None

    else:
        raise ValueError(f"Regola sconosciuta: {rule}")


def is_unbounded(tableau: Tableau, entering_col: int) -> bool:
    """
    Controlla se il problema è illimitato.

    Se la colonna entrante ha tutti i coefficienti nei vincoli <= 0,
    allora non esiste una variabile uscente e il problema è illimitato.
    """
    column_values = get_column_values(tableau, entering_col)
    return all(val <= 0 for val in column_values)


def choose_leaving_variable(
    tableau: Tableau, entering_col: int, rule: str = "most_negative"
) -> tuple[int | None, list[tuple[str, Fraction]]]:
    """
    Esegue il test dei rapporti per scegliere la variabile uscente.

    Args:
        tableau: tableau corrente
        entering_col: indice della colonna entrante
        rule: "first", "bland" (per gestire i pareggi)

    Returns:
        (indice della riga dove avviene il pivot, lista dei rapporti)
    """
    rhs_values = get_rhs_values(tableau)
    column_values = get_column_values(tableau, entering_col)

    # Calcola i rapporti per le righe con coefficiente positivo
    ratios = []  # lista di tuple (indice_riga, rapporto)

    for i, col_val in enumerate(column_values):
        if col_val > 0:
            ratio = rhs_values[i] / col_val
            ratios.append((i, ratio))

    if not ratios:
        # Nessun coefficiente positivo: il problema è illimitato
        return None, []

    # Scegli la riga con il rapporto minimo
    if rule == "first":
        leaving_row = ratios[0][0]
    elif rule == "bland":
        # In caso di pareggio nei rapporti, scegli la riga con indice più piccolo
        min_ratio = min(ratio for _, ratio in ratios)
        leaving_row = min(i for i, ratio in ratios if ratio == min_ratio)
    else:
        raise ValueError(f"Regola sconosciuta: {rule}")

    # Formatta i rapporti per il report
    ratio_report = []
    for i, (row_idx, ratio) in enumerate(ratios):
        var_name = tableau.var_names[tableau.basis[row_idx]]
        ratio_report.append((var_name, ratio))

    return leaving_row, ratio_report


def simplex(
    tableau: Tableau, options: SolverOptions | None = None
) -> tuple[Tableau, list[Step], str]:
    """
    Risolve un tableau già canonico usando l'algoritmo del simplesso.

    Args:
        tableau: tableau canonico iniziale (già in forma standard)
        options: opzioni del solver

    Returns:
        (tableau finale, lista di step, stato: "optimal", "unbounded", "iteration_limit")
    """
    if options is None:
        options = SolverOptions()

    steps = []
    current_tableau = tableau
    iteration = 0

    # Passo iniziale: registra il tableau iniziale
    initial_step = Step(
        title="Tableau iniziale fase II",
        description="Il tableau è stato inizializzato con la base corrente.",
        phase=2,
        tableau_before=None,
        tableau_after=current_tableau,
        notes=["Inizio dell'algoritmo del simplesso."],
    )
    steps.append(initial_step)

    while iteration < options.max_iterations:
        iteration += 1

        # Test di ottimalità
        if is_optimal(current_tableau):
            final_step = Step(
                title="Soluzione ottima trovata",
                description="Tutti i costi ridotti sono non negativi. Il tableau è ottimale.",
                phase=2,
                tableau_before=current_tableau,
                tableau_after=None,
                notes=[f"Iterazione {iteration - 1} completata. Algoritmo terminato."],
            )
            steps.append(final_step)
            return current_tableau, steps, "optimal"

        # Scegli la variabile entrante
        entering_col = choose_entering_variable(current_tableau, options.entering_var_rule)

        if entering_col is None:
            # Questo non dovrebbe succedere se is_optimal è stata già controllata
            final_step = Step(
                title="Anomalia: nessuna variabile entrante ammissibile",
                description="Non è stata trovata nessuna variabile con costo ridotto negativo, ma il tableau non è ottimale.",
                phase=2,
                tableau_before=current_tableau,
                notes=["Possibile errore nel codice."],
            )
            steps.append(final_step)
            return current_tableau, steps, "iteration_limit"

        entering_var_name = current_tableau.var_names[entering_col]

        # Test di illimitatezza
        if is_unbounded(current_tableau, entering_col):
            unbounded_step = Step(
                title="Problema illimitato",
                description=f"La colonna della variabile {entering_var_name} ha tutti i coefficienti <= 0. "
                f"Non esiste una variabile uscente.",
                phase=2,
                tableau_before=current_tableau,
                tableau_after=None,
                entering_var=entering_var_name,
                notes=["L'obiettivo può decrescere indefinitamente."],
            )
            steps.append(unbounded_step)
            return current_tableau, steps, "unbounded"

        # Scegli la variabile uscente
        leaving_row, ratio_report = choose_leaving_variable(
            current_tableau, entering_col, rule="bland"
        )

        if leaving_row is None:
            # Non dovrebbe accadere se is_unbounded è stata già controllata
            unbounded_step = Step(
                title="Anomalia: test dei rapporti fallito",
                description="Impossibile trovare una riga con coefficiente positivo nella colonna entrante.",
                phase=2,
                tableau_before=current_tableau,
                notes=["Possibile errore nel codice."],
            )
            steps.append(unbounded_step)
            return current_tableau, steps, "iteration_limit"

        leaving_var_name = current_tableau.var_names[current_tableau.basis[leaving_row]]

        # Registra lo step di scelta variabili
        choice_step = Step(
            title=f"Iterazione {iteration}: scelta variabili",
            description=f"Variabile entrante: {entering_var_name} (costo ridotto: {get_reduced_costs(current_tableau)[entering_col]}) "
            f"\nVariabile uscente: {leaving_var_name}",
            phase=2,
            tableau_before=current_tableau,
            entering_var=entering_var_name,
            leaving_var=leaving_var_name,
            ratios=ratio_report,
            notes=["Test dei rapporti completato."],
        )
        steps.append(choice_step)

        # Effettua il pivot
        new_tableau = pivot(current_tableau, leaving_row, entering_col)

        # Registra lo step del pivot
        pivot_step = Step(
            title=f"Iterazione {iteration}: pivot",
            description=f"Pivot sulla riga {leaving_row}, colonna {entering_col}. "
            f"{entering_var_name} entra, {leaving_var_name} esce.",
            phase=2,
            tableau_before=current_tableau,
            tableau_after=new_tableau,
            entering_var=entering_var_name,
            leaving_var=leaving_var_name,
            pivot_row=leaving_row,
            pivot_col=entering_col,
            notes=[f"Elemento pivot: {current_tableau.data[leaving_row + 1][entering_col]}"],
        )
        steps.append(pivot_step)

        current_tableau = new_tableau

    # Limite di iterazioni raggiunto
    final_step = Step(
        title="Limite massimo di iterazioni raggiunto",
        description=f"L'algoritmo non è converso entro {options.max_iterations} iterazioni. Possibile degenerazione o ciclo.",
        phase=2,
        tableau_before=current_tableau,
        notes=[f"Ultime iterazioni eseguite: {iteration}"],
    )
    steps.append(final_step)
    return current_tableau, steps, "iteration_limit"
