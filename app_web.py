import datetime
import hashlib
import math
import os
import re
import joblib
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import requests
import streamlit as st
import streamlit.components.v1 as components  # <-- AGREGÁ ESTA LÍNEA AQUÍ
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
# FUNCION PARA MOSTRAR ANUNCIO DE ADSENSE
# =====================================================================
def mostrar_anuncio_adsense():
  codigo_adsense = """
    <div style="text-align: center; margin: 10px 0;">
        <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-6333118178688004"
             crossorigin="anonymous"></script>
        <ins class="adsbygoogle"
             style="display:block"
             data-ad-client="ca-pub-6333118178688004"
             data-ad-slot="2020973308"
             data-ad-format="auto"
             data-full-width-responsive="true"></ins>
        <script>
             (adsbygoogle = window.adsbygoogle || []).push({});
        </script>
    </div>
    """
  components.html(codigo_adsense, height=130)
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

import datetime
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# =====================================================================
# PERSISTENCIA ETERNA CON GOOGLE SHEETS
# =====================================================================
def obtener_conexion_gsheets():
    """Autentica contra la API de Google Sheets leyendo st.secrets."""
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds_dict = dict(st.secrets["gcp_service_account"])
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        
        sheet_url = st.secrets.get("spreadsheet_url", "")
        if sheet_url and "PEGAR_AQUI" not in sheet_url:
            return client.open_by_url(sheet_url).sheet1
        else:
            return client.open("WinPredictor_Historial").sheet1
    except Exception as e:
        st.error(f"Error de conexión con Google Sheets: {e}")
        return None

def cargar_historial_permanente():
    """Lee el historial directamente desde la planilla de Google Sheets."""
    sheet = obtener_conexion_gsheets()
    if not sheet:
        return []
    try:
        records = sheet.get_all_records()
        # Mapeamos para mantener compatibilidad de datos
        historial = []
        for r in records:
            historial.append({
                "id": str(r.get("id", "")),
                "partido": str(r.get("partido", "")),
                "prediccion": str(r.get("prediccion", "")),
                "acerto": str(r.get("acerto", "")).upper() in ["TRUE", "1", "VERDADERO"],
                "fecha": str(r.get("fecha", ""))
            })
        return historial
    except Exception:
        return []

def guardar_resultado_partido(partido, prediccion, acerto, fecha_str=None):
    """Guarda una nueva fila en Google Sheets evitando duplicados."""
    sheet = obtener_conexion_gsheets()
    if not sheet:
        return

    fecha = fecha_str or datetime.datetime.now().strftime("%Y-%m-%d")
    id_unico = f"{partido}_{fecha}"

    # Cargar actual para verificar duplicados
    historial_actual = cargar_historial_permanente()
    if any(h.get("id") == id_unico for h in historial_actual):
        return

    nueva_fila = [id_unico, partido, prediccion, "TRUE" if acerto else "FALSE", fecha]
    sheet.append_row(nueva_fila)
