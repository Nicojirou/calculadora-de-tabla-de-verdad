import streamlit as st
import re
from itertools import product
import pandas as pd

# ============================================================
# CONFIGURACIÓN
# ============================================================
st.set_page_config(
    page_title="Calculadora Tabla de la Verdad",
    page_icon="🧮",
    layout="centered"
)

st.title("🧮 Calculadora de Tabla de la Verdad")
st.markdown("Construye tu expresión haciendo clic. El resultado se muestra en **0 y 1**.")

# ============================================================
# ESTADO DE LA SESIÓN
# ============================================================
if "expr" not in st.session_state:
    st.session_state.expr = ""

# ============================================================
# CONSTRUCTOR DE EXPRESIÓN
# ============================================================
st.subheader("🛠️ Constructor de Expresión")

# Variables
st.markdown("**Variables:**")
cols = st.columns(6)
variables = ["p", "q", "r", "s", "t", "u"]
for i, v in enumerate(variables):
    with cols[i % 6]:
        if st.button(f"{v}", key=f"btn_{v}", use_container_width=True):
            st.session_state.expr += f" {v} "

# Operadores
st.markdown("**Operadores:**")
cols = st.columns(6)
operadores = [
    ("∧", "AND"),
    ("∨", "OR"),
    ("¬", "NOT"),
    ("⊕", "XOR"),
    ("→", "IMPLIES"),
    ("↔", "IFF")
]

for i, (symbol, name) in enumerate(operadores):
    with cols[i % 6]:
        if st.button(f"{symbol}", key=f"btn_{name}", use_container_width=True):
            st.session_state.expr += f" {symbol} "

# Paréntesis y controles
col_paren1, col_paren2, col_limpiar, col_borrar = st.columns(4)

with col_paren1:
    if st.button("(", use_container_width=True):
        st.session_state.expr += "("

with col_paren2:
    if st.button(")", use_container_width=True):
        st.session_state.expr += ")"

with col_limpiar:
    if st.button("🗑️ Limpiar Todo", use_container_width=True):
        st.session_state.expr = ""
        st.session_state.tabla_generada = False
        st.session_state.df = None

with col_borrar:
    if st.button("⌫ Borrar Último", use_container_width=True):
        expr = st.session_state.expr.rstrip()
        if expr:
            st.session_state.expr = expr[:-1]

st.markdown("---")

# Preview de la expresión
st.markdown("**Expresión actual:**")
st.code(st.session_state.expr.strip() or "(vacío)", language="text")

# ============================================================
# LÓGICA CENTRAL - PARSER MEJORADO
# ============================================================

def normalizar_expresion(expr: str) -> str:
    """
    Convierte símbolos lógicos a expresiones Python evaluables de forma robusta.
    """
    e = expr.strip()
    
    # 1. Reemplazar operadores básicos primero
    e = e.replace("∧", " and ")
    e = e.replace("∨", " or ")
    e = e.replace("¬", " not ")
    e = e.replace("⊕", " xor ")
    
    # Patrón para reconocer términos que pueden incluir 'not' y paréntesis o variables
    term_pattern = r'(?:not\s+)*(?:\b[p-ut]\b|\([^()]+\))'
    
    # 2. Manejar la implicación (→) de manera iterativa para expresiones complejas
    while "→" in e:
        pattern = f'({term_pattern})\\s*→\\s*({term_pattern})'
        nuevo = re.sub(pattern, r'(not (\1) or (\2))', e)
        if nuevo == e:
            nuevo = re.sub(r'([^→↔]+)\s*→\s*([^→↔]+)', r'(not (\1) or (\2))', e)
        if nuevo == e:
            break
        e = nuevo

    # 3. Manejar el bicondicional (↔) de manera iterativa
    while "↔" in e:
        pattern = f'({term_pattern})\\s*↔\\s*({term_pattern})'
        nuevo = re.sub(pattern, r'((\1) == (\2))', e)
        if nuevo == e:
            nuevo = re.sub(r'([^→↔]+)\s*↔\s*([^→↔]+)', r'((\1) == (\2))', e)
        if nuevo == e:
            break
        e = nuevo
        
    # Limpiar espacios múltiples
    e = re.sub(r'\s+', ' ', e).strip()
    
    return e


def extraer_variables(expr: str) -> list:
    """Extrae las variables únicas (p, q, r, s, t, u) de la expresión."""
    return sorted(set(re.findall(r'\b[p-ut]\b', expr)))


def xor(a, b):
    """Función XOR lógica."""
    return bool(a) != bool(b)


def generar_tabla(expr_raw: str):
    """
    Genera la tabla de verdad completa.
    Retorna: (variables, tabla)
    """
    if not expr_raw.strip():
        return [], []
    
    expr_norm = normalizar_expresion(expr_raw)
    variables = extraer_variables(expr_norm)
    
    if not variables:
        return [], []
    
    tabla = []
    
    # Generar todas las combinaciones posibles (2^n)
    for valores in product([0, 1], repeat=len(variables)):
        entorno = {v: bool(val) for v, val in zip(variables, valores)}
        entorno['xor'] = xor 
        
        try:
            resultado = eval(expr_norm, {"__builtins__": {}}, entorno)
            fila = list(valores) + [int(bool(resultado))]
            tabla.append(fila)
        except Exception as e:
            return [], []
    
    return variables, tabla


