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
    
    # GeoJSON oficial de países del mundo (GeoJSON de alta compatibilidad con ID de 3 letras)
    url_geojson = "https://raw.githubusercontent.com/python-visualization/folium-example-data/main/world_countries.json"
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

# Transformaciones logarítmicas
df_geo['densidad_log'] = np.log10(df_geo['densidad_poblacional'])

# Indicadores derivados
df_geo['eficiencia_espacial'] = df_geo['pib_per_capita'] / df_geo['densidad_poblacional']
df_geo['pib_por_km2'] = (df_geo['pib_miles_millones_eur'] * 1e9) / df_geo['superficie_km2']

df_geo['eficiencia_log'] = np.log10(df_geo['eficiencia_espacial'])
df_geo['intensidad_log'] = np.log10(df_geo['pib_por_km2'])

# Formatters para Tooltips
df_geo['pib_pc_fmt'] = df_geo['pib_per_capita'].apply(lambda x: f"{x:,.2f} €")
df_geo['densidad_fmt'] = df_geo['densidad_poblacional'].apply(lambda x: f"{x:,.2f} hab/km²")

# --- 3. MAPEADOR DE NOMBRES A ISO3 PARA PLOTLY ---
MAPEO_ISO3 = {
    'albania': 'ALB', 'andorra': 'AND', 'austria': 'AUT', 'belarus': 'BLR',
    'belgium': 'BEL', 'bosnia and herzegovina': 'BIH', 'bulgaria': 'BGR',
    'croatia': 'HRV', 'cyprus': 'CYP', 'czechia': 'CZE', 'czech republic': 'CZE',
    'denmark': 'DNK', 'estonia': 'EST', 'finland': 'FIN', 'france': 'FRA',
    'germany': 'DEU', 'greece': 'GRC', 'hungary': 'HUN', 'iceland': 'ISL',
    'ireland': 'IRL', 'italy': 'ITA', 'latvia': 'LVA', 'liechtenstein': 'LIE',
    'lithuania': 'LTU', 'luxembourg': 'LUX', 'malta': 'MLT', 'moldova': 'MDA',
    'monaco': 'MCO', 'montenegro': 'MNE', 'netherlands': 'NLD', 'north macedonia': 'MKD',
    'norway': 'NOR', 'poland': 'POL', 'portugal': 'PRT', 'romania': 'ROU',
    'san marino': 'SMR', 'serbia': 'SRB', 'slovakia': 'SVK', 'slovenia': 'SVN',
    'spain': 'ESP', 'sweden': 'SWE', 'switzerland': 'CHE', 'ukraine': 'UKR',
    'united kingdom': 'GBR', 'vatican city': 'VAT'
}

df_geo['iso_a3'] = df_geo['pais_clean'].str.lower().map(MAPEO_ISO3)

# --- 4. CONFIGURACIÓN DE CATEGORÍAS Y DESCRIPCIONES ---
DESCRIPCION_CATEGORIAS = {
    "📐 Categoría Territorial": "En esta sección se representan las variables físicas y demográficas base.",
    "💶 Categoría Económica": "En esta sección se agrupan los indicadores macroeconómicos volumétricos finales.",
    "📊 Indicadores Base": "Esta sección analiza los coeficientes socioeconómicos estándar de densidad demográfica e ingreso por habitante.",
    "💡 Indicadores Derivados": "En esta sección se presentan modelos analíticos complejos en escala logarítmica (log₁₀)."
}

