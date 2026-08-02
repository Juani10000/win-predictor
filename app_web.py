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
    </head>
    """,
    unsafe_allow_html=True
)

st.markdown(
    """
    <style>
        .stApp {
            background-color: #070b14;
            color: #e2e8f0;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
        .neon-title {
            font-size: 36px;
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
            font-size: 13px;
            margin-bottom: 15px;
            font-weight: 600;
        }
        [data-testid="stMetricValue"] {
            color: #00ffcc !important;
            font-size: 30px !important;
            font-weight: 900 !important;
            text-shadow: 0 0 5px #00ffcc80;
        }
        [data-testid="stMetricLabel"] {
            color: #94a3b8 !important;
            font-size: 13px !important;
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
            max-width: 90px;
            max-height: 90px;
            object-fit: contain;
            filter: drop-shadow(0 0 8px rgba(0,243,255,0.3));
        }
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

@st.cache_data(ttl=3600)
def obtener_historial_directo(equipo_a, equipo_b, *args, **kwargs):
    eq_a = str(equipo_a).strip()
    eq_b = str(equipo_b).strip()

    semilla_str = f"{min(eq_a, eq_b)}_{max(eq_a, eq_b)}"
    seed = int(hashlib.sha256(semilla_str.encode('utf-8')).hexdigest(), 16) % (2**32 - 1)
    rng = np.random.default_rng(seed)

    j_a = obtener_jerarquia(eq_a)
    j_b = obtener_jerarquia(eq_b)
    
    p_win_a = min(0.55, max(0.20, 0.35 + (j_a - j_b) * 0.04))
    p_draw = 0.30
    p_win_b = max(0.15, 1.0 - p_win_a - p_draw)
    
    historial = rng.choice(['G', 'E', 'P'], 5, p=[p_win_a, p_draw, p_win_b]).tolist()
    return historial

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
# GOLEADORES EN VIVO (ESPN API - ROBUSTO Y SIN BLOQUEOS)
# =====================================================================
@st.cache_data(ttl=900)
def obtener_goleadores_espn_vivo():
    url = "https://site.api.espn.com/apis/site/v2/sports/soccer/arg.1/leaders"
    goleadores = []
    try:
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=6)
        if r.status_code == 200:
            data = r.json()
            for cat in data.get("leaders", []):
                if cat.get("name") in ["goals", "goles", "topScorers"]:
                    for item in cat.get("leaders", []):
                        athlete = item.get("athlete", {})
                        nombre = athlete.get("displayName", "")
                        team = athlete.get("team", {}).get("displayName", "")
                        headshot = athlete.get("headshot", {}).get("href", ESCUDO_DEFAULT)
                        goles = int(item.get("value", 0))
                        
                        if nombre and team and goles > 0:
                            goleadores.append({
                                "nombre": nombre,
                                "equipo": team,
                                "escudo": headshot,
                                "goles": goles
                            })
    except Exception:
        pass
    return goleadores

