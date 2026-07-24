import streamlit as st
import pandas as pd
import os
import re

# =====================================================================
# 1. CONFIGURACIÓN DE PÁGINA Y ENCABEZADO
# =====================================================================
st.set_page_config(page_title="Win Predictor - LPF Argentina", layout="wide")

# Logo oficial de la LPF (vía Wikimedia URL oficial)
URL_LOGO_LPF = "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d4/Logo_de_la_Liga_Profesional_de_F%C3%BAtbol.png/600px-Logo_de_la_Liga_Profesional_de_F%C3%BAtbol.png"

col_logo, col_titulo = st.columns([1, 6])
with col_logo:
    st.image(URL_LOGO_LPF, width=95)
with col_titulo:
    st.title("⚽ Win Predictor - Liga Profesional")
    st.markdown("**Tabla Anual & Predictor de Partidos (Local / Empate / Visitante)**")

st.markdown("---")

# =====================================================================
# 2. CARGA DE DATOS DESDE EL CSV
# =====================================================================
DIRECTORIO_APP = os.path.dirname(os.path.abspath(__file__))
RUTA_CSV = os.path.join(DIRECTORIO_APP, "datos_procesados.csv")

if not os.path.exists(RUTA_CSV):
    # Revisa si el CSV está adentro de la carpeta 'datos'
    RUTA_CSV = os.path.join(DIRECTORIO_APP, "datos", "datos_procesados.csv")

if os.path.exists(RUTA_CSV):
    df = pd.read_csv(RUTA_CSV)
    
    if "Equipo" in df.columns:
        df["Equipo"] = df["Equipo"].astype(str).apply(lambda x: re.sub(r'\[.*?\]|\(.*?\)', '', x).strip())

    # -----------------------------------------------------------------
    # 3. TABLA DE POSICIONES
    # -----------------------------------------------------------------
    st.subheader("📊 Tabla de Posiciones")
    st.dataframe(df, use_container_width=True, hide_index=True)
    st.markdown("---")

    # -----------------------------------------------------------------
    # 4. PREDICTOR DE ENFRENTAMIENTOS (LOCAL / EMPATE / VISITANTE)
    # -----------------------------------------------------------------
    st.subheader("🔮 Predictor de Enfrentamientos")
    
    lista_equipos = sorted(df["Equipo"].unique()) if "Equipo" in df.columns else []

    if len(lista_equipos) >= 2:
        col1, col2 = st.columns(2)
        with col1:
            local = st.selectbox("🏠 Equipo Local", lista_equipos, index=0)
        with col2:
            visitante = st.selectbox("✈️ Equipo Visitante", lista_equipos, index=min(1, len(lista_equipos)-1))

        if local == visitante:
            st.warning("⚠️ Seleccioná dos equipos distintos.")
        else:
            # Datos del equipo local y visitante
            row_loc = df[df["Equipo"] == local].iloc[0]
            row_vis = df[df["Equipo"] == visitante].iloc[0]

            pts_loc = float(row_loc.get("Puntos", 0)) if "Puntos" in df.columns else 0.0
            pts_vis = float(row_vis.get("Puntos", 0)) if "Puntos" in df.columns else 0.0
            pj_loc = max(float(row_loc.get("PJ", 1)), 1.0) if "PJ" in df.columns else 1.0
            pj_vis = max(float(row_vis.get("PJ", 1)), 1.0) if "PJ" in df.columns else 1.0

            # Promedio de puntos por partido (+12% extra por localía)
            prom_loc = (pts_loc / pj_loc) * 1.12
            prom_vis = (pts_vis / pj_vis)

            # Diferencia de nivel entre equipos
            diferencia = abs(prom_loc - prom_vis)

            # Cuanto más parejos, mayor probabilidad de empate (rango típico en fútbol argentino ~22% a 32%)
            prob_empate = max(18.0, min(33.0, 29.0 - (diferencia * 7.5)))

            # El porcentaje restante se reparte entre victoria local y visitante
            resto = 100.0 - prob_empate
            total_prom = prom_loc + prom_vis

            if total_prom > 0:
                prob_loc = (prom_loc / total_prom) * resto
                prob_vis = (prom_vis / total_prom) * resto
            else:
                prob_loc = resto / 2
                prob_vis = resto / 2

            # Muestra de Enfrentamiento
            st.markdown(f"### **{local}** &nbsp; vs &nbsp; **{visitante}**")
            st.markdown("#### **Probabilidades del Partido**")

            # Métrica en 3 columnas
            m1, m2, m3 = st.columns(3)
            m1.metric(f"Victoria {local}", f"{prob_loc:.1f}%")
            m2.metric("Empate", f"{prob_empate:.1f}%")
            m3.metric(f"Victoria {visitante}", f"{prob_vis:.1f}%")

            # Barra visual acumulada
            st.markdown("**Distribución visual:**")
            col_bar1, col_bar2, col_bar3 = st.columns([int(prob_loc), int(prob_empate), int(prob_vis)])
            with col_bar1:
                st.info(f"Local: {prob_loc:.1f}%")
            with col_bar2:
                st.warning(f"Empate: {prob_empate:.1f}%")
            with col_bar3:
                st.error(f"Visitante: {prob_vis:.1f}%")

else:
    st.error("⚠️ No se encontró el archivo 'datos_procesados.csv'. Verificá que esté guardado en el mismo directorio.")
