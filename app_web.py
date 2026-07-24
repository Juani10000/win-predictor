import streamlit as st
import pandas as pd
import os
import re

st.set_page_config(page_title="Win Predictor - LPF", page_icon="⚽", layout="centered")

# ---------------------------------------------------------
# ENCABEZADO CON LOGO OFICIAL DE LA LIGA PROFESIONAL (LPF)
# ---------------------------------------------------------
col_logo, col_titulo = st.columns([0.15, 0.85])
with col_logo:
    st.image(
        "https://upload.wikimedia.org/wikipedia/commons/thumb/1/15/Liga_Profesional_de_F%C3%Batbol_%28Argentina%29_logo.svg/300px-Liga_Profesional_de_F%C3%Batbol_%28Argentina%29_logo.svg.png",
        width=55
    )
with col_titulo:
    st.title("Win Predictor - LPF")

@st.cache_data(ttl=60)
def cargar_datos():
    if os.path.exists("datos_procesados.csv"):
        return pd.read_csv("datos_procesados.csv")
    return None

df = cargar_datos()

if df is None or df.empty:
    st.error("❌ No se encontraron datos procesados. Por favor ejecutá la actualización en GitHub.")
else:
    # ---------------------------------------------------------
    # DICCIONARIO DE ESCUDOS OFICIALES Y EXACTOS (PNG Wikimedia Directo)
    # ---------------------------------------------------------
    escudos_oficiales = {
        "Argentinos Juniors": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/1b/AAAJ_logo.svg/200px-AAAJ_logo.svg.png",
        "Atlético Tucumán": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/ae/Escudo_Atl%C3%A9tico_Tucum%C3%A1n_-_2020.svg/200px-Escudo_Atl%C3%A9tico_Tucum%C3%A1n_-_2020.svg.png",
        "Banfield": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c8/Escudo_del_Club_Atl%C3%A9tico_Banfield.svg/200px-Escudo_del_Club_Atl%C3%A9tico_Banfield.svg.png",
        "Barracas Central": "https://upload.wikimedia.org/wikipedia/commons/thumb/2/20/Escudo_de_Barracas_Central.svg/200px-Escudo_de_Barracas_Central.svg.png",
        "Belgrano": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c3/Escudo_oficial_del_Club_Atl%C3%A9tico_Belgrano.svg/200px-Escudo_oficial_del_Club_Atl%C3%A9tico_Belgrano.svg.png",
        "Boca Juniors": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/1b/Escudo_del_Club_Atl%C3%A9tico_Boca_Juniors.svg/200px-Escudo_del_Club_Atl%C3%A9tico_Boca_Juniors.svg.png",
        "Central Córdoba (SdE)": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/87/Escudo_de_Central_C%C3%B3rdoba_de_Santiago_del_Estero.svg/200px-Escudo_de_Central_C%C3%B3rdoba_de_Santiago_del_Estero.svg.png",
        "Defensa y Justicia": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/ac/Escudo_del_Club_Social_y_Deportivo_Defensa_y_Justicia.svg/200px-Escudo_del_Club_Social_y_Deportivo_Defensa_y_Justicia.svg.png",
        "Deportivo Riestra": "https://upload.wikimedia.org/wikipedia/commons/thumb/b/b5/Deportivo_Riestra_logo.svg/200px-Deportivo_Riestra_logo.svg.png",
        "Estudiantes (LP)": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a1/Escudo_de_Estudiantes_de_La_Plata.svg/200px-Escudo_de_Estudiantes_de_La_Plata.svg.png",
        "Gimnasia (LP)": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/36/Gimnasia_y_Esgrima_de_La_Plata_logo.svg/200px-Gimnasia_y_Esgrima_de_La_Plata_logo.svg.png",
        "Gimnasia (Mendoza)": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a2/Escudo_del_Club_Gimnasia_y_Esgrima_de_Mendoza.svg/200px-Escudo_del_Club_Gimnasia_y_Esgrima_de_Mendoza.svg.png",
        "Godoy Cruz": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c2/Escudo_del_Club_Deportivo_Godoy_Cruz_Antonio_Tomba.svg/200px-Escudo_del_Club_Deportivo_Godoy_Cruz_Antonio_Tomba.svg.png",
        "Huracán": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a0/Escudo_del_Club_Atl%C3%A9tico_Hurac%C3%A1n.svg/200px-Escudo_del_Club_Atl%C3%A9tico_Hurac%C3%A1n.svg.png",
        "Independiente": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/db/Escudo_del_Club_Atl%C3%A9tico_Independiente.svg/200px-Escudo_del_Club_Atl%C3%A9tico_Independiente.svg.png",
        "Independiente Rivadavia": "https://upload.wikimedia.org/wikipedia/commons/thumb/2/23/Escudo_del_Club_Sportivo_Independiente_Rivadavia.svg/200px-Escudo_del_Club_Sportivo_Independiente_Rivadavia.svg.png",
        "Instituto": "https://upload.wikimedia.org/wikipedia/commons/thumb/f/f3/Escudo_de_Instituto_ACC.svg/200px-Escudo_de_Instituto_ACC.svg.png",
        "Lanús": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c1/Escudo_del_Club_Atl%C3%A9tico_Lan%C3%Bas.svg/200px-Escudo_del_Club_Atl%C3%A9tico_Lan%C3%Bas.svg.png",
        "Newell's Old Boys": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a2/Escudo_del_Club_Atl%C3%A9tico_Newell%27s_Old_Boys.svg/200px-Escudo_del_Club_Atl%C3%A9tico_Newell%27s_Old_Boys.svg.png",
        "Platense": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d4/Escudo_del_Club_Atl%C3%A9tico_Platense.svg/200px-Escudo_del_Club_Atl%C3%A9tico_Platense.svg.png",
        "Racing Club": "https://upload.wikimedia.org/wikipedia/commons/thumb/5/56/Escudo_de_Racing_Club.svg/200px-Escudo_de_Racing_Club.svg.png",
        "River Plate": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/ac/Escudo_del_C_A_River_Plate.svg/200px-Escudo_del_C_A_River_Plate.svg.png",
        "Rosario Central": "https://upload.wikimedia.org/wikipedia/commons/thumb/f/f7/Escudo_del_Club_Atl%C3%A9tico_Rosario_Central.svg/200px-Escudo_del_Club_Atl%C3%A9tico_Rosario_Central.svg.png",
        "San Lorenzo": "https://upload.wikimedia.org/wikipedia/commons/thumb/7/77/Escudo_del_Club_Atl%C3%A9tico_San_Lorenzo_de_Almagro.svg/200px-Escudo_del_Club_Atl%C3%A9tico_San_Lorenzo_de_Almagro.svg.png",
        "Sarmiento (J)": "https://upload.wikimedia.org/wikipedia/commons/thumb/2/23/Escudo_del_Club_Atl%C3%A9tico_Sarmiento_%28Jun%C3%ADn%29.svg/200px-Escudo_del_Club_Atl%C3%A9tico_Sarmiento_%28Jun%C3%ADn%29.svg.png",
        "Talleres (C)": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/07/Escudo_del_Club_Atl%C3%A9tico_Talleres_de_C%C3%B3rdoba.svg/200px-Escudo_del_Club_Atl%C3%A9tico_Talleres_de_C%C3%B3rdoba.svg.png",
        "Tigre": "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e0/Escudo_del_Club_Atl%C3%A9tico_Tigre.svg/200px-Escudo_del_Club_Atl%C3%A9tico_Tigre.svg.png",
        "Unión": "https://upload.wikimedia.org/wikipedia/commons/thumb/7/79/Escudo_del_Club_Atl%C3%A9tico_Uni%C3%B3n_de_Santa_Fe.svg/200px-Escudo_del_Club_Atl%C3%A9tico_Uni%C3%B3n_de_Santa_Fe.svg.png",
        "Vélez Sarsfield": "https://upload.wikimedia.org/wikipedia/commons/thumb/2/20/Escudo_del_Club_Atl%C3%A9tico_V%C3%A9lez_Sarsfield.svg/200px-Escudo_del_Club_Atl%C3%A9tico_V%C3%A9lez_Sarsfield.svg.png",
        "Aldosivi": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/80/Escudo_del_Club_Atl%C3%A9tico_Aldosivi.svg/200px-Escudo_del_Club_Atl%C3%A9tico_Aldosivi.svg.png",
        "Estudiantes (RC)": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3a/Escudo_del_Club_A%C3%A9reo_y_Deportivo_Estudiantes_de_R%C3%ADo_Cuarto.svg/200px-Escudo_del_Club_A%C3%A9reo_y_Deportivo_Estudiantes_de_R%C3%ADo_Cuarto.svg.png"
    }

    escudo_defecto = "https://upload.wikimedia.org/wikipedia/commons/thumb/1/15/Liga_Profesional_de_F%C3%Batbol_%28Argentina%29_logo.svg/200px-Liga_Profesional_de_F%C3%Batbol_%28Argentina%29_logo.svg.png"

    def obtener_escudo(nombre_bruto):
        if not isinstance(nombre_bruto, str):
            return escudo_defecto
        
        # Elimina notas entre corchetes como [n. 1], [1], etc.
        nombre = re.sub(r'\[.*?\]', '', nombre_bruto).strip()
        
        if nombre in escudos_oficiales:
            return escudos_oficiales[nombre]
            
        nom_lower = nombre.lower()
        if "argentinos" in nom_lower:
            return escudos_oficiales["Argentinos Juniors"]
        if "boca" in nom_lower:
            return escudos_oficiales["Boca Juniors"]
        if "talleres" in nom_lower:
            return escudos_oficiales["Talleres (C)"]
        if "belgrano" in nom_lower:
            return escudos_oficiales["Belgrano"]
        if "independiente riv" in nom_lower or "rivadavia" in nom_lower:
            return escudos_oficiales["Independiente Rivadavia"]
        if "independiente" in nom_lower:
            return escudos_oficiales["Independiente"]
        if "gimnasia" in nom_lower and ("lp" in nom_lower or "esgrima" in nom_lower):
            return escudos_oficiales["Gimnasia (LP)"]
        if "gimnasia" in nom_lower and "mendoza" in nom_lower:
            return escudos_oficiales["Gimnasia (Mendoza)"]
        if "estudiantes" in nom_lower and "lp" in nom_lower:
            return escudos_oficiales["Estudiantes (LP)"]
        if "estudiantes" in nom_lower and "rc" in nom_lower:
            return escudos_oficiales["Estudiantes (RC)"]
        if "sarmiento" in nom_lower:
            return escudos_oficiales["Sarmiento (J)"]
        if "central c" in nom_lower or "cordoba" in nom_lower:
            return escudos_oficiales["Central Córdoba (SdE)"]
        if "newell" in nom_lower:
            return escudos_oficiales["Newell's Old Boys"]
        if "riestra" in nom_lower:
            return escudos_oficiales["Deportivo Riestra"]
        if "tucuman" in nom_lower or "tucumán" in nom_lower:
            return escudos_oficiales["Atlético Tucumán"]
        if "barracas" in nom_lower:
            return escudos_oficiales["Barracas Central"]
            
        for key, url in escudos_oficiales.items():
            if key.lower() in nom_lower or nom_lower in key.lower():
                return url
                
        return escudo_defecto

    # ---------------------------------------------------------
    # SECCIÓN 1: PREDICCIÓN DE PARTIDOS
    # ---------------------------------------------------------
    st.markdown("### 🔮 Predicción de Partido")
    st.caption("Cálculo de probabilidades basado en el rendimiento actual.")
    
    lista_equipos = sorted(df["Equipo"].astype(str).unique())
    
    col1, col2 = st.columns(2)
    with col1:
        local = st.selectbox("Seleccionar Local", lista_equipos, index=0)
    with col2:
        idx_vis = 1 if len(lista_equipos) > 1 else 0
        visitante = st.selectbox("Seleccionar Visitante", lista_equipos, index=idx_vis)

    if local == visitante:
        st.warning("⚠️ Elegí dos equipos distintos.")
    else:
        row_loc = df[df["Equipo"] == local].iloc[0]
        row_vis = df[df["Equipo"] == visitante].iloc[0]

        pts_loc = float(row_loc.get("Puntos", 0))
        pj_loc = max(float(row_loc.get("PJ", 1)), 1.0)
        rend_loc = pts_loc / (pj_loc * 3.0)

        pts_vis = float(row_vis.get("Puntos", 0))
        pj_vis = max(float(row_vis.get("PJ", 1)), 1.0)
        rend_vis = pts_vis / (pj_vis * 3.0)

        p_loc = rend_loc + 0.10
        p_vis = rend_vis
        total = p_loc + p_vis + 0.05

        prob_local = round((p_loc / total) * 100, 1)
        prob_vis = round((p_vis / total) * 100, 1)
        prob_empate = round(100.0 - prob_local - prob_vis, 1)

        st.markdown(f"#### 📊 Resultados: **{local}** vs **{visitante}**")
        
        m1, m2, m3 = st.columns(3)
        m1.metric(f"Gana {local}", f"{prob_local}%")
        m2.metric("Empate", f"{prob_empate}%")
        m3.metric(f"Gana {visitante}", f"{prob_vis}%")

    st.markdown("---")
    
    # ---------------------------------------------------------
    # SECCIÓN 2: TABLA ANUAL CON ESCUDOS
    # ---------------------------------------------------------
    st.subheader("⚽ Tabla Anual - Liga Profesional de Fútbol")

    cols_basicas = ["Equipo", "Puntos", "PJ", "PG", "PE", "PP", "GF", "GC"]
    cols_existentes = [c for c in cols_basicas if c in df.columns]
    
    df_tabla = df[cols_existentes].copy()
    
    # Asignación segura del escudo por fila
    df_tabla["Escudo"] = df_tabla["Equipo"].apply(obtener_escudo)
    
    # Ordenar por Puntos (el escudo se mueve junto con la fila)
    df_tabla = df_tabla.sort_values(by="Puntos", ascending=False).reset_index(drop=True)
    
    # Posicionar la columna Escudo al inicio
    columnas_ordenadas = ["Escudo"] + [c for c in df_tabla.columns if c != "Escudo"]
    df_tabla = df_tabla[columnas_ordenadas]

    # Renderizado seguro en Streamlit
    st.dataframe(
        df_tabla,
        hide_index=True, 
        column_config={
            "Escudo": st.column_config.ImageColumn("🛡️", width="small"),
            "Equipo": st.column_config.TextColumn("Equipo", width="medium"),
        },
        use_container_width=True
    )
