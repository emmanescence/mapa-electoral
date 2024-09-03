import streamlit as st
import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
import requests
import zipfile
import io

# Descargar y leer el archivo ZIP
@st.cache_data
def descargar_datos():
    zip_url = 'https://www.argentina.gob.ar/sites/default/files/2023_generales_1.zip'
    response = requests.get(zip_url)
    zip_file = zipfile.ZipFile(io.BytesIO(response.content))
    
    archivo_csv = '2023_Generales/ResultadoElectorales_2023_Generales.csv'
    with zip_file.open(archivo_csv) as csv_file:
        csv_df = pd.read_csv(csv_file)
    
    geo_df = gpd.read_file('circuitos-electorales.geojson')
    
    return csv_df, geo_df

# Cargar los datos
csv_df, geo_df = descargar_datos()

# Interfaz de usuario en Streamlit
st.title('Mapa de Resultados Electorales 2023')

cabecera = st.selectbox('Cabecera:', ['Todas'] + list(geo_df['cabecera'].unique()))
cargo_nombre = st.selectbox('Cargo:', csv_df['cargo_nombre'].unique())
circuito = st.selectbox('Circuito:', ['Todos'] + list(geo_df['circuito'].unique()))

# Función para actualizar el mapa y mostrar la tabla
def actualizar_mapa(cabecera, cargo_nombre, circuito):
    if cabecera != 'Todas':
        geo_lp_df = geo_df[geo_df['cabecera'] == cabecera]
    else:
        geo_lp_df = geo_df

    if circuito != 'Todos':
        geo_lp_df = geo_lp_df[geo_lp_df['circuito'] == circuito]

    geo_lp_df['circuito'] = geo_lp_df['circuito'].astype(str).str.lstrip('0')
    
    df_filtered = csv_df[csv_df['cargo_nombre'] == cargo_nombre]
    df_summed = df_filtered.groupby(['circuito_id', 'agrupacion_nombre'], as_index=False)['votos_cantidad'].sum()
    df_summed['circuito_id'] = df_summed['circuito_id'].astype(str).str.lstrip('0')
    df_summed = df_summed[df_summed['circuito_id'].isin(geo_lp_df['circuito'])]

    df_totals = df_summed.groupby('circuito_id')['votos_cantidad'].sum().reset_index().rename(columns={'votos_cantidad': 'total_votos'})
    df_summed = pd.merge(df_summed, df_totals, on='circuito_id')
    df_summed['porcentaje_votos'] = (df_summed['votos_cantidad'] / df_summed['total_votos']) * 100
    
    df_merged = pd.merge(df_summed, geo_lp_df, left_on='circuito_id', right_on='circuito', how='inner')
    geo_merged_df = gpd.GeoDataFrame(df_merged, geometry='geometry')
    geo_merged_df.set_crs(epsg=4326, inplace=True)

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

    fig, ax = plt.subplots(figsize=(15, 15))
    geo_merged_df.plot(ax=ax, edgecolor='k', color=geo_merged_df['color'])
    ax.set_title(f'Mapa de Circuitos en {cabecera} ({cargo_nombre}) - {circuito if circuito != "Todos" else "Todos los Circuitos"}')
    st.pyplot(fig)

    df_table = df_summed.pivot_table(index='circuito_id', columns='agrupacion_nombre', values='porcentaje_votos', fill_value=0)
    df_table = df_table.round(2)
    st.write(df_table)

    df_total_agrupacion = df_summed.groupby('agrupacion_nombre')['votos_cantidad'].sum()
    total_votos_cabecera = df_total_agrupacion.sum()
    df_total_agrupacion_percent = (df_total_agrupacion / total_votos_cabecera) * 100

    st.write(f"Porcentajes totales de votos por agrupación en {cabecera} ({cargo_nombre}):")
    st.write(df_total_agrupacion_percent.round(2).to_frame(name='% de Votos'))

# Llamar la función para actualizar el mapa con los valores seleccionados
if st.button('Actualizar Mapa'):
    actualizar_mapa(cabecera, cargo_nombre, circuito)

