import datetime
import os
import joblib
import numpy as np
import pandas as pd
import requests
import streamlit as st
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline

# =====================================================================
# 1. CONFIGURACIÓN Y CSS COMPACTO PARA MÓVIL
# =====================================================================
st.set_page_config(page_title="Win Predictor LPF", layout="centered")

css_mobile_compact = """
    <style>
    #MainMenu, header, footer, .stAppHeader {display: none !important;}
    
    /* Reducción general de paddings para cel */
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 1rem !important;
        padding-left: 0.5rem !important;
        padding-right: 0.5rem !important;
    }
    .stApp {
        background-color: #0d1117;
        color: #e2e8f0;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }
    
    /* Encabezado compacto */
    .mobile-header {
        text-align: center;
        padding: 5px 0 10px 0;
    }
    .mobile-title {
        font-size: 20px;
        font-weight: 900;
        color: #ffffff;
        letter-spacing: 0.5px;
        text-transform: uppercase;
        margin: 0;
    }
    .mobile-sub {
        color: #00f3ff;
        font-size: 10px;
        font-weight: 700;
        letter-spacing: 1px;
    }

    /* Tarjeta de Partido */
    .match-card {
        background: #161b22;
        border: 1px solid #30363d;
        border-radius: 8px;
        padding: 10px;
        margin-bottom: 12px;
    }
    .match-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        font-size: 12px;
        font-weight: 700;
        color: #f0f6fc;
        margin-bottom: 8px;
    }
    .team-box {
        display: flex;
        align-items: center;
        gap: 6px;
        width: 42%;
    }
    .team-box.right {
        justify-content: flex-end;
    }
    .team-logo {
        width: 24px;
        height: 24px;
        object-fit: contain;
    }
    .team-name {
        font-size: 12px;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    .vs-badge {
        font-size: 10px;
        color: #8b949e;
        background: #21262d;
        padding: 2px 6px;
        border-radius: 4px;
    }

    /* Contenedor de la barra unificada estilo imagen */
    .prob-container {
        background-color: #0d1117;
        border-radius: 6px;
        padding: 8px 10px;
        margin-top: 6px;
    }
    .prob-title {
        text-align: center;
        font-size: 9px;
        font-weight: 800;
        color: #8b949e;
        letter-spacing: 1px;
        margin-bottom: 6px;
    }
    .prob-labels {
        display: flex;
        justify-content: space-between;
        font-size: 11px;
        font-weight: 700;
        margin-bottom: 5px;
    }
    .prob-val {
        font-size: 12px;
        font-weight: 800;
    }
    
    /* Barra progresiva continua dividida */
    .prob-bar-wrapper {
        display: flex;
        height: 7px;
        border-radius: 3px;
        overflow: hidden;
        gap: 2px;
        background-color: #21262d;
    }
    .bar-loc { background-color: #ff6b81; }
    .bar-emp { background-color: #cbd5e1; }
    .bar-vis { background-color: #70a1ff; }

    /* Achicar tablas de posiciones */
    .dataframe {
        font-size: 10px !important;
    }
    </style>
"""
st.markdown(css_mobile_compact, unsafe_allow_html=True)

ESCUDO_DEFAULT = "https://a.espncdn.com/combiner/i?img=/i/leaguelogos/soccer/500/1.png"
RUTA_DATASET = "dataset_historico.csv"
RUTA_MODELO = "modelo_ia_lpf.pkl"

# =====================================================================
# 2. CONEXIÓN ESPN EN VIVO
# =====================================================================
@st.cache_data(ttl=1800)
def obtener_tabla_posiciones_espn():
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
                nombre_grupo = grupo.get("name", f"Zona {chr(65 + idx)}")
                entries = grupo.get("standings", {}).get("entries", [])
                
                lista_equipos = []
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

                    lista_equipos.append({
                        "Escudo": logo_url,
                        "Equipo": nombre,
                        "ID_ESPN": team_id,
                        "Pts": pts,
                        "PJ": pj,
                        "DG": gf - gc
                    })

                df_g = pd.DataFrame(lista_equipos)
                if not df_g.empty:
                    df_g = df_g.sort_values(by=["Pts", "DG"], ascending=[False, False]).reset_index(drop=True)
                    df_g.insert(0, "Pos", range(1, len(df_g) + 1))
                grupos[nombre_grupo] = df_g
    except Exception:
        pass
    return grupos

