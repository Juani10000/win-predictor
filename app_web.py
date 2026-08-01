import datetime
import math
import os
import re
import hashlib
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import requests
import streamlit as st
import joblib

# =====================================================================
# 1. CONFIGURACION Y CSS ESTILO NEON / CORPORATIVO (OPTIMIZADO MÓVIL)
# =====================================================================
st.set_page_config(page_title="Win Predictor | LPF", layout="wide")

# Ocultar menús nativos y footer de Streamlit
ocultar_elementos_streamlit = """
    <style>
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    .stAppHeader {display: none;}
    </style>
    """
st.markdown(ocultar_elementos_streamlit, unsafe_allow_html=True)
st.markdown(
    """
    <head>
        <meta name="google-site-verification" content="nGtul4qMmIIjYUn" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    </head>
    """,
    unsafe_allow_html=True
)

st.markdown(
    """
    <style>
        /* Bloquear Pull-to-Refresh molesto en móviles */
        html, body, .stApp {
            background-color: #070b14;
            color: #e2e8f0;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            overscroll-behavior-y: none !important;
            touch-action: pan-x pan-y;
        }
        .neon-title {
            font-size: 32px;
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
            letter-spacing: 1px;
            font-size: 13px;
            margin-bottom: 15px;
            font-weight: 600;
        }
        [data-testid="stMetricValue"] {
            color: #00ffcc !important;
            font-size: 26px !important;
            font-weight: 900 !important;
            text-shadow: 0 0 5px #00ffcc80;
        }
        [data-testid="stMetricLabel"] {
            color: #94a3b8 !important;
            font-size: 12px !important;
            text-transform: uppercase;
        }
        hr {
            border-top: 1px solid #1e293b;
        }
        /* Estilos para Tarjetas de Goleadores (Móvil) */
        .player-card {
            background: linear-gradient(135deg, #0d1527 0%, #111e38 100%);
            border: 1px solid #00f3ff40;
            border-radius: 12px;
            padding: 16px;
            text-align: center;
            box-shadow: 0 4px 15px rgba(0, 243, 255, 0.1);
            margin-bottom: 12px;
        }
        .player-name {
            font-size: 19px;
            font-weight: 800;
            color: #ffffff;
            margin-bottom: 4px;
        }
        .player-team {
            font-size: 12px;
            color: #00ffcc;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 10px;
        }
        .player-stat {
            font-size: 28px;
            font-weight: 900;
            color: #00f3ff;
            text-shadow: 0 0 8px rgba(0, 243, 255, 0.6);
        }
        .player-sub {
            font-size: 12px;
            color: #94a3b8;
            margin-top: 4px;
        }
        /* Estilo para escudos en el duelo de equipos */
        .team-shield-box {
            text-align: center;
            background: #0d1527;
            border: 1px solid #1e293b;
            border-radius: 12px;
            padding: 15px;
            margin-bottom: 10px;
        }
        .team-shield-img {
            max-width: 80px;
            max-height: 80px;
            object-fit: contain;
            filter: drop-shadow(0 0 8px rgba(0,243,255,0.3));
        }

        /* INICIO MEJORAS MOBILE-FIRST APPS / BOTONES Y SELECTS TÁCTILES */
        .stSelectbox > div > div {
            background: #111827 !important;
            color: #00f3ff !important;
            border: 2px solid #00f3ff50 !important;
            border-radius: 12px !important;
            font-size: 16px !important; /* 16px evita auto-zoom en iOS */
            min-height: 50px !important;
            box-shadow: 0 0 10px rgba(0, 243, 255, 0.15) !important;
        }
        .stButton > button {
            width: 100%;
            min-height: 52px !important;
            font-size: 1.05rem !important;
            font-weight: 800 !important;
            border-radius: 12px !important;
            background: linear-gradient(135deg, #00f3ff 0%, #0077ff 100%) !important;
            color: #070b14 !important;
            border: none !important;
            box-shadow: 0 4px 15px rgba(0, 243, 255, 0.3) !important;
            transition: all 0.2s ease !important;
        }
        .stButton > button:active {
            transform: scale(0.97);
        }
        @media (max-width: 768px) {
            .stApp {
                padding-left: 0.3rem !important;
                padding-right: 0.3rem !important;
            }
            .neon-title {
                font-size: 24px;
                text-align: center;
            }
            .tech-sub {
                text-align: center;
            }
            .stDataFrame {
                width: 100% !important;
                overflow-x: auto !important;
            }
        }
        /* FIN MEJORAS MOBILE-FIRST APPS */
    </style>
    """,
    unsafe_allow_html=True,
)

# =====================================================================
# 2. DICCIONARIO DE JERARQUIA DE PLANTELES Y CARGA DE MODELO IA
# =====================================================================
JERARQUIA_EQUIPOS = {
    "River Plate": 9.5, "Boca Juniors": 9.2, "Racing Club": 8.5,
    "San Lorenzo": 8.0, "Independiente": 8.0, "Estudiantes": 7.8,
    "Talleres": 7.8, "Vélez Sarsfield": 7.5, "Lanús": 7.5,
    "Huracán": 7.2, "Rosario Central": 7.2, "Argentinos Juniors": 7.0,
    "Godoy Cruz": 7.0, "Belgrano": 6.8, "Newell's": 6.8,
    "Defensa y Justicia": 6.8, "Unión": 6.5, "Platense": 6.5,
    "Gimnasia LP": 6.5, "Instituto": 6.3, "Banfield": 6.3,
    "Tigre": 6.2, "Barracas Central": 6.0, "Central Córdoba": 6.0,
    "Sarmiento": 5.8, "Deportivo Riestra": 5.8, "Independiente Rivadavia": 5.8,
    "Atlético Tucumán": 6.2, "Aldosivi": 5.5, "San Martín (SJ)": 5.5
}

# Base de datos de principales atacantes y su promedio de gol por partido
JUGADORES_LPF = [
    {"nombre": "Miguel Borja", "equipo": "River Plate", "prom_goles": 0.65},
    {"nombre": "Facundo Colidio", "equipo": "River Plate", "prom_goles": 0.38},
    {"nombre": "Edinson Cavani", "equipo": "Boca Juniors", "prom_goles": 0.58},
    {"nombre": "Miguel Merentiel", "equipo": "Boca Juniors", "prom_goles": 0.45},
    {"nombre": "Adrian Martinez", "equipo": "Racing Club", "prom_goles": 0.62},
    {"nombre": "Maximiliano Salas", "equipo": "Racing Club", "prom_goles": 0.32},
    {"nombre": "Braian Romero", "equipo": "Vélez Sarsfield", "prom_goles": 0.52},
    {"nombre": "Claudio Aquino", "equipo": "Vélez Sarsfield", "prom_goles": 0.40},
    {"nombre": "Walter Bou", "equipo": "Lanús", "prom_goles": 0.48},
    {"nombre": "Marcelino Moreno", "equipo": "Lanús", "prom_goles": 0.35},
    {"nombre": "Luciano Gondou", "equipo": "Argentinos Juniors", "prom_goles": 0.50},
    {"nombre": "Guido Carrillo", "equipo": "Estudiantes", "prom_goles": 0.42},
    {"nombre": "Edwar Lopez", "equipo": "Tigre", "prom_goles": 0.30},
    {"nombre": "Federico Girotti", "equipo": "Talleres", "prom_goles": 0.41},
    {"nombre": "Matias Coccaro", "equipo": "Huracán", "prom_goles": 0.38},
    {"nombre": "Adam Bareiro", "equipo": "River Plate", "prom_goles": 0.36},
    {"nombre": "Jaminton Campaz", "equipo": "Rosario Central", "prom_goles": 0.30},
    {"nombre": "Marco Ruben", "equipo": "Rosario Central", "prom_goles": 0.35},
    {"nombre": "Gabriel Avalos", "equipo": "Independiente", "prom_goles": 0.37},
    {"nombre": "Santiago Rodriguez", "equipo": "Instituto", "prom_goles": 0.36},
    {"nombre": "Jonathan Candia", "equipo": "Barracas Central", "prom_goles": 0.31},
    {"nombre": "Florian Monzon", "equipo": "Tigre", "prom_goles": 0.33},
    {"nombre": "Ignacio Pussetto", "equipo": "Huracán", "prom_goles": 0.40},
    {"nombre": "Mateo Pellegrino", "equipo": "Platense", "prom_goles": 0.38}
]

