"""
Parser per l'input testuale del problema di programmazione lineare.
"""

import ast
import re
from fractions import Fraction
from .models import LinearProblem


def parse_fraction(value: str) -> Fraction:
    """
    Converte una stringa in Fraction.

    Accetta:
        - interi: "3", "-2"
        - frazioni: "1/3", "-5/7"
        - decimali: "0.5", "-3.25"

    Args:
        value: stringa da convertire

    Returns:
        Fraction

    Raises:
        ValueError: se il formato non è riconosciuto
    """
    value = value.strip()

    # Prova a interpretare come Fraction
    try:
        return Fraction(value)
    except (ValueError, ZeroDivisionError):
        raise ValueError(f"Non riesco a interpretare '{value}' come frazione o numero decimale")


def parse_fraction_list(s: str) -> list[Fraction]:
    """
    Converte una stringa che rappresenta una lista di numeri in lista di Fraction.

    Formato supportato:
        "[1, 2, 3]"
        "[-1/3, 0.5, 2]"

    Args:
        s: stringa da convertire

    Returns:
        Lista di Fraction

    Raises:
        ValueError: se il formato non è valido
    """
    s = s.strip()

    # Aspettiamo una lista Python; usiamo ast.literal_eval dopo aver
    # quotato eventuali frazioni come "a/b" perché ast.non accetta
    # espressioni come 1/2 (sono BinOp)
    s = s.strip()
    if not s.startswith("[") or not s.endswith("]"):
        raise ValueError(f"Lista deve iniziare con '[' e terminare con ']': {s}")

    inner = s[1:-1].strip()
    if not inner:
        return []

    # Trova tutti i numeri: frazioni (a/b), float e interi
    pattern = r"-?\d+/\d+|-?\d+\.\d+|-?\d+"
    matches = re.findall(pattern, inner)
    if not matches:
        raise ValueError(f"Nessun numero valido trovato nella lista: {s}")

    result = [parse_fraction(m) for m in matches]
    return result


def parse_matrix(s: str) -> list[list[Fraction]]:
    """
    Converte una stringa che rappresenta una matrice.

    Formato supportato:
        "[[1, 2], [3, 4]]"

    Args:
        s: stringa da convertire

    Returns:
        Matrice come lista di liste di Fraction

    Raises:
        ValueError: se il formato non è valido
    """
    s = s.strip()
    # Normalizza gli spazi: rimuove spazi dopo "[" e prima di "]"
    s = s.replace("[ ", "[").replace(" ]", "]")

    if not s.startswith("[[") or not s.endswith("]]"):
        raise ValueError(f"Matrice deve iniziare con '[[' e terminare con ']]': {s}")

    # Split delle righe: rimuovi le due parentesi esterne e dividi su '],['
    inner = s[1:-1].strip()
    # Se inner è qualcosa come '[1,2], [3,4]' vogliamo separare le righe
    rows = re.split(r"\],\s*\[", inner)
    cleaned_rows = []
    for i, row in enumerate(rows):
        r = row.strip()
        if i == 0 and r.startswith("["):
            r = r[1:]
        if i == len(rows) - 1 and r.endswith("]"):
            r = r[:-1]
        cleaned_rows.append(r)

    result = []
    for row in cleaned_rows:
        row_s = f"[{row}]"
        result.append(parse_fraction_list(row_s))

    return result


def parse_signs_list(s: str) -> list[str]:
    """
    Converte una stringa che rappresenta una lista di segni di vincoli.

    Formato supportato:
        "[\"<=\", \">=\", \"=\"]"

    Args:
        s: stringa da convertire

    Returns:
        Lista di segni

    Raises:
        ValueError: se il formato non è valido
    """
    s = s.strip()

    if not s.startswith("[") or not s.endswith("]"):
        raise ValueError(f"Lista deve iniziare con '[' e terminare con ']': {s}")

    # Usa ast.literal_eval
    try:
        signs = ast.literal_eval(s)
    except (ValueError, SyntaxError) as e:
        raise ValueError(f"Errore nel parsing della lista di segni: {e}")

    if not isinstance(signs, list):
        raise ValueError("La lista di segni deve essere una lista")

    valid_signs = {"<=", ">=", "="}
    for sign in signs:
        if sign not in valid_signs:
            raise ValueError(f"Segno non riconosciuto: '{sign}'. Validi: {valid_signs}")

    return signs


