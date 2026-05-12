# Roadmap completa — Programma per il Simplesso con Python, `Fraction` e Streamlit

## 0. Obiettivo del progetto

L'obiettivo è costruire un'applicazione didattica che, dato un problema di programmazione lineare scritto in forma grezza, restituisca tutti i passaggi necessari per arrivare al tableau canonico e poi, opzionalmente, alla soluzione ottima tramite il metodo del simplesso.

Il programma dovrà:

1. leggere una funzione obiettivo e un insieme di vincoli;
2. normalizzare il problema;
3. trasformarlo in forma standard;
4. cercare una base ammissibile iniziale;
5. se la base iniziale non esiste, costruire e risolvere il problema artificiale con il metodo delle due fasi;
6. costruire il tableau canonico rispetto alla base corrente;
7. mostrare tutti i passaggi in una GUI Streamlit;
8. permettere all'utente di vedere tableau, pivot, variabili entranti/uscenti, test dei rapporti, test di ottimalità e diagnosi finale.

Il programma deve essere progettato in modo modulare: la GUI non deve contenere la logica matematica. La logica del simplesso deve stare in moduli separati, testabili anche da terminale.

---

## 1. Scelte tecnologiche

### Linguaggio

Usare **Python**.

Motivi:

- è semplice da leggere;
- ha buone librerie per interfacce rapide;
- supporta `fractions.Fraction`, utile per lavorare con numeri razionali esatti;
- permette di separare facilmente logica matematica, parser e GUI.

### Aritmetica

Usare **`Fraction`** dal modulo standard `fractions`.

Motivo principale: il metodo del simplesso produce spesso frazioni. Usando `float`, i tableau diventano rapidamente poco leggibili, ad esempio:

```text
0.3333333333333333
```

invece di:

```text
1/3
```

Con `Fraction`, invece, puoi mostrare passaggi esatti come nelle slide.

### GUI

Usare **Streamlit**.

Motivi:

- permette di creare rapidamente una web app locale;
- è ideale per visualizzare tabelle, testi, formule e passaggi;
- non richiede una gestione complessa di finestre, eventi e layout;
- è perfetta per un progetto didattico/interattivo.

---

## 2. Architettura generale del progetto

Struttura consigliata:

```text
simplex_streamlit/
│
├── app.py
│
├── core/
│   ├── __init__.py
│   ├── models.py
│   ├── parser.py
│   ├── standard_form.py
│   ├── basis.py
│   ├── tableau.py
│   ├── pivot.py
│   ├── simplex.py
│   ├── two_phase.py
│   ├── solver.py
│   └── formatting.py
│
├── ui/
│   ├── __init__.py
│   ├── input_panel.py
│   ├── steps_panel.py
│   ├── tableau_panel.py
│   └── examples.py
│
├── tests/
│   ├── test_parser.py
│   ├── test_standard_form.py
│   ├── test_basis.py
│   ├── test_tableau.py
│   ├── test_pivot.py
│   ├── test_simplex.py
│   └── test_two_phase.py
│
├── examples/
│   ├── example_01_slack.json
│   ├── example_02_two_phase.json
│   └── example_03_unbounded.json
│
├── requirements.txt
└── README.md
```

---

## 3. Flusso completo dei dati

Il flusso logico deve essere questo:

```text
Input utente
   ↓
Parser
   ↓
LinearProblem
   ↓
Normalizzazione
   ↓
Problema in forma standard
   ↓
Ricerca base iniziale
   ↓
Se base trovata → costruzione tableau fase II
   ↓
Se base non trovata → costruzione problema artificiale → fase I
   ↓
Tableau canonico
   ↓
Simplesso
   ↓
Step log
   ↓
Output Streamlit
```

La GUI comunica solo con un modulo principale, ad esempio `solver.py`.

Streamlit non deve chiamare direttamente funzioni come `pivot()`, `build_tableau()` o `find_basis()`. Deve chiamare una funzione ad alto livello:

```python
solve_problem(raw_input: RawProblemInput, options: SolverOptions) -> SolveResult
```

Questa funzione restituisce un oggetto contenente:

- problema originale;
- forma standard;
- eventuale problema artificiale;
- lista dei passaggi;
- tableau finali;
- soluzione;
- stato finale: ottimo, illimitato, inammissibile, errore di input.

