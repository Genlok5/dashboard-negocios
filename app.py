import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

st.set_page_config(page_title="Monitor Negocios", layout="wide")
st.title("📊 Monitor de Negocios en Vivo")

def conectar_google_sheets():
    try:
        # 1. Cargar secretos y corregir formato de llave
        secretos = dict(st.secrets["gcp_service_account"])
        if "private_key" in secretos:
            secretos["private_key"] = secretos["private_key"].replace("\\n", "\n")

        # 2. Definir alcance (Scope)
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]

        # 3. Autenticar
        creds = Credentials.from_service_account_info(secretos, scopes=scopes)
        client = gspread.authorize(creds)

        # 4. Abrir la hoja
        # ⚠️ IMPORTANTE: Asegúrate de que tu archivo en Drive se llame EXACTAMENTE así:
        sh = client.open("Mis Negocios Data") 
        return sh

    except Exception as e:
        st.error(f"❌ Error al conectar: {e}")
        return None

# Ejecutar la app
sh = conectar_google_sheets()

if sh:
    try:
        worksheet = sh.get_worksheet(0)
        datos = worksheet.get_all_records()
        df = pd.DataFrame(datos)

        if not df.empty:
            # --- MÉTRICAS ---
            # Intentamos calcular totales si existen las columnas 'Monto' y 'Tipo'
            # Si tus columnas tienen otros nombres, el código seguirá funcionando mostrando solo la tabla
            if 'Monto' in df.columns and 'Tipo' in df.columns:
                ingresos = df[df['Tipo'] == 'Ingreso']['Monto'].sum()
                gastos = df[df['Tipo'] == 'Gasto']['Monto'].sum()
                ganancia = ingresos - gastos # Resta simple (Ingresos - Gastos absolutos)
                
                # Para mostrarlo bien, a veces los gastos se registran negativos. 
                # Si en tu Excel los gastos son negativos (ej: -500), la fórmula sería suma directa.
                # Aquí asumo que son positivos y los restamos.
                
                col1, col2, col3 = st.columns(3)
                col1.metric("Ingresos Totales", f"${ingresos:,.2f}")
                col2.metric("Gastos Totales", f"${gastos:,.2f}")
                col3.metric("Balance", f"${(ingresos - gastos):,.2f}")
            
            st.subheader("📋 Detalle de Movimientos")
            st.dataframe(df)
        else:
            st.warning("La hoja está vacía. Agrega datos en tu Google Sheet.")

    except Exception as e:
        st.error(f"Error al leer la hoja: {e}")

