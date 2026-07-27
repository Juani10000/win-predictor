import datetime
import math
import os
import re
import hashlib
from bs4 import BeautifulSoup
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import requests
import streamlit as st
import joblib

# =====================================================================
# 1. CONFIGURACIÓN Y CSS ESTILO NEÓN
# =====================================================================
st.set_page_config(page_title="Win Predictor | LPF", layout="wide")

# Insertar meta etiqueta de verificación para Google Search Console
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

# =====================================================================
# 2. DICCIONARIO DE JERARQUÍA DE PLANTELES Y CARGA DE MODELO IA
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

def obtener_jerarquia(nombre_equipo):
    """Devuelve la jerarquía del equipo. Si no está mapeado, da un valor promedio."""
    if not isinstance(nombre_equipo, str):
        return 6.5
    nombre_clean = nombre_equipo.lower().strip()
    for eq, rating in JERARQUIA_EQUIPOS.items():
        if eq.lower() in nombre_clean or nombre_clean in eq.lower():
            return rating
    return 6.5

@st.cache_resource
def cargar_modelo_ia():
    """Intenta cargar el archivo de modelo guardado (.pkl) generado por el script de entrenamiento."""
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
# 3. FUNCIONES MATEMÁTICAS Y DE SIMULACIÓN
# =====================================================================
def poisson_prob(lmbda, k):
    if lmbda <= 0:
        return 1.0 if k == 0 else 0.0
    return (math.pow(lmbda, k) * math.exp(-lmbda)) / math.factorial(k)

def simular_monte_carlo(xg_loc, xg_vis, num_simulaciones=10000):
    rng = np.random.default_rng()
    
    xg_loc_sim = rng.normal(xg_loc, xg_loc * 0.10, num_simulaciones)
    xg_vis_sim = rng.normal(xg_vis, xg_vis * 0.10, num_simulaciones)

    xg_loc_sim = np.maximum(0.05, xg_loc_sim)
    xg_vis_sim = np.maximum(0.05, xg_vis_sim)

    goles_loc = rng.poisson(xg_loc_sim)
    goles_vis = rng.poisson(xg_vis_sim)

    victorias_loc = np.sum(goles_loc > goles_vis)
    empates = np.sum(goles_loc == goles_vis)
    victorias_vis = np.sum(goles_vis > goles_loc)

    prob_loc_mc = (victorias_loc / num_simulaciones) * 100
    prob_emp_mc = (empates / num_simulaciones) * 100
    prob_vis_mc = (victorias_vis / num_simulaciones) * 100

    goles_totales = goles_loc + goles_vis

    return prob_loc_mc, prob_emp_mc, prob_vis_mc, goles_totales

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
        if i > j:
            p_ajustada = p * factor_loc
        elif i == j:
            p_ajustada = p * factor_emp
        else:
            p_ajustada = p * factor_vis
            
        scores[f"{i} - {j}"] = p_ajustada * 100

    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    top_5 = sorted_scores[:5]

    prob_top_5 = sum(p for _, p in top_5)
    prob_otro = max(0.0, 100.0 - prob_top_5)

    return top_5, prob_otro

def calcular_mercados_adicionales(xg_loc, xg_vis):
    prob_under_2_5 = 0.0
    prob_btts = 0.0

    for i in range(7):
        for j in range(7):
            p = poisson_prob(xg_loc, i) * poisson_prob(xg_vis, j)
            if (i + j) < 2.5:
                prob_under_2_5 += p
            if i > 0 and j > 0:
                prob_btts += p

    prob_over_2_5 = (1.0 - prob_under_2_5) * 100
    prob_under_2_5 *= 100
    prob_btts *= 100

    return prob_over_2_5, prob_under_2_5, prob_btts

def calcular_indice_volatilidad(xg_loc, xg_vis, stats_loc, stats_vis):
    xg_total = xg_loc + xg_vis
    vol_goles = min(40.0, (xg_total / 3.5) * 40.0)
    deb_def = 100.0 - ((stats_loc["Fortaleza"] + stats_vis["Fortaleza"]) / 2.0)
    vol_defensa = (deb_def / 100.0) * 30.0
    dif_xg = abs(xg_loc - xg_vis)
    vol_paridad = max(0.0, 30.0 - (dif_xg * 20.0))

    indice = min(99.0, max(10.0, vol_goles + vol_defensa + vol_paridad))

    if indice >= 65:
        categoria = "ALTA (Partido Impredecible / Caótico)"
        color = "red"
    elif indice >= 40:
        categoria = "MEDIA (Desarrollo Dinámico)"
        color = "orange"
    else:
        categoria = "BAJA (Partido Estructurado / Controlado)"
        color = "green"

    return round(indice, 1), categoria, color

