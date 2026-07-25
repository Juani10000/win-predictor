import math
import os
import re
import pandas as pd
import streamlit as st
import requests
import datetime

# =====================================================================
# 1. CONFIGURACIÓN Y CSS ESTILO NEÓN
# =====================================================================
st.set_page_config(page_title="Win Predictor | LPF", layout="wide")

st.markdown(
    """
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
""",
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------------
# FUNCIONES AUXILIARES PARA CÁLCULO DE POISSON Y PREDICCIÓN
# ---------------------------------------------------------------------
def poisson_prob(lmbda, k):
    """Calcula la probabilidad de anotar k goles dado un xG de lmbda."""
    if lmbda <= 0:
        return 1.0 if k == 0 else 0.0
    return (math.pow(lmbda, k) * math.exp(-lmbda)) / math.factorial(k)


def calcular_top_resultados(xg_loc, xg_vis):
    """Calcula la matriz de probabilidades de marcadores exactos (0 a 5 goles)."""
    scores = {}
    total_prob_matriz = 0.0

    for i in range(6):  
        for j in range(6):  
            p = poisson_prob(xg_loc, i) * poisson_prob(xg_vis, j)
            scores[f"{i} - {j}"] = p * 100
            total_prob_matriz += p * 100

    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    top_5 = sorted_scores[:5]

    prob_top_5 = sum(p for _, p in top_5)
    prob_otro = max(0.0, 100.0 - prob_top_5)

    return top_5, prob_otro


def realizar_prediccion(local, visitante, df):
    """Lógica principal de predicción de partidos."""
    row_loc = df[df["Equipo"] == local].iloc[0]
    row_vis = df[df["Equipo"] == visitante].iloc[0]

    pts_loc = float(row_loc.get("Puntos", 0)) if "Puntos" in df.columns else 0.0
    pts_vis = float(row_vis.get("Puntos", 0)) if "Puntos" in df.columns else 0.0
    pj_loc = max(float(row_loc.get("PJ", 1)), 1.0) if "PJ" in df.columns else 1.0
    pj_vis = max(float(row_vis.get("PJ", 1)), 1.0) if "PJ" in df.columns else 1.0

    xg_loc_base = float(row_loc.get("xG", 1.25))
    xg_vis_base = float(row_vis.get("xG", 1.10))

    xg_proyectado_local = round(xg_loc_base * 1.10, 2)
    xg_proyectado_visi = round(xg_vis_base * 0.95, 2)

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

    return prob_loc, prob_empate, prob_vis, xg_proyectado_local, xg_proyectado_visi


def buscar_equipo(nombre_buscado, lista_equipos):
    """Mapea un nombre común de equipo al nombre exacto en el DataFrame."""
    nombre_clean = nombre_buscado.lower().strip()
    
    # 1. Búsqueda exacta parcial
    for eq in lista_equipos:
        eq_clean = eq.lower().strip()
        if nombre_clean in eq_clean or eq_clean in nombre_clean:
            return eq
            
    # 2. Búsqueda por palabras clave (ej: "Estudiantes RC" -> "Estudiantes")
    palabras = nombre_clean.split()
    if palabras:
        palabra_clave = palabras[0]
        for eq in lista_equipos:
            if palabra_clave in eq.lower():
                return eq
    return None


# ---------------------------------------------------------------------
# SCRAPING 100% AUTOMÁTICO - API ESPN (Sin fallas de Wikipedia)
# ---------------------------------------------------------------------
@st.cache_data(ttl=3600)
def obtener_partidos_hoy_auto(equipos_disponibles):
    # Liga Profesional Argentina en ESPN
    url = "https://site.api.espn.com/apis/site/v2/sports/soccer/arg.1/scoreboard"
    partidos_hoy = []
    
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        
        # ESPN usa horario mundial (UTC). Restamos 3 horas para la hora de Argentina
        ahora_arg = datetime.datetime.utcnow() - datetime.timedelta(hours=3)
        fecha_hoy_str = ahora_arg.strftime("%Y-%m-%d")
        
        if 'events' in data:
            for event in data['events']:
                # Analizar fecha del partido
                fecha_api = datetime.datetime.strptime(event['date'], "%Y-%m-%dT%H:%MZ")
                fecha_partido_arg = fecha_api - datetime.timedelta(hours=3)
                
                # Si el partido coincide con la fecha de hoy
                if fecha_partido_arg.strftime("%Y-%m-%d") == fecha_hoy_str:
                    comps = event['competitions'][0]['competitors']
                    
                    equipo_1 = comps[0]['team']['name']
                    equipo_2 = comps[1]['team']['name']
                    
                    # Identificar quién es local y visitante
                    loc_raw = equipo_1 if comps[0]['homeAway'] == 'home' else equipo_2
                    vis_raw = equipo_2 if comps[0]['homeAway'] == 'home' else equipo_1
                    
                    hora_str = fecha_partido_arg.strftime("%H:%M")
                    
                    loc_match = buscar_equipo(loc_raw, equipos_disponibles)
                    vis_match = buscar_equipo(vis_raw, equipos_disponibles)
                    
                    # Agregar solo si encontramos a ambos equipos en tu CSV
                    if loc_match and vis_match and loc_match != vis_match:
                        partidos_hoy.append({
                            "Local": loc_match,
                            "Visitante": vis_match,
                            "Hora": hora_str
                        })
    except Exception:
        pass

    return partidos_hoy


# ---------------------------------------------------------------------
# ENCABEZADO CON LOGO
# ---------------------------------------------------------------------
col_logo, col_titulo = st.columns([1, 6])
with col_logo:
    url_lpf = (
        "https://a.espncdn.com/combiner/i?img=/i/leaguelogos/soccer/500/1.png"
    )
    st.image(url_lpf, width=110)

with col_titulo:
    st.markdown(
        '<div class="neon-title">Win Predictor LPF</div>', unsafe_allow_html=True
    )
    st.markdown(
        '<div class="tech-sub">MOTOR DE PREDICCIÓN CON xG Y RESULTADOS EXACTOS</div>',
        unsafe_allow_html=True,
    )

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
        df["Equipo"] = (
            df["Equipo"]
            .astype(str)
            .apply(lambda x: re.sub(r"\[.*?\]|\(.*?\)", "", x).strip())
        )

    # Garantizar columna xG
    if "xG" not in df.columns and "xG_Favor" not in df.columns:
        if "GF" in df.columns and "PJ" in df.columns:
            df["xG"] = (df["GF"] / df["PJ"].replace(0, 1) * 0.95).round(2)
        else:
            df["xG"] = 1.25
    elif "xG_Favor" in df.columns and "xG" not in df.columns:
        df["xG"] = df["xG_Favor"]

    lista_equipos = sorted(df["Equipo"].unique()) if "Equipo" in df.columns else []


    # -----------------------------------------------------------------
    # 3. AGENDA DEL DÍA AUTOMÁTICA
    # -----------------------------------------------------------------
    st.markdown(
        "<h3 style='color: #cbd5e1;'>📅 Partidos de Hoy</h3>",
        unsafe_allow_html=True,
    )
    
    # Llama a la API inteligente de ESPN
    partidos_del_dia = obtener_partidos_hoy_auto(lista_equipos)

    # Renderizado de las tarjetas
    if partidos_del_dia:
        for idx, partido in enumerate(partidos_del_dia):
            with st.container():
                c_info, c_btn = st.columns([4, 1])
                with c_info:
                    st.markdown(f"🕒 **{partido['Hora']}** | **{partido['Local']}** vs **{partido['Visitante']}**")
                with c_btn:
                    if st.button("🔮 Predecir", key=f"btn_hoy_{idx}"):
                        st.session_state['sel_local'] = partido['Local']
                        st.session_state['sel_visitante'] = partido['Visitante']
            st.divider()
    else:
        st.info("Sin partidos programados para el día de hoy según la liga oficial.")
        st.divider()


    # -----------------------------------------------------------------
    # 4. TABLA DE POSICIONES SIEMPRE VISIBLE
    # -----------------------------------------------------------------
    st.markdown(
        "<h3 style='color: #cbd5e1;'>Tabla General de Posiciones & xG</h3>",
        unsafe_allow_html=True,
    )
    st.dataframe(df, use_container_width=True, hide_index=True)
    st.markdown("---")


    # -----------------------------------------------------------------
    # 5. MOTOR DE PREDICCIÓN MANUAL Y VISUALIZACIÓN
    # -----------------------------------------------------------------
    st.markdown(
        "<h3 style='color: #cbd5e1;'>Motor de Predicción de Partidos</h3>",
        unsafe_allow_html=True,
    )

    if len(lista_equipos) >= 2:
        idx_loc = 0
        idx_vis = min(1, len(lista_equipos) - 1)
        
        if 'sel_local' in st.session_state and st.session_state['sel_local'] in lista_equipos:
            idx_loc = lista_equipos.index(st.session_state['sel_local'])
        if 'sel_visitante' in st.session_state and st.session_state['sel_visitante'] in lista_equipos:
            idx_vis = lista_equipos.index(st.session_state['sel_visitante'])

        col1, col2 = st.columns(2)
        with col1:
            local = st.selectbox("Seleccionar Local", lista_equipos, index=idx_loc, key="sb_local")
        with col2:
            visitante = st.selectbox("Seleccionar Visitante", lista_equipos, index=idx_vis, key="sb_visit")

        if local == visitante:
            st.error("SISTEMA BLOQUEADO: Seleccione escuadras diferentes.")
        else:
            prob_loc, prob_empate, prob_vis, xg_proyectado_local, xg_proyectado_visi = realizar_prediccion(local, visitante, df)

            st.markdown(
                f"<h2 style='text-align: center; color: #fff; margin-top:"
                f" 25px;'>{local.upper()} vs {visitante.upper()}</h2>",
                unsafe_allow_html=True,
            )

            col_xg1, col_xg2 = st.columns(2)
            with col_xg1:
                st.info(f"xG Proyectado {local}: **{xg_proyectado_local}**")
            with col_xg2:
                st.info(f"xG Proyectado {visitante}: **{xg_proyectado_visi}**")

            m1, m2, m3 = st.columns(3)
            m1.metric(label=f"Victoria {local}", value=f"{prob_loc:.1f}%")
            m2.metric(label="Probabilidad Empate", value=f"{prob_empate:.1f}%")
            m3.metric(label=f"Victoria {visitante}", value=f"{prob_vis:.1f}%")

            st.markdown(
                "<br><p style='color: #94a3b8;'>Distribución de probabilidad 1X2:</p>",
                unsafe_allow_html=True,
            )
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

            st.markdown("---")

            # -----------------------------------------------------------------
            # 6. TOP 5 RESULTADOS MÁS PROBABLES (CÁLCULO POISSON)
            # -----------------------------------------------------------------
            st.markdown(
                "<h4 style='color: #cbd5e1;'>Top 5 Marcadores Exactos Más Probables</h4>",
                unsafe_allow_html=True,
            )

            top_5_marcadores, prob_otro = calcular_top_resultados(
                xg_proyectado_local, xg_proyectado_visi
            )

            tabla_marcadores = []
            for rank, (marcador, prob) in enumerate(top_5_marcadores, 1):
                tabla_marcadores.append({
                    "Ranking": f"#{rank}",
                    "Resultado Exacto (Local - Visitante)": marcador,
                    "Probabilidad": f"{prob:.1f}%",
                })

            tabla_marcadores.append({
                "Ranking": "Otros",
                "Resultado Exacto (Local - Visitante)": "Cualquier otro resultado",
                "Probabilidad": f"{prob_otro:.1f}%",
            })

            df_marcadores = pd.DataFrame(tabla_marcadores)
            st.dataframe(df_marcadores, use_container_width=True, hide_index=True)

else:
    st.error("Archivo de origen no encontrado. Verifique que 'datos_procesados.csv' exista.")