def validate_dimensions(
    c: list[Fraction],
    A: list[list[Fraction]],
    signs: list[str],
    b: list[Fraction],
) -> None:
    """
    Valida che le dimensioni siano coerenti.

    Args:
        c: vettore dei costi
        A: matrice dei vincoli
        signs: lista dei segni
        b: vettore dei termini noti

    Raises:
        ValueError: se le dimensioni non sono coerenti
    """
    if len(A) == 0:
        raise ValueError("La matrice A deve avere almeno una riga")

    num_vars = len(c)
    num_constraints = len(A)
    num_cols = len(A[0])

    # Controlla che A sia rettangolare
    for i, row in enumerate(A):
        if len(row) != num_cols:
            raise ValueError(f"La riga {i} di A ha {len(row)} elementi, ma dovrebbe averne {num_cols}")

    # Controlla che num_cols == num_vars
    if num_cols != num_vars:
        raise ValueError(
            f"Numero di colonne di A ({num_cols}) diverso dalla lunghezza di c ({num_vars})"
        )

    # Controlla che len(b) == num_constraints
    if len(b) != num_constraints:
        raise ValueError(
            f"Lunghezza di b ({len(b)}) diversa dal numero di righe di A ({num_constraints})"
        )

    # Controlla che len(signs) == num_constraints
    if len(signs) != num_constraints:
        raise ValueError(
            f"Lunghezza di signs ({len(signs)}) diversa dal numero di vincoli ({num_constraints})"
        )


def generate_var_names(num_vars: int) -> list[str]:
    """
    Genera i nomi delle variabili originali.

    Per n variabili, genera: x1, x2, ..., xn

    Args:
        num_vars: numero di variabili

    Returns:
        Lista dei nomi
    """
    return [f"x{i + 1}" for i in range(num_vars)]


def parse_problem(text: str) -> LinearProblem:
    """
    Parsa un problema di programmazione lineare da testo.

    Formato richiesto:

        min
        c = [3, 4, 6]
        A = [
          [1, 3, 4],
          [2, 1, 3]
        ]
        signs = ["=", "="]
        b = [1, 2]

    Oppure:

        max
        c = [...]
        ...

    Il parser supporta:
    - min/max
    - c = [lista di numeri]
    - A = [[lista], [lista], ...] (su una o più righe)
    - signs = ["<=", ">=", "=", ...]
    - b = [lista di numeri]
    - linee vuote e commenti (righe che iniziano con #)

    Args:
        text: testo da parsare

    Returns:
        Oggetto LinearProblem

    Raises:
        ValueError: se il formato non è corretto
    """
    lines = text.strip().split("\n")
    sense = None
    c = None
    A = None
    signs = None
    b = None

    i = 0
    while i < len(lines):
        line = lines[i].strip()
        i += 1

        if not line or line.startswith("#"):
            # Linea vuota o commento
            continue

        if line.lower() in ["min", "max"]:
            sense = line.lower()

        elif line.startswith("c"):
            # Parse c
            parts = line.split("=", 1)
            if len(parts) != 2:
                raise ValueError(f"Linea non valida per c: {line}")
            c = parse_fraction_list(parts[1].strip())

        elif line.startswith("A"):
            # Parse A - con supporto multilinea
            parts = line.split("=", 1)
            if len(parts) != 2:
                raise ValueError(f"Linea non valida per A: {line}")

            # Costruisci la stringa della matrice, aggregando righe fino a che non termina con ]]
            matrix_str = parts[1].strip()
            while i < len(lines):
                # Controlla se la matrice è completa (normalizzando gli spazi)
                normalized = matrix_str.strip().replace("[ ", "[").replace(" ]", "]")
                if normalized.endswith("]]"):
                    break
                next_line = lines[i].strip()
                i += 1
                if next_line and not next_line.startswith("#"):
                    matrix_str += " " + next_line

            A = parse_matrix(matrix_str)

        elif line.startswith("signs"):
            # Parse signs
            parts = line.split("=", 1)
            if len(parts) != 2:
                raise ValueError(f"Linea non valida per signs: {line}")
            signs = parse_signs_list(parts[1].strip())

        elif line.startswith("b"):
            # Parse b
            parts = line.split("=", 1)
            if len(parts) != 2:
                raise ValueError(f"Linea non valida per b: {line}")
            b = parse_fraction_list(parts[1].strip())

    # Validazione
    if sense is None:
        raise ValueError("Manca il verso della funzione obiettivo (min o max)")
    if c is None:
        raise ValueError("Manca il vettore c")
    if A is None:
        raise ValueError("Manca la matrice A")
    if signs is None:
        raise ValueError("Manca la lista di segni")
    if b is None:
        raise ValueError("Manca il vettore b")

    # Valida le dimensioni
    validate_dimensions(c, A, signs, b)

    # Genera i nomi delle variabili
    var_names = generate_var_names(len(c))

    return LinearProblem(
        sense=sense, c=c, A=A, signs=signs, b=b, var_names=var_names
    )
