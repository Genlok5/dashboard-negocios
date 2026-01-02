import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import numpy as np
from sklearn.linear_model import LinearRegression
from datetime import datetime

st.set_page_config(page_title="Monitor PRO + IA", layout="wide")

# --- 1. SEGURIDAD (CANDADO RECUPERADO) ---
def check_password():
    """Retorna True si el usuario ingresó la clave correcta."""
    if "password_correct" not in st.session_state:
        st.session_state.password_correct = False

    if st.session_state.password_correct:
        return True

    # Pantalla de Login
    st.title("🔒 Acceso Restringido")
    pwd = st.text_input("Ingresa la contraseña maestra:", type="password")
    
    if st.button("Entrar"):
        # Verifica contra los secrets (Asegúrate de tener [general] password="..." en tus secrets)
        if pwd == st.secrets["general"]["password"]:
            st.session_state.password_correct = True
            st.rerun()
        else:
            st.error("Contraseña incorrecta")
    return False

# Si la contraseña no es correcta, el código se detiene aquí y no muestra nada más
if not check_password():
    st.stop()

# --- SI PASAS LA CLAVE, CARGA EL RESTO ---

st.title("📊 Monitor Financiero Inteligente")

# --- 2. CONEXIÓN ---
def conectar_google_sheets():
    try:
        secretos = dict(st.secrets["gcp_service_account"])
        if "private_key" in secretos:
            secretos["private_key"] = secretos["private_key"].replace("\\n", "\n")

        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(secretos, scopes=scopes)
        client = gspread.authorize(creds)
        sh = client.open("Datos") 
        return sh
    except Exception as e:
        st.error(f"❌ Error al conectar: {e}")
        return None

sh = conectar_google_sheets()

if sh:
    try:
        worksheet = sh.get_worksheet(0)
        datos = worksheet.get_all_records()
        df = pd.DataFrame(datos)

        if not df.empty:
            # --- 3. LIMPIEZA DE DATOS ---
            if 'Monto' in df.columns:
                df['Monto'] = df['Monto'].astype(str).str.replace('$', '').str.replace(',', '')
                df['Monto'] = pd.to_numeric(df['Monto'])
            
            if 'Fecha' in df.columns:
                df['Fecha'] = pd.to_datetime(df['Fecha'], dayfirst=True)
                df['Mes'] = df['Fecha'].dt.strftime('%Y-%m')

            # --- 4. BARRA LATERAL (FILTROS) ---
            st.sidebar.header("🔍 Filtros")

            # Detectar Categoría o Negocio
            columna_filtro = 'Negocio' if 'Negocio' in df.columns else 'Categoría'
            
            lista_categorias = ["Todas"] + list(df[columna_filtro].unique())
            cat_seleccionada = st.sidebar.selectbox(f"Filtrar por {columna_filtro}:", lista_categorias)

            lista_meses = ["Todos"] + sorted(list(df['Mes'].unique()), reverse=True)
            mes_seleccionado = st.sidebar.selectbox("Filtrar por Mes:", lista_meses)

            # --- 5. APLICAR FILTROS ---
            df_ai = df.copy() # Para la IA (Historia completa)
            df_dashboard = df.copy() # Para ver los números del mes

            if cat_seleccionada != "Todas":
                df_dashboard = df_dashboard[df_dashboard[columna_filtro] == cat_seleccionada]
                df_ai = df_ai[df_ai[columna_filtro] == cat_seleccionada]

            if mes_seleccionado != "Todos":
                df_dashboard = df_dashboard[df_dashboard['Mes'] == mes_seleccionado]

            # --- 6. MOSTRAR KPIs ---
            st.subheader(f"Resumen: {mes_seleccionado} - {cat_seleccionada}")
            
            if not df_dashboard.empty:
                ingresos = df_dashboard[df_dashboard['Tipo'] == 'Ingreso']['Monto'].sum()
                gastos = df_dashboard[df_dashboard['Tipo'] == 'Gasto']['Monto'].sum()
                balance = ingresos + gastos if gastos < 0 else ingresos - gastos

                col1, col2, col3 = st.columns(3)
                col1.metric("Ingresos", f"${ingresos:,.2f}")
                col2.metric("Gastos", f"${abs(gastos):,.2f}")
                col3.metric("Balance Neto", f"${balance:,.2f}")
            else:
                st.warning("No hay movimientos con estos filtros.")

            st.divider()

            # --- 7. INTELIGENCIA ARTIFICIAL ---
            st.subheader(f"🔮 Oráculo IA ({cat_seleccionada})")
            
            df_prediccion = df_ai[df_ai['Tipo'] == 'Ingreso'].copy()

            if len(df_prediccion) >= 3:
                df_prediccion['Fecha_Num'] = df_prediccion['Fecha'].map(datetime.toordinal)
                X = df_prediccion[['Fecha_Num']]
                y = df_prediccion['Monto']

                modelo = LinearRegression()
                modelo.fit(X, y)
                tendencia = modelo.coef_[0]

                c1, c2 = st.columns(2)
                with c1:
                    if tendencia > 0:
                        st.success(f"📈 **Creciendo:** +${tendencia:,.2f} / día")
                    else:
                        st.error(f"📉 **Bajando:** -${abs(tendencia):,.2f} / día")
                
                with c2:
                    ultimo_dia = df_prediccion['Fecha_Num'].max()
                    mañana = np.array([[ultimo_dia + 1]])
                    prediccion = modelo.predict(mañana)[0]
                    st.info(f"💰 Ventas estimadas mañana: **${prediccion:,.2f}**")
            else:
                st.info("💡 La IA está aprendiendo (necesita más de 3 días de datos).")

            # --- 8. TABLA ---
            st.divider()
            with st.expander("Ver Tabla de Datos Completa"):
                st.dataframe(df_dashboard)

        else:
            st.warning("Tu hoja de Google Sheets está vacía.")

    except Exception as e:
        st.error(f"Ocurrió un error: {e}")








