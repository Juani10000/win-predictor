import streamlit as st
import pandas as pd
import unicodedata
import re
import os
import urllib.request
from PIL import Image

# 1. Configuración de página
st.set_page_config(page_title="Tabla Anual - LPF", page_icon="⚽", layout="wide")

# 2. URLs directas de escudos en alta calidad
URLS_ESCUDOS = {
    "argentinos": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/1b/AAAJ_logo.svg/200px-AAAJ_logo.svg.png",
    "tucuman": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/ae/Escudo_Atl%C3%A9tico_Tucum%C3%A1n_-_2020.svg/200px-Escudo_Atl%C3%A9tico_Tucum%C3%A1n_-_2020.svg.png",
    "banfield": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c8/Escudo_del_Club_Atl%C3%A9tico_Banfield.svg/200px-Escudo_del_Club_Atl%C3%A9tico_Banfield.svg.png",
    "barracas": "https://upload.wikimedia.org/wikipedia/commons/thumb/2/20/Escudo_de_Barracas_Central.svg/200px-Escudo_de_Barracas_Central.svg.png",
    "belgrano": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c3/Escudo_oficial_del_Club_Atl%C3%A9tico_Belgrano.svg/200px-Escudo_oficial_del_Club_Atl%C3%A9tico_Belgrano.svg.png",
    "boca": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/1b/Escudo_del_Club_Atl%C3%A9tico_Boca_Juniors.svg/200px-Escudo_del_Club_Atl%C3%A9tico_Boca_Juniors.svg.png",
    "central cordoba": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/87/Escudo_de_Central_C%C3%B3rdoba_de_Santiago_del_Estero.svg/200px-Escudo_de_Central_C%C3%B3rdoba_de_Santiago_del_Estero.svg.png",
    "defensa": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/ac/Escudo_del_Club_Social_y_Deportivo_Defensa_y_Justicia.svg/200px-Escudo_del_Club_Social_y_Deportivo_Defensa_y_Justicia.svg.png",
    "riestra": "https://upload.wikimedia.org/wikipedia/commons/thumb/b/b5/Deportivo_Riestra_logo.svg/200px-Deportivo_Riestra_logo.svg.png",
    "estudiantes": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a1/Escudo_de_Estudiantes_de_La_Plata.svg/200px-Escudo_de_Estudiantes_de_La_Plata.svg.png",
    "gimnasia": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/36/Gimnasia_y_Esgrima_de_La_Plata_logo.svg/200px-Gimnasia_y_Esgrima_de_La_Plata_logo.svg.png",
    "godoy": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c2/Escudo_del_Club_Deportivo_Godoy_Cruz_Antonio_Tomba.svg/200px-Escudo_del_Club_Deportivo_Godoy_Cruz_Antonio_Tomba.svg.png",
    "huracan": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a0/Escudo_del_Club_Atl%C3%A9tico_Hurac%C3%A1n.svg/200px-Escudo_del_Club_Atl%C3%A9tico_Hurac%C3%A1n.svg.png",
    "rivadavia": "https://upload.wikimedia.org/wikipedia/commons/thumb/2/23/Escudo_del_Club_Sportivo_Independiente_Rivadavia.svg/200px-Escudo_del_Club_Sportivo_Independiente_Rivadavia.svg.png",
    "independiente": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/db/Escudo_del_Club_Atl%C3%A9tico_Independiente.svg/200px-Escudo_del_Club_Atl%C3%A9tico_Independiente.svg.png",
    "instituto": "https://upload.wikimedia.org/wikipedia/commons/thumb/f/f3/Escudo_de_Instituto_ACC.svg/200px-Escudo_de_Instituto_ACC.svg.png",
    "lanus": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c1/Escudo_del_Club_Atl%C3%A9tico_Lan%C3%Bas.svg/200px-Escudo_del_Club_Atl%C3%A9tico_Lan%C3%Bas.svg.png",
    "newell": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a2/Escudo_del_Club_Atl%C3%A9tico_Newell%27s_Old_Boys.svg/200px-Escudo_del_Club_Atl%C3%A9tico_Newell%27s_Old_Boys.svg.png",
    "platense": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d4/Escudo_del_Club_Atl%C3%A9tico_Platense.svg/200px-Escudo_del_Club_Atl%C3%A9tico_Platense.svg.png",
    "racing": "https://upload.wikimedia.org/wikipedia/commons/thumb/5/56/Escudo_de_Racing_Club.svg/200px-Escudo_de_Racing_Club.svg.png",
    "river": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/ac/Escudo_del_C_A_River_Plate.svg/200px-Escudo_del_C_A_River_Plate.svg.png",
    "rosario": "https://upload.wikimedia.org/wikipedia/commons/thumb/f/f7/Escudo_del_Club_Atl%C3%A9tico_Rosario_Central.svg/200px-Escudo_del_Club_Atl%C3%A9tico_Rosario_Central.svg.png",
    "san lorenzo": "https://upload.wikimedia.org/wikipedia/commons/thumb/7/77/Escudo_del_Club_Atl%C3%A9tico_San_Lorenzo_de_Almagro.svg/200px-Escudo_del_Club_Atl%C3%A9tico_San_Lorenzo_de_Almagro.svg.png",
    "sarmiento": "https://upload.wikimedia.org/wikipedia/commons/thumb/2/23/Escudo_del_Club_Atl%C3%A9tico_Sarmiento_%28Jun%C3%ADn%29.svg/200px-Escudo_del_Club_Atl%C3%A9tico_Sarmiento_%28Jun%C3%ADn%29.svg.png",
    "talleres": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/07/Escudo_del_Club_Atl%C3%A9tico_Talleres_de_C%C3%B3rdoba.svg/200px-Escudo_del_Club_Atl%C3%A9tico_Talleres_de_C%C3%B3rdoba.svg.png",
    "tigre": "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e0/Escudo_del_Club_Atl%C3%A9tico_Tigre.svg/200px-Escudo_del_Club_Atl%C3%A9tico_Tigre.svg.png",
    "union": "https://upload.wikimedia.org/wikipedia/commons/thumb/7/79/Escudo_del_Club_Atl%C3%A9tico_Uni%C3%B3n_de_Santa_Fe.svg/200px-Escudo_del_Club_Atl%C3%A9tico_Uni%C3%B3n_de_Santa_Fe.svg.png",
    "velez": "https://upload.wikimedia.org/wikipedia/commons/thumb/2/20/Escudo_del_Club_Atl%C3%A9tico_V%C3%A9lez_Sarsfield.svg/200px-Escudo_del_Club_Atl%C3%A9tico_V%C3%A9lez_Sarsfield.svg.png",
    "aldosivi": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/80/Escudo_del_Club_Atl%C3%A9tico_Aldosivi.svg/200px-Escudo_del_Club_Atl%C3%A9tico_Aldosivi.svg.png",
    "san martin": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/1a/Escudo_del_Club_Atl%C3%A9tico_San_Mart%C3%ADn_de_San_Juan.svg/200px-Escudo_del_Club_Atl%C3%A9tico_San_Mart%C3%ADn_de_San_Juan.svg.png"
}