---

## 4. Modelli dati principali

Nel file:

```text
core/models.py
```

conviene definire tutte le strutture dati condivise.

### 4.1 `LinearProblem`

Rappresenta il problema originale o già normalizzato.

```python
@dataclass
class LinearProblem:
    sense: str
    c: list[Fraction]
    A: list[list[Fraction]]
    signs: list[str]
    b: list[Fraction]
    var_names: list[str]
```

Campi:

- `sense`: `"min"` oppure `"max"`;
- `c`: coefficienti della funzione obiettivo;
- `A`: matrice dei vincoli;
- `signs`: lista contenente `"<="`, `">="`, `"="`;
- `b`: termini noti;
- `var_names`: nomi delle variabili originali, ad esempio `x1`, `x2`, `x3`.

---

### 4.2 `StandardProblem`

Rappresenta il problema in forma standard:

```text
min c^T x
Ax = b
x >= 0
```

```python
@dataclass
class StandardProblem:
    c: list[Fraction]
    A: list[list[Fraction]]
    b: list[Fraction]
    var_names: list[str]
    original_var_count: int
    slack_vars: list[int]
    surplus_vars: list[int]
    artificial_vars: list[int]
    transformation_log: list[str]
```

Campi importanti:

- `slack_vars`: indici delle variabili slack;
- `surplus_vars`: indici delle variabili surplus;
- `artificial_vars`: indici delle variabili artificiali, se aggiunte;
- `transformation_log`: descrizione testuale delle trasformazioni fatte.

---

### 4.3 `Tableau`

Rappresenta un tableau del simplesso.

```python
@dataclass
class Tableau:
    data: list[list[Fraction]]
    basis: list[int]
    var_names: list[str]
    phase: int
    objective_name: str
```

Convenzione consigliata:

- `data[0]` è la riga della funzione obiettivo;
- `data[1:]` sono le righe dei vincoli;
- l'ultima colonna è il termine noto;
- `basis[i]` è l'indice della variabile in base nella riga `i + 1`.

Esempio concettuale:

```text
       x1   x2   s1   s2 | RHS
z     -3   -2    0    0 | 0
s1     1    1    1    0 | 4
s2     2    1    0    1 | 5
```

---

### 4.4 `Step`

Ogni passaggio mostrato nella GUI deve essere salvato come oggetto.

```python
@dataclass
class Step:
    title: str
    description: str
    phase: int | None
    tableau_before: Tableau | None
    tableau_after: Tableau | None
    entering_var: str | None
    leaving_var: str | None
    pivot_row: int | None
    pivot_col: int | None
    ratios: list[tuple[str, Fraction]] | None
    notes: list[str]
```

Esempi di step:

- `Normalizzazione del problema`;
- `Aggiunta variabili slack`;
- `Costruzione problema artificiale`;
- `Tableau iniziale fase I`;
- `Iterazione 1: scelta variabile entrante`;
- `Test dei rapporti`;
- `Pivot`;
- `Passaggio alla fase II`;
- `Soluzione ottima`.

---

### 4.5 `SolveResult`

Risultato finale del solver.

```python
@dataclass
class SolveResult:
    status: str
    message: str
    original_problem: LinearProblem
    standard_problem: StandardProblem | None
    steps: list[Step]
    final_tableau: Tableau | None
    solution: dict[str, Fraction] | None
    optimal_value: Fraction | None
```

Valori possibili per `status`:

```text
"optimal"
"unbounded"
"infeasible"
"input_error"
"iteration_limit"
```

---

## 5. Parser dell'input

File:

```text
core/parser.py
```

### 5.1 Prima versione consigliata

Per evitare un parser troppo difficile, partire da un input semi-strutturato.

Esempio:

```text
min
c = [-10, -12, -12]
A = [
  [1, 2, 2],
  [2, 1, 2],
  [2, 2, 1]
]
signs = ["<=", "<=", "<="]
b = [20, 20, 20]
```

La funzione principale sarà:

```python
def parse_problem(text: str) -> LinearProblem:
    ...
```

Responsabilità:

1. leggere il verso della funzione obiettivo;
2. leggere `c`, `A`, `signs`, `b`;
3. convertire interi, decimali e frazioni in `Fraction`;
4. controllare che le dimensioni siano coerenti;
5. generare i nomi delle variabili originali.

