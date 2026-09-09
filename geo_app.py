import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import unicodedata
from sqlalchemy import create_engine, text

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
    with engine.connect() as conn:
        df = pd.read_sql_query(text("SELECT * FROM tb_indicadores_europa;"), conn)
    return df

try:
    df_indicadores = cargar_datos_desde_db()
except Exception as e:
    st.error(f"⚠️ Error de conexión a PostgreSQL: {e}")
    st.stop()

# --- 2. FUNCIONES DE LIMPIEZA Y PREPARACIÓN ---
def normalizar_cadena(texto):
    if pd.isna(texto): return ""
    texto = str(texto).lower().strip()
    return ''.join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')

df_geo = df_indicadores.copy()
df_geo['pais_norm'] = df_geo['pais'].apply(normalizar_cadena)

# Diccionario exhaustivo a códigos ISO Alpha-3 para la cartografía nativa de Plotly
MAPEO_ISO3 = {
    'albania': 'ALB', 'andorra': 'AND', 'austria': 'AUT', 'belarus': 'BLR', 'bielorrusia': 'BLR',
    'belgium': 'BEL', 'belgica': 'BEL', 'bosnia and herzegovina': 'BIH', 'bosnia y herzegovina': 'BIH',
    'bulgaria': 'BGR', 'croatia': 'HRV', 'croacia': 'HRV', 'cyprus': 'CYP', 'chipre': 'CYP',
    'czechia': 'CZE', 'czech republic': 'CZE', 'republica checa': 'CZE', 'denmark': 'DNK', 'dinamarca': 'DNK',
    'estonia': 'EST', 'finland': 'FIN', 'finlandia': 'FIN', 'france': 'FRA', 'francia': 'FRA',
    'germany': 'DEU', 'alemania': 'DEU', 'greece': 'GRC', 'grecia': 'GRC', 'hungary': 'HUN', 'hungria': 'HUN',
    'iceland': 'ISL', 'islandia': 'ISL', 'ireland': 'IRL', 'irlanda': 'IRL', 'italy': 'ITA', 'italia': 'ITA',
    'latvia': 'LVA', 'letonia': 'LVA', 'liechtenstein': 'LIE', 'lithuania': 'LTU', 'lituania': 'LTU',
    'luxembourg': 'LUX', 'luxemburgo': 'LUX', 'malta': 'MLT', 'moldova': 'MDA', 'moldavia': 'MDA',
    'monaco': 'MCO', 'montenegro': 'MNE', 'netherlands': 'NLD', 'paises bajos': 'NLD',
    'north macedonia': 'MKD', 'macedonia del norte': 'MKD', 'macedonia': 'MKD', 'norway': 'NOR', 'noruega': 'NOR',
    'poland': 'POL', 'polonia': 'POL', 'portugal': 'PRT', 'romania': 'ROU', 'rumania': 'ROU',
    'san marino': 'SMR', 'serbia': 'SRB', 'republic of serbia': 'SRB', 'slovakia': 'SVK', 'eslovaquia': 'SVK',
    'slovenia': 'SVN', 'eslovenia': 'SVN', 'spain': 'ESP', 'espana': 'ESP', 'sweden': 'SWE', 'suecia': 'SWE',
    'switzerland': 'CHE', 'suiza': 'CHE', 'ukraine': 'UKR', 'ucrania': 'UKR',
    'united kingdom': 'GBR', 'reino unido': 'GBR', 'vatican city': 'VAT', 'vaticano': 'VAT'
}

df_geo['iso_alpha'] = df_geo['pais_norm'].map(MAPEO_ISO3)

# Indicadores derivados
df_geo['densidad_log'] = np.log10(df_geo['densidad_poblacional'])
df_geo['eficiencia_espacial'] = df_geo['pib_per_capita'] / df_geo['densidad_poblacional']
df_geo['pib_por_km2'] = (df_geo['pib_miles_millones_eur'] * 1e9) / df_geo['superficie_km2']

df_geo['eficiencia_log'] = np.log10(df_geo['eficiencia_espacial'])
df_geo['intensidad_log'] = np.log10(df_geo['pib_por_km2'])

# Formatters para Tooltips
df_geo['pib_pc_fmt'] = df_geo['pib_per_capita'].apply(lambda x: f"{x:,.2f} €")
df_geo['densidad_fmt'] = df_geo['densidad_poblacional'].apply(lambda x: f"{x:,.2f} hab/km²")

