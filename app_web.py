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

    # DICCIONARIO DE ESCUDOS USANDO CDN DE ESPN (No se bloquean)
    escudos = {
        "Boca Juniors": "https://a.espncdn.com/i/teamlogos/soccer/500/5.png",
        "River Plate": "https://a.espncdn.com/i/teamlogos/soccer/500/16.png",
        "Racing Club": "https://a.espncdn.com/i/teamlogos/soccer/500/15.png",
        "Independiente": "https://a.espncdn.com/i/teamlogos/soccer/500/10.png",
        "San Lorenzo": "https://a.espncdn.com/i/teamlogos/soccer/500/18.png",
        "Vélez Sarsfield": "https://a.espncdn.com/i/teamlogos/soccer/500/21.png",
        "Estudiantes (LP)": "https://a.espncdn.com/i/teamlogos/soccer/500/8.png",
        "Rosario Central": "https://a.espncdn.com/i/teamlogos/soccer/500/17.png",
        "Newell's Old Boys": "https://a.espncdn.com/i/teamlogos/soccer/500/14.png",
        "Talleres (C)": "https://a.espncdn.com/i/teamlogos/soccer/500/3282.png",
        "Belgrano": "https://a.espncdn.com/i/teamlogos/soccer/500/2464.png",
        "Huracán": "https://a.espncdn.com/i/teamlogos/soccer/500/9.png",
        "Argentinos Juniors": "https://a.espncdn.com/i/teamlogos/soccer/500/2.png",
        "Lanús": "https://a.espncdn.com/i/teamlogos/soccer/500/12.png",
        "Banfield": "https://a.espncdn.com/i/teamlogos/soccer/500/4.png"
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