---

### 5.2 Funzioni interne utili

```python
def parse_fraction(value: str) -> Fraction:
    ...
```

Deve accettare:

```text
"3"
"-2"
"1/3"
"-5/7"
"0.5"
```

```python
def validate_dimensions(c, A, signs, b) -> None:
    ...
```

Deve controllare:

- numero colonne di `A` uguale alla lunghezza di `c`;
- numero righe di `A` uguale alla lunghezza di `b`;
- numero segni uguale al numero di vincoli;
- segni ammessi solo `<=`, `>=`, `=`.

---

## 6. Normalizzazione e forma standard

File:

```text
core/standard_form.py
```

### 6.1 Funzione principale

```python
def to_standard_form(problem: LinearProblem) -> tuple[StandardProblem, list[Step]]:
    ...
```

Questa funzione trasforma il problema grezzo in forma:

```text
min c^T x
Ax = b
x >= 0
```

restituendo anche gli step descrittivi da mostrare nella GUI.

---

### 6.2 Trasformazione `max` → `min`

Se il problema è:

```text
max c^T x
```

lo trasformi in:

```text
min -c^T x
```

Devi salvare nel log:

```text
Il problema è di massimo. Moltiplico la funzione obiettivo per -1 per ottenere un problema di minimo.
```

---

### 6.3 Gestione di `b_i < 0`

Se un vincolo ha termine noto negativo, moltiplica tutta la riga per `-1` e inverti il verso:

```text
a_i x <= -5
```

diventa:

```text
-a_i x >= 5
```

Regole:

```text
<= diventa >=
>= diventa <=
= rimane =
```

---

### 6.4 Aggiunta variabili slack

Per vincoli:

```text
a_i x <= b_i
```

aggiungi:

```text
+s_i
```

ottenendo:

```text
a_i x + s_i = b_i
s_i >= 0
```

---

### 6.5 Aggiunta variabili surplus

Per vincoli:

```text
a_i x >= b_i
```

aggiungi:

```text
-s_i
```

ottenendo:

```text
a_i x - s_i = b_i
s_i >= 0
```

---

### 6.6 Vincoli di uguaglianza

Per vincoli:

```text
a_i x = b_i
```

non aggiungi slack o surplus. Tuttavia, probabilmente servirà una variabile artificiale nella fase I se non esiste una colonna identità utilizzabile come base.

---

## 7. Ricerca della base iniziale

File:

```text
core/basis.py
```

### 7.1 Funzione principale

```python
def find_identity_basis(A: list[list[Fraction]]) -> list[int] | None:
    ...
```

Scopo: cercare colonne di `A` che formino una matrice identità.

Se `A` ha `m` righe, serve trovare `m` colonne tali che:

```text
[1,0,0,...]^T
[0,1,0,...]^T
...
[0,0,...,1]^T
```

Se esistono, restituisci gli indici delle colonne. Se non esistono, restituisci `None`.

---

### 7.2 Funzioni utili

```python
def is_unit_column(A, col_index) -> tuple[bool, int | None]:
    ...
```

Restituisce:

- `True` se la colonna è una colonna dell'identità;
- l'indice della riga dove compare l'1.

```python
def basis_is_feasible(A, b, basis) -> bool:
    ...
```

Controlla se:

```text
B^{-1}b >= 0
```

Nel caso di base identità e `b >= 0`, la base è direttamente ammissibile.

---

## 8. Costruzione del tableau canonico

File:

```text
core/tableau.py
```

### 8.1 Funzione principale

```python
def build_canonical_tableau(
    A: list[list[Fraction]],
    b: list[Fraction],
    c: list[Fraction],
    basis: list[int],
    var_names: list[str],
    phase: int,
    objective_name: str
) -> Tableau:
    ...
```

Dato un problema:

```text
min c^T x
Ax = b
x >= 0
```

con base `B`, il tableau canonico si costruisce calcolando:

```text
B^{-1}b
B^{-1}F
c_F^T - c_B^T B^{-1}F
-c_B^T B^{-1}b
```

La forma concettuale è:

```text
0^T    c_F^T - c_B^T B^{-1}F    | -c_B^T B^{-1}b
I      B^{-1}F                  | B^{-1}b
```

