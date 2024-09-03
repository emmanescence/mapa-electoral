import streamlit as st
import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from mpl_toolkits.axes_grid1 import make_axes_locatable

# Cargar el archivo GeoJSON
@st.cache
def load_geojson(file_path):
    return gpd.read_file(file_path)

# Cargar el archivo CSV con los nombres de cabeceras
@st.cache
def load_csv(file_path):
    return pd.read_csv(file_path)

# Cargar los datos
geojson_file = 'path_to_your_geojson_file.geojson'
csv_file = 'path_to_your_csv_file.csv'

geo_data = load_geojson(geojson_file)
header_data = load_csv(csv_file)

# Configuración de Streamlit
st.title('Mapa de Circuitos Electorales')

# Selección de la cabecera
st.sidebar.header('Seleccionar Cabecera')
selected_header = st.sidebar.selectbox('Elige una cabecera', header_data['seccion_nombre'].unique())

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

