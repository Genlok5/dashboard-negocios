import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

st.set_page_config(page_title="Monitor Negocios", layout="wide")
st.title("📊 Monitor de Negocios")

def conectar_google_sheets():
    try:
        # 1. Recuperamos los secretos
        secretos = dict(st.secrets["gcp_service_account"])

        # 2. TRUCO DE LIMPIEZA: Forzamos el formato correcto de la llave
        # Esto arregla el error <Response [200]> causado por saltos de línea rotos
        if "private_key" in secretos:
            secretos["private_key"] = secretos["private_key"].replace("\\n", "\n")

        # 3. Definimos los permisos
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]

        # 4. Conectamos
        creds = Credentials.from_service_account_info(secretos, scopes=scopes)
        client = gspread.authorize(creds)

        # 5. Abrimos la hoja
        # IMPORTANTE: Verifica que este nombre sea IDÉNTICO a tu archivo en Drive
        sh = client.open("Mis Negocios Data") 
        return sh

    except Exception as e:
        st.error(f"❌ Error detallado: {e}")
        return None

# Ejecutamos
sh = conectar_google_sheets()

if sh:
    try:
        worksheet = sh.get_worksheet(0)
        datos = worksheet.get_all_records()
        df = pd.DataFrame(datos)

        if not df.empty:
            st.success("✅ ¡Conexión Exitosa!")
            st.dataframe(df)
        else:
            st.warning("La hoja está vacía.")

    except Exception as e:
        st.error(f"Error al leer datos: {e}")



