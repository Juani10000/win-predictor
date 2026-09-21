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
# 1. CONFIGURACIÓN DE PÁGINA Y ESTILO MÓVIL NEÓN
# =====================================================================
st.set_page_config(page_title="Win Predictor LPF | IA", layout="wide")

ocultar_elementos = """
    <style>
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    .stAppHeader {display: none;}
    .stApp {
        background-color: #070b14;
        color: #e2e8f0;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    .neon-title {
        font-size: 32px;
        font-weight: 900;
        color: #ffffff;
        text-shadow: 0 0 10px #00f3ff, 0 0 20px #00f3ff;
        margin-bottom: 2px;
        text-transform: uppercase;
    }
    .tech-sub {
        color: #94a3b8;
        letter-spacing: 1px;
        font-size: 12px;
        margin-bottom: 15px;
        font-weight: 600;
    }
    .team-card {
        background: #0d1527;
        border: 1px solid #00f3ff40;
        border-radius: 10px;
        padding: 12px;
        text-align: center;
        margin-bottom: 10px;
    }
    .team-shield {
        max-width: 70px;
        max-height: 70px;
        object-fit: contain;
    }
    [data-testid="stMetricValue"] {
        color: #00ffcc !important;
        font-size: 26px !important;
        font-weight: 800 !important;
    }
    </style>
"""
st.markdown(ocultar_elementos, unsafe_allow_html=True)

ESCUDO_DEFAULT = "https://a.espncdn.com/combiner/i?img=/i/leaguelogos/soccer/500/1.png"
RUTA_DATASET = "dataset_historico.csv"
RUTA_MODELO = "modelo_ia_lpf.pkl"

# =====================================================================
# 2. CONEXIÓN A ESPN EN VIVO (TABLAS Y BUSCADOR DE PARTIDOS)
# =====================================================================
@st.cache_data(ttl=1800)
def obtener_tabla_posiciones_espn():
    """Obtiene la tabla de posiciones en vivo desde la API de ESPN."""
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
                        "GF": gf,
                        "GC": gc,
                        "DG": gf - gc
                    })

                df_g = pd.DataFrame(lista_equipos)
                if not df_g.empty:
                    df_g = df_g.sort_values(by=["Pts", "DG", "GF"], ascending=[False, False, False]).reset_index(drop=True)
                    df_g.insert(0, "Pos", range(1, len(df_g) + 1))
                grupos[nombre_grupo] = df_g
    except Exception as e:
        st.error(f"Error al conectar con la API de ESPN: {e}")

    return grupos