# --- 3. CONFIGURACIÓN DE CATEGORÍAS Y DESCRIPCIONES ---
DESCRIPCION_CATEGORIAS = {
    "📐 Categoría Territorial": "Variables físicas y demográficas base de las naciones europeas.",
    "💶 Categoría Económica": "Indicadores macroeconómicos volumétricos finales.",
    "📊 Indicadores Base": "Coeficientes socioeconómicos estándar de densidad demográfica e ingreso.",
    "💡 Indicadores Derivados": "Modelos analíticos complejos en escala logarítmica (log₁₀)."
}

DICCIONARIO_CATEGORIAS = {
    "📐 Categoría Territorial": {
        "Población": {
            "columna": "poblacion", "escala": "Blues",
            "titulo": "Población Total por País", "leyenda": "Habitantes",
            "interpretacion": "Muestra la asimetría demográfica continental entre los núcleos del centro/oeste y la periferia."
        },
        "Superficie (km²)": {
            "columna": "superficie_km2", "escala": "Greens",
            "titulo": "Superficie Territorial (km²)", "leyenda": "Superficie km²",
            "interpretacion": "Contrasta la extensión física de las naciones europeas."
        }
    },
    "💶 Categoría Económica": {
        "PIB (€ miles de millones)": {
            "columna": "pib_miles_millones_eur", "escala": "Purples",
            "titulo": "Producto Interior Bruto (€ en M)", "leyenda": "PIB (€ M)",
            "interpretacion": "Concentración de la riqueza nominal en las principales economías."
        }
    },
    "📊 Indicadores Base": {
        "Densidad Poblacional (Ajustado Log)": {
            "columna": "densidad_log", "escala": "YlOrRd",
            "titulo": "Densidad de Población (Escala Logarítmica)", "leyenda": "Densidad (log₁₀)",
            "interpretacion": "Evalúa el gradiente de asentamiento urbano neutralizando picos de microestados."
        },
        "PIB per Cápita (€)": {
            "columna": "pib_per_capita", "escala": "Viridis",
            "titulo": "PIB per Cápita (€)", "leyenda": "PIB p.c. (€)",
            "interpretacion": "Prosperidad promedio e ingreso por habitante."
        }
    },
    "💡 Indicadores Derivados": {
        "Eficiencia Espacial del Capital (Log)": {
            "columna": "eficiencia_log", "escala": "Cividis",
            "titulo": "Eficiencia Espacial (PIB p.c. / Densidad Log)", "leyenda": "Eficiencia (log₁₀)",
            "interpretacion": "Mide el ingreso per cápita generado en función de la presión poblacional."
        },
        "Intensidad Económica Territorial (Log)": {
            "columna": "intensidad_log", "escala": "Magma",
            "titulo": "Intensidad Económica (€ PIB por km² Log)", "leyenda": "PIB / km² (log₁₀)",
            "interpretacion": "Rendimiento productivo por kilómetro cuadrado de superficie."
        }
    }
}

# --- 4. INTERFAZ Y RENDERIZADO ---
st.title("🇪🇺 Dashboard Socioeconómico de Europa")
st.markdown("Análisis geoespacial e indicadores socioeconómicos consolidados para 44 países europeos.")

col_cat, col_ind = st.columns(2)

with col_cat:
    categoria_seleccionada = st.selectbox("1. Selecciona la Categoría de Análisis:", list(DICCIONARIO_CATEGORIAS.keys()))

with col_ind:
    indicador_seleccionado = st.selectbox("2. Selecciona el Indicador:", list(DICCIONARIO_CATEGORIAS[categoria_seleccionada].keys()))

st.info(f"ℹ️ **Sobre esta sección:** {DESCRIPCION_CATEGORIAS[categoria_seleccionada]}")

cfg = DICCIONARIO_CATEGORIAS[categoria_seleccionada][indicador_seleccionado]

# DIBUJO MAPA VECTORIAL CON CARTOGRAFÍA NATIVA PLOTLY ISO-3
fig = px.choropleth(
    df_geo,
    locations="iso_alpha",
    color=cfg['columna'],
    hover_name="pais",
    color_continuous_scale=cfg['escala'],
    title=f"<b>Mapa de Europa: {cfg['titulo']}</b>",
    locationmode="ISO-3",
    scope="europe",
    hover_data={
        cfg['columna']: False,
        'iso_alpha': False,
        'pais_norm': False,
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

fig.update_layout(
    margin={"r": 0, "t": 40, "l": 0, "b": 0},
    height=580
)

st.plotly_chart(fig, use_container_width=True)

with st.expander("📌 **Interpretación analítica del mapa**", expanded=True):
    st.write(cfg['interpretacion'])
