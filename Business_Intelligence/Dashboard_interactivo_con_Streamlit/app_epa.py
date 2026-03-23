import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
import os

# --- CONFIGURACIÓN ---
st.set_page_config(
    page_title="Analista Total v9.0",
    page_icon="🚀",
    layout="wide"
)

# --- 1. CARGA Y LIMPIEZA DE DATOS (ETL DEFINITIVO) ---
@st.cache_data
def load_data():
    possible_paths = [
        "vehicles.csv",
        r"C:\Users\EM2025008339\Desktop\Formación Cross\Curso Python\Ejercicio EPA\vehicles.csv"
    ]
    
    df = None
    for path in possible_paths:
        if os.path.exists(path):
            try:
                df = pd.read_csv(path, low_memory=False)
                break
            except:
                continue
    
    if df is None: return None

    # Renombrado
    cols_map = {
        'make': 'Marca', 'model': 'Modelo', 'year': 'Año',
        'city08': 'MPG_Ciudad', 'highway08': 'MPG_Autopista',
        'co2TailpipeGpm': 'CO2', 'cylinders': 'Cilindros',
        'displ': 'Motor_Litros', 'drive': 'Tracción',
        'fuelType': 'Combustible_Raw', 'trany': 'Transmision_Raw',
        'VClass': 'Clase_Raw'
    }
    df = df[[c for c in cols_map.keys() if c in df.columns]].rename(columns=cols_map)

    # Conversión numérica
    for c in ['Año', 'MPG_Ciudad', 'MPG_Autopista', 'CO2', 'Cilindros', 'Motor_Litros']:
        df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)

    # Variables Calculadas
    df['MPG_Total'] = (df['MPG_Ciudad'] + df['MPG_Autopista']) / 2
    
    # --- LIMPIEZA CATEGÓRICA AVANZADA ---
    
    # 1. Transmisión: Lógica robusta
    def clean_trans(x):
        if pd.isna(x): return "Automático" # Asumimos auto si es nulo (mayoría)
        x = str(x).lower()
        if 'manual' in x: return 'Manual'
        return 'Automático'
    df['Transmisión'] = df['Transmision_Raw'].apply(clean_trans)
    
    # 2. Combustible
    def clean_fuel(x):
        x = str(x).lower()
        if 'electric' in x: return 'Eléctrico'
        if 'diesel' in x: return 'Diesel'
        if 'hybrid' in x: return 'Híbrido'
        if 'natural' in x or 'cng' in x: return 'Gas Natural'
        return 'Gasolina'
    df['Combustible'] = df['Combustible_Raw'].apply(clean_fuel)

    # 3. Clase
    def clean_class(x):
        x = str(x).lower()
        if 'pickup' in x or 'truck' in x: return 'Pickup'
        if 'suv' in x: return 'SUV'
        if 'van' in x or 'minivan' in x: return 'Furgoneta'
        if 'sport' in x or 'two' in x: return 'Deportivo'
        return 'Turismo'
    df['Clase'] = df['Clase_Raw'].apply(clean_class)

    return df

