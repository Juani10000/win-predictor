import streamlit as st
import pandas as pd
import os
from PIL import Image

# 1. Configuración de la página
st.set_page_config(page_title="Tabla Anual - LPF", layout="wide")
st.title("⚽ Tabla Anual & Predictor - Liga Profesional")
st.markdown("---")

# 2. RUTA DE LA CARPETA
# Escribí la ruta de tu carpeta acá, asegurate de usar \\ en lugar de \
# Ejemplo: "C:\\Users\\Usuario\\Desktop\\escudos"
CARPETA_ESCUDOS = r"C:\TU\RUTA\ACA" 
# Podés reemplazar la línea de arriba por la ruta que copiaste, dejando la 'r' al principio.

# 3. EL DICCIONARIO INFALIBLE
# Acá conectamos el nombre exacto del equipo (como aparece en el CSV) con el archivo.
# Si tu foto se llama distinto, solo cambiá el lado derecho (ej: "boca_escudo.png")
MAPEO_ARCHIVOS = {
    "Boca Juniors": "boca.png",
    "River Plate": "river.png",
    "Racing Club": "racing.png",
    "Independiente": "independiente.png",
    "San Lorenzo": "sanlorenzo.png",
    "Huracan": "huracan.png",
    "Estudiantes (LP)": "estudiantes.png",
    "Gimnasia (LP)": "gimnasia.png",
    "Rosario Central": "rosario.png",
    "Newells": "newells.png",
    "Talleres (C)": "talleres.png",
    "Belgrano": "belgrano.png",
    "Instituto": "instituto.png",
    "Argentinos Juniors": "argentinos.png",
    "Velez": "velez.png",
    "Lanus": "lanus.png",
    "Banfield": "banfield.png",
    "Defensa y Justicia": "defensa.png",
    "Platense": "platense.png",
    "Tigre": "tigre.png",
    "Union": "union.png",
    "Godoy Cruz": "godoycruz.png",
    "Atl. Tucuman": "tucuman.png",
    "Central Cordoba": "centralcordoba.png",
    "Sarmiento (J)": "sarmiento.png",
    "Barracas Central": "barracas.png",
    "Ind. Rivadavia": "independienterivadavia.png",
    "Dep. Riestra": "riestra.png"
}

def obtener_ruta_imagen(nombre_equipo):
    # Buscamos si el equipo tiene un archivo asignado en el diccionario
    for clave, nombre_archivo in MAPEO_ARCHIVOS.items():
        if clave.lower() in nombre_equipo.lower():
            ruta_completa = os.path.join(CARPETA_ESCUDOS, nombre_archivo)
            if os.path.exists(ruta_completa):
                return ruta_completa
    return None

# =====================================================================
# 4. Predictor de Enfrentamientos
# =====================================================================
DIRECTORIO_APP = os.path.dirname(os.path.abspath(__file__))
RUTA_CSV = os.path.join(DIRECTORIO_APP, "datos_procesados.csv")

if not os.path.exists(RUTA_CSV):
    st.error(f"⚠️ No se encontró 'datos_procesados.csv'.")
else:
    df = pd.read_csv(RUTA_CSV)
    
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
            ruta_loc = obtener_ruta_imagen(local)
            ruta_vis = obtener_ruta_imagen(visitante)

            c_loc, c_vs, c_vis = st.columns([2, 1, 2])
            
            with c_loc:
                if ruta_loc:
                    st.image(Image.open(ruta_loc), width=130)
                else:
                    st.caption("🛡️ Revisá el nombre en el diccionario")
                st.markdown(f"### **{local}**")
                
            with c_vs:
                st.markdown("<h1 style='text-align: center; margin-top: 30px;'>VS</h1>", unsafe_allow_html=True)
                
            with c_vis:
                if ruta_vis:
                    st.image(Image.open(ruta_vis), width=130)
                else:
                    st.caption("🛡️ Revisá el nombre en el diccionario")
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

            st.markdown("#### **Probabilidades de Victoria**")
            p1, p2 = st.columns(2)
            p1.metric(f"{local} (Local)", f"{prob_loc:.1f}%")
            p2.metric(f"{visitante} (Visitante)", f"{prob_vis:.1f}%")
            st.progress(int(prob_loc))
