import streamlit as st
import pandas as pd
import zipfile
import requests
import io

# URL del archivo comprimido
zip_url_resultados = 'https://www.argentina.gob.ar/sites/default/files/2023_generales_1.zip'

# Descargar y descomprimir el archivo
def download_and_extract_zip(url):
    response = requests.get(url)
    with zipfile.ZipFile(io.BytesIO(response.content)) as z:
        z.extractall('data')

# Cargar los datos
def load_data():
    download_and_extract_zip(zip_url_resultados)
    # Aquí deberías adaptar el nombre del archivo según lo que contiene el zip
    try:
        df = pd.read_csv('circuitos-electorales.geojson', delimiter=',', error_bad_lines=False, warn_bad_lines=True)
    except Exception as e:
        st.error(f'Error al cargar los datos: {e}')
        return pd.DataFrame()  # Retorna un DataFrame vacío en caso de error
    return df

# Crear la aplicación en Streamlit
def main():
    st.title('Resultados Electorales por Cabecera')
    
    # Cargar los datos
    df = load_data()
    
    if df.empty:
        st.warning('No se pudieron cargar los datos.')
        return
    
    # Selección de cabecera
    cabeceras = df['Cabecera'].unique()  # Asegúrate de que la columna se llama 'Cabecera'
    selected_cabecera = st.selectbox('Selecciona una cabecera:', cabeceras)
    
    # Filtrar los datos por cabecera
    filtered_df = df[df['Cabecera'] == selected_cabecera]
    
    st.write(f'Resultados para la cabecera: {selected_cabecera}')
    st.dataframe(filtered_df)

if __name__ == "__main__":
    main()