ESCUDO_DEFAULT = "https://a.espncdn.com/combiner/i?img=/i/leaguelogos/soccer/500/1.png"

def obtener_jerarquia(nombre_equipo):
    if not isinstance(nombre_equipo, str):
        return 6.5
    nombre_clean = nombre_equipo.lower().strip()
    for eq, rating in JERARQUIA_EQUIPOS.items():
        if eq.lower() in nombre_clean or nombre_clean in eq.lower():
            return rating
    return 6.5

@st.cache_resource
def cargar_modelo_ia():
    rutas = ["modelo_entrenado.pkl", os.path.join("datos", "modelo_entrenado.pkl")]
    for ruta in rutas:
        if os.path.exists(ruta):
            try:
                return joblib.load(ruta)
            except Exception:
                pass
    return None

paquete_ia = cargar_modelo_ia()

# =====================================================================
# 3. EXTRAER TABLAS, ESCUDOS Y MAPA DE IDs DESDE ESPN
# =====================================================================
@st.cache_data(ttl=1800)
def obtener_grupos_en_vivo_espn():
    url = "https://site.api.espn.com/apis/v2/sports/soccer/arg.1/standings"
    grupos = {}

    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            data = r.json()
            children = data.get("children", [])

            if not children and "standings" in data:
                children = [data]

            for idx, grupo in enumerate(children):
                nombre_grupo = grupo.get("name", f"Grupo {chr(65 + idx)}")
                entries = grupo.get("standings", {}).get("entries", [])
                
                lista_equipos_grupo = []
                for entry in entries:
                    team_info = entry.get("team", {})
                    nombre = team_info.get("displayName", "")
                    team_id = team_info.get("id", "")
                    logos = team_info.get("logos", [])
                    logo_url = logos[0].get("href", ESCUDO_DEFAULT) if logos else ESCUDO_DEFAULT

                    if not nombre:
                        continue

                    stats_raw = entry.get("stats", [])
                    stats_map = {s.get("name"): s.get("value", 0) for s in stats_raw}

                    pj = int(stats_map.get("gamesPlayed", 0))
                    gf = int(stats_map.get("pointsFor", 0))
                    gc = int(stats_map.get("pointsAgainst", 0))
                    pts = int(stats_map.get("points", 0))

                    lista_equipos_grupo.append({
                        "Escudo": logo_url,
                        "Equipo": nombre,
                        "ID_ESPN": team_id,
                        "Puntos": pts,
                        "PJ": pj,
                        "GF": gf,
                        "GC": gc,
                        "DG": gf - gc,
                        "xG": max(0.80, round((gf / max(1, pj)) * 0.95, 2))
                    })

                df_grupo = pd.DataFrame(lista_equipos_grupo)
                if not df_grupo.empty:
                    df_grupo = df_grupo.sort_values(
                        by=["Puntos", "DG", "GF"],
                        ascending=[False, False, False]
                    ).drop(columns=["DG"]).reset_index(drop=True)

                    df_grupo.insert(0, "Pos", range(1, len(df_grupo) + 1))

                grupos[nombre_grupo] = df_grupo

    except Exception:
        pass

    return grupos

def obtener_escudo_equipo(nombre_equipo, df_unificado):
    if df_unificado.empty or "Equipo" not in df_unificado.columns:
        return ESCUDO_DEFAULT
    match = df_unificado[df_unificado["Equipo"] == nombre_equipo]
    if not match.empty and "Escudo" in match.columns:
        return match.iloc[0]["Escudo"]
    return ESCUDO_DEFAULT

# =====================================================================
# 4. OBTENER ULTIMOS 10 PARTIDOS REALES DE ESPN
# =====================================================================
@st.cache_data(ttl=3600)
def obtener_ultimos_10_partidos_espn(team_id):
    if not team_id:
        return []

    url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/arg.1/teams/{team_id}/schedule"
    partidos_finalizados = []

    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            events = r.json().get("events", [])
            for ev in events:
                status = ev.get("status", {}).get("type", {}).get("completed", False)
                if status:
                    competitions = ev.get("competitions", [])
                    if not competitions:
                        continue
                    
                    comps = competitions[0]["competitors"]
                    mi_equipo = comps[0] if str(comps[0].get("team", {}).get("id")) == str(team_id) else comps[1]
                    rival_equipo = comps[1] if str(comps[0].get("team", {}).get("id")) == str(team_id) else comps[0]

                    goles_favor = int(mi_equipo.get("score", {}).get("value", 0))
                    goles_contra = int(rival_equipo.get("score", {}).get("value", 0))

                    if goles_favor > goles_contra:
                        pts = 3 
                    elif goles_favor == goles_contra:
                        pts = 1 
                    else:
                        pts = 0 

                    partidos_finalizados.append({
                        "Fecha": ev.get("date", ""),
                        "Rival": rival_equipo.get("team", {}).get("displayName", "Rival"),
                        "GF": goles_favor,
                        "GC": goles_contra,
                        "Puntos": pts
                    })

            partidos_finalizados.sort(key=lambda x: x["Fecha"], reverse=True)
            return partidos_finalizados[:10]

    except Exception:
        pass

    return partidos_finalizados

def calcular_score_forma_exponencial_real(partidos_10, jerarquia):
    pesos = [0.20, 0.15, 0.12, 0.10, 0.08, 0.05, 0.04, 0.03, 0.02, 0.01]

    if not partidos_10:
        return jerarquia

    score_total = 0.0
    peso_acumulado = 0.0

    for i, p in enumerate(partidos_10):
        if i >= len(pesos):
            break
        
        peso = pesos[i]
        rendimiento_partido = (p["Puntos"] / 3.0) * 10.0
        score_total += rendimiento_partido * peso
        peso_acumulado += peso

    if peso_acumulado > 0:
        score_normalizado = score_total / peso_acumulado
    else:
        score_normalizado = jerarquia

    return min(10.0, max(1.0, score_normalizado))

# =====================================================================
# 5. FUNCIONES MATEMATICAS Y DE SIMULACION
# =====================================================================
def poisson_prob(lmbda, k):
    if lmbda <= 0:
        return 1.0 if k == 0 else 0.0
    return (math.pow(lmbda, k) * math.exp(-lmbda)) / math.factorial(k)

def simular_monte_carlo(xg_loc, xg_vis, num_simulaciones=10000):
    rng = np.random.default_rng()
    xg_loc_sim = np.maximum(0.05, rng.normal(xg_loc, xg_loc * 0.10, num_simulaciones))
    xg_vis_sim = np.maximum(0.05, rng.normal(xg_vis, xg_vis * 0.10, num_simulaciones))

    goles_loc = rng.poisson(xg_loc_sim)
    goles_vis = rng.poisson(xg_vis_sim)

    prob_loc_mc = (np.sum(goles_loc > goles_vis) / num_simulaciones) * 100
    prob_emp_mc = (np.sum(goles_loc == goles_vis) / num_simulaciones) * 100
    prob_vis_mc = (np.sum(goles_vis > goles_loc) / num_simulaciones) * 100

    return prob_loc_mc, prob_emp_mc, prob_vis_mc, goles_loc + goles_vis

