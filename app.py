import streamlit as st
import pandas as pd
import gspread

st.set_page_config(page_title="Monitor Negocios", layout="wide")
st.title("📊 Monitor de Negocios")

# Función de conexión con manejo de errores detallado
def conectar_google_sheets():
    try:
        # Creamos una copia de los secretos para no modificar el original
        secrets_dict = dict(st.secrets["gcp_service_account"])
        
        # Conexión directa
        gc = gspread.service_account_from_dict(secrets_dict)
        
        # Intentar abrir la hoja
        sh = gc.open("Mis Negocios Data") # <--- VERIFICA ESTE NOMBRE
        return sh
    except Exception as e:
        st.error(f"❌ Error CRÍTICO de conexión: {e}")
        return None

# Ejecutar conexión
sh = conectar_google_sheets()

if sh:
    try:
        worksheet = sh.get_worksheet(0)
        datos = worksheet.get_all_records()
        df = pd.DataFrame(datos)

        if not df.empty:
            st.success("✅ Conexión exitosa. Datos cargados.")
            st.dataframe(df)
            # Aquí irían tus gráficas...
        else:
            st.warning("La hoja está vacía.")
            
    except Exception as e:
        st.error(f"Error al leer los datos: {e}")