DICCIONARIO_CATEGORIAS = {
    "📐 Categoría Territorial": {
        "Población": {
            "columna": "poblacion",
            "escala": "Blues",
            "titulo": "Población Total por País",
            "leyenda": "Habitantes",
            "interpretacion": "Muestra una marcada asimetría demográfica continental. Países del eje central y occidental (Alemania, Francia, Italia) actúan como núcleos de volumen."
        },
        "Superficie (km²)": {
            "columna": "superficie_km2",
            "escala": "Greens",
            "titulo": "Superficie Territorial (km²)",
            "leyenda": "Superficie km²",
            "interpretacion": "Permite contrastar la extensión física real de los países."
        }
    },
    "💶 Categoría Económica": {
        "PIB (€ miles de millones)": {
            "columna": "pib_miles_millones_eur",
            "escala": "Purples",
            "titulo": "Producto Interior Bruto (€ en miles de millones)",
            "leyenda": "PIB (€ M)",
            "interpretacion": "Ilustra la concentración de riqueza nominal en las grandes potencias industriales."
        }
    },
    "📊 Indicadores Base": {
        "Densidad Poblacional (Ajustado Log)": {
            "columna": "densidad_log",
            "escala": "YlOrRd",
            "titulo": "Densidad de Población (hab/km² - Escala Logarítmica)",
            "leyenda": "Densidad (log₁₀)",
            "interpretacion": "Neutraliza el efecto distorsionador de microestados súper densos."
        },
        "PIB per Cápita (€)": {
            "columna": "pib_per_capita",
            "escala": "Viridis",
            "titulo": "PIB per Cápita (€)",
            "leyenda": "PIB p.c. (€)",
            "interpretacion": "Representa el nivel de prosperidad económica promedio por habitante."
        }
    },
    "💡 Indicadores Derivados": {
        "Eficiencia Espacial del Capital (Log)": {
            "columna": "eficiencia_log",
            "escala": "Cividis",
            "titulo": "Eficiencia Espacial del Capital (PIB p.c. / Densidad - Escala Log)",
            "leyenda": "Eficiencia (log₁₀)",
            "interpretacion": "Mide cuánto ingreso por habitante es capaz de generar una nación en relación con su presión demográfica."
        },
        "Intensidad Económica Territorial (Log)": {
            "columna": "intensidad_log",
            "escala": "Magma",
            "titulo": "Intensidad Económica Territorial (€ PIB por km² - Escala Log)",
            "leyenda": "PIB / km² (€ log₁₀)",
            "interpretacion": "Cuantifica la densidad de producción de riqueza por kilómetro cuadrado."
        }
    }
}

# --- 5. INTERFAZ Y RENDERIZADO EN STREAMLIT ---
st.title("🇪🇺 Dashboard Socioeconómico de Europa")
st.markdown("Análisis geoespacial e indicadores socioeconómicos consolidados para 44 países europeos.")

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

st.info(f"ℹ️ **Sobre esta sección:** {DESCRIPCION_CATEGORIAS[categoria_seleccionada]}")

cfg = DICCIONARIO_CATEGORIAS[categoria_seleccionada][indicador_seleccionado]

# GENERACIÓN CON PROYECCIÓN NATIVA DE PLOTLY MEDIANTE ISO-3 (Sin fallos de renderizado)
fig = px.choropleth(
    df_geo,
    locations='iso_a3',
    color=cfg['columna'],
    hover_name='pais',
    color_continuous_scale=cfg['escala'],
    title=f"<b>Mapa de Europa: {cfg['titulo']}</b>",
    scope='europe', # Fuerza la proyección exclusiva en el continente europeo
    hover_data={
        cfg['columna']: False,
        'iso_a3': False,
        'pib_pc_fmt': True,
        'densidad_fmt': True
    },
    labels={
        cfg['columna']: cfg['leyenda'],
        'pib_pc_fmt': 'PIB p.c. (€): ',
        'densidad_fmt': 'Densidad (hab/km²): '
    }
)

fig.update_geos(
    showcountries=True,
    countrycolor="LightGrey",
    showsubunits=True,
    showframe=False,
    projection_type="natural earth"
)

fig.update_layout(margin={"r":0, "t":40, "l":0, "b":0}, height=580)

st.plotly_chart(fig, use_container_width=True)

with st.expander("📌 **Interpretación analítica del mapa**", expanded=True):
    st.write(cfg['interpretacion'])
