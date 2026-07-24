import streamlit as st
import pandas as pd
import unicodedata
import re
import os

# 1. Configuración de la página Streamlit
st.set_page_config(
    page_title="Tabla Anual - LPF Argentina",
    page_icon="⚽",
    layout="wide"
)

# 2. Escudos directos desde Wikimedia Commons (A prueba de fallos)
LOGO_LPF = "https://upload.wikimedia.org/wikipedia/commons/thumb/1/15/Liga_Profesional_de_F%C3%Batbol_%28Argentina%29_logo.svg/200px-Liga_Profesional_de_F%C3%Batbol_%28Argentina%29_logo.svg.png"

ESCUDOS_WIKIPEDIA = {
    "argentinos": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/1b/AAAJ_logo.svg/100px-AAAJ_logo.svg.png",
    "atletico tucuman": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/ae/Escudo_Atl%C3%A9tico_Tucum%C3%A1n_-_2020.svg/100px-Escudo_Atl%C3%A9tico_Tucum%C3%A1n_-_2020.svg.png",
    "banfield": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c8/Escudo_del_Club_Atl%C3%A9tico_Banfield.svg/100px-Escudo_del_Club_Atl%C3%A9tico_Banfield.svg.png",
    "barracas": "https://upload.wikimedia.org/wikipedia/commons/thumb/2/20/Escudo_de_Barracas_Central.svg/100px-Escudo_de_Barracas_Central.svg.png",
    "belgrano": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c3/Escudo_oficial_del_Club_Atl%C3%A9tico_Belgrano.svg/100px-Escudo_oficial_del_Club_Atl%C3%A9tico_Belgrano.svg.png",
    "boca": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/1b/Escudo_del_Club_Atl%C3%A9tico_Boca_Juniors.svg/100px-Escudo_del_Club_Atl%C3%A9tico_Boca_Juniors.svg.png",
    "central cordoba": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/87/Escudo_de_Central_C%C3%B3rdoba_de_Santiago_del_Estero.svg/100px-Escudo_de_Central_C%C3%B3rdoba_de_Santiago_del_Estero.svg.png",
    "defensa": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/ac/Escudo_del_Club_Social_y_Deportivo_Defensa_y_Justicia.svg/100px-Escudo_del_Club_Social_y_Deportivo_Defensa_y_Justicia.svg.png",
    "riestra": "https://upload.wikimedia.org/wikipedia/commons/thumb/b/b5/Deportivo_Riestra_logo.svg/100px-Deportivo_Riestra_logo.svg.png",
    "estudiantes lp": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a1/Escudo_de_Estudiantes_de_La_Plata.svg/100px-Escudo_de_Estudiantes_de_La_Plata.svg.png",
    "gimnasia lp": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/36/Gimnasia_y_Esgrima_de_La_Plata_logo.svg/100px-Gimnasia_y_Esgrima_de_La_Plata_logo.svg.png",
    "godoy cruz": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c2/Escudo_del_Club_Deportivo_Godoy_Cruz_Antonio_Tomba.svg/100px-Escudo_del_Club_Deportivo_Godoy_Cruz_Antonio_Tomba.svg.png",
    "huracan": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a0/Escudo_del_Club_Atl%C3%A9tico_Hurac%C3%A1n.svg/100px-Escudo_del_Club_Atl%C3%A9tico_Hurac%C3%A1n.svg.png",
    "independiente rivadavia": "https://upload.wikimedia.org/wikipedia/commons/thumb/2/23/Escudo_del_Club_Sportivo_Independiente_Rivadavia.svg/100px-Escudo_del_Club_Sportivo_Independiente_Rivadavia.svg.png",
    "independiente": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/db/Escudo_del_Club_Atl%C3%A9tico_Independiente.svg/100px-Escudo_del_Club_Atl%C3%A9tico_Independiente.svg.png",
    "instituto": "https://upload.wikimedia.org/wikipedia/commons/thumb/f/f3/Escudo_de_Instituto_ACC.svg/100px-Escudo_de_Instituto_ACC.svg.png",
    "lanus": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c1/Escudo_del_Club_Atl%C3%A9tico_Lan%C3%Bas.svg/100px-Escudo_del_Club_Atl%C3%A9tico_Lan%C3%Bas.svg.png",
    "newell": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a2/Escudo_del_Club_Atl%C3%A9tico_Newell%27s_Old_Boys.svg/100px-Escudo_del_Club_Atl%C3%A9tico_Newell%27s_Old_Boys.svg.png",
    "platense": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d4/Escudo_del_Club_Atl%C3%A9tico_Platense.svg/100px-Escudo_del_Club_Atl%C3%A9tico_Platense.svg.png",
    "racing": "https://upload.wikimedia.org/wikipedia/commons/thumb/5/56/Escudo_de_Racing_Club.svg/100px-Escudo_de_Racing_Club.svg.png",
    "river": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/ac/Escudo_del_C_A_River_Plate.svg/100px-Escudo_del_C_A_River_Plate.svg.png",
    "rosario central": "https://upload.wikimedia.org/wikipedia/commons/thumb/f/f7/Escudo_del_Club_Atl%C3%A9tico_Rosario_Central.svg/100px-Escudo_del_Club_Atl%C3%A9tico_Rosario_Central.svg.png",
    "san lorenzo": "https://upload.wikimedia.org/wikipedia/commons/thumb/7/77/Escudo_del_Club_Atl%C3%A9tico_San_Lorenzo_de_Almagro.svg/100px-Escudo_del_Club_Atl%C3%A9tico_San_Lorenzo_de_Almagro.svg.png",
    "sarmiento": "https://upload.wikimedia.org/wikipedia/commons/thumb/2/23/Escudo_del_Club_Atl%C3%A9tico_Sarmiento_%28Jun%C3%ADn%29.svg/100px-Escudo_del_Club_Atl%C3%A9tico_Sarmiento_%28Jun%C3%ADn%29.svg.png",
    "talleres": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/07/Escudo_del_Club_Atl%C3%A9tico_Talleres_de_C%C3%B3rdoba.svg/100px-Escudo_del_Club_Atl%C3%A9tico_Talleres_de_C%C3%B3rdoba.svg.png",
    "tigre": "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e0/Escudo_del_Club_Atl%C3%A9tico_Tigre.svg/100px-Escudo_del_Club_Atl%C3%A9tico_Tigre.svg.png",
    "union": "https://upload.wikimedia.org/wikipedia/commons/thumb/7/79/Escudo_del_Club_Atl%C3%A9tico_Uni%C3%B3n_de_Santa_Fe.svg/100px-Escudo_del_Club_Atl%C3%A9tico_Uni%C3%B3n_de_Santa_Fe.svg.png",
    "velez": "https://upload.wikimedia.org/wikipedia/commons/thumb/2/20/Escudo_del_Club_Atl%C3%A9tico_V%C3%A9lez_Sarsfield.svg/100px-Escudo_del_Club_Atl%C3%A9tico_V%C3%A9lez_Sarsfield.svg.png",
    "aldosivi": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/80/Escudo_del_Club_Atl%C3%A9tico_Aldosivi.svg/100px-Escudo_del_Club_Atl%C3%A9tico_Aldosivi.svg.png",
    "san martin sj": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/1a/Escudo_del_Club_Atl%C3%A9tico_San_Mart%C3%ADn_de_San_Juan.svg/100px-Escudo_del_Club_Atl%C3%A9tico_San_Mart%C3%ADn_de_San_Juan.svg.png"
}

