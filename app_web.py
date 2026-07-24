import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Win Predictor - LPF", page_icon="⚽", layout="centered")

st.title("⚽ Win Predictor - Fútbol Argentino 2026")

@st.cache_data(ttl=60)
def cargar_datos():
    if os.path.exists("datos_procesados.csv"):
        return pd.read_csv("datos_procesados.csv")
    return None

df = cargar_datos()

if df is None or df.empty:
    st.error("❌ No se encontraron datos procesados. Por favor ejecutá la actualización en GitHub.")
else:
    st.markdown("### 🔮 Predicción de Partido")
    st.caption("Cálculo de probabilidades basado en el rendimiento actual.")
    
    lista_equipos = sorted(df["Equipo"].unique())
    
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
    
    # Título con el Logo Oficial de la AFA / LPF usando un servidor estable
    col_logo, col_titulo = st.columns([1, 6])
    with col_logo:
        logo_lpf = "https://a.espncdn.com/i/leaguelogos/soccer/500/1.png" # Logo Liga Argentina en ESPN
        st.image(logo_lpf, width=60)
    with col_titulo:
        st.subheader("Tabla Anual - Liga Profesional de Fútbol")

    # DICCIONARIO COMPLETO CON LOS 30 EQUIPOS 
    escudos = {
        "Independiente Rivadavia": "https://upload.wikimedia.org/wikipedia/commons/thumb/f/fa/Escudo_del_Club_Sportivo_Independiente_Rivadavia.svg/100px-Escudo_del_Club_Sportivo_Independiente_Rivadavia.svg.png",
        "Argentinos Juniors": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/1c/Escudo_de_la_Asociaci%C3%B3n_Atl%C3%A9tica_Argentinos_Juniors.svg/100px-Escudo_de_la_Asociaci%C3%B3n_Atl%C3%A9tica_Argentinos_Juniors.svg.png",
        "Estudiantes (LP)": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/38/Escudo_de_Estudiantes_de_La_Plata.svg/100px-Escudo_de_Estudiantes_de_La_Plata.svg.png",
        "Boca Juniors": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/cf/Boca_Juniors_logo_2012.svg/100px-Boca_Juniors_logo_2012.svg.png",
        "River Plate": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3f/Logo_River_Plate_2022.png/100px-Logo_River_Plate_2022.png",
        "Belgrano": "https://upload.wikimedia.org/wikipedia/commons/thumb/7/7b/Club_Atl%C3%A9tico_Belgrano_logo.svg/100px-Club_Atl%C3%A9tico_Belgrano_logo.svg.png",
        "Vélez Sarsfield": "https://upload.wikimedia.org/wikipedia/commons/thumb/9/97/Escudo_del_Club_Atl%C3%A9tico_V%C3%A9lez_Sarsfield.svg/100px-Escudo_del_Club_Atl%C3%A9tico_V%C3%A9lez_Sarsfield.svg.png",
        "Rosario Central": "https://upload.wikimedia.org/wikipedia/commons/thumb/9/91/Escudo_del_Club_Atl%C3%A9tico_Rosario_Central.svg/100px-Escudo_del_Club_Atl%C3%A9tico_Rosario_Central.svg.png",
        "Talleres (C)": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/14/Club_Atl%C3%A9tico_Talleres_logo.svg/100px-Club_Atl%C3%A9tico_Talleres_logo.svg.png",
        "Gimnasia (LP)": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4c/Escudo_del_Club_de_Gimnasia_y_Esgrima_La_Plata.svg/100px-Escudo_del_Club_de_Gimnasia_y_Esgrima_La_Plata.svg.png",
        "Independiente": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d6/Club_Atl%C3%A9tico_Independiente_logo.svg/100px-Club_Atl%C3%A9tico_Independiente_logo.svg.png",
        "Lanús": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/18/Escudo_del_Club_Atl%C3%A9tico_Lan%C3%BAs.svg/100px-Escudo_del_Club_Atl%C3%A9tico_Lan%C3%BAs.svg.png",
        "Huracán": "https://upload.wikimedia.org/wikipedia/commons/thumb/7/74/Escudo_del_Club_Atl%C3%A9tico_Hurac%C3%A1n.svg/100px-Escudo_del_Club_Atl%C3%A9tico_Hurac%C3%A1n.svg.png",
        "San Lorenzo": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/17/Escudo_del_Club_Atl%C3%A9tico_San_Lorenzo_de_Almagro.svg/100px-Escudo_del_Club_Atl%C3%A9tico_San_Lorenzo_de_Almagro.svg.png",
        "Unión": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/ab/Escudo_del_Club_Atl%C3%A9tico_Uni%C3%B3n_de_Santa_Fe.svg/100px-Escudo_del_Club_Atl%C3%A9tico_Uni%C3%B3n_de_Santa_Fe.svg.png",
        "Racing Club": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/13/Racing_Club_logo.svg/100px-Racing_Club_logo.svg.png",
        "Instituto": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/36/Escudo_del_Instituto_Atl%C3%A9tico_Central_C%C3%B3rdoba.svg/100px-Escudo_del_Instituto_Atl%C3%A9tico_Central_C%C3%B3rdoba.svg.png",
        "Barracas Central": "https://upload.wikimedia.org/wikipedia/commons/thumb/6/60/Escudo_del_Club_Atl%C3%A9tico_Barracas_Central.svg/100px-Escudo_del_Club_Atl%C3%A9tico_Barracas_Central.svg.png",
        "Tigre": "https://upload.wikimedia.org/wikipedia/commons/thumb/6/61/Escudo_del_Club_Atl%C3%A9tico_Tigre.svg/100px-Escudo_del_Club_Atl%C3%A9tico_Tigre.svg.png",
        "Defensa y Justicia": "https://upload.wikimedia.org/wikipedia/commons/thumb/5/52/Escudo_del_Club_Social_y_Deportivo_Defensa_y_Justicia.svg/100px-Escudo_del_Club_Social_y_Deportivo_Defensa_y_Justicia.svg.png",
        "Sarmiento (J)": "https://upload.wikimedia.org/wikipedia/commons/thumb/9/91/Escudo_del_Club_Atl%C3%A9tico_Sarmiento_de_Jun%C3%ADn.svg/100px-Escudo_del_Club_Atl%C3%A9tico_Sarmiento_de_Jun%C3%ADn.svg.png",
        "Gimnasia (Mendoza)": "https://upload.wikimedia.org/wikipedia/commons/thumb/9/90/Escudo_del_Club_Atl%C3%A9tico_Gimnasia_y_Esgrima_de_Mendoza.svg/100px-Escudo_del_Club_Atl%C3%A9tico_Gimnasia_y_Esgrima_de_Mendoza.svg.png",
        "Banfield": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/87/Escudo_del_Club_Atl%C3%A9tico_Banfield.svg/100px-Escudo_del_Club_Atl%C3%A9tico_Banfield.svg.png",
        "Platense": "https://upload.wikimedia.org/wikipedia/commons/thumb/7/7b/Escudo_del_Club_Atl%C3%A9tico_Platense.svg/100px-Escudo_del_Club_Atl%C3%A9tico_Platense.svg.png",
        "Central Córdoba (SdE)": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/ca/Escudo_del_Club_Atl%C3%A9tico_Central_C%C3%B3rdoba_de_Santiago_del_Estero.svg/100px-Escudo_del_Club_Atl%C3%A9tico_Central_C%C3%B3rdoba_de_Santiago_del_Estero.svg.png",
        "Newell's Old Boys": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/30/Escudo_del_Club_Atl%C3%A9tico_Newell%27s_Old_Boys.svg/100px-Escudo_del_Club_Atl%C3%A9tico_Newell%27s_Old_Boys.svg.png",
        "Atlético Tucumán": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/37/Escudo_del_Club_Atl%C3%A9tico_Tucum%C3%A1n.svg/100px-Escudo_del_Club_Atl%C3%A9tico_Tucum%C3%A1n.svg.png",
        "Deportivo Riestra": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/88/Escudo_del_Deportivo_Riestra_Asociaci%C3%B3n_de_Fomento_Barrio_Col%C3%B3n.svg/100px-Escudo_del_Deportivo_Riestra_Asociaci%C3%B3n_de_Fomento_Barrio_Col%C3%B3n.svg.png",
        "Aldosivi": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/1a/Escudo_del_Club_Atl%C3%A9tico_Aldosivi.svg/100px-Escudo_del_Club_Atl%C3%A9tico_Aldosivi.svg.png",
        "Estudiantes (RC)": "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e5/Escudo_de_la_Asociaci%C3%B3n_Atl%C3%A9tica_Estudiantes_de_R%C3%ADo_Cuarto.svg/100px-Escudo_de_la_Asociaci%C3%B3n_Atl%C3%A9tica_Estudiantes_de_R%C3%ADo_Cuarto.svg.png"
    }
    
    # Imagen genérica (una pelota) por si falta agregar el escudo de algún equipo
    escudo_generico = "https://a.espncdn.com/i/leaguelogos/soccer/500/default.png"

    cols_basicas = ["Equipo", "Puntos", "PJ", "PG", "PE", "PP", "GF", "GC"]
    cols_existentes = [c for c in cols_basicas if c in df.columns]
    
    df_mostrar = df[cols_existentes].sort_values(by="Puntos", ascending=False).copy()
    
    # Inyectamos la URL del escudo
    df_mostrar.insert(0, "🛡️", df_mostrar["Equipo"].apply(lambda eq: escudos.get(eq, escudo_generico)))

    # Mostramos la tabla (las URLs se renderizan como imágenes automáticamente)
    st.dataframe(
        df_mostrar,
        hide_index=True, 
        column_config={
            "🛡️": st.column_config.ImageColumn("🛡️", help="Escudo"),
        },
        use_container_width=True
    )
