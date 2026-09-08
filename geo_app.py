import streamlit as st
import pandas as pd
import numpy as np
import requests
import json
import plotly.express as px
from sqlalchemy import create_engine

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(
    page_title="Dashboard Geoespacial de Europa",
    page_icon="🇪🇺",
    layout="wide"
)

# 2. PANEL LATERAL (BARRA DE CONEXIÓN BBDD)
st.sidebar.header("🔌 Configuración de Conexión")
db_user = st.sidebar.text_input("Usuario PostgreSQL", value="admin_etl")
db_password = st.sidebar.text_input("Contraseña", value="Password123!", type="password")
db_host = st.sidebar.text_input("Host", value="localhost")
db_port = st.sidebar.text_input("Puerto", value="5433")
db_name = st.sidebar.text_input("Base de Datos", value="db_europa_dw")

# Botón para limpiar la caché y reconectar manualmente
if st.sidebar.button("🔄 Reconectar y Actualizar Datos"):
    st.cache_data.clear()
    st.rerun()

cadena_conexion = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
URL_GEOJSON = "https://raw.githubusercontent.com/leakyMirror/map-of-europe/master/GeoJSON/europe.geojson"

# 3. CARGA DE DATOS SENSIBLE A LA CADENA DE CONEXIÓN
@st.cache_data(ttl=60)
def cargar_y_preparar_datos(connection_string):
    # Definición interna de formateadores para evitar NameError
    fmt_entero = lambda x: f"{x:,.0f}".replace(",", "X").replace(".", ",").replace("X", ".") if pd.notnull(x) else ""
    fmt_decimal = lambda x: f"{x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") if pd.notnull(x) else ""

    engine = create_engine(connection_string)
    df = pd.read_sql("SELECT * FROM tb_indicadores_europa;", engine)
    geojson_europa = requests.get(URL_GEOJSON).json()
    
    # Formateo de columnas para Tooltips
    df['poblacion_fmt'] = df['poblacion'].apply(fmt_entero)
    df['superficie_fmt'] = df['superficie_km2'].apply(fmt_decimal)
    df['pib_fmt'] = df['pib_miles_millones_eur'].apply(fmt_decimal)
    df['densidad_fmt'] = df['densidad_poblacional'].apply(fmt_decimal)
    df['pib_pc_fmt'] = df['pib_per_capita'].apply(fmt_decimal)
    
    # Ajuste logarítmico para densidad
    df['densidad_log'] = np.log10(df['densidad_poblacional'])
    
    # Indicadores Derivados (Fase 4)
    df['eficiencia_espacial'] = df['pib_per_capita'] / df['densidad_poblacional']
    df['pib_por_km2'] = (df['pib_miles_millones_eur'] * 1e9) / df['superficie_km2']
    df['eficiencia_log'] = np.log10(df['eficiencia_espacial'])
    df['intensidad_log'] = np.log10(df['pib_por_km2'])
    
    df['eficiencia_fmt'] = df['eficiencia_espacial'].apply(fmt_decimal)
    df['intensidad_fmt'] = df['pib_por_km2'].apply(fmt_entero)
    
    # Mapeo territorial
    MAPEO_NORMALIZADO = {
        'serbia': 'Republic of Serbia',
        'bosnia and herzegovina': 'Bosnia and Herzegovina',
        'czechia': 'Czech Republic',
        'north macedonia': 'Macedonia',
        'republic of macedonia': 'Macedonia',
        'moldova': 'Moldova', 
        'republic of moldova': 'Moldova',
        'vatican city': 'Vatican',
        'united kingdom': 'United Kingdom',
        'switzerland': 'Switzerland'
    }
    
    df['pais_norm_aux'] = df['pais'].astype(str).str.lower().str.strip()
    df['pais_mapa'] = df['pais_norm_aux'].map(MAPEO_NORMALIZADO).fillna(df['pais'])
    
    for feature in geojson_europa['features']:
        props = feature['properties']
        nombre_geo = props.get('NAME') or props.get('NAME_LONG') or props.get('ADMIN')
        if nombre_geo in ['Republic of Serbia', 'Serbia']:
            props['NAME'] = 'Republic of Serbia'
        elif nombre_geo in ['Bosnia and Herzegovina', 'Bosnia and Herz.']:
            props['NAME'] = 'Bosnia and Herzegovina'
        elif nombre_geo in ['Macedonia', 'North Macedonia']:
            props['NAME'] = 'Macedonia'
        elif nombre_geo in ['Moldova', 'Republic of Moldova']:
            props['NAME'] = 'Moldova'
            
    return df, geojson_europa

