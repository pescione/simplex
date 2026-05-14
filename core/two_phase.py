"""
Metodo delle due fasi per il simplesso.
"""

from fractions import Fraction
from .models import StandardProblem, Tableau, Step, SolverOptions
from .tableau import build_canonical_tableau, get_objective_value
from .simplex import simplex
from .pivot import pivot


def build_artificial_problem(
    std: StandardProblem, options: SolverOptions | None = None
) -> tuple[StandardProblem, list[int], list[Step]]:
    """
    Costruisce il problema artificiale per la fase I.

    Dato:
        min c^T x
        Ax = b
        x >= 0

    Costruisce:
        min y1 + y2 + ... + yk
        Ax + Iy = b
        x, y >= 0

    dove y_i sono le variabili artificiali, aggiunte ai vincoli che non hanno
    una base iniziale immediata, cioè ai vincoli "=" e ai vincoli ">=".

    Args:
        std: problema in forma standard
        options: opzioni del solver (non usate qui)

    Returns:
        (problema artificiale, indici delle variabili artificiali, lista di step)
    """
    if options is None:
        options = SolverOptions()

    steps = []

    m = len(std.b)  # numero di vincoli
    n = len(std.c)  # numero di variabili originali (incluso slack/surplus)

    # Determina quali vincoli richiedono variabili artificiali
    # Un vincolo richiede artificiale se:
    # 1. Non ha slack/surplus (vincolo = originale), oppure
    # 2. Ha surplus (vincolo >= originale) - il surplus da solo non forma base ammissibile
    artificial_indices_per_constraint = []  # Per ogni vincolo, -1 se non necessita artificiale, altrimenti indice futura
    num_artificial = 0
    for i in range(m):
        if std.constraint_auxiliary_var[i] == -1:
            # Vincolo =: richiede artificiale
            artificial_indices_per_constraint.append(num_artificial)
            num_artificial += 1
        elif std.constraint_auxiliary_var[i] in std.surplus_vars:
            # Vincolo >= con surplus: richiede anche artificiale per base iniziale
            artificial_indices_per_constraint.append(num_artificial)
            num_artificial += 1
        else:
            # Vincolo <= con slack: non richiede artificiale
            artificial_indices_per_constraint.append(-1)

    # Costruisci il nuovo vettore c per la Fase I:
    # - Costo 0 per TUTTE le variabili originali, slack e surplus
    # - Costo 1 SOLO per le variabili artificiali
    # La Fase I NON deve mai usare i coefficienti originali della funzione obiettivo!
    c_artificial = [Fraction(0) for _ in range(n + num_artificial)]
    for i in range(num_artificial):
        c_artificial[n + i] = Fraction(1)

    # Costruisci la nuova matrice A (aggiungi colonne per le variabili artificiali)
    A_artificial = []
    for i, row in enumerate(std.A):
        new_row = list(row)
        # Aggiungi colonne per le variabili artificiali
        for j in range(num_artificial):
            if artificial_indices_per_constraint[i] == j:
                new_row.append(Fraction(1))
            else:
                new_row.append(Fraction(0))
        A_artificial.append(new_row)

    # Costruisci i nuovi nomi delle variabili
    var_names_artificial = list(std.var_names)
    artificial_indices = []
    for i in range(num_artificial):
        artificial_indices.append(len(var_names_artificial))
        var_names_artificial.append(f"y{i + 1}")

    # Crea il problema artificiale
    artificial_problem = StandardProblem(
        c=c_artificial,
        A=A_artificial,
        b=list(std.b),  # copia di b
        var_names=var_names_artificial,
        original_var_count=std.original_var_count,
        slack_vars=std.slack_vars,
        surplus_vars=std.surplus_vars,
        artificial_vars=artificial_indices,
        constraint_auxiliary_var=std.constraint_auxiliary_var,
        transformation_log=std.transformation_log + ["Costruzione del problema artificiale per la fase I"],
    )

    step = Step(
        title="Costruzione del problema artificiale",
        description=f"Aggiunto {num_artificial} variabili artificiali per i vincoli che richiedono una base iniziale artificiale.",
        phase=1,
        notes=[
            f"La fase I minimizzerà la somma delle variabili artificiali.",
            f"Se il valore ottimo è 0, esiste una soluzione ammissibile del problema originale.",
        ],
    )
    steps.append(step)

    return artificial_problem, artificial_indices, steps