# =====================================================================
# GRÁFICO FACHERO NEÓN CON ZOOM ADAPTATIVO ("ZOOM OUT" AUTOMÁTICO)
# =====================================================================
def renderizar_medidor_efectividad_definitivo():
    """Muestra KPIs estilo Neón y el gráfico que va disminuyendo el zoom con N partidos."""
    historial = cargar_historial_permanente()

    if not historial:
        st.info("⚡ Todavía no hay historial de partidos finalizados guardado en el archivo permanente.")
        return

    # Creamos un DataFrame con los datos guardados en el JSON
    df = pd.DataFrame(historial)
    df["partido_num"] = range(1, len(df) + 1)
    df["acierto_int"] = df["acerto"].astype(int)
    df["aciertos_acumulados"] = df["acierto_int"].cumsum()
    df["efectividad_pct"] = (df["aciertos_acumulados"] / df["partido_num"]) * 100

    total_partidos = len(df)
    total_aciertos = int(df["aciertos_acumulados"].iloc[-1])
    efectividad_actual = df["efectividad_pct"].iloc[-1]

    # Calcular racha actual en verde
    racha = 0
    for ac in reversed(df["acerto"].tolist()):
        if ac: racha += 1
        else: break

    # 1. MÉTRICAS KPI (Tarjetas Neón)
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Analizados", f"{total_partidos} Partidos")
    with col2:
        st.metric("Aciertos Totales", f"{total_aciertos} ✅")
    with col3:
        st.metric("Efectividad Global", f"{efectividad_actual:.1f}%")
    with col4:
        st.metric("Racha Actual", f"{racha} seguidos 🔥" if racha > 0 else "0 ❄️")

    # 2. GRÁFICO PLOTLY CON ZOOM ADAPTATIVO
    fig = go.Figure()

    # Línea de referencia 50%
    fig.add_trace(go.Scatter(
        x=[1, max(total_partidos, 10)],
        y=[50, 50],
        mode="lines",
        name="Línea 50%",
        line=dict(color="#475569", width=1.5, dash="dash"),
        hoverinfo="skip"
    ))

    # Colores por punto (Verde si acertó, Rojo si falló)
    colores_puntos = ["#00ffcc" if a else "#ff3366" for a in df["acerto"]]

    # Curva principal
    fig.add_trace(go.Scatter(
        x=df["partido_num"],
        y=df["efectividad_pct"],
        mode="lines+markers",
        name="Efectividad",
        line=dict(color="#00ffcc", width=3, shape="spline"),
        marker=dict(
            size=8,
            color=colores_puntos,
            line=dict(width=1.5, color="#070b14")
        ),
        fill="tozeroy",
        fillcolor="rgba(0, 255, 204, 0.08)",
        hovertemplate="<b>Partido #%{x}</b><br>Efectividad: <b>%{y:.1f}%</b><br>%{text}<extra></extra>",
        text=[f"{p}<br>Resultado: {'✅ Acierto' if a else '❌ Fallo'}" for p, a in zip(df["partido"], df["acerto"])]
    ))

    # Configuración de Layout y Zoom Automático
    fig.update_layout(
        title=dict(
            text="📈 Evolución Histórica del Win Predictor",
            font=dict(color="#00ffcc", size=18)
        ),
        paper_bgcolor="#070b14",
        plot_bgcolor="#0c1322",
        margin=dict(l=15, r=15, t=50, b=20),
        height=380,
        showlegend=False,
        xaxis=dict(
            title="Cantidad de Partidos Analizados (N)",
            titlefont=dict(color="#94a3b8", size=12),
            tickfont=dict(color="#cbd5e1"),
            gridcolor="rgba(255, 255, 255, 0.05)",
            # EL ZOOM DISMINUYE AUTOMÁTICAMENTE (ZOOM OUT) A MEDIDA QUE CRECE N:
            autorange=True,
            zeroline=False
        ),
        yaxis=dict(
            title="Efectividad (%)",
            titlefont=dict(color="#94a3b8", size=12),
            tickfont=dict(color="#cbd5e1"),
            gridcolor="rgba(255, 255, 255, 0.05)",
            range=[0, 105],
            ticksuffix="%"
        )
    )

    st.plotly_chart(fig, use_container_width=True)
    
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

                    # Insertar Posición en la columna 0 (a la izquierda de Escudo)
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

