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

        # Lógica matemática básica de predicción
        pts_loc = float(row_loc.get("Puntos", 0))
        pj_loc = max(float(row_loc.get("PJ", 1)), 1.0)
        rend_loc = pts_loc / (pj_loc * 3.0)

        pts_vis = float(row_vis.get("Puntos", 0))
        pj_vis = max(float(row_vis.get("PJ", 1)), 1.0)
        rend_vis = pts_vis / (pj_vis * 3.0)

        p_loc = rend_loc + 0.10  # Bonificación por localía
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
    
    # Título oficial con Logo de la LPF
    col_logo, col_titulo = st.columns([1, 6])
    with col_logo:
        # Link al logo oficial de la Liga Profesional
        logo_lpf = "https://upload.wikimedia.org/wikipedia/en/thumb/9/94/Liga_Profesional_de_F%C3%BAtbol_%28Argentina%29_logo.svg/200px-Liga_Profesional_de_F%C3%BAtbol_%28Argentina%29_logo.svg.png"
        st.image(logo_lpf, width=60)
    with col_titulo:
        st.subheader("Tabla Anual - Liga Profesional de Fútbol")

    # DICCIONARIO DE ESCUDOS (Acá podés ir agregando los que faltan buscando el logo en Wikipedia)
    escudos = {
        "Independiente Rivadavia": "https://upload.wikimedia.org/wikipedia/commons/thumb/f/fa/Escudo_del_Club_Sportivo_Independiente_Rivadavia.svg/100px-Escudo_del_Club_Sportivo_Independiente_Rivadavia.svg.png",
        "Boca Juniors": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/cf/Boca_Juniors_logo_2012.svg/100px-Boca_Juniors_logo_2012.svg.png",
        "River Plate": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3f/Logo_River_Plate_2022.png/100px-Logo_River_Plate_2022.png",
        "Racing Club": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/13/Racing_Club_logo.svg/100px-Racing_Club_logo.svg.png",
        "Independiente": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d6/Club_Atl%C3%A9tico_Independiente_logo.svg/100px-Club_Atl%C3%A9tico_Independiente_logo.svg.png",
        "San Lorenzo": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/17/Escudo_del_Club_Atl%C3%A9tico_San_Lorenzo_de_Almagro.svg/100px-Escudo_del_Club_Atl%C3%A9tico_San_Lorenzo_de_Almagro.svg.png",
        "Estudiantes (LP)": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/38/Escudo_de_Estudiantes_de_La_Plata.svg/100px-Escudo_de_Estudiantes_de_La_Plata.svg.png",
        "Rosario Central": "https://upload.wikimedia.org/wikipedia/commons/thumb/9/91/Escudo_del_Club_Atl%C3%A9tico_Rosario_Central.svg/100px-Escudo_del_Club_Atl%C3%A9tico_Rosario_Central.svg.png",
        "Belgrano": "https://upload.wikimedia.org/wikipedia/commons/thumb/7/7b/Club_Atl%C3%A9tico_Belgrano_logo.svg/100px-Club_Atl%C3%A9tico_Belgrano_logo.svg.png",
        "Vélez Sarsfield": "https://upload.wikimedia.org/wikipedia/commons/thumb/9/97/Escudo_del_Club_Atl%C3%A9tico_V%C3%A9lez_Sarsfield.svg/100px-Escudo_del_Club_Atl%C3%A9tico_V%C3%A9lez_Sarsfield.svg.png",
        "Argentinos Juniors": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/1c/Escudo_de_la_Asociaci%C3%B3n_Atl%C3%A9tica_Argentinos_Juniors.svg/100px-Escudo_de_la_Asociaci%C3%B3n_Atl%C3%A9tica_Argentinos_Juniors.svg.png"
    }
    
    # Imagen genérica para los equipos que aún no agregaste al diccionario
    escudo_generico = "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d3/Soccerball.svg/100px-Soccerball.svg.png"

    # Preparamos la tabla para mostrar
    cols_basicas = ["Equipo", "Puntos", "PJ", "PG", "PE", "PP", "GF", "GC"]
    cols_existentes = [c for c in cols_basicas if c in df.columns]
    
    df_mostrar = df[cols_existentes].sort_values(by="Puntos", ascending=False).copy()
    
    # Agregamos la columna de los escudos usando el diccionario
    df_mostrar.insert(0, "🛡️", df_mostrar["Equipo"].apply(lambda eq: escudos.get(eq, escudo_generico)))

    # Mostramos la tabla configurando la columna como imagen y ocultando el índice (los números)
    st.dataframe(
        df_mostrar,
        hide_index=True, 
        column_config={
            "🛡️": st.column_config.ImageColumn("🛡️", help="Escudo"),
        },
        use_container_width=True
    )
