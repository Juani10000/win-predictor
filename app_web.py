import streamlit as st
import pandas as pd
import os
import re
import math

# =====================================================================
# 1. FUNCIONES AUXILIARES DE CÁLCULO (DEBEN IR AL INICIO)
# =====================================================================
def poisson_prob(lmbda, k):
    """Calcula la probabilidad de anotar k goles dado un xG de lmbda."""
    if lmbda <= 0:
        return 1.0 if k == 0 else 0.0
    return (math.pow(lmbda, k) * math.exp(-lmbda)) / math.factorial(k)

def calcular_top_resultados(xg_loc, xg_vis):
    """Calcula la matriz de probabilidades de marcadores exactos (0 a 5 goles)."""
    scores = {}
    for i in range(6):
        for j in range(6):
            p = poisson_prob(xg_loc, i) * poisson_prob(xg_vis, j)
            scores[f"{i} - {j}"] = p * 100

    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    top_5 = sorted_scores[:5]
    prob_top_5 = sum(p for _, p in top_5)
    prob_otro = max(0.0, 100.0 - prob_top_5)

    return top_5, prob_otro

# =====================================================================
# 2. CONFIGURACIÓN Y CSS PROFESIONAL FUTURISTA (SIN EMOJIS)
# =====================================================================
st.set_page_config(page_title="Win Predictor | LPF", layout="wide")