# ============================================================
# EJEMPLOS PREDEFINIDOS
# ============================================================
st.markdown("---")
st.markdown("**Ejemplos rápidos:**")

ejemplos = {
    "p ∧ q": "Conjunción simple",
    "p ∨ q": "Disyunción simple",
    "p ⊕ q": "XOR",
    "p → q": "Condicional",
    "p ↔ q": "Bicondicional",
    "¬p": "Negación",
    "(p → q) ↔ (¬q → ¬p)": "Ley de contrarrecíproca",
    "p ∨ ¬p": "Tautología",
    "p ∧ ¬p": "Contradicción"
}

cols = st.columns(3)
for i, (expr, desc) in enumerate(ejemplos.items()):
    with cols[i % 3]:
        if st.button(f"{expr}", key=f"ejemplo_{i}", use_container_width=True):
            st.session_state.expr = expr

st.markdown("---")

# ============================================================
# ESTADO INICIAL PARA LA TABLA
# ============================================================
if "tabla_generada" not in st.session_state:
    st.session_state.tabla_generada = False
    st.session_state.df = None
    st.session_state.vars_encontradas = []

# ============================================================
# GENERAR TABLA
# ============================================================
if st.button("🚀 Generar Tabla", type="primary", use_container_width=True):
    if not st.session_state.expr.strip():
        st.warning("⚠️ Ingresa o construye una expresión primero.")
        st.session_state.tabla_generada = False
    else:
        vars_encontradas, tabla = generar_tabla(st.session_state.expr)
        
        if not vars_encontradas:
            st.error("❌ Expresión inválida o sin variables detectadas.")
            st.session_state.tabla_generada = False
        else:
            cols_df = vars_encontradas + ["Resultado"]
            st.session_state.df = pd.DataFrame(tabla, columns=cols_df)
            st.session_state.vars_encontradas = vars_encontradas
            st.session_state.tabla_generada = True

# Mostrar la tabla y resultados si ya fueron generados en la sesión
if st.session_state.tabla_generada and st.session_state.df is not None:
    df = st.session_state.df
    vars_encontradas = st.session_state.vars_encontradas
    tabla = df.values.tolist()
    
    st.success(f"✅ Tabla generada para {len(vars_encontradas)} variable(s) - {len(tabla)} filas")
    
    resultados = df["Resultado"].tolist()
    if all(r == 1 for r in resultados):
        st.info("📊 **Tipo: TAUTOLOGÍA** (siempre verdadera)")
    elif all(r == 0 for r in resultados):
        st.error("📊 **Tipo: CONTRADICCIÓN** (siempre falsa)")
    else:
        st.info("📊 **Tipo: CONTINGENCIA** (depende de los valores)")
    
    st.dataframe(df, use_container_width=True, hide_index=True)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total de filas", len(tabla))
    with col2:
        verdaderos = sum(resultados)
        st.metric("Verdaderos (1)", verdaderos)
    with col3:
        falsos = len(tabla) - verdaderos
        st.metric("Falsos (0)", falsos)
    
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "📥 Descargar CSV",
        csv,
        "tabla_verdad.csv",
        "text/csv",
        use_container_width=True
    )

# ============================================================
# GUÍA DE REFERENCIA
# ============================================================
with st.expander("📚 Guía de Operadores"):
    st.markdown(
        "| Símbolo | Nombre | Significado |\n"
        "|:-------:|:-------|:------------|\n"
        "| **∧** | Conjunción | AND - Verdadero si AMBOS son verdaderos |\n"
        "| **∨** | Disyunción | OR - Verdadero si al menos UNO es verdadero |\n"
        "| **¬** | Negación | NOT - Invierte el valor |\n"
        "| **⊕** | XOR | Verdadero si son DIFERENTES |\n"
        "| **→** | Condicional | Falso solo si p=1 y q=0 |\n"
        "| **↔** | Bicondicional | Verdadero si ambos son IGUALES |\n\n"
        "**Variables permitidas:** p, q, r, s, t, u\n\n"
        "**Ejemplos:**\n"
        "- `p ∧ q` → Conjunción simple\n"
        "- `(p ∨ q) → r` → Condicional con disyunción\n"
        "- `¬p ⊕ q` → XOR con negación\n"
        "- `(p → q) ↔ (¬q → ¬p)` → Ley de contrarrecíproca"
    )

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: gray; font-size: 0.9em;'>"
    "<p>🎓 <strong>Estructuras Discretas</strong> - Ingeniería en Software</p>"
    "<p>💻 Desarrollado con Python y Streamlit</p>"
    "</div>",
    unsafe_allow_html=True
)
