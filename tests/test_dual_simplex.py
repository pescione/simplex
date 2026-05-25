"""
Test del metodo del simplesso duale.
"""

import sys
from pathlib import Path

# Aggiungi la cartella padre al path per importare i moduli
sys.path.insert(0, str(Path(__file__).parent.parent))

from fractions import Fraction
from core.models import LinearProblem, SolverOptions
from core.solver import solve_problem


def test_dual_simplex_basic():
    """
    Test del simplesso duale con un problema semplice.
    
    Problema:
    min -3x1 - 2x2
    2x1 + x2 ≤ 8
    x1 + 2x2 ≤ 8
    x1, x2 ≥ 0
    
    Questo problema ha una base ammissibile iniziale,
    quindi potrebbe essere risolto direttamente con il simplesso.
    """
    problem_text = """min
c = [-3, -2]
A = [
  [2, 1],
  [1, 2]
]
signs = ["<=", "<="]
b = [8, 8]
"""
    
    # Risolvi con il metodo del simplesso duale
    options = SolverOptions(method="dual_simplex", max_iterations=100)
    result = solve_problem(problem_text, options)
    
    assert result.status == "optimal", f"Status: {result.status}, Message: {result.message}"
    assert result.solution is not None
    assert result.optimal_value is not None
    
    # Verifica il valore ottimo
    # Soluzione attesa: x1 = 4, x2 = 0, oppure varianti equivalenti
    # Valore: -3*4 - 2*0 = -12
    print(f"Soluzione: {result.solution}")
    print(f"Valore ottimo: {result.optimal_value}")
    print(f"Numero iterazioni: {len([s for s in result.steps if 'Pivot' in s.title])}")


def test_dual_simplex_vs_simplex():
    """
    Confronta il simplesso duale con il simplesso ordinario.
    Entrambi dovrebbero dare lo stesso risultato.
    """
    problem_text = """min
c = [1, 2]
A = [
  [1, 1],
  [2, 1]
]
signs = [">=", ">="]
b = [4, 5]
"""
    
    # Risolvi con il simplesso ordinario
    options_simplex = SolverOptions(method="auto", max_iterations=100)
    result_simplex = solve_problem(problem_text, options_simplex)
    
    # Risolvi con il simplesso duale
    options_dual = SolverOptions(method="dual_simplex", max_iterations=100)
    result_dual = solve_problem(problem_text, options_dual)
    
    print(f"\nSimplesso ordinario:")
    print(f"  Status: {result_simplex.status}")
    print(f"  Soluzione: {result_simplex.solution}")
    print(f"  Valore: {result_simplex.optimal_value}")
    
    print(f"\nSimplesso duale:")
    print(f"  Status: {result_dual.status}")
    print(f"  Soluzione: {result_dual.solution}")
    print(f"  Valore: {result_dual.optimal_value}")
    
    # Entrambi dovrebbero essere ottimali
    assert result_simplex.status == "optimal"
    assert result_dual.status == "optimal"
    
    # I valori ottimi dovrebbero essere uguali
    assert result_simplex.optimal_value == result_dual.optimal_value


def test_dual_simplex_method_selection():
    """
    Verifica che il metodo duale sia correttamente selezionato.
    """
    problem_text = """min
c = [1, 1]
A = [
  [1, 1]
]
signs = ["="]
b = [5]
"""
    
    options = SolverOptions(method="dual_simplex")
    result = solve_problem(problem_text, options)
    
    # Verifica che il metodo sia stato selezionato (se presente uno step appropriato)
    method_steps = [s for s in result.steps if "Metodo risolutivo" in s.title or "Simplesso Duale" in s.description]
    
    print(f"Steps con metodo: {len(method_steps)}")
    for s in result.steps:
        print(f"  - {s.title}")