st.markdown("""
    <style>
        /* Fondo general y tipografía */
        .stApp {
            background-color: #070b19;
            color: #f1f5f9;
            font-family: 'Inter', system-ui, -apple-system, sans-serif;
        }
        
        /* Título Principal con Degradé */
        .hero-title {
            font-size: 40px;
            font-weight: 900;
            letter-spacing: -0.5px;
            margin-bottom: 2px;
            background: linear-gradient(90deg, #ffffff 0%, #00f3ff 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            text-transform: uppercase;
        }
        .hero-subtitle {
            color: #64748b;
            letter-spacing: 2px;
            font-size: 12px;
            font-weight: 700;
            text-transform: uppercase;
            margin-bottom: 20px;
        }
        
        /* Encabezados de Sección */
        .section-header {
            font-size: 18px;
            font-weight: 700;
            color: #38bdf8;
            letter-spacing: 0.5px;
            border-left: 3px solid #00f3ff;
            padding-left: 12px;
            margin-top: 25px;
            margin-bottom: 18px;
            text-transform: uppercase;
        }

        /* Banner de Enfrentamiento (VS) */
        .match-banner {
            background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 100%);
            border: 1px solid #312e81;
            border-radius: 12px;
            padding: 20px;
            text-align: center;
            margin-top: 15px;
            margin-bottom: 20px;
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.4);
        }
        .match-title {
            font-size: 26px;
            font-weight: 800;
            color: #ffffff;
            letter-spacing: 1px;
            text-transform: uppercase;
        }
        
        /* Tarjetas de Estadísticas (xG y Métricas) */
        .stat-card {
            background-color: #0f172a;
            border: 1px solid #1e293b;
            border-radius: 10px;
            padding: 16px;
            text-align: center;
            box-shadow: 0 4px 12px rgba(0,0,0,0.25);
        }
        .stat-label {
            font-size: 11px;
            color: #94a3b8;
            text-transform: uppercase;
            letter-spacing: 1px;
            font-weight: 600;
            margin-bottom: 6px;
        }
        .stat-value {
            font-size: 30px;
            font-weight: 900;
            color: #00ffcc;
        }
        .stat-value-alt {
            font-size: 30px;
            font-weight: 900;
            color: #ff3366;
        }
        .stat-value-draw {
            font-size: 30px;
            font-weight: 900;
            color: #cbd5e1;
        }

        /* Personalización del Selector */
        div[data-baseweb="select"] > div {
            background-color: #0f172a !important;
            border-color: #334155 !important;
            color: #ffffff !important;
            border-radius: 8px !important;
        }

        /* Tabla estilizada de marcadores exactos */
        .custom-table {
            width: 100%;
            border-collapse: collapse;
            background-color: #0f172a;
            border-radius: 8px;
            overflow: hidden;
            border: 1px solid #1e293b;
        }
        .custom-table th {
            background-color: #1e293b;
            color: #94a3b8;
            padding: 12px 16px;
            text-align: left;
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        .custom-table td {
            padding: 12px 16px;
            border-bottom: 1px solid #1e293b;
            color: #e2e8f0;
            font-size: 14px;
        }
        .rank-top {
            color: #00f3ff;
            font-weight: bold;
        }

        /* Separador */
        hr {
            border: 0;
            height: 1px;
            background: linear-gradient(90deg, transparent, #1e293b, transparent);
            margin: 25px 0;
        }
    </style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------
# ENCABEZADO PRINCIPAL
# ---------------------------------------------------------------------
col_logo, col_titulo = st.columns([1, 7])
with col_logo:
    url_lpf = "https://a.espncdn.com/combiner/i?img=/i/leaguelogos/soccer/500/1.png"
    st.image(url_lpf, width=95)

with col_titulo:
    st.markdown('<div class="hero-title">WIN PREDICTOR LPF</div>', unsafe_allow_html=True)
    st.markdown('<div class="hero-subtitle">MODELO ANALÍTICO DE EXPECTED GOALS Y MATRIZ DE PROBABILIDAD</div>', unsafe_allow_html=True)

st.markdown("<hr>", unsafe_allow_html=True)

# =====================================================================
# 3. CARGA DE DATOS
# =====================================================================
DIRECTORIO_APP = os.path.dirname(os.path.abspath(__file__))
RUTA_CSV = os.path.join(DIRECTORIO_APP, "datos_procesados.csv")

if not os.path.exists(RUTA_CSV):
    RUTA_CSV = os.path.join(DIRECTORIO_APP, "datos", "datos_procesados.csv")

if os.path.exists(RUTA_CSV):
    df = pd.read_csv(RUTA_CSV)
    
    if "Equipo" in df.columns:
        df["Equipo"] = df["Equipo"].astype(str).apply(lambda x: re.sub(r'\[.*?\]|\(.*?\)', '', x).strip())

    # Garantizar columna xG
    if "xG" not in df.columns and "xG_Favor" not in df.columns:
        if "GF" in df.columns and "PJ" in df.columns:
            df["xG"] = (df["GF"] / df["PJ"].replace(0, 1) * 0.95).round(2)
        else:
            df["xG"] = 1.25
    elif "xG_Favor" in df.columns and "xG" not in df.columns:
        df["xG"] = df["xG_Favor"]

    # -----------------------------------------------------------------
    # 4. TABLA DE POSICIONES
    # -----------------------------------------------------------------
    st.markdown('<div class="section-header">TABLA GENERAL DE POSICIONES Y METRICAS DE XG</div>', unsafe_allow_html=True)
    st.dataframe(df, use_container_width=True, hide_index=True)
    
    st.markdown("<hr>", unsafe_allow_html=True)

    # -----------------------------------------------------------------
    # 5. PREDICTOR DE PARTIDO
    # -----------------------------------------------------------------
    st.markdown('<div class="section-header">CONFIGURACIÓN DEL ENFRENTAMIENTO</div>', unsafe_allow_html=True)
    
    lista_equipos = sorted(df["Equipo"].unique()) if "Equipo" in df.columns else []

    if len(lista_equipos) >= 2:
        col1, col2 = st.columns(2)
        with col1:
            local = st.selectbox("Equipo Local", lista_equipos, index=0)
        with col2:
            visitante = st.selectbox("Equipo Visitante", lista_equipos, index=min(1, len(lista_equipos)-1))

        if local == visitante:
            st.error("Selección inválida: Elija dos equipos diferentes.")
        else:
            row_loc = df[df["Equipo"] == local].iloc[0]
            row_vis = df[df["Equipo"] == visitante].iloc[0]

            pts_loc = float(row_loc.get("Puntos", 0)) if "Puntos" in df.columns else 0.0
            pts_vis = float(row_vis.get("Puntos", 0)) if "Puntos" in df.columns else 0.0
            pj_loc = max(float(row_loc.get("PJ", 1)), 1.0) if "PJ" in df.columns else 1.0
            pj_vis = max(float(row_vis.get("PJ", 1)), 1.0) if "PJ" in df.columns else 1.0

            xg_loc_base = float(row_loc.get("xG", 1.25))
            xg_vis_base = float(row_vis.get("xG", 1.10))

            # xG Proyectado para el encuentro
            xg_proyectado_local = round(xg_loc_base * 1.10, 2)
            xg_proyectado_visi = round(xg_vis_base * 0.95, 2)

            # Algoritmo de probabilidad 1X2
            prom_loc = ((pts_loc / pj_loc) * 0.6) + (xg_proyectado_local * 0.4)
            prom_vis = ((pts_vis / pj_vis) * 0.6) + (xg_proyectado_visi * 0.4)

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

            # Banner del Partido
            st.markdown(f'''
                <div class="match-banner">
                    <div class="match-title">{local} vs {visitante}</div>
                </div>
            ''', unsafe_allow_html=True)

            # Tarjetas de xG Proyectado
            col_xg1, col_xg2 = st.columns(2)
            with col_xg1:
                st.markdown(f'''
                    <div class="stat-card">
                        <div class="stat-label">xG Proyectado Local ({local})</div>
                        <div style="font-size: 24px; font-weight: 800; color: #00f3ff;">{xg_proyectado_local}</div>
                    </div>
                ''', unsafe_allow_html=True)
            with col_xg2:
                st.markdown(f'''
                    <div class="stat-card">
                        <div class="stat-label">xG Proyectado Visitante ({visitante})</div>
                        <div style="font-size: 24px; font-weight: 800; color: #00f3ff;">{xg_proyectado_visi}</div>
                    </div>
                ''', unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)

            # Tarjetas Principales de Probabilidades 1X2
            c_m1, c_m2, c_m3 = st.columns(3)
            with c_m1:
                st.markdown(f'''
                    <div class="stat-card">
                        <div class="stat-label">Victoria {local}</div>
                        <div class="stat-value">{prob_loc:.1f}%</div>
                    </div>
                ''', unsafe_allow_html=True)
            with c_m2:
                st.markdown(f'''
                    <div class="stat-card">
                        <div class="stat-label">Probabilidad de Empate</div>
                        <div class="stat-value-draw">{prob_empate:.1f}%</div>
                    </div>
                ''', unsafe_allow_html=True)
            with c_m3:
                st.markdown(f'''
                    <div class="stat-card">
                        <div class="stat-label">Victoria {visitante}</div>
                        <div class="stat-value-alt">{prob_vis:.1f}%</div>
                    </div>
                ''', unsafe_allow_html=True)

            # Barras de Progreso
            st.markdown("<br>", unsafe_allow_html=True)
            b1, b2, b3 = st.columns(3)
            with b1:
                st.progress(int(prob_loc) / 100)
            with b2:
                st.progress(int(prob_empate) / 100)
            with b3:
                st.progress(int(prob_vis) / 100)

            st.markdown("<hr>", unsafe_allow_html=True)

            # -----------------------------------------------------------------
            # 6. TOP 5 MARCADORES EXACTOS
            # -----------------------------------------------------------------
            st.markdown('<div class="section-header">TOP 5 MARCADORES EXACTOS MÁS PROBABLES</div>', unsafe_allow_html=True)
            
            top_5_marcadores, prob_otro = calcular_top_resultados(xg_proyectado_local, xg_proyectado_visi)

            # Construcción de la tabla en HTML puro para máxima estética
            rows_html = ""
            for rank, (marcador, prob) in enumerate(top_5_marcadores, 1):
                rank_class = "rank-top" if rank == 1 else ""
                rows_html += f"""
                    <tr>
                        <td class="{rank_class}">#{rank}</td>
                        <td style="font-weight: 600;">{marcador}</td>
                        <td style="font-weight: 700; color: #00ffcc;">{prob:.1f}%</td>
                    </tr>
                """
            
            # Fila de otros resultados
            rows_html += f"""
                <tr>
                    <td style="color: #64748b;">Otros</td>
                    <td style="color: #94a3b8;">Cualquier otro marcador</td>
                    <td style="font-weight: 700; color: #94a3b8;">{prob_otro:.1f}%</td>
                </tr>
            """

            table_html = f"""
                <table class="custom-table">
                    <thead>
                        <tr>
                            <th>Ranking</th>
                            <th>Resultado Exacto (Local - Visitante)</th>
                            <th>Probabilidad Calculada</th>
                        </tr>
                    </thead>
                    <tbody>
                        {rows_html}
                    </tbody>
                </table>
            """
            st.markdown(table_html, unsafe_allow_html=True)

else:
    st.error("Archivo de origen no encontrado. Verifique la existencia de 'datos_procesados.csv'.")