def calcular_top_resultados(xg_loc, xg_vis, prob_loc_target, prob_emp_target, prob_vis_target):
    scores = {}
    prob_loc_poisson = 0.0
    prob_emp_poisson = 0.0
    prob_vis_poisson = 0.0
    poisson_matriz = {}

    for i in range(7):
        for j in range(7):
            p = poisson_prob(xg_loc, i) * poisson_prob(xg_vis, j)
            poisson_matriz[(i, j)] = p
            if i > j: prob_loc_poisson += p
            elif i == j: prob_emp_poisson += p
            else: prob_vis_poisson += p

    factor_loc = (prob_loc_target / 100.0) / max(0.0001, prob_loc_poisson)
    factor_emp = (prob_emp_target / 100.0) / max(0.0001, prob_emp_poisson)
    factor_vis = (prob_vis_target / 100.0) / max(0.0001, prob_vis_poisson)

    for (i, j), p in poisson_matriz.items():
        if i > j: p_ajustada = p * factor_loc
        elif i == j: p_ajustada = p * factor_emp
        else: p_ajustada = p * factor_vis
        scores[f"{i}-{j}"] = p_ajustada * 100

    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    top_5 = sorted_scores[:5]
    prob_otro = max(0.0, 100.0 - sum(p for _, p in top_5))

    return top_5, prob_otro

def calcular_mercados_adicionales(xg_loc, xg_vis):
    prob_under_2_5 = 0.0
    prob_btts = 0.0

    for i in range(7):
        for j in range(7):
            p = poisson_prob(xg_loc, i) * poisson_prob(xg_vis, j)
            if (i + j) < 2.5: prob_under_2_5 += p
            if i > 0 and j > 0: prob_btts += p

    return (1.0 - prob_under_2_5) * 100, prob_under_2_5 * 100, prob_btts * 100

def calcular_indice_volatilidad(xg_loc, xg_vis, stats_loc, stats_vis):
    vol_goles = min(40.0, ((xg_loc + xg_vis) / 3.5) * 40.0)
    vol_defensa = ((100.0 - ((stats_loc["Fortaleza"] + stats_vis["Fortaleza"]) / 2.0)) / 100.0) * 30.0
    vol_paridad = max(0.0, 30.0 - (abs(xg_loc - xg_vis) * 20.0))

    indice = min(99.0, max(10.0, vol_goles + vol_defensa + vol_paridad))
    if indice >= 65:
        categoria, color = "ALTA (Partido Impredecible)", "red"
    elif indice >= 40:
        categoria, color = "MEDIA (Desarrollo Dinamico)", "orange"
    else:
        categoria, color = "BAJA (Partido Estructurado)", "green"

    return round(indice, 1), categoria, color

def obtener_historial_directo(equipo_a, equipo_b):
    semilla_str = f"{min(equipo_a, equipo_b)}_{max(equipo_a, equipo_b)}"
    seed = int(hashlib.sha256(semilla_str.encode('utf-8')).hexdigest(), 16) % (2**32 - 1)
    rng = np.random.default_rng(seed)

    es_inverso = equipo_a != min(equipo_a, equipo_b)
    historial_base = rng.choice(['G', 'E', 'P'], 5, p=[0.38, 0.32, 0.30]).tolist()

    if es_inverso:
        return ['P' if r == 'G' else 'G' if r == 'P' else 'E' for r in historial_base]
    return historial_base

def render_h2h_pills(historial, local, visitante):
    html = "<div style='text-align: center; font-size: 12px; color: #94a3b8; margin-bottom: 10px;'>"
    html += f"<span style='color: #00ffcc; font-weight: bold;'>G</span> = Gano {local} &nbsp;&nbsp;|&nbsp;&nbsp; "
    html += "<span style='color: #cbd5e1; font-weight: bold;'>E</span> = Empate &nbsp;&nbsp;|&nbsp;&nbsp; "
    html += f"<span style='color: #ff3366; font-weight: bold;'>P</span> = Gano {visitante}</div>"
    html += "<div style='display: flex; gap: 8px; justify-content: center; margin-bottom: 20px;'>"

    for res in historial:
        color = "#00ffcc" if res == 'G' else "#cbd5e1" if res == 'E' else "#ff3366"
        bg = "rgba(0, 255, 204, 0.2)" if res == 'G' else "rgba(203, 213, 225, 0.2)" if res == 'E' else "rgba(255, 51, 102, 0.2)"
        tooltip = f"Gano {local}" if res == 'G' else "Empate" if res == 'E' else f"Gano {visitante}"
        html += f"<div title='{tooltip}' style='background-color: {bg}; color: {color}; width: 32px; height: 32px; border: 2px solid {color}; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: 900; font-size: 14px; box-shadow: 0 0 5px {color}80; cursor: help;'>{res}</div>"

    html += "</div>"
    return html

# =====================================================================
# CALCULO TOP 3 JUGADORES CON MAS PROBABILIDAD DEL DIA
# =====================================================================
def calcular_top_3_goleadores_dia(partidos_del_dia, df_unificado):
    if df_unificado.empty or not partidos_del_dia:
        return []

    df_defensas = df_unificado.copy()
    df_defensas["GC_prom"] = df_defensas["GC"] / np.maximum(1, df_defensas["PJ"])
    df_defensas = df_defensas.sort_values(by=["GC_prom", "GC"], ascending=[False, False]).reset_index(drop=True)
    
    ranking_defensas = {}
    for idx, row in df_defensas.iterrows():
        ranking_defensas[row["Equipo"]] = idx + 1

    candidatos = []

    for partido in partidos_del_dia:
        eq_loc = partido["Local"]
        eq_vis = partido["Visitante"]

        puesto_loc_gc = ranking_defensas.get(eq_loc, 15)
        puesto_vis_gc = ranking_defensas.get(eq_vis, 15)

        for jugador in JUGADORES_LPF:
            nombre = jugador["nombre"]
            eq_jugador = jugador["equipo"]
            prom_goles = jugador["prom_goles"]

            if buscar_equipo(eq_jugador, [eq_loc]):
                rival = eq_vis
                puesto_rival = puesto_vis_gc
            elif buscar_equipo(eq_jugador, [eq_vis]):
                rival = eq_loc
                puesto_rival = puesto_loc_gc
            else:
                continue

            prob_base = min(85.0, prom_goles * 100.0)

            descuento_pct = puesto_rival * 1.5
            prob_final = max(5.0, prob_base - descuento_pct)
            cuota_justa = round(100.0 / max(0.1, prob_final), 2)
            escudo_jugador = obtener_escudo_equipo(eq_jugador, df_unificado)

            candidatos.append({
                "nombre": nombre,
                "equipo": eq_jugador,
                "escudo": escudo_jugador,
                "rival": rival,
                "puesto_rival_defensa": puesto_rival,
                "probabilidad": round(prob_final, 1),
                "cuota_justa": cuota_justa
            })

    candidatos.sort(key=lambda x: x["probabilidad"], reverse=True)
    return candidatos[:3]

