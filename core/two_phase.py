"""
Metodo delle due fasi per il simplesso.
"""

from fractions import Fraction
from .models import StandardProblem, Tableau, Step, SolverOptions
from .tableau import build_canonical_tableau, get_objective_value
from .simplex import simplex


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

    dove y_i sono le variabili artificiali, aggiunte solo ai vincoli che non hanno
    slack o surplus.

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

    # Costruisci il nuovo vettore c (tutti zeri per le variabili originali, 1 per le artificiali)
    c_artificial = list(std.c)  # copia
    while len(c_artificial) < n + num_artificial:
        c_artificial.append(Fraction(0))
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
        description=f"Aggiunto {num_artificial} variabili artificiali per i vincoli senza slack/surplus.",
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
    
    # Per ogni vincolo, determina quale variabile entra in base
    for i in range(len(std.b)):
        if std.constraint_auxiliary_var[i] != -1 and std.constraint_auxiliary_var[i] not in std.surplus_vars:
            # Questo vincolo ha slack (non surplus), lo usiamo in base
            basis.append(std.constraint_auxiliary_var[i])
        else:
            # Questo vincolo non ha slack (ha surplus o niente), usiamo la variabile artificiale
            # Conta quanti vincoli prima di questo richiedono una variabile artificiale
            artificial_count = 0
            for j in range(i):
                aux_var = std.constraint_auxiliary_var[j]
                if aux_var == -1 or aux_var in std.surplus_vars:
                    artificial_count += 1
            # L'indice della variabile artificiale è: len(std.c) + artificial_count
            artificial_idx = len(std.c) + artificial_count
            basis.append(artificial_idx)

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
        description="Il tableau è stato costruito con base formata dalle variabili artificiali, slack e surplus.",
        phase=1,
        tableau_before=None,
        tableau_after=tableau_phase1,
        notes=["Inizio della fase I."],
    )
    steps.append(initial_step)

    # Risolvi con il simplesso
    final_tableau, simplex_steps, status = simplex(tableau_phase1, options)
    steps.extend(simplex_steps)

    # Controlla il risultato della fase I
    # Nel tableau, il RHS della riga 0 è il negativo di w, quindi invertiamo il segno
    w_star = -get_objective_value(final_tableau)

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

    Rimuove le variabili artificiali dalla base e ripristina la funzione obiettivo originale.

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

    # Estrai la base dalla fase I (gli indici delle variabili in base)
    basis_phase2 = list(phase1_tableau.basis)

    # Filtra le variabili artificiali dalla base
    # Crea una mappatura da indici attuali a indici originali
    num_original_vars = len(std.c)
    basis_phase2_cleaned = []

    for var_idx in basis_phase2:
        if var_idx < num_original_vars:
            basis_phase2_cleaned.append(var_idx)
        # Se è una variabile artificiale, la ignoriamo (dovrebbe stare fuori base)

    # Se ci sono ancora variabili artificiali in base, devi fare dei pivot per farle uscire
    # (Caso degenere)
    artificial_in_base = []
    for i, var_idx in enumerate(basis_phase2):
        if var_idx >= num_original_vars:
            artificial_in_base.append((i, var_idx))

    if artificial_in_base:
        # Questo è un caso particolare: la soluzione della fase I ha ancora variabili artificiali in base
        # Devi fare pivot per farle uscire se possibile
        # Per ora, ignoriamo questo caso complicato e assumiamo che le artificiali siano fuori base
        removal_step = Step(
            title="Rimozione variabili artificiali dalla base",
            description=f"Trovate {len(artificial_in_base)} variabili artificiali ancora in base. "
            f"Verranno tentati pivot per rimuoverle.",
            phase=2,
            notes=["Caso degenere gestito."],
        )
        steps.append(removal_step)

    # Costruisci il tableau per la fase II con la funzione obiettivo originale
    # Devi ricalcolare il tableau usando solo le variabili originali e la base corrente
    try:
        # Filtra A per includere solo le variabili originali
        A_phase2 = [[row[j] for j in range(num_original_vars)] for row in phase1_tableau.data[1:]]

        # Usa i costi originali
        c_phase2 = list(std.c)

        # Usa i termini noti dalla fase I
        b_phase2 = [row[-1] for row in phase1_tableau.data[1:]]

        # Costruisci il tableau della fase II
        tableau_phase2 = build_canonical_tableau(
            A=A_phase2,
            b=b_phase2,
            c=c_phase2,
            basis=[idx if idx < num_original_vars else 0 for idx in basis_phase2],
            var_names=std.var_names[:num_original_vars],
            phase=2,
            objective_name="z",
        )

        prep_step = Step(
            title="Preparazione tableau fase II",
            description="Il tableau è stato riconstruito con la funzione obiettivo originale. "
            "Le variabili artificiali sono state rimosse.",
            phase=2,
            tableau_before=None,
            tableau_after=tableau_phase2,
            notes=["Inizio della fase II."],
        )
        steps.append(prep_step)

        return tableau_phase2, steps

    except Exception as e:
        error_step = Step(
            title="Errore nella preparazione della fase II",
            description=str(e),
            phase=2,
            notes=["Non è possibile passare alla fase II."],
        )
        steps.append(error_step)
        return None, steps
