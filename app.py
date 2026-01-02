import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

st.title("🛠️ Prueba de Diagnóstico")

def probar_conexion():
    try:
        # 1. Cargar secretos
        secretos = dict(st.secrets["gcp_service_account"])
        
        # Corrección de formato de llave
        if "private_key" in secretos:
            secretos["private_key"] = secretos["private_key"].replace("\\n", "\n")

        # 2. Definir alcance
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]

        # 3. Autenticar
        creds = Credentials.from_service_account_info(secretos, scopes=scopes)
        client = gspread.authorize(creds)

        # 4. PRUEBA DE FUEGO: Listar archivos
        st.info("Intentando listar tus hojas de cálculo...")
        archivos = client.list_spreadsheet_files()
        
        if archivos:
            st.success(f"✅ ¡ÉXITO! El robot ve {len(archivos)} archivos.")
            st.write("Estos son los archivos que puede ver:")
            for f in archivos:
                st.code(f"Nombre: {f['name']} | ID: {f['id']}")
        else:
            st.warning("⚠️ Conexión exitosa, pero el robot no ve ningún archivo. ¿Compartiste el Excel con su email?")
            st.write(f"Email del robot: {secretos.get('client_email')}")

    except Exception as e:
        st.error("❌ Falló la conexión.")
        st.write(f"Tipo de error: {type(e).__name__}")
        st.write(f"Mensaje de error: {e}")

if st.button("Correr Diagnóstico"):
    probar_conexion()
