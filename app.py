import streamlit as st
import pandas as pd
import gspread
import numpy as np
from sklearn.linear_model import LinearRegression
from google.oauth2.service_account import Credentials
from datetime import datetime

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Monitor Negocios PRO", layout="wide")

# --- 1. FUNCIÓN DE SEGURIDAD (CANDADO) ---
def check_password():
    """Retorna True si el usuario ingresó la clave correcta."""
    if "password_correct" not in st.session_state:
        st.session_state.password_correct = False

    if st.session_state.password_correct:
        return True

    # Input de contraseña
    st.title("🔒 Acceso Restringido")
    pwd = st.text_input("Ingresa la contraseña maestra:", type="password")
    
    if st.button("Entrar"):
        # Verifica contra los secrets que configuraste
        if pwd == st.secrets["general"]["password"]:
            st.session_state.password_correct = True
            st.rerun() # Recarga la página
        else:
            st.error("Contraseña incorrecta")
    return False

# Si la contraseña no es correcta, detiene todo aquí
if not check_password():
    st.stop()

# --- SI PASA EL CANDADO, MUESTRA EL RESTO ---

st.sidebar.title("🎛️ Filtros") # Barra lateral

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
            # --- LIMPIEZA DE DATOS ---
            # 1. Limpiar dinero
            if 'Monto' in df.columns:
                df['Monto'] = df['Monto'].astype(str).str.replace('$', '').str.replace(',', '')
                df['Monto'] = pd.to_numeric(df['Monto'])
            
            # 2. Convertir Fechas (Vital para el filtro)
            # Asumimos formato dia/mes/año (ej: 01/01/2026)
            if 'Fecha' in df.columns:
                df['Fecha'] = pd.to_datetime(df['Fecha'], dayfirst=True)

            # --- FILTROS INTELIGENTES (SIDEBAR) ---
            
            # A. Filtro de Negocio
            lista_negocios = ["Todos"] + list(df['Negocio'].unique())
            negocio_seleccionado = st.sidebar.selectbox("Selecciona un Negocio:", lista_negocios)
            
            # B. Filtro de Fechas
            min_date = df['Fecha'].min().date()
            max_date = df['Fecha'].max().date()
            
            st.sidebar.write("Rango de Fechas:")
            fecha_inicio = st.sidebar.date_input("Desde", min_date)
            fecha_fin = st.sidebar.date_input("Hasta", max_date)

            # --- APLICAR FILTROS ---
            df_filtrado = df.copy()

            # 1. Filtrar por negocio (si no es 'Todos')
            if negocio_seleccionado != "Todos":
                df_filtrado = df_filtrado[df_filtrado['Negocio'] == negocio_seleccionado]
            
            # 2. Filtrar por fechas (convertimos a datetime para comparar)
            df_filtrado = df_filtrado[
                (df_filtrado['Fecha'].dt.date >= fecha_inicio) & 
                (df_filtrado['Fecha'].dt.date <= fecha_fin)
            ]

            # --- DASHBOARD PRINCIPAL ---
            st.title(f"📊 Resultados: {negocio_seleccionado}")
            st.markdown(f"*Mostrando datos del {fecha_inicio} al {fecha_fin}*")

            if not df_filtrado.empty:
                # Cálculos sobre datos FILTRADOS
                ingresos = df_filtrado[df_filtrado['Tipo'] == 'Ingreso']['Monto'].sum()
                gastos = df_filtrado[df_filtrado['Tipo'] == 'Gasto']['Monto'].sum()
                balance = ingresos + gastos if gastos < 0 else ingresos - gastos

                # Tarjetas
                col1, col2, col3 = st.columns(3)
                col1.metric("Ingresos", f"${ingresos:,.2f}")
                col2.metric("Gastos", f"${abs(gastos):,.2f}")
                col3.metric("Ganancia Neta", f"${balance:,.2f}", 
                            delta_color="normal")

                # Gráficas y Tablas
                tab1, tab2 = st.tabs(["📈 Gráficos", "📋 Tabla de Datos"])
                
                with tab1:
                    # Gráfica de barras por día
                    st.subheader("Ingresos por Día")
                    datos_grafica = df_filtrado[df_filtrado['Tipo']=='Ingreso'].groupby('Fecha')['Monto'].sum()
                    st.bar_chart(datos_grafica)
                
                with tab2:
                    # Tabla con formato bonito
                    # Regresamos la fecha a texto para que se lea bien
                    df_show = df_filtrado.copy()
                    df_show['Fecha'] = df_show['Fecha'].dt.strftime('%d/%m/%Y')
                    st.dataframe(df_show, use_container_width=True)
            else:
                st.info("No hay datos para los filtros seleccionados.")

        else:
            st.warning("Tu Excel está vacío.")

    except Exception as e:
        st.error(f"Error procesando datos: {e}")
st.divider()
st.subheader("🔮 Predicción de Ventas")

if not df.empty and 'Fecha' in df.columns and 'Monto' in df.columns:
    # 1. Preparamos los datos para la IA
    # Filtramos solo Ingresos
    df_ingresos = df[df['Tipo'] == 'Ingreso'].copy()
    
    # La IA no entiende fechas, entiende números. Convertimos fecha a "Día del año"
    df_ingresos['Dia_Numero'] = df_ingresos['Fecha'].map(datetime.toordinal)
    
    X = df_ingresos[['Dia_Numero']] # Fechas (Input)
    y = df_ingresos['Monto']        # Dinero (Output)
    
    if len(df_ingresos) > 5: # Necesitamos al menos 5 datos para aprender
        # 2. Entrenamos al modelo
        modelo = LinearRegression()
        modelo.fit(X, y)
        
        # 3. Predecimos el futuro (ej: próximos 7 días)
        ultimo_dia = df_ingresos['Dia_Numero'].max()
        futuro_dias = np.array([ultimo_dia + i for i in range(1, 8)]).reshape(-1, 1)
        prediccion = modelo.predict(futuro_dias)
        
        st.write(f"Según la tendencia, mañana venderás aprox: **${prediccion[0]:,.2f}**")
    else:
        st.info("Necesitas más datos históricos para hacer predicciones.")





