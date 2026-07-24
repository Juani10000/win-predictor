import streamlit as st
import pandas as pd
import os
import re

# =====================================================================
# 1. CONFIGURACIÓN DE PÁGINA (MODO SERIO)
# =====================================================================
st.set_page_config(page_title="Win Predictor | LPF", layout="wide", initial_sidebar_state="collapsed")

# Inyectamos CSS para darle estilo oscuro, limpio y profesional (sin emojis)
st.markdown("""
    <style>
        /* Estilos generales */
        body, .stApp {
            background-color: #0E1117;
            font-family: 'Inter', sans-serif;
        }
        /* Títulos */
        h1, h2, h3 {
            color: #F8F9FA !important;
            font-weight: 700 !important;
            letter-spacing: -0.5px;
        }
        /* Métrica de resultados */
        [data-testid="stMetricValue"] {
            font-size: 32px !important;
            font-weight: 800 !important;
            color: #E2E8F0 !important;
        }
        /* Línea separadora */
        hr {
            border-color: #334155 !important;
            margin-top: 10px;
            margin-bottom: 30px;
        }
        /* Contenedores de alerta */
        .stAlert {
            border-radius: 8px;
            border: 1px solid #334155;
            background-color: #1E293B;
            color: #CBD5E1;
        }
    </style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------
# ENCABEZADO CON IMAGEN BANNER Y LOGO
# ---------------------------------------------------------------------
# Banner de estadio de fondo (imagen cinemática de cancha)
url_banner = "http://googleusercontent.com/image_collection/image_retrieval/913811032378318840_0"
st.image(url_banner, use_container_width=True)

col_logo, col_titulo = st.columns([1, 8])
with col_logo:
    # URL directa de ESPN que no bloquea la imagen
    url_lpf = "https://a.espncdn.com/combiner/i?img=/i/leaguelogos/soccer/500/1.png"
    st.image(url_lpf, width=90)

with col_titulo:
    st.markdown("<h1 style='margin-bottom: 0; padding-bottom: 0;'>WIN PREDICTOR | LPF</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color: #94A3B8; font-size: 18px; margin-top: 0;'>Modelo Analítico de Probabilidades - Liga Profesional Argentina</p>", unsafe_allow_html=True)

st.markdown("---")

# =====================================================================
# 2. CARGA DE DATOS DESDE EL CSV
# =====================================================================
DIRECTORIO_APP = os.path.dirname(os.path.abspath(__file__))
RUTA_CSV = os.path.join(DIRECTORIO_APP, "datos_procesados.csv")

if not os.path.exists(RUTA_CSV):
    RUTA_CSV = os.path.join(DIRECTORIO_APP, "datos", "datos_procesados.csv")

if os.path.exists(RUTA_CSV):
    df = pd.read_csv(RUTA_CSV)
    
    if "Equipo" in df.columns:
        df["Equipo"] = df["Equipo"].astype(str).apply(lambda x: re.sub(r'\[.*?\]|\(.*?\)', '', x).strip())

    # -----------------------------------------------------------------
    # 3. TABLA DE POSICIONES 
    # -----------------------------------------------------------------
    st.subheader("Clasificación General")
    st.dataframe(df, use_container_width=True, hide_index=True)
    st.markdown("---")

    # -----------------------------------------------------------------
    # 4. PREDICTOR DE ENFRENTAMIENTOS (LOCAL / EMPATE / VISITANTE)
    # -----------------------------------------------------------------
    st.subheader("Proyección de Enfrentamiento")
    st.markdown("<p style='color: #64748B;'>Seleccione las escuadras para calcular la distribución de probabilidades.</p>", unsafe_allow_html=True)
    
    lista_equipos = sorted(df["Equipo"].unique()) if "Equipo" in df.columns else []

    if len(lista_equipos) >= 2:
        col1, col2 = st.columns(2)
        with col1:
            local = st.selectbox("Condición: Local", lista_equipos, index=0)
        with col2:
            visitante = st.selectbox("Condición: Visitante", lista_equipos, index=min(1, len(lista_equipos)-1))

        if local == visitante:
            st.error("Error de selección: El equipo local y visitante no pueden ser el mismo.")
        else:
            # Cálculos de probabilidad
            row_loc = df[df["Equipo"] == local].iloc[0]
            row_vis = df[df["Equipo"] == visitante].iloc[0]

            pts_loc = float(row_loc.get("Puntos", 0)) if "Puntos" in df.columns else 0.0
            pts_vis = float(row_vis.get("Puntos", 0)) if "Puntos" in df.columns else 0.0
            pj_loc = max(float(row_loc.get("PJ", 1)), 1.0) if "PJ" in df.columns else 1.0
            pj_vis = max(float(row_vis.get("PJ", 1)), 1.0) if "PJ" in df.columns else 1.0

            # Ventaja estadística de localía (12%)
            prom_loc = (pts_loc / pj_loc) * 1.12
            prom_vis = (pts_vis / pj_vis)

            # Probabilidad de Empate
            diferencia = abs(prom_loc - prom_vis)
            prob_empate = max(18.0, min(33.0, 29.0 - (diferencia * 7.5)))

            # Reparto de las victorias
            resto = 100.0 - prob_empate
            total_prom = prom_loc + prom_vis

            if total_prom > 0:
                prob_loc = (prom_loc / total_prom) * resto
                prob_vis = (prom_vis / total_prom) * resto
            else:
                prob_loc = resto / 2
                prob_vis = resto / 2

            # Presentación visual del análisis
            st.markdown(f"<h3 style='text-align: center; margin-top: 30px; margin-bottom: 20px; color: #E2E8F0;'>{local.upper()} vs {visitante.upper()}</h3>", unsafe_allow_html=True)
            
            # Métricas en cajas
            m1, m2, m3 = st.columns(3)
            with m1:
                st.metric(label=f"Victoria Local", value=f"{prob_loc:.1f}%")
            with m2:
                st.metric(label="Empate", value=f"{prob_empate:.1f}%")
            with m3:
                st.metric(label=f"Victoria Visitante", value=f"{prob_vis:.1f}%")

            # Barra visual de proporción 
            st.markdown("<p style='color: #94A3B8; font-size: 14px; margin-top: 30px; margin-bottom: 5px;'>Distribución de Probabilidad del Modelo</p>", unsafe_allow_html=True)
            
            # Usamos los colores de éxito (verde), advertencia (amarillo) y error (rojo) de streamlit pero sin emojis
            c_loc, c_emp, c_vis = st.columns([max(1, int(prob_loc)), max(1, int(prob_empate)), max(1, int(prob_vis))])
            with c_loc:
                st.success(f"LOCAL: {prob_loc:.1f}%")
            with c_emp:
                st.warning(f"EMPATE: {prob_empate:.1f}%")
            with c_vis:
                st.error(f"VISITANTE: {prob_vis:.1f}%")

else:
    st.error("Archivo de origen no encontrado. Verifique que 'datos_procesados.csv' exista en el directorio raíz o en '/datos'.")
