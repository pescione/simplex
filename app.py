"""
Interfaccia Streamlit per il solver del simplesso.
"""

import re
import streamlit as st
import pandas as pd
from fractions import Fraction
from core.models import SolverOptions
from core.solver import solve_problem
from core.formatting import tableau_to_dataframe, fraction_to_str


# Configurazione della pagina
st.set_page_config(
    page_title="Simplesso Solver",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("📊 Solver Didattico del Simplesso")
st.markdown(
    """
    Applicazione interattiva per la **risoluzione di problemi di programmazione lineare** 
    con il **metodo del simplesso**.
    
    ✨ **Caratteristiche:**
    - Trasformazione automatica in forma standard
    - Visualizzazione passo-passo del processo di risoluzione
    - Rilevazione di casi speciali (illimitato, inammissibile)
    - Aritmetica esatta con frazioni
    - Supporto per il metodo delle due fasi
    """
)

# Sidebar
st.sidebar.title("⚙️ Impostazioni")

# Selezione dell'esempio
example_choice = st.sidebar.selectbox(
    "Scegli un esempio o personalizzato",
    ["Personalizzato", "Slack iniziale", "Due fasi", "Illimitato", "Variabili libere"],
    key="example_choice",
)

# Estratto degli esempi dalla roadmap (sezione 17)
EXAMPLES = {
    "Slack iniziale": """min
c = [-10, -12, -12]
A = [
  [1, 2, 2],
  [2, 1, 2],
  [2, 2, 1]
]
signs = ["<=", "<=", "<="]
b = [20, 20, 20]
""",
    "Due fasi": """min
c = [3, 4, 6]
A = [
  [1, 3, 4],
  [2, 1, 3]
]
signs = ["=", "="]
b = [1, 2]
""",
    "Illimitato": """min
c = [-3, 2, 4, 0, 0]
A = [
  [-1, -1, 2, 1, 0],
  [1, -2, 1, 0, 1]
]
signs = ["=", "="]
b = [1, -1]
""",
    "Variabili libere": """min
c = [1, -2, 3]
A = [
  [1, 1, 1],
  [2, -1, 1]
]
signs = ["=", "="]
b = [5, 3]
free = [x2]
""",
}

default_example = (
    EXAMPLES.get(example_choice, "") if example_choice in EXAMPLES else ""
)

# Regola per la scelta della variabile entrante
pivot_rule = st.sidebar.selectbox(
    "Regola variabile entrante",
    ["most_negative", "first_negative", "bland"],
    index=0,
)

# Metodo risolutivo
solving_method = st.sidebar.selectbox(
    "Metodo risolutivo",
    ["auto", "two_phase", "dual_simplex"],
    index=0,
    help="auto: sceglie automaticamente | two_phase: metodo delle due fasi | dual_simplex: simplesso duale",
)

# Numero massimo di iterazioni
max_iterations = st.sidebar.slider(
    "Numero massimo iterazioni", min_value=1, max_value=2000, value=100, step=10
)

# Pulsante per risolvere
solve_button = st.sidebar.button("🚀 Risolvi", use_container_width=True)

# Inizializza session state per il testo del problema
if "problem_text" not in st.session_state:
    st.session_state.problem_text = default_example

# Aggiorna il problem_text quando cambia l'esempio
if "last_example_choice" not in st.session_state:
    st.session_state.last_example_choice = example_choice

if example_choice != st.session_state.last_example_choice:
    st.session_state.problem_text = default_example
    st.session_state.problem_input = default_example
    st.session_state.last_example_choice = example_choice


def build_markdown_report(result) -> str:
    """
    Costruisce un report Markdown della soluzione.
    """
    report = "# Report del Simplesso\n\n"

    report += "## Problema originale\n\n"
    report += f"**Verso:** {result.original_problem.sense}imo\n"
    report += f"**Variabili:** {', '.join(result.original_problem.var_names)}\n"
    report += f"**Vincoli:** {len(result.original_problem.b)}\n\n"

    report += "## Stato della soluzione\n\n"
    report += f"**Status:** {result.status}\n"
    report += f"**Messaggio:** {result.message}\n\n"

    if result.status == "optimal":
        report += "## Soluzione ottima\n\n"
        original_vars = result.original_problem.var_names
        for var in original_vars:
            if var in result.solution:
                report += f"- {var} = {result.solution[var]}\n"

        report += f"\n**Valore ottimo:** {result.optimal_value}\n\n"

    report += "## Passaggi della risoluzione\n\n"
    for i, step in enumerate(result.steps, 1):
        phase_label = f"Fase {step.phase}" if step.phase else "Setup"
        report += f"### Passo {i}: {step.title} ({phase_label})\n\n"
        report += f"{step.description}\n\n"
        if step.notes:
            report += "**Note:**\n"
            for note in step.notes:
                report += f"- {note}\n"
        report += "\n"

    return report


def fraction_to_latex(value: Fraction) -> str:
    """Converte una frazione in una stringa LaTeX."""
    if value.denominator == 1:
        return str(value.numerator)

    sign = "-" if value.numerator < 0 else ""
    return f"{sign}\\frac{{{abs(value.numerator)}}}{{{value.denominator}}}"


def variable_to_latex(name: str) -> str:
    """Rende i nomi di variabile compatibili con LaTeX."""
    match = re.fullmatch(r"([a-zA-Z]+)(\d+)", name)
    if match:
        return f"{match.group(1)}_{{{match.group(2)}}}"
    return name


def linear_term_to_latex(coeff: Fraction, name: str) -> str:
    """Formatta un termine lineare per una formula LaTeX."""
    if coeff == 0:
        return ""

    variable = variable_to_latex(name)
    abs_coeff = abs(coeff)

    if abs_coeff == 1:
        term = variable
    else:
        term = f"{fraction_to_latex(abs_coeff)}\\,{variable}"

    return f"- {term}" if coeff < 0 else term


def standard_problem_to_latex(result) -> str:
    """Costruisce la forma standard come blocco matematico LaTeX."""
    standard_problem = result.standard_problem
    if not standard_problem:
        return ""

    objective_terms = [
        linear_term_to_latex(coeff, var)
        for var, coeff in zip(standard_problem.var_names, standard_problem.c)
        if coeff != 0
    ]
    objective = " + ".join(objective_terms) if objective_terms else "0"
    objective = objective.replace("+ -", "- ")

    constraint_lines = []
    for row, rhs in zip(standard_problem.A, standard_problem.b):
        terms = [
            linear_term_to_latex(coeff, var)
            for var, coeff in zip(standard_problem.var_names, row)
            if coeff != 0
        ]
        equation = " + ".join(terms) if terms else "0"
        equation = equation.replace("+ -", "- ")
        constraint_lines.append(f"& {equation} = {fraction_to_latex(rhs)}\\")

    non_negative = ", ".join(
        variable_to_latex(var) for var in standard_problem.var_names
    )

    lines = [
        "\\begin{aligned}",
        f"\\min\\quad & {objective}\\\\",
        "\\text{s.t.}\\quad",
    ]
    lines.extend(constraint_lines)
    lines.append(f"& {non_negative} \\geq 0")
    lines.append("\\end{aligned}")

    return "$$\n" + "\n".join(lines) + "\n$$"

# Area principale con tab
tab_input, tab_standard, tab_phase1, tab_phase2, tab_solution, tab_log = st.tabs(
    [
        "📝 Input",
        "📋 Forma Standard",
        "🔄 Fase I",
        "🔄 Fase II",
        "✅ Soluzione",
        "📄 Log Completo",
    ]
)

# Tab Input
with tab_input:
    st.subheader("📝 Inserisci il tuo problema")

    if not st.session_state.problem_text.strip():
        st.info(
            "💡 **Prima volta qui?**\n\n"
            "1. Seleziona un esempio dal menu a sinistra oppure scrivi il tuo problema\n"
            "2. Configura le opzioni nella barra laterale\n"
            "3. Clicca 'Risolvi' per iniziare\n\n"
            "Vedi la sezione 'Aiuto sul formato' qui sotto per i dettagli."
        )

    problem_text = st.text_area(
        "Formato richiesto:",
        value=st.session_state.problem_text,
        height=300,
        key="problem_input",
        placeholder="""min
c = [3, 4, 6]
A = [
  [1, 3, 4],
  [2, 1, 3]
]
signs = ["=", "="]
b = [1, 2]
""",
    )
    
    # Aggiorna session state
    st.session_state.problem_text = problem_text

    st.markdown("### Guida del formato")
    with st.expander("Aiuto sul formato"):
        st.markdown(
            """
        **Formato richiesto:**

        ```
        min          # o 'max' per massimizzazione
        c = [c1, c2, c3, ...]    # coefficienti funzione obiettivo
        A = [
          [a11, a12, a13, ...],  # matrice dei vincoli
          [a21, a22, a23, ...],
          ...
        ]
        signs = ["<=", ">=", "=", ...]  # verso dei vincoli
        b = [b1, b2, b3, ...]   # termini noti
        free = [x1, x3]          # (opzionale) variabili libere (non vincolate a x ≥ 0)
        ```

        **Esempi di numeri supportati:**
        - Interi: `3`, `-2`
        - Frazioni: `1/3`, `-5/7`
        - Decimali: `0.5`, `-3.25`

        **⚠️ Vincoli di non negatività:**
        - Per **default**, tutte le variabili sono **automaticamente non-negative** (`x ≥ 0`)
        - Per specificare variabili **libere** (non vincolate), usa la riga `free`
        - Esempio: `free = [x2, x4]` rende x₂ e x₄ variabili libere
        - Le variabili libere sono automaticamente trasformate in `x_i = x_i⁺ - x_i⁻` dove x_i⁺, x_i⁻ ≥ 0

        **Importante:**
        - I vincoli `<=`, `>=`, `=` nella riga `signs` sono solo per gli altri vincoli
        - La riga `free` è **opzionale**: se non la specifichi, tutte le variabili sono non-negative
        """
        )

# Resolver principale
if solve_button:
    problem_text = st.session_state.problem_text
    if not problem_text.strip():
        st.error("❌ Errore: Il campo del problema è vuoto. Inserisci un problema valido.")
    else:
        with st.spinner("⏳ Risoluzione in corso..."):
            try:
                options = SolverOptions(
                    entering_var_rule=pivot_rule,
                    max_iterations=max_iterations,
                    verbosity=1,
                    method=solving_method,
                )
                result = solve_problem(problem_text, options)

                # Salva il risultato in session state
                st.session_state.last_result = result

                # Mostra messaggio di successo se c'è una soluzione
                if result.status == "optimal":
                    st.success(f"✅ {result.message}")
                elif result.status == "unbounded":
                    st.warning(f"⚠️ {result.message}")
                elif result.status == "infeasible":
                    st.error(f"❌ {result.message}")
                elif result.status == "input_error":
                    st.error(f"❌ Errore di input: {result.message}")
                else:
                    st.warning(f"⚠️ {result.message}")

            except Exception as e:
                st.error(f"❌ Errore durante la risoluzione: {str(e)}")
                st.info("Controlla il formato del tuo input e riprova.")

# Recupera il risultato dal session state
result = st.session_state.get("last_result", None)

if result:
    # Tab Forma Standard
    with tab_standard:
        st.subheader("Forma Standard")

        # Visualizza il problema originale
        with st.expander("📌 Problema originale"):
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**Verso:**", help="min o max")
                st.write(result.original_problem.sense)
            with col2:
                st.markdown("**Numero variabili:**")
                st.write(len(result.original_problem.var_names))

        # Visualizza le trasformazioni
        if result.standard_problem:
            with st.expander("🔄 Trasformazioni effettuate"):
                for i, log_entry in enumerate(result.standard_problem.transformation_log):
                    st.write(f"{i + 1}. {log_entry}")

            # Visualizza il sistema in forma standard
            with st.expander("📐 Sistema in forma standard"):
                st.markdown("**Forma standard:** min c^T x, Ax = b, x ≥ 0")

                standard_latex = standard_problem_to_latex(result)
                if standard_latex:
                    st.markdown(standard_latex)

                # Matrice A
                st.markdown("**Matrice A:**")
                A_df = pd.DataFrame(
                    [[fraction_to_str(x) for x in row] for row in result.standard_problem.A],
                    columns=result.standard_problem.var_names,
                    index=[f"v{i + 1}" for i in range(len(result.standard_problem.A))],
                )
                st.dataframe(A_df, use_container_width=True)

                # Vettore b
                st.markdown("**Vettore b:**")
                b_df = pd.DataFrame(
                    {
                        "Vincolo": [f"v{i + 1}" for i in range(len(result.standard_problem.b))],
                        "b": [fraction_to_str(x) for x in result.standard_problem.b],
                    }
                )
                st.dataframe(b_df, use_container_width=True)

                # Vettore c
                st.markdown("**Vettore c (costi):**")
                c_df = pd.DataFrame(
                    {
                        "Variabile": result.standard_problem.var_names,
                        "Costo": [fraction_to_str(x) for x in result.standard_problem.c],
                    }
                )
                st.dataframe(c_df, use_container_width=True)

    # Tab Fase I
    with tab_phase1:
        st.subheader("Fase I - Ricerca Base Ammissibile")

        phase1_steps = [s for s in result.steps if s.phase == 1]

        if phase1_steps:
            st.info("La fase I è stata utilizzata per trovare una base ammissibile iniziale.")

            for i, step in enumerate(phase1_steps, 1):
                with st.expander(f"**Passo {i}: {step.title}**"):
                    if step.description:
                        st.markdown(step.description)

                    if step.tableau_before:
                        st.markdown("**Tableau prima:**")
                        df_before = tableau_to_dataframe(step.tableau_before)
                        st.dataframe(df_before, use_container_width=True)

                    if step.tableau_after:
                        st.markdown("**Tableau dopo:**")
                        df_after = tableau_to_dataframe(step.tableau_after)
                        st.dataframe(df_after, use_container_width=True)

                    if step.notes:
                        st.markdown("**Note:**")
                        for note in step.notes:
                            st.write(f"- {note}")
        else:
            st.info("La fase I non è stata necessaria (base ammissibile trovata direttamente).")

    # Tab Fase II
    with tab_phase2:
        st.subheader("Fase II - Ottimizzazione")

        phase2_steps = [s for s in result.steps if s.phase == 2]

        if phase2_steps:
            for i, step in enumerate(phase2_steps, 1):
                with st.expander(f"**Passo {i}: {step.title}**"):
                    if step.description:
                        st.markdown(step.description)

                    # Mostra variabili entranti e uscenti
                    col1, col2 = st.columns(2)
                    with col1:
                        if step.entering_var:
                            st.markdown(f"**Var. entrante:** `{step.entering_var}`")
                    with col2:
                        if step.leaving_var:
                            st.markdown(f"**Var. uscente:** `{step.leaving_var}`")

                    # Mostra i rapporti del test
                    if step.ratios:
                        st.markdown("**Test dei rapporti:**")
                        ratios_df = pd.DataFrame(
                            {
                                "Variabile": [name for name, _ in step.ratios],
                                "Rapporto": [fraction_to_str(ratio) for _, ratio in step.ratios],
                            }
                        )
                        st.dataframe(ratios_df, use_container_width=True)

                    if step.tableau_before:
                        st.markdown("**Tableau prima:**")
                        df_before = tableau_to_dataframe(step.tableau_before)
                        st.dataframe(df_before, use_container_width=True)

                    if step.tableau_after:
                        st.markdown("**Tableau dopo:**")
                        df_after = tableau_to_dataframe(step.tableau_after)
                        st.dataframe(df_after, use_container_width=True)

                    if step.notes:
                        st.markdown("**Note:**")
                        for note in step.notes:
                            st.write(f"- {note}")
        else:
            st.warning("Nessun passo nella fase II.")

    # Tab Soluzione
    with tab_solution:
        st.subheader("Soluzione")

        # Stato finale
        status_colors = {
            "optimal": "🟢 Soluzione ottima trovata",
            "unbounded": "🔴 Problema illimitato",
            "infeasible": "🔴 Problema inammissibile",
            "input_error": "🟠 Errore di input",
            "iteration_limit": "🟡 Limite di iterazioni raggiunto",
        }

        status_text = status_colors.get(result.status, result.status)
        st.markdown(f"## {status_text}")

        if result.message:
            st.info(result.message)

        if result.status == "optimal":
            # Mostra la soluzione
            st.markdown("### Soluzione ottima")

            # Mostra solo le variabili originali
            original_vars = result.original_problem.var_names
            solution_dict = {
                var: result.solution[var] for var in original_vars if var in result.solution
            }

            solution_df = pd.DataFrame(
                {
                    "Variabile": list(solution_dict.keys()),
                    "Valore": [fraction_to_str(v) for v in solution_dict.values()],
                }
            )
            st.dataframe(solution_df, use_container_width=True)

            # Mostra il valore ottimo
            st.markdown("### Valore della funzione obiettivo")
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Valore ottimo", fraction_to_str(result.optimal_value))
            with col2:
                st.write(f"(Problema di {result.original_problem.sense}imo)")

        elif result.status == "unbounded":
            st.error(
                "Il problema è illimitato. La funzione obiettivo può decrescere indefinitamente."
            )

        elif result.status == "infeasible":
            st.error(
                "Il problema è inammissibile. Non esiste alcuna soluzione che soddisfi tutti i vincoli."
            )

    # Tab Log Completo
    with tab_log:
        st.subheader("Log Completo")

        st.markdown("### Tutti i passaggi della risoluzione")

        for i, step in enumerate(result.steps, 1):
            phase_label = f"Fase {step.phase}" if step.phase else "Setup"
            with st.expander(f"**Passo {i} ({phase_label}): {step.title}**"):
                if step.description:
                    st.markdown(step.description)

                if step.tableau_before:
                    st.markdown("**Tableau prima:**")
                    df = tableau_to_dataframe(step.tableau_before)
                    st.dataframe(df, use_container_width=True)

                if step.tableau_after:
                    st.markdown("**Tableau dopo:**")
                    df = tableau_to_dataframe(step.tableau_after)
                    st.dataframe(df, use_container_width=True)

                if step.notes:
                    st.markdown("**Note:**")
                    for note in step.notes:
                        st.write(f"- {note}")

        # Pulsante per scaricare il report
        st.markdown("---")
        st.subheader("Esporta")

        report_text = build_markdown_report(result)
        st.download_button(
            label="📥 Scarica report Markdown",
            data=report_text,
            file_name="report_simplesso.md",
            mime="text/markdown",
        )



# Initialize session state
if "last_result" not in st.session_state:
    st.session_state.last_result = None