try:
    df_geo, geojson_data = cargar_y_preparar_datos(cadena_conexion)
except Exception as e:
    st.error("❌ Error de Autenticación o Conexión con PostgreSQL:")
    st.info("Revisa la contraseña introducida en la barra lateral (Sidebar) o verifica el valor configurado en tu docker-compose.yml.")
    st.code(str(e))
    st.stop()

# 4. FUNCIÓN GENERADORA DE MAPAS
def generar_mapa(df, geojson, col_color, titulo, escala, leyenda, fmt_col=None, fmt_label=None):
    hover_dict = {
        col_color: False, 'pais_mapa': False, 'pais_norm_aux': False,
        'poblacion_fmt': True, 'superficie_fmt': True, 'pib_fmt': True,
        'densidad_fmt': True, 'pib_pc_fmt': True
    }
    labels_dict = {
        col_color: leyenda, 'poblacion_fmt': 'Población: ',
        'superficie_fmt': 'Superficie (km²): ', 'pib_fmt': 'PIB (€ B): ',
        'densidad_fmt': 'Densidad (hab/km²): ', 'pib_pc_fmt': 'PIB p.c. (€): '
    }
    
    if fmt_col and fmt_label:
        hover_dict[fmt_col] = True
        labels_dict[fmt_col] = fmt_label

    fig = px.choropleth(
        df,
        geojson=geojson,
        locations='pais_mapa',
        featureidkey='properties.NAME',
        color=col_color,
        color_continuous_scale=escala,
        title=f"<b>{titulo}</b>",
        hover_name='pais',
        hover_data=hover_dict,
        labels=labels_dict
    )
    
    fig.update_geos(fitbounds="locations", visible=False, projection_type="natural earth")
    fig.update_layout(margin={"r":0, "t":40, "l":0, "b":0}, height=550)
    return fig

# 5. ENCABEZADO Y PESTAÑAS
st.title("🇪🇺 Suite Geoespacial de Indicadores de Europa")
st.markdown("Visualización e inteligencia territorial sobre **44 países europeos** procesados mediante el pipeline ETL.")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Países Analizados", len(df_geo))
col2.metric("Población Total", f"{df_geo['poblacion'].sum():,.0f}".replace(",", "."))
col3.metric("PIB Continental", f"{df_geo['pib_miles_millones_eur'].sum():,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") + " B€")
col4.metric("Estado PostgreSQL", "Conectado (Puerto 5433)")

st.divider()

# CATEGORÍAS ORDENADAS
tab_geo, tab_econ, tab_orig, tab_deriv = st.tabs([
    "📍 1. Sección Geográfica y Demográfica", 
    "💶 2. Sección Económica", 
    "📊 3. Indicadores Base del Proyecto", 
    "🚀 4. Indicadores Derivados (Fase 4)"
])

# --- 1. SECCIÓN GEOGRÁFICA Y DEMOGRÁFICA ---
with tab_geo:
    st.subheader("Dimensión Territorial y Demográfica")
    opcion_geo = st.radio(
        "Seleccione la métrica geográfica / demográfica:",
        ["Superficie Territorial (km²)", "Población Total", "Densidad Poblacional (Escala Ajustada Log10)"],
        horizontal=True
    )
    
    if opcion_geo == "Superficie Territorial (km²)":
        fig = generar_mapa(df_geo, geojson_data, 'superficie_km2', 'Superficie Territorial por País (km²)', 'Greens', 'Superficie (km²)')
    elif opcion_geo == "Población Total":
        fig = generar_mapa(df_geo, geojson_data, 'poblacion', 'Población Total por País', 'YlGnBu', 'Población total')
    else:
        fig = generar_mapa(df_geo, geojson_data, 'densidad_log', 'Densidad Poblacional (hab/km² - Escala Logarítmica)', 'Plasma', 'Densidad poblacional (log₁₀)')
    
    st.plotly_chart(fig, use_container_width=True)

