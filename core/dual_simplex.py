"""
Algoritmo del simplesso duale.

Teoria:
    Il simplesso duale risolve problemi con:
    - Tableau ottimale dal punto di vista duale (tutti i costi ridotti ≥ 0)
    - Inammissibilità primale (RHS negativi)
    
    Algoritmo:
    1. Se RHS ≥ 0 per tutti i vincoli: soluzione ammissibile → STOP (ottimale)
    2. Sceglie riga con RHS negativo minimo (variabile uscente dalla base)
    3. Controlla ammissibilità della riga: se tutti i coeff. della riga ≥ 0, INAMMISSIBILE
    4. Sceglie colonna (variabile entrante) minimizzando il rapporto tra
       costo ridotto e coefficiente della riga (rapporto minimo)
    5. Esegue il pivot
    6. Torna a 1

Per questo algoritmo, abbiamo bisogno di una base iniziale. Nel nostro caso:
- La base proviene dalla forma standard (slack/surplus)
- Potremmo avere RHS negati, quindi facciamo un passo di preprocessing
"""

from fractions import Fraction
from .models import Tableau, Step, SolverOptions
from .tableau import get_reduced_costs, get_column_values, get_rhs_values
from .pivot import pivot


def is_primal_feasible(tableau: Tableau) -> bool:
    """
    Controlla se il tableau è ammissibile dal punto di vista primale.
    
    Un tableau è ammissibile primale se tutti i termini noti (RHS) sono ≥ 0.
    
    Args:
        tableau: tableau corrente
        
    Returns:
        True se tutti i RHS ≥ 0
    """
    rhs_values = get_rhs_values(tableau)
    return all(val >= 0 for val in rhs_values)


def is_dual_feasible(tableau: Tableau) -> bool:
    """
    Controlla se il tableau è ammissibile dal punto di vista duale.
    
    Un tableau è ammissibile duale se tutti i costi ridotti (riga 0) sono ≥ 0.
    
    Args:
        tableau: tableau corrente
        
    Returns:
        True se tutti i costi ridotti ≥ 0
    """
    reduced_costs = get_reduced_costs(tableau)
    basis_set = set(tableau.basis)
    
    # Solo variabili non basiche hanno senso
    for j, cost in enumerate(reduced_costs):
        if j not in basis_set and cost < 0:
            return False
    
    return True


def choose_leaving_variable_dual(tableau: Tableau) -> int | None:
    """
    Sceglie la variabile uscente (riga con RHS negativo più negativo).
    
    Nel simplesso duale:
    - Una variabile in base con valore negativo deve uscire dalla base
    - Scegliamo quella con il valore più negativo (euristica di Bland: minimo indice)
    
    Args:
        tableau: tableau corrente
        
    Returns:
        Indice della riga (0-based relativo ai vincoli, non al tableau) o None
    """
    rhs_values = get_rhs_values(tableau)
    
    # Trova la riga con RHS negativo più negativo (minimo)
    min_val = Fraction(0)
    min_row = None
    
    for i, val in enumerate(rhs_values):
        if val < min_val:
            min_val = val
            min_row = i
    
    return min_row


def choose_entering_variable_dual(
    tableau: Tableau, leaving_row: int, rule: str = "bland"
) -> int | None:
    """
    Sceglie la variabile entrante usando il test del rapporto (dual ratio test).
    
    Per la riga uscente, calcoliamo il rapporto tra il costo ridotto e
    il coefficiente della riga per ogni colonna con coefficiente < 0.
    
    Scegliamo la colonna che minimizza questo rapporto (per mantenere
    l'ammissibilità duale).
    
    Args:
        tableau: tableau corrente
        leaving_row: indice della riga uscente (0-based relativo ai vincoli)
        rule: euristica ("bland" = minimo rapporto, poi minimo indice)
        
    Returns:
        Indice della colonna (variabile entrante) o None se inammissibile
    """
    # Converte indice della riga: relativo ai vincoli → assoluto nel tableau
    absolute_row = leaving_row + 1
    
    reduced_costs = get_reduced_costs(tableau)
    basis_set = set(tableau.basis)
    
    # Estrai i coefficienti della riga uscente (escluso RHS)
    row_coefficients = tableau.data[absolute_row][:-1]
    
    # Trova le colonne con coefficiente < 0 (condidati per entrare)
    candidates = []
    
    for j in range(len(row_coefficients)):
        coeff = row_coefficients[j]

        if coeff < 0 and j not in basis_set:
            reduced_cost = reduced_costs[j]

            # Dual ratio test:
            # con costi ridotti >= 0 e coefficiente a_ij < 0,
            # il rapporto corretto è reduced_cost / (-a_ij).
            ratio = reduced_cost / (-coeff)
            candidates.append((ratio, j))
    
    if not candidates:
        # Nessuna colonna con coefficiente negativo: problema inammissibile
        return None
    
    if rule == "bland":
        # Minimo rapporto, poi minimo indice
        candidates.sort(key=lambda x: (x[0], x[1]))
        return candidates[0][1]
    else:
        raise ValueError(f"Regola sconosciuta per dual ratio test: {rule}")


