import streamlit as st
import pandas as pd
import unicodedata
import os
import re

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Tabla Anual - LPF", layout="wide")
st.title("⚽ Tabla Anual - Liga Profesional")
st.markdown("---")

# 2. DICCIONARIO DE ESCUDOS (URLs directas, cero fallas)
ESCUDOS_URL = {
    "boca": "https://a.espncdn.com/i/teamlogos/soccer/500/5.png",
    "river": "https://a.espncdn.com/i/teamlogos/soccer/500/16.png",
    "racing": "https://a.espncdn.com/i/teamlogos/soccer/500/15.png",
    "independiente": "https://a.espncdn.com/i/teamlogos/soccer/500/11.png",
    "san lorenzo": "https://a.espncdn.com/i/teamlogos/soccer/500/17.png",
    "estudiantes": "https://a.espncdn.com/i/teamlogos/soccer/500/10.png",
    "velez": "https://a.espncdn.com/i/teamlogos/soccer/500/18.png",
    "gimnasia": "https://a.espncdn.com/i/teamlogos/soccer/500/14.png",
    "talleres": "https://a.espncdn.com/i/teamlogos/soccer/500/8051.png",
    "belgrano": "https://a.espncdn.com/i/teamlogos/soccer/500/6.png",
    "rosario": "https://a.espncdn.com/i/teamlogos/soccer/500/13.png",
    "newell": "https://a.espncdn.com/i/teamlogos/soccer/500/12.png",
    "lanus": "https://a.espncdn.com/i/teamlogos/soccer/500/2753.png",
    "argentinos": "https://a.espncdn.com/i/teamlogos/soccer/500/2.png",
    "huracan": "https://a.espncdn.com/i/teamlogos/soccer/500/2070.png",
}
# Un escudo genérico por si algún equipo (ej: Riestra) no está en la lista de arriba
URL_POR_DEFECTO = "https://cdn-icons-png.flaticon.com/512/825/825590.png"

def obtener_url_escudo(nombre_equipo):
    nombre_limpio = unicodedata.normalize('NFD', str(nombre_equipo)).encode('ascii', 'ignore').decode("utf-8").lower()
    for clave, url in ESCUDOS_URL.items():
        if clave in nombre_limpio:
            return url
    return URL_POR_DEFECTO

# 3. CARGA DEL CSV Y LA TABLA
if not os.path.exists("datos_procesados.csv"):
    st.error("⚠️ No se encontró 'datos_procesados.csv'.")
else:
    df = pd.read_csv("datos_procesados.csv")
    
    # Limpiar nombres de equipo
    df["Equipo"] = df["Equipo"].astype(str).str.replace(r'\[.*?\]|\(.*?\)', '', regex=True).str.strip()
    
    # Agregar la columna de la foto
    df["Escudo"] = df["Equipo"].apply(obtener_url_escudo)
    
    # Mover la columna "Escudo" al principio de la tabla
    cols = df.columns.tolist()
    cols.insert(0, cols.pop(cols.index("Escudo")))
    df = df[cols]

    st.subheader("📊 Tabla de Posiciones")
    
    # ACÁ ESTÁ LA MAGIA: Le decimos a Streamlit que renderice la columna como imagen
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Escudo": st.column_config.ImageColumn("🛡️", help="Escudo")
        }
    )
    st.markdown("---")

    # 4. PREDICTOR DE ENFRENTAMIENTOS
    st.subheader("🔮 Predictor de Enfrentamientos")
    lista_equipos = sorted(df["Equipo"].unique())

    if len(lista_equipos) >= 2:
        col1, col2 = st.columns(2)
        with col1:
            local = st.selectbox("Equipo Local", lista_equipos, index=0)
        with col2:
            visitante = st.selectbox("Equipo Visitante", lista_equipos, index=min(1, len(lista_equipos)-1))

        if local == visitante:
            st.warning("Seleccioná dos equipos distintos.")
        else:
            url_loc = obtener_url_escudo(local)
            url_vis = obtener_url_escudo(visitante)

            c_loc, c_vs, c_vis = st.columns([2, 1, 2])
            
            with c_loc:
                st.image(url_loc, width=120)
                st.markdown(f"### {local}")
                
            with c_vs:
                st.markdown("<h1 style='text-align: center; margin-top: 30px;'>VS</h1>", unsafe_allow_html=True)
                
            with c_vis:
                st.image(url_vis, width=120)
                st.markdown(f"### {visitante}")

            # Matemáticas
            row_loc = df[df["Equipo"] == local].iloc[0]
            row_vis = df[df["Equipo"] == visitante].iloc[0]

            pts_loc = float(row_loc.get("Puntos", 0)) if "Puntos" in df.columns else 0.0
            pts_vis = float(row_vis.get("Puntos", 0)) if "Puntos" in df.columns else 0.0
            pj_loc = max(float(row_loc.get("PJ", 1)), 1.0) if "PJ" in df.columns else 1.0
            pj_vis = max(float(row_vis.get("PJ", 1)), 1.0) if "PJ" in df.columns else 1.0

            prom_loc = (pts_loc / pj_loc) * 1.15
            prom_vis = pts_vis / pj_vis
            total = prom_loc + prom_vis

            if total > 0:
                prob_loc, prob_vis = (prom_loc / total) * 100, (prom_vis / total) * 100
            else:
                prob_loc, prob_vis = 50.0, 50.0

            st.markdown("#### **Probabilidades**")
            p1, p2 = st.columns(2)
            p1.metric(f"{local} (Local)", f"{prob_loc:.1f}%")
            p2.metric(f"{visitante} (Visitante)", f"{prob_vis:.1f}%")
            st.progress(int(prob_loc))