def run_phase_one(
    std: StandardProblem, options: SolverOptions | None = None
) -> tuple[Tableau, list[Step], str]:
    """
    Risolve il problema artificiale (fase I).

    Args:
        std: problema in forma standard
        options: opzioni del solver

    Returns:
        (tableau finale della fase I, lista di step, stato: "feasible" o "infeasible")
    """
    if options is None:
        options = SolverOptions()

    steps = []

    # Costruisci il problema artificiale
    artificial_problem, artificial_indices, construction_steps = build_artificial_problem(std, options)
    steps.extend(construction_steps)

    # La base iniziale è formata dalle variabili artificiali e slack
    # Le variabili surplus non vengono usate direttamente in base; servono solo a trasformare >= in =
    basis = []
    artificial_counter = 0  # Conta il numero di variabili artificiali aggiunte finora
    
    # Per ogni vincolo, determina quale variabile entra in base
    for i in range(len(std.b)):
        if std.constraint_auxiliary_var[i] != -1 and std.constraint_auxiliary_var[i] not in std.surplus_vars:
            # Questo vincolo ha slack (non surplus), lo usiamo in base
            basis.append(std.constraint_auxiliary_var[i])
        else:
            # Questo vincolo non ha slack (ha surplus o niente), usiamo la variabile artificiale
            # L'indice della variabile artificiale è: len(std.c) + artificial_counter
            artificial_idx = len(std.c) + artificial_counter
            basis.append(artificial_idx)
            artificial_counter += 1

    # Costruisci il tableau canonico della fase I
    try:
        tableau_phase1 = build_canonical_tableau(
            A=artificial_problem.A,
            b=artificial_problem.b,
            c=artificial_problem.c,
            basis=basis,
            var_names=artificial_problem.var_names,
            phase=1,
            objective_name="w",  # w per il problema artificiale
        )
    except ValueError as e:
        error_step = Step(
            title="Errore nella costruzione del tableau della fase I",
            description=str(e),
            phase=1,
            notes=["Non è possibile costruire il tableau iniziale."],
        )
        steps.append(error_step)
        return None, steps, "error"

    # Registra il tableau iniziale della fase I
    initial_step = Step(
        title="Tableau iniziale fase I",
        description="Il tableau è stato costruito con la base iniziale determinata da slack, surplus e variabili artificiali.",
        phase=1,
        tableau_before=None,
        tableau_after=tableau_phase1,
        notes=["Inizio della fase I."],
    )
    steps.append(initial_step)

    # Risolvi con il simplesso
    final_tableau, simplex_steps, status = simplex(tableau_phase1, options)
    steps.extend(simplex_steps)

    # ✅ FIX BUG 2: Validare che la Fase I sia arrivata a "optimal" prima di interpretare w*
    if status != "optimal":
        # La Fase I NON è terminata correttamente
        if status == "unbounded":
            # ✅ FIX BUG 1: In Fase 1, "unbounded" è un errore interno
            error_step = Step(
                title="ERRORE: Fase I unbounded",
                description="Il problema artificiale non dovrebbe mai essere illimitato. "
                "Questo indica un errore nella costruzione del problema artificiale.",
                phase=1,
                tableau_before=final_tableau,
                notes=["Errore interno: controllare la costruzione del problema artificiale."],
            )
            steps.append(error_step)
            return final_tableau, steps, "error_phase1_unbounded"
        elif status == "iteration_limit":
            error_step = Step(
                title="Errore: Fase I - limite iterazioni raggiunto",
                description="La Fase I non ha raggiunto l'ottimalità entro il limite di iterazioni. "
                "Il problema potrebbe essere degenere o molto complesso.",
                phase=1,
                tableau_before=final_tableau,
                notes=["Errore: Aumentare il limite di iterazioni o controllare il problema."],
            )
            steps.append(error_step)
            return final_tableau, steps, "error_phase1_iteration_limit"
        else:
            error_step = Step(
                title=f"Errore: Fase I - stato non riconosciuto: {status}",
                description="La Fase I ha terminato con uno stato inaspettato.",
                phase=1,
                tableau_before=final_tableau,
                notes=["Errore interno: stato sconosciuto della Fase I."],
            )
            steps.append(error_step)
            return final_tableau, steps, "error_phase1_unknown"

    # ✅ A questo punto, status == "optimal", quindi w* è valido
    # Nel tableau, il RHS della riga 0 è il negativo di w
    # get_objective_value(tableau) = -tableau.data[0][-1] = -(-w) = w
    w_star = get_objective_value(final_tableau)

    if w_star > 0:
        # Problema inammissibile
        infeasible_step = Step(
            title="Problema originale inammissibile",
            description=f"Il valore ottimo della fase I è w* = {w_star} > 0. "
            f"Non esiste una soluzione ammissibile del problema originale.",
            phase=1,
            tableau_before=final_tableau,
            notes=["La fase I si ferma qui. Nessuna base ammissibile trovata."],
        )
        steps.append(infeasible_step)
        return final_tableau, steps, "infeasible"

    else:
        # Problema ammissibile
        feasible_step = Step(
            title="Base ammissibile trovata",
            description=f"Il valore ottimo della fase I è w* = {w_star} = 0. "
            f"Esiste una soluzione ammissibile del problema originale.",
            phase=1,
            tableau_before=final_tableau,
            notes=["La fase I è completata. Si passa alla fase II."],
        )
        steps.append(feasible_step)
        return final_tableau, steps, "feasible"


