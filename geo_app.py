import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import requests
from sqlalchemy import create_engine

# --- CONFIGURACIÓN DE PÁGINA STREAMLIT ---
st.set_page_config(
    page_title="Dashboard Socioeconómico de Europa",
    page_icon="🇪🇺",
    layout="wide"
)

# --- 1. CONEXIÓN A POSTGRESQL Y CARGA DE DATOS ---
# Si se ejecuta en Streamlit Cloud lee los Secrets, si no usa la URL directa de Render
if "postgres" in st.secrets:
    CADENA_CONEXION_PG = st.secrets["postgres"]["db_url"]
else:
    CADENA_CONEXION_PG = "postgresql://etl_user:1cJXGkjERZZ7cBUszrr3PJ2ryUu1nTNT@dpg-dagi338u01pc73fvq5e0-a.frankfurt-postgres.render.com/etl_database_ir8u?sslmode=require"

@st.cache_data(ttl=3600)
def cargar_datos_desde_db():
    engine = create_engine(
        CADENA_CONEXION_PG,
        connect_args={"sslmode": "require"}
    )
    df = pd.read_sql("SELECT * FROM tb_indicadores_europa;", engine)
    
    # URL GeoJSON oficial de Europa
    url_geojson = "https://raw.githubusercontent.com/leakyMirror/map-of-europe/master/GeoJSON/europe.geojson"
    geojson = requests.get(url_geojson).json()
    
    return df, geojson

try:
    df_indicadores, geojson_europa = cargar_datos_desde_db()
except Exception as e:
    st.error(f"⚠️ Error de conexión a PostgreSQL: {e}")
    st.stop()

# --- 2. PREPARACIÓN Y CÁLCULOS DERIVADOS ---
df_geo = df_indicadores.copy()
df_geo['pais_clean'] = df_geo['pais'].astype(str).str.strip()

# Transformaciones logarítmicas para escalado correcto
df_geo['densidad_log'] = np.log10(df_geo['densidad_poblacional'])

# Indicadores derivados avanzados
df_geo['eficiencia_espacial'] = df_geo['pib_per_capita'] / df_geo['densidad_poblacional']
df_geo['pib_por_km2'] = (df_geo['pib_miles_millones_eur'] * 1e9) / df_geo['superficie_km2']

df_geo['eficiencia_log'] = np.log10(df_geo['eficiencia_espacial'])
df_geo['intensidad_log'] = np.log10(df_geo['pib_por_km2'])

# Formatters para Tooltips
df_geo['pib_pc_fmt'] = df_geo['pib_per_capita'].apply(lambda x: f"{x:,.2f} €")
df_geo['densidad_fmt'] = df_geo['densidad_poblacional'].apply(lambda x: f"{x:,.2f} hab/km²")
df_geo['eficiencia_fmt'] = df_geo['eficiencia_espacial'].apply(lambda x: f"{x:,.2f}")
df_geo['intensidad_fmt'] = df_geo['pib_por_km2'].apply(lambda x: f"{x:,.0f} €")

# --- 3. DICCIONARIO Y NORMALIZACIÓN TOPOLÓGICA INFALIBLE ---
MAPEO_NORMALIZADO = {
    'bosnia y herzegovina': 'Bosnia and Herzegovina',
    'bosnia and herzegovina': 'Bosnia and Herzegovina',
    'bosnia and herz.': 'Bosnia and Herzegovina',
    'bosnia herzegovina': 'Bosnia and Herzegovina',
    'bosnia & herzegovina': 'Bosnia and Herzegovina',
    'bosnia': 'Bosnia and Herzegovina',
    'north macedonia': 'Macedonia',
    'macedonia del norte': 'Macedonia',
    'macedonia': 'Macedonia',
    'moldavia': 'Moldova',
    'moldova': 'Moldova',
    'república checa': 'Czech Republic',
    'republica checa': 'Czech Republic',
    'czechia': 'Czech Republic',
    'czech republic': 'Czech Republic',
    'serbia': 'Republic of Serbia',
    'republic of serbia': 'Republic of Serbia'
}

