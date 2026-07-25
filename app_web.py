import streamlit as st
import pandas as pd
import os
import re

# =====================================================================
# 1. CONFIGURACIÓN Y CSS NEÓN
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
    st.markdown('<div class="tech-sub">MODELO xG & PREDICCIÓN AVANZADA DE PARTIDOS</div>', unsafe_allow_html=True)

st.markdown("---")

# =====================================================================
# 2. CARGA Y PROCESAMIENTO DE DATOS CON xG
# =====================================================================
DIRECTORIO_APP = os.path.dirname(os.path.abspath(__file__))
RUTA_CSV = os.path.join(DIRECTORIO_APP, "datos_procesados.csv")

if not os.path.exists(RUTA_CSV):
    RUTA_CSV = os.path.join(DIRECTORIO_APP, "datos", "datos_procesados.csv")

if os.path.exists(RUTA_CSV):
    df = pd.read_csv(RUTA_CSV)
    
    if "Equipo" in df.columns:
        df["Equipo"] = df["Equipo"].astype(str).apply(lambda x: re.sub(r'\[.*?\]|\(.*?\)', '', x).strip())

    # Generación o validación de columna xG si no existe en el CSV
    if "xG" not in df.columns and "xG_Favor" not in df.columns:
        # Estimación estándar basada en goles convertidos o partidos si falta la métrica exacta
        if "GF" in df.columns and "PJ" in df.columns:
            df["xG"] = (df["GF"] / df["PJ"].replace(0, 1) * 0.95).round(2)
        else:
            df["xG"] = 1.20  # Valor base estándar
    elif "xG_Favor" in df.columns:
        df["xG"] = df["xG_Favor"]

    # -----------------------------------------------------------------
    # 3. TABLA DE POSICIONES CON METRICA xG
    # -----------------------------------------------------------------
    st.markdown("<h3 style='color: #cbd5e1;'>📊 Tabla General & Métricas de xG</h3>", unsafe_allow_html=True)
    st.dataframe(df, use_container_width=True, hide_index=True)
    st.markdown("---")

    # -----------------------------------------------------------------
    # 4. PREDICTOR BASADO EN xG + RENDIMIENTO
    # -----------------------------------------------------------------
    st.markdown("<h3 style='color: #cbd5e1;'>🎯 Predictor de Partido con xG Proyectado</h3>", unsafe_allow_html=True)
    
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
            row_loc = df[df["Equipo"] == local].iloc[0]
            row_vis = df[df["Equipo"] == visitante].iloc[0]

            pts_loc = float(row_loc.get("Puntos", 0)) if "Puntos" in df.columns else 0.0
            pts_vis = float(row_vis.get("Puntos", 0)) if "Puntos" in df.columns else 0.0
            pj_loc = max(float(row_loc.get("PJ", 1)), 1.0) if "PJ" in df.columns else 1.0
            pj_vis = max(float(row_vis.get("PJ", 1)), 1.0) if "PJ" in df.columns else 1.0

            xg_loc_base = float(row_loc.get("xG", 1.25))
            xg_vis_base = float(row_vis.get("xG", 1.10))

            # Cálculo de xG proyectado para el encuentro (+10% factor localía)
            xg_proyectado_local = round(xg_loc_base * 1.10, 2)
            xg_proyectado_visi = round(xg_vis_base * 0.95, 2)

            # Promedio combinado (Puntos + xG)
            prom_loc = ((pts_loc / pj_loc) * 0.6) + (xg_proyectado_local * 0.4)
            prom_vis = ((pts_vis / pj_vis) * 0.6) + (xg_proyectado_visi * 0.4)

            # Probabilidades
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
            
            # Fila extra con xG proyectado
            col_xg1, col_xg2 = st.columns(2)
            with col_xg1:
                st.info(f"xG Proyectado {local}: **{xg_proyectado_local}**")
            with col_xg2:
                st.info(f"xG Proyectado {visitante}: **{xg_proyectado_visi}**")

            # Tarjetas de resultado
            m1, m2, m3 = st.columns(3)
            m1.metric(label=f"Victoria {local}", value=f"{prob_loc:.1f}%")
            m2.metric(label="Empate", value=f"{prob_empate:.1f}%")
            m3.metric(label=f"Victoria {visitante}", value=f"{prob_vis:.1f}%")

            # Barras de porcentaje
            st.markdown("<br><p style='color: #94a3b8;'>Distribución estadística de posibilidades:</p>", unsafe_allow_html=True)
            
            c_loc, c_emp, c_vis = st.columns(3)
            with c_loc:
                st.markdown(f"<p style='color: #00ffcc;'>Local</p>", unsafe_allow_html=True)
                st.progress(int(prob_loc) / 100)
            with c_emp:
                st.markdown(f"<p style='color: #cbd5e1;'>Empate</p>", unsafe_allow_html=True)
                st.progress(int(prob_empate) / 100)
            with c_vis:
                st.markdown(f"<p style='color: #ff3366;'>Visitante</p>", unsafe_allow_html=True)
                st.progress(int(prob_vis) / 100)

else:
    st.error("Archivo de origen no encontrado. Verifique que 'datos_procesados.csv' exista.")
