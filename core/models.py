"""
Modelli dati principali per il solver del simplesso.
"""

from dataclasses import dataclass, field
from fractions import Fraction
from typing import Optional


@dataclass
class LinearProblem:
    """
    Rappresenta un problema di programmazione lineare in forma grezza o normalizzata.
    
    Attributi:
        sense: "min" o "max"
        c: coefficienti della funzione obiettivo
        A: matrice dei vincoli
        signs: lista di "<=", ">=", "="
        b: termini noti
        var_names: nomi delle variabili
    """
    sense: str
    c: list[Fraction]
    A: list[list[Fraction]]
    signs: list[str]
    b: list[Fraction]
    var_names: list[str]


@dataclass
class StandardProblem:
    """
    Rappresenta un problema in forma standard:
    min c^T x
    Ax = b
    x >= 0
    
    Attributi:
        c: coefficienti della funzione obiettivo
        A: matrice dei vincoli
        b: termini noti
        var_names: nomi di tutte le variabili (originali + slack + surplus + artificiali)
        original_var_count: numero delle variabili originali
        slack_vars: indici delle variabili slack
        surplus_vars: indici delle variabili surplus
        artificial_vars: indici delle variabili artificiali
        transformation_log: lista descrittiva delle trasformazioni effettuate
    """
    c: list[Fraction]
    A: list[list[Fraction]]
    b: list[Fraction]
    var_names: list[str]
    original_var_count: int
    slack_vars: list[int] = field(default_factory=list)
    surplus_vars: list[int] = field(default_factory=list)
    artificial_vars: list[int] = field(default_factory=list)
    transformation_log: list[str] = field(default_factory=list)


@dataclass
class Tableau:
    """
    Rappresenta un tableau del simplesso.
    
    Convenzione:
        - data[0] è la riga della funzione obiettivo (z o w)
        - data[1:] sono le righe dei vincoli
        - l'ultima colonna è il termine noto (RHS)
        - basis[i] è l'indice della variabile in base nella riga i+1
    
    Attributi:
        data: matrice del tableau
        basis: lista degli indici delle variabili in base
        var_names: nomi di tutte le variabili
        phase: numero della fase (1 o 2)
        objective_name: nome della funzione obiettivo ("z" o "w")
    """
    data: list[list[Fraction]]
    basis: list[int]
    var_names: list[str]
    phase: int
    objective_name: str


@dataclass
class Step:
    """
    Rappresenta un passaggio del processo di risoluzione.
    
    Attributi:
        title: titolo dello step
        description: descrizione testuale
        phase: numero della fase (1 o 2)
        tableau_before: tableau prima dell'operazione
        tableau_after: tableau dopo dell'operazione
        entering_var: nome della variabile entrante
        leaving_var: nome della variabile uscente
        pivot_row: riga del pivot (0-based nell'interno del tableau)
        pivot_col: colonna del pivot (0-based)
        ratios: lista di tuple (nome_var, rapporto) per il test dei rapporti
        notes: lista di note aggiuntive
    """
    title: str
    description: str
    phase: Optional[int] = None
    tableau_before: Optional[Tableau] = None
    tableau_after: Optional[Tableau] = None
    entering_var: Optional[str] = None
    leaving_var: Optional[str] = None
    pivot_row: Optional[int] = None
    pivot_col: Optional[int] = None
    ratios: Optional[list[tuple[str, Fraction]]] = None
    notes: list[str] = field(default_factory=list)


@dataclass
class SolveResult:
    """
    Risultato finale del solver.
    
    Attributi:
        status: "optimal", "unbounded", "infeasible", "input_error", "iteration_limit"
        message: messaggio descrittivo
        original_problem: problema originale
        standard_problem: problema in forma standard
        steps: lista di tutti gli step
        final_tableau: ultimo tableau
        solution: dict {nome_var: valore}
        optimal_value: valore della funzione obiettivo
    """
    status: str
    message: str
    original_problem: LinearProblem
    standard_problem: Optional[StandardProblem] = None
    steps: list[Step] = field(default_factory=list)
    final_tableau: Optional[Tableau] = None
    solution: Optional[dict[str, Fraction]] = None
    optimal_value: Optional[Fraction] = None


@dataclass
class SolverOptions:
    """
    Opzioni del solver.
    
    Attributi:
        entering_var_rule: "most_negative", "first_negative", "bland"
        max_iterations: numero massimo di iterazioni
        verbosity: livello di dettaglio (0, 1, 2)
    """
    entering_var_rule: str = "most_negative"
    max_iterations: int = 100
    verbosity: int = 1