def normalizar_texto(texto):
    if not isinstance(texto, str):
        return ""
    texto = re.sub(r'\[.*?\]', '', texto)
    texto = re.sub(r'\(.*?\)', '', texto)
    texto = unicodedata.normalize('NFD', texto).encode('ascii', 'ignore').decode("utf-8")
    return texto.lower().strip()

def obtener_escudo(nombre_equipo):
    norm = normalizar_texto(nombre_equipo)
    
    if "independiente riv" in norm or "rivadavia" in norm:
        return ESCUDOS_WIKIPEDIA["independiente rivadavia"]
    if "independiente" in norm:
        return ESCUDOS_WIKIPEDIA["independiente"]
    if "central cordoba" in norm or "sde" in norm or "santiago" in norm:
        return ESCUDOS_WIKIPEDIA["central cordoba"]
    if "rosario central" in norm:
        return ESCUDOS_WIKIPEDIA["rosario central"]
    if "gimnasia" in norm:
        return ESCUDOS_WIKIPEDIA["gimnasia lp"]
    if "estudiantes" in norm:
        return ESCUDOS_WIKIPEDIA["estudiantes lp"]
    if "argentinos" in norm:
        return ESCUDOS_WIKIPEDIA["argentinos"]
    if "atletico tucuman" in norm or "tucuman" in norm:
        return ESCUDOS_WIKIPEDIA["atletico tucuman"]
    if "barracas" in norm:
        return ESCUDOS_WIKIPEDIA["barracas"]
    if "boca" in norm:
        return ESCUDOS_WIKIPEDIA["boca"]
    if "defensa" in norm:
        return ESCUDOS_WIKIPEDIA["defensa"]
    if "riestra" in norm:
        return ESCUDOS_WIKIPEDIA["riestra"]
    if "godoy cruz" in norm:
        return ESCUDOS_WIKIPEDIA["godoy cruz"]
    if "huracan" in norm:
        return ESCUDOS_WIKIPEDIA["huracan"]
    if "instituto" in norm:
        return ESCUDOS_WIKIPEDIA["instituto"]
    if "lanus" in norm:
        return ESCUDOS_WIKIPEDIA["lanus"]
    if "newell" in norm:
        return ESCUDOS_WIKIPEDIA["newell"]
    if "platense" in norm:
        return ESCUDOS_WIKIPEDIA["platense"]
    if "racing" in norm:
        return ESCUDOS_WIKIPEDIA["racing"]
    if "river" in norm:
        return ESCUDOS_WIKIPEDIA["river"]
    if "san lorenzo" in norm:
        return ESCUDOS_WIKIPEDIA["san lorenzo"]
    if "sarmiento" in norm:
        return ESCUDOS_WIKIPEDIA["sarmiento"]
    if "talleres" in norm:
        return ESCUDOS_WIKIPEDIA["talleres"]
    if "tigre" in norm:
        return ESCUDOS_WIKIPEDIA["tigre"]
    if "union" in norm:
        return ESCUDOS_WIKIPEDIA["union"]
    if "velez" in norm:
        return ESCUDOS_WIKIPEDIA["velez"]
    if "belgrano" in norm:
        return ESCUDOS_WIKIPEDIA["belgrano"]
    if "banfield" in norm:
        return ESCUDOS_WIKIPEDIA["banfield"]
    if "aldosivi" in norm:
        return ESCUDOS_WIKIPEDIA["aldosivi"]
    if "san martin" in norm:
        return ESCUDOS_WIKIPEDIA["san martin sj"]
        
    return LOGO_LPF

