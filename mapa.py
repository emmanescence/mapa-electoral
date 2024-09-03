import streamlit as st
import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
import ipywidgets as widgets
from IPython.display import display, HTML
import requests
import zipfile
import io

# URL del archivo comprimido
zip_url = 'https://www.argentina.gob.ar/sites/default/files/2023_generales_1.zip'

# Descargar el archivo ZIP
response = requests.get(zip_url)
zip_file = zipfile.ZipFile(io.BytesIO(response.content))

# Listar los archivos dentro del ZIP
zip_file.namelist()

archivo_csv = '2023_Generales/ResultadoElectorales_2023_Generales.csv'

# Leer el archivo CSV extraído
with zip_file.open(archivo_csv) as csv_file:
    csv_df = pd.read_csv(csv_file)


# Cargar el archivo GeoJSON y CSV
geo_df = gpd.read_file('circuitos-electorales.geojson')
#csv_df = pd.read_csv('/content/drive/MyDrive/BASES/ResultadoElectorales_2023_Generales.csv')

# Crear widgets interactivos
cabecera_widget = widgets.Dropdown(
    options=['Todas'] + list(geo_df['cabecera'].unique()),
    description='Cabecera:',
    value='Todas'
)

cargo_nombre_widget = widgets.Dropdown(
    options=csv_df['cargo_nombre'].unique(),
    description='Cargo:',
    value='PRESIDENTE Y VICE'
)

circuito_widget = widgets.Dropdown(
    options=['Todos'] + list(geo_df['circuito'].unique()),
    description='Circuito:',
    value='Todos'
)

# Función que actualiza el mapa y muestra la tabla de porcentajes
def actualizar_mapa(cabecera, cargo_nombre, circuito):
    # Si se selecciona "Todas", no filtrar por cabecera; de lo contrario, filtrar por cabecera
    if cabecera != 'Todas':
        geo_lp_df = geo_df[geo_df['cabecera'] == cabecera]
    else:
        geo_lp_df = geo_df

    # Si se selecciona un circuito específico, filtrar solo ese circuito
    if circuito != 'Todos':
        geo_lp_df = geo_lp_df[geo_lp_df['circuito'] == circuito]

    # Eliminar ceros a la izquierda en la columna 'circuito'
    geo_lp_df['circuito'] = geo_lp_df['circuito'].astype(str).str.lstrip('0')

    # Filtrar por el valor específico en la columna 'cargo_nombre'
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
    ax.set_title(f'Mapa de Circuitos en {cabecera} ({cargo_nombre}) - {circuito if circuito != "Todos" else "Todos los Circuitos"}')
    plt.show()

    # Crear una tabla con los porcentajes de votos por circuito solo para los circuitos de la cabecera seleccionada
    df_table = df_summed.pivot_table(index='circuito_id', columns='agrupacion_nombre', values='porcentaje_votos', fill_value=0)
    df_table = df_table.round(2)  # Redondear a 2 decimales
    display(HTML(df_table.to_html()))  # Mostrar la tabla en el notebook

    # Calcular el total de votos por agrupación para la cabecera
    df_total_agrupacion = df_summed.groupby('agrupacion_nombre')['votos_cantidad'].sum()
    total_votos_cabecera = df_total_agrupacion.sum()
    df_total_agrupacion_percent = (df_total_agrupacion / total_votos_cabecera) * 100

    # Mostrar la tabla de porcentajes totales por agrupación
    print(f"Porcentajes totales de votos por agrupación en {cabecera} ({cargo_nombre}):")
    display(HTML(df_total_agrupacion_percent.round(2).to_frame(name='% de Votos').to_html()))

# Crear una función para mostrar los widgets y actualizar el mapa
def mostrar_interfaz():
    ui = widgets.VBox([cabecera_widget, cargo_nombre_widget, circuito_widget])
    out = widgets.interactive_output(actualizar_mapa, {'cabecera': cabecera_widget, 'cargo_nombre': cargo_nombre_widget, 'circuito': circuito_widget})
    display(ui, out)

# Mostrar la interfaz
mostrar_interfaz()