# --- 2. SECCIÓN ECONÓMICA ---
with tab_econ:
    st.subheader("Dimensión Económica y Riqueza")
    opcion_econ = st.radio(
        "Seleccione el indicador económico:",
        ["PIB Total (€ en miles de millones)", "PIB per Cápita (€/hab)"],
        horizontal=True
    )
    
    if opcion_econ == "PIB Total (€ en miles de millones)":
        fig = generar_mapa(df_geo, geojson_data, 'pib_miles_millones_eur', 'PIB Total (€ en miles de millones)', 'Blues', 'PIB en miles de millones de €')
    else:
        fig = generar_mapa(df_geo, geojson_data, 'pib_per_capita', 'PIB per Cápita en Europa (€/hab)', 'Viridis', 'PIB per cápita (€)')
        
    st.plotly_chart(fig, use_container_width=True)

# --- 3. INDICADORES BASE DEL PROYECTO ---
with tab_orig:
    st.subheader("Colección Completa de Indicadores Base")
    st.markdown("Visualice cualquiera de las 5 variables originales procesadas en la primera fase del pipeline ETL.")
    
    opcion_orig = st.selectbox(
        "Seleccione el indicador base a desplegar:",
        ["PIB per Cápita (€/hab)", "Densidad Poblacional (Escala Log10)", "PIB Total (€ B)", "Población Total", "Superficie (km²)"]
    )
    
    mapa_dict = {
        "PIB per Cápita (€/hab)": ('pib_per_capita', 'PIB per Cápita (€/hab)', 'Viridis', 'PIB per cápita (€)'),
        "Densidad Poblacional (Escala Log10)": ('densidad_log', 'Densidad Poblacional (Escala Log10)', 'Plasma', 'Densidad poblacional (log₁₀)'),
        "PIB Total (€ B)": ('pib_miles_millones_eur', 'PIB Total en miles de millones de €', 'Blues', 'PIB en miles de millones de €'),
        "Población Total": ('poblacion', 'Población Total', 'YlGnBu', 'Población total'),
        "Superficie (km²)": ('superficie_km2', 'Superficie Territorial (km²)', 'Greens', 'Superficie (km²)')
    }
    
    col_c, tit, esc, ley = mapa_dict[opcion_orig]
    fig = generar_mapa(df_geo, geojson_data, col_c, tit, esc, ley)
    st.plotly_chart(fig, use_container_width=True)

# --- 4. INDICADORES DERIVADOS (FASE 4) ---
with tab_deriv:
    st.subheader("Innovación e Indicadores Derivados Espaciales")
    st.info("Métricas avanzadas introducidas para analizar la eficiencia del capital respecto al suelo y la población.")
    
    opcion_deriv = st.radio(
        "Seleccione el indicador derivado:",
        ["Eficiencia Espacial del Capital", "Intensidad Económica Territorial"],
        horizontal=True
    )
    
    if opcion_deriv == "Eficiencia Espacial del Capital":
        st.markdown("**Eficiencia Espacial del Capital:** Mide la relación entre la riqueza por habitante y la concentración demográfica ($\text{PIB p.c.} / \text{Densidad}$).")
        fig = generar_mapa(
            df_geo, geojson_data, 'eficiencia_log', 'Eficiencia Espacial del Capital (Escala Logarítmica)', 
            'Cividis', 'Eficiencia espacial (log₁₀)', fmt_col='eficiencia_fmt', fmt_label='Eficiencia Espacial: '
        )
    else:
        st.markdown("**Intensidad Económica Territorial:** Mide la concentración de masa monetaria por kilómetro cuadrado de superficie ($\text{PIB Total} / \text{Superficie}$).")
        fig = generar_mapa(
            df_geo, geojson_data, 'intensidad_log', 'Intensidad Económica Territorial (€ PIB por km² - Escala Logarítmica)', 
            'Magma', 'PIB por km² (€, log₁₀)', fmt_col='intensidad_fmt', fmt_label='PIB / km² (€): '
        )
        
    st.plotly_chart(fig, use_container_width=True)