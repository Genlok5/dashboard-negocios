import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import numpy as np
from sklearn.linear_model import LinearRegression
from datetime import datetime

st.set_page_config(page_title="Monitor PRO", layout="wide")
st.title("📊 Monitor Financiero Inteligente")

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
            # --- 1. LIMPIEZA DE DATOS ---
            # Limpiamos símbolos de moneda
            if 'Monto' in df.columns:
                df['Monto'] = df['Monto'].astype(str).str.replace('$', '').str.replace(',', '')
                df['Monto'] = pd.to_numeric(df['Monto'])
            
            # Formato de Fechas
            if 'Fecha' in df.columns:
                df['Fecha'] = pd.to_datetime(df['Fecha'], dayfirst=True)
                df['Mes'] = df['Fecha'].dt.strftime('%Y-%m') # Creamos columna Mes para filtrar

            # --- 2. BARRA LATERAL (FILTROS) ---
            st.sidebar.header("🔍 Filtros")

            # A. Filtro de Categoría / Negocio
            # Detectamos si usas "Negocio" o "Categoría" en tu Excel
            columna_filtro = 'Negocio' if 'Negocio' in df.columns else 'Categoría'
            
            lista_categorias = ["Todas"] + list(df[columna_filtro].unique())
            cat_seleccionada = st.sidebar.selectbox(f"Filtrar por {columna_filtro}:", lista_categorias)

            # B. Filtro de Mes
            lista_meses = ["Todos"] + sorted(list(df['Mes'].unique()), reverse=True)
            mes_seleccionado = st.sidebar.selectbox("Filtrar por Mes:", lista_meses)

            # --- 3. APLICAR FILTROS ---
            # Creamos dos copias de datos:
            # df_ai -> Para la IA (Necesita TODA la historia de la categoría, no solo un mes)
            # df_dashboard -> Para ver los números del mes seleccionado
            
            df_ai = df.copy()
            df_dashboard = df.copy()

            # Filtramos por Categoría en ambos
            if cat_seleccionada != "Todas":
                df_dashboard = df_dashboard[df_dashboard[columna_filtro] == cat_seleccionada]
                df_ai = df_ai[df_ai[columna_filtro] == cat_seleccionada]

            # Filtramos por Mes SOLO en el Dashboard (La IA necesita historia completa)
            if mes_seleccionado != "Todos":
                df_dashboard = df_dashboard[df_dashboard['Mes'] == mes_seleccionado]

            # --- 4. MOSTRAR KPIs (Del Mes Seleccionado) ---
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

            # --- 5. INTELIGENCIA ARTIFICIAL (Basada en la Categoría) ---
            st.subheader(f"🔮 Oráculo IA ({cat_seleccionada})")
            
            # Solo analizamos Ingresos para predecir ventas
            df_prediccion = df_ai[df_ai['Tipo'] == 'Ingreso'].copy()

            if len(df_prediccion) >= 3:
                # Preparamos datos matemáticos
                df_prediccion['Fecha_Num'] = df_prediccion['Fecha'].map(datetime.toordinal)
                X = df_prediccion[['Fecha_Num']]
                y = df_prediccion['Monto']

                modelo = LinearRegression()
                modelo.fit(X, y)
                tendencia = modelo.coef_[0]

                # Mostramos resultados
                c1, c2 = st.columns(2)
                with c1:
                    if tendencia > 0:
                        st.success(f"📈 **Tendencia Positiva:** Estás creciendo aprox **${tendencia:,.2f}** por día en esta categoría.")
                    else:
                        st.error(f"📉 **Tendencia Negativa:** Las ventas están bajando **${abs(tendencia):,.2f}** por día.")
                
                with c2:
                    # Predicción para mañana
                    ultimo_dia = df_prediccion['Fecha_Num'].max()
                    mañana = np.array([[ultimo_dia + 1]])
                    prediccion = modelo.predict(mañana)[0]
                    st.info(f"💰 Se estima que mañana ingresarán: **${prediccion:,.2f}**")
            else:
                st.info("💡 Necesito al menos 3 días de ventas históricas en esta categoría para poder predecir el futuro.")

            # --- 6. TABLA DETALLADA ---
            st.divider()
            with st.expander("Ver Tabla de Datos Completa"):
                st.dataframe(df_dashboard)

        else:
            st.warning("Tu hoja de Google Sheets está vacía.")

    except Exception as e:
        st.error(f"Ocurrió un error: {e}")







