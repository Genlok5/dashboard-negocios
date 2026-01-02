import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import numpy as np
from sklearn.linear_model import LinearRegression
from datetime import datetime

st.set_page_config(page_title="Monitor Inteligente", layout="wide")
st.title("📊 Monitor de Negocios + IA 🧠")

# --- CONEXIÓN ---
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
            if 'Monto' in df.columns:
                df['Monto'] = df['Monto'].astype(str).str.replace('$', '').str.replace(',', '')
                df['Monto'] = pd.to_numeric(df['Monto'])
            
            if 'Fecha' in df.columns:
                df['Fecha'] = pd.to_datetime(df['Fecha'], dayfirst=True)

            # --- DASHBOARD PRINCIPAL ---
            # Filtro de Mes
            df['Mes'] = df['Fecha'].dt.strftime('%Y-%m')
            lista_meses = ["Todos"] + list(df['Mes'].unique())
            mes_seleccionado = st.sidebar.selectbox("Filtrar por Mes:", lista_meses)

            df_filtrado = df.copy()
            if mes_seleccionado != "Todos":
                df_filtrado = df_filtrado[df_filtrado['Mes'] == mes_seleccionado]

            # KPIs
            ingresos = df_filtrado[df_filtrado['Tipo'] == 'Ingreso']['Monto'].sum()
            gastos = df_filtrado[df_filtrado['Tipo'] == 'Gasto']['Monto'].sum()
            balance = ingresos + gastos if gastos < 0 else ingresos - gastos

            col1, col2, col3 = st.columns(3)
            col1.metric("Ingresos", f"${ingresos:,.2f}")
            col2.metric("Gastos", f"${abs(gastos):,.2f}")
            col3.metric("Balance", f"${balance:,.2f}")

            st.divider()

            # --- SECCIÓN DE INTELIGENCIA ARTIFICIAL (NUEVO) ---
            st.subheader("🔮 Oráculo de Predicción (IA)")
            
            # Solo predecimos si hay suficientes datos de Ingresos
            df_ia = df[df['Tipo'] == 'Ingreso'].copy()
            
            if len(df_ia) >= 3: # Necesitamos mínimo 3 ventas para calcular tendencia
                # 1. Preparar datos: La IA no entiende fechas, entiende "Día 1, Día 2..."
                # Convertimos fecha a número ordinal
                df_ia['Fecha_Num'] = df_ia['Fecha'].map(datetime.toordinal)
                
                X = df_ia[['Fecha_Num']] # Eje X (Tiempo)
                y = df_ia['Monto']       # Eje Y (Dinero)

                # 2. Entrenar Modelo
                modelo = LinearRegression()
                modelo.fit(X, y)

                # 3. Calcular la Tendencia (Coeficiente)
                tendencia = modelo.coef_[0]
                
                col_ia1, col_ia2 = st.columns(2)
                
                with col_ia1:
                    st.info(f"📈 Tendencia diaria detectada: **${tendencia:,.2f} / día**")
                    if tendencia > 0:
                        st.write("Tu negocio está **creciendo** 🚀")
                    else:
                        st.write("Tu negocio está **decreciendo** 📉. ¡Cuidado!")

                with col_ia2:
                    # 4. Predecir el futuro (Mañana)
                    ultimo_dia_conocido = df_ia['Fecha_Num'].max()
                    mañana = np.array([[ultimo_dia_conocido + 1]])
                    prediccion_mañana = modelo.predict(mañana)[0]
                    
                    st.success(f"💰 Predicción de ventas para mañana: **${prediccion_mañana:,.2f}**")

            else:
                st.warning("⚠️ La IA necesita al menos 3 registros de ingresos para aprender.")

            # --- TABLAS ---
            st.divider()
            st.subheader("📋 Detalle de Movimientos")
            st.dataframe(df_filtrado)

        else:
            st.warning("Tu Excel está vacío.")

    except Exception as e:
        st.error(f"Error procesando datos: {e}")





