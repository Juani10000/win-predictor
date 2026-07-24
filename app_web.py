import streamlit as st
import pandas as pd
import os
import re
import unicodedata

# 1. Configuración de la página
st.set_page_config(page_title="Tabla Anual & Predictor - LPF", layout="wide")
st.title("⚽ Tabla Anual & Predictor - Liga Profesional")
st.markdown("---")

# 2. DICCIONARIO INFALIBLE (EMOJIS)
# Como es texto nativo, Streamlit lo carga sí o sí, al instante.
EMOJIS_EQUIPOS = {
    "boca": "🔵🟡🔵",
    "river": "⚪🔴⚪",
    "racing": "🩵🤍🩵",
    "independiente": "🔴👹🔴",
    "san lorenzo": "🔴🔵🔴",
    "huracan": "⚪🎈⚪",
    "estudiantes": "🔴🦁🔴",
    "gimnasia": "🔵🐺🔵",
    "rosario central": "🟡🔵🟡",
    "newell": "🔴⚫🔴",
    "talleres": "🔵⚪🔵",
    "belgrano": "🩵🏴‍☠️🩵",
    "instituto": "🔴⚪🔴",
    "argentinos": "🔴🐞🔴",
    "velez": "⚪🔵⚪",
    "lanus": "🟤🧱🟤",
    "banfield": "🟩⬜🟩",
    "defensa": "🟡🟢🟡",
    "platense": "🟤⚪🟤",
    "tigre": "🔵🔴🔵",
    "union": "🔴⚪🔴",
    "godoy cruz": "🔵🍷🔵",
    "tucuman": "🩵🤍🩵",
    "central cordoba": "⚫⚪⚫",
    "sarmiento": "🟩🟢🟩",
    "barracas": "🔴⚪🔴",
    "riestra": "⚫⚡⚫",
    "independiente rivadavia": "🔵🟣🔵"
}

def normalizar_texto(txt):
    """Limpia tildes y caracteres especiales."""
    txt = str(txt).lower()
    txt = re.sub(r'\[.*?\]|\(.*?\)', '', txt)
    txt = unicodedata.normalize('NFD', txt).encode('ascii', 'ignore').decode("utf-8")
    return txt.strip()

def buscar_emoji(nombre_equipo):
    nombre_limpio = normalizar_texto(nombre_equipo)
    for clave, emoji in EMOJIS_EQUIPOS.items():
        if clave in nombre_limpio:
            return emoji
    return "⚽" # Si no encuentra, pone una pelota genérica

# =====================================================================
# 3. CARGA DE DATOS (TABLA DE POSICIONES)
# =====================================================================
DIRECTORIO_APP = os.path.dirname(os.path.abspath(__file__))
RUTA_CSV = os.path.join(DIRECTORIO_APP, "datos_procesados.csv")

if not os.path.exists(RUTA_CSV):
    RUTA_CSV = os.path.join(os.getcwd(), "datos_procesados.csv")

if os.path.exists(RUTA_CSV):
    df = pd.read_csv(RUTA_CSV)
    
    if "Equipo" in df.columns:
        df["Equipo"] = df["Equipo"].astype(str).apply(lambda x: re.sub(r'\[.*?\]|\(.*?\)', '', x).strip())

    st.subheader("📊 Tabla de Posiciones")
    st.dataframe(df, use_container_width=True, hide_index=True)
    st.markdown("---")

    # =====================================================================
    # 4. PREDICTOR DE ENFRENTAMIENTOS
    # =====================================================================
    st.subheader("🔮 Predictor de Enfrentamientos")
    
    lista_equipos = sorted(df["Equipo"].unique()) if "Equipo" in df.columns else []

    if len(lista_equipos) >= 2:
        col1, col2 = st.columns(2)
        with col1:
            local = st.selectbox("Equipo Local", lista_equipos, index=0)
        with col2:
            visitante = st.selectbox("Equipo Visitante", lista_equipos, index=min(1, len(lista_equipos)-1))

        if local == visitante:
            st.warning("Seleccioná dos equipos distintos.")
        else:
            emoji_loc = buscar_emoji(local)
            emoji_vis = buscar_emoji(visitante)

            c_loc, c_vs, c_vis = st.columns([2, 1, 2])
            
            with c_loc:
                # Mostramos los colores en tamaño gigante
                st.markdown(f"<h1 style='text-align: left; font-size: 60px;'>{emoji_loc}</h1>", unsafe_allow_html=True)
                st.markdown(f"### **{local}**")
                
            with c_vs:
                st.markdown("<h1 style='text-align: center; margin-top: 25px;'>VS</h1>", unsafe_allow_html=True)
                
            with c_vis:
                st.markdown(f"<h1 style='text-align: left; font-size: 60px;'>{emoji_vis}</h1>", unsafe_allow_html=True)
                st.markdown(f"### **{visitante}**")

            # Cálculo de Probabilidades
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
                prob_loc = (prom_loc / total) * 100
                prob_vis = (prom_vis / total) * 100
            else:
                prob_loc, prob_vis = 50.0, 50.0

            st.markdown("#### **Probabilidades de Victoria**")
            p1, p2 = st.columns(2)
            p1.metric(f"{local} (Local)", f"{prob_loc:.1f}%")
            p2.metric(f"{visitante} (Visitante)", f"{prob_vis:.1f}%")
            st.progress(int(prob_loc))
else:
    st.error("⚠️ No se encontró el archivo 'datos_procesados.csv'. Verificá que esté en la misma carpeta.")
