import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st
import requests
import zipfile
import io

# URL del archivo comprimido
zip_url_resultados = 'https://www.argentina.gob.ar/sites/default/files/2023_generales_1.zip'

# Descargar el archivo ZIP
response = requests.get(zip_url_resultados)
zip_file_resultados = zipfile.ZipFile(io.BytesIO(response.content))

# Listar los archivos dentro del ZIP
archivo_csv = '2023_Generales/ResultadoElectorales_2023_Generales.csv'

# Leer el archivo CSV extraído, especificando tipos de datos y sin procesar en trozos
with zip_file_resultados.open(archivo_csv) as csv_file:
    csv_df = pd.read_csv(csv_file, low_memory=False, dtype={'circuito_id': str, 'votos_cantidad': float})

# Cargar el archivo GeoJSON
zip_url_circ = 'https://catalogo.datos.gba.gob.ar/dataset/4fe68b69-c788-4c06-ac67-26e4ebc7416b/resource/37bd466c-4a80-4e2e-be11-a68cfe60aa1e/download/circuitos-electorales.zip'

# Descargar el archivo ZIP
response = requests.get(zip_url_circ)
zip_file_circ = zipfile.ZipFile(io.BytesIO(response.content))

# Nombre del archivo GeoJSON dentro del ZIP
archivo_geojson = 'circuitos-electorales.geojson'

# Leer el archivo GeoJSON extraído
with zip_file_circ.open(archivo_geojson) as geojson_file:
    geo_df = gpd.read_file(geojson_file)

# Mostrar las primeras filas del GeoDataFrame en Streamlit
st.write("Primeras filas del GeoDataFrame:")
st.write(geo_df.head())

# Crear widgets interactivos
cabecera_options = ['Todas'] + list(geo_df['cabecera'].unique())
cargo_options = csv_df['cargo_nombre'].unique()
circuito_options = ['Todos'] + list(geo_df['circuito'].unique())

cabecera = st.selectbox('Cabecera:', cabecera_options, index=0)
cargo_nombre = st.selectbox('Cargo:', cargo_options)
circuito = st.selectbox('Circuito:', circuito_options, index=0)

def actualizar_mapa(cabecera, cargo_nombre, circuito):
    # Filtrar GeoDataFrame
    geo_lp_df = geo_df if cabecera == 'Todas' else geo_df[geo_df['cabecera'] == cabecera]
    geo_lp_df = geo_lp_df[geo_lp_df['circuito'] == circuito] if circuito != 'Todos' else geo_lp_df

    # Filtrar datos CSV
    df_filtered = csv_df[csv_df['cargo_nombre'] == cargo_nombre]
    df_summed = df_filtered.groupby(['circuito_id', 'agrupacion_nombre'], as_index=False)['votos_cantidad'].sum()
    df_summed['circuito_id'] = df_summed['circuito_id'].astype(str).str.lstrip('0')
    df_summed = df_summed[df_summed['circuito_id'].isin(geo_lp_df['circuito'])]

    # Total de votos por circuito
    df_totals = df_summed.groupby('circuito_id')['votos_cantidad'].sum().reset_index().rename(columns={'votos_cantidad': 'total_votos'})
    df_summed = pd.merge(df_summed, df_totals, on='circuito_id')
    df_summed['porcentaje_votos'] = (df_summed['votos_cantidad'] / df_summed['total_votos']) * 100

    # Unir con GeoDataFrame
    df_merged = pd.merge(df_summed, geo_lp_df, left_on='circuito_id', right_on='circuito', how='inner')
    geo_merged_df = gpd.GeoDataFrame(df_merged, geometry='geometry')
    geo_merged_df.set_crs(epsg=4326, inplace=True)

    # Colores para el mapa
    def get_color(agrupacion):
        if agrupacion == 'LA LIBERTAD AVANZA':
            return 'violet'
        elif agrupacion == 'JUNTOS POR EL CAMBIO':
            return 'yellow'
        elif agrupacion == 'UNION POR LA PATRIA':
            return 'blue'
        else:
            return 'grey'

    dominant_party = df_summed.loc[df_summed.groupby('circuito_id')['votos_cantidad'].idxmax()]
    geo_merged_df = geo_merged_df.merge(dominant_party[['circuito_id', 'agrupacion_nombre']], left_on='circuito', right_on='circuito_id', suffixes=('', '_dominant'))
    geo_merged_df['color'] = geo_merged_df['agrupacion_nombre_dominant'].apply(get_color)

    # Crear el mapa
    fig, ax = plt.subplots(figsize=(15, 15))
    geo_merged_df.plot(ax=ax, edgecolor='k', color=geo_merged_df['color'])
    ax.set_title(f'Mapa de Circuitos en {cabecera} ({cargo_nombre}) - {circuito if circuito != "Todos" else "Todos los Circuitos"}')
    st.pyplot(fig)

    # Tabla de porcentajes
    df_table = df_summed.pivot_table(index='circuito_id', columns='agrupacion_nombre', values='porcentaje_votos', fill_value=0)
    df_table = df_table.round(2)
    st.write("Porcentajes de votos por circuito:")
    st.write(df_table)

    # Tabla de porcentajes totales
    df_total_agrupacion = df_summed.groupby('agrupacion_nombre')['votos_cantidad'].sum()
    total_votos_cabecera = df_total_agrupacion.sum()
    df_total_agrupacion_percent = (df_total_agrupacion / total_votos_cabecera) * 100
    st.write(f"Porcentajes totales de votos por agrupación en {cabecera} ({cargo_nombre}):")
    st.write(df_total_agrupacion_percent.round(2).to_frame(name='% de Votos'))

# Ejecutar la función para actualizar el mapa con los parámetros seleccionados
if st.button('Actualizar Mapa'):
    actualizar_mapa(cabecera, cargo_nombre, circuito)