df_geo['pais_key'] = df_geo['pais_clean'].str.lower()
df_geo['pais_mapa'] = df_geo['pais_key'].map(MAPEO_NORMALIZADO).fillna(df_geo['pais_clean'])

# Normalización interna del GeoJSON
for feature in geojson_europa['features']:
    props = feature['properties']
    props_str = str(props).lower()
    
    if 'bosnia' in props_str or 'herz' in props_str or 'bih' in props_str:
        props['NAME'] = 'Bosnia and Herzegovina'
    elif 'macedonia' in props_str or 'mkd' in props_str:
        props['NAME'] = 'Macedonia'
    elif 'moldova' in props_str or 'mda' in props_str:
        props['NAME'] = 'Moldova'
    elif 'serbia' in props_str or 'srb' in props_str:
        props['NAME'] = 'Republic of Serbia'
    elif 'czech' in props_str or 'cze' in props_str:
        props['NAME'] = 'Czech Republic'

# --- 4. CONFIGURACIÓN DE CATEGORÍAS, DESCRIPCIONES E INTERPRETACIONES ---
DESCRIPCION_CATEGORIAS = {
    "📐 Categoría Territorial": "En esta sección se representan las variables físicas y demográficas base. Permite comparar la escala física absoluta y la masa poblacional de las naciones europeas sin ponderaciones económicas.",
    "💶 Categoría Económica": "En esta sección se agrupan los indicadores macroeconómicos volumétricos finales, reflejando el tamaño nominal de las economías continentales antes de ajustar por volumen poblacional o extensión de suelo.",
    "📊 Indicadores Base": "Esta sección analiza los coeficientes socioeconómicos estándar de densidad demográfica e ingreso por habitante, clave para evaluar la distribución de la población y el nivel de desarrollo medio.",
    "💡 Indicadores Derivados": "En esta sección se presentan modelos analíticos complejos en escala logarítmica (log₁₀). Permiten identificar fricciones territoriales, saturación urbana y eficiencia en el uso económico de la superficie."
}

DICCIONARIO_CATEGORIAS = {
    "📐 Categoría Territorial": {
        "Población": {
            "columna": "poblacion",
            "escala": "Blues",
            "titulo": "Población Total por País",
            "leyenda": "Habitantes",
            "interpretacion": "Muestra una marcada asimetría demográfica continental. Países del eje central y occidental (Alemania, Francia, Italia) actúan como núcleos de volumen, mientras que los estados nórdicos y bálticos registran volúmenes poblacionales notablemente más reducidos."
        },
        "Superficie (km²)": {
            "columna": "superficie_km2",
            "escala": "Greens",
            "titulo": "Superficie Territorial (km²)",
            "leyenda": "Superficie km²",
            "interpretacion": "Permite contrastar la extensión física real de los países. Refleja cómo la disponibilidad espacial condiciona el desarrollo de infraestructuras y la densidad habitacional de cada estado."
        }
    },
    "💶 Categoría Económica": {
        "PIB (€ miles de millones)": {
            "columna": "pib_miles_millones_eur",
            "escala": "Purples",
            "titulo": "Producto Interior Bruto (€ en miles de millones)",
            "leyenda": "PIB (€ M)",
            "interpretacion": "Ilustra la concentración de riqueza nominal en las grandes potencias industriales (Alemania, Reino Unido, Francia). Destaca la brecha entre las economías consolidadas de Europa occidental y los mercados del sudeste europeo."
        }
    },
    "📊 Indicadores Base": {
        "Densidad Poblacional (Ajustado Log)": {
            "columna": "densidad_log",
            "escala": "YlOrRd",
            "titulo": "Densidad de Población (hab/km² - Escala Logarítmica Ajustada)",
            "leyenda": "Densidad (log₁₀)",
            "interpretacion": "Gracias al escalado logarítmico, se neutraliza el efecto distorsionador de microestados súper densos (Mónaco, Malta). Permite apreciar con claridad el gradiente de asentamiento: alta presión urbana en los Países Bajos y Bélgica frente al patrón disperso de la península escandinava."
        },
        "PIB per Cápita (€)": {
            "columna": "pib_per_capita",
            "escala": "Viridis",
            "titulo": "PIB per Cápita (€)",
            "leyenda": "PIB p.c. (€)",
            "interpretacion": "Representa el nivel de prosperidad económica promedio por habitante. Evidencia la marcada brecha Norte-Sur y Este-Oeste, con focos de alto rendimiento financiero en Luxemburgo, Suiza y los países nórdicos."
        }
    },
    "💡 Indicadores Derivados": {
        "Eficiencia Espacial del Capital (Log)": {
            "columna": "eficiencia_log",
            "escala": "Cividis",
            "titulo": "Eficiencia Espacial del Capital (PIB p.c. / Densidad - Escala Log)",
            "leyenda": "Eficiencia (log₁₀)",
            "interpretacion": "Mide cuánto ingreso por habitante es capaz de generar una nación en relación con su presión demográfica. Los valores más altos identifican territorios donde la población genera elevado valor añadido sin sufrir los costes de la saturación o la congestión urbana."
        },
        "Intensidad Económica Territorial (Log)": {
            "columna": "intensidad_log",
            "escala": "Magma",
            "titulo": "Intensidad Económica Territorial (€ PIB por km² - Escala Log)",
            "leyenda": "PIB / km² (€ log₁₀)",
            "interpretacion": "Cuantifica la densidad de producción de riqueza por kilómetro cuadrado. Revela el grado de rendimiento y aprovechamiento productivo del suelo, destacando la alta concentración económica en el corazón industrial de Europa central."
        }
    }
}