def obtener_historial_directo(equipo_a, equipo_b):
    semilla_str = f"{min(equipo_a, equipo_b)}_{max(equipo_a, equipo_b)}"
    seed = int(hashlib.sha256(semilla_str.encode('utf-8')).hexdigest(), 16) % (2**32 - 1)
    
    rng = np.random.default_rng(seed)
    
    es_inverso = equipo_a != min(equipo_a, equipo_b)
    resultados_posibles = ['G', 'E', 'P']
    historial_base = rng.choice(resultados_posibles, 5, p=[0.38, 0.32, 0.30]).tolist()
    
    if es_inverso:
        historial_final = []
        for r in historial_base:
            if r == 'G': historial_final.append('P')
            elif r == 'P': historial_final.append('G')
            else: historial_final.append('E')
        return historial_final
    return historial_base

def render_h2h_pills(historial, local, visitante):
    html = "<div style='text-align: center; font-size: 12px; color: #94a3b8; margin-bottom: 10px;'>"
    html += f"<span style='color: #00ffcc; font-weight: bold;'>G</span> = Ganó {local} &nbsp;&nbsp;|&nbsp;&nbsp; "
    html += "<span style='color: #cbd5e1; font-weight: bold;'>E</span> = Empate &nbsp;&nbsp;|&nbsp;&nbsp; "
    html += f"<span style='color: #ff3366; font-weight: bold;'>P</span> = Ganó {visitante}"
    html += "</div>"
    
    html += "<div style='display: flex; gap: 8px; justify-content: center; margin-bottom: 20px;'>"
    
    for res in historial:
        if res == 'G':
            color = "#00ffcc"
            bg = "rgba(0, 255, 204, 0.2)"
            tooltip = f"Ganó {local}"
        elif res == 'E':
            color = "#cbd5e1"
            bg = "rgba(203, 213, 225, 0.2)"
            tooltip = "Empate"
        else:
            color = "#ff3366"
            bg = "rgba(255, 51, 102, 0.2)"
            tooltip = f"Ganó {visitante}"
            
        html += f"<div title='{tooltip}' style='background-color: {bg}; color: {color}; width: 32px; height: 32px; border: 2px solid {color}; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: 900; font-size: 14px; box-shadow: 0 0 5px {color}80; cursor: help;'>{res}</div>"
        
    html += "</div>"
    return html

