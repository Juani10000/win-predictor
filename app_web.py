import streamlit as st
import pandas as pd
import os
import re

# =====================================================================
# 1. CONFIGURACIÓN DE PÁGINA Y ESTILO SERIO (MODO OSCURO NEÓN)
# =====================================================================
st.set_page_config(page_title="Win Predictor | LPF", layout="wide")

st.markdown("""
    <style>
        .stApp {
            background-color: #070b14;
            color: #e2e8f0;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
        .neon-title {
            font-size: 44px;
            font-weight: 900;
            text-align: left;
            color: #ffffff;
            text-shadow: 0 0 10px #00f3ff, 0 0 20px #00f3ff, 0 0 30px #00f3ff;
            margin-bottom: 5px;
            text-transform: uppercase;
        }
        .tech-sub {
            text-align: left;
            color: #94a3b8;
            letter-spacing: 2px;
            font-size: 15px;
            margin-bottom: 25px;
        }
        [data-testid="stMetricValue"] {
            color: #00ffcc !important;
            font-size: 36px !important;
            font-weight: 900 !important;
            text-shadow: 0 0 5px #00ffcc80;
        }
        [data-testid="stMetricLabel"] {
            color: #94a3b8 !important;
            font-size: 14px !important;
            text-transform: uppercase;
        }
        hr {
            border-top: 1px solid #1e293b;
        }
    </style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------
# ENCABEZADO CON LOGO
# ---------------------------------------------------------------------
col_logo, col_titulo = st.columns([1, 6])
with col_logo:
    url_lpf = "https://a.espncdn.com/combiner/i?img=/i/leaguelogos/soccer/500/1.png"
    st.image(url_lpf, width=110)

with col_titulo:
    st.markdown('<div class="neon-title">Win Predictor LPF</div>', unsafe_allow_html=True)
    st.markdown('<div class="tech-sub">TABLA DE POSICIONES, FIXTURE POR JORNADA & PREDICCIÓN</div>', unsafe_allow_html=True)

st.markdown("---")

# =====================================================================
# 2. CARGA DE DATOS (POSICIONES Y FIXTURE DE JORNADAS)
# =====================================================================
DIRECTORIO_APP = os.path.dirname(os.path.abspath(__file__))
RUTA_CSV = os.path.join(DIRECTORIO_APP, "datos_procesados.csv")
RUTA_FIXTURE_CSV = os.path.join(DIRECTORIO_APP, "fixture_jornadas.csv")

if not os.path.exists(RUTA_CSV):
    RUTA_CSV = os.path.join(DIRECTORIO_APP, "datos", "datos_procesados.csv")

if os.path.exists(RUTA_CSV):
    df_posiciones = pd.read_csv(RUTA_CSV)
    
    if "Equipo" in df_posiciones.columns:
        df_posiciones["Equipo"] = df_posiciones["Equipo"].astype(str).apply(lambda x: re.sub(r'\[.*?\]|\(.*?\)', '', x).strip())

    # Cargar o generar dataset de fixture por jornada
    if os.path.exists(RUTA_FIXTURE_CSV):
        df_fixture = pd.read_csv(RUTA_FIXTURE_CSV)
    else:
        # Estructura base de ejemplo con varias jornadas
        partidos_demo = [
            # Jornada 12
            {"Jornada": "Jornada 12", "Local": "River Plate", "GL": 2, "GV": 0, "Visitante": "Boca Juniors", "Estado": "Finalizado"},
            {"Jornada": "Jornada 12", "Local": "Racing Club", "GL": 1, "GV": 1, "Visitante": "Independiente", "Estado": "Finalizado"},
            {"Jornada": "Jornada 12", "Local": "San Lorenzo", "GL": 0, "GV": 1, "Visitante": "Vélez Sarsfield", "Estado": "Finalizado"},
            {"Jornada": "Jornada 12", "Local": "Estudiantes", "GL": 3, "GV": 1, "Visitante": "Gimnasia LP", "Estado": "Finalizado"},
            {"Jornada": "Jornada 12", "Local": "Talleres", "GL": 2, "GV": 2, "Visitante": "Belgrano", "Estado": "Finalizado"},

            # Jornada 13 (Jornada actual / en curso)
            {"Jornada": "Jornada 13", "Local": "Boca Juniors", "GL": 1, "GV": 0, "Visitante": "San Lorenzo", "Estado": "Finalizado"},
            {"Jornada": "Jornada 13", "Local": "Independiente", "GL": 2, "GV": 1, "Visitante": "Estudiantes", "Estado": "Finalizado"},
            {"Jornada": "Jornada 13", "Local": "Vélez Sarsfield", "GL": 0, "GV": 0, "Visitante": "River Plate", "Estado": "Finalizado"},
            {"Jornada": "Jornada 13", "Local": "Belgrano", "GL": 1, "GV": 2, "Visitante": "Racing Club", "Estado": "Finalizado"},
            {"Jornada": "Jornada 13", "Local": "Gimnasia LP", "GL": 0, "GV": 1, "Visitante": "Talleres", "Estado": "Finalizado"},

            # Jornada 14 (Próxima)
            {"Jornada": "Jornada 14", "Local": "River Plate", "GL": "-", "GV": "-", "Visitante": "Independiente", "Estado": "Por Jugar"},
            {"Jornada": "Jornada 14", "Local": "Racing Club", "GL": "-", "GV": "-", "Visitante": "Boca Juniors", "Estado": "Por Jugar"},
            {"Jornada": "Jornada 14", "Local": "San Lorenzo", "GL": "-", "GV": "-", "Visitante": "Estudiantes", "Estado": "Por Jugar"},
            {"Jornada": "Jornada 14", "Local": "Talleres", "GL": "-", "GV": "-", "Visitante": "Vélez Sarsfield", "Estado": "Por Jugar"},
            {"Jornada": "Jornada 14", "Local": "Belgrano", "GL": "-", "GV": "-", "Visitante": "Gimnasia LP", "Estado": "Por Jugar"},
        ]
        df_fixture = pd.DataFrame(partidos_demo)

    # -----------------------------------------------------------------
    # 3. TABLA GENERAL DE POSICIONES
    # -----------------------------------------------------------------
    st.markdown("<h3 style='color: #cbd5e1;'>📊 Tabla General de Posiciones</h3>", unsafe_allow_html=True)
    st.dataframe(df_posiciones, use_container_width=True, hide_index=True)
    st.markdown("---")

    # -----------------------------------------------------------------
    # 4. RESULTADOS Y FIXTURE NAVEGABLE POR JORNADA
    # -----------------------------------------------------------------
    st.markdown("<h3 style='color: #cbd5e1;'>📅 Fixture & Resultados por Jornada</h3>", unsafe_allow_html=True)
    
    lista_jornadas = sorted(df_fixture["Jornada"].unique(), key=lambda x: int(re.search(r'\d+', x).group()) if re.search(r'\d+', x) else x)
    
    # Selector de Fecha / Jornada
    jornada_seleccionada = st.selectbox("Seleccionar Jornada a consultar:", lista_jornadas, index=len(lista_jornadas) - 2)

    # Filtrar el DataFrame según la fecha seleccionada
    df_jornada = df_fixture[df_fixture["Jornada"] == jornada_seleccionada][["Local", "GL", "GV", "Visitante", "Estado"]]
    df_jornada.columns = ["Equipo Local", "Goles Local", "Goles Visitante", "Equipo Visitante", "Estado del Partido"]

    st.markdown(f"<h4 style='color: #00ffcc;'>Partidos de la {jornada_seleccionada}</h4>", unsafe_allow_html=True)
    st.dataframe(df_jornada, use_container_width=True, hide_index=True)
    st.markdown("---")

    # -----------------------------------------------------------------
    # 5. PREDICTOR DE MATCHUPS
    # -----------------------------------------------------------------
    st.markdown("<h3 style='color: #cbd5e1;'>🎯 Predictor de Enfrentamientos</h3>", unsafe_allow_html=True)
    
    lista_equipos = sorted(df_posiciones["Equipo"].unique()) if "Equipo" in df_posiciones.columns else []

    if len(lista_equipos) >= 2:
        col1, col2 = st.columns(2)
        with col1:
            local = st.selectbox("Seleccionar Local", lista_equipos, index=0)
        with col2:
            visitante = st.selectbox("Seleccionar Visitante", lista_equipos, index=min(1, len(lista_equipos)-1))

        if local == visitante:
            st.error("SISTEMA BLOQUEADO: Seleccione escuadras diferentes.")
        else:
            row_loc = df_posiciones[df_posiciones["Equipo"] == local].iloc[0]
            row_vis = df_posiciones[df_posiciones["Equipo"] == visitante].iloc[0]

            pts_loc = float(row_loc.get("Puntos", 0)) if "Puntos" in df_posiciones.columns else 0.0
            pts_vis = float(row_vis.get("Puntos", 0)) if "Puntos" in df_posiciones.columns else 0.0
            pj_loc = max(float(row_loc.get("PJ", 1)), 1.0) if "PJ" in df_posiciones.columns else 1.0
            pj_vis = max(float(row_vis.get("PJ", 1)), 1.0) if "PJ" in df_posiciones.columns else 1.0

            prom_loc = (pts_loc / pj_loc) * 1.12
            prom_vis = (pts_vis / pj_vis)

            diferencia = abs(prom_loc - prom_vis)
            prob_empate = max(18.0, min(33.0, 28.5 - (diferencia * 6.0)))

            resto = 100.0 - prob_empate
            total_prom = prom_loc + prom_vis

            if total_prom > 0:
                prob_loc = (prom_loc / total_prom) * resto
                prob_vis = (prom_vis / total_prom) * resto
            else:
                prob_loc = resto / 2
                prob_vis = resto / 2

            st.markdown(f"<h2 style='text-align: center; color: #fff; margin-top: 25px;'>{local.upper()} vs {visitante.upper()}</h2>", unsafe_allow_html=True)
            
            m1, m2, m3 = st.columns(3)
            m1.metric(label=f"Victoria {local}", value=f"{prob_loc:.1f}%")
            m2.metric(label="Probabilidad Empate", value=f"{prob_empate:.1f}%")
            m3.metric(label=f"Victoria {visitante}", value=f"{prob_vis:.1f}%")

            st.markdown("<br>", unsafe_allow_html=True)
            c_b1, c_b2, c_b3 = st.columns(3)
            with c_b1:
                st.markdown("<p style='color: #00ffcc;'>Local</p>", unsafe_allow_html=True)
                st.progress(int(prob_loc) / 100)
            with c_b2:
                st.markdown("<p style='color: #cbd5e1;'>Empate</p>", unsafe_allow_html=True)
                st.progress(int(prob_empate) / 100)
            with c_b3:
                st.markdown("<p style='color: #ff3366;'>Visitante</p>", unsafe_allow_html=True)
                st.progress(int(prob_vis) / 100)

else:
    st.error("Archivo de origen no encontrado. Verifique que 'datos_procesados.csv' exista.")