# =====================================================================
# HISTORIAL DIRECTO (H2H) REAL - VÍA SOFASCORE API (NO ESPN)
# =====================================================================
@st.cache_data(ttl=86400)
def obtener_historial_directo(local, visitante, *args, **kwargs):
    """
    Obtiene el historial H2H real buscando en la API pública de SofaScore.
    No requiere API Key y es 100% independiente de ESPN.
    """
    # Encabezados para que SofaScore no bloquee la petición
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Origin": "https://www.sofascore.com",
        "Referer": "https://www.sofascore.com/"
    }

    def buscar_id_sofascore(nombre_equipo):
        try:
            # Limpiamos el nombre para que el buscador lo encuentre fácil
            busqueda = str(nombre_equipo).lower().replace("club", "").replace("atlético", "atletico").replace("ca ", "").strip()
            url_search = f"https://api.sofascore.com/api/v1/search/teams?q={busqueda}"
            r = requests.get(url_search, headers=headers, timeout=5)
            if r.status_code == 200:
                equipos = r.json().get("teams", [])
                for eq in equipos:
                    # Filtramos que sea equipo de fútbol y de Argentina si es posible
                    if eq.get("sport", {}).get("name") == "Football":
                        return str(eq.get("id"))
        except Exception:
            pass
        return None

    # 1. Obtener los IDs de ambos equipos en la base de datos de SofaScore
    id_loc = buscar_id_sofascore(local)
    id_vis = buscar_id_sofascore(visitante)

    if not id_loc or not id_vis:
        return []

    historial = []
    
    # 2. Buscar en los últimos ~100 partidos (páginas 0, 1 y 2) del equipo local
    try:
        for pagina in range(3):
            if len(historial) >= 5:
                break
                
            url_partidos = f"https://api.sofascore.com/api/v1/team/{id_loc}/events/last/{pagina}"
            r = requests.get(url_partidos, headers=headers, timeout=5)
            
            if r.status_code == 200:
                eventos = r.json().get("events", [])
                for ev in eventos:
                    # Solo evaluamos partidos terminados
                    if ev.get("status", {}).get("type") != "finished":
                        continue
                        
                    eq_casa = str(ev.get("homeTeam", {}).get("id", ""))
                    eq_fuera = str(ev.get("awayTeam", {}).get("id", ""))
                    
                    # Verificamos si es un partido entre nuestro Local y nuestro Visitante
                    if (eq_casa == id_loc and eq_fuera == id_vis) or (eq_casa == id_vis and eq_fuera == id_loc):
                        goles_casa = int(ev.get("homeScore", {}).get("current", 0))
                        goles_fuera = int(ev.get("awayScore", {}).get("current", 0))
                        
                        soy_local_en_este_partido = (eq_casa == id_loc)
                        
                        # Determinar G, E, P desde la perspectiva del equipo LOCAL de la app
                        if goles_casa == goles_fuera:
                            historial.append("E")
                        elif (goles_casa > goles_fuera and soy_local_en_este_partido) or (goles_casa < goles_fuera and not soy_local_en_este_partido):
                            historial.append("G")
                        else:
                            historial.append("P")
                            
                        if len(historial) >= 5:
                            break
    except Exception:
        pass

    return historial[:5]

def render_h2h_pills(historial, local, visitante):
    if not historial:
        return "<div style='text-align: center; font-size: 13px; color: #94a3b8; margin-bottom: 20px;'>No hay historial directo reciente registrado entre ambos.</div>"
        
    html = "<div style='text-align: center; font-size: 12px; color: #94a3b8; margin-bottom: 10px;'>"
    html += f"<span style='color: #00ffcc; font-weight: bold;'>G</span> = Ganó {local} &nbsp;&nbsp;|&nbsp;&nbsp; "
    html += "<span style='color: #cbd5e1; font-weight: bold;'>E</span> = Empate &nbsp;&nbsp;|&nbsp;&nbsp; "
    html += f"<span style='color: #ff3366; font-weight: bold;'>P</span> = Ganó {visitante}</div>"
    html += "<div style='display: flex; gap: 8px; justify-content: center; margin-bottom: 20px;'>"

    for res in historial:
        color = "#00ffcc" if res == 'G' else "#cbd5e1" if res == 'E' else "#ff3366"
        bg = "rgba(0, 255, 204, 0.2)" if res == 'G' else "rgba(203, 213, 225, 0.2)" if res == 'E' else "rgba(255, 51, 102, 0.2)"
        tooltip = f"Ganó {local}" if res == 'G' else "Empate" if res == 'E' else f"Ganó {visitante}"
        html += f"<div title='{tooltip}' style='background-color: {bg}; color: {color}; width: 32px; height: 32px; border: 2px solid {color}; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: 900; font-size: 14px; box-shadow: 0 0 5px {color}80; cursor: help;'>{res}</div>"

    html += "</div>"
    return html



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
        "GF": int(prom_gf * 10), "xG": round(xg_proyectado, 1), "Pos": pos, "VI": vi,
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
        showlegend=True, paper_bgcolor="#070b14", plot_bgcolor="#070b14", font=dict(color="#94a3b8"), margin=dict(t=30, b=30, l=30, r=30)
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
        "Prediccion_1X2", "Marcador_Predicho", "Prob_Over25", "Prob_BTTS", "Corners_Est", 
        "Goles_Local_Real", "Goles_Visita_Real", "Corners_Reales", "Estado"
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

                                    c_totales = 9
                                    try:
                                        r_sum = requests.get(f"https://site.api.espn.com/apis/site/v2/sports/soccer/arg.1/summary?event={ev['id']}", timeout=5)
                                        if r_sum.status_code == 200:
                                            cc = sum(int(st_item.get("displayValue", 0)) for t in r_sum.json().get("boxscore", {}).get("teams", []) for st_item in t.get("statistics", []) if "corner" in st_item.get("name", "").lower())
                                            if cc > 0: c_totales = cc
                                    except Exception: pass

                                    df_hist.at[idx, "Corners_Reales"] = c_totales
                                    df_hist.at[idx, "Estado"] = "Finalizado"
                                    hubo_cambios = True
                except Exception: pass

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
                "ID": pid, "Fecha": fecha_hoy, "Local": loc, "Visitante": vis,
                "Prob_Loc": round(pl, 1), "Prob_Emp": round(pe, 1), "Prob_Vis": round(pv, 1),
                "Prediccion_1X2": p1x2, "Marcador_Predicho": marcador_top,
                "Prob_Over25": round(po25, 1), "Prob_BTTS": round(pbtts, 1),
                "Corners_Est": round(corn_est, 1),
                "Goles_Local_Real": np.nan, "Goles_Visita_Real": np.nan, "Corners_Reales": np.nan,
                "Estado": "Pendiente"
            }])
            df_hist = pd.concat([df_hist, n_fila], ignore_index=True)
            existentes.add((fecha_hoy, str(loc), str(vis)))
            nuevos += 1
            hubo_cambios = True

    if hubo_cambios:
        df_hist = df_hist.drop_duplicates(subset=['Fecha', 'Local', 'Visitante'], keep='first')
        df_hist = depurar_partidos_cercanos(df_hist)
        df_hist.to_csv(RUTA_HISTORIAL, index=False)

    return hubo_cambios, nuevos