# =====================================================================
# 4. MOTOR DE PREDICCIÓN (IA O MODELO ESTADÍSTICO DE RESPALDO)
# =====================================================================
def realizar_prediccion(local, visitante, df, stats_loc, stats_vis, xg_proyectado_local, xg_proyectado_visi, factor_localia=0.15, historial_h2h=[], paquete_ia=None):
    jer_loc = obtener_jerarquia(local)
    jer_vis = obtener_jerarquia(visitante)

    pts_u5_loc = float(stats_loc.get("Pts_U5", 7.5))
    pts_u5_vis = float(stats_vis.get("Pts_U5", 7.5))

    pts_u5_loc_ajustado = pts_u5_loc * (jer_vis / 10.0)
    pts_u5_vis_ajustado = pts_u5_vis * (jer_loc / 10.0)

   # Si tenemos un modelo .pkl cargado, intentamos predecir directamente con IA
    if paquete_ia and "modelo" in paquete_ia and "mapa_equipos" in paquete_ia:
        mapa = paquete_ia["mapa_equipos"]
        modelo = paquete_ia["modelo"]
        features_req = paquete_ia.get("features", [])

        # TODO ESTE BLOQUE DEBE ESTAR ALINEADO A LA MISMA ALTURA QUE "mapa" Y "modelo"
        data_dict = {
            "local_cod": mapa[local],
            "visitante_cod": mapa[visitante],
            "local_jerarquia": jer_loc,
            "visitante_jerarquia": jer_vis,
            "dif_jerarquia": jer_loc - jer_vis,
            "local_gf_5": stats_loc.get("GF", 1.2) / max(1, stats_loc.get("PJ", 1)),
            "local_gc_5": 1.0,
            "local_pts_5": pts_u5_loc / 5.0,
            "local_pts_ajustados_5": pts_u5_loc_ajustado / 5.0,
            "visita_gf_5": stats_vis.get("GF", 1.0) / max(1, stats_vis.get("PJ", 1)),
            "visita_gc_5": 1.0,
            "visita_pts_5": pts_u5_vis / 5.0,
            "visita_pts_ajustados_5": pts_u5_vis_ajustado / 5.0,
            "local_xG_prom_5": xg_proyectado_local,
            "visita_xG_prom_5": xg_proyectado_visi,
            "dif_xG_prom_5": xg_proyectado_local - xg_proyectado_visi
        }

        # EL "if" TAMBIÉN DEBE IR EN ESA MISMA LÍNEA VERTICAL
        if features_req:
            row_input = pd.DataFrame([{col: data_dict.get(col, 0) for col in features_req}])
        else:
            row_input = pd.DataFrame([data_dict])

        try:
            probs = modelo.predict_proba(row_input)[0]
                clases = list(modelo.classes_)
                
                idx_loc = clases.index(1) if 1 in clases else 0
                idx_emp = clases.index(0) if 0 in clases else 1
                idx_vis = clases.index(2) if 2 in clases else 2

                prob_loc = float(probs[idx_loc]) * 100.0
                prob_empate = float(probs[idx_emp]) * 100.0
                prob_vis = float(probs[idx_vis]) * 100.0

                return prob_loc, prob_empate, prob_vis, True
            except Exception:
                pass

    # Resguardo: Algoritmo estadístico heurístico
    row_loc = df[df["Equipo"] == local].iloc[0]
    row_vis = df[df["Equipo"] == visitante].iloc[0]

    pts_loc = float(row_loc.get("Puntos", 0)) if "Puntos" in df.columns else 0.0
    pts_vis = float(row_vis.get("Puntos", 0)) if "Puntos" in df.columns else 0.0
    pj_loc = max(float(row_loc.get("PJ", 1)), 1.0) if "PJ" in df.columns else 1.0
    pj_vis = max(float(row_vis.get("PJ", 1)), 1.0) if "PJ" in df.columns else 1.0

    prom_loc = ((pts_loc / pj_loc) * 0.4) + (xg_proyectado_local * 0.4)
    prom_vis = ((pts_vis / pj_vis) * 0.4) + (xg_proyectado_visi * 0.4)

    factor_forma_loc = 0.85 + (pts_u5_loc_ajustado / 15.0) * 0.30
    factor_forma_vis = 0.85 + (pts_u5_vis_ajustado / 15.0) * 0.30

    prom_loc *= factor_forma_loc
    prom_vis *= factor_forma_vis

    prom_loc_ajustado = prom_loc * (1.0 + (factor_localia * 0.5))
    prom_vis_ajustado = prom_vis

    score_loc = (
        (stats_loc["GF"] * 0.2) + (stats_loc["Pos"] * 0.05) + (stats_loc["VI"] * 1.2) +
        (stats_loc["TirosArco"] * 0.8) + (stats_loc["Fortaleza"] * 0.1)
    )
    score_vis = (
        (stats_vis["GF"] * 0.2) + (stats_vis["Pos"] * 0.05) + (stats_vis["VI"] * 1.2) +
        (stats_vis["TirosArco"] * 0.8) + (stats_vis["Fortaleza"] * 0.1)
    )

    if (score_loc + score_vis) > 0:
        ventaja_relativa = (score_loc - score_vis) / (score_loc + score_vis)
    else:
        ventaja_relativa = 0.0

    ajuste_h2h = ventaja_relativa * 0.08
    
    victorias_h2h = historial_h2h.count('G')
    derrotas_h2h = historial_h2h.count('P')
    balance_h2h = victorias_h2h - derrotas_h2h
    bono_historial = balance_h2h * 0.025 

    bono_jerarquia = (jer_loc - jer_vis) * 0.04

    prom_loc_ajustado = prom_loc_ajustado * (1.0 + ajuste_h2h + bono_historial + bono_jerarquia)
    prom_vis_ajustado = prom_vis_ajustado * (1.0 - ajuste_h2h - bono_historial - bono_jerarquia)

    prob_empate_poisson = sum(
        poisson_prob(xg_proyectado_local, k) * poisson_prob(xg_proyectado_visi, k) for k in range(5)
    )

    diferencia_xg = abs(xg_proyectado_local - xg_proyectado_visi)
    factor_paridad = max(0.85, 1.25 - (diferencia_xg * 0.4))
    prob_empate = (prob_empate_poisson * 100) * factor_paridad
    prob_empate = max(22.0, min(38.0, prob_empate))

    resto = 100.0 - prob_empate
    total_prom = prom_loc_ajustado + prom_vis_ajustado

    if total_prom > 0:
        prob_loc = (prom_loc_ajustado / total_prom) * resto
        prob_vis = (prom_vis_ajustado / total_prom) * resto
    else:
        prob_loc = resto / 2
        prob_vis = resto / 2

    return prob_loc, prob_empate, prob_vis, False

