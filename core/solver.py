"""
Solver ad alto livello che coordina tutti i moduli.
"""

from fractions import Fraction
from .models import LinearProblem, SolveResult, SolverOptions, Step
from .parser import parse_problem
from .standard_form import to_standard_form
from .basis import find_identity_basis, basis_is_feasible
from .tableau import build_canonical_tableau, get_rhs_values, get_objective_value
from .simplex import simplex
from .two_phase import run_phase_one, prepare_phase_two


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

        # Risolvi con il simplesso
        final_tableau, simplex_steps, status = simplex(tableau, options)
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

    return solution
