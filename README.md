# 📊 Solver del Simplesso

Un'applicazione didattica interattiva per la risoluzione di problemi di programmazione lineare usando il metodo del simplesso. Implementata in Python con interfaccia Streamlit.

## 🎯 Caratteristiche

- **Trasformazione in forma standard**: Conversione automatica da max a min, aggiunta di slack/surplus
- **Metodo delle due fasi**: Ricerca di base ammissibile con variabili artificiali
- **Visualizzazione dettagliata**: Tableau e passaggi passo-passo
- **Rilevazione di casi speciali**: Problema illimitato, inammissibile, degenerazione
- **Aritmetica esatta**: Uso di `Fraction` per evitare errori di arrotondamento
- **Multiple strategie**: Regole diverse per la scelta della variabile entrante (most_negative, first_negative, bland)

## 📦 Installazione

### Requisiti
- Python 3.9+
- pip

### Setup

```bash
# Clone o download del progetto
cd simplex

# Installazione delle dipendenze
pip install -r requirements.txt
```

## 🚀 Utilizzo

### Lanciare l'applicazione Streamlit

```bash
streamlit run app.py
```

Quindi apri il browser e accedi a `http://localhost:8501`

### Formato dell'input

Usa il seguente formato per inserire il problema:

```
min
c = [3, 4, 6]
A = [
  [1, 3, 4],
  [2, 1, 3]
]
signs = ["=", "="]
b = [1, 2]
```

**Spiegazione:**
- Prima riga: `min` (minimizzazione) o `max` (massimizzazione)
- `c`: coefficienti della funzione obiettivo
- `A`: matrice dei coefficienti dei vincoli
- `signs`: verso di ogni vincolo (`<=`, `>=`, `=`)
- `b`: termini noti

**⚠️ Vincoli di non negatività:**
- Tutte le variabili sono **automaticamente non-negative** (`x ≥ 0`)
- **NON** è necessario specificarli esplicitamente nell'input
- Questo è il comportamento standard della programmazione lineare

**Numeri supportati:**
- Interi: `3`, `-2`
- Frazioni: `1/3`, `-5/7`
- Decimali: `0.5`, `-3.25`

### Esempi inclusi

L'applicazione include 3 esempi precaricati:

1. **Slack iniziale**: Problema con solo vincoli `<=` (necessita solo slack)
2. **Due fasi**: Problema con vincoli `=` (richiede variabili artificiali)
3. **Illimitato**: Problema che evidenzia la rilevazione di illimitatezza

## 🔧 Utilizzo da linea di comando

```python
from core.solver import solve_problem
from core.models import SolverOptions

# Definisci il problema
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

# Opzioni
options = SolverOptions(entering_var_rule="most_negative", max_iterations=100)

# Risolvi
result = solve_problem(problem_text, options)

# Accedi ai risultati
print(f"Status: {result.status}")
print(f"Solution: {result.solution}")
print(f"Optimal value: {result.optimal_value}")
```

## 📁 Struttura del progetto

```
simplex/
├── app.py                    # App principale Streamlit
├── core/
│   ├── models.py            # Strutture dati principali
│   ├── parser.py            # Parser dell'input
│   ├── standard_form.py     # Trasformazione forma standard
│   ├── basis.py             # Ricerca base iniziale
│   ├── matrices.py          # Operazioni su matrici
│   ├── tableau.py           # Costruzione tableau
│   ├── pivot.py             # Operazione di pivot
│   ├── simplex.py           # Algoritmo simplesso fase II
│   ├── two_phase.py         # Metodo delle due fasi
│   ├── solver.py            # Solver ad alto livello
│   └── formatting.py        # Formattazione per visualizzazione
├── tests/
│   ├── test_parser.py       # Test del parser
│   ├── test_standard_form.py # Test della forma standard
│   ├── test_basis.py        # Test ricerca base
│   ├── test_tableau.py      # Test tableau
│   ├── test_pivot.py        # Test pivot
│   ├── test_simplex.py      # Test simplesso
│   └── test_two_phase.py    # Test due fasi
├── requirements.txt         # Dipendenze
└── README.md               # Questo file
```

## 🧪 Esecuzione dei test

```bash
# Esegui tutti i test
pytest

# Con output verboso
pytest -v

# Test specifico
pytest tests/test_parser.py
```

## 📝 Esempi di problemi

### Problema 1: Massimizzazione con slack

```
max
c = [10, 12, 12]
A = [
  [1, 2, 2],
  [2, 1, 2],
  [2, 2, 1]
]
signs = ["<=", "<=", "<="]
b = [20, 20, 20]
```

Soluzione ottima: `x1 = 0, x2 = 10, x3 = 0` con valore `120`

### Problema 2: Due fasi

```
min
c = [3, 4, 6]
A = [
  [1, 3, 4],
  [2, 1, 3]
]
signs = ["=", "="]
b = [1, 2]
```

Questo problema richiede la fase I perché non c'è una base slack immediata.

### Problema 3: Problema illimitato

```
min
c = [-3, 2, 4, 0, 0]
A = [
  [-1, -1, 2, 1, 0],
  [1, -2, 1, 0, 1]
]
signs = ["=", "="]
b = [1, -1]
```

L'algoritmo rileva che il problema è illimitato.

## 🐛 Troubleshooting

### "Errore: La matrice non è invertibile"

Questo significa che la base selezionata è singolare (le colonne non sono linearmente indipendenti).

### "Limite massimo di iterazioni raggiunto"

Il problema potrebbe avere degenerazione o cicli. Prova con la regola `bland` che è più robusta.

### Errori di parsing

Controlla che:
- Le liste siano tra `[` e `]`
- Le matrici siano tra `[[` e `]]`
- I numeri siano validi (interi, frazioni, decimali)
- Il numero di colonne di A corrisponda alla lunghezza di c

## 📚 Riferimenti matematici

### Forma standard
```
min c^T x
Ax = b
x ≥ 0
```

### Tableau canonico
```
       x1   x2   ...   xn | RHS
z      c1   c2   ...   cn | obj
v1     a11  a12  ...  a1n | b1
v2     a21  a22  ...  a2n | b2
...
```

### Metodo delle due fasi

**Fase I**: Minimizza la somma delle variabili artificiali per trovare una base ammissibile
**Fase II**: Minimizza la funzione obiettivo originale partendo dalla base trovata in Fase I

## 💡 Note di implementazione

- Usa `Fraction` dal modulo `fractions` per aritmetica esatta
- Implementazione senza NumPy per mantenere esattezza
- Algoritmi di Gauss-Jordan per inversione matriciale
- Supporta la regola di Bland per evitare cicli

## 📄 Licenza

MIT License

## 👤 Autore

Applicazione didattica per l'insegnamento del metodo del simplesso.

---

**Versione**: 1.0.0  
**Ultimo aggiornamento**: 2026
