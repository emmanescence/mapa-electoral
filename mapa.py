import streamlit as st
import geopandas as gpd
import pandas as pd
import requests
import zipfile
import io
import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1 import make_axes_locatable

# Función para descargar y leer el archivo GeoJSON desde un ZIP
@st.cache
def load_geojson_from_zip(zip_url, geojson_filename):
    response = requests.get(zip_url)
    zip_file = zipfile.ZipFile(io.BytesIO(response.content))
    with zip_file.open(geojson_filename) as geojson_file:
        return gpd.read_file(geojson_file)

# URL del archivo comprimido y nombre del archivo GeoJSON dentro del ZIP
zip_url_circ = 'https://catalogo.datos.gba.gob.ar/dataset/4fe68b69-c788-4c06-ac67-26e4ebc7416b/resource/37bd466c-4a80-4e2e-be11-a68cfe60aa1e/download/circuitos-electorales.zip'
archivo_geojson = 'circuitos-electorales.geojson'

# Cargar el archivo GeoJSON
geo_data = load_geojson_from_zip(zip_url_circ, archivo_geojson)

# Configuración de Streamlit
st.title('Mapa de Circuitos Electorales')

# Selección de la cabecera
st.sidebar.header('Seleccionar Cabecera')
header_options = geo_data['departamen'].unique()
selected_header = st.sidebar.selectbox('Elige una cabecera', header_options)

# Mostrar mapa para la cabecera seleccionada
if st.sidebar.button('Mostrar Mapa para la Cabecera Seleccionada'):
    # Filtrar los datos del GeoDataFrame
    filtered_geo_data = geo_data[geo_data['departamen'] == selected_header]
    
    fig, ax = plt.subplots(figsize=(10, 10))
    divider = make_axes_locatable(ax)
    cax = divider.append_axes("right", size="5%", pad=0.1)
    
    # Graficar el mapa
    filtered_geo_data.plot(ax=ax, color='lightblue', edgecolor='black')
    ax.set_title(f'Circuitos Electorales para {selected_header}', fontsize=16)
    ax.set_xlabel('Longitud', fontsize=12)
    ax.set_ylabel('Latitud', fontsize=12)
    
    st.pyplot(fig)

# Mostrar todos los circuitos con sus cabeceras
if st.sidebar.checkbox('Ver Todos los Circuitos con Sus Cabeceras'):
    fig, ax = plt.subplots(figsize=(10, 10))
    divider = make_axes_locatable(ax)
    cax = divider.append_axes("right", size="5%", pad=0.1)
    
    # Graficar todos los circuitos
    geo_data.plot(ax=ax, color='lightblue', edgecolor='black')
    ax.set_title('Todos los Circuitos Electorales', fontsize=16)
    ax.set_xlabel('Longitud', fontsize=12)
    ax.set_ylabel('Latitud', fontsize=12)
    
    st.pyplot(fig)
