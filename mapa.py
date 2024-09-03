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

# Función para descargar y leer el archivo CSV desde un ZIP
@st.cache
def load_csv_from_zip(zip_url, csv_filename):
    response = requests.get(zip_url)
    zip_file = zipfile.ZipFile(io.BytesIO(response.content))
    with zip_file.open(csv_filename) as csv_file:
        return pd.read_csv(csv_file)

# URL de los archivos comprimidos y nombres de los archivos dentro del ZIP
zip_url_circ = 'https://catalogo.datos.gba.gob.ar/dataset/4fe68b69-c788-4c06-ac67-26e4ebc7416b/resource/37bd466c-4a80-4e2e-be11-a68cfe60aa1e/download/circuitos-electorales.zip'
archivo_geojson = 'circuitos-electorales.geojson'

zip_url_resultados = 'https://www.argentina.gob.ar/sites/default/files/2023_generales_1.zip'
archivo_csv = '2023_Generales/ResultadoElectorales_2023_Generales.csv'

# Cargar los datos
geo_data = load_geojson_from_zip(zip_url_circ, archivo_geojson)
resultados_df = load_csv_from_zip(zip_url_resultados, archivo_csv)

# Preparar los datos de resultados
resultados_df['circuito_id'] = resultados_df['circuito_id'].astype(str).str.zfill(4)  # Asegurarse de que tenga ceros a la izquierda
geo_data['circuito_id'] = geo_data['circuito_id'].astype(str).str.zfill(4)  # Asegurarse de que tenga ceros a la izquierda

# Unir los DataFrames
merged_df = geo_data.merge(resultados_df, on='circuito_id')

# Encontrar el partido con más votos en cada circuito
resultados_agrupados = merged_df.groupby('circuito_id').apply(
    lambda x: x.loc[x['votos_cantidad'].idxmax()]
).reset_index(drop=True)

# Función para asignar colores según el partido
def asignar_color(agrupacion_nombre):
    if agrupacion_nombre == 'JUNTOS POR EL CAMBIO':
        return 'yellow'
    elif agrupacion_nombre == 'LA LIBERTAD AVANZA':
        return 'violet'
    elif agrupacion_nombre == 'UNION POR LA PATRIA':
        return 'blue'
    else:
        return 'darkgrey'

# Asignar colores al GeoDataFrame
resultados_agrupados['color'] = resultados_agrupados['agrupacion_nombre'].apply(asignar_color)

# Configuración de Streamlit
st.title('Mapa de Resultados Electorales 2023')

# Selección de la cabecera
st.sidebar.header('Seleccionar Cabecera')
header_options = geo_data['departamen'].unique()
selected_header = st.sidebar.selectbox('Elige una cabecera', header_options)

# Mostrar mapa para la cabecera seleccionada
if st.sidebar.button('Mostrar Mapa para la Cabecera Seleccionada'):
    # Filtrar los datos del GeoDataFrame
    filtered_geo_data = resultados_agrupados[resultados_agrupados['departamen'] == selected_header]
    
    fig, ax = plt.subplots(figsize=(10, 10))
    divider = make_axes_locatable(ax)
    cax = divider.append_axes("right", size="5%", pad=0.1)
    
    # Graficar el mapa con colores
    filtered_geo_data.plot(ax=ax, color=filtered_geo_data['color'], edgecolor='black')
    ax.set_title(f'Resultados Electorales para {selected_header}', fontsize=16)
    ax.set_xlabel('Longitud', fontsize=12)
    ax.set_ylabel('Latitud', fontsize=12)
    
    st.pyplot(fig)

# Mostrar todos los circuitos con sus resultados
if st.sidebar.checkbox('Ver Todos los Circuitos con Sus Resultados'):
    fig, ax = plt.subplots(figsize=(10, 10))
    divider = make_axes_locatable(ax)
    cax = divider.append_axes("right", size="5%", pad=0.1)
    
    # Graficar todos los circuitos
    resultados_agrupados.plot(ax=ax, color=resultados_agrupados['color'], edgecolor='black')
    ax.set_title('Todos los Circuitos Electorales con Resultados', fontsize=16)
    ax.set_xlabel('Longitud', fontsize=12)
    ax.set_ylabel('Latitud', fontsize=12)
    
    st.pyplot(fig)
