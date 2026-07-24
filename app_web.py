import streamlit as st
import pandas as pd
import unicodedata
import os
import re

# 1. Configuración de la página
st.set_page_config(page_title="Tabla Anual - LPF", layout="wide")
st.title("⚽ Tabla Anual & Predictor - Liga Profesional")
st.markdown("---")

# 2. Rutas del Proyecto
DIRECTORIO_APP = os.path.dirname(os.path.abspath(__file__))
RUTA_CSV = os.path.join(DIRECTORIO_APP, "datos_procesados.csv")
CARPETA_ESCUDOS = os.path.join(DIRECTORIO_APP, "escudos")

# Funciones de Limpieza y Búsqueda
def limpiar_texto(texto):
    """Limpia tildes, corchetes y caracteres especiales para comparar fácil."""
    txt = str(texto).lower()
    txt = re.sub(r'\[.*?\]|\(.*?\)', '', txt) # Quita [ARG], (1), etc.
    txt = re.sub(r'\.(png|jpg|jpeg)', '', txt)
    txt = unicodedata.normalize('NFD', txt).encode('ascii', 'ignore').decode("utf-8")
    return re.sub(r'[^a-z0-9]', '', txt).strip()

def buscar_escudo_local(nombre_equipo):
    """Busca el archivo de imagen en la carpeta 'escudos'."""
    if not os.path.exists(CARPETA_ESCUDOS):
        return None
        
    equipo_limpio = limpiar_texto(nombre_equipo)
    
    try:
        archivos = os.listdir(CARPETA_ESCUDOS)
    except Exception:
        return None

    # Busca coincidencia de nombre (ej: "boca" en "boca.png" o "boca_juniors.png")
    for archivo in archivos:
        if archivo.lower().endswith(('.png', '.jpg', '.jpeg')):
            archivo_limpio = limpiar_texto(archivo)
            if archivo_limpio in equipo_limpio or equipo_limpio in archivo_limpio:
                return os.path.join(CARPETA_ESCUDOS, archivo)
    return None

# =====================================================================
# 3. Carga de Datos y Tabla de Posiciones
# =====================================================================
if not os.path.exists(RUTA_CSV):
    st.error(f"⚠️ No se encontró 'datos_procesados.csv' en: {DIRECTORIO_APP}")
else:
    df = pd.read_csv(RUTA_CSV)
    df["Equipo"] = df["Equipo"].astype(str).apply(lambda x: re.sub(r'\[.*?\]|\(.*?\)', '', x).strip())

    st.subheader("📊 Tabla de Posiciones")
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True
    )
    st.markdown("---")

    # =====================================================================
    # 4. Predictor de Enfrentamientos (Win Predictor)
    # =====================================================================
    st.subheader("🔮 Predictor de Enfrentamientos")
    
    # Diagnóstico amigable de la carpeta
    if not os.path.exists(CARPETA_ESCUDOS):
        st.info("💡 Consejo: Creá la carpeta 'escudos' al lado de app_web.py y guardá ahí las fotos para ver los logos.")
    
    lista_equipos = sorted(df["Equipo"].unique())

    if len(lista_equipos) >= 2:
        col1, col2 = st.columns(2)
        with col1:
            local = st.selectbox("Equipo Local", lista_equipos, index=0)
        with col2:
            visitante = st.selectbox("Equipo Visitante", lista_equipos, index=min(1, len(lista_equipos)-1))

        if local == visitante:
            st.warning("Seleccioná dos equipos distintos.")
        else:
            # Buscar escudos para el local y el visitante
            ruta_loc = buscar_escudo_local(local)
            ruta_vis = buscar_escudo_local(visitante)

            c_loc, c_vs, c_vis = st.columns([2, 1, 2])
            
            with c_loc:
                if ruta_loc and os.path.exists(ruta_loc):
                    st.image(ruta_loc, width=130)
                else:
                    st.caption("🛡️ (Sin escudo)")
                st.markdown(f"### **{local}**")
                
            with c_vs:
                st.markdown("<h1 style='text-align: center; margin-top: 30px;'>VS</h1>", unsafe_allow_html=True)
                
            with c_vis:
                if ruta_vis and os.path.exists(ruta_vis):
                    st.image(ruta_vis, width=130)
                else:
                    st.caption("🛡️ (Sin escudo)")
                st.markdown(f"### **{visitante}**")

            # Cálculo de Probabilidades
            row_loc = df[df["Equipo"] == local].iloc[0]
            row_vis = df[df["Equipo"] == visitante].iloc[0]

            pts_loc = float(row_loc.get("Puntos", 0)) if "Puntos" in df.columns else 0.0
            pts_vis = float(row_vis.get("Puntos", 0)) if "Puntos" in df.columns else 0.0
            pj_loc = max(float(row_loc.get("PJ", 1)), 1.0) if "PJ" in df.columns else 1.0
            pj_vis = max(float(row_vis.get("PJ", 1)), 1.0) if "PJ" in df.columns else 1.0

            # Promedio de puntos + ventaja de localía (+15%)
            prom_loc = (pts_loc / pj_loc) * 1.15
            prom_vis = pts_vis / pj_vis
            total = prom_loc + prom_vis

            if total > 0:
                prob_loc = (prom_loc / total) * 100
                prob_vis = (prom_vis / total) * 100
            else:
                prob_loc, prob_vis = 50.0, 50.0

            st.markdown("#### **Probabilidades de Victoria**")
            p1, p2 = st.columns(2)
            p1.metric(f"{local} (Local)", f"{prob_loc:.1f}%")
            p2.metric(f"{visitante} (Visitante)", f"{prob_vis:.1f}%")
            st.progress(int(prob_loc))
