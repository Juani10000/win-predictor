import streamlit as st
import pandas as pd
import os
from PIL import Image
import unicodedata

# 1. Configuración de página
st.set_page_config(page_title="Tabla Anual - LPF", layout="wide")
st.title("⚽ Tabla Anual - Liga Profesional de Fútbol")
st.markdown("---")

# 2. Cargar el CSV
if not os.path.exists("datos_procesados.csv"):
    st.error("⚠️ No se encontró el archivo 'datos_procesados.csv'.")
else:
    df = pd.read_csv("datos_procesados.csv")
    
    st.subheader("📊 Tabla de Posiciones")
    st.dataframe(df, use_container_width=True, hide_index=True)
    st.markdown("---")

    # 3. Predictor de Enfrentamientos
    st.subheader("🔮 Predictor de Enfrentamientos")
    
    # Limpiar nombres de los equipos por si traen corchetes raros
    df["Equipo"] = df["Equipo"].astype(str).str.replace(r'\[.*?\]|\(.*?\)', '', regex=True).str.strip()
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
            # 4. Lógica de Escudos Locales
            nombre_local_limpio = unicodedata.normalize('NFD', local.lower()).encode('ascii', 'ignore').decode("utf-8")
            nombre_vis_limpio = unicodedata.normalize('NFD', visitante.lower()).encode('ascii', 'ignore').decode("utf-8")
            
            archivos_en_carpeta = os.listdir("escudos") if os.path.exists("escudos") else []
            
            ruta_loc = None
            ruta_vis = None
            
            # Buscar coincidencia de nombres de archivo
            for archivo in archivos_en_carpeta:
                nombre_archivo = archivo.replace(".png", "").replace(".jpg", "").replace("_", " ")
                if nombre_archivo in nombre_local_limpio or nombre_local_limpio in nombre_archivo:
                    ruta_loc = f"escudos/{archivo}"
                if nombre_archivo in nombre_vis_limpio or nombre_vis_limpio in nombre_archivo:
                    ruta_vis = f"escudos/{archivo}"

            # Mostrar Interfaz Visual
            c_loc, c_vs, c_vis = st.columns([2, 1, 2])
            
            with c_loc:
                if ruta_loc:
                    st.image(Image.open(ruta_loc), width=120)
                else:
                    st.info(f"Falta imagen en carpeta")
                st.markdown(f"### {local}")
                
            with c_vs:
                st.markdown("<h1 style='text-align: center; margin-top: 30px;'>VS</h1>", unsafe_allow_html=True)
                
            with c_vis:
                if ruta_vis:
                    st.image(Image.open(ruta_vis), width=120)
                else:
                    st.info(f"Falta imagen en carpeta")
                st.markdown(f"### {visitante}")

            # 5. Cálculo de Probabilidades (El cerebro del predictor)
            row_loc = df[df["Equipo"] == local].iloc[0]
            row_vis = df[df["Equipo"] == visitante].iloc[0]

            pts_loc = float(row_loc.get("Puntos", 0))
            pts_vis = float(row_vis.get("Puntos", 0))
            pj_loc = max(float(row_loc.get("PJ", 1)), 1.0)
            pj_vis = max(float(row_vis.get("PJ", 1)), 1.0)

            # Cálculo de promedio con ventaja deportiva de localía (15% extra)
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
