"""
Test per il problema iniziale dell'utente.

Questo test verifica che il solver risolve correttamente il problema:

min
c = [3, 4, 6]
A = [
  [1, 3, 4],
  [2, 1, 3]
]
signs = ["=", "="]
b = [1, 2]

Soluzione attesa:
x1 = 1
x2 = 0
x3 = 0
z_min = 3
"""

import pytest
from fractions import Fraction
from core.solver import solve_problem


def test_example_initial_problem():
    """Test del problema iniziale con due vincoli di uguaglianza."""
    
    problem_text = """
    min
    c = [3, 4, 6]
    A = [
      [1, 3, 4],
      [2, 1, 3]
    ]
    signs = ["=", "="]
    b = [1, 2]
    """
    
    result = solve_problem(problem_text)
    
    # Verifiche di base
    assert result.status == "optimal", f"Status atteso 'optimal', ottenuto '{result.status}'. Messaggio: {result.message}"
    assert result.solution is not None, "Soluzione non trovata"
    assert result.optimal_value is not None, "Valore ottimo non trovato"
    
    # Verifiche sulla soluzione
    x1 = result.solution.get("x1", Fraction(0))
    x2 = result.solution.get("x2", Fraction(0))
    x3 = result.solution.get("x3", Fraction(0))
    
    print(f"Soluzione trovata: x1={x1}, x2={x2}, x3={x3}, z={result.optimal_value}")
    
    # La soluzione attesa è x1=1, x2=0, x3=0, z=3
    # Verifichiamo il vincolo Ax = b:
    # [1, 3, 4] · [x1, x2, x3] = 1*x1 + 3*x2 + 4*x3 = 1*1 + 3*0 + 4*0 = 1 ✓
    # [2, 1, 3] · [x1, x2, x3] = 2*x1 + 1*x2 + 3*x3 = 2*1 + 1*0 + 3*0 = 2 ✓
    
    # Controllo vincoli
    constraint1 = 1*x1 + 3*x2 + 4*x3
    constraint2 = 2*x1 + 1*x2 + 3*x3
    
    assert constraint1 == Fraction(1), f"Vincolo 1 non soddisfatto: {constraint1} != 1"
    assert constraint2 == Fraction(2), f"Vincolo 2 non soddisfatto: {constraint2} != 2"
    
    # Controllo valore obiettivo
    computed_z = 3*x1 + 4*x2 + 6*x3
    assert result.optimal_value == computed_z, \
        f"Valore obiettivo non corrisponde: z={result.optimal_value}, ma 3*x1 + 4*x2 + 6*x3 = {computed_z}"
    
    # Verifichiamo che z = 3
    assert result.optimal_value == Fraction(3), \
        f"Valore ottimo atteso 3, ottenuto {result.optimal_value}"


def test_simple_inequality_problem():
    """Test di un problema semplice con disuguaglianze."""
    
    problem_text = """
    min
    c = [1, 1]
    A = [
      [1, 0],
      [0, 1]
    ]
    signs = ["<=", "<="]
    b = [2, 3]
    """
    
    result = solve_problem(problem_text)
    
    assert result.status == "optimal", f"Status atteso 'optimal', ottenuto '{result.status}'. Messaggio: {result.message}"
    assert result.solution is not None
    assert result.optimal_value is not None
    
    # Per questo problema, la soluzione ottima dovrebbe essere x1=0, x2=0, z=0
    x1 = result.solution.get("x1", Fraction(0))
    x2 = result.solution.get("x2", Fraction(0))
    
    print(f"Soluzione semplice: x1={x1}, x2={x2}, z={result.optimal_value}")
    
    # Verifichiamo che sia ammissibile
    assert x1 >= 0 and x2 >= 0, f"Soluzione non ammissibile: x1={x1}, x2={x2}"
    assert x1 <= Fraction(2), f"Vincolo 1 violato: x1={x1} > 2"
    assert x2 <= Fraction(3), f"Vincolo 2 violato: x2={x2} > 3"
    
    # Valore obiettivo
    computed_z = x1 + x2
    assert result.optimal_value == computed_z, \
        f"Valore obiettivo non corrisponde: z={result.optimal_value}, ma x1 + x2 = {computed_z}"


