import streamlit as st
import pandas as pd
import unicodedata
import os
import re

# 1. Configuración de la página
st.set_page_config(page_title="Tabla Anual - LPF", layout="wide")
st.title("⚽ Tabla Anual - Liga Profesional")
st.markdown("---")

DIRECTORIO_APP = os.path.dirname(os.path.abspath(__file__))
RUTA_CSV = os.path.join(DIRECTORIO_APP, "datos_procesados.csv")

# =====================================================================
# 2. Diccionario de Corazones (Solución definitiva)
# =====================================================================
CORAZONES = {
    "boca": "💙💛💙",
    "river": "🤍❤️🤍",
    "racing": "🩵🤍🩵",
    "independiente": "❤️❤️❤️",
    "san lorenzo": "❤️💙❤️",
    "huracan": "🤍🤍🤍",
    "estudiantes": "❤️🤍❤️",
    "gimnasia": "💙🤍💙",
    "rosario central": "💙💛💙",
    "newells": "❤️🖤❤️",
    "talleres": "💙🤍💙",
    "belgrano": "🩵🩵🩵",
    "instituto": "❤️🤍❤️",
    "argentinos": "❤️❤️❤️",
    "velez": "🤍💙🤍",
    "lanus": "🤎🤎🤎",
    "banfield": "💚🤍💚",
    "defensa": "💛💚💛",
    "platense": "🤎🤍🤎",
    "tigre": "💙❤️💙",
    "union": "❤️🤍❤️",
    "godoy cruz": "💙🤍💙",
    "tucuman": "🩵🤍🩵",
    "central cordoba": "🖤🤍🖤",
    "sarmiento": "💚💚💚",
    "barracas": "❤️🤍❤️",
    "independiente rivadavia": "💙💙💙",
    "riestra": "🖤🤍🖤"
}

def limpiar_texto(texto):
    txt = str(texto).lower()
    txt = unicodedata.normalize('NFD', txt).encode('ascii', 'ignore').decode("utf-8")
    return re.sub(r'[^a-z\s]', '', txt).strip()

def obtener_corazones(nombre_equipo):
    equipo_limpio = limpiar_texto(nombre_equipo)
    for clave, emojis in CORAZONES.items():
        if clave in equipo_limpio:
            return emojis
    return "⚽" # Emoji por defecto si no encuentra el equipo

# =====================================================================
# 3. Carga de Datos y Visualización de la Tabla
# =====================================================================
if not os.path.exists(RUTA_CSV):
    st.error(f"⚠️ No se encontró el archivo '{RUTA_CSV}'.")
else:
    df = pd.read_csv(RUTA_CSV)
    
    # Limpiar nombres de los equipos
    df["Equipo"] = df["Equipo"].astype(str).apply(lambda x: re.sub(r'\[.*?\]|\(.*?\)', '', x).strip())
    
    # Asignar los emojis
    df["Colores"] = df["Equipo"].apply(obtener_corazones)
    
    # Mover la columna 'Colores' al principio
    cols = df.columns.tolist()
    if "Colores" in cols:
        cols.insert(0, cols.pop(cols.index("Colores")))
        df = df[cols]

    st.subheader("📊 Tabla de Posiciones")
    
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True
    )
    st.markdown("---")

    # =====================================================================
    # 4. Predictor de Enfrentamientos
    # =====================================================================
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
            corazon_loc = obtener_corazones(local)
            corazon_vis = obtener_corazones(visitante)

            c_loc, c_vs, c_vis = st.columns([2, 1, 2])
            
            with c_loc:
                st.markdown(f"<h1>{corazon_loc}</h1>", unsafe_allow_html=True)
                st.markdown(f"### **{local}**")
                
            with c_vs:
                st.markdown("<h1 style='text-align: center; margin-top: 20px;'>VS</h1>", unsafe_allow_html=True)
                
            with c_vis:
                st.markdown(f"<h1>{corazon_vis}</h1>", unsafe_allow_html=True)
                st.markdown(f"### **{visitante}**")

            # Cálculo Matemático
            row_loc = df[df["Equipo"] == local].iloc[0]
            row_vis = df[df["Equipo"] == visitante].iloc[0]

            pts_loc = float(row_loc.get("Puntos", 0)) if "Puntos" in df.columns else 0.0
            pts_vis = float(row_vis.get("Puntos", 0)) if "Puntos" in df.columns else 0.0
            pj_loc = max(float(row_loc.get("PJ", 1)), 1.0) if "PJ" in df.columns else 1.0
            pj_vis = max(float(row_vis.get("PJ", 1)), 1.0) if "PJ" in df.columns else 1.0

            # Ventaja del local (+15%)
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
