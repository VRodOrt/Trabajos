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

# --- 1. CARGA Y LIMPIEZA DE DATOS (ETL DEFINITIVO CON URL) ---
@st.cache_data
def load_data():
    # URL directa (Raw) al CSV en GitHub. Esto no fallará ni en local ni en la nube.
    url = "https://raw.githubusercontent.com/VRodOrt/Trabajos/main/Business_Intelligence/Dashboard_interactivo_con_Streamlit/vehicles.csv"
    
    try:
        # Carga directa desde la web
        df = pd.read_csv(url, low_memory=False)
        
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
        
        # Limpieza Categorías
        def clean_trans(x):
            if pd.isna(x): return "Automático"
            x = str(x).lower()
            return 'Manual' if 'manual' in x else 'Automático'
        df['Transmisión'] = df['Transmision_Raw'].apply(clean_trans)
        
        def clean_fuel(x):
            x = str(x).lower()
            if 'electric' in x: return 'Eléctrico'
            if 'diesel' in x: return 'Diesel'
            if 'hybrid' in x: return 'Híbrido'
            if 'natural' in x or 'cng' in x: return 'Gas Natural'
            return 'Gasolina'
        df['Combustible'] = df['Combustible_Raw'].apply(clean_fuel)

        def clean_class(x):
            x = str(x).lower()
            if 'pickup' in x or 'truck' in x: return 'Pickup'
            if 'suv' in x: return 'SUV'
            if 'van' in x or 'minivan' in x: return 'Furgoneta'
            if 'sport' in x or 'two' in x: return 'Deportivo'
            return 'Turismo'
        df['Clase'] = df['Clase_Raw'].apply(clean_class)

        return df
    except Exception as e:
        st.error(f"Error procesando el CSV desde GitHub: {e}")
        return None

# --- 2. CEREBRO INTELIGENTE ---
def analizar_inteligente(q, df):
    q = q.lower()
    df_res = df.copy()
    filtros_txt = []
    
    map_vars = {
        'marca': 'Marca', 'modelo': 'Modelo',
        'combustible': 'Combustible', 'gasolina': 'Combustible', 'diesel': 'Combustible', 'electrico': 'Combustible',
        'transmision': 'Transmisión', 'manual': 'Transmisión', 'automatico': 'Transmisión',
        'clase': 'Clase', 'tipo': 'Clase', 'suv': 'Clase', 'pickup': 'Clase',
        'traccion': 'Tracción',
        'año': 'Año', 'evolucion': 'Año',
        'co2': 'CO2', 'emisiones': 'CO2',
        'consumo': 'MPG_Total', 'mpg': 'MPG_Total',
        'cilindros': 'Cilindros', 'motor': 'Motor_Litros'
    }

    vars_found = []
    for word, col in map_vars.items():
        if word in q:
            tipo = 'num' if col in ['Año', 'CO2', 'MPG_Total', 'Cilindros', 'Motor_Litros'] else 'cat'
            if not any(v['col'] == col for v in vars_found):
                vars_found.append({'col': col, 'tipo': tipo})

    top_makes = df['Marca'].value_counts().head(50).index.tolist()
    marcas_mencionadas = [m for m in top_makes if m.lower() in q]
    if marcas_mencionadas:
        df_res = df_res[df_res['Marca'].isin(marcas_mencionadas)]
        filtros_txt.append(f"Marca: {', '.join(marcas_mencionadas)}")
        if len(marcas_mencionadas) == 1:
            vars_found = [v for v in vars_found if v['col'] != 'Marca']

    # Lógica de salida simplificada para el motor gráfico
    cats = [v['col'] for v in vars_found if v['tipo'] == 'cat']
    nums = [v['col'] for v in vars_found if v['tipo'] == 'num']
    
    has_year = 'Año' in nums
    if has_year: nums.remove('Año')

    if len(cats) >= 2:
        c1, c2 = cats[0], cats[1]
        if not nums:
            data = df_res.groupby([c1, c2]).size().reset_index(name='Cantidad')
            return data, "stacked_bar", f"Distribución: {c1} vs {c2}", c1, 'Cantidad', c2
        else:
            n1 = nums[0]
            data = df_res.groupby([c1, c2])[n1].mean().reset_index()
            return data, "heatmap", f"Promedio de {n1} por {c1} y {c2}", c1, c2, n1
    elif has_year:
        n1 = nums[0] if nums else 'MPG_Total'
        c1 = cats[0] if cats else None
        data = df_res.groupby(['Año', c1])[n1].mean().reset_index() if c1 else df_res.groupby('Año')[n1].mean().reset_index()
        return data, "linea", f"Evolución de {n1}", 'Año', n1, c1
    elif len(cats) == 1:
        c1 = cats[0]
        if nums:
            n1 = nums[0]
            data = df_res.groupby(c1)[n1].mean().reset_index().sort_values(n1, ascending=False)
            return data.head(20), "barra", f"Promedio de {n1} por {c1}", c1, n1, c1
        else:
            data = df_res[c1].value_counts().reset_index()
            data.columns = [c1, 'Cantidad']
            return data.head(20), "pie", f"Recuento de {c1}", c1, 'Cantidad', None
    else:
        return df_res.head(50), "tabla", "Datos Generales", 'Modelo', 'MPG_Total', 'Combustible'