---

### 8.2 Funzioni di algebra razionale

Non usare `numpy` per la parte esatta, perché `numpy` lavora normalmente con float.

Implementa funzioni su liste di `Fraction`:

```python
def matrix_inverse(M: list[list[Fraction]]) -> list[list[Fraction]]:
    ...
```

```python
def matrix_vector_mul(M, v):
    ...
```

```python
def matrix_matrix_mul(A, B):
    ...
```

```python
def dot(u, v):
    ...
```

Per l'inversa puoi usare Gauss-Jordan con `Fraction`.

---

## 9. Pivot sul tableau

File:

```text
core/pivot.py
```

### 9.1 Funzione principale

```python
def pivot(tableau: Tableau, pivot_row: int, pivot_col: int) -> Tableau:
    ...
```

La riga `pivot_row` è riferita alle righe dei vincoli, non alla riga 0. Conviene adottare una convenzione chiara:

- `pivot_row = 1` indica la prima riga dei vincoli nel tableau completo;
- `pivot_col = 0` indica la prima variabile.

Algoritmo pratico:

1. prendi l'elemento pivot;
2. dividi tutta la riga pivot per l'elemento pivot;
3. per ogni altra riga, compresa la riga 0, sottrai un multiplo della riga pivot normalizzata per azzerare la colonna pivot;
4. aggiorna la base.

---

### 9.2 Informazioni da registrare

Ogni pivot deve generare uno `Step` con:

- variabile entrante;
- variabile uscente;
- elemento pivot;
- riga pivot;
- colonna pivot;
- tableau prima;
- tableau dopo;
- operazioni di riga effettuate.

---

## 10. Simplesso fase II

File:

```text
core/simplex.py
```

### 10.1 Funzione principale

```python
def simplex(
    tableau: Tableau,
    options: SolverOptions
) -> tuple[Tableau, list[Step], str]:
    ...
```

Questa funzione risolve un tableau già canonico.

---

### 10.2 Test di ottimalità

Per un problema di minimo, il tableau è ottimo se tutti i costi ridotti delle variabili fuori base sono maggiori o uguali a zero:

```python
def is_optimal(tableau: Tableau) -> bool:
    return all(c >= 0 for c in reduced_costs)
```

---

### 10.3 Scelta della variabile entrante

Funzione:

```python
def choose_entering_variable(tableau: Tableau, rule: str) -> int | None:
    ...
```

Strategie possibili:

1. `most_negative`: scegli il costo ridotto più negativo;
2. `first_negative`: scegli la prima colonna con costo ridotto negativo;
3. `bland`: scegli la variabile con indice minimo tra quelle con costo ridotto negativo.

Per iniziare, implementa `most_negative`. Poi aggiungi Bland per gestire meglio casi degeneri.

---

### 10.4 Test di illimitatezza

Una volta scelta la colonna entrante `h`, se tutti i coefficienti della colonna nei vincoli sono `<= 0`, il problema è illimitato.

```python
def is_unbounded(tableau: Tableau, entering_col: int) -> bool:
    return all(row[entering_col] <= 0 for row in tableau.data[1:])
```

---

### 10.5 Test dei rapporti

Funzione:

```python
def choose_leaving_variable(tableau: Tableau, entering_col: int) -> tuple[int, list[tuple[int, Fraction]]]:
    ...
```

Per ogni riga con coefficiente positivo nella colonna entrante, calcola:

```text
RHS_i / a_i,h
```

Scegli la riga con rapporto minimo.

In caso di pareggio:

- versione semplice: scegli la prima;
- versione robusta: usa la regola di Bland sulla variabile uscente.

---

### 10.6 Loop principale

Pseudocodice:

```text
while True:
    se tableau ottimo:
        restituisci soluzione ottima

    scegli variabile entrante

    se colonna entrante ha tutti coefficienti <= 0:
        STOP: problema illimitato

    esegui test dei rapporti

    scegli variabile uscente

    fai pivot

    salva lo step
```

Aggiungi sempre un limite massimo di iterazioni:

```python
max_iterations = 100
```

per evitare loop infiniti in caso di bug.

---

## 11. Metodo delle due fasi

File:

```text
core/two_phase.py
```