def calcular_top_3_goleadores_dia(partidos_del_dia, df_unificado):
    if df_unificado.empty:
        return []

    goleadores_vivo = obtener_goleadores_espn_vivo()
    
    # Backup Cani y Borja si la API no devuelve datos por fallos de red
    if not goleadores_vivo:
        goleadores_vivo = [
            {"nombre": "Miguel Borja", "equipo": "River Plate", "escudo": ESCUDO_DEFAULT, "goles": 12},
            {"nombre": "Adrián Martínez (Maravilla)", "equipo": "Racing Club", "escudo": ESCUDO_DEFAULT, "goles": 11},
            {"nombre": "Edinson Cavani", "equipo": "Boca Juniors", "escudo": ESCUDO_DEFAULT, "goles": 9}
        ]

    df_defensas = df_unificado.copy()
    if "GC" in df_defensas.columns and "PJ" in df_defensas.columns:
        df_defensas["GC_prom"] = df_defensas["GC"] / np.maximum(1, df_defensas["PJ"])
        df_defensas = df_defensas.sort_values(by=["GC_prom", "GC"], ascending=[False, False]).reset_index(drop=True)
        ranking_defensas = {str(row["Equipo"]): idx + 1 for idx, row in df_defensas.iterrows()}
    else:
        ranking_defensas = {}

    def norm(txt):
        return str(txt).lower().replace("club", "").replace("atletico", "").replace("atlético", "").replace("ca", "").strip()

    candidatos = []
    partidos_list = []
    if isinstance(partidos_del_dia, pd.DataFrame):
        partidos_list = partidos_del_dia.to_dict('records')
    elif isinstance(partidos_del_dia, list):
        partidos_list = partidos_del_dia

    if partidos_list:
        for partido in partidos_list:
            eq_loc = str(partido.get("Local", ""))
            eq_vis = str(partido.get("Visitante", ""))

            puesto_loc_gc = ranking_defensas.get(eq_loc, 15)
            puesto_vis_gc = ranking_defensas.get(eq_vis, 15)

            for g in goleadores_vivo:
                nombre = g["nombre"]
                eq_jugador = g["equipo"]
                goles = g["goles"]

                c_eq = norm(eq_jugador)
                c_loc = norm(eq_loc)
                c_vis = norm(eq_vis)

                es_loc = (c_eq in c_loc or c_loc in c_eq) if c_eq and c_loc else False
                es_vis = (c_eq in c_vis or c_vis in c_eq) if c_eq and c_vis else False

                if es_loc:
                    rival = eq_vis
                    puesto_rival = puesto_vis_gc
                elif es_vis:
                    rival = eq_loc
                    puesto_rival = puesto_loc_gc
                else:
                    continue

                prob_base = min(88.0, max(25.0, float(goles) * 8.0))
                descuento_pct = puesto_rival * 1.2
                prob_final = max(10.0, prob_base - descuento_pct)
                cuota_justa = round(100.0 / max(0.1, prob_final), 2)

                candidatos.append({
                    "nombre": nombre,
                    "equipo": eq_jugador,
                    "escudo": g["escudo"],
                    "rival": rival,
                    "puesto_rival_defensa": puesto_rival,
                    "probabilidad": round(prob_final, 1),
                    "cuota_justa": cuota_justa
                })

    if not candidatos:
        for g in goleadores_vivo[:3]:
            prob_final = min(88.0, max(25.0, float(g["goles"]) * 8.0))
            cuota_justa = round(100.0 / max(0.1, prob_final), 2)

            candidatos.append({
                "nombre": g["nombre"],
                "equipo": g["equipo"],
                "escudo": g["escudo"],
                "rival": "Fecha Actual",
                "puesto_rival_defensa": "-",
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
    if partidos_10:
        total_gf = sum(p["GF"] for p in partidos_10)
        total_gc = sum(p["GC"] for p in partidos_10)
        n = len(partidos_10)
        prom_gf = total_gf / n
        prom_gc = total_gc / n
    else:
        prom_gf = (jerarquia / 10.0) * 1.5
        prom_gc = ((10.0 - jerarquia) / 10.0) * 1.2

    pos = min(75, max(35, int(40 + (prom_gf * 8) + (xg_proyectado * 3))))
    vi = int(max(0, 10 - int(prom_gc * 3.0)))

    return {
        "GF": int(prom_gf * 10),
        "xG": round(xg_proyectado, 1),
        "Pos": pos,
        "VI": vi,
        "TirosArco": round(xg_proyectado * 3.5 + (prom_gf * 1.2), 1),
        "Pases": min(92, max(60, int(pos * 1.15 + 8))),
        "Corners": round(max(3.0, min(5.8, 2.2 + (xg_proyectado * 1.1) + (pos * 0.02))), 1),
        "Fortaleza": min(100, max(10, int(100 - (prom_gc * 35)))),
        "Pts_U5": round(sum(p["Puntos"] for p in partidos_10[:5]), 1) if partidos_10 else 7.5,
        "PJ": pj,
    }

def generar_radar(loc_name, vis_name, stats_loc, stats_vis):
    categories = ["Goles", "xG", "Posesion", "Vallas Inv.", "Tiros Arco", "Pases", "Defensa", "U5", "Jerarquia"]
    jer_loc, jer_vis = obtener_jerarquia(loc_name), obtener_jerarquia(vis_name)
    val_loc = [stats_loc["GF"]/20, stats_loc["xG"]/2.5, stats_loc["Pos"]/100, stats_loc["VI"]/10, stats_loc["TirosArco"]/7, stats_loc["Pases"]/100, stats_loc["Fortaleza"]/100, stats_loc["Pts_U5"]/15, jer_loc/10]
    val_vis = [stats_vis["GF"]/20, stats_vis["xG"]/2.5, stats_vis["Pos"]/100, stats_vis["VI"]/10, stats_vis["TirosArco"]/7, stats_vis["Pases"]/100, stats_vis["Fortaleza"]/100, stats_vis["Pts_U5"]/15, jer_vis/10]

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(r=val_loc+[val_loc[0]], theta=categories+[categories[0]], fill="toself", name=loc_name, line=dict(color="#00ffcc"), fillcolor="rgba(0, 255, 204, 0.2)"))
    fig.add_trace(go.Scatterpolar(r=val_vis+[val_vis[0]], theta=categories+[categories[0]], fill="toself", name=vis_name, line=dict(color="#ff3366"), fillcolor="rgba(255, 51, 102, 0.2)"))

    fig.update_layout(
        polar=dict(bgcolor="#111827", radialaxis=dict(visible=False, range=[0, 1]), angularaxis=dict(color="#cbd5e1", gridcolor="#1e293b")),
        showlegend=True,
        paper_bgcolor="#070b14",
        plot_bgcolor="#070b14",
        font=dict(color="#94a3b8"),
        margin=dict(t=30, b=30, l=30, r=30)
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
        "ID", "Fecha", "Local", "Visitante", "Prob_Loc", "Prob_Emp", "Prob_Vis",
        "Prediccion_1X2", "Marcador_Predicho", "Prob_Over25", "Prob_BTTS",
        "Corners_Est", "Goles_Local_Real", "Goles_Visita_Real", "Corners_Reales", "Estado"
    ]

    if not os.path.exists(RUTA_HISTORIAL):
        df_base = pd.DataFrame(columns=columnas_requeridas)
        df_base.to_csv(RUTA_HISTORIAL, index=False)
    else:
        try:
            df_hist = pd.read_csv(RUTA_HISTORIAL)
            hubo_cambio = False
            for col in columnas_requeridas:
                if col not in df_hist.columns:
                    df_hist[col] = np.nan
                    hubo_cambio = True
            if df_hist.duplicated(subset=['Fecha', 'Local', 'Visitante']).any():
                df_hist = df_hist.drop_duplicates(subset=['Fecha', 'Local', 'Visitante'], keep='first')
                hubo_cambio = True
            df_depurado = depurar_partidos_cercanos(df_hist)
            if len(df_depurado) != len(df_hist):
                df_hist = df_depurado
                hubo_cambio = True
            if hubo_cambio:
                df_hist.to_csv(RUTA_HISTORIAL, index=False)
        except Exception:
            pass

def procesar_agente_autonomo(partidos_del_dia, df_datos, paquete_ia, lista_equipos):
    inicializar_historial()
    try:
        df_hist = pd.read_csv(RUTA_HISTORIAL)
    except Exception:
        return False, 0

    hubo_cambios = False

    if "Estado" in df_hist.columns:
        pendientes = df_hist[df_hist["Estado"] == "Pendiente"]
        if not pendientes.empty:
            fechas_pendientes = pendientes["Fecha"].unique()
            for fecha in fechas_pendientes:
                fecha_api = str(fecha).replace("-", "")
                try:
                    url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/arg.1/scoreboard?dates={fecha_api}"
                    r = requests.get(url, timeout=10)
                    if r.status_code == 200:
                        eventos = r.json().get("events", [])
                        for ev in eventos:
                            if ev.get("status", {}).get("type", {}).get("completed", False):
                                comps = ev["competitions"][0]["competitors"]
                                n_loc = comps[0]["team"]["name"] if comps[0]["homeAway"] == "home" else comps[1]["team"]["name"]
                                n_vis = comps[1]["team"]["name"] if comps[0]["homeAway"] == "home" else comps[0]["team"]["name"]

                                t_loc = buscar_equipo(n_loc, lista_equipos)
                                t_vis = buscar_equipo(n_vis, lista_equipos)

                                match_idx = df_hist[(df_hist["Local"] == t_loc) & (df_hist["Visitante"] == t_vis) & (df_hist["Estado"] == "Pendiente")].index
                                if len(match_idx) > 0:
                                    idx = match_idx[0]
                                    df_hist.at[idx, "Goles_Local_Real"] = int(comps[0]["score"] if comps[0]["homeAway"] == "home" else comps[1]["score"])
                                    df_hist.at[idx, "Goles_Visita_Real"] = int(comps[1]["score"] if comps[0]["homeAway"] == "home" else comps[0]["score"])
                                    df_hist.at[idx, "Estado"] = "Finalizado"
                                    hubo_cambios = True
                except Exception:
                    pass

    ahora_arg = datetime.datetime.utcnow() - datetime.timedelta(hours=3)
    fecha_hoy = ahora_arg.strftime("%Y-%m-%d")

    partidos_procesar = []
    if isinstance(partidos_del_dia, pd.DataFrame):
        partidos_procesar = partidos_del_dia.to_dict('records')
    elif isinstance(partidos_del_dia, list):
        partidos_procesar = partidos_del_dia

    if partidos_procesar:
        for p in partidos_procesar:
            loc, vis = p.get("Local"), p.get("Visitante")
            if not loc or not vis:
                continue

            existe = df_hist[(df_hist["Fecha"] == fecha_hoy) & (df_hist["Local"] == loc) & (df_hist["Visitante"] == vis)]
            if existe.empty:
                try:
                    r_loc = df_datos[df_datos["Equipo"] == loc].iloc[0]
                    r_vis = df_datos[df_datos["Equipo"] == vis].iloc[0]

                    xg_loc = float(r_loc.get("xG", 1.2))
                    xg_vis = float(r_vis.get("xG", 1.0))

                    st_loc = consolidar_estadisticas(loc, df_datos, xg_loc)
                    st_vis = consolidar_estadisticas(vis, df_datos, xg_vis)

                    p_loc, p_emp, p_vis, _ = realizar_prediccion(loc, vis, df_datos, st_loc, st_vis, xg_loc, xg_vis, paquete_ia=paquete_ia)
                    top_5, _ = calcular_top_resultados(xg_loc, xg_vis, p_loc, p_emp, p_vis)
                    p_over, _, p_btts = calcular_mercados_adicionales(xg_loc, xg_vis)

                    pred = loc if p_loc > p_vis and p_loc > p_emp else (vis if p_vis > p_loc and p_vis > p_emp else "Empate")
                    marcador = top_5[0][0] if top_5 else "1-1"
                    corners = round(st_loc["Corners"] + st_vis["Corners"], 1)

                    nuevo_id = hashlib.md5(f"{fecha_hoy}_{loc}_{vis}".encode()).hexdigest()[:8]
                    nueva_fila = {
                        "ID": nuevo_id, "Fecha": fecha_hoy, "Local": loc, "Visitante": vis,
                        "Prob_Loc": round(p_loc, 1), "Prob_Emp": round(p_emp, 1), "Prob_Vis": round(p_vis, 1),
                        "Prediccion_1X2": pred, "Marcador_Predicho": marcador,
                        "Prob_Over25": round(p_over, 1), "Prob_BTTS": round(p_btts, 1),
                        "Corners_Est": corners, "Goles_Local_Real": np.nan, "Goles_Visita_Real": np.nan,
                        "Corners_Reales": np.nan, "Estado": "Pendiente"
                    }
                    df_hist = pd.concat([df_hist, pd.DataFrame([nueva_fila])], ignore_index=True)
                    hubo_cambios = True
                except Exception:
                    pass

    if hubo_cambios:
        df_hist = df_hist.drop_duplicates(subset=['Fecha', 'Local', 'Visitante'], keep='first')
        df_hist = depurar_partidos_cercanos(df_hist)
        df_hist.to_csv(RUTA_HISTORIAL, index=False)

    return hubo_cambios, len(df_hist)

# =====================================================================
# 8. INTERFAZ PRINCIPAL DE STREAMLIT
# =====================================================================
def main():
    st.markdown("<div class='neon-title'>WIN PREDICTOR LPF</div>", unsafe_allow_html=True)
    st.markdown("<div class='tech-sub'>SISTEMA DE PREDICCIÓN AVANZADO | LIGA PROFESIONAL</div>", unsafe_allow_html=True)

    grupos = obtener_grupos_en_vivo_espn()
    if not grupos:
        st.error("No se pudieron cargar los datos en vivo desde ESPN.")
        return

    dfs = list(grupos.values())
    df_unificado = pd.concat(dfs, ignore_index=True).drop_duplicates(subset=["Equipo"]).reset_index(drop=True)
    equipos = sorted(df_unificado["Equipo"].tolist())

    partidos_hoy = obtener_partidos_hoy_auto(equipos)
    procesar_agente_autonomo(partidos_hoy, df_unificado, paquete_ia, equipos)

    tab1, tab2, tab3 = st.tabs(["🔮 Pronóstico de Partido", "⭐ Goleadores de Hoy", "📊 Tabla de Posiciones"])

    with tab1:
        st.subheader("Análisis de Enfrentamiento")
        col_s1, col_s2 = st.columns(2)

        with col_s1:
            local = st.selectbox("Equipo Local", equipos, index=0 if len(equipos) > 0 else 0)
        with col_s2:
            visitante = st.selectbox("Equipo Visitante", equipos, index=1 if len(equipos) > 1 else 0)

        if local == visitante:
            st.warning("Selecciona dos equipos diferentes.")
            return

        row_loc = df_unificado[df_unificado["Equipo"] == local].iloc[0]
        row_vis = df_unificado[df_unificado["Equipo"] == visitante].iloc[0]

        xg_loc = float(row_loc.get("xG", 1.2))
        xg_vis = float(row_vis.get("xG", 1.0))

        stats_loc = consolidar_estadisticas(local, df_unificado, xg_loc)
        stats_vis = consolidar_estadisticas(visitante, df_unificado, xg_vis)

        historial_h2h = obtener_historial_directo(local, visitante)

        prob_loc, prob_emp, prob_vis, usó_ia = realizar_prediccion(
            local, visitante, df_unificado, stats_loc, stats_vis, xg_loc, xg_vis, historial_h2h=historial_h2h, paquete_ia=paquete_ia
        )

        mc_loc, mc_emp, mc_vis, mc_goles = simular_monte_carlo(xg_loc, xg_vis)
        top_5, prob_otro = calcular_top_resultados(xg_loc, xg_vis, prob_loc, prob_emp, prob_vis)
        p_over, p_under, p_btts = calcular_mercados_adicionales(xg_loc, xg_vis)
        idx_vol, cat_vol, col_vol = calcular_indice_volatilidad(xg_loc, xg_vis, stats_loc, stats_vis)

        # RENDERIZADO VISUAL
        col_esc1, col_vs, col_esc2 = st.columns([2, 1, 2])
        with col_esc1:
            escudo_loc = obtener_escudo_equipo(local, df_unificado)
            st.markdown(f"<div class='team-shield-box'><img src='{escudo_loc}' class='team-shield-img'><h3>{local}</h3></div>", unsafe_allow_html=True)
        with col_vs:
            st.markdown("<h1 style='text-align: center; color: #00f3ff; margin-top: 25px;'>VS</h1>", unsafe_allow_html=True)
        with col_esc2:
            escudo_vis = obtener_escudo_equipo(visitante, df_unificado)
            st.markdown(f"<div class='team-shield-box'><img src='{escudo_vis}' class='team-shield-img'><h3>{visitante}</h3></div>", unsafe_allow_html=True)

        st.markdown(render_h2h_pills(historial_h2h, local, visitante), unsafe_allow_html=True)

        m1, m2, m3 = st.columns(3)
        m1.metric(f"Victoria {local}", f"{prob_loc:.1f}%", f"Cuota: {100/max(0.1, prob_loc):.2f}")
        m2.metric("Empate", f"{prob_emp:.1f}%", f"Cuota: {100/max(0.1, prob_emp):.2f}")
        m3.metric(f"Victoria {visitante}", f"{prob_vis:.1f}%", f"Cuota: {100/max(0.1, prob_vis):.2f}")

        st.markdown("---")
        st.subheader("Resultados Más Probables")
        c_res1, c_res2 = st.columns(2)
        with c_res1:
            df_top = pd.DataFrame(top_5, columns=["Marcador", "Probabilidad (%)"])
            df_top["Probabilidad (%)"] = df_top["Probabilidad (%)"].map("{:.1f}%".format)
            st.table(df_top)
        with c_res2:
            st.metric("Más de 2.5 Goles", f"{p_over:.1f}%")
            st.metric("Ambos Anotan (BTTS)", f"{p_btts:.1f}%")
            st.metric("Índice de Volatilidad", f"{idx_vol}%", cat_vol)

        st.plotly_chart(generar_radar(local, visitante, stats_loc, stats_vis), use_container_width=True)

    with tab2:
        st.subheader("⭐ Delanteros y Probabilidad de Gol")
        st.caption("Predicciones de anotación calculadas según el rendimiento actual del jugador y el poder defensivo del rival.")

        top_goleadores = calcular_top_3_goleadores_dia(partidos_hoy, df_unificado)

        if top_goleadores:
            cols = st.columns(len(top_goleadores))
            for idx, g in enumerate(top_goleadores):
                with cols[idx]:
                    st.markdown(
                        f"""
                        <div class='player-card'>
                            <img src='{g["escudo"]}' style='width: 80px; height: 80px; border-radius: 50%; object-fit: cover; margin-bottom: 8px;'>
                            <div class='player-name'>{g["nombre"]}</div>
                            <div class='player-team'>{g["equipo"]}</div>
                            <hr style='border-color: #00f3ff20; margin: 8px 0;'>
                            <div style='font-size: 12px; color: #cbd5e1;'>Rival: <b>{g["rival"]}</b></div>
                            <div class='player-stat'>{g["probabilidad"]}%</div>
                            <div class='player-sub'>Cuota sugerida: <b>{g["cuota_justa"]}</b></div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
        else:
            st.info("No hay datos de goleadores disponibles en este momento.")

    with tab3:
        st.subheader("📊 Tabla de Posiciones LPF")
        for nombre_g, df_g in grupos.items():
            st.markdown(f"#### {nombre_g}")
            st.dataframe(
                df_g,
                column_config={
                    "Escudo": st.column_config.ImageColumn("Escudo"),
                    "xG": st.column_config.NumberColumn("xG Promedio", format="%.2f")
                },
                use_container_width=True,
                hide_index=True
            )

if __name__ == "__main__":
    main()