@st.cache_data(ttl=1800)
def obtener_ultimos_partidos_equipo(team_id):
    if not team_id:
        return []
    url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/arg.1/teams/{team_id}/schedule"
    historial = []
    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            for ev in r.json().get("events", []):
                if ev.get("status", {}).get("type", {}).get("completed", False):
                    comps = ev["competitions"][0]["competitors"]
                    mi_eq = comps[0] if str(comps[0].get("team", {}).get("id")) == str(team_id) else comps[1]
                    riv_eq = comps[1] if str(comps[0].get("team", {}).get("id")) == str(team_id) else comps[0]

                    gf = int(mi_eq.get("score", {}).get("value", 0))
                    gc = int(riv_eq.get("score", {}).get("value", 0))
                    pts = 3 if gf > gc else (1 if gf == gc else 0)

                    historial.append({"GF": gf, "GC": gc, "Pts": pts})
            historial.reverse()
    except Exception:
        pass
    return historial

def buscar_equipo(nombre_buscado, lista_equipos):
    nombre_clean = nombre_buscado.lower().strip()
    for eq in lista_equipos:
        if nombre_clean == eq.lower().strip() or nombre_clean in eq.lower().strip() or eq.lower().strip() in nombre_clean:
            return eq
    return None

@st.cache_data(ttl=1800)
def obtener_partidos_hoy(lista_equipos):
    ahora_arg = datetime.datetime.utcnow() - datetime.timedelta(hours=3)
    fecha_hoy_str = ahora_arg.strftime("%Y-%m-%d")
    url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/arg.1/scoreboard?dates={ahora_arg.strftime('%Y%m%d')}"
    partidos = []

    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            for event in r.json().get("events", []):
                fecha_partido = datetime.datetime.strptime(event["date"], "%Y-%m-%dT%H:%MZ") - datetime.timedelta(hours=3)
                if fecha_partido.strftime("%Y-%m-%d") == fecha_hoy_str:
                    comps = event["competitions"][0]["competitors"]
                    loc_raw = comps[0]["team"]["name"] if comps[0]["homeAway"] == "home" else comps[1]["team"]["name"]
                    vis_raw = comps[1]["team"]["name"] if comps[0]["homeAway"] == "home" else comps[0]["team"]["name"]

                    loc_match = buscar_equipo(loc_raw, lista_equipos)
                    vis_match = buscar_equipo(vis_raw, lista_equipos)

                    if loc_match and vis_match and loc_match != vis_match:
                        partidos.append({
                            "Local": loc_match,
                            "Visitante": vis_match,
                            "Hora": fecha_partido.strftime("%H:%M")
                        })
    except Exception:
        pass
    return partidos

# =====================================================================
# 3. PIPELINE DE INTELIGENCIA ARTIFICIAL
# =====================================================================
def extraer_features(local, visitante, df_unificado):
    row_loc = df_unificado[df_unificado["Equipo"] == local].iloc[0]
    row_vis = df_unificado[df_unificado["Equipo"] == visitante].iloc[0]

    h_loc = obtener_ultimos_partidos_equipo(row_loc.get("ID_ESPN"))
    h_vis = obtener_ultimos_partidos_equipo(row_vis.get("ID_ESPN"))

    u5_loc = h_loc[-5:] if len(h_loc) >= 5 else h_loc
    u5_vis = h_vis[-5:] if len(h_vis) >= 5 else h_vis

    pts_u5_loc = sum(p["Pts"] for p in u5_loc) if u5_loc else 5
    pts_u5_vis = sum(p["Pts"] for p in u5_vis) if u5_vis else 5

    prom_gf_u5_loc = (sum(p["GF"] for p in u5_loc) / len(u5_loc)) if u5_loc else 1.0
    prom_gc_u5_loc = (sum(p["GC"] for p in u5_loc) / len(u5_loc)) if u5_loc else 1.0

    prom_gf_u5_vis = (sum(p["GF"] for p in u5_vis) / len(u5_vis)) if u5_vis else 1.0
    prom_gc_u5_vis = (sum(p["GC"] for p in u5_vis) / len(u5_vis)) if u5_vis else 1.0

    pj_loc = max(1, int(row_loc.get("PJ", 1)))
    pj_vis = max(1, int(row_vis.get("PJ", 1)))

    return {
        "pos_loc": int(row_loc.get("Pos", 15)),
        "pos_vis": int(row_vis.get("Pos", 15)),
        "prom_pts_loc": float(row_loc.get("Pts", 0)) / pj_loc,
        "prom_pts_vis": float(row_vis.get("Pts", 0)) / pj_vis,
        "pts_u5_loc": pts_u5_loc,
        "pts_u5_vis": pts_u5_vis,
        "prom_gf_u5_loc": prom_gf_u5_loc,
        "prom_gc_u5_loc": prom_gc_u5_loc,
        "prom_gf_u5_vis": prom_gf_u5_vis,
        "prom_gc_u5_vis": prom_gc_u5_vis,
        "dif_pos": int(row_vis.get("Pos", 15)) - int(row_loc.get("Pos", 15)),
        "dif_prom_pts": (float(row_loc.get("Pts", 0)) / pj_loc) - (float(row_vis.get("Pts", 0)) / pj_vis)
    }