# --- 2. CEREBRO INTELIGENTE (LOGICA DE NEGOCIO) ---
def analizar_inteligente(q, df):
    q = q.lower()
    df_res = df.copy()
    filtros_txt = []
    
    # --- A. DETECCIÓN DE VARIABLES ---
    map_vars = {
        # Categóricas
        'marca': 'Marca', 'modelo': 'Modelo',
        'combustible': 'Combustible', 'gasolina': 'Combustible', 'diesel': 'Combustible', 'electrico': 'Combustible',
        'transmision': 'Transmisión', 'manual': 'Transmisión', 'automatico': 'Transmisión',
        'clase': 'Clase', 'tipo': 'Clase', 'suv': 'Clase', 'pickup': 'Clase',
        'traccion': 'Tracción',
        # Numéricas
        'año': 'Año', 'evolucion': 'Año',
        'co2': 'CO2', 'emisiones': 'CO2',
        'consumo': 'MPG_Total', 'mpg': 'MPG_Total',
        'cilindros': 'Cilindros', 'motor': 'Motor_Litros'
    }

    vars_found = []
    for word, col in map_vars.items():
        if word in q:
            # Determinar tipo
            tipo = 'num' if col in ['Año', 'CO2', 'MPG_Total', 'Cilindros', 'Motor_Litros'] else 'cat'
            # Evitar duplicados
            if not any(v['col'] == col for v in vars_found):
                vars_found.append({'col': col, 'tipo': tipo})

    # --- B. FILTROS INTELIGENTES (AQUÍ ESTÁ LA MEJORA) ---
    
    # 1. Filtro Marca
    top_makes = df['Marca'].value_counts().head(50).index.tolist()
    marcas_mencionadas = [m for m in top_makes if m.lower() in q]
    
    if marcas_mencionadas:
        df_res = df_res[df_res['Marca'].isin(marcas_mencionadas)]
        filtros_txt.append(f"Marca: {', '.join(marcas_mencionadas)}")
        # Si filtramos por marca, la quitamos de agrupación a menos que haya varias (comparación)
        if len(marcas_mencionadas) == 1:
            vars_found = [v for v in vars_found if v['col'] != 'Marca']

    # 2. Lógica "Vs" para Transmisión y Combustible
    # Si dice "Manual y Automático", NO filtramos, queremos ver ambos.
    # Si solo dice "Manual", SÍ filtramos.
    
    mencion_manual = 'manual' in q
    mencion_auto = 'automatico' in q or 'automática' in q
    
    if mencion_manual and not mencion_auto:
        df_res = df_res[df_res['Transmisión'] == 'Manual']
        filtros_txt.append("Solo Manual")
    elif mencion_auto and not mencion_manual:
        df_res = df_res[df_res['Transmisión'] == 'Automático']
        filtros_txt.append("Solo Automático")
    # Si están los dos, no filtramos nada, la variable 'Transmisión' ya está en vars_found para agrupar.

    # Misma lógica para Combustibles
    mencion_diesel = 'diesel' in q
    mencion_elec = 'electrico' in q
    if mencion_diesel and not mencion_elec and 'combustible' not in q:
         df_res = df_res[df_res['Combustible'] == 'Diesel']
         filtros_txt.append("Solo Diesel")
    elif mencion_elec and not mencion_diesel and 'combustible' not in q:
         df_res = df_res[df_res['Combustible'] == 'Eléctrico']
         filtros_txt.append("Solo Eléctrico")

    # --- C. MOTOR DE DECISIÓN GRÁFICA ---
    cats = [v['col'] for v in vars_found if v['tipo'] == 'cat']
    nums = [v['col'] for v in vars_found if v['tipo'] == 'num']
    
    # Forzamos Año a ser eje X si está presente
    if 'Año' in nums: 
        nums.remove('Año')
        has_year = True
    else: has_year = False

    # ESCENARIO 1: CRUCE 2 CATEGORÍAS (Ej: Transmisión vs Clase)
    if len(cats) >= 2:
        c1, c2 = cats[0], cats[1]
        
        # ¿Quiere contar o promediar?
        if not nums:
            # Recuento
            data = df_res.groupby([c1, c2]).size().reset_index(name='Cantidad')
            # Ordenar para que se vea bonito
            top = data.groupby(c1)['Cantidad'].sum().sort_values(ascending=False).index[:15]
            data = data[data[c1].isin(top)]
            msg = f"Distribución: **{c1}** vs **{c2}**"
            return data, "stacked_bar", msg, c1, 'Cantidad', c2
        else:
            # Promedio Numérico
            n1 = nums[0]
            data = df_res.groupby([c1, c2])[n1].mean().reset_index()
            msg = f"Promedio de **{n1}** por **{c1}** y **{c2}**"
            return data, "heatmap", msg, c1, c2, n1

    # ESCENARIO 2: EVOLUCIÓN TEMPORAL
    elif has_year:
        n1 = nums[0] if nums else 'MPG_Total'
        # Si hay categoría, desglosamos por ella
        if cats:
            c1 = cats[0]
            data = df_res.groupby(['Año', c1])[n1].mean().reset_index()
            msg = f"Evolución de **{n1}** por **{c1}**"
            return data, "linea", msg, 'Año', n1, c1
        else:
            data = df_res.groupby('Año')[n1].mean().reset_index()
            msg = f"Evolución de **{n1}**"
            return data, "linea", msg, 'Año', n1, None

    # ESCENARIO 3: 1 CATEGORÍA (Recuento o Promedio)
    elif len(cats) == 1:
        c1 = cats[0]
        if nums:
            n1 = nums[0]
            data = df_res.groupby(c1)[n1].mean().reset_index().sort_values(n1, ascending=False)
            msg = f"Promedio de **{n1}** por **{c1}**"
            return data.head(20), "barra", msg, c1, n1, c1
        else:
            data = df_res[c1].value_counts().reset_index()
            data.columns = [c1, 'Cantidad']
            msg = f"Recuento de **{c1}**"
            return data.head(20), "pie", msg, c1, 'Cantidad', None

    # ESCENARIO 4: CORRELACIÓN (2 Numéricas)
    elif len(nums) >= 2:
        n1, n2 = nums[0], nums[1]
        data = df_res.head(1000) # Muestra para no saturar
        msg = f"Relación **{n1}** vs **{n2}**"
        return data, "scatter", msg, n1, n2, 'Combustible'

    # DEFAULT
    else:
        data = df_res.sort_values('MPG_Total', ascending=False).head(50)
        msg = "Datos Generales"
        if filtros_txt: msg += f" ({', '.join(filtros_txt)})"
        return data, "tabla", msg, 'Modelo', 'MPG_Total', 'Combustible'