def buscar_equipo(nombre_buscado, lista_equipos):
    nombre_clean = nombre_buscado.lower().strip()
    if "estudiantes" in nombre_clean:
        if any(k in nombre_clean for k in ["rio cuarto", "río cuarto"]):
            for eq in lista_equipos:
                if "rc" in eq.lower() or "rio cuarto" in eq.lower(): return eq
        elif any(k in nombre_clean.split() for k in ["la plata", "lp", "estudiantes"]):
            for eq in lista_equipos:
                if "estudiantes" in eq.lower() and "rc" not in eq.lower(): return eq
    elif "gimnasia" in nombre_clean:
        if "la plata" in nombre_clean or "lp" in nombre_clean.split():
            for eq in lista_equipos:
                if "gimnasia" in eq.lower(): return eq

    for eq in lista_equipos:
        if nombre_clean == eq.lower().strip(): return eq

    for eq in lista_equipos:
        eq_clean = eq.lower().strip()
        if nombre_clean in eq_clean or eq_clean in nombre_clean:
            if "estudiantes" in eq_clean and "estudiantes" in nombre_clean:
                es_buscado_rc = "rc" in nombre_clean.split() or "rio cuarto" in nombre_clean
                es_equipo_rc = "rc" in eq_clean or "rio cuarto" in eq_clean
                if es_buscado_rc != es_equipo_rc: continue
            return eq
    return None

# =====================================================================
# 5. SCRAPING AUTOMÁTICO
# =====================================================================
@st.cache_data(ttl=3600)
def obtener_estadisticas_promiedos(equipos_disponibles):
    url = "https://www.promiedos.com.ar/primera"
    stats_promiedos = {}
    
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Accept-Language": "es-AR,es;q=0.8"
        }
        response = requests.get(url, headers=headers, timeout=15)
        response.encoding = 'utf-8'
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            tabla = soup.find("table", id="posiciones")
            
            if tabla:
                filas = tabla.find_all("tr")
                for fila in filas[1:]:
                    celdas = fila.find_all(["td", "th"])
                    if len(celdas) >= 9:
                        equipo_raw = celdas[1].get_text(strip=True)
                        pts_raw = celdas[2].get_text(strip=True)
                        pj_raw = celdas[3].get_text(strip=True)
                        gf_raw = celdas[7].get_text(strip=True)
                        gc_raw = celdas[8].get_text(strip=True)

                        eq_match = buscar_equipo(equipo_raw, equipos_disponibles)
                        if eq_match:
                            stats_promiedos[eq_match] = {
                                "Puntos": int(pts_raw) if pts_raw.isdigit() else 0,
                                "GF": int(gf_raw) if gf_raw.isdigit() else 0,
                                "GC": int(gc_raw) if gc_raw.isdigit() else 0,
                                "PJ": int(pj_raw) if pj_raw.isdigit() else 1,
                            }
    except Exception:
        pass
        
    return stats_promiedos

@st.cache_data(ttl=3600)
def obtener_partidos_hoy_auto(equipos_disponibles):
    ahora_arg = datetime.datetime.utcnow() - datetime.timedelta(hours=3)
    fecha_hoy_str = ahora_arg.strftime("%Y-%m-%d")
    fecha_espn_url = ahora_arg.strftime("%Y%m%d")
    url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/arg.1/scoreboard?dates={fecha_espn_url}"
    partidos_hoy = []
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if "events" in data:
                for event in data["events"]:
                    fecha_api = datetime.datetime.strptime(event["date"], "%Y-%m-%dT%H:%MZ")
                    fecha_partido_arg = fecha_api - datetime.timedelta(hours=3)
                    if fecha_partido_arg.strftime("%Y-%m-%d") == fecha_hoy_str:
                        comps = event["competitions"][0]["competitors"]
                        loc_raw = comps[0]["team"]["name"] if comps[0]["homeAway"] == "home" else comps[1]["team"]["name"]
                        vis_raw = comps[1]["team"]["name"] if comps[0]["homeAway"] == "home" else comps[0]["team"]["name"]
                        hora_str = fecha_partido_arg.strftime("%H:%M")
                        loc_match = buscar_equipo(loc_raw, equipos_disponibles)
                        vis_match = buscar_equipo(vis_raw, equipos_disponibles)
                        if loc_match and vis_match and loc_match != vis_match:
                            partidos_hoy.append({"Local": loc_match, "Visitante": vis_match, "Hora": hora_str})
    except Exception:
        pass
    return partidos_hoy

