import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import requests
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

def limpiar_cadena(val):
    if pd.isna(val): return ""
    txt = str(val).lower().strip()
    return ''.join(c for c in unicodedata.normalize('NFD', txt) if unicodedata.category(c) != 'Mn')

# CARGAMOS EL GEOJSON PURO, SIN ALTERARLO
@st.cache_data(ttl=3600)
def cargar_datos_desde_db():
    engine = create_engine(
        CADENA_CONEXION_PG,
        connect_args={"sslmode": "require"}
    )
    with engine.connect() as conn:
        df = pd.read_sql_query(text("SELECT * FROM tb_indicadores_europa;"), conn)
    
    url_geojson = "https://raw.githubusercontent.com/leakyMirror/map-of-europe/master/GeoJSON/europe.geojson"
    geojson = requests.get(url_geojson).json()
    
    return df, geojson

try:
    df_indicadores, geojson_europa = cargar_datos_desde_db()
except Exception as e:
    st.error(f"⚠️ Error de conexión a PostgreSQL: {e}")
    st.stop()

# --- 2. PREPARACIÓN DE DATOS Y MAPEO DINÁMICO ---
df_geo = df_indicadores.copy()
df_geo['pais_limpio'] = df_geo['pais'].apply(limpiar_cadena)

cols_num = ['poblacion', 'superficie_km2', 'pib_miles_millones_eur', 'densidad_poblacional', 'pib_per_capita']
for c in cols_num:
    df_geo[c] = pd.to_numeric(df_geo[c], errors='coerce')

# Diccionario original (Base de Datos -> Inglés)
DICCIONARIO_NOMBRES = {
    'spain': 'Spain', 'espana': 'Spain', 'france': 'France', 'francia': 'France',
    'germany': 'Germany', 'alemania': 'Germany', 'italy': 'Italy', 'italia': 'Italy',
    'united kingdom': 'United Kingdom', 'reino unido': 'United Kingdom',
    'portugal': 'Portugal', 'greece': 'Greece', 'grecia': 'Greece',
    'poland': 'Poland', 'polonia': 'Poland', 'ukraine': 'Ukraine', 'ucrania': 'Ukraine',
    'sweden': 'Sweden', 'suecia': 'Sweden', 'norway': 'Norway', 'noruega': 'Norway',
    'finland': 'Finland', 'finlandia': 'Finland', 'belgium': 'Belgium', 'belgica': 'Belgium',
    'netherlands': 'Netherlands', 'paises bajos': 'Netherlands',
    'switzerland': 'Switzerland', 'suiza': 'Switzerland', 'austria': 'Austria', 
    'ireland': 'Ireland', 'irlanda': 'Ireland', 'czechia': 'Czech Republic', 
    'czech republic': 'Czech Republic', 'republica checa': 'Czech Republic',
    'romania': 'Romania', 'rumania': 'Romania', 'bulgaria': 'Bulgaria', 
    'hungary': 'Hungary', 'hungria': 'Hungary', 'denmark': 'Denmark', 'dinamarca': 'Denmark',
    'slovakia': 'Slovakia', 'eslovaquia': 'Slovakia', 'slovenia': 'Slovenia', 'eslovenia': 'Slovenia',
    'croatia': 'Croatia', 'croacia': 'Croatia', 
    'bosnia and herzegovina': 'Bosnia and Herzegovina', 'bosnia y herzegovina': 'Bosnia and Herzegovina',
    'serbia': 'Republic of Serbia', 'republic of serbia': 'Republic of Serbia',
    'north macedonia': 'Macedonia', 'macedonia': 'Macedonia',
    'albania': 'Albania', 'moldova': 'Moldova', 'moldavia': 'Moldova',
    'belarus': 'Belarus', 'bielorrusia': 'Belarus', 'lithuania': 'Lithuania', 'lituania': 'Lithuania',
    'latvia': 'Latvia', 'letonia': 'Latvia', 'estonia': 'Estonia', 
    'iceland': 'Iceland', 'islandia': 'Iceland', 'luxembourg': 'Luxembourg', 'luxemburgo': 'Luxembourg',
    'malta': 'Malta', 'cyprus': 'Cyprus', 'chipre': 'Cyprus', 'andorra': 'Andorra', 
    'monaco': 'Monaco', 'san marino': 'San Marino', 'liechtenstein': 'Liechtenstein', 
    'vatican city': 'Vatican', 'vaticano': 'Vatican'
}

df_geo['pais_english'] = df_geo['pais_limpio'].map(DICCIONARIO_NOMBRES).fillna(df_geo['pais'].astype(str).str.title())

# Extraemos los nombres puros del GeoJSON y creamos un índice de búsqueda
nombres_en_geojson = {}
for feature in geojson_europa['features']:
    nombre_real = feature['properties'].get('NAME', '')
    nombre_limpio = limpiar_cadena(nombre_real)
    nombres_en_geojson[nombre_limpio] = nombre_real
    
    # Manejamos las excepciones conflictivas sin tocar el GeoJSON
    if 'bosnia' in nombre_limpio: nombres_en_geojson['bosnia and herzegovina'] = nombre_real
    if 'serbia' in nombre_limpio: nombres_en_geojson['republic of serbia'] = nombre_real
    if 'macedonia' in nombre_limpio: nombres_en_geojson['macedonia'] = nombre_real
    if 'czech' in nombre_limpio: nombres_en_geojson['czech republic'] = nombre_real
    if 'moldova' in nombre_limpio: nombres_en_geojson['moldova'] = nombre_real

# Ahora le decimos al DataFrame que adopte el nombre EXACTO que tiene el GeoJSON
df_geo['pais_geojson_exacto'] = df_geo['pais_english'].apply(
    lambda x: nombres_en_geojson.get(limpiar_cadena(x), x)
)