# =====================================================================
# 6. MOTOR DE PREDICCION CON HISTORIAL EXPONENCIAL REAL
# =====================================================================
def realizar_prediccion(local, visitante, df, stats_loc, stats_vis, xg_proyectado_local, xg_proyectado_visi, factor_localia=0.15, historial_h2h=[], paquete_ia=None):
    jer_loc = obtener_jerarquia(local)
    jer_vis = obtener_jerarquia(visitante)

    row_loc = df[df["Equipo"] == local].iloc[0]
    row_vis = df[df["Equipo"] == visitante].iloc[0]

    partidos_10_loc = obtener_ultimos_10_partidos_espn(row_loc.get("ID_ESPN"))
    partidos_10_vis = obtener_ultimos_10_partidos_espn(row_vis.get("ID_ESPN"))

    if paquete_ia and "modelo" in paquete_ia and "mapa_equipos" in paquete_ia:
        mapa = paquete_ia["mapa_equipos"]
        modelo = paquete_ia["modelo"]
        features_req = paquete_ia.get("features", [])

        if local in mapa and visitante in mapa:
            pts_u5_loc = float(stats_loc.get("Pts_U5", 7.5))
            pts_u5_vis = float(stats_vis.get("Pts_U5", 7.5))
            data_dict = {
                "local_cod": mapa[local],
                "visitante_cod": mapa[visitante],
                "local_jerarquia": jer_loc,
                "visitante_jerarquia": jer_vis,
                "dif_jerarquia": jer_loc - jer_vis,
                "local_gf_5": stats_loc.get("GF", 1.2) / max(1, stats_loc.get("PJ", 1)),
                "local_gc_5": 1.0,
                "local_pts_5": pts_u5_loc / 5.0,
                "local_pts_ajustados_5": pts_u5_loc / 5.0,
                "visita_gf_5": stats_vis.get("GF", 1.0) / max(1, stats_vis.get("PJ", 1)),
                "visita_gc_5": 1.0,
                "visita_pts_5": pts_u5_vis / 5.0,
                "visita_pts_ajustados_5": pts_u5_vis / 5.0,
            }
            row_input = pd.DataFrame([{col: data_dict.get(col, 0) for col in features_req}]) if features_req else pd.DataFrame([data_dict])

            try:
                probs = modelo.predict_proba(row_input)[0]
                clases = list(modelo.classes_)
                return float(probs[clases.index(1)]) * 100.0, float(probs[clases.index(0)]) * 100.0, float(probs[clases.index(2)]) * 100.0, True
            except Exception:
                pass

    base_loc = calcular_score_forma_exponencial_real(partidos_10_loc, jer_loc)
    base_vis = calcular_score_forma_exponencial_real(partidos_10_vis, jer_vis)

    pj_loc = max(1.0, float(row_loc.get("PJ", 1)))
    pj_vis = max(1.0, float(row_vis.get("PJ", 1)))
    bonus_tabla_loc = ((float(row_loc.get("Puntos", 0)) / pj_loc) / 3.0) * 0.03
    bonus_tabla_vis = ((float(row_vis.get("Puntos", 0)) / pj_vis) / 3.0) * 0.03

    power_loc = base_loc * (1.0 + bonus_tabla_loc)
    power_vis = base_vis * (1.0 + bonus_tabla_vis)

    dif_jer = jer_loc - jer_vis
    if dif_jer > 0:
        power_loc *= (1.0 + (dif_jer * 0.08))
    elif dif_jer < 0:
        power_vis *= (1.0 + (abs(dif_jer) * 0.08))

    power_loc_ajustado = power_loc * (1.0 + factor_localia)
    power_vis_ajustado = power_vis

    bono_h2h = (historial_h2h.count('G') - historial_h2h.count('P')) * 0.025
    power_loc_ajustado *= max(0.1, (1.0 + bono_h2h))

    total_power = max(0.1, power_loc_ajustado + power_vis_ajustado)

    dif_power = abs(power_loc_ajustado - power_vis_ajustado)
    prob_empate = max(20.0, min(36.0, 34.0 - (dif_power * 3.2)))

    resto = 100.0 - prob_empate
    prob_loc = (power_loc_ajustado / total_power) * resto
    prob_vis = (power_vis_ajustado / total_power) * resto

    return prob_loc, prob_empate, prob_vis, False

def buscar_equipo(nombre_buscado, lista_equipos):
    nombre_clean = nombre_buscado.lower().strip()
    for eq in lista_equipos:
        if nombre_clean == eq.lower().strip(): return eq
    for eq in lista_equipos:
        if nombre_clean in eq.lower().strip() or eq.lower().strip() in nombre_clean: return eq
    return None

@st.cache_data(ttl=1800)
def obtener_partidos_hoy_auto(equipos_disponibles):
    ahora_arg = datetime.datetime.utcnow() - datetime.timedelta(hours=3)
    fecha_hoy_str = ahora_arg.strftime("%Y-%m-%d")
    url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/arg.1/scoreboard?dates={ahora_arg.strftime('%Y%m%d')}"
    partidos_hoy = []

    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            for event in r.json().get("events", []):
                fecha_partido_arg = datetime.datetime.strptime(event["date"], "%Y-%m-%dT%H:%MZ") - datetime.timedelta(hours=3)
                if fecha_partido_arg.strftime("%Y-%m-%d") == fecha_hoy_str:
                    comps = event["competitions"][0]["competitors"]
                    loc_raw = comps[0]["team"]["name"] if comps[0]["homeAway"] == "home" else comps[1]["team"]["name"]
                    vis_raw = comps[1]["team"]["name"] if comps[0]["homeAway"] == "home" else comps[0]["team"]["name"]
                    loc_match = buscar_equipo(loc_raw, equipos_disponibles)
                    vis_match = buscar_equipo(vis_raw, equipos_disponibles)
                    if loc_match and vis_match and loc_match != vis_match:
                        partidos_hoy.append({"Local": loc_match, "Visitante": vis_match, "Hora": fecha_partido_arg.strftime("%H:%M")})
    except Exception:
        pass
    return partidos_hoy

def consolidar_estadisticas(equipo, df, xg_proyectado):
    row = df[df["Equipo"] == equipo].iloc[0]
    pj = max(1, int(row.get("PJ", 1)))
    jerarquia = obtener_jerarquia(equipo)

    partidos_10 = obtener_ultimos_10_partidos_espn(row.get("ID_ESPN"))
    
    gf = float(row.get("GF", 0))
    gc = float(row.get("GC", 0))
    puntos = float(row.get("Puntos", 0))
    
    pts_u5 = sum(p["Puntos"] for p in partidos_10[:5]) if len(partidos_10) >= 5 else (puntos / pj) * min(5, pj)
    
    potencia_atk = min(100.0, max(20.0, (xg_proyectado / 2.5) * 100.0))
    fortaleza_def = min(100.0, max(20.0, 100.0 - ((gc / pj) * 35.0)))
    forma = min(100.0, max(20.0, (pts_u5 / 15.0) * 100.0))
    posicion = max(1, int(row.get("Pos", 15)))
    posesion = min(70.0, max(35.0, 48.0 + (jerarquia - 6.5) * 4.0))
    precision = min(90.0, max(65.0, 75.0 + (jerarquia - 6.5) * 3.0))
    corners = round(max(3.0, min(8.5, 4.5 + (jerarquia - 6.5) * 0.8)), 1)

    return {
        "Potencia": round(potencia_atk, 1),
        "Fortaleza": round(fortaleza_def, 1),
        "Forma": round(forma, 1),
        "Jerarquia": jerarquia,
        "Posicion": posicion,
        "Posesion": round(posesion, 1),
        "Precision": round(precision, 1),
        "Corners": corners,
        "GF": gf,
        "GC": gc,
        "PJ": pj,
        "Puntos": puntos,
        "Pts_U5": round(pts_u5, 1)
    }

