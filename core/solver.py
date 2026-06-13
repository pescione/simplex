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
from .dual_simplex import dual_simplex
from .dual import can_use_dual_simplex, identify_dual_infeasibility


def build_tableau_for_dual_simplex(
    standard_problem: "StandardProblem", basis: list[int], options: SolverOptions
) -> Optional["Tableau"]:
    """
    Prepara il tableau per il simplesso duale secondo il Lez14.
    
    Procedimento:
    1. Verifica ammissibilità duale (c >= 0)
    2. Nega le righe con RHS < 0 per avere ammissibilità duale nel tableau
    3. Costruisce il tableau canonico
    
    Args:
        standard_problem: problema in forma standard
        basis: base iniziale
        options: opzioni del solver
        
    Returns:
        Tableau pronto per il simplesso duale, o None se non ammissibile duale
    """
    # Verifica ammissibilità duale: c deve essere >= 0
    # (altrimenti il tableau non sarà ammissibile duale)
    if not all(c >= 0 for c in standard_problem.c):
        # Non ammissibile duale: non possiamo usare il duale
        return None
    
    # Copia il problema
    A = [row[:] for row in standard_problem.A]
    b = list(standard_problem.b)
    
    # Nega le righe con RHS < 0 (come nel Lez14)
    # Questo prepara il tableau per il duale:
    # - Ammissibilità duale: costi ridotti >= 0 (sono uguali a c)
    # - Inammissibilità primale: RHS potenzialmente < 0
    for i in range(len(b)):
        if b[i] < 0:
            A[i] = [-coeff for coeff in A[i]]
            b[i] = -b[i]
    
    # Costruisci il tableau canonico
    tableau = build_canonical_tableau(
        A=A,
        b=b,
        c=standard_problem.c,
        basis=basis,
        var_names=standard_problem.var_names,
        phase=2,
        objective_name="z",
    )
    
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
    # PERCORSO 1: SIMPLESSO DUALE (se richiesto esplicitamente)
    # ===================================================================
    if options.method == "dual_simplex":
        method_step = Step(
            title="Metodo risolutivo scelto: Simplesso Duale",
            description="Verrà utilizzato il metodo del simplesso duale (da Lez14).",
            notes=["Non verrà usata la fase I. Il duale parte da ammissibilità duale."],
        )
        all_steps.append(method_step)
        
        # Il simplesso duale richiede una base identità naturale
        # Se non la trovo, fallback alle due fasi (è un compromesso ragionevole)
        if basis is None:
            fallback_step = Step(
                title="Fallback alle due fasi",
                description="Non è stata trovata una base identità naturale. Il metodo duale richiede una base iniziale immediata. Fallback al metodo delle due fasi.",
                notes=["Il duale non è applicabile per questo problema."],
            )
            all_steps.append(fallback_step)
            # Procedi al PERCORSO 3 (Due fasi) usando la logica sotto
        else:
            # Costruisci il tableau per il simplesso duale con la base identità trovata
            try:
                tableau = build_tableau_for_dual_simplex(standard_problem, basis, options)
                if tableau is None:
                    # Il problema non è ammissibile duale
                    error_result = SolveResult(
                        status="input_error",
                        message="Il problema non è ammissibile duale. I coefficienti della funzione obiettivo (c) contengono valori negativi. Il simplesso duale richiede c >= 0.",
                        original_problem=original_problem,
                        standard_problem=standard_problem,
                        steps=all_steps,
                        final_tableau=None,
                        solution=None,
                        optimal_value=None,
                    )
                    return error_result
            except Exception as e:
                error_result = SolveResult(
                    status="input_error",
                    message=f"Errore nella costruzione del tableau per il simplesso duale: {str(e)}",
                    original_problem=original_problem,
                    standard_problem=standard_problem,
                    steps=all_steps,
                    final_tableau=None,
                    solution=None,
                    optimal_value=None,
                )
                return error_result
            
            # Risolvi con il simplesso duale
            final_tableau, simplex_steps, status = dual_simplex(tableau, options)
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
                    message="Soluzione ottima trovata con il simplesso duale.",
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
