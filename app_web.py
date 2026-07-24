import streamlit as st
import pandas as pd
import unicodedata
import re
import os

# 1. Configuración básica
st.set_page_config(page_title="Tabla Anual - LPF Argentina", page_icon="⚽", layout="wide")

# 2. Diccionario simplificado de escudos
ESCUDOS = {
    "argentinos": "https://upload.wikimedia.org/wikipedia/commons/1/1b/AAAJ_logo.svg",
    "tucuman": "https://upload.wikimedia.org/wikipedia/commons/a/ae/Escudo_Atl%C3%A9tico_Tucum%C3%A1n_-_2020.svg",
    "banfield": "https://upload.wikimedia.org/wikipedia/commons/c/c8/Escudo_del_Club_Atl%C3%A9tico_Banfield.svg",
    "barracas": "https://upload.wikimedia.org/wikipedia/commons/2/20/Escudo_de_Barracas_Central.svg",
    "belgrano": "https://upload.wikimedia.org/wikipedia/commons/c/c3/Escudo_oficial_del_Club_Atl%C3%A9tico_Belgrano.svg",
    "boca": "https://upload.wikimedia.org/wikipedia/commons/1/1b/Escudo_del_Club_Atl%C3%A9tico_Boca_Juniors.svg",
    "central cordoba": "https://upload.wikimedia.org/wikipedia/commons/8/87/Escudo_de_Central_C%C3%B3rdoba_de_Santiago_del_Estero.svg",
    "defensa": "https://upload.wikimedia.org/wikipedia/commons/a/ac/Escudo_del_Club_Social_y_Deportivo_Defensa_y_Justicia.svg",
    "riestra": "https://upload.wikimedia.org/wikipedia/commons/b/b5/Deportivo_Riestra_logo.svg",
    "estudiantes": "https://upload.wikimedia.org/wikipedia/commons/a/a1/Escudo_de_Estudiantes_de_La_Plata.svg",
    "gimnasia": "https://upload.wikimedia.org/wikipedia/commons/3/36/Gimnasia_y_Esgrima_de_La_Plata_logo.svg",
    "godoy": "https://upload.wikimedia.org/wikipedia/commons/c/c2/Escudo_del_Club_Deportivo_Godoy_Cruz_Antonio_Tomba.svg",
    "huracan": "https://upload.wikimedia.org/wikipedia/commons/a/a0/Escudo_del_Club_Atl%C3%A9tico_Hurac%C3%A1n.svg",
    "rivadavia": "https://upload.wikimedia.org/wikipedia/commons/2/23/Escudo_del_Club_Sportivo_Independiente_Rivadavia.svg",
    "independiente": "https://upload.wikimedia.org/wikipedia/commons/d/db/Escudo_del_Club_Atl%C3%A9tico_Independiente.svg",
    "instituto": "https://upload.wikimedia.org/wikipedia/commons/f/f3/Escudo_de_Instituto_ACC.svg",
    "lanus": "https://upload.wikimedia.org/wikipedia/commons/c/c1/Escudo_del_Club_Atl%C3%A9tico_Lan%C3%Bas.svg",
    "newell": "https://upload.wikimedia.org/wikipedia/commons/a/a2/Escudo_del_Club_Atl%C3%A9tico_Newell%27s_Old_Boys.svg",
    "platense": "https://upload.wikimedia.org/wikipedia/commons/d/d4/Escudo_del_Club_Atl%C3%A9tico_Platense.svg",
    "racing": "https://upload.wikimedia.org/wikipedia/commons/5/56/Escudo_de_Racing_Club.svg",
    "river": "https://upload.wikimedia.org/wikipedia/commons/a/ac/Escudo_del_C_A_River_Plate.svg",
    "rosario": "https://upload.wikimedia.org/wikipedia/commons/f/f7/Escudo_del_Club_Atl%C3%A9tico_Rosario_Central.svg",
    "san lorenzo": "https://upload.wikimedia.org/wikipedia/commons/7/77/Escudo_del_Club_Atl%C3%A9tico_San_Lorenzo_de_Almagro.svg",
    "sarmiento": "https://upload.wikimedia.org/wikipedia/commons/2/23/Escudo_del_Club_Atl%C3%A9tico_Sarmiento_%28Jun%C3%ADn%29.svg",
    "talleres": "https://upload.wikimedia.org/wikipedia/commons/0/07/Escudo_del_Club_Atl%C3%A9tico_Talleres_de_C%C3%B3rdoba.svg",
    "tigre": "https://upload.wikimedia.org/wikipedia/commons/e/e0/Escudo_del_Club_Atl%C3%A9tico_Tigre.svg",
    "union": "https://upload.wikimedia.org/wikipedia/commons/7/79/Escudo_del_Club_Atl%C3%A9tico_Uni%C3%B3n_de_Santa_Fe.svg",
    "velez": "https://upload.wikimedia.org/wikipedia/commons/2/20/Escudo_del_Club_Atl%C3%A9tico_V%C3%A9lez_Sarsfield.svg",
    "aldosivi": "https://upload.wikimedia.org/wikipedia/commons/8/80/Escudo_del_Club_Atl%C3%A9tico_Aldosivi.svg",
    "san martin": "https://upload.wikimedia.org/wikipedia/commons/1/1a/Escudo_del_Club_Atl%C3%A9tico_San_Mart%C3%ADn_de_San_Juan.svg"
}