### 11.1 Quando serve la fase I

La fase I serve quando, dopo la forma standard, non si trova una base ammissibile iniziale.

Esempi tipici:

- vincoli `=`;
- vincoli `>=`;
- assenza di una matrice identità nelle colonne di `A`.

---

### 11.2 Costruzione del problema artificiale

Funzione:

```python
def build_artificial_problem(std: StandardProblem) -> tuple[StandardProblem, list[int], list[Step]]:
    ...
```

Dato:

```text
min c^T x
Ax = b
x >= 0
```

costruisci:

```text
min y1 + y2 + ... + ym
Ax + Iy = b
x, y >= 0
```

Le variabili artificiali formano una base iniziale immediata.

---

### 11.3 Fase I

Procedura:

1. costruisci il problema artificiale;
2. usa come base iniziale le variabili artificiali;
3. costruisci il tableau canonico della fase I;
4. risolvi con `simplex()`;
5. leggi il valore ottimo `w*`.

Se:

```text
w* > 0
```

allora il problema originale è inammissibile.

Se:

```text
w* = 0
```

allora esiste una soluzione ammissibile per il problema originale e puoi passare alla fase II.

---

### 11.4 Eliminazione delle variabili artificiali

Funzione:

```python
def remove_artificial_variables(
    phase1_tableau: Tableau,
    artificial_indices: list[int]
) -> tuple[Tableau, list[Step]]:
    ...
```

Ci sono due casi.

#### Caso A — tutte le artificiali sono fuori base

Procedura:

1. elimina le colonne artificiali;
2. ripristina la funzione obiettivo originale;
3. ricostruisci la riga 0 in forma canonica rispetto alla base corrente;
4. passa alla fase II.

#### Caso B — una o più artificiali sono ancora in base

Questo è un caso degenere.

Per ogni artificiale ancora in base:

1. guarda la riga in cui è in base;
2. cerca una colonna non artificiale con coefficiente non nullo;
3. se la trovi, fai un pivot per far uscire l'artificiale dalla base;
4. se non la trovi, la riga è ridondante e può essere eliminata.

---

## 12. Solver ad alto livello

File:

```text
core/solver.py
```

La GUI deve chiamare solo questo modulo.

### 12.1 Funzione principale

```python
def solve_problem(raw_text: str, options: SolverOptions) -> SolveResult:
    ...
```

Responsabilità:

1. chiamare il parser;
2. trasformare in forma standard;
3. cercare una base iniziale;
4. se esiste, costruire il tableau di fase II;
5. se non esiste, lanciare la fase I;
6. lanciare la fase II se possibile;
7. raccogliere tutti gli step;
8. restituire `SolveResult`.

---

### 12.2 Pseudocodice del solver

```text
solve_problem(raw_text, options):
    steps = []

    problem = parse_problem(raw_text)
    steps.append(step input letto)

    std, std_steps = to_standard_form(problem)
    steps.extend(std_steps)

    basis = find_identity_basis(std.A)

    if basis exists and basis feasible:
        tableau = build_canonical_tableau(std.A, std.b, std.c, basis)
        phase2_tableau, simplex_steps, status = simplex(tableau)
        steps.extend(simplex_steps)
        return result

    else:
        phase1_result = run_phase_one(std)
        steps.extend(phase1_result.steps)

        if phase1_result.status == "infeasible":
            return infeasible result

        phase2_tableau = prepare_phase_two(phase1_result.final_tableau, std)
        final_tableau, simplex_steps, status = simplex(phase2_tableau)
        steps.extend(simplex_steps)
        return result
```

---

## 13. Formattazione dei dati per Streamlit

File:

```text
core/formatting.py
```

Streamlit visualizza bene i `pandas.DataFrame`, ma i `Fraction` devono essere convertiti in stringhe.

### 13.1 Conversione `Fraction` → stringa

```python
def fraction_to_str(x: Fraction) -> str:
    if x.denominator == 1:
        return str(x.numerator)
    return f"{x.numerator}/{x.denominator}"
```

---

### 13.2 Tableau → DataFrame

```python
def tableau_to_dataframe(tableau: Tableau) -> pd.DataFrame:
    ...
```

Colonne:

```text
Base | x1 | x2 | x3 | s1 | s2 | RHS
```

