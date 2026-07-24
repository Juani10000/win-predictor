import streamlit as st
import pandas as pd
import os
import re
from PIL import Image

# 1. Configuración de la página
st.set_page_config(page_title="Tabla Anual & Predictor - LPF", layout="wide")
st.title("⚽ Tabla Anual & Predictor - Liga Profesional")
st.markdown("---")

# 2. DIRECTORIO EXACTO (Busca en la carpeta "datos")
DIRECTORIO_APP = os.path.dirname(os.path.abspath(__file__))
# Acá le decimos que la carpeta de las imágenes se llama "datos"
CARPETA_DATOS = os.path.join(DIRECTORIO_APP, "datos") 

# El CSV puede estar suelto o en datos, buscamos en los dos lados
RUTA_CSV = os.path.join(DIRECTORIO_APP, "datos_procesados.csv")
if not os.path.exists(RUTA_CSV):
    RUTA_CSV = os.path.join(CARPETA_DATOS, "datos_procesados.csv")

def encontrar_escudo(nombre_equipo):
    """Busca automáticamente la imagen en la carpeta 'datos'."""
    if not os.path.exists(CARPETA_DATOS):
        return None
        
    # Limpiamos el nombre del equipo (Ej: "Boca Juniors" -> "bocajuniors")
    eq_limpio = re.sub(r'[^a-z0-9]', '', str(nombre_equipo).lower())
    
    try:
        archivos = os.listdir(CARPETA_DATOS)
        for arch in archivos:
            if arch.lower().endswith(('.png', '.jpg', '.jpeg')):
                # Limpiamos el nombre del archivo (Ej: "boca.png" -> "boca")
                arch_limpio = re.sub(r'[^a-z0-9]', '', os.path.splitext(arch)[0].lower())
                
                # Si coinciden (ej: "boca" está dentro de "bocajuniors"), devolvemos la ruta
                if arch_limpio and (arch_limpio in eq_limpio or eq_limpio in arch_limpio):
                    return os.path.join(CARPETA_DATOS, arch)
    except Exception as e:
        pass
    
    return None

# =====================================================================
# 3. CARGA DE DATOS (TABLA DE POSICIONES)
# =====================================================================
if os.path.exists(RUTA_CSV):
    df = pd.read_csv(RUTA_CSV)
    
    if "Equipo" in df.columns:
        df["Equipo"] = df["Equipo"].astype(str).apply(lambda x: re.sub(r'\[.*?\]|\(.*?\)', '', x).strip())

    st.subheader("📊 Tabla de Posiciones")
    st.dataframe(df, use_container_width=True, hide_index=True)
    st.markdown("---")

    # =====================================================================
    # 4. PREDICTOR DE ENFRENTAMIENTOS
    # =====================================================================
    st.subheader("🔮 Predictor de Enfrentamientos")
    
    # Diagnóstico para ver si encuentra la carpeta datos
    if not os.path.exists(CARPETA_DATOS):
        st.warning(f"⚠️ No encuentro la carpeta 'datos' en: {DIRECTORIO_APP}. Asegurate de que se llame exactamente 'datos' en minúsculas.")
    
    lista_equipos = sorted(df["Equipo"].unique()) if "Equipo" in df.columns else []

    if len(lista_equipos) >= 2:
        col1, col2 = st.columns(2)
        with col1:
            local = st.selectbox("Equipo Local", lista_equipos, index=0)
        with col2:
            visitante = st.selectbox("Equipo Visitante", lista_equipos, index=min(1, len(lista_equipos)-1))

        if local == visitante:
            st.warning("⚠️ Seleccioná dos equipos distintos.")
        else:
            # Buscamos las imágenes locales en "datos"
            ruta_loc = encontrar_escudo(local)
            ruta_vis = encontrar_escudo(visitante)

            c_loc, c_vs, c_vis = st.columns([2, 1, 2])
            
            with c_loc:
                if ruta_loc:
                    st.image(Image.open(ruta_loc), width=130)
                else:
                    st.caption(f"🛡️ (Falta {local}.png en datos/)")
                st.markdown(f"### **{local}**")
                
            with c_vs:
                st.markdown("<h1 style='text-align: center; margin-top: 35px;'>VS</h1>", unsafe_allow_html=True)
                
            with c_vis:
                if ruta_vis:
                    st.image(Image.open(ruta_vis), width=130)
                else:
                    st.caption(f"🛡️ (Falta {visitante}.png en datos/)")
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
    st.error("⚠️ No se encontró el archivo 'datos_procesados.csv'. Verificá que esté en la carpeta del programa o adentro de 'datos'.")