# --- 3. INTERFAZ GRÁFICA ---
def main():
    st.title("🚀 Analista Total v9.0")
    
    df = load_data()
    if df is None:
        st.error("Error CSV.")
        st.stop()

    if 'v9_data' not in st.session_state: st.session_state['v9_data'] = None
    if 'v9_msg' not in st.session_state: st.session_state['v9_msg'] = ""
    if 'v9_cfg' not in st.session_state: st.session_state['v9_cfg'] = {}

    # --- PESTAÑAS ---
    tab1, tab2, tab3 = st.tabs(["📊 Dashboard", "💬 Consultas IA", "🛠️ Constructor Manual"])

    # 1. DASHBOARD
    with tab1:
        st.markdown("### 🌍 Visión de Mercado")
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Total", len(df))
        k2.metric("Marcas", df['Marca'].nunique())
        k3.metric("Manuales", len(df[df['Transmisión']=='Manual']))
        k4.metric("Eléctricos", len(df[df['Combustible']=='Eléctrico']))
        
        c1, c2 = st.columns(2)
        c1.plotly_chart(px.pie(df, names='Transmisión', title="Transmisión", hole=0.4), use_container_width=True)
        # Evolución compleja fija
        evo = df.groupby(['Año', 'Clase'])['MPG_Total'].mean().reset_index()
        c2.plotly_chart(px.line(evo, x='Año', y='MPG_Total', color='Clase', title="Evolución Eficiencia por Clase"), use_container_width=True)

    # 2. CONSULTAS IA
    with tab2:
        col_in, col_btn = st.columns([4, 1])
        with col_in:
            q = st.text_input("Consulta:", placeholder="Ej: Transmisión vs Clase, Consumo Ford vs Toyota...", key="q_v9")
        with col_btn:
            st.write("") 
            st.write("")
            if st.button("🔍 Analizar") or st.button("🎲 Ejemplo"):
                if not q:
                    opts = [
                        "Cuántos coches manuales y automáticos hay por marca", # Cruce 3 vars
                        "Comparar consumo de transmisión manual vs automática", # Comparativa
                        "Evolución del CO2 en SUVs", # Tiempo + Filtro
                        "Marcas con más coches eléctricos", # Filtro + Recuento
                        "Relación cilindros y consumo" # Scatter
                    ]
                    q = np.random.choice(opts)
                    st.info(f"Ejemplo: **{q}**")
                
                d, t, m, x, y, c = analizar_inteligente(q, df)
                st.session_state['v9_data'] = d
                st.session_state['v9_msg'] = m
                st.session_state['v9_cfg'] = {'tipo': t, 'x': x, 'y': y, 'c': c}

        # RESULTADOS IA
        if st.session_state['v9_data'] is not None:
            data = st.session_state['v9_data']
            msg = st.session_state['v9_msg']
            cfg = st.session_state['v9_cfg']
            
            st.success(f"📊 {msg}")
            
            # Selector Gráfico
            tipos = ["Tabla", "Barra", "Barra Apilada", "Heatmap", "Línea", "Scatter", "Pie", "Boxplot"]
            idx = 0
            if cfg['tipo'] == 'stacked_bar': idx = 2
            elif cfg['tipo'] == 'heatmap': idx = 3
            elif cfg['tipo'] == 'linea': idx = 4
            elif cfg['tipo'] == 'pie': idx = 6
            
            grafico = st.selectbox("Visualización:", tipos, index=idx)
            x, y, c = cfg['x'], cfg['y'], cfg['c']
            
            try:
                if grafico == "Tabla": st.dataframe(data, use_container_width=True)
                elif grafico == "Barra": st.plotly_chart(px.bar(data, x=x, y=y, color=c or x, barmode='group'), use_container_width=True)
                elif grafico == "Barra Apilada": st.plotly_chart(px.bar(data, x=x, y=y, color=c or x, barmode='stack'), use_container_width=True)
                elif grafico == "Heatmap": 
                    if c: st.plotly_chart(px.density_heatmap(data, x=x, y=c, z=y, text_auto=True), use_container_width=True)
                    else: st.warning("Heatmap requiere 3 variables (X, Y, Color/Z).")
                elif grafico == "Línea": st.plotly_chart(px.line(data, x=x, y=y, color=c, markers=True), use_container_width=True)
                elif grafico == "Scatter": st.plotly_chart(px.scatter(data, x=x, y=y, color=c), use_container_width=True)
                elif grafico == "Pie": st.plotly_chart(px.pie(data, names=x, values=y if pd.api.types.is_numeric_dtype(data[y]) else None), use_container_width=True)
                elif grafico == "Boxplot": st.plotly_chart(px.box(data, x=x, y=y, color=c), use_container_width=True)
            except Exception as e:
                st.error(f"Error visualizando: {e}")

    # 3. CONSTRUCTOR MANUAL (RECUPERADO)
    with tab3:
        st.markdown("### 🛠️ Constructor Manual de Gráficos")
        st.caption("Si la IA no acierta, construye tu gráfico aquí.")
        
        col1, col2, col3, col4 = st.columns(4)
        
        all_cols = df.columns.tolist()
        num_cols = df.select_dtypes(include=np.number).columns.tolist()
        cat_cols = df.select_dtypes(exclude=np.number).columns.tolist()
        
        with col1:
            m_x = st.selectbox("Eje X (Categoría)", ['Ninguno'] + all_cols, index=all_cols.index('Marca') if 'Marca' in all_cols else 0)
        with col2:
            m_y = st.selectbox("Eje Y (Valor)", ['Ninguno', 'Conteo'] + num_cols, index=num_cols.index('MPG_Total')+1 if 'MPG_Total' in num_cols else 0)
        with col3:
            m_color = st.selectbox("Color / Grupo", ['Ninguno'] + cat_cols, index=0)
        with col4:
            m_tipo = st.selectbox("Tipo Gráfico", ["Barra", "Línea", "Scatter", "Boxplot", "Histograma", "Pie"])
            
        if st.button("Generar Gráfico Manual"):
            if m_x != 'Ninguno':
                try:
                    # Preparar datos
                    if m_y == 'Conteo':
                        if m_color != 'Ninguno':
                            df_m = df.groupby([m_x, m_color]).size().reset_index(name='Conteo')
                            y_val = 'Conteo'
                        else:
                            df_m = df[m_x].value_counts().reset_index()
                            df_m.columns = [m_x, 'Conteo']
                            y_val = 'Conteo'
                    elif m_y != 'Ninguno':
                        if m_color != 'Ninguno':
                            df_m = df.groupby([m_x, m_color])[m_y].mean().reset_index()
                        else:
                            df_m = df.groupby(m_x)[m_y].mean().reset_index()
                        y_val = m_y
                    else:
                        df_m = df # Datos crudos para scatter/hist
                        y_val = None

                    # Renderizar
                    color_val = m_color if m_color != 'Ninguno' else None
                    
                    if m_tipo == "Barra": st.plotly_chart(px.bar(df_m, x=m_x, y=y_val, color=color_val), use_container_width=True)
                    elif m_tipo == "Línea": st.plotly_chart(px.line(df_m, x=m_x, y=y_val, color=color_val, markers=True), use_container_width=True)
                    elif m_tipo == "Scatter": st.plotly_chart(px.scatter(df, x=m_x, y=m_y if m_y != 'Conteo' else None, color=color_val), use_container_width=True)
                    elif m_tipo == "Pie": st.plotly_chart(px.pie(df_m, names=m_x, values=y_val), use_container_width=True)
                    elif m_tipo == "Boxplot": st.plotly_chart(px.box(df, x=m_x, y=m_y if m_y != 'Conteo' else None, color=color_val), use_container_width=True)
                    elif m_tipo == "Histograma": st.plotly_chart(px.histogram(df, x=m_x, color=color_val), use_container_width=True)
                    
                except Exception as e:
                    st.error(f"Error al generar gráfico: {e}")

if __name__ == "__main__":
    main()