def generar_radar(local, visitante, stats_loc, stats_vis):
    categorias = [
        "Ataque Proyectado", "Defensa", "Forma Reciente",
        "Jerarquía de Plantel", "Posesión Estimada", "Precisión Pase",
        "Presión (Corners)", "Ataque Proyectado"
    ]

    val_loc = [
        stats_loc["Potencia"], stats_loc["Fortaleza"], stats_loc["Forma"],
        (stats_loc["Jerarquia"] / 10.0) * 100.0, (stats_loc["Posesion"] / 70.0) * 100.0,
        (stats_loc["Precision"] / 90.0) * 100.0, (stats_loc["Corners"] / 8.5) * 100.0
    ]
    val_loc.append(val_loc[0])

    val_vis = [
        stats_vis["Potencia"], stats_vis["Fortaleza"], stats_vis["Forma"],
        (stats_vis["Jerarquia"] / 10.0) * 100.0, (stats_vis["Posesion"] / 70.0) * 100.0,
        (stats_vis["Precision"] / 90.0) * 100.0, (stats_vis["Corners"] / 8.5) * 100.0
    ]
    val_vis.append(val_vis[0])

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(r=val_loc, theta=categorias, fill="toself", name=local, line_color="#00ffcc", fillcolor="rgba(0, 255, 204, 0.25)"))
    fig.add_trace(go.Scatterpolar(r=val_vis, theta=categorias, fill="toself", name=visitante, line_color="#ff3366", fillcolor="rgba(255, 51, 102, 0.25)"))
    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 100], gridcolor="#1e293b", tickfont=dict(color="#64748b")),
            bgcolor="#070b14",
            angularaxis=dict(gridcolor="#1e293b", tickfont=dict(color="#cbd5e1", size=11))
        ),
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5, font=dict(color="#ffffff")),
        paper_bgcolor="#070b14",
        plot_bgcolor="#070b14",
        margin=dict(t=30, b=50, l=30, r=30)
    )
    return fig

# =====================================================================
# 7. HISTORIAL Y AGENTE AUTONOMO
# =====================================================================
DIRECTORIO_APP = os.path.dirname(os.path.abspath(__file__))
RUTA_HISTORIAL = os.path.join(DIRECTORIO_APP, "historial_predicciones.csv")

def depurar_partidos_cercanos(df_hist):
    if df_hist.empty or "Fecha" not in df_hist.columns:
        return df_hist
    df_temp = df_hist.copy()
    df_temp["Fecha_dt"] = pd.to_datetime(df_temp["Fecha"], errors="coerce")
    df_temp = df_temp.sort_values(by="Fecha_dt").reset_index(drop=True)
    fechas_ultimo_partido = {}
    indices_validos = []
    for idx, row in df_temp.iterrows():
        f_dt = row["Fecha_dt"]
        if pd.isna(f_dt):
            indices_validos.append(idx)
            continue
        loc, vis = str(row["Local"]), str(row["Visitante"])
        valido = True
        for equipo in (loc, vis):
            if equipo in fechas_ultimo_partido:
                dias_dif = (f_dt - fechas_ultimo_partido[equipo]).days
                if 0 <= dias_dif < 3:
                    valido = False
                    break
        if valido:
            indices_validos.append(idx)
            fechas_ultimo_partido[loc] = f_dt
            fechas_ultimo_partido[vis] = f_dt
    df_limpio = df_temp.loc[indices_validos].drop(columns=["Fecha_dt"]).reset_index(drop=True)
    return df_limpio

def inicializar_historial():
    columnas_requeridas = [
        "ID", "Fecha", "Local", "Visitante",
        "Prob_Loc", "Prob_Emp", "Prob_Vis",
        "Prediccion_1X2", "Marcador_Predicho",
        "Prob_Over25", "Prob_BTTS", "Corners_Est",
        "Goles_Local_Real", "Goles_Visita_Real",
        "Corners_Reales", "Estado"
    ]
    if not os.path.exists(RUTA_HISTORIAL):
        df_vacio = pd.DataFrame(columns=columnas_requeridas)
        df_vacio.to_csv(RUTA_HISTORIAL, index=False)
    else:
        try:
            df = pd.read_csv(RUTA_HISTORIAL)
            for col in columnas_requeridas:
                if col not in df.columns:
                    df[col] = np.nan
            df.to_csv(RUTA_HISTORIAL, index=False)
        except Exception:
            pass

def validar_y_sincronizar_resultados(df_hist):
    if df_hist.empty:
        return df_hist, False
    pendientes = df_hist[df_hist["Estado"] == "Pendiente"]
    if pendientes.empty:
        return df_hist, False

    hoy_str = datetime.date.today().strftime("%Y%m%d")
    url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/arg.1/scoreboard?dates={hoy_str}"
    hubo_cambios = False

    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            events = r.json().get("events", [])
            for event in events:
                status_type = event.get("status", {}).get("type", {})
                if status_type.get("completed", False):
                    comps = event["competitions"][0]["competitors"]
                    loc_api = comps[0]["team"]["displayName"] if comps[0]["homeAway"] == "home" else comps[1]["team"]["displayName"]
                    vis_api = comps[1]["team"]["displayName"] if comps[0]["homeAway"] == "home" else comps[0]["team"]["displayName"]
                    goles_loc = int(comps[0]["score"]) if comps[0]["homeAway"] == "home" else int(comps[1]["score"])
                    goles_vis = int(comps[1]["score"]) if comps[0]["homeAway"] == "home" else int(comps[0]["score"])

                    for idx, row in pendientes.iterrows():
                        loc_row = str(row["Local"])
                        vis_row = str(row["Visitante"])
                        if (loc_api.lower() in loc_row.lower() or loc_row.lower() in loc_api.lower()) and \
                           (vis_api.lower() in vis_row.lower() or vis_row.lower() in vis_api.lower()):
                            df_hist.at[idx, "Goles_Local_Real"] = goals_loc = goles_loc
                            df_hist.at[idx, "Goles_Visita_Real"] = goals_vis = goles_vis
                            
                            c_totales = np.nan
                            try:
                                url_summary = f"https://site.api.espn.com/apis/site/v2/sports/soccer/arg.1/summary?event={event['id']}"
                                r_sum = requests.get(url_summary, timeout=8)
                                if r_sum.status_code == 200:
                                    box = r_sum.json().get("boxscore", {}).get("teams", [])
                                    cc = 0
                                    for t_stats in box:
                                        for st_item in t_stats.get("statistics", []):
                                            if st_item.get("name") == "wonCorners" or st_item.get("label", "").lower() == "tiros de esquina":
                                                cc += int(st_item.get("displayValue", 0))
                                    if cc > 0:
                                        c_totales = cc
                            except Exception:
                                pass

                            df_hist.at[idx, "Corners_Reales"] = c_totales
                            df_hist.at[idx, "Estado"] = "Finalizado"
                            hubo_cambios = True
    except Exception:
        pass

    return df_hist, hubo_cambios

