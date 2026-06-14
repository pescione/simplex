"""
Solver ad alto livello che coordina tutti i moduli.
"""

from fractions import Fraction
from typing import Optional
from .models import LinearProblem, SolveResult, SolverOptions, Step
from .parser import parse_problem
from .standard_form import to_standard_form
from .basis import find_identity_basis, basis_is_feasible
from .tableau import build_canonical_tableau, get_rhs_values, get_objective_value
from .simplex import simplex
from .two_phase import run_phase_one, prepare_phase_two, build_artificial_problem
from .dual_simplex import dual_simplex, is_dual_feasible
from .dual import compute_dual_problem, can_use_dual_simplex, identify_dual_infeasibility

def find_signed_identity_basis(
    A: list[list[Fraction]],
) -> tuple[list[int], list[Fraction]] | None:
    """
    Cerca una base formata da colonne +e_i oppure -e_i.

    Restituisce:
        (basis, row_multipliers)

    Dove:
        basis[i] = indice della variabile basica della riga i
        row_multipliers[i] = 1 se la colonna era +e_i
                             -1 se la colonna era -e_i

    Se una colonna basica è -e_i, moltiplicheremo tutta la riga i per -1
    per ottenere una base canonica +I.
    """
    if not A:
        return None

    m = len(A)
    n = len(A[0])

    basis: list[int | None] = [None] * m
    row_multipliers = [Fraction(1)] * m
    used_cols = set()

    for i in range(m):
        found = False

        for j in range(n):
            if j in used_cols:
                continue

            col = [A[r][j] for r in range(m)]

            is_plus_e = all(
                col[r] == (Fraction(1) if r == i else Fraction(0))
                for r in range(m)
            )

            is_minus_e = all(
                col[r] == (Fraction(-1) if r == i else Fraction(0))
                for r in range(m)
            )

            if is_plus_e:
                basis[i] = j
                row_multipliers[i] = Fraction(1)
                used_cols.add(j)
                found = True
                break

            if is_minus_e:
                basis[i] = j
                row_multipliers[i] = Fraction(-1)
                used_cols.add(j)
                found = True
                break

        if not found:
            return None

    return [int(x) for x in basis], row_multipliers


def normalize_rows_for_signed_basis(
    A: list[list[Fraction]],
    b: list[Fraction],
    row_multipliers: list[Fraction],
) -> tuple[list[list[Fraction]], list[Fraction]]:
    """
    Moltiplica le righe per +1 o -1 in modo che una base ±I diventi +I.
    """
    A_norm = []
    b_norm = []

    for i, multiplier in enumerate(row_multipliers):
        A_norm.append([multiplier * value for value in A[i]])
        b_norm.append(multiplier * b[i])

    return A_norm, b_norm

def build_tableau_for_dual_simplex(
    standard_problem: "StandardProblem",
    basis: list[int],
    row_multipliers: list[Fraction] | None,
    options: SolverOptions,
) -> Optional["Tableau"]:
    """
    Prepara il tableau per il simplesso duale.

    Il simplesso duale richiede:
    - una base canonica iniziale;
    - ammissibilità duale: costi ridotti >= 0;
    - ammissibilità primale non richiesta: RHS possono essere negativi.

    Se la base trovata è una -identità, moltiplichiamo le righe necessarie
    per trasformarla in +identità.
    """
    A = [row[:] for row in standard_problem.A]
    b = list(standard_problem.b)

    if row_multipliers is not None:
        A, b = normalize_rows_for_signed_basis(A, b, row_multipliers)

    tableau = build_canonical_tableau(
        A=A,
        b=b,
        c=standard_problem.c,
        basis=basis,
        var_names=standard_problem.var_names,
        phase=2,
        objective_name="z",
    )

    # La condizione corretta è sui costi ridotti del tableau,
    # non direttamente sui coefficienti c.
    if not is_dual_feasible(tableau):
        return None

    return tableau