def prepare_phase_two(
    phase1_tableau: Tableau, std: StandardProblem, options: SolverOptions | None = None
) -> tuple[Tableau, list[Step]]:
    """
    Prepara il tableau per la fase II dopo la fase I.

    Procedura:
    1. Estrai la base dalla Fase I (basis_phase1)
    2. Rimuovi le variabili artificiali dalla base (dovrebbero essere fuori base se w*=0)
    3. Filtra la base per includere solo le variabili della forma standard (non artificiali)
    4. Costruisci il tableau della Fase II usando:
       - A = std.A (la matrice originale della forma standard)
       - b = std.b (i termini noti originali)
       - c = std.c (la funzione obiettivo originale)
       - basis = base filtrata dalla Fase I

    Args:
        phase1_tableau: tableau finale della fase I
        std: problema in forma standard originale
        options: opzioni del solver

    Returns:
        (tableau per la fase II, lista di step)
    """
    if options is None:
        options = SolverOptions()

    steps = []

    # Estrai la base dalla fase I
    basis_phase1 = list(phase1_tableau.basis)
    num_original_vars = len(std.c)  # variabili originali + slack + surplus (ma NO artificiali)

    # Filtra la base per rimuovere le variabili artificiali
    # Le variabili artificiali hanno indice >= num_original_vars
    current_tableau = phase1_tableau

    artificial_rows = [
        row_idx for row_idx, var_idx in enumerate(current_tableau.basis)
        if var_idx >= num_original_vars
    ]

    if artificial_rows:
        removal_step = Step(
            title="Gestione variabili artificiali in base con valore 0",
            description=f"Trovate {len(artificial_rows)} variabili artificiali ancora in base dopo la Fase I. "
            f"Si tenta di pivotarle fuori; se non è possibile, la riga viene trattata come ridondante.",
            phase=2,
            notes=["Caso degenere della Fase I."],
        )
        steps.append(removal_step)

    # Prova a pivotare fuori tutte le artificiali rimaste in base.
    # Il ciclo continua finché riusciamo a fare progressi, così una pivot può
    # liberare un'altra colonna per le iterazioni successive.
    while True:
        progress = False
        for row_idx, var_idx in enumerate(list(current_tableau.basis)):
            if var_idx < num_original_vars:
                continue

            rhs_value = current_tableau.data[row_idx + 1][-1]
            if rhs_value > Fraction(0):
                error_step = Step(
                    title="ERRORE: Variabile artificiale con valore > 0 ancora in base",
                    description=f"Variabile artificiale {current_tableau.var_names[var_idx]} ha valore {rhs_value} > 0 in base. "
                    f"Questo contraddice w* = 0 della Fase I.",
                    phase=2,
                    notes=["Errore interno: controllare la Fase I."],
                )
                steps.append(error_step)
                return None, steps

            pivot_col_found = None
            row_values = current_tableau.data[row_idx + 1][:num_original_vars]
            for col_idx, coeff in enumerate(row_values):
                if coeff != Fraction(0) and col_idx not in current_tableau.basis:
                    pivot_col_found = col_idx
                    break

            if pivot_col_found is not None:
                try:
                    current_tableau = pivot(current_tableau, row_idx, pivot_col_found)
                    progress = True
                    break
                except ValueError:
                    # Se il pivot non è possibile, passiamo alla classificazione delle righe.
                    continue

        if not progress:
            break

    keep_rows: list[int] = []
    reduced_basis: list[int] = []
    redundant_rows: list[int] = []

    for row_idx, var_idx in enumerate(current_tableau.basis):
        rhs_value = current_tableau.data[row_idx + 1][-1]
        row_values = current_tableau.data[row_idx + 1][:num_original_vars]

        if var_idx < num_original_vars:
            keep_rows.append(row_idx)
            reduced_basis.append(var_idx)
            continue

        # Se l'artificiale non è stata eliminata ma la riga è 0 = 0,
        # il vincolo è ridondante e può essere rimosso.
        if all(coeff == Fraction(0) for coeff in row_values) and rhs_value == Fraction(0):
            redundant_rows.append(row_idx)
            continue

        # Se la riga è ancora inconsistente, il problema è incoerente.
        error_step = Step(
            title="ERRORE: Vincolo incompatibile nella preparazione della Fase II",
            description=f"La riga {row_idx + 1} mantiene una variabile artificiale in base e non è riducibile a 0 = 0. "
            f"Non è possibile costruire una base ammissibile per la Fase II.",
            phase=2,
            notes=["Il vincolo residuo non è eliminabile e non è compatibile con la Fase II."],
        )
        steps.append(error_step)
        return None, steps

    if redundant_rows:
        redundant_step = Step(
            title="Vincoli ridondanti rimossi",
            description=f"Eliminati {len(redundant_rows)} vincoli ridondanti della forma 0 = 0 prima della Fase II.",
            phase=2,
            notes=["Le righe ridondanti non influenzano la soluzione ottima."],
        )
        steps.append(redundant_step)

    if not keep_rows:
        # Nessun vincolo rimasto: il problema della Fase II è puramente di non negatività.
        tableau_phase2 = Tableau(
            data=[std.c[:] + [Fraction(0)]],
            basis=[],
            var_names=std.var_names,
            phase=2,
            objective_name="z",
        )

        prep_step = Step(
            title="Preparazione tableau fase II",
            description="Tutti i vincoli erano ridondanti dopo la Fase I. La Fase II parte da un tableau senza righe di vincolo.",
            phase=2,
            tableau_before=phase1_tableau,
            tableau_after=tableau_phase2,
            notes=["Base della Fase II: []"],
        )
        steps.append(prep_step)

        return tableau_phase2, steps

    reduced_A = [std.A[row_idx] for row_idx in keep_rows]
    reduced_b = [std.b[row_idx] for row_idx in keep_rows]

    # Costruisci il tableau della Fase II usando la matrice originale std.A
    # e la base filtrata dalla Fase I
    try:
        tableau_phase2 = build_canonical_tableau(
            A=reduced_A,
            b=reduced_b,
            c=std.c,
            basis=reduced_basis,
            var_names=std.var_names,
            phase=2,
            objective_name="z",
        )

        prep_step = Step(
            title="Preparazione tableau fase II",
            description="Il tableau è stato riconstruito con la matrice originale e la funzione obiettivo originale. "
            "Le variabili artificiali sono state rimosse dalla considerazione.",
            phase=2,
            tableau_before=phase1_tableau,
            tableau_after=tableau_phase2,
            notes=[f"Base della Fase II: {[std.var_names[i] for i in reduced_basis]}"],
        )
        steps.append(prep_step)

        return tableau_phase2, steps

    except Exception as e:
        error_step = Step(
            title="Errore nella preparazione della fase II",
            description=f"Errore durante la costruzione del tableau della Fase II: {str(e)}",
            phase=2,
            notes=["Non è possibile passare alla fase II."],
        )
        steps.append(error_step)
        return None, steps