def test_solution_contains_only_original_variables():
    """Test che la soluzione pubblica non esponga variabili ausiliarie."""

    problem_text = """
    min
    c = [1, 1]
    A = [
      [1, 0],
      [0, 1]
    ]
    signs = ["<=", "<="]
    b = [2, 3]
    """

    result = solve_problem(problem_text)

    assert result.status == "optimal"
    assert result.solution is not None
    assert set(result.solution.keys()) == {"x1", "x2"}


def test_max_problem():
    """Test di un problema di massimizzazione."""
    
    problem_text = """
    max
    c = [3, 2]
    A = [
      [1, 1],
      [1, 0],
      [0, 1]
    ]
    signs = ["<=", "<=", "<="]
    b = [4, 2, 3]
    """
    
    result = solve_problem(problem_text)
    
    assert result.status == "optimal", f"Status atteso 'optimal', ottenuto '{result.status}'. Messaggio: {result.message}"
    assert result.solution is not None
    assert result.optimal_value is not None
    
    x1 = result.solution.get("x1", Fraction(0))
    x2 = result.solution.get("x2", Fraction(0))
    
    print(f"Soluzione max: x1={x1}, x2={x2}, z={result.optimal_value}")
    
    # Verifichiamo i vincoli
    assert x1 + x2 <= Fraction(4), f"Vincolo 1 violato: {x1} + {x2} > 4"
    assert x1 <= Fraction(2), f"Vincolo 2 violato: {x1} > 2"
    assert x2 <= Fraction(3), f"Vincolo 3 violato: {x2} > 3"
    
    # Valore obiettivo
    computed_z = 3*x1 + 2*x2
    assert result.optimal_value == computed_z, \
        f"Valore obiettivo non corrisponde: z={result.optimal_value}, ma 3*x1 + 2*x2 = {computed_z}"


def test_infeasible_problem():
    """Test di un problema inammissibile."""
    
    problem_text = """
    min
    c = [1]
    A = [
      [1],
      [1]
    ]
    signs = [">=", "<="]
    b = [2, 1]
    """
    
    result = solve_problem(problem_text)
    
    # x >= 2 e x <= 1 è inammissibile
    assert result.status == "infeasible", \
        f"Status atteso 'infeasible', ottenuto '{result.status}'. Messaggio: {result.message}"


def test_unbounded_problem():
    """Test di un problema illimitato."""
    
    problem_text = """
    min
    c = [-1]
    A = [
      [1]
    ]
    signs = [">="]
    b = [0]
    """
    
    result = solve_problem(problem_text)
    
    # min -x con x >= 0 è illimitato inferiormente
    assert result.status == "unbounded", \
        f"Status atteso 'unbounded', ottenuto '{result.status}'. Messaggio: {result.message}"


def test_redundant_constraints_problem():
    """Test di un problema con un vincolo ridondante eliminato dopo la Fase I."""

    problem_text = """
    min
    c = [1]
    A = [
      [1],
      [2]
    ]
    signs = ["=", "="]
    b = [1, 2]
    """

    result = solve_problem(problem_text)

    assert result.status == "optimal", \
        f"Status atteso 'optimal', ottenuto '{result.status}'. Messaggio: {result.message}"
    assert result.solution is not None
    assert result.solution.get("x1", Fraction(0)) == Fraction(1)
    assert result.optimal_value == Fraction(1)


if __name__ == "__main__":
    test_example_initial_problem()
    test_simple_inequality_problem()
    test_max_problem()
    test_infeasible_problem()
    test_unbounded_problem()
    print("✅ Tutti i test passati!")
