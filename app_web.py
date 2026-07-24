import streamlit as st
import pandas as pd
import os
import re
import unicodedata

# 1. Configuración de la página
st.set_page_config(page_title="Tabla Anual & Predictor - LPF", layout="wide")
st.title("⚽ Tabla Anual & Predictor - Liga Profesional")
st.markdown("---")

# 2. DICCIONARIO DE ESCUDOS (URLs directas de Internet)
ESCUDOS_WEB = {
    "boca": "https://upload.wikimedia.org/wikipedia/commons/1/1b/Escudo_del_Club_Atl%C3%A9tico_Boca_Juniors.png",
    "river": "https://upload.wikimedia.org/wikipedia/commons/a/ac/Escudo_del_C_A_River_Plate.png",
    "racing": "https://upload.wikimedia.org/wikipedia/commons/5/56/Escudo_de_Racing_Club_%282014%29.png",
    "independiente": "https://upload.wikimedia.org/wikipedia/commons/d/db/Escudo_del_C._A._Independiente.png",
    "san lorenzo": "https://upload.wikimedia.org/wikipedia/commons/7/77/Escudo_del_Club_Atl%C3%A9tico_San_Lorenzo_de_Almagro.png",
    "huracan": "https://upload.wikimedia.org/wikipedia/commons/a/a2/Escudo_de_Hurac%C3%A1n.png",
    "estudiantes": "https://upload.wikimedia.org/wikipedia/commons/a/a1/Escudo_de_Estudiantes_de_La_Plata.png",
    "gimnasia": "https://upload.wikimedia.org/wikipedia/commons/0/04/Escudo_Gimnasia_y_Esgrima_La_Plata.png",
    "rosario central": "https://upload.wikimedia.org/wikipedia/commons/b/b5/Escudo_del_Club_Atl%C3%A9tico_Rosario_Central.png",
    "newell": "https://upload.wikimedia.org/wikipedia/commons/a/a8/Escudo_Newell%27s_Old_Boys.png",
    "talleres": "https://upload.wikimedia.org/wikipedia/commons/c/c5/Escudo_de_Talleres.png",
    "belgrano": "https://upload.wikimedia.org/wikipedia/commons/2/23/Escudo_del_Club_Atl%C3%A9tico_Belgrano.png",
    "instituto": "https://upload.wikimedia.org/wikipedia/commons/7/78/Escudo_del_Instituto_Atl%C3%A9tico_Central_C%C3%B3rdoba.png",
    "argentinos": "https://upload.wikimedia.org/wikipedia/commons/4/4b/Escudo_de_Argentinos_Juniors.png",
    "velez": "https://upload.wikimedia.org/wikipedia/commons/2/21/Escudo_del_Club_Atl%C3%A9tico_V%C3%A9lez_Sarsfield.png",
    "lanus": "https://upload.wikimedia.org/wikipedia/commons/b/b8/Escudo_del_Club_Atl%C3%A9tico_Lan%C3%Bas.png",
    "banfield": "https://upload.wikimedia.org/wikipedia/commons/1/1a/Escudo_del_Club_Atl%C3%A9tico_Banfield.png",
    "defensa": "https://upload.wikimedia.org/wikipedia/commons/8/87/Escudo_de_Defensa_y_Justicia.png",
    "platense": "https://upload.wikimedia.org/wikipedia/commons/c/c8/Escudo_del_Club_Atl%C3%A9tico_Platense.png",
    "tigre": "https://upload.wikimedia.org/wikipedia/commons/1/17/Escudo_del_Club_Atl%C3%A9tico_Tigre.png",
    "union": "https://upload.wikimedia.org/wikipedia/commons/e/e0/Escudo_del_Club_Atl%C3%A9tico_Uni%C3%B3n_de_Santa_Fe.png",
    "godoy cruz": "https://upload.wikimedia.org/wikipedia/commons/b/bc/Escudo_de_Godoy_Cruz.png",
    "tucuman": "https://upload.wikimedia.org/wikipedia/commons/8/8e/Escudo_del_Club_Atl%C3%A9tico_Tucum%C3%A1n.png",
    "central cordoba": "https://upload.wikimedia.org/wikipedia/commons/2/2a/Escudo_de_Central_C%C3%B3rdoba.png",
    "sarmiento": "https://upload.wikimedia.org/wikipedia/commons/7/7e/Escudo_de_Sarmiento_de_Jun%C3%ADn.png",
    "barracas": "https://upload.wikimedia.org/wikipedia/commons/b/be/Escudo_de_Barracas_Central.png",
    "riestra": "https://upload.wikimedia.org/wikipedia/commons/3/36/Escudo_de_Deportivo_Riestra.png",
    "independiente rivadavia": "https://upload.wikimedia.org/wikipedia/commons/5/52/Escudo_de_Independiente_Rivadavia.png"
}

def normalizar_texto(txt):
    """Limpia tildes y caracteres especiales."""
    txt = str(txt).lower()
    txt = re.sub(r'\[.*?\]|\(.*?\)', '', txt)
    txt = unicodedata.normalize('NFD', txt).encode('ascii', 'ignore').decode("utf-8")
    return txt.strip()

def buscar_url_escudo(nombre_equipo):
    nombre_limpio = normalizar_texto(nombre_equipo)
    for clave, url in ESCUDOS_WEB.items():
        if clave in nombre_limpio:
            return url
    return None

# =====================================================================
# 3. CARGA DE DATOS (TABLA DE POSICIONES)
# =====================================================================
DIRECTORIO_APP = os.path.dirname(os.path.abspath(__file__))
RUTA_CSV = os.path.join(DIRECTORIO_APP, "datos_procesados.csv")

if not os.path.exists(RUTA_CSV):
    RUTA_CSV = os.path.join(os.getcwd(), "datos_procesados.csv")

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
            url_loc = buscar_url_escudo(local)
            url_vis = buscar_url_escudo(visitante)

            c_loc, c_vs, c_vis = st.columns([2, 1, 2])
            
            with c_loc:
                if url_loc:
                    st.image(url_loc, width=120)
                else:
                    st.caption("🛡️ (Sin escudo)")
                st.markdown(f"### **{local}**")
                
            with c_vs:
                st.markdown("<h1 style='text-align: center; margin-top: 25px;'>VS</h1>", unsafe_allow_html=True)
                
            with c_vis:
                if url_vis:
                    st.image(url_vis, width=120)
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
    st.error("⚠️ No se encontró el archivo 'datos_procesados.csv'. Verificá que esté en la misma carpeta.")