La riga 0 può avere base `z` o `w`, a seconda della fase.

Esempio:

```text
Base   x1    x2    s1    s2    RHS
z      -3    -2    0     0     0
s1      1     1    1     0     4
s2      2     1    0     1     5
```

---

## 14. GUI con Streamlit

File principale:

```text
app.py
```

### 14.1 Layout consigliato

Usa una struttura a colonne e tab.

```text
Titolo

Sidebar:
- scelta esempio
- strategia pivot
- limite iterazioni
- pulsante risolvi

Area principale:
- tab Input
- tab Forma standard
- tab Fase I
- tab Fase II
- tab Soluzione finale
- tab Log completo
```

---

### 14.2 Sidebar

Contenuti consigliati:

```python
st.sidebar.title("Impostazioni")

example = st.sidebar.selectbox(
    "Esempio",
    ["Personalizzato", "Slack iniziale", "Due fasi", "Illimitato"]
)

pivot_rule = st.sidebar.selectbox(
    "Regola variabile entrante",
    ["most_negative", "first_negative", "bland"]
)

max_iter = st.sidebar.number_input(
    "Numero massimo iterazioni",
    min_value=1,
    max_value=500,
    value=100
)

solve_clicked = st.sidebar.button("Risolvi")
```

---

### 14.3 Tab Input

Nel tab Input:

```python
raw_text = st.text_area(
    "Inserisci il problema",
    value=default_example,
    height=300
)
```

Aggiungi una sezione di aiuto:

```text
Formato richiesto:

min
c = [3, 4, 6]
A = [
  [1, 3, 4],
  [2, 1, 3]
]
signs = ["=", "="]
b = [1, 2]
```

---

### 14.4 Tab Forma standard

Mostrare:

- problema originale;
- trasformazioni effettuate;
- matrice `A`, vettore `b`, vettore `c` in forma standard;
- variabili aggiunte: slack, surplus, artificiali.

Esempio:

```python
with tab_standard:
    st.subheader("Forma standard")
    for step in standard_steps:
        st.markdown(step.description)
    st.dataframe(standard_matrix_df)
```

---

### 14.5 Tab Fase I

Mostrare solo se la fase I è stata usata.

Contenuti:

- problema artificiale;
- tableau iniziale fase I;
- ogni iterazione;
- valore finale `w*`;
- esito:
  - problema inammissibile;
  - oppure passaggio alla fase II.

Usa `st.expander` per non rendere la pagina troppo lunga:

```python
for i, step in enumerate(phase1_steps):
    with st.expander(f"{i+1}. {step.title}"):
        st.markdown(step.description)
        if step.tableau_before:
            st.dataframe(tableau_to_dataframe(step.tableau_before))
        if step.tableau_after:
            st.dataframe(tableau_to_dataframe(step.tableau_after))
```

---

### 14.6 Tab Fase II

Mostrare:

- tableau iniziale fase II;
- scelta della variabile entrante;
- test di illimitatezza;
- test dei rapporti;
- pivot;
- tableau dopo ogni pivot;
- test di ottimalità finale.

Per ogni iterazione, visualizzare:

```text
Variabile entrante: x2
Variabile uscente: s1
Elemento pivot: 2
Rapporti:
- riga s1: 20/2 = 10
- riga s2: 20/1 = 20
- riga s3: 20/2 = 10
```

---

### 14.7 Tab Soluzione finale

Mostrare uno stato finale chiaro.

#### Caso ottimo

```text
Stato: soluzione ottima trovata
x1 = 4
x2 = 4
x3 = 4
Valore ottimo = -136
```

#### Caso illimitato

```text
Stato: problema illimitato
La colonna della variabile entrante x1 ha tutti coefficienti <= 0, quindi non esiste una variabile uscente.
```

#### Caso inammissibile

```text
Stato: problema inammissibile
Il valore ottimo della fase I è w* > 0, quindi non esiste una soluzione ammissibile del problema originale.
```

---

### 14.8 Tab Log completo

Mostrare una timeline testuale di tutti gli step.

Esempio:

```python
for step in result.steps:
    st.markdown(f"### {step.title}")
    st.markdown(step.description)
```

Aggiungi anche un pulsante per esportare il log:

