import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Win Predictor - Fútbol Argentino", page_icon="⚽", layout="centered")

st.title("⚽ Win Predictor - Fútbol Argentino")

# Cargar datos procesados con ttl=60 para que invalide la caché automáticamente cada 1 minuto
@st.cache_data(ttl=60)
def cargar_datos():
    if os.path.exists("datos_procesados.csv"):
        return pd.read_csv("datos_procesados.csv")
    elif os.path.exists("tabla_anual.csv"):
        return pd.read_csv("tabla_anual.csv")
    return None

df = cargar_datos()

if df is None or df.empty:
    st.error("❌ No se encontraron datos actualizados. Ejecutá la actualización de datos primero.")
else:
    # EXTRAER EQUIPOS DINÁMICAMENTE DEL CSV (Adios listas viejas)
    equipos = sorted(df["Equipo"].unique())

    st.subheader("Predicción de Partido")
    
    col1, col2 = st.columns(2)
    with col1:
        local = st.selectbox("Seleccionar Equipo Local", equipos, index=0)
    with col2:
        idx_vis = 1 if len(equipos) > 1 else 0
        visitante = st.selectbox("Seleccionar Equipo Visitante", equipos, index=idx_vis)

    if local == visitante:
        st.warning("⚠️ Seleccioná dos equipos diferentes.")
    else:
        row_local = df[df["Equipo"] == local].iloc[0]
        row_vis = df[df["Equipo"] == visitante].iloc[0]

        # Algoritmo de predicción basado en rendimiento actual
        pts_loc = float(row_local.get("Puntos", 0))
        pj_loc = max(float(row_local.get("PJ", 1)), 1.0)
        rend_loc = pts_loc / (pj_loc * 3.0)

        pts_vis = float(row_vis.get("Puntos", 0))
        pj_vis = max(float(row_vis.get("PJ", 1)), 1.0)
        rend_vis = pts_vis / (pj_vis * 3.0)

        # Factor localía (+10%)
        p_loc = rend_loc + 0.10
        p_vis = rend_vis
        total = p_loc + p_vis + 0.05

        prob_local = round((p_loc / total) * 100, 1)
        prob_vis = round((p_vis / total) * 100, 1)
        prob_empate = round(100.0 - prob_local - prob_vis, 1)

        st.markdown(f"### 📊 Probabilidades: **{local}** vs **{visitante}**")
        
        m1, m2, m3 = st.columns(3)
        m1.metric(f"Gana {local}", f"{prob_local}%")
        m2.metric("Empate", f"{prob_empate}%")
        m3.metric(f"Gana {visitante}", f"{prob_vis}%")

    st.markdown("---")
    st.subheader("📋 Tabla Anual Actualizada")
    
    # Mostrar la tabla ordenada por Puntos
    cols_mostrar = [c for c in ["Equipo", "Puntos", "PJ", "PG", "PE", "PP", "GF", "GC"] if c in df.columns]
    st.dataframe(df[cols_mostrar].sort_values(by="Puntos", ascending=False), use_container_width=True)
