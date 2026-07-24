import streamlit as st
import pandas as pd
import os
import re
import time

# =====================================================================
# 1. CONFIGURACIÓN Y CSS FACHERO (NEÓN, COLORES, ANIMACIONES)
# =====================================================================
st.set_page_config(page_title="Win Predictor | LPF", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
        /* Fondo general súper oscuro */
        .stApp {
            background-color: #070b14;
            color: #e2e8f0;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
        /* Efecto Neón para el título principal */
        .neon-title {
            font-size: 48px;
            font-weight: 900;
            text-align: center;
            color: #ffffff;
            text-shadow: 0 0 10px #00f3ff, 0 0 20px #00f3ff, 0 0 40px #00f3ff;
            margin-bottom: 5px;
            text-transform: uppercase;
        }
        /* Subtítulo tecnológico */
        .tech-sub {
            text-align: center;
            color: #94a3b8;
            letter-spacing: 2px;
            font-size: 16px;
            margin-bottom: 30px;
        }
        /* Estilo de los números de porcentaje */
        [data-testid="stMetricValue"] {
            color: #00ffcc !important;
            font-size: 40px !important;
            font-weight: 900 !important;
            text-shadow: 0 0 5px #00ffcc80;
        }
        [data-testid="stMetricLabel"] {
            color: #94a3b8 !important;
            font-size: 16px !important;
            text-transform: uppercase;
        }
        /* Separadores */
        hr {
            border-top: 1px solid #1e293b;
        }
    </style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------
# ENCABEZADO CON GIF Y LOGO
# ---------------------------------------------------------------------
# Usamos un GIF de luces/datos para darle movimiento (sacado de Giphy)
st.markdown(
    """
    <div style="width: 100%; height: 150px; background-image: url('https://media.giphy.com/media/l41JONXqO0EqiC5yw/giphy.gif'); background-size: cover; background-position: center; border-radius: 10px; opacity: 0.7; margin-bottom: 20px;">
    </div>
    """, 
    unsafe_allow_html=True
)

col_logo, col_vacia, col_titulo = st.columns([1, 1, 6])
with col_logo:
    # URL directa de ESPN que ya comprobamos que funciona joya
    url_lpf = "https://a.espncdn.com/combiner/i?img=/i/leaguelogos/soccer/500/1.png"
    st.image(url_lpf, width=120)

with col_titulo:
    st.markdown('<div class="neon-title">Win Predictor LPF</div>', unsafe_allow_html=True)
    st.markdown('<div class="tech-sub">MOTOR DE PROBABILIDAD ESTADÍSTICA v2.0</div>', unsafe_allow_html=True)

st.markdown("---")

# =====================================================================
# 2. CARGA DE DATOS
# =====================================================================
DIRECTORIO_APP = os.path.dirname(os.path.abspath(__file__))
RUTA_CSV = os.path.join(DIRECTORIO_APP, "datos_procesados.csv")

if not os.path.exists(RUTA_CSV):
    RUTA_CSV = os.path.join(DIRECTORIO_APP, "datos", "datos_procesados.csv")

if os.path.exists(RUTA_CSV):
    df = pd.read_csv(RUTA_CSV)
    
    if "Equipo" in df.columns:
        df["Equipo"] = df["Equipo"].astype(str).apply(lambda x: re.sub(r'\[.*?\]|\(.*?\)', '', x).strip())

    # =================================================================
    # 3. INTERFAZ EN PESTAÑAS (TABS) PARA QUE SE VEA MODERNO
    # =================================================================
    tab_predictor, tab_tabla = st.tabs(["🎯 MOTOR DE PREDICCIÓN", "📊 BASE DE DATOS (TABLA)"])

    # -----------------------------------------------------------------
    # PESTAÑA 1: PREDICTOR ANIMADO
    # -----------------------------------------------------------------
    with tab_predictor:
        st.markdown("<h3 style='color: #cbd5e1;'>Configurar Encuentro</h3>", unsafe_allow_html=True)
        
        lista_equipos = sorted(df["Equipo"].unique()) if "Equipo" in df.columns else []

        if len(lista_equipos) >= 2:
            col1, col2 = st.columns(2)
            with col1:
                local = st.selectbox("Seleccionar Local", lista_equipos, index=0)
            with col2:
                visitante = st.selectbox("Seleccionar Visitante", lista_equipos, index=min(1, len(lista_equipos)-1))

            if local == visitante:
                st.error("SISTEMA BLOQUEADO: Seleccione escuadras diferentes.")
            else:
                # Botón de cálculo
                if st.button("⚡ EJECUTAR SIMULACIÓN", use_container_width=True, type="primary"):
                    
                    # Animación de carga artificial para darle suspenso
                    with st.spinner('Procesando estadísticas e historial...'):
                        time.sleep(1.5) # Simula tiempo de procesamiento

                    # Cálculos de probabilidad
                    row_loc = df[df["Equipo"] == local].iloc[0]
                    row_vis = df[df["Equipo"] == visitante].iloc[0]

                    pts_loc = float(row_loc.get("Puntos", 0)) if "Puntos" in df.columns else 0.0
                    pts_vis = float(row_vis.get("Puntos", 0)) if "Puntos" in df.columns else 0.0
                    pj_loc = max(float(row_loc.get("PJ", 1)), 1.0) if "PJ" in df.columns else 1.0
                    pj_vis = max(float(row_vis.get("PJ", 1)), 1.0) if "PJ" in df.columns else 1.0

                    prom_loc = (pts_loc / pj_loc) * 1.12
                    prom_vis = (pts_vis / pj_vis)

                    diferencia = abs(prom_loc - prom_vis)
                    prob_empate = max(18.0, min(33.0, 29.0 - (diferencia * 7.5)))

                    resto = 100.0 - prob_empate
                    total_prom = prom_loc + prom_vis

                    if total_prom > 0:
                        prob_loc = (prom_loc / total_prom) * resto
                        prob_vis = (prom_vis / total_prom) * resto
                    else:
                        prob_loc = resto / 2
                        prob_vis = resto / 2

                    # Animación de éxito (tira globitos en la pantalla)
                    st.balloons()

                    # Presentación visual del análisis
                    st.markdown("---")
                    st.markdown(f"<h2 style='text-align: center; color: #fff;'>{local.upper()} vs {visitante.upper()}</h2>", unsafe_allow_html=True)
                    
                    # Métricas destacadas
                    m1, m2, m3 = st.columns(3)
                    m1.metric(label=f"Victoria {local}", value=f"{prob_loc:.1f}%")
                    m2.metric(label="Probabilidad Empate", value=f"{prob_empate:.1f}%")
                    m3.metric(label=f"Victoria {visitante}", value=f"{prob_vis:.1f}%")

                    # Barras de progreso animadas nativas de Streamlit
                    st.markdown("<br><p style='color: #94a3b8;'>Distribución de victoria local:</p>", unsafe_allow_html=True)
                    st.progress(int(prob_loc) / 100)
                    
                    st.markdown("<p style='color: #94a3b8;'>Distribución de empate:</p>", unsafe_allow_html=True)
                    st.progress(int(prob_empate) / 100)
                    
                    st.markdown("<p style='color: #94a3b8;'>Distribución de victoria visitante:</p>", unsafe_allow_html=True)
                    st.progress(int(prob_vis) / 100)

    # -----------------------------------------------------------------
    # PESTAÑA 2: TABLA DE POSICIONES
    # -----------------------------------------------------------------
    with tab_tabla:
        st.markdown("<h3 style='color: #cbd5e1;'>Estado Actual del Campeonato</h3>", unsafe_allow_html=True)
        st.dataframe(df, use_container_width=True, hide_index=True)

else:
    st.error("Archivo de origen no encontrado. Verifique que 'datos_procesados.csv' exista.")
