import streamlit as st
import re
from itertools import product
import pandas as pd

st.set_page_config(page_title="Calculadora Tabla de la Verdad", layout="centered")

st.title("🧮 Calculadora de Tabla de la Verdad")
st.markdown("Construye tu expresión haciendo clic. El resultado se mostrará **exclusivamente en 0 y 1**.")

# --- Estado de la sesión ---
if "expr" not in st.session_state:
    st.session_state.expr = ""

# --- UI: Constructor de Expresión ---
st.subheader("🛠️ Constructor de Expresión")

cols = st.columns(6)
variables = ["A", "B", "C", "D", "E", "F"]
for i, v in enumerate(variables):
    with cols[i % 6]:
        if st.button(f"{v}", key=f"btn_v{v}", use_container_width=True):
            st.session_state.expr += f" {v} "

st.markdown("---")

st.subheader("➕ Operadores")

cols = st.columns(6)
operadores = ["AND", "OR", "NOT", "XOR", "->", "<->", "(", ")"]
for i, op in enumerate(operadores):
    with cols[i % 6]:
        if st.button(f"{op}", key=f"btn_{op}", use_container_width=True):
            if op == "NOT":
                st.session_state.expr += " NOT "
            elif op in ("(", ")"):
                st.session_state.expr += f"{op}"
            else:
                st.session_state.expr += f" {op} "

col_limpiar, col_preview, col_gen = st.columns([2, 3, 2])

with col_limpiar:
    if st.button("🗑️ Limpiar", type="secondary", use_container_width=True):
        st.session_state.expr = ""

with col_preview:
    st.code(st.session_state.expr.strip() or "(vacío)", language="text")


# --- Lógica Central ---
def normalizar_expresion(expr: str) -> str:
    e = expr.strip().upper()
    e = re.sub(r'\bAND\b', ' and ', e)
    e = re.sub(r'\bOR\b', ' or ', e)
    e = re.sub(r'\bNOT\b', ' not ', e)
    e = re.sub(r'\bXOR\b', ' ^ ', e)
    
    # Implicación y Bicondicional
    e = re.sub(r'([A-Z])\s*->\s*([A-Z])', r'(not \1 or \2)', e)
    e = re.sub(r'([A-Z])\s*<->\s*([A-Z])', r'(\1 == \2)', e)
    
    return re.sub(r'\s+', ' ', e).strip()

def extraer_variables(expr: str) -> list:
    return sorted(set(re.findall(r'\b[A-Z]\b', expr)))

def generar_tabla(expr_raw: str):
    if not expr_raw.strip():
        return [], []
    
    expr_norm = normalizar_expresion(expr_raw)
    variables = extraer_variables(expr_norm)
    
    if not variables:
        return [], []
    
    tabla = []
    
    # Generamos combinaciones directamente en 0/1
    for valores in product([0, 1], repeat=len(variables)):
        entorno = {v: bool(val) for v, val in zip(variables, valores)}
        try:
            resultado = eval(expr_norm, {"__builtins__": {}}, entorno)
            # Lista plana [0, 1, 0] en lugar de ([0, 1], 0)
            fila = list(valores) + [int(bool(resultado))]
            tabla.append(fila)
        except Exception:
            return [], []
            
    return variables, tabla


# --- Ejecución ---
if st.button("🚀 Generar Tabla", type="primary", use_container_width=True):
    if not st.session_state.expr.strip():
        st.warning("⚠️ Ingresa o construye una expresión primero.")
    else:
        vars, tabla = generar_tabla(st.session_state.expr)
        
        if not vars:
            st.error("❌ Expresión inválida o sin variables detectadas.")
        else:
            cols_df = vars + ["Resultado"]
            df = pd.DataFrame(tabla, columns=cols_df)
            
            st.success(f"✅ Tabla generada para {len(vars)} variable(s)")
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button("📥 Descargar CSV", csv, "tabla_verdad.csv", "text/csv")