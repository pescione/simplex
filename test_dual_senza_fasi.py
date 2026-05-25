#!/usr/bin/env python
"""
Test per verificare che il simplesso duale usa davvero il duale
senza passare per le due fasi.
"""

import sys
sys.path.insert(0, '.')

from core.models import SolverOptions
from core.solver import solve_problem


def test_dual_vs_two_phase():
    """Confronta il simplesso duale con le due fasi."""
    
    # Problema ideale per il duale (vincoli >=)
    problem = """min
c = [2, 3]
A = [
  [1, 1],
  [2, 1]
]
signs = [">=", ">="]
b = [4, 5]
"""

    print('='*70)
    print('TEST: Simplesso Duale vs Due Fasi')
    print('='*70)

    # Test 1: Con duale
    print('\n1️⃣  SIMPLESSO DUALE (method="dual_simplex"):')
    print('-'*70)
    options_dual = SolverOptions(method='dual_simplex', max_iterations=100)
    result_dual = solve_problem(problem, options_dual)
    
    print(f'Status: {result_dual.status}')
    print(f'Soluzione: {result_dual.solution}')
    print(f'Valore: {result_dual.optimal_value}')
    print(f'Numero di step: {len(result_dual.steps)}')
    print('\nStep eseguiti:')
    for i, step in enumerate(result_dual.steps, 1):
        print(f'  {i}. {step.title}')
    
    # Verifica che non ci siano step delle due fasi
    has_phase_1 = any('Fase I' in s.title or 'artificiale' in s.title.lower() 
                      for s in result_dual.steps)
    has_dual = any('Simplesso Duale' in s.title or 'duale' in s.title.lower() 
                   for s in result_dual.steps)
    
    print(f'\n✓ Contiene step "Fase I": {has_phase_1}')
    print(f'✓ Contiene step "Simplesso Duale": {has_dual}')

    # Test 2: Con due fasi
    print('\n' + '='*70)
    print('\n2️⃣  DUE FASI (method="two_phase"):')
    print('-'*70)
    options_two_phase = SolverOptions(method='two_phase', max_iterations=100)
    result_two_phase = solve_problem(problem, options_two_phase)
    
    print(f'Status: {result_two_phase.status}')
    print(f'Soluzione: {result_two_phase.solution}')
    print(f'Valore: {result_two_phase.optimal_value}')
    print(f'Numero di step: {len(result_two_phase.steps)}')
    print('\nStep eseguiti:')
    for i, step in enumerate(result_two_phase.steps, 1):
        print(f'  {i}. {step.title}')

    # Verifica risultati
    print('\n' + '='*70)
    print('\nVERIFICA RISULTATI:')
    print('-'*70)
    
    if result_dual.status != result_two_phase.status:
        print(f'❌ Status diversi: {result_dual.status} vs {result_two_phase.status}')
        return False
    
    if result_dual.optimal_value != result_two_phase.optimal_value:
        print(f'❌ Valori diversi: {result_dual.optimal_value} vs {result_two_phase.optimal_value}')
        return False
    
    if not has_dual:
        print('❌ Il simplesso duale NON è stato scelto!')
        return False
    
    print('✅ SUCCESSO!')
    print(f'   - Entrambi i metodi convergono al valore: {result_dual.optimal_value}')
    print(f'   - Simplesso duale: {len(result_dual.steps)} step')
    print(f'   - Due fasi: {len(result_two_phase.steps)} step')
    
    return True


if __name__ == '__main__':
    success = test_dual_vs_two_phase()
    sys.exit(0 if success else 1)
