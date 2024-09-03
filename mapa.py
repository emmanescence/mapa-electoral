import streamlit as st
import geopandas as gpd
import pandas as pd
import requests
import zipfile
import io
import gc

st.title('Mapa Electoral Interactivo')

@st.cache_data(show_spinner=True)
def cargar_datos():
    zip_url_resultados = 'https://www.argentina.gob.ar/sites/default/files/2023_generales_1.zip'
    response = requests.get(zip_url_resultados)
    zip_file_resultados = zipfile.ZipFile(io.BytesIO(response.content))

    archivo_csv = '2023_Generales/ResultadoElectorales_2023_Generales.csv'
    with zip_file_resultados.open(archivo_csv) as csv_file:
        # Cargar solo las primeras 1000 filas para pruebas
        csv_df = pd.read_csv(csv_file, dtype={'nombre_columna': 'str'}, nrows=1000, low_memory=False)

    # Liberar recursos no utilizados
    del response, zip_file_resultados
    gc.collect()

    zip_url_circ = 'https://catalogo.datos.gba.gob.ar/dataset/4fe68b69-c788-4c06-ac67-26e4ebc7416b/resource/37bd466c-4a80-4e2e-be11-a68cfe60aa1e/download/circuitos-electorales.zip'
    response = requests.get(zip_url_circ)
    zip_file_circ = zipfile.ZipFile(io.BytesIO(response.content))

    archivo_geojson = 'circuitos-electorales.geojson'
    with zip_file_circ.open(archivo_geojson) as geojson_file:
        geo_df = gpd.read_file(geojson_file)

    del response, zip_file_circ
    gc.collect()

    return csv_df, geo_df

csv_df, geo_df = cargar_datos()

cabecera = st.selectbox('Selecciona una cabecera', ['Todas'] + list(geo_df['cabecera'].unique()))
cargo_nombre = st.selectbox('Selecciona un cargo', csv_df['cargo_nombre'].unique())
circuito = st.selectbox('Selecciona un circuito', ['Todos'] + list(geo_df['circuito'].unique()))

def actualizar_mapa(cabecera, cargo_nombre, circuito):
    pass  # Lógica para actualizar el mapa

if st.button('Actualizar mapa'):
    actualizar_mapa(cabecera, cargo_nombre, circuito)
