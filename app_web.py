import streamlit as st
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier

# --- 1. CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Win Predictor", page_icon="⚽")
st.title("⚽ Win Predictor - Liga Argentina")
st.write("Seleccioná los equipos para ver el pronóstico de la Inteligencia Artificial.")

# --- 2. CARGAR DATOS Y ENTRENAR EL MODELO (Oculto al usuario) ---
@st.cache_data # Esto hace que la página cargue rápido
def preparar_modelo():
    df = pd.read_csv("datos/datos_procesados.csv")
    
    features = ["local_cod", "visitante_cod", "local_gf_5", "local_gc_5", "local_pts_5", "visita_gf_5", "visita_gc_5", "visita_pts_5"]
    X = df[features]
    y = df["resultado_num"]
    
    modelo = RandomForestClassifier(n_estimators=100, max_depth=5, random_state=42)
    modelo.fit(X, y)
    
    equipos_unicos = sorted(pd.concat([df["Local"], df["Visitante"]]).unique())
    mapa_equipos = {equipo: i for i, equipo in enumerate(equipos_unicos)}
    
    return df, modelo, equipos_unicos, mapa_equipos

df, modelo, equipos_unicos, mapa_equipos = preparar_modelo()

# Función para la racha
def obtener_racha_actual(equipo, df):
    partidos = df[(df["Local"] == equipo) | (df["Visitante"] == equipo)].tail(5)
    if len(partidos) == 0:
        return 1.0, 1.0, 1.0
    gf, gc, pts = [], [], []
    for _, fila in partidos.iterrows():
        es_local = fila["Local"] == equipo
        g_fav = fila["Goles_Local"] if es_local else fila["Goles_Visitante"]
        g_con = fila["Goles_Visitante"] if es_local else fila["Goles_Local"]
        res = fila["Resultado"]
        
        if (es_local and res == "L") or (not es_local and res == "V"): p = 3
        elif res == "E": p = 1
        else: p = 0
            
        gf.append(g_fav)
        gc.append(g_con)
        pts.append(p)
    return np.mean(gf), np.mean(gc), np.mean(pts)

# --- 3. INTERFAZ DE USUARIO (Lo que se ve en la web) ---
col1, col2 = st.columns(2)

with col1:
    equipo_local = st.selectbox("🏟️ Equipo Local", equipos_unicos, index=equipos_unicos.index("Boca Juniors") if "Boca Juniors" in equipos_unicos else 0)

with col2:
    equipo_visitante = st.selectbox("✈️ Equipo Visitante", equipos_unicos, index=equipos_unicos.index("River Plate") if "River Plate" in equipos_unicos else 1)

if st.button("🔮 Predecir Partido"):
    if equipo_local == equipo_visitante:
        st.warning("⚠️ ¡Tenés que elegir dos equipos distintos!")
    else:
        # Calcular rachas
        l_gf, l_gc, l_pts = obtener_racha_actual(equipo_local, df)
        v_gf, v_gc, v_pts = obtener_racha_actual(equipo_visitante, df)
        
        # Predecir
        partido_nuevo = pd.DataFrame([{
            "local_cod": mapa_equipos[equipo_local], "visitante_cod": mapa_equipos[equipo_visitante],
            "local_gf_5": l_gf, "local_gc_5": l_gc, "local_pts_5": l_pts,
            "visita_gf_5": v_gf, "visita_gc_5": v_gc, "visita_pts_5": v_pts
        }])
        
        prediccion = modelo.predict(partido_nuevo)[0]
        probs = modelo.predict_proba(partido_nuevo)[0]
        clases = list(modelo.classes_)
        
        prob_local = probs[clases.index(1)] * 100 if 1 in clases else 0
        prob_empate = probs[clases.index(0)] * 100 if 0 in clases else 0
        prob_visita = probs[clases.index(2)] * 100 if 2 in clases else 0

        # Mostrar resultados visuales
        st.divider()
        st.subheader("📊 Resultados del Pronóstico")
        
        res_txt = {1: f"🏆 Gana {equipo_local}", 0: "🤝 Empate", 2: f"🏆 Gana {equipo_visitante}"}
        st.success(f"**Resultado más probable:** {res_txt[prediccion]}")
        
        # Barras de progreso para las probabilidades
        st.write(f"**{equipo_local} (Local):** {prob_local:.1f}%")
        st.progress(int(prob_local))
        
        st.write(f"**Empate:** {prob_empate:.1f}%")
        st.progress(int(prob_empate))
        
        st.write(f"**{equipo_visitante} (Visitante):** {prob_visita:.1f}%")
        st.progress(int(prob_visita))