def ejecutar_agente_autonomo(df_datos, partidos_del_dia):
    inicializar_historial()
    if df_datos.empty:
        return

    try:
        df_hist = pd.read_csv(RUTA_HISTORIAL)
    except Exception:
        return

    df_hist, hubo_cambios = validar_y_sincronizar_resultados(df_hist)
    nuevos = 0
    fecha_hoy = datetime.date.today().strftime("%Y-%m-%d")
    existentes = set(zip(df_hist["Fecha"].astype(str), df_hist["Local"].astype(str), df_hist["Visitante"].astype(str)))

    for p in partidos_del_dia:
        loc, vis = p["Local"], p["Visitante"]
        if (fecha_hoy, str(loc), str(vis)) not in existentes and loc in df_datos["Equipo"].values and vis in df_datos["Equipo"].values:
            pid = f"{fecha_hoy}_{loc.replace(' ', '')[:4].upper()}_{vis.replace(' ', '')[:4].upper()}"
            xl_base = float(df_datos[df_datos["Equipo"] == loc].iloc[0].get("xG", 1.25))
            xv_base = float(df_datos[df_datos["Equipo"] == vis].iloc[0].get("xG", 1.10))
            xgl = round(xl_base * 1.15, 2)
            xgv = round(xv_base * 0.925, 2)

            sl = consolidar_estadisticas(loc, df_datos, xgl)
            sv = consolidar_estadisticas(vis, df_datos, xgv)
            h2h = obtener_historial_directo(loc, vis)

            pl, pe, pv, _ = realizar_prediccion(loc, vis, df_datos, sl, sv, xgl, xgv, 0.15, h2h, paquete_ia)
            po25, _, pbtts = calcular_mercados_adicionales(xgl, xgv)
            top_marc, _ = calcular_top_resultados(xgl, xgv, pl, pe, pv)
            marcador_top = top_marc[0][0] if top_marc else "1-1"
            corn_est = round(sl["Corners"] + sv["Corners"], 1)

            p1x2 = "Local" if pl > pe and pl > pv else "Visitante" if pv > pl and pv > pe else "Empate"

            n_fila = pd.DataFrame([{
                "ID": pid,
                "Fecha": fecha_hoy,
                "Local": loc,
                "Visitante": vis,
                "Prob_Loc": round(pl, 1),
                "Prob_Emp": round(pe, 1),
                "Prob_Vis": round(pv, 1),
                "Prediccion_1X2": p1x2,
                "Marcador_Predicho": marcador_top,
                "Prob_Over25": round(po25, 1),
                "Prob_BTTS": round(pbtts, 1),
                "Corners_Est": corn_est,
                "Goles_Local_Real": np.nan,
                "Goles_Visita_Real": np.nan,
                "Corners_Reales": np.nan,
                "Estado": "Pendiente"
            }])
            df_hist = pd.concat([df_hist, n_fila], ignore_index=True)
            hubo_cambios = True
            nuevos += 1

    if hubo_cambios:
        try:
            df_hist.to_csv(RUTA_HISTORIAL, index=False)
        except Exception:
            pass

# =====================================================================
# 8. SISTEMA DE NAVEGACIÓN PRINCIPAL (FACHERO Y GRANDE PARA MÓVIL)
# =====================================================================
grupos = obtener_grupos_en_vivo_espn()
listas_grupos = [df for df in grupos.values() if not df.empty]
df_unificado = pd.concat(listas_grupos, ignore_index=True) if listas_grupos else pd.DataFrame()

equipos_disponibles = sorted(list(df_unificado["Equipo"].unique())) if not df_unificado.empty else sorted(list(JERARQUIA_EQUIPOS.keys()))
partidos_del_dia = obtener_partidos_hoy_auto(equipos_disponibles)
ejecutar_agente_autonomo(df_unificado, partidos_del_dia)

st.markdown('<div class="neon-title">⚽ WIN PREDICTOR | LPF</div>', unsafe_allow_html=True)
st.markdown('<div class="tech-sub">SISTEMA INTELIGENTE DE PRONÓSTICOS Y CUOTAS JUSTAS</div>', unsafe_allow_html=True)

# Selectbox mejorado estilo App Móvil
opciones_pantallas = ["Predicción de Partido", "Cuotas Justas y Opciones de Valor", "Posiciones y Zonas"]
opcion_pantalla = st.selectbox(
    "📱 SELECCIONAR SECCIÓN:",
    opciones_pantallas,
    index=0
)
st.markdown("---")

# =====================================================================
# PANTALLA 1: PREDICCIÓN DE PARTIDO
# =====================================================================
if opcion_pantalla == "Predicción de Partido":
    if df_unificado.empty:
        st.warning("⚠️ No se pudo obtener la tabla actualizada de ESPN.")
    else:
        col1, col2 = st.columns(2)
        with col1:
            local = st.selectbox("🏠 Equipo Local:", equipos_disponibles, index=0)
        with col2:
            equipos_vis = [eq for eq in equipos_disponibles if eq != local]
            visitante = st.selectbox("✈️ Equipo Visitante:", equipos_vis, index=0)

        with st.expander("🛠️ Parámetros de Simulación (Opcional)"):
            c_f1, c_f2 = st.columns(2)
            with c_f1:
                FACTOR_LOCALIA = st.slider("Bono de Localía (%)", min_value=0, max_value=30, value=15, step=1) / 100.0
            with c_f2:
                N_SIMULACIONES = st.number_input("Iteraciones Monte Carlo", min_value=1000, max_value=20000, value=10000, step=1000)

        if st.button("🚀 GENERAR PRONÓSTICO MÓVIL"):
            with st.spinner("Computando redes neuronales, Poisson y Monte Carlo..."):
                row_loc = df_unificado[df_unificado["Equipo"] == local].iloc[0]
                row_vis = df_unificado[df_unificado["Equipo"] == visitante].iloc[0]

                xg_base_loc = float(row_loc.get("xG", 1.25))
                xg_base_vis = float(row_vis.get("xG", 1.10))

                xg_proyectado_local = round(xg_base_loc * (1.0 + FACTOR_LOCALIA), 2)
                xg_proyectado_visi = round(xg_base_vis * (1.0 - (FACTOR_LOCALIA * 0.5)), 2)

                stats_loc = consolidar_estadisticas(local, df_unificado, xg_proyectado_local)
                stats_vis = consolidar_estadisticas(visitante, df_unificado, xg_proyectado_visi)
                historial_h2h = obtener_historial_directo(local, visitante)

                prob_loc, prob_empate, prob_vis, es_ia = realizar_prediccion(
                    local, visitante, df_unificado, stats_loc, stats_vis,
                    xg_proyectado_local, xg_proyectado_visi,
                    factor_localia=FACTOR_LOCALIA,
                    historial_h2h=historial_h2h,
                    paquete_ia=paquete_ia
                )

                escudo_loc = obtener_escudo_equipo(local, df_unificado)
                escudo_vis = obtener_escudo_equipo(visitante, df_unificado)

                # Tarjetas de escudos (Responsivas para celular)
                col_esc1, col_esc2 = st.columns(2)
                with col_esc1:
                    st.markdown(f"""
                        <div class="team-shield-box">
                            <img src="{escudo_loc}" class="team-shield-img" />
                            <div style="font-weight: 800; color: #ffffff; margin-top: 8px;">{local.upper()}</div>
                            <div style="font-size: 11px; color: #00ffcc;">LOCAL</div>
                        </div>
                    """, unsafe_allow_html=True)
                with col_esc2:
                    st.markdown(f"""
                        <div class="team-shield-box">
                            <img src="{escudo_vis}" class="team-shield-img" />
                            <div style="font-weight: 800; color: #ffffff; margin-top: 8px;">{visitante.upper()}</div>
                            <div style="font-size: 11px; color: #ff3366;">VISITANTE</div>
                        </div>
                    """, unsafe_allow_html=True)

                if es_ia:
                    st.success("Proyección ejecutada mediante Red Neural Recursiva & Árboles de Decisión Estocásticos")
                else:
                    st.info("Proyección ejecutada: Algoritmo de Decaimiento Exponencial Temporal & Ponderación Jerárquica H2H")

                st.markdown("<p style='text-align: center; color: #94a3b8; font-size: 13px; margin-bottom: 5px;'>HISTORIAL DIRECTO SIMULADO (ÚLTIMOS 5 PARTIDOS)</p>", unsafe_allow_html=True)
                st.markdown(render_h2h_pills(historial_h2h, local, visitante), unsafe_allow_html=True)

                m_col1, m_col2, m_col3 = st.columns(3)
                with m_col1:
                    st.metric(label=f"GANA {local.upper()}", value=f"{prob_loc:.1f}%")
                with m_col2:
                    st.metric(label="EMPATE", value=f"{prob_empate:.1f}%")
                with m_col3:
                    st.metric(label=f"GANA {visitante.upper()}", value=f"{prob_vis:.1f}%")

                st.markdown("---")
                prob_o25, prob_u25, prob_btts = calcular_mercados_adicionales(xg_proyectado_local, xg_proyectado_visi)
                mc_loc, mc_emp, mc_vis, total_goles_sim = simular_monte_carlo(xg_proyectado_local, xg_proyectado_visi, num_simulaciones=N_SIMULACIONES)

                s_col1, s_col2, s_col3 = st.columns(3)
                with s_col1:
                    st.metric(label="MÁS DE 2.5 GOLES", value=f"{prob_o25:.1f}%")
                with s_col2:
                    st.metric(label="AMBOS ANOTAN (BTTS)", value=f"{prob_btts:.1f}%")
                with s_col3:
                    st.metric(label="CORNERS EST.", value=f"{round(stats_loc['Corners'] + stats_vis['Corners'], 1)}")

                st.markdown("---")
                st.markdown("<h4 style='color: #cbd5e1;'>Simulación Monte Carlo: Distribución de Goles</h4>", unsafe_allow_html=True)
                
                fig_hist = go.Figure()
                fig_hist.add_trace(go.Histogram(x=total_goles_sim, nbinsx=10, marker_color="#00f3ff", opacity=0.75))
                fig_hist.update_layout(
                    title_text=f"Frecuencia de Goles en {N_SIMULACIONES} Simulaciones",
                    xaxis_title="Escenarios de Goles",
                    yaxis_title="Frecuencia",
                    paper_bgcolor="#070b14",
                    plot_bgcolor="#111827",
                    font=dict(color="#cbd5e1"),
                    margin=dict(t=40, b=40, l=30, r=30),
                )
                st.plotly_chart(fig_hist, use_container_width=True)

                st.markdown("---")
                st.markdown("<h4 style='color: #cbd5e1;'>Frente a Frente: Análisis Octagonal</h4>", unsafe_allow_html=True)
                fig_radar = generar_radar(local, visitante, stats_loc, stats_vis)
                st.plotly_chart(fig_radar, use_container_width=True)

                st.markdown("---")
                st.markdown("<h4 style='color: #cbd5e1;'>Top 5 Marcadores Exactos Más Probables</h4>", unsafe_allow_html=True)
                top_5_marcadores, prob_otro = calcular_top_resultados(xg_proyectado_local, xg_proyectado_visi, prob_loc, prob_empate, prob_vis)
                
                tabla_marcadores = [
                    {"Ranking": f"#{rank}", "Resultado Exacto": marcador, "Probabilidad": f"{prob:.1f}%"}
                    for rank, (marcador, prob) in enumerate(top_5_marcadores, 1)
                ]
                tabla_marcadores.append({"Ranking": "Otros", "Resultado Exacto": "Cualquier otro resultado", "Probabilidad": f"{prob_otro:.1f}%"})
                st.dataframe(pd.DataFrame(tabla_marcadores), use_container_width=True, hide_index=True)