```python
st.download_button(
    "Scarica report Markdown",
    data=build_markdown_report(result),
    file_name="report_simplesso.md",
    mime="text/markdown"
)
```

---

## 15. Comunicazione fra moduli

### 15.1 Dipendenze consigliate

```text
app.py
  ↓
ui/input_panel.py
ui/steps_panel.py
ui/tableau_panel.py
  ↓
core/solver.py
  ↓
core/parser.py
core/standard_form.py
core/basis.py
core/tableau.py
core/simplex.py
core/two_phase.py
core/formatting.py
```

### 15.2 Regola importante

La dipendenza deve andare sempre in una sola direzione:

```text
GUI → Solver → Core matematico
```

Mai il contrario.

Quindi:

- `core/simplex.py` non deve importare Streamlit;
- `core/tableau.py` non deve conoscere la GUI;
- `core/solver.py` deve restituire dati, non stamparli;
- la GUI decide solo come visualizzare i dati.

---

## 16. Piano di sviluppo in fasi

### Fase 1 — Motore aritmetico

Implementa:

- `Fraction` parser;
- operazioni su matrici;
- inversione con Gauss-Jordan;
- conversione tableau in stringhe.

Test minimi:

- inversione di identità;
- inversione di matrici 2x2;
- prodotto matrice-vettore;
- gestione di frazioni negative.

---

### Fase 2 — Tableau canonico

Implementa:

- `build_canonical_tableau()`;
- calcolo di `B^{-1}b`;
- calcolo di `B^{-1}F`;
- calcolo dei costi ridotti;
- costruzione riga 0.

Testa con esempi già in forma standard e base assegnata.

---

### Fase 3 — Simplesso fase II

Implementa:

- test di ottimalità;
- scelta variabile entrante;
- test di illimitatezza;
- test dei rapporti;
- pivot;
- estrazione soluzione finale.

In questa fase non usare ancora input grezzo. Dai al programma direttamente `A`, `b`, `c`, `basis`.

---

### Fase 4 — Forma standard

Implementa:

- conversione `max` in `min`;
- normalizzazione `b >= 0`;
- slack;
- surplus;
- uguaglianze;
- nomi variabili.

Testa problemi con soli vincoli `<=`, perché dovrebbero produrre una base slack immediata.

---

### Fase 5 — Metodo delle due fasi

Implementa:

- costruzione problema artificiale;
- fase I;
- controllo `w* > 0`;
- controllo `w* = 0`;
- eliminazione artificiali;
- passaggio alla fase II.

---

### Fase 6 — Parser testuale

Implementa il parser semi-strutturato.

Prima supporta solo:

```text
min/max
c = [...]
A = [...]
signs = [...]
b = [...]
```

Solo dopo, eventualmente, aggiungi un parser più naturale per input tipo:

```text
min 3x1 + 4x2
x1 + 2x2 <= 10
```

---

### Fase 7 — Streamlit MVP

Crea una prima GUI con:

- text area input;
- pulsante risolvi;
- visualizzazione risultato finale;
- visualizzazione lista step;
- visualizzazione tableau.

Non pensare subito all'estetica: prima fai funzionare tutto.

---

### Fase 8 — Miglioramento GUI

Aggiungi:

- esempi precompilati;
- tab separate;
- expander per ogni iterazione;
- evidenziazione del pivot;
- download del report Markdown;
- messaggi di errore chiari.

---

## 17. Esempi da includere nella GUI

### 17.1 Problema con slack e base iniziale immediata

```text
min
c = [-10, -12, -12]
A = [
  [1, 2, 2],
  [2, 1, 2],
  [2, 2, 1]
]
signs = ["<=", "<=", "<="]
b = [20, 20, 20]
```

Serve per testare:

- slack;
- base identità;
- fase II diretta.

---

### 17.2 Problema con due fasi

```text
min
c = [3, 4, 6]
A = [
  [1, 3, 4],
  [2, 1, 3]
]
signs = ["=", "="]
b = [1, 2]
```

Serve per testare:

- variabili artificiali;
- fase I;
- eliminazione artificiali;
- fase II.

---

### 17.3 Problema illimitato

```text
min
c = [-3, 2, 4, 0, 0]
A = [
  [-1, -1, 2, 1, 0],
  [1, -2, 1, 0, 1]
]
signs = ["=", "="]
b = [1, -1]
```