# 3. Encabezado principal
col_lpf, col_title = st.columns([1, 6])
with col_lpf:
    st.image(LOGO_LPF, width=80)
with col_title:
    st.title("Tabla Anual - Liga Profesional de Fútbol")
    st.caption("Estadísticas oficiales y predictor de partidos en tiempo real")

st.markdown("---")

# 4. Carga de datos y renderizado de la tabla
CSV_PATH = "datos_procesados.csv"

if not os.path.exists(CSV_PATH):
    st.error(f"No se encontró el archivo '{CSV_PATH}'.")
else:
    df = pd.read_csv(CSV_PATH)
    df.columns = df.columns.str.strip()
    
    if "Equipo" in df.columns:
        df["Equipo"] = df["Equipo"].astype(str)
        df["Escudo"] = df["Equipo"].apply(obtener_escudo)
        
        columnas_deseadas = ["Escudo", "Equipo", "Puntos", "PJ", "PG", "PE", "PP", "GF", "GC"]
        cols_existentes = [c for c in columnas_deseadas if c in df.columns]
        
        otras_cols = [c for c in df.columns if c not in cols_existentes]
        df_mostrar = df[cols_existentes + otras_cols].copy()
        
        st.dataframe(
            df_mostrar,
            hide_index=True,
            column_config={
                "Escudo": st.column_config.ImageColumn(
                    "🛡️", 
                    width="small"
                ),
                "Equipo": st.column_config.TextColumn("Equipo", width="medium"),
                "Puntos": st.column_config.NumberColumn("Puntos", format="%d"),
                "PJ": st.column_config.NumberColumn("PJ", format="%d"),
                "PG": st.column_config.NumberColumn("PG", format="%d"),
                "PE": st.column_config.NumberColumn("PE", format="%d"),
                "PP": st.column_config.NumberColumn("PP", format="%d"),
                "GF": st.column_config.NumberColumn("GF", format="%d"),
                "GC": st.column_config.NumberColumn("GC", format="%d"),
            },
            use_container_width=True
        )

        st.markdown("---")

        # 5. Predictor
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
                    st.image(escudo_local, width=90)
                    st.markdown(f"### **{local}**")
                with c_vs:
                    st.markdown("<h2 style='text-align: center; margin-top: 20px;'>VS</h2>", unsafe_allow_html=True)
                with c_vis:
                    st.image(escudo_vis, width=90)
                    st.markdown(f"### **{visitante}**")

                stats_loc = df[df["Equipo"] == local].iloc[0]
                stats_vis = df[df["Equipo"] == visitante].iloc[0]

                pts_loc = stats_loc.get("Puntos", 0)
                pts_vis = stats_vis.get("Puntos", 0)
                pj_loc = max(stats_loc.get("PJ", 1), 1)
                pj_vis = max(stats_vis.get("PJ", 1), 1)

                prom_loc = pts_loc / pj_loc
                prom_vis = pts_vis / pj_vis

                factor_localia = 1.15
                score_loc = prom_loc * factor_localia
                score_vis = prom_vis

                total = score_loc + score_vis
                if total > 0:
                    prob_loc = (score_loc / total) * 100
                    prob_vis = (score_vis / total) * 100
                else:
                    prob_loc, prob_vis = 50.0, 50.0

                st.markdown("#### **Probabilidades del Encuentro**")
                p1, p2 = st.columns(2)
                p1.metric(f"Victoria {local} (Local)", f"{prob_loc:.1f}%")
                p2.metric(f"Victoria {visitante} (Visitante)", f"{prob_vis:.1f}%")

                st.progress(int(prob_loc))