# =====================================================================
# 8. ENCABEZADO Y BARRA SUPERIOR DE NAVEGACION PARA CELULAR
# =====================================================================
# =====================================================================
# 8. ENCABEZADO Y BARRA SUPERIOR DE NAVEGACION PARA CELULAR
# =====================================================================
col_logo, col_titulo = st.columns([1, 6])
with col_logo:
  st.image(
      "https://a.espncdn.com/combiner/i?img=/i/leaguelogos/soccer/500/1.png",
      width=80,
  )
with col_titulo:
  st.markdown(
      '<div class="neon-title">Win Predictor LPF</div>', unsafe_allow_html=True
  )
  st.markdown(
      '<div class="tech-sub">PLATAFORMA DE INTELIGENCIA PREDICTIVA & ANÁLISIS'
      " ESTOCÁSTICO</div>",
      unsafe_allow_html=True,
  )

# 📢 AQUÍ SE MUESTRA TU ANUNCIO DE ADSENSE (Debajo del título y arriba del menú)
mostrar_anuncio_adsense()

opcion_pantalla = st.radio(
    "Menú de Navegación:",
    ["Predicciones y Métricas", "Cuotas Justas y Opciones de Valor"],
    horizontal=True,
    label_visibility="collapsed",
)
st.markdown("---")
col_logo, col_titulo = st.columns([1, 6])
with col_logo:
    st.image("https://a.espncdn.com/combiner/i?img=/i/leaguelogos/soccer/500/1.png", width=80)

with col_titulo:
    st.markdown('<div class="neon-title">Win Predictor LPF</div>', unsafe_allow_html=True)
    st.markdown('<div class="tech-sub">PLATAFORMA DE INTELIGENCIA PREDICTIVA & ANÁLISIS ESTOCÁSTICO</div>', unsafe_allow_html=True)

opcion_pantalla = st.radio(
    "Menú de Navegación:",
    ["Predicciones y Métricas", "Cuotas Justas y Opciones de Valor"],
    horizontal=True,
    label_visibility="collapsed"
)

st.markdown("---")

grupos = obtener_grupos_en_vivo_espn()

if not grupos:
    st.error("No se pudo obtener la información en vivo desde ESPN. Intenta refrescar la página.")