def solve_problem(raw_text: str, options: SolverOptions | None = None) -> SolveResult:
    """
    Risolve un problema di programmazione lineare dato come testo.

    Il flusso è:
    1. Parse del testo di input
    2. Trasformazione in forma standard
    3. Ricerca di una base iniziale
    4. Se esiste base ammissibile: risoluzione diretta (fase II)
    5. Se non esiste: fase I + fase II

    Args:
        raw_text: testo del problema in formato specificato
        options: opzioni del solver

    Returns:
        Oggetto SolveResult con il risultato completo
    """
    if options is None:
        options = SolverOptions()

    all_steps = []

    # Step 1: Parse del problema
    try:
        original_problem = parse_problem(raw_text)
        parse_step = Step(
            title="Input letto",
            description=f"Problema di {original_problem.sense}imo con {len(original_problem.c)} variabili e {len(original_problem.b)} vincoli.",
            notes=["Input parsato correttamente."],
        )
        all_steps.append(parse_step)
    except Exception as e:
        error_result = SolveResult(
            status="input_error",
            message=f"Errore nel parsing dell'input: {str(e)}",
            original_problem=None,
            standard_problem=None,
            steps=all_steps,
            final_tableau=None,
            solution=None,
            optimal_value=None,
        )
        return error_result

    # Step 2: Trasformazione in forma standard
    try:
        standard_problem, standard_steps = to_standard_form(original_problem)
        all_steps.extend(standard_steps)
    except Exception as e:
        error_result = SolveResult(
            status="input_error",
            message=f"Errore nella trasformazione in forma standard: {str(e)}",
            original_problem=original_problem,
            standard_problem=None,
            steps=all_steps,
            final_tableau=None,
            solution=None,
            optimal_value=None,
        )
        return error_result

    # Step 3: Ricerca della base iniziale
    basis = find_identity_basis(standard_problem.A)

    # ===================================================================
    # PERCORSO 1: TRASFORMAZIONE IN DUALE + SIMPLESSO DUALE
    # ===================================================================
    if options.method == "dual_simplex":
        method_step = Step(
            title="Metodo risolutivo scelto: Duale + Simplesso Duale",
            description=(
                "Il problema in input viene trasformato nel suo duale. "
                "Il problema duale viene poi portato in forma standard "
                "e risolto con il metodo del simplesso duale."
            ),
            notes=[
                "Non viene eseguita la fase I sul primale.",
                "Il risultato riportato è ottenuto risolvendo il problema duale.",
            ],
        )
        all_steps.append(method_step)

        # 1. Costruzione del problema duale dal problema originale
        try:
            dual_problem, dual_steps = compute_dual_problem(original_problem)
            all_steps.extend(dual_steps)
        except Exception as e:
            return SolveResult(
                status="input_error",
                message=f"Errore nella costruzione del problema duale: {str(e)}",
                original_problem=original_problem,
                standard_problem=standard_problem,
                steps=all_steps,
                final_tableau=None,
                solution=None,
                optimal_value=None,
                dual_problem=None,

            )

        # 2. Trasformazione del duale in forma standard
        try:
            dual_standard_problem, dual_standard_steps = to_standard_form(dual_problem)
            all_steps.extend(dual_standard_steps)
        except Exception as e:
            return SolveResult(
                status="input_error",
                message=f"Errore nella trasformazione del duale in forma standard: {str(e)}",
                original_problem=original_problem,
                standard_problem=None,
                steps=all_steps,
                final_tableau=None,
                solution=None,
                optimal_value=None,
                dual_problem=dual_problem,
            )

        # 3. Ricerca di una base +I oppure -I nel duale standardizzato
        signed_basis_result = find_signed_identity_basis(dual_standard_problem.A)

        if signed_basis_result is None:
            all_steps.append(
                Step(
                    title="Base iniziale non trovata per il simplesso duale",
                    description=(
                        "Nel problema duale standardizzato non è stata trovata "
                        "una base identità o meno-identità naturale."
                    ),
                    notes=[
                        "Il simplesso duale richiede una base iniziale canonica.",
                        "In questo caso puoi usare una fase ausiliaria oppure il metodo delle due fasi.",
                    ],
                )
            )

            return SolveResult(
                status="dual_simplex_not_applicable",
                message=(
                    "Il problema è stato trasformato in duale, ma non è stata trovata "
                    "una base iniziale ±I per avviare il simplesso duale."
                ),
                original_problem=original_problem,
                standard_problem=dual_standard_problem,
                steps=all_steps,
                final_tableau=None,
                solution=None,
                optimal_value=None,
                dual_problem=dual_problem,
            )

        dual_basis, row_multipliers = signed_basis_result

        all_steps.append(
            Step(
                title="Base iniziale per simplesso duale trovata",
                description=(
                    "È stata trovata una base identità o meno-identità "
                    "nel problema duale standardizzato."
                ),
                notes=[
                    f"Base: {[dual_standard_problem.var_names[i] for i in dual_basis]}",
                    f"Moltiplicatori di riga: {row_multipliers}",
                ],
            )
        )

        # 4. Costruzione del tableau per il simplesso duale
        try:
            tableau = build_tableau_for_dual_simplex(
                dual_standard_problem,
                dual_basis,
                row_multipliers,
                options,
            )

            if tableau is None:
                all_steps.append(
                    Step(
                        title="Tableau non dualmente ammissibile",
                        description=(
                            "Il tableau iniziale del duale non soddisfa "
                            "la condizione di ammissibilità duale."
                        ),
                        notes=[
                            "I costi ridotti non sono tutti >= 0.",
                            "Il simplesso duale diretto non può partire da questo tableau.",
                        ],
                    )
                )

                return SolveResult(
                    status="dual_simplex_not_applicable",
                    message=(
                        "Il duale è stato costruito, ma il tableau iniziale "
                        "non è dualmente ammissibile."
                    ),
                    original_problem=original_problem,
                    standard_problem=dual_standard_problem,
                    steps=all_steps,
                    final_tableau=None,
                    solution=None,
                    optimal_value=None,
                    dual_problem=dual_problem,
                )

        except Exception as e:
            return SolveResult(
                status="input_error",
                message=f"Errore nella costruzione del tableau duale: {str(e)}",
                original_problem=original_problem,
                standard_problem=dual_standard_problem,
                steps=all_steps,
                final_tableau=None,
                solution=None,
                optimal_value=None,
                dual_problem=dual_problem,
            )

        # 5. Esecuzione del simplesso duale sul problema duale
        final_tableau, simplex_steps, status = dual_simplex(tableau, options)
        all_steps.extend(simplex_steps)

        if status == "optimal":
            solution = extract_solution(final_tableau, dual_standard_problem)
            optimal_value = get_objective_value(final_tableau)

            # Se il problema effettivamente risolto, cioè il duale,
            # era un massimo, to_standard_form lo ha trasformato in minimo.
            # Quindi bisogna cambiare segno al valore ottimo.
            if dual_problem.sense == "max":
                optimal_value = -optimal_value

            return SolveResult(
                status="optimal",
                message=(
                    "Soluzione ottima trovata trasformando il problema in duale "
                    "e risolvendo il duale con il simplesso duale."
                ),
                original_problem=original_problem,
                standard_problem=dual_standard_problem,
                steps=all_steps,
                final_tableau=final_tableau,
                solution=solution,
                optimal_value=optimal_value,
                dual_problem=dual_problem,

            )

        elif status == "unbounded":
            return SolveResult(
                status="unbounded",
                message=(
                    "Il problema duale risulta illimitato durante il simplesso duale. "
                    "Per dualità, questo può indicare inammissibilità del primale."
                ),
                original_problem=original_problem,
                standard_problem=dual_standard_problem,
                steps=all_steps,
                final_tableau=final_tableau,
                solution=None,
                optimal_value=None,
                dual_problem=dual_problem,
            )

        else:
            return SolveResult(
                status="iteration_limit",
                message=(
                    "Limite massimo di iterazioni raggiunto nel simplesso duale "
                    "applicato al problema duale."
                ),
                original_problem=original_problem,
                standard_problem=dual_standard_problem,
                steps=all_steps,
                final_tableau=final_tableau,
                solution=None,
                optimal_value=None,
                dual_problem=dual_problem,
            )
    
    # ===================================================================
    # PERCORSO 2: SIMPLESSO ORDINARIO (se base ammissibile)
    # ===================================================================
    if basis is not None and basis_is_feasible(standard_problem.A, standard_problem.b, basis):
        # Base ammissibile trovata: risoluzione diretta (fase II)
        base_step = Step(
            title="Base ammissibile trovata",
            description="Trovata una base ammissibile attraverso le variabili slack/surplus. La fase I non è necessaria.",
            notes=[f"Base: {[standard_problem.var_names[i] for i in basis]}"],
        )
        all_steps.append(base_step)

        # Costruisci il tableau canonico della fase II
        try:
            tableau = build_canonical_tableau(
                A=standard_problem.A,
                b=standard_problem.b,
                c=standard_problem.c,
                basis=basis,
                var_names=standard_problem.var_names,
                phase=2,
                objective_name="z",
            )
        except Exception as e:
            error_result = SolveResult(
                status="input_error",
                message=f"Errore nella costruzione del tableau: {str(e)}",
                original_problem=original_problem,
                standard_problem=standard_problem,
                steps=all_steps,
                final_tableau=None,
                solution=None,
                optimal_value=None,
            )
            return error_result

        # Usa il simplesso ordinario (metodo primale)
        final_tableau, simplex_steps, status = simplex(tableau, options)

        # Estrai la soluzione
        if status == "optimal":
            solution = extract_solution(final_tableau, standard_problem)
            optimal_value = get_objective_value(final_tableau)

            # Se il problema originale era di massimo, cambia il segno del valore ottimo
            if original_problem.sense == "max":
                optimal_value = -optimal_value

            return SolveResult(
                status="optimal",
                message="Soluzione ottima trovata.",
                original_problem=original_problem,
                standard_problem=standard_problem,
                steps=all_steps,
                final_tableau=final_tableau,
                solution=solution,
                optimal_value=optimal_value,
            )
        elif status == "unbounded":
            return SolveResult(
                status="unbounded",
                message="Il problema è illimitato.",
                original_problem=original_problem,
                standard_problem=standard_problem,
                steps=all_steps,
                final_tableau=final_tableau,
                solution=None,
                optimal_value=None,
            )
        else:
            return SolveResult(
                status="iteration_limit",
                message="Limite massimo di iterazioni raggiunto.",
                original_problem=original_problem,
                standard_problem=standard_problem,
                steps=all_steps,
                final_tableau=final_tableau,
                solution=None,
                optimal_value=None,
            )

    else:
        # Base non trovata: necessaria la fase I
        base_not_found_step = Step(
            title="Base ammissibile non trovata",
            description="Non è stata trovata una base ammissibile attraverso le variabili slack/surplus. Si usa il metodo delle due fasi.",
            notes=["Inizio della fase I con variabili artificiali."],
        )
        all_steps.append(base_not_found_step)

        # Risolvi il problema artificiale (fase I)
        phase1_tableau, phase1_steps, phase1_status = run_phase_one(standard_problem, options)
        all_steps.extend(phase1_steps)

        # ✅ FIX BUG 3: Separare completamente la Fase I dalla Fase II
        # Controlla i risultati possibili della Fase I
        if phase1_status == "infeasible":
            # Stato valido: il problema originale non ha soluzioni ammissibili
            return SolveResult(
                status="infeasible",
                message="Il problema originale è inammissibile. La Fase I ha determinato che non esiste una base ammissibile.",
                original_problem=original_problem,
                standard_problem=standard_problem,
                steps=all_steps,
                final_tableau=phase1_tableau,
                solution=None,
                optimal_value=None,
            )
        elif phase1_status == "feasible":
            # Stato valido: esiste una base ammissibile, procediamo con la Fase II
            pass  # Continuiamo con la preparazione della Fase II
        elif phase1_status == "error_phase1_unbounded":
            # Errore interno: il problema artificiale non dovrebbe mai essere illimitato
            return SolveResult(
                status="error_phase1",
                message="ERRORE INTERNO: La Fase I è terminata con stato 'unbounded'. "
                "Il problema artificiale non dovrebbe mai essere illimitato. "
                "Controllare la costruzione del problema.",
                original_problem=original_problem,
                standard_problem=standard_problem,
                steps=all_steps,
                final_tableau=phase1_tableau,
                solution=None,
                optimal_value=None,
            )
        elif phase1_status == "error_phase1_iteration_limit":
            # Errore: limite iterazioni raggiunto in Fase I
            return SolveResult(
                status="error_phase1",
                message="La Fase I non ha raggiunto l'ottimalità entro il limite di iterazioni. "
                "Il problema potrebbe essere degenere o molto complesso.",
                original_problem=original_problem,
                standard_problem=standard_problem,
                steps=all_steps,
                final_tableau=phase1_tableau,
                solution=None,
                optimal_value=None,
            )
        else:
            # Stato non riconosciuto
            return SolveResult(
                status="error_phase1",
                message=f"ERRORE: La Fase I ha terminato con stato sconosciuto: {phase1_status}",
                original_problem=original_problem,
                standard_problem=standard_problem,
                steps=all_steps,
                final_tableau=phase1_tableau,
                solution=None,
                optimal_value=None,
            )

        # Prepara il tableau per la fase II
        tableau_phase2, prep_steps = prepare_phase_two(phase1_tableau, standard_problem, options)
        all_steps.extend(prep_steps)

        if tableau_phase2 is None:
            error_result = SolveResult(
                status="input_error",
                message="Errore nella preparazione della fase II.",
                original_problem=original_problem,
                standard_problem=standard_problem,
                steps=all_steps,
                final_tableau=None,
                solution=None,
                optimal_value=None,
            )
            return error_result

        # Risolvi con il simplesso (fase II)
        final_tableau, simplex_steps, status = simplex(tableau_phase2, options)
        all_steps.extend(simplex_steps)

        # Estrai la soluzione
        if status == "optimal":
            solution = extract_solution(final_tableau, standard_problem)
            optimal_value = get_objective_value(final_tableau)

            # Se il problema originale era di massimo, cambia il segno del valore ottimo
            if original_problem.sense == "max":
                optimal_value = -optimal_value

            return SolveResult(
                status="optimal",
                message="Soluzione ottima trovata.",
                original_problem=original_problem,
                standard_problem=standard_problem,
                steps=all_steps,
                final_tableau=final_tableau,
                solution=solution,
                optimal_value=optimal_value,
            )
        elif status == "unbounded":
            return SolveResult(
                status="unbounded",
                message="Il problema è illimitato.",
                original_problem=original_problem,
                standard_problem=standard_problem,
                steps=all_steps,
                final_tableau=final_tableau,
                solution=None,
                optimal_value=None,
            )
        else:
            return SolveResult(
                status="iteration_limit",
                message="Limite massimo di iterazioni raggiunto.",
                original_problem=original_problem,
                standard_problem=standard_problem,
                steps=all_steps,
                final_tableau=final_tableau,
                solution=None,
                optimal_value=None,
            )