# --- 3. INTERFAZ ---
def main():
    st.title("🚀 Analista Total v9.0")
    
    df = load_data()
    if df is None:
        st.stop()

    if 'v9_data' not in st.session_state: st.session_state['v9_data'] = None
    if 'v9_msg' not in st.session_state: st.session_state['v9_msg'] = ""
    if 'v9_cfg' not in st.session_state: st.session_state['v9_cfg'] = {}

    tab1, tab2, tab3 = st.tabs(["📊 Dashboard", "💬 Consultas IA", "🛠️ Manual"])

    with tab1:
        st.markdown("### 🌍 Visión de Mercado")
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Total", len(df))
        k2.metric("Marcas", df['Marca'].nunique())
        k3.metric("Manuales", len(df[df['Transmisión']=='Manual']))
        k4.metric("Eléctricos", len(df[df['Combustible']=='Eléctrico']))
        
        c1, c2 = st.columns(2)
        with c1:
            fig1 = px.pie(df, names='Transmisión', title="Transmisión", hole=0.4)
            st.plotly_chart(fig1, use_container_width=True, key="dash_pie_trans")
        with c2:
            evo = df.groupby(['Año', 'Clase'])['MPG_Total'].mean().reset_index()
            fig2 = px.line(evo, x='Año', y='MPG_Total', color='Clase', title="Eficiencia por Clase")
            st.plotly_chart(fig2, use_container_width=True, key="dash_line_evo")

    with tab2:
        col_in, col_btn = st.columns([4, 1])
        with col_in:
            q = st.text_input("Haz tu consulta:", placeholder="Ej: Consumo por marca...", key="q_v9")
        with col_btn:
            st.write("")
            st.write("")
            btn = st.button("🔍 Analizar")
        
        if btn and q:
            d, t, m, x, y, c = analizar_inteligente(q, df)
            st.session_state['v9_data'], st.session_state['v9_msg'] = d, m
            st.session_state['v9_cfg'] = {'tipo': t, 'x': x, 'y': y, 'c': c}

        if st.session_state['v9_data'] is not None:
            data, msg, cfg = st.session_state['v9_data'], st.session_state['v9_msg'], st.session_state['v9_cfg']
            st.success(f"📊 {msg}")
            
            x, y, color = cfg['x'], cfg['y'], cfg['c']
            tipo = cfg['tipo']
            
            try:
                if tipo == "stacked_bar":
                    st.plotly_chart(px.bar(data, x=x, y=y, color=color, barmode='stack'), key="ia_stacked")
                elif tipo == "heatmap":
                    st.plotly_chart(px.density_heatmap(data, x=x, y=y, z=color, text_auto=True), key="ia_heat")
                elif tipo == "linea":
                    st.plotly_chart(px.line(data, x=x, y=y, color=color, markers=True), key="ia_line")
                elif tipo == "barra":
                    st.plotly_chart(px.bar(data, x=x, y=y, color=color or x), key="ia_bar")
                elif tipo == "pie":
                    st.plotly_chart(px.pie(data, names=x, values=y), key="ia_pie")
                else:
                    st.dataframe(data, use_container_width=True)
            except Exception as e:
                st.error(f"Error gráfico: {e}")

    with tab3:
        st.markdown("### 🛠️ Constructor Manual")
        all_cols = df.columns.tolist()
        c1, c2, c3 = st.columns(3)
        sel_x = c1.selectbox("Eje X", all_cols, index=all_cols.index('Marca'))
        sel_y = c2.selectbox("Eje Y", all_cols, index=all_cols.index('MPG_Total'))
        sel_c = c3.selectbox("Color", ['Ninguno'] + all_cols)
        
        if st.button("Generar Gráfico"):
            color_arg = sel_c if sel_c != 'Ninguno' else None
            fig_m = px.scatter(df.head(1000), x=sel_x, y=sel_y, color=color_arg)
            st.plotly_chart(fig_m, use_container_width=True, key="manual_scatter")

if __name__ == "__main__":
    main()