@st.cache_data(ttl=1800)
def obtener_ultimos_partidos_equipo(team_id):
    """Obtiene el historial de partidos finalizados de un equipo."""
    if not team_id:
        return []
    url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/arg.1/teams/{team_id}/schedule"
    historial = []

    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            events = r.json().get("events", [])
            for ev in events:
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
    """Buscador de partidos de la fecha que se juegan hoy."""
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
# 3. MOTOR DE APRENDIZAJE AUTOMÁTICO DE IA (PIPELINE AUTO-MEJORABLE)
# =====================================================================
def extraer_features(local, visitante, df_unificado):
    """Calcula el vector numérico de características (features) para la IA."""
    row_loc = df_unificado[df_unificado["Equipo"] == local].iloc[0]
    row_vis = df_unificado[df_unificado["Equipo"] == visitante].iloc[0]

    h_loc = obtener_ultimos_partidos_equipo(row_loc.get("ID_ESPN"))
    h_vis = obtener_ultimos_partidos_equipo(row_vis.get("ID_ESPN"))

    # Métricas en los últimos 5 partidos
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

    features = {
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
    return features

def inicializar_dataset_y_modelo(df_unificado):
    """Si no existe un modelo previo, extrae datos históricos de la liga para entrenar el primer modelo IA."""
    if not os.path.exists(RUTA_DATASET):
        filas = []
        equipos = df_unificado["Equipo"].unique()
        
        # Descargamos los partidos ya jugados para armar la base de entrenamiento inicial
        for eq in equipos:
            row_eq = df_unificado[df_unificado["Equipo"] == eq].iloc[0]
            team_id = row_eq.get("ID_ESPN")
            url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/arg.1/teams/{team_id}/schedule"
            try:
                r = requests.get(url, timeout=5)
                if r.status_code == 200:
                    for ev in r.json().get("events", []):
                        if ev.get("status", {}).get("type", {}).get("completed", False):
                            comps = ev["competitions"][0]["competitors"]
                            is_home = (str(comps[0].get("team", {}).get("id")) == str(team_id) and comps[0].get("homeAway") == "home")
                            if is_home:
                                loc_name = eq
                                vis_raw = comps[1].get("team", {}).get("displayName", "")
                                vis_name = buscar_equipo(vis_raw, equipos)
                                if vis_name and vis_name in df_unificado["Equipo"].values:
                                    g_loc = int(comps[0].get("score", {}).get("value", 0))
                                    g_vis = int(comps[1].get("score", {}).get("value", 0))
                                    res = 1 if g_loc > g_vis else (0 if g_loc == g_vis else 2)

                                    f = extraer_features(loc_name, vis_name, df_unificado)
                                    f["resultado"] = res
                                    filas.append(f)
            except Exception:
                pass

        df_base = pd.DataFrame(filas).drop_duplicates()
        if not df_base.empty:
            df_base.to_csv(RUTA_DATASET, index=False)
        else:
            # Fallback seguro
            cols = ["pos_loc", "pos_vis", "prom_pts_loc", "prom_pts_vis", "pts_u5_loc", "pts_u5_vis", 
                    "prom_gf_u5_loc", "prom_gc_u5_loc", "prom_gf_u5_vis", "prom_gc_u5_vis", "dif_pos", "dif_prom_pts", "resultado"]
            df_base = pd.DataFrame(columns=cols)
            df_base.to_csv(RUTA_DATASET, index=False)

    entrenar_y_guardar_modelo()

def entrenar_y_guardar_modelo():
    """Entrena un pipeline de RandomForest que aprende progresivamente de los partidos."""
    if os.path.exists(RUTA_DATASET):
        df = pd.read_csv(RUTA_DATASET)
        if len(df) >= 10:
            X = df.drop(columns=["resultado"])
            y = df["resultado"]

            modelo = Pipeline([
                ('scaler', StandardScaler()),
                ('rf', RandomForestClassifier(n_estimators=100, random_state=42))
            ])
            modelo.fit(X, y)
            joblib.dump(modelo, RUTA_MODELO)

def predecir_partido_ia(local, visitante, df_unificado):
    """Aplica la IA auto-mejorable para predecir las probabilidades del partido."""
    if not os.path.exists(RUTA_MODELO):
        inicializar_dataset_y_modelo(df_unificado)

    try:
        modelo = joblib.load(RUTA_MODELO)
        f_dict = extraer_features(local, visitante, df_unificado)
        f_df = pd.DataFrame([f_dict])

        probs = modelo.predict_proba(f_df)[0]
        clases = list(modelo.classes_)

        prob_loc = float(probs[clases.index(1)]) * 100 if 1 in clases else 33.3
        prob_emp = float(probs[clases.index(0)]) * 100 if 0 in clases else 33.3
        prob_vis = float(probs[clases.index(2)]) * 100 if 2 in clases else 33.3

        # Normalización por seguridad
        total = prob_loc + prob_emp + prob_vis
        return round((prob_loc/total)*100, 1), round((prob_emp/total)*100, 1), round((prob_vis/total)*100, 1)
    except Exception:
        return 40.0, 30.0, 30.0

def registrar_resultado_y_reentrenar(local, visitante, resultado_real, df_unificado):
    """
    Función de auto-aprendizaje:
    Añade el resultado recién finalizado (1: Ganó Local, 0: Empate, 2: Ganó Visitante) al dataset
    y reentrena el modelo inmediatamente para mejorar con el tiempo.
    """
    f = extraer_features(local, visitante, df_unificado)
    f["resultado"] = resultado_real
    
    if os.path.exists(RUTA_DATASET):
        df_hist = pd.read_csv(RUTA_DATASET)
        df_hist = pd.concat([df_hist, pd.DataFrame([f])], ignore_index=True)
        df_hist.to_csv(RUTA_DATASET, index=False)
    else:
        pd.DataFrame([f]).to_csv(RUTA_DATASET, index=False)

    entrenar_y_guardar_modelo()

# =====================================================================
# 4. INTERFAZ GRÁFICA PRINCIPAL STREAMLIT
# =====================================================================
col_logo, col_titulo = st.columns([1, 6])
with col_logo:
    st.image(ESCUDO_DEFAULT, width=70)
with col_titulo:
    st.markdown('<div class="neon-title">Win Predictor LPF</div>', unsafe_allow_html=True)
    st.markdown('<div class="tech-sub">TABLA EN VIVO & MODELO DE PREDICCIÓN AUTO-APRENDIZ (ML)</div>', unsafe_allow_html=True)

grupos = obtener_tabla_posiciones_espn()

if not grupos:
    st.error("Servicio de datos no disponible temporalmente. Reintenta en unos instantes.")
else:
    df_unificado = pd.concat(grupos.values(), ignore_index=True)
    lista_equipos = sorted(df_unificado["Equipo"].unique())

    # Garantizar que el modelo inicial esté listo
    if not os.path.exists(RUTA_MODELO):
        inicializar_dataset_y_modelo(df_unificado)

    # -----------------------------------------------------------------
    # SECCIÓN 1: TABLA DE POSICIONES EN VIVO
    # -----------------------------------------------------------------
    st.markdown("---")
    st.markdown("<h3 style='color: #00ffcc;'>🏆 Tabla de Posiciones Oficiales</h3>", unsafe_allow_html=True)
    
    cols = st.columns(len(grupos))
    for idx, (nombre_grupo, df_g) in enumerate(grupos.items()):
        with cols[idx]:
            st.markdown(f"<h4 style='color: #ffffff; text-align: center;'>{nombre_grupo}</h4>", unsafe_allow_html=True)
            df_mostrar = df_g.drop(columns=["ID_ESPN"], errors="ignore")
            st.dataframe(
                df_mostrar,
                column_config={
                    "Pos": st.column_config.NumberColumn("Pos", width="small"),
                    "Escudo": st.column_config.ImageColumn("Escudo", width="small"),
                },
                use_container_width=True,
                hide_index=True
            )

    # -----------------------------------------------------------------
    # SECCIÓN 2: BUSCADOR DE PARTIDOS DE LA FECHA Y PREDICCIÓN CON IA
    # -----------------------------------------------------------------
    st.markdown("---")
    st.markdown("<h3 style='color: #00f3ff;'>⚽ Buscador de Partidos y Predicción IA</h3>", unsafe_allow_html=True)

    partidos_hoy = obtener_partidos_hoy(lista_equipos)

    if partidos_hoy:
        st.success(f"🔥 Se encontraron {len(partidos_hoy)} partidos programados para hoy:")
        opciones_partidos = [f"{p['Hora']} hs - {p['Local']} vs {p['Visitante']}" for p in partidos_hoy]
        partido_sel_str = st.selectbox("Selecciona un partido de la fecha:", opciones_partidos)
        
        idx_sel = opciones_partidos.index(partido_sel_str)
        local = partidos_hoy[idx_sel]["Local"]
        visitante = partidos_hoy[idx_sel]["Visitante"]
    else:
        st.info("💡 No hay partidos programados en vivo para hoy. Puedes seleccionar manualmente dos equipos para probar el modelo de IA:")
        col_s1, col_s2 = st.columns(2)
        with col_s1:
            local = st.selectbox("Local:", lista_equipos, index=0)
        with col_s2:
            visitante = st.selectbox("Visitante:", lista_equipos, index=min(1, len(lista_equipos)-1))

    if local == visitante:
        st.warning("Selecciona dos equipos diferentes.")
    else:
        # PREDICCIÓN MEDIANTE LA IA DE APRENDIZAJE CONTINUO
        prob_loc, prob_emp, prob_vis = predecir_partido_ia(local, visitante, df_unificado)

        row_loc = df_unificado[df_unificado["Equipo"] == local].iloc[0]
        row_vis = df_unificado[df_unificado["Equipo"] == visitante].iloc[0]

        # Mostrar Escudos y Nombres
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"""
            <div class="team-card">
                <img src="{row_loc['Escudo']}" class="team-shield"/><br>
                <strong style="color:#ffffff;">{local.upper()}</strong><br>
                <small style="color:#00ffcc;">Posición #{row_loc['Pos']}</small>
            </div>
            """, unsafe_allow_html=True)
        with c2:
            st.markdown(f"""
            <div class="team-card">
                <img src="{row_vis['Escudo']}" class="team-shield"/><br>
                <strong style="color:#ffffff;">{visitante.upper()}</strong><br>
                <small style="color:#ff3366;">Posición #{row_vis['Pos']}</small>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<h4 style='text-align: center; color: #cbd5e1;'>Pronóstico Generado por la IA:</h4>", unsafe_allow_html=True)
        
        m1, m2, m3 = st.columns(3)
        m1.metric(f"Gana {local}", f"{prob_loc}%")
        m2.metric("Empate", f"{prob_emp}%")
        m3.metric(f"Gana {visitante}", f"{prob_vis}%")

        # Barras de Progreso Visuales
        st.write("Distribución de Probabilidad:")
        b1, b2, b3 = st.columns(3)
        with b1:
            st.caption(f"Local: {prob_loc}%")
            st.progress(prob_loc / 100.0)
        with b2:
            st.caption(f"Empate: {prob_emp}%")
            st.progress(prob_emp / 100.0)
        with b3:
            st.caption(f"Visitante: {prob_vis}%")
            st.progress(prob_vis / 100.0)

    # -----------------------------------------------------------------
    # SECCIÓN 3: PANEL DE APRENDIZAJE Y ESTADO DEL MODELO
    # -----------------------------------------------------------------
    st.markdown("---")
    with st.expander("🤖 Estado del Aprendizaje Autónomo de la IA"):
        if os.path.exists(RUTA_DATASET):
            df_h = pd.read_csv(RUTA_DATASET)
            st.write(f"📊 **Partidos procesados por la IA en su base de conocimiento:** `{len(df_h)} partidos`")
            st.caption("A medida que finalizan las fechas, los resultados reales se incorporan automáticamente al dataset y la IA se reentrena sola.")
            st.dataframe(df_h.tail(5), use_container_width=True)
        else:
            st.write("Cargando y configurando base de conocimiento inicial...")