def inicializar_dataset_y_modelo(df_unificado):
    if not os.path.exists(RUTA_DATASET):
        filas = []
        equipos = df_unificado["Equipo"].unique()
        for eq in equipos:
            row_eq = df_unificado[df_unificado["Equipo"] == eq].iloc[0]
            team_id = row_eq.get("ID_ESPN")
            try:
                r = requests.get(f"https://site.api.espn.com/apis/site/v2/sports/soccer/arg.1/teams/{team_id}/schedule", timeout=5)
                if r.status_code == 200:
                    for ev in r.json().get("events", []):
                        if ev.get("status", {}).get("type", {}).get("completed", False):
                            comps = ev["competitions"][0]["competitors"]
                            is_home = (str(comps[0].get("team", {}).get("id")) == str(team_id) and comps[0].get("homeAway") == "home")
                            if is_home:
                                vis_raw = comps[1].get("team", {}).get("displayName", "")
                                vis_name = buscar_equipo(vis_raw, equipos)
                                if vis_name and vis_name in df_unificado["Equipo"].values:
                                    g_loc = int(comps[0].get("score", {}).get("value", 0))
                                    g_vis = int(comps[1].get("score", {}).get("value", 0))
                                    res = 1 if g_loc > g_vis else (0 if g_loc == g_vis else 2)
                                    f = extraer_features(eq, vis_name, df_unificado)
                                    f["resultado"] = res
                                    filas.append(f)
            except Exception:
                pass

        df_base = pd.DataFrame(filas).drop_duplicates() if filas else pd.DataFrame()
        df_base.to_csv(RUTA_DATASET, index=False)

    entrenar_y_guardar_modelo()

def entrenar_y_guardar_modelo():
    if os.path.exists(RUTA_DATASET):
        df = pd.read_csv(RUTA_DATASET)
        if len(df) >= 5:
            X = df.drop(columns=["resultado"])
            y = df["resultado"]
            modelo = Pipeline([
                ('scaler', StandardScaler()),
                ('rf', RandomForestClassifier(n_estimators=100, random_state=42))
            ])
            modelo.fit(X, y)
            joblib.dump(modelo, RUTA_MODELO)

def predecir_partido_ia(local, visitante, df_unificado):
    if not os.path.exists(RUTA_MODELO):
        inicializar_dataset_y_modelo(df_unificado)

    try:
        modelo = joblib.load(RUTA_MODELO)
        f_dict = extraer_features(local, visitante, df_unificado)
        probs = modelo.predict_proba(pd.DataFrame([f_dict]))[0]
        clases = list(modelo.classes_)

        prob_loc = float(probs[clases.index(1)]) * 100 if 1 in clases else 33.3
        prob_emp = float(probs[clases.index(0)]) * 100 if 0 in clases else 33.3
        prob_vis = float(probs[clases.index(2)]) * 100 if 2 in clases else 33.3

        total = prob_loc + prob_emp + prob_vis
        return int(round((prob_loc/total)*100)), int(round((prob_emp/total)*100)), int(round((prob_vis/total)*100))
    except Exception:
        return 40, 30, 30

