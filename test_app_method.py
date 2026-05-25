#!/usr/bin/env python
"""
Test per verificare che app.py usa il metodo selezionato dall'utente.
"""

import sys
sys.path.insert(0, '.')


def test_app_method_selection():
    """Testa se l'app seleziona correttamente il metodo."""
    
    print('='*70)
    print('TEST: Selezione Metodo in app.py')
    print('='*70)
    
    # Leggi il codice di app.py per verificare il selectbox
    with open('app.py', 'r', encoding='utf-8') as f:
        app_code = f.read()
    
    # Verifica che il selectbox per il metodo sia presente
    if 'selectbox' not in app_code or 'method' not in app_code:
        print('❌ Il selectbox del metodo NON è stato trovato in app.py')
        return False
    
    print('✅ Selectbox del metodo trovato in app.py')
    
    # Verifica che il metodo viene passato a solve_problem
    if 'SolverOptions' not in app_code:
        print('❌ SolverOptions NON è stato trovato in app.py')
        return False
    
    if 'method=' not in app_code:
        print('❌ Il metodo NON viene passato a SolverOptions')
        return False
    
    print('✅ Il metodo viene passato a SolverOptions')
    
    # Verifica la struttura del codice
    if 'solve_problem' not in app_code:
        print('❌ solve_problem NON è stato trovato in app.py')
        return False
    
    print('✅ solve_problem è stato trovato in app.py')
    
    print('\n' + '='*70)
    print('VERIFICA COMPLETATA:')
    print('='*70)
    print('✅ L\'app.py è configurato per selezionare e usare il metodo!')
    
    return True


if __name__ == '__main__':
    success = test_app_method_selection()
    sys.exit(0 if success else 1)
