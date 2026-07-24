import streamlit as st
import pandas as pd
import os
import re
import requests
from io import BytesIO
from PIL import Image

# =====================================================================
# 1. CONFIGURACIÓN DE PÁGINA Y ENCABEZADO CON LOGO DE LA LPF
# =====================================================================
st.set_page_config(page_title="Win Predictor - LPF Argentina", layout="wide")

col_logo, col_titulo = st.columns([1, 6])

with col_logo:
    # TRUCO DEFINITIVO: Python descarga la imagen en memoria y la muestra
    try:
        url_logo = "https://upload.wikimedia.org/wikipedia/commons/d/d4/Logo_de_la_Liga_Profesional_de_F%C3%BAtbol.png"
        respuesta = requests.get(url_logo, timeout=5)
        imagen_logo = Image.open(BytesIO(respuesta.content))
        st.image(imagen_logo, width=110)
    except Exception:
        # Si algo falla (sin internet, antivirus, etc.), pone un emoji para no romper la app
        st.markdown("<h1 style='font-size: 60px;'>⚽</h1>", unsafe_allow_html=True)

with col_titulo:
    st.title("⚽ Win Predictor - Liga Profesional Argentina")
    st.markdown("**Tabla Anual & Predictor de Partidos (Local / Empate / Visitante)**")

st.markdown("---")

# =====================================================================
# 2. CARGA DE DATOS DESDE EL CSV
# =====================================================================
DIRECTORIO_APP = os.path.dirname(os.path.abspath(__file__))
RUTA_CSV = os.path.join(DIRECTORIO_APP, "datos_procesados.csv")

# Si no está en la raíz, busca dentro de la carpeta 'datos'
if not os.path.exists(RUTA_CSV):
    RUTA_CSV = os.path.join(DIRECTORIO_APP, "datos", "datos_procesados.csv")

if os.path.exists(RUTA_CSV):
    df = pd.read_csv(RUTA_CSV)
    
    if "Equipo" in df.columns:
        df["Equipo"] = df["Equipo"].astype(str).apply(lambda x: re.sub(r'\[.*?\]|\(.*?\)', '', x).strip())

    # -----------------------------------------------------------------
    # 3. TABLA DE POSICIONES
    # -----------------------------------------------------------------
    st.subheader("📊 Tabla de Posiciones")
    st.dataframe(df, use_container_width=True, hide_index=True)
    st.markdown("---")

    # -----------------------------------------------------------------
    # 4. PREDICTOR DE ENFRENTAMIENTOS (LOCAL / EMPATE / VISITANTE)
    # -----------------------------------------------------------------
    st.subheader("🔮 Predictor de Enfrentamientos")
    
    lista_equipos = sorted(df["Equipo"].unique()) if "Equipo" in df.columns else []

    if len(lista_equipos) >= 2:
        col1, col2 = st.columns(2)
        with col1:
            local = st.selectbox("🏠 Equipo Local", lista_equipos, index=0)
        with col2:
            visitante = st.selectbox("✈️ Equipo Visitante", lista_equipos, index=min(1, len(lista_equipos)-1))

        if local == visitante:
            st.warning("⚠️ Seleccioná dos equipos distintos.")
        else:
            # Obtención de datos por equipo
            row_loc = df[df["Equipo"] == local].iloc[0]
            row_vis = df[df["Equipo"] == visitante].iloc[0]

            pts_loc = float(row_loc.get("Puntos", 0)) if "Puntos" in df.columns else 0.0
            pts_vis = float(row_vis.get("Puntos", 0)) if "Puntos" in df.columns else 0.0
            pj_loc = max(float(row_loc.get("PJ", 1)), 1.0) if "PJ" in df.columns else 1.0
            pj_vis = max(float(row_vis.get("PJ", 1)), 1.0) if "PJ" in df.columns else 1.0

            # Promedio de puntos (+12% de ventaja por localía)
            prom_loc = (pts_loc / pj_loc) * 1.12
            prom_vis = (pts_vis / pj_vis)

            # Cálculo de la probabilidad de empate según la paridad entre equipos
            diferencia = abs(prom_loc - prom_vis)
            prob_empate = max(18.0, min(33.0, 29.0 - (diferencia * 7.5)))

            # Distribución del porcentaje restante
            resto = 100.0 - prob_empate
            total_prom = prom_loc + prom_vis

            if total_prom > 0:
                prob_loc = (prom_loc / total_prom) * resto
                prob_vis = (prom_vis / total_prom) * resto
            else:
                prob_loc = resto / 2
                prob_vis = resto / 2

            # Presentación de resultados
            st.markdown(f"### **{local}** vs **{visitante}**")
            st.markdown("#### **Probabilidades del Partido**")

            # Tarjetas numéricas
            m1, m2, m3 = st.columns(3)
            m1.metric(f"Victoria {local}", f"{prob_loc:.1f}%")
            m2.metric("Empate", f"{prob_empate:.1f}%")
            m3.metric(f"Victoria {visitante}", f"{prob_vis:.1f}%")

            # Barras comparativas
            st.markdown("**Distribución visual:**")
            col_b1, col_b2, col_b3 = st.columns([max(1, int(prob_loc)), max(1, int(prob_empate)), max(1, int(prob_vis))])
            with col_b1:
                st.info(f"Local: {prob_loc:.1f}%")
            with col_b2:
                st.warning(f"Empate: {prob_empate:.1f}%")
            with col_b3:
                st.error(f"Visitante: {prob_vis:.1f}%")

else:
    st.error("⚠️ No se encontró el archivo 'datos_procesados.csv'. Verificá que esté guardado en la carpeta del programa o en la subcarpeta 'datos'.")