def dual_simplex(
    tableau: Tableau, options: SolverOptions | None = None
) -> tuple[Tableau, list[Step], str]:
    """
    Risolve il problema usando l'algoritmo del simplesso duale.
    
    Precondizioni:
    - Tableau ha una base iniziale
    - Tutti i costi ridotti ≥ 0 (ammissibilità duale)
    - Possibili RHS negativi (inammissibilità primale)
    
    Args:
        tableau: tableau iniziale (deve essere dual-feasible)
        options: opzioni del solver
        
    Returns:
        (tableau finale, lista di step, status)
        status: "optimal", "unbounded", "iteration_limit"
    """
    if options is None:
        options = SolverOptions()
    
    steps = []
    iteration = 0
    
    # Verifica ammissibilità duale iniziale
    if not is_dual_feasible(tableau):
        step = Step(
            title="Avvertenza: Tableau non è duale-ammissibile",
            description="Il tableau iniziale non soddisfa l'ammissibilità duale. L'algoritmo potrebbe non convergere.",
            notes=["Verificare il tableau iniziale."],
        )
        steps.append(step)
    
    current_tableau = tableau
    
    # Fase principale del simplesso duale
    while iteration < options.max_iterations:
        iteration += 1
        
        # Verifica ammissibilità primale (criterio di stop)
        if is_primal_feasible(current_tableau):
            # Soluzione ottimale trovata
            step = Step(
                title="Soluzione ottimale trovata",
                description=f"Tableau ammissibile primale dopo {iteration - 1} iterazioni.",
                notes=[],
            )
            steps.append(step)
            return current_tableau, steps, "optimal"
        
        # Sceglie variabile uscente (RHS più negativo)
        leaving_row = choose_leaving_variable_dual(current_tableau)
        
        if leaving_row is None:
            # Non dovrebbe accadere se il tableau è ammissibile duale
            step = Step(
                title="Errore interno",
                description="Nessuna riga con RHS negativo trovata, ma il tableau non è ammissibile primale.",
                notes=[],
            )
            steps.append(step)
            return current_tableau, steps, "unbounded"
        
        leaving_var_idx = current_tableau.basis[leaving_row]
        leaving_var_name = current_tableau.var_names[leaving_var_idx]
        
        # Sceglie variabile entrante (dual ratio test)
        entering_col = choose_entering_variable_dual(
            current_tableau, leaving_row, rule="bland"
        )
        
        if entering_col is None:
            # Nessuna colonna ammissibile: problema inammissibile
            step = Step(
                title="Problema inammissibile",
                description=f"Riga {leaving_row} ha tutti i coefficienti ≥ 0. Nessuna variabile può entrare.",
                notes=[f"Variabile uscente: {leaving_var_name}"],
            )
            steps.append(step)
            return current_tableau, steps, "unbounded"
        
        entering_var_idx = entering_col
        entering_var_name = current_tableau.var_names[entering_var_idx]
        
        # Registra lo step di pivot
        step = Step(
            title=f"Iterazione {iteration}: Pivot",
            description=f"Variabile uscente: {leaving_var_name}, Variabile entrante: {entering_var_name}",
            phase=2,
            tableau_before=current_tableau,
            entering_var=entering_var_name,
            leaving_var=leaving_var_name,
            pivot_row=leaving_row,
            pivot_col=entering_col,
            notes=[],
        )
        
        # Esegui il pivot
        try:
            current_tableau = pivot(current_tableau, leaving_row, entering_col)
            step.tableau_after = current_tableau
        except Exception as e:
            step.notes.append(f"Errore nel pivot: {str(e)}")
            steps.append(step)
            return current_tableau, steps, "unbounded"
        
        steps.append(step)
    
    # Limite di iterazioni raggiunto
    step = Step(
        title="Limite di iterazioni raggiunto",
        description=f"Simplesso duale non ha convergito dopo {options.max_iterations} iterazioni.",
        notes=[],
    )
    steps.append(step)
    return current_tableau, steps, "iteration_limit"
