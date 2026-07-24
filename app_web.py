import streamlit as st
import pandas as pd
import unicodedata
import os
import re
import base64

# 1. Configuración de página
st.set_page_config(page_title="Tabla Anual - LPF", layout="wide")
st.title("⚽ Tabla Anual - Liga Profesional")

# =====================================================================
# 🛠️ MODO DIAGNÓSTICO - ACÁ VAMOS A VER POR QUÉ FALLA
# =====================================================================
DIRECTORIO_ACTUAL = os.getcwd()
CARPETA_ESCUDOS = os.path.join(DIRECTORIO_ACTUAL, "escudos")

with st.expander("🛠️ MODO DIAGNÓSTICO (Abrí acá para ver qué pasa con las imágenes)", expanded=True):
    st.markdown(f"**Python está ejecutando desde:** `{DIRECTORIO_ACTUAL}`")
    st.markdown(f"**Buscando la carpeta escudos en:** `{CARPETA_ESCUDOS}`")
    
    if os.path.exists(CARPETA_ESCUDOS):
        archivos = os.listdir(CARPETA_ESCUDOS)
        st.success(f"✅ ¡La carpeta 'escudos' existe!")
        st.write(f"📂 Archivos detectados adentro: {archivos}")
        if not archivos:
            st.warning("⚠️ La carpeta está vacía.")
    else:
        st.error("❌ LA CARPETA 'escudos' NO SE ENCUENTRA EN ESA RUTA.")
        st.info("👉 Movela para que coincida con la ruta que figura arriba o revisá cómo está escrita (todo en minúsculas).")
st.markdown("---")
# =====================================================================

def normalizar(texto):
    txt = str(texto)
    txt = re.sub(r'\[.*?\]|\(.*?\)', '', txt).strip()
    txt = unicodedata.normalize('NFD', txt).encode('ascii', 'ignore').decode("utf-8").lower()
    return re.sub(r'[^a-z0-9]', '', txt)

def obtener_ruta_escudo(nombre_equipo):
    if not os.path.exists(CARPETA_ESCUDOS):
        return None
        
    nombre_norm = normalizar(nombre_equipo)
    
    for archivo in os.listdir(CARPETA_ESCUDOS):
        nombre_arch, _ = os.path.splitext(archivo)
        arch_norm = normalizar(nombre_arch)
        if arch_norm and (arch_norm in nombre_norm or nombre_norm in arch_norm):
            return os.path.join(CARPETA_ESCUDOS, archivo)
            
    return None

def imagen_a_base64(ruta_imagen):
    if ruta_imagen and os.path.exists(ruta_imagen):
        try:
            with open(ruta_imagen, "rb") as image_file:
                encoded_string = base64.b64encode(image_file.read()).decode()
            ext = os.path.splitext(ruta_imagen)[1].lower().replace(".", "")
            if ext == "jpg": ext = "jpeg"
            return f"data:image/{ext};base64,{encoded_string}"
        except Exception:
            return None
    return None

# 2. Carga de datos y visualización
ruta_csv = os.path.join(DIRECTORIO_ACTUAL, "datos_procesados.csv")

if not os.path.exists(ruta_csv):
    st.error(f"⚠️ No se encontró '{ruta_csv}'.")
else:
    df = pd.read_csv(ruta_csv)
    
    df["Equipo"] = df["Equipo"].astype(str).apply(lambda x: re.sub(r'\[.*?\]|\(.*?\)', '', x).strip())
    
    rutas = df["Equipo"].apply(obtener_ruta_escudo)
    df["Escudo"] = rutas.apply(imagen_a_base64)
    
    cols = df.columns.tolist()
    if "Escudo" in cols:
        cols.insert(0, cols.pop(cols.index("Escudo")))
        df = df[cols]

    st.subheader("📊 Tabla de Posiciones")
    
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Escudo": st.column_config.ImageColumn("🛡️", help="Escudo")
        }
    )
    st.markdown("---")

    # 3. Predictor
    st.subheader("🔮 Predictor de Enfrentamientos")
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
            ruta_loc = obtener_ruta_escudo(local)
            ruta_vis = obtener_ruta_escudo(visitante)

            c_loc, c_vs, c_vis = st.columns([2, 1, 2])
            
            with c_loc:
                if ruta_loc and os.path.exists(ruta_loc):
                    st.image(ruta_loc, width=120)
                else:
                    st.error("Falta imagen")
                st.markdown(f"### **{local}**")
                
            with c_vs:
                st.markdown("<h1 style='text-align: center; margin-top: 30px;'>VS</h1>", unsafe_allow_html=True)
                
            with c_vis:
                if ruta_vis and os.path.exists(ruta_vis):
                    st.image(ruta_vis, width=120)
                else:
                    st.error("Falta imagen")
                st.markdown(f"### **{visitante}**")

            # Matemáticas
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

            st.markdown("#### **Probabilidades**")
            p1, p2 = st.columns(2)
            p1.metric(f"{local} (Local)", f"{prob_loc:.1f}%")
            p2.metric(f"{visitante} (Visitante)", f"{prob_vis:.1f}%")
            st.progress(int(prob_loc))