# 3. Descarga Automática (Se ejecuta en 2 segundos la primera vez)
@st.cache_resource
def auto_descargar_escudos():
    os.makedirs("escudos", exist_ok=True)
    headers = {'User-Agent': 'Mozilla/5.0'}
    for clave, url in URLS_ESCUDOS.items():
        ruta = os.path.join("escudos", f"{clave}.png")
        if not os.path.exists(ruta):
            try:
                req = urllib.request.Request(url, headers=headers)
                with urllib.request.urlopen(req) as response, open(ruta, 'wb') as out_file:
                    out_file.write(response.read())
            except Exception:
                pass

auto_descargar_escudos()

# 4. Buscador de escudo guardado
def obtener_escudo_local(nombre_equipo):
    txt = unicodedata.normalize('NFD', str(nombre_equipo)).encode('ascii', 'ignore').decode("utf-8").lower()
    for clave in URLS_ESCUDOS.keys():
        if clave in txt:
            ruta = os.path.join("escudos", f"{clave}.png")
            if os.path.exists(ruta):
                return ruta
    return None

# 5. Interfaz
st.title("⚽ Tabla Anual - Liga Profesional de Fútbol")
st.caption("Estadísticas oficiales y predictor de partidos")
st.markdown("---")

CSV_PATH = "datos_procesados.csv"

if not os.path.exists(CSV_PATH):
    st.error(f"⚠️ No se encontró el archivo '{CSV_PATH}'.")
else:
    df = pd.read_csv(CSV_PATH)
    df.columns = df.columns.str.strip()

    if "Equipo" in df.columns:
        df["Equipo"] = df["Equipo"].astype(str).apply(lambda x: re.sub(r'\[.*?\]|\(.*?\)', '', x).strip())
        
        # Tabla limpia y rápida
        st.subheader("📊 Tabla de Posiciones")
        st.dataframe(df, use_container_width=True, hide_index=True)

        st.markdown("---")

        # Predictor con escudos locales cargados solos
        st.subheader("🔮 Predictor de Enfrentamientos")
        lista_equipos = sorted(df["Equipo"].unique())

        if len(lista_equipos) >= 2:
            col1, col2 = st.columns(2)
            with col1:
                local = st.selectbox("Equipo Local", lista_equipos, index=0)
            with col2:
                visitante = st.selectbox("Equipo Visitante", lista_equipos, index=min(1, len(lista_equipos)-1))

            if local == visitante:
                st.warning("Selecciona dos equipos distintos.")
            else:
                escudo_loc = obtener_escudo_local(local)
                escudo_vis = obtener_escudo_local(visitante)

                c_loc, c_vs, c_vis = st.columns([2, 1, 2])
                with c_loc:
                    if escudo_loc:
                        st.image(Image.open(escudo_loc), width=110)
                    st.markdown(f"### **{local}**")
                with c_vs:
                    st.markdown("<h1 style='text-align: center; margin-top: 30px;'>VS</h1>", unsafe_allow_html=True)
                with c_vis:
                    if escudo_vis:
                        st.image(Image.open(escudo_vis), width=110)
                    st.markdown(f"### **{visitante}**")

                # Probabilidades
                row_loc = df[df["Equipo"] == local].iloc[0]
                row_vis = df[df["Equipo"] == visitante].iloc[0]

                pts_loc = float(row_loc.get("Puntos", 0))
                pts_vis = float(row_vis.get("Puntos", 0))
                pj_loc = max(float(row_loc.get("PJ", 1)), 1.0)
                pj_vis = max(float(row_vis.get("PJ", 1)), 1.0)

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
