import streamlit as st
import pandas as pd
import unicodedata
import os
import re
from PIL import Image

# 1. Configuración de la página
st.set_page_config(page_title="Tabla Anual & Predictor - LPF", layout="wide")
st.title("⚽ Tabla Anual & Predictor - Liga Profesional")
st.markdown("---")

# 2. LOCALIZACIÓN AUTOMÁTICA DE ARCHIVOS Y CARPETAS
DIRECTORIO_APP = os.path.dirname(os.path.abspath(__file__))

# Busca el CSV donde sea que esté guardado
RUTA_CSV = os.path.join(DIRECTORIO_APP, "datos_procesados.csv")
if not os.path.exists(RUTA_CSV):
    RUTA_CSV = os.path.join(os.getcwd(), "datos_procesados.csv")

# Busca la carpeta de escudos (revisa si está en la carpeta actual o en /escudos)
CARPETAS_POSIBLES = [
    os.path.join(DIRECTORIO_APP, "escudos"),
    DIRECTORIO_APP,
    os.path.join(os.getcwd(), "escudos"),
    os.getcwd()
]

CARPETA_ESCUDOS = DIRECTORIO_APP
for carpeta in CARPETAS_POSIBLES:
    if os.path.exists(carpeta):
        archivos_img = [f for f in os.listdir(carpeta) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        if len(archivos_img) > 0:
            CARPETA_ESCUDOS = carpeta
            break

# Opción para cambiar la ruta manualmente desde la barra lateral si fuera necesario
st.sidebar.header("⚙️ Configuración")
ruta_custom = st.sidebar.text_input("Carpeta de imágenes:", value=CARPETA_ESCUDOS)
if ruta_custom and os.path.exists(ruta_custom.strip()):
    CARPETA_ESCUDOS = ruta_custom.strip()

# 3. LÓGICA DE COINCIDENCIA (boca.png -> Boca Juniors)
def normalizar(texto):
    """Quita corchetes, paréntesis, tildes y símbolos para comparar fácil."""
    txt = str(texto).lower()
    txt = re.sub(r'\[.*?\]|\(.*?\)', '', txt)
    txt = unicodedata.normalize('NFD', txt).encode('ascii', 'ignore').decode("utf-8")
    return re.sub(r'[^a-z0-9]', '', txt).strip()

def obtener_imagen_equipo(nombre_equipo):
    if not os.path.exists(CARPETA_ESCUDOS):
        return None
    
    equipo_norm = normalizar(nombre_equipo)
    if not equipo_norm:
        return None

    try:
        archivos = [f for f in os.listdir(CARPETA_ESCUDOS) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    except Exception:
        return None

    # Busca si "boca" está dentro de "bocajuniors" o viceversa
    for archivo in archivos:
        nombre_sin_ext = os.path.splitext(archivo)[0]
        archivo_norm = normalizar(nombre_sin_ext)
        if archivo_norm and (archivo_norm in equipo_norm or equipo_norm in archivo_norm):
            return os.path.join(CARPETA_ESCUDOS, archivo)
            
    return None

# =====================================================================
# 4. TABLA DE POSICIONES
# =====================================================================
if os.path.exists(RUTA_CSV):
    df = pd.read_csv(RUTA_CSV)
    
    if "Equipo" in df.columns:
        df["Equipo"] = df["Equipo"].astype(str).apply(lambda x: re.sub(r'\[.*?\]|\(.*?\)', '', x).strip())

    st.subheader("📊 Tabla de Posiciones")
    st.dataframe(df, use_container_width=True, hide_index=True)
    st.markdown("---")

    # =====================================================================
    # 5. PREDICTOR DE ENFRENTAMIENTOS
    # =====================================================================
    st.subheader("🔮 Predictor de Enfrentamientos")
    
    lista_equipos = sorted(df["Equipo"].unique()) if "Equipo" in df.columns else []

    if len(lista_equipos) >= 2:
        col1, col2 = st.columns(2)
        with col1:
            local = st.selectbox("Equipo Local", lista_equipos, index=0)
        with col2:
            visitante = st.selectbox("Equipo Visitante", lista_equipos, index=min(1, len(lista_equipos)-1))

        if local == visitante:
            st.warning("Seleccioná dos equipos distintos.")
        else:
            ruta_loc = obtener_imagen_equipo(local)
            ruta_vis = obtener_imagen_equipo(visitante)

            c_loc, c_vs, c_vis = st.columns([2, 1, 2])
            
            with c_loc:
                if ruta_loc and os.path.exists(ruta_loc):
                    st.image(Image.open(ruta_loc), width=120)
                else:
                    st.caption("🛡️ (Sin escudo)")
                st.markdown(f"### **{local}**")
                
            with c_vs:
                st.markdown("<h1 style='text-align: center; margin-top: 20px;'>VS</h1>", unsafe_allow_html=True)
                
            with c_vis:
                if ruta_vis and os.path.exists(ruta_vis):
                    st.image(Image.open(ruta_vis), width=120)
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
else:
    st.error("⚠️ No se encontró el archivo 'datos_procesados.csv'. Verificá que esté guardado en la misma carpeta del proyecto.")