# Indicadores derivados
df_geo['densidad_log'] = np.log10(df_geo['densidad_poblacional'])
df_geo['eficiencia_espacial'] = df_geo['pib_per_capita'] / df_geo['densidad_poblacional']
df_geo['pib_por_km2'] = (df_geo['pib_miles_millones_eur'] * 1e9) / df_geo['superficie_km2']
df_geo['eficiencia_log'] = np.log10(df_geo['eficiencia_espacial'])
df_geo['intensidad_log'] = np.log10(df_geo['pib_por_km2'])

df_geo['pib_pc_fmt'] = df_geo['pib_per_capita'].apply(lambda x: f"{x:,.2f} €" if pd.notnull(x) else "N/A")
df_geo['densidad_fmt'] = df_geo['densidad_poblacional'].apply(lambda x: f"{x:,.2f} hab/km²" if pd.notnull(x) else "N/A")

# --- 3. DICCIONARIOS ---
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

# --- 4. INTERFAZ ---
st.title("🇪🇺 Dashboard Socioeconómico de Europa")
st.markdown("Análisis geoespacial e indicadores socioeconómicos consolidados para 44 países europeos.")

# 1. Reservamos un contenedor vacío JUSTO DEBAJO del título
contenedor_kpis = st.container()

# 2. Mostramos los selectores
col_cat, col_ind = st.columns(2)
with col_cat:
    categoria_seleccionada = st.selectbox("1. Selecciona la Categoría de Análisis:", list(DICCIONARIO_CATEGORIAS.keys()))
with col_ind:
    indicador_seleccionado = st.selectbox("2. Selecciona el Indicador:", list(DICCIONARIO_CATEGORIAS[categoria_seleccionada].keys()))

# 3. Llenamos el contenedor de KPIs que dejamos arriba en función de la selección
with contenedor_kpis:
    st.markdown("### 📊 Visión General Continental")
    k1, k2, k3 = st.columns(3)
    
    if categoria_seleccionada == "📐 Categoría Territorial":
        k1.metric("Población Total (Europa)", f"{df_geo['poblacion'].sum() / 1e6:.1f} Millones")
        k2.metric("Superficie Total", f"{df_geo['superficie_km2'].sum() / 1e6:.2f} M km²")
        
        # El tercer KPI cambia según lo que elijas en el segundo desplegable
        if indicador_seleccionado == "Población":
            pais_max = df_geo.loc[df_geo['poblacion'].idxmax(), 'pais']
            k3.metric("Nación más poblada", pais_max)
        else:
            pais_max = df_geo.loc[df_geo['superficie_km2'].idxmax(), 'pais']
            k3.metric("Nación más extensa", pais_max)

    elif categoria_seleccionada == "💶 Categoría Económica":
        k1.metric("PIB Total (Europa)", f"{df_geo['pib_miles_millones_eur'].sum():,.0f} mil M €")
        k2.metric("PIB Medio por País", f"{df_geo['pib_miles_millones_eur'].mean():,.0f} mil M €")
        pais_pib_max = df_geo.loc[df_geo['pib_miles_millones_eur'].idxmax(), 'pais']
        k3.metric("Motor Económico (Máx PIB)", pais_pib_max)

    elif categoria_seleccionada == "📊 Indicadores Base":
        k1.metric("Densidad Media", f"{df_geo['densidad_poblacional'].mean():.1f} hab/km²")
        k2.metric("PIB per Cápita Promedio", f"{df_geo['pib_per_capita'].mean():,.0f} €")
        pais_pc_max = df_geo.loc[df_geo['pib_per_capita'].idxmax(), 'pais']
        k3.metric("Líder Ingreso p.c.", pais_pc_max)

    elif categoria_seleccionada == "💡 Indicadores Derivados":
        k1.metric("Intensidad Económica Media", f"{df_geo['pib_por_km2'].mean() / 1e6:.1f} M €/km²")
        pais_efi_max = df_geo.loc[df_geo['eficiencia_espacial'].idxmax(), 'pais']
        k2.metric("Máxima Eficiencia Espacial", pais_efi_max)
        pais_int_max = df_geo.loc[df_geo['pib_por_km2'].idxmax(), 'pais']
        k3.metric("Máxima Intensidad Económica", pais_int_max)
        
    st.divider() # Añade una línea sutil para separar los KPIs de los selectores

st.info(f"ℹ️ **Sobre esta sección:** {DESCRIPCION_CATEGORIAS[categoria_seleccionada]}")
cfg = DICCIONARIO_CATEGORIAS[categoria_seleccionada][indicador_seleccionado]

# DIBUJO DEL MAPA USANDO LA PROPIEDAD 'NAME' ORIGINAL
fig = px.choropleth(
    df_geo,
    geojson=geojson_europa,
    locations='pais_geojson_exacto',
    featureidkey='properties.NAME', # Usamos la clave limpia original del GeoJSON
    color=cfg['columna'],
    color_continuous_scale=cfg['escala'],
    title=f"<b>Mapa de Europa: {cfg['titulo']}</b>",
    hover_name='pais',
    template='plotly_dark',
    hover_data={
        cfg['columna']: False,
        'pais_geojson_exacto': False,
        'pais_limpio': False,
        'pais_english': False,
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
    fitbounds="locations",
    visible=False,
    bgcolor="#0e1117"
)

fig.update_layout(
    paper_bgcolor="#0e1117",
    plot_bgcolor="#0e1117",
    margin={"r": 0, "t": 40, "l": 0, "b": 0},
    height=600
)

st.plotly_chart(fig, use_container_width=True)

with st.expander("📌 **Interpretación analítica del mapa**", expanded=True):
    st.write(cfg['interpretacion'])