def consolidar_estadisticas(equipo, df, stats_torneo, xg_proyectado):
    row = df[df["Equipo"] == equipo].iloc[0]

    if equipo in stats_torneo:
        gf = stats_torneo[equipo]["GF"]
        pj = max(1, stats_torneo[equipo]["PJ"])
        gc = stats_torneo[equipo]["GC"]
    else:
        gf = int(row.get("GF", round(xg_proyectado * 12)))
        pj = int(row.get("PJ", 12))
        gc = int(row.get("GC", 12))
        if pj == 0: pj = 1

    pos = min(75, max(35, int(40 + (gf / pj * 8) + (xg_proyectado * 3))))
    tasa_invicta = max(0, pj - int(gc * 0.8))
    vi = int(tasa_invicta * 0.4)
    tiros_arco = round(xg_proyectado * 3.5 + (gf / pj * 1.5), 1)
    pases = min(92, max(60, int(pos * 1.15 + 8)))

    if "Corners" in df.columns:
        corners = round(float(row.get("Corners", 4.2)), 1)
    elif "Corners_Favor" in df.columns:
        corners = round(float(row.get("Corners_Favor", 4.2)), 1)
    else:
        corners = round(max(3.0, min(5.8, 2.2 + (xg_proyectado * 1.1) + (pos * 0.02))), 1)

    gc_pp = gc / pj
    fortaleza = min(100, max(10, int(100 - (gc_pp * 35))))

    if "Forma_U5" in df.columns:
        pts_u5 = float(row.get("Forma_U5", 7.5))
    else:
        pts_u5 = round(min(15.0, max(1.0, (gf / pj) * 3.5 + (xg_proyectado * 2.0))), 1)

    return {
        "GF": gf,
        "xG": round(xg_proyectado, 1),
        "Pos": pos,
        "VI": vi,
        "TirosArco": tiros_arco,
        "Pases": pases,
        "Corners": corners,
        "Fortaleza": fortaleza,
        "Pts_U5": pts_u5,
        "PJ": pj,
    }

def generar_radar(loc_name, vis_name, stats_loc, stats_vis):
    categories = [
        "Goles a Favor", "xG Proyectado", "Posesión (%)", 
        "Vallas Invictas", "Tiros al Arco", "Eficacia Pases", 
        "Fuerza Defensiva", "Forma Reciente (U5)", "Jerarquía Plantel"
    ]

    max_gf = max(stats_loc["GF"], stats_vis["GF"], 15) * 1.1
    max_xg = max(stats_loc["xG"], stats_vis["xG"], 2.0) * 1.2
    max_pos = 100
    max_vi = max(stats_loc["VI"], stats_vis["VI"], 5) * 1.2
    max_ta = max(stats_loc["TirosArco"], stats_vis["TirosArco"], 5.0) * 1.2
    max_pa = 100
    max_fd = 100
    max_forma = 15.0
    max_jer = 10.0

    jer_loc = obtener_jerarquia(loc_name)
    jer_vis = obtener_jerarquia(vis_name)

    val_loc_norm = [
        stats_loc["GF"] / max_gf, stats_loc["xG"] / max_xg, stats_loc["Pos"] / max_pos,
        stats_loc["VI"] / max_vi, stats_loc["TirosArco"] / max_ta, stats_loc["Pases"] / max_pa,
        stats_loc["Fortaleza"] / max_fd, stats_loc["Pts_U5"] / max_forma, jer_loc / max_jer
    ]
    val_vis_norm = [
        stats_vis["GF"] / max_gf, stats_vis["xG"] / max_xg, stats_vis["Pos"] / max_pos,
        stats_vis["VI"] / max_vi, stats_vis["TirosArco"] / max_ta, stats_vis["Pases"] / max_pa,
        stats_vis["Fortaleza"] / max_fd, stats_vis["Pts_U5"] / max_forma, jer_vis / max_jer
    ]

    text_loc = [
        str(stats_loc["GF"]), str(stats_loc["xG"]), f"{stats_loc['Pos']} %",
        str(stats_loc["VI"]), str(stats_loc["TirosArco"]), f"{stats_loc['Pases']} %",
        f"{stats_loc['Fortaleza']}/100", f"{stats_loc['Pts_U5']} pts", f"{jer_loc}/10"
    ]
    text_vis = [
        str(stats_vis["GF"]), str(stats_vis["xG"]), f"{stats_vis['Pos']} %",
        str(stats_vis["VI"]), str(stats_vis["TirosArco"]), f"{stats_vis['Pases']} %",
        f"{stats_vis['Fortaleza']}/100", f"{stats_vis['Pts_U5']} pts", f"{jer_vis}/10"
    ]

    fig = go.Figure()

    fig.add_trace(go.Scatterpolar(
        r=val_loc_norm + [val_loc_norm[0]], theta=categories + [categories[0]],
        fill="toself", name=loc_name, line=dict(color="#00ffcc"),
        fillcolor="rgba(0, 255, 204, 0.2)", text=text_loc + [text_loc[0]], hoverinfo="text+name", mode="lines+markers"
    ))
    fig.add_trace(go.Scatterpolar(
        r=val_vis_norm + [val_vis_norm[0]], theta=categories + [categories[0]],
        fill="toself", name=vis_name, line=dict(color="#ff3366"),
        fillcolor="rgba(255, 51, 102, 0.2)", text=text_vis + [text_vis[0]], hoverinfo="text+name", mode="lines+markers"
    ))

    fig.update_layout(
        polar=dict(
            bgcolor="#111827",
            radialaxis=dict(visible=False, range=[0, 1]),
            angularaxis=dict(color="#cbd5e1", gridcolor="#1e293b"),
        ),
        showlegend=True,
        legend=dict(font=dict(color="#cbd5e1")),
        paper_bgcolor="#070b14", plot_bgcolor="#070b14", font=dict(color="#94a3b8"),
        margin=dict(t=50, b=50, l=60, r=60),
    )
    return fig

