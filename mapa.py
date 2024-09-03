import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
import requests
import zipfile
import io
import streamlit as st

# Descargar y cargar los datos
@st.cache_data
def cargar_datos():
    # Descargar y leer archivo CSV de resultados electorales
    zip_url_resultados = 'https://www.argentina.gob.ar/sites/default/files/2023_generales_1.zip'
    response = requests.get(zip_url_resultados)
    zip_file_resultados = zipfile.ZipFile(io.BytesIO(response.content))
    archivo_csv = '2023_Generales/ResultadoElectorales_2023_Generales.csv'
    with zip_file_resultados.open(archivo_csv) as csv_file:
        csv_df = pd.read_csv(csv_file)

    # Descargar y leer archivo GeoJSON de circuitos electorales
    zip_url_circ = 'https://catalogo.datos.gba.gob.ar/dataset/4fe68b69-c788-4c06-ac67-26e4ebc7416b/resource/37bd466c-4a80-4e2e-be11-a68cfe60aa1e/download/circuitos-electorales.zip'
    response = requests.get(zip_url_circ)
    zip_file_circ = zipfile.ZipFile(io.BytesIO(response.content))
    archivo_geojson = 'circuitos-electorales.geojson'
    with zip_file_circ.open(archivo_geojson) as geojson_file:
        geo_df = gpd.read_file(geojson_file)

    return csv_df, geo_df

csv_df, geo_df = cargar_datos()

# Crear selección de cabecera, cargo y circuito
cabecera = st.selectbox('Cabecera:', ['Todas'] + list(geo_df['cabecera'].unique()))
cargo_nombre = st.selectbox('Cargo:', csv_df['cargo_nombre'].unique())

# Función para actualizar el mapa y mostrar la tabla de porcentajes
def actualizar_mapa(cabecera, cargo_nombre):
    # Filtrar GeoDataFrame por cabecera seleccionada
    if cabecera != 'Todas':
        geo_lp_df = geo_df[geo_df['cabecera'] == cabecera]
    else:
        geo_lp_df = geo_df

    # Filtrar DataFrame CSV por cargo seleccionado
    df_filtered = csv_df[csv_df['cargo_nombre'] == cargo_nombre]

    # Agrupar por 'circuito_id' y 'agrupacion_nombre' y sumar 'votos_cantidad'
    df_summed = df_filtered.groupby(['circuito_id', 'agrupacion_nombre'], as_index=False)['votos_cantidad'].sum()

    # Eliminar ceros a la izquierda en la columna 'circuito_id'
    df_summed['circuito_id'] = df_summed['circuito_id'].astype(str).str.lstrip('0')

    # Filtrar para que solo se incluyan los circuitos de las cabeceras seleccionadas
    df_summed = df_summed[df_summed['circuito_id'].isin(geo_lp_df['circuito'])]

    # Calcular el total de votos por circuito
    df_totals = df_summed.groupby('circuito_id')['votos_cantidad'].sum().reset_index().rename(columns={'votos_cantidad': 'total_votos'})

    # Unir el total de votos a los datos agrupados por circuito y agrupación
    df_summed = pd.merge(df_summed, df_totals, on='circuito_id')

    # Calcular el porcentaje de votos por agrupación en cada circuito
    df_summed['porcentaje_votos'] = (df_summed['votos_cantidad'] / df_summed['total_votos']) * 100

    # Realizar la unión de los DataFrames
    df_merged = pd.merge(df_summed, geo_lp_df, left_on='circuito_id', right_on='circuito', how='inner')

    # Asegúrate de que 'geometry' sea del tipo geométrico adecuado para geopandas
    geo_merged_df = gpd.GeoDataFrame(df_merged, geometry='geometry')

    # Configura el sistema de coordenadas (CRS) si es necesario
    geo_merged_df.set_crs(epsg=4326, inplace=True)

    # Crear una columna para el color según la agrupación con más votos
    def get_color(agrupacion):
        if agrupacion == 'LA LIBERTAD AVANZA':
            return 'violet'
        elif agrupacion == 'JUNTOS POR EL CAMBIO':
            return 'yellow'
        elif agrupacion == 'UNION POR LA PATRIA':
            return 'blue'
        else:
            return 'grey'

    # Agrupar por 'circuito_id' para obtener la agrupación con más votos en cada circuito
    dominant_party = df_summed.loc[df_summed.groupby('circuito_id')['votos_cantidad'].idxmax()]

    # Crear una columna de colores en el GeoDataFrame
    geo_merged_df = geo_merged_df.merge(dominant_party[['circuito_id', 'agrupacion_nombre']], left_on='circuito', right_on='circuito_id', suffixes=('', '_dominant'))
    geo_merged_df['color'] = geo_merged_df['agrupacion_nombre_dominant'].apply(get_color)

    # Crear el mapa con la columna de colores
    fig, ax = plt.subplots(figsize=(15, 15))
    geo_merged_df.plot(ax=ax, edgecolor='k', color=geo_merged_df['color'])
    ax.set_title(f'Mapa de Circuitos en {cabecera} ({cargo_nombre})')
    st.pyplot(fig)

    # Crear una tabla con los porcentajes de votos por circuito
    df_table = df_summed.pivot_table(index='circuito_id', columns='agrupacion_nombre', values='porcentaje_votos', fill_value=0)
    df_table = df_table.round(2)  # Redondear a 2 decimales
    st.dataframe(df_table)

    # Calcular el total de votos por agrupación para la cabecera
    df_total_agrupacion = df_summed.groupby('agrupacion_nombre')['votos_cantidad'].sum()
    total_votos_cabecera = df_total_agrupacion.sum()
    df_total_agrupacion_percent = (df_total_agrupacion / total_votos_cabecera) * 100

    # Mostrar la tabla de porcentajes totales por agrupación
    st.write(f"Porcentajes totales de votos por agrupación en {cabecera} ({cargo_nombre}):")
    st.dataframe(df_total_agrupacion_percent.round(2).to_frame(name='% de Votos'))

# Llamar a la función para actualizar el mapa y mostrar la tabla
actualizar_mapa(cabecera, cargo_nombre)
