#!/usr/bin/env python
"""
Test per il simplesso duale con base identità naturale (vincoli <=)
"""

import sys
sys.path.insert(0, '.')

from core.models import SolverOptions
from core.solver import solve_problem


def test_dual_with_natural_identity_basis():
    """
    Testa il duale con un problema che ha una base identità naturale.
    Vincoli <=: producono slack che formano la base identità.
    """
    
    # Problema con vincoli <=: ha base identità naturale
    problem = """min
c = [2, 3]
A = [
  [1, 1],
  [2, 1]
]
signs = ["<=", "<="]
b = [4, 5]
"""

    print('='*70)
    print('TEST: Simplesso Duale con Base Identità Naturale (Vincoli <=)')
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
    
    # Verifica che NON contiene "Fallback" e Fase I
    has_fallback = any('Fallback' in s.title for s in result_dual.steps)
    has_phase_1 = any('Fase I' in s.title for s in result_dual.steps)
    has_dual = any('Simplesso Duale' in s.title for s in result_dual.steps)
    
    print(f'\n✓ Contiene "Fallback": {has_fallback}')
    print(f'✓ Contiene "Fase I": {has_phase_1}')
    print(f'✓ Contiene "Simplesso Duale": {has_dual}')
    
    print('\nStep eseguiti:')
    for i, step in enumerate(result_dual.steps, 1):
        print(f'  {i}. {step.title}')

    # Test 2: Con due fasi per confronto
    print('\n' + '='*70)
    print('\n2️⃣  DUE FASI (method="two_phase"):')
    print('-'*70)
    options_two_phase = SolverOptions(method='two_phase', max_iterations=100)
    result_two_phase = solve_problem(problem, options_two_phase)
    
    print(f'Status: {result_two_phase.status}')
    print(f'Soluzione: {result_two_phase.solution}')
    print(f'Valore: {result_two_phase.optimal_value}')
    print(f'Numero di step: {len(result_two_phase.steps)}')

    # Verifica
    print('\n' + '='*70)
    print('\nVERIFICA RISULTATI:')
    print('-'*70)
    
    if result_dual.status != result_two_phase.status:
        print(f'❌ Status diversi: {result_dual.status} vs {result_two_phase.status}')
        return False
    
    if result_dual.optimal_value != result_two_phase.optimal_value:
        print(f'❌ Valori diversi: {result_dual.optimal_value} vs {result_two_phase.optimal_value}')
        return False
    
    if has_fallback:
        print('❌ Il duale ha fatto fallback alle due fasi (non dovrebbe!).')
        print('   Per vincoli <=, dovrebbe trovarsi la base identità naturale.')
        return False
    
    if has_phase_1:
        print('❌ Il duale ha usato la Fase I (non dovrebbe!).')
        return False
    
    if not has_dual:
        print('❌ Il simplesso duale NON è stato usato!')
        return False
    
    print('✅ SUCCESSO!')
    print(f'   - Entrambi i metodi convergono al valore: {result_dual.optimal_value}')
    print(f'   - Duale: {len(result_dual.steps)} step (SENZA Fallback e SENZA Fase I)')
    print(f'   - Due fasi: {len(result_two_phase.steps)} step')
    print(f'   - Il duale ha usato direttamente la base identità naturale!')
    
    return True


if __name__ == '__main__':
    success = test_dual_with_natural_identity_basis()
    sys.exit(0 if success else 1)