def extract_solution(
    final_tableau: "Tableau", standard_problem: "StandardProblem"
) -> dict[str, Fraction]:
    """
    Estrae la soluzione dal tableau finale.

    La soluzione pubblica contiene solo le variabili originali del problema.
    Le variabili slack/surplus sono variabili ausiliarie interne e non fanno
    parte della soluzione finale esposta all'utente.
    
    Per le variabili libere (non vincolate), la soluzione ricostruisce il valore
    originale da x_i = x_i+ - x_i-.

    Args:
        final_tableau: tableau finale
        standard_problem: problema in forma standard

    Returns:
        Dizionario {nome_variabile: valore}
    """
    solution = {}

    # Le variabili in base hanno il valore dell'RHS della loro riga
    rhs_values = get_rhs_values(final_tableau)

    # Inizializza solo le variabili originali a zero
    for name in standard_problem.var_names[: standard_problem.original_var_count]:
        solution[name] = Fraction(0)

    # Assegna i valori alle variabili in base
    for i, var_idx in enumerate(final_tableau.basis):
        if var_idx < standard_problem.original_var_count:
            solution[standard_problem.var_names[var_idx]] = rhs_values[i]

    # Ricostituisci le variabili libere da x_i = x_i+ - x_i-
    for free_var, (pos_idx, neg_idx) in standard_problem.free_var_map.items():
        val_pos = solution.get(standard_problem.var_names[pos_idx], Fraction(0))
        val_neg = solution.get(standard_problem.var_names[neg_idx], Fraction(0))
        value = val_pos - val_neg
        
        # Aggiorna la soluzione: rimuovi le variabili trasformate
        # e aggiungi la variabile originale
        if standard_problem.var_names[pos_idx] in solution:
            del solution[standard_problem.var_names[pos_idx]]
        if standard_problem.var_names[neg_idx] in solution:
            del solution[standard_problem.var_names[neg_idx]]
        
        # Aggiungi la variabile libera originale
        solution[free_var] = value

    return solution