# =====================================================================
# 4. COMPONENTE VISUAL DE BARRA DE PROBABILIDAD UNIFICADA
# =====================================================================
def renderizar_tarjeta_partido(local, visitante, hora, df_unificado):
    prob_loc, prob_emp, prob_vis = predecir_partido_ia(local, visitante, df_unificado)
    
    row_loc = df_unificado[df_unificado["Equipo"] == local].iloc[0]
    row_vis = df_unificado[df_unificado["Equipo"] == visitante].iloc[0]

    escudo_loc = row_loc.get("Escudo", ESCUDO_DEFAULT)
    escudo_vis = row_vis.get("Escudo", ESCUDO_DEFAULT)

    html_card = f"""
    <div class="match-card">
        <div class="match-header">
            <div class="team-box">
                <img src="{escudo_loc}" class="team-logo"/>
                <span class="team-name">{local}</span>
            </div>
            <span class="vs-badge">{hora}</span>
            <div class="team-box right">
                <span class="team-name">{visitante}</span>
                <img src="{escudo_vis}" class="team-logo"/>
            </div>
        </div>
        <div class="prob-container">
            <div class="prob-title">PROBABILIDAD DE VICTORIA</div>
            <div class="prob-labels">
                <div style="color: #ff6b81; text-align: left;">
                    <div>{local}</div>
                    <div class="prob-val">{prob_loc}%</div>
                </div>
                <div style="color: #cbd5e1; text-align: center;">
                    <div>Empate</div>
                    <div class="prob-val">{prob_emp}%</div>
                </div>
                <div style="color: #70a1ff; text-align: right;">
                    <div>{visitante}</div>
                    <div class="prob-val">{prob_vis}%</div>
                </div>
            </div>
            <div class="prob-bar-wrapper">
                <div class="bar-loc" style="width: {prob_loc}%;"></div>
                <div class="bar-emp" style="width: {prob_emp}%;"></div>
                <div class="bar-vis" style="width: {prob_vis}%;"></div>
            </div>
        </div>
    </div>
    """
    st.markdown(html_card, unsafe_allow_html=True)

# =====================================================================
# 5. VISTA PRINCIPAL STREAMLIT
# =====================================================================
st.markdown("""
    <div class="mobile-header">
        <div class="mobile-title">Win Predictor LPF</div>
        <div class="mobile-sub">IA DE PREDICCIÓN & EN VIVO</div>
    </div>
""", unsafe_allow_html=True)

grupos = obtener_tabla_posiciones_espn()

if grupos:
    df_unificado = pd.concat(grupos.values(), ignore_index=True)
    lista_equipos = sorted(df_unificado["Equipo"].unique())

    if not os.path.exists(RUTA_MODELO):
        inicializar_dataset_y_modelo(df_unificado)

    # -----------------------------------------------------------------
    # SECCIÓN: PARTIDOS DE LA FECHA (LISTADOS AUTOMÁTICAMENTE UNO ABAJO DEL OTRO)
    # -----------------------------------------------------------------
    st.markdown("<div style='font-size: 13px; font-weight: 800; color: #00f3ff; margin-bottom: 8px;'>⚽ PARTIDOS DE HOY</div>", unsafe_allow_html=True)
    
    partidos_hoy = obtener_partidos_hoy(lista_equipos)

    if partidos_hoy:
        for p in partidos_hoy:
            renderizar_tarjeta_partido(p["Local"], p["Visitante"], p["Hora"], df_unificado)
    else:
        st.info("No hay partidos oficiales programados para hoy. Mostrando simulador:")
        col1, col2 = st.columns(2)
        with col1:
            eq_loc = st.selectbox("Local", lista_equipos, index=0)
        with col2:
            eq_vis = st.selectbox("Visitante", lista_equipos, index=min(1, len(lista_equipos)-1))
        
        if eq_loc != eq_vis:
            renderizar_tarjeta_partido(eq_loc, eq_vis, "VS", df_unificado)

    # -----------------------------------------------------------------
    # SECCIÓN: TABLAS DE POSICIONES
    # -----------------------------------------------------------------
    st.markdown("<div style='font-size: 13px; font-weight: 800; color: #00ffcc; margin-top: 15px; margin-bottom: 8px;'>🏆 TABLA DE POSICIONES</div>", unsafe_allow_html=True)
    
    for nombre_grupo, df_g in grupos.items():
        with st.expander(f"📌 {nombre_grupo}", expanded=True):
            df_mostrar = df_g[["Pos", "Escudo", "Equipo", "Pts", "PJ", "DG"]]
            st.dataframe(
                df_mostrar,
                column_config={
                    "Pos": st.column_config.NumberColumn("", width="small"),
                    "Escudo": st.column_config.ImageColumn("", width="small"),
                    "Equipo": st.column_config.TextColumn("Equipo", width="medium"),
                    "Pts": st.column_config.NumberColumn("Pts", width="small"),
                    "PJ": st.column_config.NumberColumn("PJ", width="small"),
                    "DG": st.column_config.NumberColumn("DG", width="small")
                },
                use_container_width=True,
                hide_index=True
            )