LOGO_LPF = "https://upload.wikimedia.org/wikipedia/commons/1/15/Liga_Profesional_de_F%C3%Batbol_%28Argentina%29_logo.svg"

def obtener_escudo(nombre):
    txt = unicodedata.normalize('NFD', str(nombre)).encode('ascii', 'ignore').decode("utf-8").lower()
    for clave, url in ESCUDOS.items():
        if clave in txt:
            return url
    return LOGO_LPF

# 3. Encabezado
col_logo, col_titulo = st.columns([1, 6])
with col_logo:
    st.image(LOGO_LPF, width=75)
with col_titulo:
    st.title("Tabla Anual - Liga Profesional de Fútbol")
    st.caption("Estadísticas en tiempo real y predictor de partidos")

st.markdown("---")

# 4. Carga y despliegue de datos
CSV_PATH = "datos_procesados.csv"

if not os.path.exists(CSV_PATH):
    st.error(f"No se encontró el archivo '{CSV_PATH}'. Asegúrate de que el scraper esté generando el CSV correctamente.")
else:
    df = pd.read_csv(CSV_PATH)
    df.columns = df.columns.str.strip()

    if "Equipo" in df.columns:
        # Limpieza de nombres
        df["Equipo"] = df["Equipo"].astype(str).apply(lambda x: re.sub(r'\[.*?\]|\(.*?\)', '', x).strip())
        
        # Muestra la tabla de datos completa, rápida y legible
        st.subheader("📊 Tabla de Posiciones")
        st.dataframe(df, use_container_width=True, hide_index=True)

        st.markdown("---")

        # 5. Predictor con escudos garantizados
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
                escudo_local = obtener_escudo(local)
                escudo_vis = obtener_escudo(visitante)

                c_loc, c_vs, c_vis = st.columns([2, 1, 2])
                with c_loc:
                    st.image(escudo_local, width=100)
                    st.markdown(f"### **{local}**")
                with c_vs:
                    st.markdown("<h2 style='text-align: center; margin-top: 30px;'>VS</h2>", unsafe_allow_html=True)
                with c_vis:
                    st.image(escudo_vis, width=100)
                    st.markdown(f"### **{visitante}**")

                # Cálculo de probabilidades según estadísticas del CSV
                row_loc = df[df["Equipo"] == local].iloc[0]
                row_vis = df[df["Equipo"] == visitante].iloc[0]

                pts_loc = float(row_loc.get("Puntos", 0))
                pts_vis = float(row_vis.get("Puntos", 0))
                pj_loc = max(float(row_loc.get("PJ", 1)), 1.0)
                pj_vis = max(float(row_vis.get("PJ", 1)), 1.0)

                prom_loc = (pts_loc / pj_loc) * 1.15  # Ventaja de localía
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