# --- 5. INTERFAZ Y RENDERIZADO EN STREAMLIT ---
st.title("🇪🇺 Dashboard Socioeconómico de Europa")
st.markdown("Análisis geoespacial e indicadores socioeconómicos consolidados para 44 países europeos.")

# Selectores jerárquicos organizados por categorías
col_cat, col_ind = st.columns(2)

with col_cat:
    categoria_seleccionada = st.selectbox(
        "1. Selecciona la Categoría de Análisis:",
        list(DICCIONARIO_CATEGORIAS.keys())
    )

with col_ind:
    indicador_seleccionado = st.selectbox(
        "2. Selecciona el Indicador:",
        list(DICCIONARIO_CATEGORIAS[categoria_seleccionada].keys())
    )

# Texto descriptivo de la sección seleccionada
st.info(f"ℹ️ **Sobre esta sección:** {DESCRIPCION_CATEGORIAS[categoria_seleccionada]}")

# Configuración del indicador elegido
cfg = DICCIONARIO_CATEGORIAS[categoria_seleccionada][indicador_seleccionado]

# Generación del gráfico con Plotly
fig = px.choropleth(
    df_geo,
    geojson=geojson_europa,
    locations='pais_mapa',
    featureidkey='properties.NAME',
    color=cfg['columna'],
    color_continuous_scale=cfg['escala'],
    title=f"<b>Mapa de Europa: {cfg['titulo']}</b>",
    hover_name='pais',
    hover_data={
        cfg['columna']: False,
        'pais_mapa': False,
        'pais_clean': False,
        'pais_key': False,
        'pib_pc_fmt': True,
        'densidad_fmt': True
    },
    labels={
        cfg['columna']: cfg['leyenda'],
        'pib_pc_fmt': 'PIB p.c. (€): ',
        'densidad_fmt': 'Densidad (hab/km²): '
    }
)

fig.update_geos(fitbounds="locations", visible=False, projection_type="natural earth")
fig.update_layout(margin={"r":0, "t":40, "l":0, "b":0}, height=560)

# Renderizar el mapa
st.plotly_chart(fig, use_container_width=True)

# Bloque interactivo de interpretación del mapa
with st.expander("📌 **Interpretación analítica del mapa**", expanded=True):
    st.write(cfg['interpretacion'])