Serve per testare:

- normalizzazione di termini noti negativi;
- rilevazione problema illimitato;
- messaggio di stop.

---

## 18. Errori da gestire bene

### Input non valido

Esempi:

- parentesi mancanti;
- numero righe di `A` diverso da `b`;
- segni non riconosciuti;
- coefficienti non convertibili in `Fraction`.

La GUI deve mostrare:

```text
Errore di input: la matrice A ha 3 righe, ma b contiene 2 elementi.
```

Non mostrare traceback Python all'utente.

---

### Matrice base singolare

Se la base scelta produce una matrice non invertibile:

```text
Errore: la matrice di base è singolare, quindi non può essere usata per costruire il tableau canonico.
```

---

### Iterazioni eccessive

Se superi il limite:

```text
Limite massimo di iterazioni raggiunto. Possibile degenerazione o ciclo.
```

---

## 19. Test automatici

I test sono fondamentali. Senza test rischi di non capire se un errore viene da:

- parser;
- forma standard;
- base;
- tableau;
- pivot;
- fase I;
- fase II.

### Test consigliati

```text
test_parser.py
- parse di interi
- parse di frazioni
- parse di decimali
- errore dimensioni

test_standard_form.py
- max diventa min
- b negativo cambia verso
- <= aggiunge slack
- >= aggiunge surplus
- = non aggiunge slack

test_basis.py
- identità trovata
- identità non trovata
- colonne identità in ordine diverso

test_tableau.py
- tableau canonico con B = I
- tableau canonico con B diversa da I

test_pivot.py
- normalizzazione riga pivot
- azzeramento colonna pivot
- aggiornamento base

test_simplex.py
- problema ottimo
- problema illimitato

test_two_phase.py
- problema inammissibile
- problema ammissibile con artificiali fuori base
- problema ammissibile con artificiale ancora in base
```

---

## 20. Requirements

File:

```text
requirements.txt
```

Contenuto minimo:

```text
streamlit
pandas
pytest
```

Non serve `numpy` per il motore matematico se vuoi mantenere esattezza con `Fraction`.

---

## 21. Comando di avvio

Da terminale, nella cartella del progetto:

```bash
streamlit run app.py
```

---

## 22. Ordine consigliato di implementazione

Ordine operativo concreto:

1. crea `models.py`;
2. crea funzioni per `Fraction` e matrici;
3. implementa `build_canonical_tableau()`;
4. implementa `pivot()`;
5. implementa `simplex()` su tableau già pronto;
6. implementa `to_standard_form()`;
7. implementa `find_identity_basis()`;
8. implementa `two_phase.py`;
9. implementa `solver.py`;
10. solo ora crea `app.py` con Streamlit;
11. aggiungi esempi;
12. aggiungi esportazione report;
13. aggiungi test automatici;
14. migliora grafica e messaggi.

---

## 23. Versione MVP da completare per prima

Per non bloccarti, punta a questa prima versione:

### Input supportato

Solo formato semi-strutturato:

```text
min
c = [...]
A = [...]
signs = [...]
b = [...]
```

### Funzionalità supportate

- problemi di minimo;
- vincoli `<=`, `>=`, `=`;
- variabili tutte non negative;
- slack e surplus;
- base slack se disponibile;
- due fasi se necessario;
- output di tutti i tableau.

### Funzionalità rimandate

- variabili libere;
- vincoli su variabili tipo `x1 <= 0`;
- parser naturale di espressioni algebriche;
- salvataggio progetto;
- grafici geometrici 2D.

---

## 24. Regola progettuale finale

La cosa più importante è questa:

```text
Prima costruisci un solver corretto da terminale.
Poi costruisci la GUI.
```

Se parti dalla GUI, rischi di perdere tempo su layout e interazione mentre il cuore matematico è ancora instabile.

La GUI Streamlit deve essere solo una finestra sul solver:

```text
utente → Streamlit → solver → step → Streamlit
```

Il solver deve poter funzionare anche così:

```python
result = solve_problem(raw_text, options)
for step in result.steps:
    print(step.title)
    print(step.description)
```

Se riesci a farlo funzionare da terminale, integrarlo in Streamlit sarà molto più semplice.
