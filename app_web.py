import streamlit as st
import pandas as pd
import unicodedata
import os
import re
from PIL import Image

# 1. Configuración de página
st.set_page_config(page_title="Tabla Anual - LPF", layout="wide")
st.title("⚽ Tabla Anual - Liga Profesional")
st.markdown("---")

# 2. Función para normalizar nombres y buscar archivo local
def normalizar(texto):
    """Limpia tildes, caracteres especiales y pasa a minúsculas."""
    txt = str(texto)
    txt = re.sub(r'\[.*?\]|\(.*?\)', '', txt).strip()
    txt = unicodedata.normalize('NFD', txt).encode('ascii', 'ignore').decode("utf-8").lower()
    return re.sub(r'[^a-z0-9]', '', txt)

def obtener_ruta_escudo(nombre_equipo):
    carpeta = "escudos"
    if not os.path.exists(carpeta):
        return None
        
    nombre_norm = normalizar(nombre_equipo)
    
    # Busca coincidencia en la carpeta escudos
    for archivo in os.listdir(carpeta):
        nombre_arch, _ = os.path.splitext(archivo)
        arch_norm = normalizar(nombre_arch)
        
        # Si la palabra clave (ej: 'boca') está contenida en el nombre del equipo
        if arch_norm and (arch_norm in nombre_norm or nombre_norm in arch_norm):
            return os.path.join(carpeta, archivo)
            
    return None

# 3. Carga de datos y visualización de Tabla
if not os.path.exists("datos_procesados.csv"):
    st.error("⚠️ No se encontró 'datos_procesados.csv'. Verificá que el archivo esté en la misma carpeta.")
else:
    df = pd.read_csv("datos_procesados.csv")
    
    # Limpieza de nombres de equipos
    df["Equipo"] = df["Equipo"].astype(str).apply(lambda x: re.sub(r'\[.*?\]|\(.*?\)', '', x).strip())
    
    # Asignar ruta de imagen local
    df["Escudo"] = df["Equipo"].apply(obtener_ruta_escudo)
    
    # Reordenar columnas para poner Escudo al principio
    cols = df.columns.tolist()
    if "Escudo" in cols:
        cols.insert(0, cols.pop(cols.index("Escudo")))
        df = df[cols]

    st.subheader("📊 Tabla de Posiciones")
    
    # Muestra las imágenes locales dentro de la tabla
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Escudo": st.column_config.ImageColumn("🛡️", help="Escudo del equipo")
        }
    )
    st.markdown("---")

    # 4. Predictor de Enfrentamientos
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
                    st.image(Image.open(ruta_loc), width=120)
                else:
                    st.caption("🛡️ (Agregar imagen a carpeta escudos)")
                st.markdown(f"### **{local}**")
                
            with c_vs:
                st.markdown("<h1 style='text-align: center; margin-top: 30px;'>VS</h1>", unsafe_allow_html=True)
                
            with c_vis:
                if ruta_vis and os.path.exists(ruta_vis):
                    st.image(Image.open(ruta_vis), width=120)
                else:
                    st.caption("🛡️ (Agregar imagen a carpeta escudos)")
                st.markdown(f"### **{visitante}**")

            # Cálculo de Probabilidades
            row_loc = df[df["Equipo"] == local].iloc[0]
            row_vis = df[df["Equipo"] == visitante].iloc[0]

            pts_loc = float(row_loc.get("Puntos", 0)) if "Puntos" in df.columns else 0.0
            pts_vis = float(row_vis.get("Puntos", 0)) if "Puntos" in df.columns else 0.0
            pj_loc = max(float(row_loc.get("PJ", 1)), 1.0) if "PJ" in df.columns else 1.0
            pj_vis = max(float(row_vis.get("PJ", 1)), 1.0) if "PJ" in df.columns else 1.0

            # 15% de ventaja por localía
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