# =====================================================================
# PANTALLA 2: CUOTAS JUSTAS & OPCIONES DE VALOR
# =====================================================================
elif opcion_pantalla == "Cuotas Justas y Opciones de Valor":
    st.markdown('<div class="neon-title">ANÁLISIS DE CUOTAS JUSTAS Y VALOR</div>', unsafe_allow_html=True)
    st.markdown('<div class="tech-sub">EVALUACIÓN AUTOMÁTICA DE MERCADOS Y OPORTUNIDADES</div>', unsafe_allow_html=True)

    partidos_evaluar = partidos_del_dia
    if not partidos_evaluar and len(equipos_disponibles) >= 2:
        partidos_evaluar = [{"Local": equipos_disponibles[0], "Visitante": equipos_disponibles[1], "Hora": "20:00"}]

    if not partidos_evaluar:
        st.warning("No hay partidos programados para analizar hoy.")
    else:
        opciones_probables = []
        opciones_razonables = []
        opciones_poco_probables = []
        mejores_opciones = []

        for p in partidos_evaluar:
            loc, vis = p["Local"], p["Visitante"]
            row_l = df_unificado[df_unificado["Equipo"] == loc].iloc[0]
            row_v = df_unificado[df_unificado["Equipo"] == vis].iloc[0]

            xgl = round(float(row_l.get("xG", 1.25)) * 1.15, 2)
            xgv = round(float(row_v.get("xG", 1.10)) * 0.925, 2)

            sl = consolidar_estadisticas(loc, df_unificado, xgl)
            sv = consolidar_estadisticas(vis, df_unificado, xgv)
            h2h = obtener_historial_directo(loc, vis)

            pl, pe, pv, _ = realizar_prediccion(loc, vis, df_unificado, sl, sv, xgl, xgv, 0.15, h2h, paquete_ia)
            po25, pu25, pbtts = calcular_mercados_adicionales(xgl, xgv)
            
            p_dc_1x = pl + pe
            p_dc_x2 = pv + pe
            p_dc_12 = pl + pv
            p_o15 = round((1.0 - (poisson_prob(xgl,0)*poisson_prob(xgv,0) + poisson_prob(xgl,1)*poisson_prob(xgv,0) + poisson_prob(xgl,0)*poisson_prob(xgv,1))) * 100.0, 1)

            mercados = [
                ("Gana o Empata " + loc, p_dc_1x),
                ("Gana o Empata " + vis, p_dc_x2),
                ("Sin Empate (" + loc + " o " + vis + ")", p_dc_12),
                ("Más de 1.5 Goles Totales", p_o15),
                ("Más de 2.5 Goles Totales", po25),
                ("Menos de 2.5 Goles Totales", pu25),
                ("Ambos Equipos Anotan - SÍ", pbtts),
                ("Victoria Simple " + loc, pl),
                ("Empate Simple", pe),
                ("Victoria Simple " + vis, pv)
            ]

            for nom, prob in mercados:
                cuota_teo = round(100.0 / max(0.1, prob), 2) if prob > 0 else 99.00
                item = {
                    "Partido": f"{loc} vs {vis}",
                    "Mercado": nom,
                    "Probabilidad": f"{prob:.1f}%",
                    "Cuota Mínima Teórica": f"{cuota_teo:.2f}",
                    "_prob_num": prob,
                    "_cuota_num": cuota_teo
                }
                if prob >= 70.0:
                    opciones_probables.append(item)
                elif 50.0 <= prob < 70.0:
                    opciones_razonables.append(item)
                else:
                    if cuota_teo >= 2.10:
                        opciones_poco_probables.append(item)
                if prob >= 60.0 and cuota_teo >= 1.50:
                    mejores_opciones.append(item)

        # ---------------------------------------------------------------------
        # TOP 3 GOLEADORES DEL DÍA
        # ---------------------------------------------------------------------
        st.markdown("<h3 style='color: #00ffcc;'>Jugadores con más probabilidad de gol del día</h3>", unsafe_allow_html=True)
        st.caption("Los 3 atacantes con mayor probabilidad de convertir tras descontar la fortaleza defensiva del rival.")
        top_3_jugadores = calcular_top_3_goleadores_dia(partidos_evaluar, df_unificado)
        
        if top_3_jugadores:
            cols_j = st.columns(3)
            for i, jug in enumerate(top_3_jugadores):
                with cols_j[i]:
                    st.markdown(f"""
                        <div class="player-card">
                            <img src="{jug['escudo']}" style="max-height:50px; margin-bottom:8px;" />
                            <div class="player-name">{jug['nombre']}</div>
                            <div class="player-team">{jug['equipo']}</div>
                            <div class="player-stat">{jug['probabilidad']}%</div>
                            <div class="player-sub">Rival: {jug['rival']} (Def #{jug['puesto_rival_defensa']})</div>
                            <div style="margin-top:8px; font-weight:bold; color:#00ffcc;">Cuota Justa: {jug['cuota_justa']}</div>
                        </div>
                    """, unsafe_allow_html=True)
        else:
            st.info("No se encontraron coincidencias suficientes de atacantes y partidos para hoy.")

        st.markdown("---")

        # MEJORES OPCIONES DEL DÍA
        st.markdown("<h3 style='color: #00f3ff;'>Mejores Opciones del Día</h3>", unsafe_allow_html=True)
        st.caption("Selecciones con alta probabilidad estadística (≥ 60%) y excelente cuota de valor (≥ 1.50).")
        if mejores_opciones:
            df_m = pd.DataFrame(mejores_opciones).sort_values(by="_prob_num", ascending=False).drop(columns=["_prob_num", "_cuota_num"])
            st.dataframe(df_m, use_container_width=True, hide_index=True)
        else:
            st.info("Sin opciones en este rango de valor para la jornada actual.")

        st.markdown("---")

        # OPCIONES MUY PROBABLES
        st.markdown("<h3 style='color: #00ffcc;'>Opciones Muy Probables (> 70% de probabilidad)</h3>", unsafe_allow_html=True)
        st.caption("Escenarios de alta certeza estadística con cuotas teóricas menores.")
        if opciones_probables:
            df_p = pd.DataFrame(opciones_probables).sort_values(by="_prob_num", ascending=False).drop(columns=["_prob_num", "_cuota_num"])
            st.dataframe(df_p, use_container_width=True, hide_index=True)
        else:
            st.info("No se detectaron mercados superiores al 70% en los partidos analizados.")

        st.markdown("---")

        # OPCIONES RAZONABLES
        st.markdown("<h3 style='color: #ffb703;'>Opciones Razonables (50% - 70% de probabilidad)</h3>", unsafe_allow_html=True)
        st.caption("Escenarios equilibrados con probabilidades moderadas y cuotas significativamente más altas.")
        if opciones_razonables:
            df_r = pd.DataFrame(opciones_razonables).sort_values(by="_prob_num", ascending=False).drop(columns=["_prob_num", "_cuota_num"])
            st.dataframe(df_r, use_container_width=True, hide_index=True)
        else:
            st.info("Sin opciones registradas en el rango del 50% al 70%.")

        st.markdown("---")

        # OPCIONES POCO PROBABLES
        st.markdown("<h3 style='color: #ff3366;'>Opciones Poco Probables (< 50% de probabilidad)</h3>", unsafe_allow_html=True)
        st.caption("Opciones de riesgo superior pero con cuotas teóricas muy elevadas (superior a 2.10).")
        if opciones_poco_probables:
            df_poc = pd.DataFrame(opciones_poco_probables).sort_values(by="_cuota_num", ascending=False).head(15).drop(columns=["_prob_num", "_cuota_num"])
            st.dataframe(df_poc, use_container_width=True, hide_index=True)
        else:
            st.info("Sin opciones de alto riesgo registradas.")