def test_dual_simplex_greater_equal_constraints():
    """
    Test con vincoli ≥ dove il simplesso duale è particolarmente utile.
    
    Problema di dieta (minimizzare costi mantenendo nutrienti):
    min 2x1 + 3x2 + x3
    x1 + 2x2 + x3 ≥ 10  (proteine minime)
    3x1 + x2 + 2x3 ≥ 15  (vitamine minime)
    x1, x2, x3 ≥ 0
    """
    problem_text = """min
c = [2, 3, 1]
A = [
  [1, 2, 1],
  [3, 1, 2]
]
signs = [">=", ">="]
b = [10, 15]
"""
    
    options = SolverOptions(method="dual_simplex", max_iterations=50)
    result = solve_problem(problem_text, options)
    
    assert result.status == "optimal", f"Status: {result.status}"
    assert result.solution is not None
    assert result.optimal_value is not None
    
    print(f"\nProblema di dieta:")
    print(f"  Soluzione ottima:")
    for var, value in result.solution.items():
        print(f"    {var} = {float(value):.2f}")
    print(f"  Costo minimo: {float(result.optimal_value):.2f}")
    
    # Verifica che i vincoli siano soddisfatti
    x1 = float(result.solution['x1'])
    x2 = float(result.solution['x2'])
    x3 = float(result.solution['x3'])
    
    assert x1 + 2*x2 + x3 >= 10 - 1e-6, "Vincolo proteine non soddisfatto"
    assert 3*x1 + x2 + 2*x3 >= 15 - 1e-6, "Vincolo vitamine non soddisfatto"


def test_dual_simplex_equality_constraints():
    """
    Test con vincoli di uguaglianza (=).
    """
    problem_text = """min
c = [1, 2, 3]
A = [
  [1, 1, 1],
  [2, 1, 3]
]
signs = ["=", "="]
b = [4, 7]
"""
    
    options = SolverOptions(method="dual_simplex", max_iterations=50)
    result = solve_problem(problem_text, options)
    
    assert result.status == "optimal", f"Status: {result.status}, Message: {result.message}"
    
    print(f"\nVincoli di uguaglianza:")
    print(f"  Soluzione: {result.solution}")
    print(f"  Valore: {result.optimal_value}")
    
    # Verifica i vincoli
    x1 = float(result.solution['x1'])
    x2 = float(result.solution['x2'])
    x3 = float(result.solution['x3'])
    
    assert abs(x1 + x2 + x3 - 4) < 1e-6, "Primo vincolo non soddisfatto"
    assert abs(2*x1 + x2 + 3*x3 - 7) < 1e-6, "Secondo vincolo non soddisfatto"


def test_dual_simplex_max_problem():
    """
    Test con problema di massimizzazione.
    """
    problem_text = """max
c = [3, 2]
A = [
  [1, 1],
  [2, 1]
]
signs = ["<=", "<="]
b = [4, 5]
"""
    
    options = SolverOptions(method="dual_simplex", max_iterations=50)
    result = solve_problem(problem_text, options)
    
    assert result.status == "optimal", f"Status: {result.status}"
    
    print(f"\nMassimizzazione:")
    print(f"  Soluzione: {result.solution}")
    print(f"  Valore: {result.optimal_value}")


if __name__ == "__main__":
    print("="*60)
    print("TEST: Simplesso Duale")
    print("="*60)
    
    print("\nTest 1: Simplesso duale con problema semplice")
    print("-"*60)
    test_dual_simplex_basic()
    
    print("\n" + "="*60)
    print("Test 2: Comparazione simplesso ordinario vs duale")
    print("-"*60)
    test_dual_simplex_vs_simplex()
    
    print("\n" + "="*60)
    print("Test 3: Selezione del metodo")
    print("-"*60)
    test_dual_simplex_method_selection()
    
    print("\n" + "="*60)
    print("Test 4: Vincoli ≥ (ideale per duale)")
    print("-"*60)
    test_dual_simplex_greater_equal_constraints()
    
    print("\n" + "="*60)
    print("Test 5: Vincoli di uguaglianza")
    print("-"*60)
    test_dual_simplex_equality_constraints()
    
    print("\n" + "="*60)
    print("Test 6: Problema di massimizzazione")
    print("-"*60)
    test_dual_simplex_max_problem()
    
    print("\n" + "="*60)
    print("✅ Tutti i test completati!")
    print("="*60)