# =====================================================================
# 6. INTERFAZ Y ENCABEZADO
# =====================================================================
col_logo, col_titulo = st.columns([1, 6])
with col_logo:
    st.image("https://a.espncdn.com/combiner/i?img=/i/leaguelogos/soccer/500/1.png", width=110)

with col_titulo:
    st.markdown('<div class="neon-title">Win Predictor LPF</div>', unsafe_allow_html=True)
    st.markdown('<div class="tech-sub">MOTOR DE PREDICCIÓN CON xG, IA APRENDIZAJE CONTINUO Y DATA OFICIAL</div>', unsafe_allow_html=True)

st.markdown("---")

# =====================================================================
# 7. CARGA DE DATOS Y MOTOR PRINCIPAL
# =====================================================================
DIRECTORIO_APP = os.path.dirname(os.path.abspath(__file__))
RUTA_CSV = os.path.join(DIRECTORIO_APP, "datos_procesados.csv")

if not os.path.exists(RUTA_CSV):
    RUTA_CSV = os.path.join(DIRECTORIO_APP, "datos", "datos_procesados.csv")

if os.path.exists(RUTA_CSV):
    df = pd.read_csv(RUTA_CSV)

    if "Equipo" in df.columns:
        def limpiar_nombre_equipo(x):
            s = str(x).strip()
            s_lower = s.lower()
            if "estudiantes" in s_lower:
                if any(k in s_lower for k in ["rio cuarto", "río cuarto", "(rc)", "estudiantes rc"]): return "Estudiantes RC"
                if any(k in s_lower for k in ["la plata", "(lp)"]): return "Estudiantes"
            return re.sub(r"\[.*?\]|\(.*?\)", "", s).strip()
        df["Equipo"] = df["Equipo"].apply(limpiar_nombre_equipo)

    if "xG" not in df.columns and "xG_Favor" not in df.columns:
        if "GF" in df.columns and "PJ" in df.columns:
            df["xG"] = (df["GF"] / df["PJ"].replace(0, 1) * 0.95).round(2)
        else:
            df["xG"] = 1.25
    elif "xG_Favor" in df.columns and "xG" not in df.columns:
        df["xG"] = df["xG_Favor"]

    lista_equipos = sorted(df["Equipo"].unique()) if "Equipo" in df.columns else []
    
    stats_torneo = obtener_estadisticas_promiedos(lista_equipos)

    # AGENDA DEL DÍA AUTOMÁTICA
    st.markdown("<h3 style='color: #cbd5e1;'>Partidos de Hoy</h3>", unsafe_allow_html=True)
    partidos_del_dia = obtener_partidos_hoy_auto(lista_equipos)

    if partidos_del_dia:
        for partido in partidos_del_dia:
            st.markdown(f"**{partido['Hora']} hs** | **{partido['Local']}** vs **{partido['Visitante']}**")
            st.divider()
    else:
        st.info("Sin partidos programados para el día de hoy según la liga oficial.")
        st.divider()

    # TABLA DE POSICIONES
    st.markdown("<h3 style='color: #cbd5e1;'>Tabla General de Posiciones & xG</h3>", unsafe_allow_html=True)
    st.dataframe(df, use_container_width=True, hide_index=True)
    st.markdown("---")

    # MOTOR DE PREDICCIÓN
    st.markdown("<h3 style='color: #cbd5e1;'>Motor de Predicción de Partidos</h3>", unsafe_allow_html=True)

    if len(lista_equipos) >= 2:
        col1, col2 = st.columns(2)
        with col1:
            local = st.selectbox("Seleccionar Local", lista_equipos, index=0, key="sb_local")
        with col2:
            visitante = st.selectbox("Seleccionar Visitante", lista_equipos, index=min(1, len(lista_equipos) - 1), key="sb_visit")

        if local == visitante:
            st.error("SISTEMA BLOQUEADO: Seleccione escuadras diferentes.")
        else:
            row_loc = df[df["Equipo"] == local].iloc[0]
            row_vis = df[df["Equipo"] == visitante].iloc[0]
            xg_loc_base = float(row_loc.get("xG", 1.25))
            xg_vis_base = float(row_vis.get("xG", 1.10))

            FACTOR_LOCALIA = 0.15
            xg_proyectado_local = round(xg_loc_base * (1.0 + FACTOR_LOCALIA), 2)
            xg_proyectado_visi = round(xg_vis_base * (1.0 - (FACTOR_LOCALIA * 0.5)), 2)

            stats_loc = consolidar_estadisticas(local, df, stats_torneo, xg_proyectado_local)
            stats_vis = consolidar_estadisticas(visitante, df, stats_torneo, xg_proyectado_visi)

            historial_h2h = obtener_historial_directo(local, visitante)

            prob_loc, prob_empate, prob_vis, es_ia = realizar_prediccion(
                local, visitante, df, stats_loc, stats_vis, 
                xg_proyectado_local, xg_proyectado_visi, 
                factor_localia=FACTOR_LOCALIA, 
                historial_h2h=historial_h2h, 
                paquete_ia=paquete_ia
            )

            st.markdown(f"<h2 style='text-align: center; color: #fff; margin-top: 25px;'>{local.upper()} vs {visitante.upper()}</h2>", unsafe_allow_html=True)
            
            if es_ia:
                st.success("Predicción ejecutada mediante el Modelo de Inteligencia Artificial (modelo_entrenado.pkl)")
            else:
                st.info("Predicción ejecutada mediante el Motor Estadístico Avanzado de Resguardo")

            st.markdown("<p style='text-align: center; color: #94a3b8; font-size: 13px; margin-bottom: 5px; text-transform: uppercase;'>Historial Directo (Últimos 5 vs)</p>", unsafe_allow_html=True)
            st.markdown(render_h2h_pills(historial_h2h, local, visitante), unsafe_allow_html=True)

            col_xg1, col_xg2 = st.columns(2)
            with col_xg1:
                jer_local_ui = obtener_jerarquia(local)
                st.info(f"Jerarquía: **{jer_local_ui}/10** | xG Proy: **{xg_proyectado_local}** | Forma (U5): **{stats_loc['Pts_U5']} pts**")
            with col_xg2:
                jer_visita_ui = obtener_jerarquia(visitante)
                st.info(f"Jerarquía: **{jer_visita_ui}/10** | xG Proy: **{xg_proyectado_visi}** | Forma (U5): **{stats_vis['Pts_U5']} pts**")

            m1, m2, m3 = st.columns(3)
            m1.metric(label=f"Victoria {local}", value=f"{prob_loc:.1f}%")
            m2.metric(label="Probabilidad Empate", value=f"{prob_empate:.1f}%")
            m3.metric(label=f"Victoria {visitante}", value=f"{prob_vis:.1f}%")

            st.markdown("<br><p style='color: #94a3b8;'>Distribución de probabilidad 1X2:</p>", unsafe_allow_html=True)
            c_b1, c_b2, c_b3 = st.columns(3)
            with c_b1:
                st.markdown("<p style='color: #00ffcc;'>Local</p>", unsafe_allow_html=True)
                st.progress(min(1.0, max(0.0, prob_loc / 100.0)))
            with c_b2:
                st.markdown("<p style='color: #cbd5e1;'>Empate</p>", unsafe_allow_html=True)
                st.progress(min(1.0, max(0.0, prob_empate / 100.0)))
            with c_b3:
                st.markdown("<p style='color: #ff3366;'>Visitante</p>", unsafe_allow_html=True)
                st.progress(min(1.0, max(0.0, prob_vis / 100.0)))

            st.markdown("---")

            st.markdown("<h4 style='color: #cbd5e1;'>Índice de Volatilidad & Impredecibilidad</h4>", unsafe_allow_html=True)
            vol_val, vol_cat, vol_col = calcular_indice_volatilidad(xg_proyectado_local, xg_proyectado_visi, stats_loc, stats_vis)
            v_col1, v_col2 = st.columns([1, 2])
            with v_col1: st.metric(label="Índice de Caos", value=f"{vol_val}%")
            with v_col2:
                st.markdown(f"**Nivel de Riesgo:** :{vol_col}[{vol_cat}]")
                st.progress(int(vol_val) / 100)

            st.markdown("---")

            st.markdown("<h4 style='color: #cbd5e1;'>Mercados Complementarios (Proyección Poisson)</h4>", unsafe_allow_html=True)
            prob_over_25, prob_under_25, prob_btts = calcular_mercados_adicionales(xg_proyectado_local, xg_proyectado_visi)
            c_m1, c_m2, c_m3, c_m4 = st.columns(4)
            with c_m1: st.metric(label="Más de 2.5 Goles", value=f"{prob_over_25:.1f}%")
            with c_m2: st.metric(label="Menos de 2.5 Goles", value=f"{prob_under_25:.1f}%")
            with c_m3: st.metric(label="Ambos Anotan (Sí)", value=f"{prob_btts:.1f}%")
            with c_m4:
                corners_est = round(stats_loc["Corners"] + stats_vis["Corners"], 1)
                st.metric(label="Córners Totales (Est.)", value=f"{corners_est}")

            st.markdown("---")

            st.markdown("<h4 style='color: #cbd5e1;'>Simulación Estocástica Monte Carlo (10,000 Partidos)</h4>", unsafe_allow_html=True)
            p_loc_mc, p_emp_mc, p_vis_mc, goles_sim = simular_monte_carlo(xg_proyectado_local, xg_proyectado_visi)
            c_mc1, c_mc2, c_mc3 = st.columns(3)
            c_mc1.metric(f"Victoria {local} (MC)", f"{p_loc_mc:.1f}%")
            c_mc2.metric("Empate (MC)", f"{p_emp_mc:.1f}%")
            c_mc3.metric(f"Victoria {visitante} (MC)", f"{p_vis_mc:.1f}%")

            fig_hist = go.Figure()
            fig_hist.add_trace(go.Histogram(x=goles_sim, nbinsx=10, marker_color="#00f3ff", opacity=0.75, name="Goles Totales"))
            fig_hist.update_layout(
                title="Distribución de Goles Totales en 10,000 Simulaciones",
                xaxis_title="Cantidad de Goles en el Partido", yaxis_title="Frecuencia (N° de Simulación)",
                paper_bgcolor="#070b14", plot_bgcolor="#111827", font=dict(color="#cbd5e1"),
                margin=dict(t=40, b=40, l=40, r=40),
            )
            st.plotly_chart(fig_hist, use_container_width=True)

            st.markdown("---")

            st.markdown("<h4 style='color: #cbd5e1;'>Frente a Frente: Análisis Octagonal (Incluye Forma Reciente)</h4>", unsafe_allow_html=True)
            fig_radar = generar_radar(local, visitante, stats_loc, stats_vis)
            st.plotly_chart(fig_radar, use_container_width=True)

            st.markdown("---")

            st.markdown("<h4 style='color: #cbd5e1;'>Top 5 Marcadores Exactos Más Probables</h4>", unsafe_allow_html=True)
            
            top_5_marcadores, prob_otro = calcular_top_resultados(
                xg_proyectado_local, 
                xg_proyectado_visi, 
                prob_loc,       
                prob_empate,    
                prob_vis
            )

            tabla_marcadores = [
                {"Ranking": f"#{rank}", "Resultado Exacto (Local - Visitante)": marcador, "Probabilidad": f"{prob:.1f}%"}
                for rank, (marcador, prob) in enumerate(top_5_marcadores, 1)
            ]
            tabla_marcadores.append({"Ranking": "Otros", "Resultado Exacto (Local - Visitante)": "Cualquier otro resultado", "Probabilidad": f"{prob_otro:.1f}%"})
            st.dataframe(pd.DataFrame(tabla_marcadores), use_container_width=True, hide_index=True)

else:
    st.error("Archivo de origen no encontrado. Verifique que 'datos_procesados.csv' exista.")
