import streamlit as st
import pandas as pd
from datetime import datetime
import os
import io

# --- 1. CONFIGURACIÓN Y ESTILO ---
st.set_page_config(page_title="insumos jm de los rios", layout="wide")

st.markdown("""
    <style>
    /* Fondo Azul Rey */
    .stApp { background-color: #143d8d; }
    
    /* Textos en Blanco */
    h1, h2, h3, p, label, span, .stMarkdown { color: white !important; }
    
    /* Botones Rojo Oscuro */
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        background-color: #8b0000;
        color: white !important;
        font-weight: bold;
        border: none;
        height: 3.5em;
    }

    /* Campos de texto Negros */
    input, textarea, [data-baseweb="select"] > div {
        background-color: #000000 !important;
        color: white !important;
        border: 1px solid #444444 !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. BASE DE DATOS ---
if not os.path.exists('historial.csv'):
    pd.DataFrame(columns=['Fecha', 'Insumo', 'Accion', 'Cant', 'Usuario']).to_csv('historial.csv', index=False)

def obtener_stock():
    df = pd.read_csv('historial.csv')
    if df.empty: return pd.DataFrame(columns=['Insumo', 'Stock Actual'])
    df['Balance'] = df.apply(lambda x: x['Cant'] if x['Accion'] == 'ENTRADA' else -x['Cant'], axis=1)
    stock = df.groupby('Insumo')['Balance'].sum().reset_index()
    stock.columns = ['Insumo', 'Stock Actual']
    return stock

USUARIOS = {"marly": "23154782", "enfermera1": "med1", "farmacia": "farma1"}

if 'auth' not in st.session_state: st.session_state.auth = False
if 'page' not in st.session_state: st.session_state.page = "menu"

# --- 3. LOGIN ---
if not st.session_state.auth:
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        if os.path.exists('logo.png'): st.image('logo.png', use_container_width=True)
        st.markdown("<h1 style='text-align: center;'>INSUMOS JM DE LOS RIOS</h1>", unsafe_allow_html=True)
        u = st.text_input("Usuario")
        p = st.text_input("Contraseña", type="password")
        if st.button("INICIAR SESIÓN"):
            if u in USUARIOS and USUARIOS[u] == p:
                st.session_state.auth = True
                st.session_state.user = u
                st.rerun()
            else: st.error("Acceso denegado")

# --- 4. PANEL PRINCIPAL ---
else:
    # Encabezado
    h1, h2 = st.columns([1, 1])
    with h1:
        if os.path.exists('logo.png'): st.image('logo.png', width=70)
    with h2:
        st.markdown(f"<p style='text-align: right;'>👤 Usuario: {st.session_state.user}</p>", unsafe_allow_html=True)
    
    # Navegación (Se pondrá vertical sola en móviles)
    nav1, nav2, nav3, nav4 = st.columns(4)
    with nav1: 
        if st.button("ENTRADA"): st.session_state.page = "in"
    with nav2: 
        if st.button("SALIDA"): st.session_state.page = "out"
    with nav3: 
        if st.button("HISTORIAL"): st.session_state.page = "log"
    with nav4:
        if st.button("STOCK"): st.session_state.page = "stock"

    st.markdown("---")

    # PÁGINAS
    if st.session_state.page in ["in", "out"]:
        tipo = "ENTRADA" if st.session_state.page == "in" else "SALIDA"
        st.subheader(f"Registro de {tipo}")
        item = st.text_input("Nombre del Insumo").upper()
        qty = st.number_input("Cantidad", min_value=1)
        
        c_b1, c_b2 = st.columns(2)
        with c_b1:
            if st.button("CONFIRMAR"):
                fecha = datetime.now().strftime("%Y-%m-%d %H:%M")
                nuevo = pd.DataFrame([[fecha, item, tipo, qty, st.session_state.user]], columns=['Fecha', 'Insumo', 'Accion', 'Cant', 'Usuario'])
                nuevo.to_csv('historial.csv', mode='a', header=False, index=False)
                st.success("✅ Guardado")
                st.session_state.page = "menu"
                st.rerun()
        with c_b2:
            if st.button("VOLVER"):
                st.session_state.page = "menu"
                st.rerun()

    elif st.session_state.page == "stock":
        st.subheader("📦 Inventario Actual")
        st.dataframe(obtener_stock(), use_container_width=True)
        if st.button("VOLVER AL MENÚ"):
            st.session_state.page = "menu"
            st.rerun()

    elif st.session_state.page == "log":
        st.subheader("📊 Historial y Filtros")
        df = pd.read_csv('historial.csv')
        
        # Filtros (Verticales en móvil, horizontales en PC)
        f1, f2, f3, f4, f5 = st.columns(5)
        with f1: f_insumo = st.text_input("Buscar Insumo").upper()
        with f2: f_accion = st.selectbox("Acción", ["Todos", "ENTRADA", "SALIDA"])
        with f3: f_usuario = st.selectbox("Usuario", ["Todos"] + list(df['Usuario'].unique()))
        with f4: f_cant = st.number_input("Cant. Mínima", min_value=0)
        with f5: f_fecha = st.text_input("Fecha (AAAA-MM)")

        df_f = df.copy()
        if f_insumo: df_f = df_f[df_f['Insumo'].str.contains(f_insumo, na=False)]
        if f_accion != "Todos": df_f = df_f[df_f['Accion'] == f_accion]
        if f_usuario != "Todos": df_f = df_f[df_f['Usuario'] == f_usuario]
        df_f = df_f[df_f['Cant'] >= f_cant]
        if f_fecha: df_f = df_f[df_f['Fecha'].str.contains(f_fecha, na=False)]

        st.dataframe(df_f.iloc[::-1], use_container_width=True)

        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            df_f.to_excel(writer, index=False, sheet_name='Historial')
        st.download_button("📥 DESCARGAR EXCEL", data=buffer.getvalue(), file_name="reporte.xlsx", mime="application/vnd.ms-excel")
        
        if st.button("CERRAR HISTORIAL"):
            st.session_state.page = "menu"
            st.rerun()

    if st.session_state.page == "menu":
        st.markdown("<h2 style='text-align: center;'>Panel de Control</h2>", unsafe_allow_html=True)
        df = pd.read_csv('historial.csv')
        if not df.empty:
            c1, c2 = st.columns(2)
            with c1:
                st.write("### Últimos movimientos")
                st.table(df.tail(3))
            with c2:
                st.write("### Resumen Stock")
                st.table(obtener_stock().head(3)) 