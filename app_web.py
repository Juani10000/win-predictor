import datetime
import os
import joblib
import numpy as np
import pandas as pd
import requests
import streamlit as st
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline

# =====================================================================
# 1. GARANTIZAR MODELO COMPATIBLE (11 FEATURES)
# =====================================================================
def asegurar_modelo_existente():
    """Verifica y recrea 'modelo_ia_lpf.pkl' si no existe o si no coincide la dimensión de 11 variables."""
    necesita_recrear = False
    
    if not os.path.exists("modelo_ia_lpf.pkl"):
        necesita_recrear = True
    else:
        try:
            m = joblib.load("modelo_ia_lpf.pkl")
            # Prueba de control enviando 11 columnas para validar compatibilidad con train.py
            test_x = np.ones((1, 11))
            m.predict_proba(test_x)
        except Exception:
            necesita_recrear = True

    if necesita_recrear:
        # Dataset dummy inicial con 11 variables para evitar fallos si no se ha ejecutado train.py
        X_init = np.random.randn(10, 11)
        y_init = np.array([1, 2, 0, 1, 2, 1, 0, 2, 1, 0])

        modelo_base = Pipeline([
            ('scaler', StandardScaler()),
            ('lr', LogisticRegression())
        ])
        modelo_base.fit(X_init, y_init)
        joblib.dump(modelo_base, "modelo_ia_lpf.pkl")

asegurar_modelo_existente()

# =====================================================================
# 2. CONFIGURACIÓN Y CSS COMPACTO PARA MÓVIL
# =====================================================================
st.set_page_config(page_title="Win Predictor LPF", layout="centered")

css_mobile_compact = """
    <style>
    #MainMenu, header, footer, .stAppHeader {display: none !important;}
    
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

    .dataframe { font-size: 10px !important; }
    </style>
"""
st.markdown(css_mobile_compact, unsafe_allow_html=True)

ESCUDO_DEFAULT = "https://a.espncdn.com/combiner/i?img=/i/leaguelogos/soccer/500/1.png"

# =====================================================================
# 3. CONEXIÓN ESPN EN VIVO
# =====================================================================
@st.cache_data(ttl=1800)
def obtener_tabla_posiciones_espn():
    url = "https://site.api.espn.com/apis/v2/sports/soccer/arg.1/standings"
    grupos = {}
    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            data = r.json()
            children = data.get("children", []) or [data]

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
# 4. EXTRACCIÓN Y PREDICCIÓN CON MODELO DE 11 VARIABLES
# =====================================================================
def extraer_features_seguras_df(row_loc, row_vis):
    pj_loc = float(row_loc.get("PJ", 0))
    pts_loc = float(row_loc.get("Pts", 0))
    dg_loc_tot = float(row_loc.get("DG", 0))

    pj_vis = float(row_vis.get("PJ", 0))
    pts_vis = float(row_vis.get("Pts", 0))
    dg_vis_tot = float(row_vis.get("DG", 0))

    # Métricas y promedios por partido
    ppm_loc = (pts_loc + 1.0) / (pj_loc + 1.0) if pj_loc < 3 else pts_loc / pj_loc
    ppm_vis = (pts_vis + 1.0) / (pj_vis + 1.0) if pj_vis < 3 else pts_vis / pj_vis

    dg_loc = dg_loc_tot / (pj_loc + 1.0) if pj_loc < 3 else dg_loc_tot / pj_loc
    dg_vis = dg_vis_tot / (pj_vis + 1.0) if pj_vis < 3 else dg_vis_tot / pj_vis

    # Estimación de rendimiento según cancha y estado de forma
    ppm_loc_cancha = ppm_loc * 1.15
    ppm_vis_cancha = ppm_vis * 0.85
    forma_loc = ppm_loc
    forma_vis = ppm_vis

    # Retorna exactamente las 11 variables que espera el ensamble de train.py
    return pd.DataFrame([{
        "ppm_loc": ppm_loc,
        "ppm_vis": ppm_vis,
        "ppm_loc_cancha": ppm_loc_cancha,
        "ppm_vis_cancha": ppm_vis_cancha,
        "dg_loc": dg_loc,
        "dg_vis": dg_vis,
        "forma_loc": forma_loc,
        "forma_vis": forma_vis,
        "dif_ppm": ppm_loc - ppm_vis,
        "dif_dg": dg_loc - dg_vis,
        "dif_forma": forma_loc - forma_vis
    }])

def predecir_partido_ia(local, visitante, df_unificado):
    try:
        row_loc = df_unificado[df_unificado["Equipo"] == local].iloc[0]
        row_vis = df_unificado[df_unificado["Equipo"] == visitante].iloc[0]

        features = extraer_features_seguras_df(row_loc, row_vis)

        if os.path.exists("modelo_ia_lpf.pkl"):
            modelo = joblib.load("modelo_ia_lpf.pkl")
            probs = modelo.predict_proba(features)[0]
            clases = list(modelo.classes_)

            p_loc_raw = probs[clases.index(1)] if 1 in clases else 0.35
            p_emp_raw = probs[clases.index(0)] if 0 in clases else 0.30
            p_vis_raw = probs[clases.index(2)] if 2 in clases else 0.35

            # Normalización directa sin truncamiento artificial
            total = p_loc_raw + p_emp_raw + p_vis_raw
            p_loc = int(round((p_loc_raw / total) * 100))
            p_emp = int(round((p_emp_raw / total) * 100))
            p_vis = max(0, 100 - p_loc - p_emp)

            return p_loc, p_emp, p_vis
    except Exception:
        pass

    return 38, 31, 31

# =====================================================================
# 5. TARJETA VISUAL Y VISTA PRINCIPAL
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

    st.markdown("<div style='font-size: 13px; font-weight: 800; color: #00f3ff; margin-bottom: 8px;'>⚽ PARTIDOS DE HOY</div>", unsafe_allow_html=True)
    
    partidos_hoy = obtener_partidos_hoy(lista_equipos)

    if partidos_hoy:
        for p in partidos_hoy:
            renderizar_tarjeta_partido(p["Local"], p["Visitante"], p["Hora"], df_unificado)
    else:
        st.info("No hay partidos oficiales programados para hoy. Prueba el simulador:")
        col1, col2 = st.columns(2)
        with col1:
            eq_loc = st.selectbox("Local", lista_equipos, index=0)
        with col2:
            eq_vis = st.selectbox("Visitante", lista_equipos, index=min(1, len(lista_equipos)-1))
        
        if eq_loc != eq_vis:
            renderizar_tarjeta_partido(eq_loc, eq_vis, "VS", df_unificado)

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
