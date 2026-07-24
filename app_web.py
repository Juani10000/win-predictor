import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Win Predictor - Fútbol Argentino", page_icon="⚽", layout="centered")

st.title("⚽ Win Predictor - Fútbol Argentino 2026")

@st.cache_data(ttl=60)
def cargar_tabla(archivo):
    if os.path.exists(archivo):
        return pd.read_csv(archivo)
    return pd.DataFrame()

# Cargar las 3 tablas
df_anual = cargar_tabla("tabla_anual.csv")
df_apertura = cargar_tabla("tabla_apertura.csv")
df_clausura = cargar_tabla("tabla_clausura.csv")

if df_anual.empty and df_clausura.empty:
    st.error("❌ No se encontraron datos. Ejecutá la actualización en GitHub.")
else:
    # Elegir qué torneo usar para la interfaz
    st.markdown("### 🏆 Seleccioná el Torneo:")
    tab1, tab2, tab3 = st.tabs(["📊 Tabla Anual", "🏆 Torneo Clausura", "🏆 Torneo Apertura"])
    
    # Determinar qué dataframe usar según la pestaña seleccionada
    df_actual = df_anual # por defecto
    
    with tab1:
        st.info("Mostrando datos de la Tabla Anual")
        df_actual = df_anual
        st.dataframe(df_actual[["Equipo", "Puntos", "PJ", "PG", "PE", "PP", "GF", "GC"]], use_container_width=True)
        
    with tab2:
        if not df_clausura.empty:
            st.info("Mostrando datos del Torneo Clausura")
            st.dataframe(df_clausura[["Equipo", "Puntos", "PJ", "PG", "PE", "PP", "GF", "GC"]], use_container_width=True)
        else:
            st.warning("Datos del Clausura no disponibles.")
            
    with tab3:
        if not df_apertura.empty:
            st.info("Mostrando datos del Torneo Apertura")
            st.dataframe(df_apertura[["Equipo", "Puntos", "PJ", "PG", "PE", "PP", "GF", "GC"]], use_container_width=True)
        else:
            st.warning("Datos del Apertura no disponibles.")

    st.markdown("---")
    
    # EL PREDICTOR TOMA SIEMPRE LA TABLA ANUAL PARA SER MÁS PRECISO (o podés cambiar df_anual por df_actual)
    st.subheader("🔮 Predicción de Partido (Basado en Tabla Anual)")
    
    lista_equipos = sorted(df_anual["Equipo"].unique())
    
    col1, col2 = st.columns(2)
    with col1:
        local = st.selectbox("Equipo Local", lista_equipos, index=0)
    with col2:
        idx_vis = 1 if len(lista_equipos) > 1 else 0
        visitante = st.selectbox("Equipo Visitante", lista_equipos, index=idx_vis)

    if local == visitante:
        st.warning("⚠️ Elegí dos equipos distintos.")
    else:
        row_loc = df_anual[df_anual["Equipo"] == local].iloc[0]
        row_vis = df_anual[df_anual["Equipo"] == visitante].iloc[0]

        pts_loc = float(row_loc.get("Puntos", 0))
        pj_loc = max(float(row_loc.get("PJ", 1)), 1.0)
        rend_loc = pts_loc / (pj_loc * 3.0)

        pts_vis = float(row_vis.get("Puntos", 0))
        pj_vis = max(float(row_vis.get("PJ", 1)), 1.0)
        rend_vis = pts_vis / (pj_vis * 3.0)

        p_loc = rend_loc + 0.10  # Bonificación por localía
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