# =====================================================================
# PANTALLA 3: POSICIONES Y ZONAS
# =====================================================================
elif opcion_pantalla == "Posiciones y Zonas":
    st.markdown('<div class="neon-title">POSICIONES Y ZONAS</div>', unsafe_allow_html=True)
    st.markdown('<div class="tech-sub">TABLA EN VIVO Y RENDIMIENTO HISTÓRICO</div>', unsafe_allow_html=True)

    cols_grupos = st.columns(len(grupos)) if grupos else [st]
    for idx, (nombre_grupo, df_g) in enumerate(grupos.items()):
        with cols_grupos[idx]:
            st.markdown(f"<h4 style='color: #00ffcc; text-align: center;'>{nombre_grupo}</h4>", unsafe_allow_html=True)
            df_mostrar_grupo = df_g.drop(columns=["ID_ESPN"], errors="ignore")
            st.dataframe(
                df_mostrar_grupo,
                column_config={
                    "Pos": st.column_config.NumberColumn("Pos", width="small"),
                    "Escudo": st.column_config.ImageColumn("Escudo", width="small"),
                },
                use_container_width=True,
                hide_index=True
            )

    st.markdown("---")
    st.markdown("<h3 style='color: #cbd5e1;'>Efectividad Histórica del Modelo</h3>", unsafe_allow_html=True)
    df_ef = pd.read_csv(RUTA_HISTORIAL) if os.path.exists(RUTA_HISTORIAL) else pd.DataFrame()
    
    if not df_ef.empty and "Estado" in df_ef.columns:
        finalizados = df_ef[df_ef["Estado"] == "Finalizado"].drop_duplicates(subset=['Fecha', 'Local', 'Visitante'], keep='first').copy()
        finalizados = depurar_partidos_cercanos(finalizados)
        if finalizados.empty:
            st.info("Las predicciones están almacenadas. Una vez finalizados los partidos, las métricas de precisión se actualizarán automáticamente.")
        else:
            finalizados["res_real_1x2"] = np.where(
                finalizados["Goles_Local_Real"] > finalizados["Goles_Visita_Real"], "Local",
                np.where(finalizados["Goles_Visita_Real"] > finalizados["Goles_Local_Real"], "Visitante", "Empate")
            )
            finalizados["acierto_1x2"] = (finalizados["Prediccion_1X2"] == finalizados["res_real_1x2"]).astype(int)
            finalizados["goles_totales_reales"] = finalizados["Goles_Local_Real"] + finalizados["Goles_Visita_Real"]
            finalizados["over25_real"] = (finalizados["goles_totales_reales"] > 2.5).astype(int)
            finalizados["pred_over25"] = (finalizados["Prob_Over25"] >= 50.0).astype(int)
            finalizados["acierto_o25"] = (finalizados["pred_over25"] == finalizados["over25_real"]).astype(int)

            acierto_1x2_pct = round((finalizados["acierto_1x2"].sum() / len(finalizados)) * 100.0, 1)
            acierto_o25_pct = round((finalizados["acierto_o25"].sum() / len(finalizados)) * 100.0, 1)

            e_col1, e_col2, e_col3 = st.columns(3)
            with e_col1:
                st.metric(label="ACIERTOS 1X2 (%)", value=f"{acierto_1x2_pct}%")
            with e_col2:
                st.metric(label="ACIERTOS OVER 2.5 (%)", value=f"{acierto_o25_pct}%")
            with e_col3:
                st.metric(label="PARTIDOS REGISTRADOS", value=f"{len(finalizados)}")

            st.markdown("#### Registro Detallado de Partidos Evaluados")
            df_vista_ef = finalizados[[
                "Fecha", "Local", "Visitante", "Prediccion_1X2",
                "res_real_1x2", "Marcador_Predicho",
                "Goles_Local_Real", "Goles_Visita_Real"
            ]].copy()
            st.dataframe(df_vista_ef.sort_values(by="Fecha", ascending=False), use_container_width=True, hide_index=True)
    else:
        st.info("Aún no hay predicciones evaluadas o el historial no se ha inicializado.")
