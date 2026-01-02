import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

st.set_page_config(page_title="Monitor Negocios", layout="wide")
st.title("📊 Monitor de Negocios en Vivo")

def conectar_google_sheets():
    try:
        secretos = dict(st.secrets["gcp_service_account"])
        if "private_key" in secretos:
            secretos["private_key"] = secretos["private_key"].replace("\\n", "\n")

        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(secretos, scopes=scopes)
        client = gspread.authorize(creds)
        
        # Asegúrate que este nombre sea correcto
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
            # --- LIMPIEZA DE DATOS (NUEVO) ---
            # Si la columna Monto existe, le quitamos el signo $ y las comas
            if 'Monto' in df.columns:
                # Convertimos a texto, quitamos '$' y ',', y luego a número
                df['Monto'] = df['Monto'].astype(str).str.replace('$', '').str.replace(',', '')
                df['Monto'] = pd.to_numeric(df['Monto'])

            # --- CÁLCULOS ---
            if 'Monto' in df.columns and 'Tipo' in df.columns:
                ingresos = df[df['Tipo'] == 'Ingreso']['Monto'].sum()
                # Sumamos los gastos (asumiendo que en Excel ya pusiste el signo negativo o positivo)
                # Si en tu excel los gastos son positivos (ej: 500), cámbialo a resta.
                # Si son negativos (ej: -500), usa suma.
                gastos = df[df['Tipo'] == 'Gasto']['Monto'].sum() 
                
                # Cálculo de ganancia
                ganancia = ingresos + gastos if gastos < 0 else ingresos - gastos

                col1, col2, col3 = st.columns(3)
                col1.metric("Ingresos Totales", f"${ingresos:,.2f}")
                col2.metric("Gastos Totales", f"${abs(gastos):,.2f}") # abs() para mostrarlo positivo
                col3.metric("Balance", f"${ganancia:,.2f}")
            
            st.subheader("📋 Detalle de Movimientos")
            st.dataframe(df)
        else:
            st.warning("La hoja está vacía.")

    except Exception as e:
        st.error(f"Error al procesar datos: {e}")