else:
    df_unificado = pd.concat(grupos.values(), ignore_index=True)
    lista_equipos = sorted(df_unificado["Equipo"].unique())
    partidos_del_dia = obtener_partidos_hoy_auto(lista_equipos)
    procesado, nuevos = procesar_agente_autonomo(partidos_del_dia, df_unificado, paquete_ia, lista_equipos)

    # =====================================================================
    # PANTALLA 1: PREDICCIONES Y MÉTRICAS
    # =====================================================================
    if opcion_pantalla == "Predicciones y Métricas":
        st.markdown("<h3 style='color: #cbd5e1;'>Tablas de Posiciones Oficiales por Zonas</h3>", unsafe_allow_html=True)
        cols_grupos = st.columns(len(grupos))
        for idx, (nombre_grupo, df_g) in enumerate(grupos.items()):
            with cols_grupos[idx]:
                st.markdown(f"<h4 style='color: #00ffcc; text-align: center;'>{nombre_grupo}</h4>", unsafe_allow_html=True)
                df_mostrar_grupo = df_g.drop(columns=["ID_ESPN"], errors="ignore")
                
                # Renderizar tabla configurando explícitamente la columna Escudo como imagen
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
                finalizados["res_real_1x2"] = np.where(finalizados["Goles_Local_Real"] > finalizados["Goles_Visita_Real"], "Local",
                                              np.where(finalizados["Goles_Visita_Real"] > finalizados["Goles_Local_Real"], "Visitante", "Empate"))
                finalizados["acierto_1x2"] = (finalizados["Prediccion_1X2"] == finalizados["res_real_1x2"]).astype(int)

                finalizados["goles_totales_reales"] = finalizados["Goles_Local_Real"] + finalizados["Goles_Visita_Real"]
                finalizados["over25_real"] = (finalizados["goles_totales_reales"] > 2.5).astype(int)
                finalizados["pred_over25"] = (finalizados["Prob_Over25"] >= 50.0).astype(int)
                finalizados["acierto_o25"] = (finalizados["pred_over25"] == finalizados["over25_real"]).astype(int)

                finalizados["marcador_real"] = finalizados["Goles_Local_Real"].astype(int).astype(str) + "-" + finalizados["Goles_Visita_Real"].astype(int).astype(str)
                finalizados["acierto_exacto"] = (finalizados["Marcador_Predicho"] == finalizados["marcador_real"]).astype(int)

                finalizados["btts_real"] = ((finalizados["Goles_Local_Real"] > 0) & (finalizados["Goles_Visita_Real"] > 0)).astype(int)
                finalizados["pred_btts"] = (finalizados["Prob_BTTS"] >= 50.0).astype(int)
                finalizados["acierto_btts"] = (finalizados["pred_btts"] == finalizados["btts_real"]).astype(int)

                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Acierto 1X2", f"{(finalizados['acierto_1x2'].mean()*100):.1f}%", f"{len(finalizados)} Evaluados")
                c2.metric("Acierto +/- 2.5 Goles", f"{(finalizados['acierto_o25'].mean()*100):.1f}%")
                c3.metric("Marcador Exacto", f"{(finalizados['acierto_exacto'].mean()*100):.1f}%")
                c4.metric("Acierto Ambos Anotan", f"{(finalizados['acierto_btts'].mean()*100):.1f}%")

                finalizados["Efectividad_Acumulada"] = (finalizados["acierto_1x2"].cumsum() / (np.arange(len(finalizados)) + 1)) * 100

                fig_efectividad = go.Figure()
                fig_efectividad.add_trace(go.Scatter(
                    x=list(range(1, len(finalizados) + 1)),
                    y=finalizados["Efectividad_Acumulada"],
                    mode='lines+markers',
                    name='Acierto 1X2 (%)',
                    line=dict(color='#00ffcc', width=3),
                    marker=dict(size=7, color='#00f3ff'),
                    hovertemplate="Partido N°%{x}<br>Efectividad: %{y:.1f}%<extra></extra>"
                ))
                fig_efectividad.update_layout(
                    title="Curva de Evolución del Porcentaje de Acierto (%)",
                    xaxis_title="Número de Partidos Evaluados",
                    yaxis_title="Acierto Acumulado (%)",
                    yaxis=dict(range=[0, 100], gridcolor="#1e293b"),
                    xaxis=dict(gridcolor="#1e293b"),
                    paper_bgcolor="#070b14",
                    plot_bgcolor="#111827",
                    font=dict(color="#cbd5e1"),
                    margin=dict(t=40, b=40, l=40, r=40)
                )
                st.plotly_chart(fig_efectividad, use_container_width=True)

                with st.expander("Ver registro detallado de las evaluaciones"):
                    df_mostrar = finalizados[["Fecha", "Local", "Visitante", "Prediccion_1X2", "res_real_1x2", "Marcador_Predicho", "marcador_real", "Prob_Over25", "goles_totales_reales"]].tail(10)
                    st.dataframe(df_mostrar, use_container_width=True, hide_index=True)

        st.markdown("---")

        st.markdown("<h3 style='color: #cbd5e1;'>Motor de Predicción de Partidos</h3>", unsafe_allow_html=True)

        if len(lista_equipos) >= 2:
            col1, col2 = st.columns(2)
            with col1: local = st.selectbox("Seleccionar Local", lista_equipos, index=0, key="sb_local")
            with col2: visitante = st.selectbox("Seleccionar Visitante", lista_equipos, index=min(1, len(lista_equipos) - 1), key="sb_visit")

            if local == visitante:
                st.error("SISTEMA BLOQUEADO: Seleccione escuadras diferentes.")
            else:
                row_loc = df_unificado[df_unificado["Equipo"] == local].iloc[0]
                row_vis = df_unificado[df_unificado["Equipo"] == visitante].iloc[0]

                FACTOR_LOCALIA = 0.15
                j_loc = obtener_jerarquia(local)
                j_vis = obtener_jerarquia(visitante)

                xg_proyectado_local = round(float(row_loc.get("xG", 1.25)) * (1.0 + FACTOR_LOCALIA), 2)
                xg_proyectado_visi = round(float(row_vis.get("xG", 1.10)) * (1.0 - (FACTOR_LOCALIA * 0.5)), 2)

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

                # Mostrar Tarjetas de Escudos
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

                st.markdown("<p style='text-align: center; color: #94a3b8; font-size: 13px; margin-bottom: 5px; text-transform: uppercase;'>Historial Directo (Últimos 5 vs)</p>", unsafe_allow_html=True)
                st.markdown(render_h2h_pills(historial_h2h, local, visitante), unsafe_allow_html=True)

                col_xg1, col_xg2 = st.columns(2)
                with col_xg1:
                    st.info(f"Jerarquía: **{j_loc}/10** | xG Proy: **{xg_proyectado_local}** | Forma (U5): **{stats_loc['Pts_U5']} pts**")
                with col_xg2:
                    st.info(f"Jerarquía: **{j_vis}/10** | xG Proy: **{xg_proyectado_visi}** | Forma (U5): **{stats_vis['Pts_U5']} pts**")

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
                with c_m4: st.metric(label="Corners Totales (Est.)", value=f"{round(stats_loc['Corners'] + stats_vis['Corners'], 1)}")

                st.markdown("---")

                st.markdown("<h4 style='color: #cbd5e1;'>Simulación Estocástica Monte Carlo (10,000 Partidos)</h4>", unsafe_allow_html=True)
                p_loc_mc, p_emp_mc, p_vis_mc, goles_sim = simular_monte_carlo(xg_proyectado_local, xg_proyectado_visi)
                c_mc1, c_mc2, c_mc3 = st.columns(3)
                c_mc1.metric(f"Victoria {local} (MC)", f"{p_loc_mc:.1f}%")
                c_mc2.metric("Empate (MC)", f"{p_emp_mc:.1f}%")
                c_mc3.metric(f"Victoria {visitante} (MC)", f"{p_vis_mc:.1f}%")

                fig_hist = go.Figure()
                fig_hist.add_trace(go.Scatter(y=np.histogram(goles_sim, bins=10)[0], mode='lines+markers', line=dict(color="#00f3ff", width=3)))
                fig_hist.update_layout(
                    title="Distribución de Goles Totales en 10,000 Simulaciones",
                    xaxis_title="Escenarios de Goles", yaxis_title="Frecuencia",
                    paper_bgcolor="#070b14", plot_bgcolor="#111827", font=dict(color="#cbd5e1"),
                    margin=dict(t=40, b=40, l=40, r=40),
                )
                st.plotly_chart(fig_hist, use_container_width=True)

                st.markdown("---")

                st.markdown("<h4 style='color: #cbd5e1;'>Frente a Frente: Análisis Octagonal</h4>", unsafe_allow_html=True)
                fig_radar = generar_radar(local, visitante, stats_loc, stats_vis)
                st.plotly_chart(fig_radar, use_container_width=True)

                st.markdown("---")

                st.markdown("<h4 style='color: #cbd5e1;'>Top 5 Marcadores Exactos Más Probables</h4>", unsafe_allow_html=True)
                top_5_marcadores, prob_otro = calcular_top_resultados(xg_proyectado_local, xg_proyectado_visi, prob_loc, prob_empate, prob_vis)

                tabla_marcadores = [{"Ranking": f"#{rank}", "Resultado Exacto": marcador, "Probabilidad": f"{prob:.1f}%"} for rank, (marcador, prob) in enumerate(top_5_marcadores, 1)]
                tabla_marcadores.append({"Ranking": "Otros", "Resultado Exacto": "Cualquier otro resultado", "Probabilidad": f"{prob_otro:.1f}%"})
                st.dataframe(pd.DataFrame(tabla_marcadores), use_container_width=True, hide_index=True)

    # =====================================================================
    # PANTALLA 2: CUOTAS JUSTAS & OPCIONES DE VALOR
    # =====================================================================
    elif opcion_pantalla == "Cuotas Justas y Opciones de Valor":
        st.markdown('<div class="neon-title">ANÁLISIS DE CUOTAS JUSTAS Y VALOR</div>', unsafe_allow_html=True)
        st.markdown('<div class="tech-sub">EVALUACIÓN AUTOMÁTICA DE MERCADOS Y OPORTUNIDADES ESTADÍSTICAS</div>', unsafe_allow_html=True)
        st.markdown("---")

        partidos_evaluar = partidos_del_dia.copy()

        if not partidos_evaluar:
            st.info("Sin partidos programados para el día de hoy en ESPN. Se muestran oportunidades calculadas entre cruces principales de la fecha.")
            equipos_disp = list(lista_equipos)
            np.random.seed(42)
            np.random.shuffle(equipos_disp)
            for i in range(0, min(10, len(equipos_disp)-1), 2):
                partidos_evaluar.append({"Local": equipos_disp[i], "Visitante": equipos_disp[i+1], "Hora": "Hoy"})

        opciones_probables = []
        opciones_razonables = []
        opciones_poco_probables = []
        mejores_opciones = []

        FACTOR_LOCALIA = 0.15

        for p in partidos_evaluar:
            loc, vis = p["Local"], p["Visitante"]
            if loc not in df_unificado["Equipo"].values or vis not in df_unificado["Equipo"].values:
                continue

            row_loc = df_unificado[df_unificado["Equipo"] == loc].iloc[0]
            row_vis = df_unificado[df_unificado["Equipo"] == vis].iloc[0]

            xgl = round(float(row_loc.get("xG", 1.25)) * (1.0 + FACTOR_LOCALIA), 2)
            xgv = round(float(row_vis.get("xG", 1.10)) * (1.0 - (FACTOR_LOCALIA * 0.5)), 2)

            sl = consolidar_estadisticas(loc, df_unificado, xgl)
            sv = consolidar_estadisticas(vis, df_unificado, xgv)
            h2h = obtener_historial_directo(loc, vis)

            pl, pe, pv, _ = realizar_prediccion(loc, vis, df_unificado, sl, sv, xgl, xgv, FACTOR_LOCALIA, h2h, paquete_ia)
            po25, pu25, pbtts = calcular_mercados_adicionales(xgl, xgv)

            mercados = [
                {"Partido": f"{loc} vs {vis}", "Mercado": f"Victoria {loc}", "Prob": pl},
                {"Partido": f"{loc} vs {vis}", "Mercado": f"Victoria {vis}", "Prob": pv},
                {"Partido": f"{loc} vs {vis}", "Mercado": "Empate", "Prob": pe},
                {"Partido": f"{loc} vs {vis}", "Mercado": "Más de 2.5 Goles", "Prob": po25},
                {"Partido": f"{loc} vs {vis}", "Mercado": "Menos de 2.5 Goles", "Prob": pu25},
                {"Partido": f"{loc} vs {vis}", "Mercado": "Ambos Anotan (Sí)", "Prob": pbtts},
            ]

            for m in mercados:
                prob = round(m["Prob"], 1)
                if prob <= 1.0:
                    continue
                
                cuota_teorica = round(100.0 / prob, 2)

                item = {
                    "Partido": m["Partido"],
                    "Mercado": m["Mercado"],
                    "Probabilidad": f"{prob}%",
                    "Cuota Justa": cuota_teorica,
                    "_prob_num": prob,
                    "_cuota_num": cuota_teorica
                }

                if prob >= 70.0:
                    opciones_probables.append(item)
                elif 50.0 <= prob < 70.0:
                    opciones_razonables.append(item)
                else:
                    if cuota_teorica >= 2.10:
                        opciones_poco_probables.append(item)

                if prob >= 60.0 and cuota_teorica >= 1.50:
                    mejores_opciones.append(item)

       
        # ---------------------------------------------------------------------
        # SECCIÓN 2: MEJORES OPCIONES DEL DÍA
        # ---------------------------------------------------------------------
        st.markdown("<h3 style='color: #00ffcc;'>Mejores opciones del día</h3>", unsafe_allow_html=True)
        st.caption("Oportunidades con alta convicción del modelo (probabilidad >= 60%) y excelente valor teórica (>= 1.50).")

        if mejores_opciones:
            df_mejores = pd.DataFrame(mejores_opciones).sort_values(by="_cuota_num", ascending=False).drop(columns=["_prob_num", "_cuota_num"])
            st.dataframe(df_mejores, use_container_width=True, hide_index=True)
        else:
            st.info("No hay selecciones que cumplan simultáneamente con los criterios de alta convicción y valor elevado para esta fecha.")

        st.markdown("---")

        # ---------------------------------------------------------------------
        # SECCIÓN 3: OPCIONES PROBABLES
        # ---------------------------------------------------------------------
        st.markdown("<h3 style='color: #00f3ff;'>Opciones Probables (Probabilidad >= 70%)</h3>", unsafe_allow_html=True)
        st.caption("Eventos con altísima tasa estimada de ocurrencia y cuotas estimadas moderadas.")

        if opciones_probables:
            df_probables = pd.DataFrame(opciones_probables).sort_values(by="_prob_num", ascending=False).drop(columns=["_prob_num", "_cuota_num"])
            st.dataframe(df_probables, use_container_width=True, hide_index=True)
        else:
            st.info("Sin opciones probables superando el 70% de probabilidades para este bloque de partidos.")

        st.markdown("---")

        # ---------------------------------------------------------------------
        # SECCIÓN 4: OPCIONES RAZONABLES
        # ---------------------------------------------------------------------
        st.markdown("<h3 style='color: #ffb703;'>Opciones Razonables (50% - 70% de probabilidad)</h3>", unsafe_allow_html=True)
        st.caption("Escenarios equilibrados con probabilidades moderadas y cuotas significativamente más altas.")

        if opciones_razonables:
            df_razonables = pd.DataFrame(opciones_razonables).sort_values(by="_prob_num", ascending=False).drop(columns=["_prob_num", "_cuota_num"])
            st.dataframe(df_razonables, use_container_width=True, hide_index=True)
        else:
            st.info("Sin opciones registradas en el rango del 50% al 70%.")

        st.markdown("---")

        # ---------------------------------------------------------------------
        # SECCIÓN 5: OPCIONES POCO PROBABLES
        # ---------------------------------------------------------------------
        st.markdown("<h3 style='color: #ff3366;'>Opciones Poco Probables (< 50% de probabilidad)</h3>", unsafe_allow_html=True)
        st.caption("Opciones de riesgo superior pero con cuotas teóricas muy elevadas (superior a 2.10).")

        if opciones_poco_probables:
            df_pocos = pd.DataFrame(opciones_poco_probables).sort_values(by="_cuota_num", ascending=False).head(15).drop(columns=["_prob_num", "_cuota_num"])
            st.dataframe(df_pocos, use_container_width=True, hide_index=True)
        else:
            st.info("Sin opciones poco probables destacadas en este bloque.")
