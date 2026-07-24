import streamlit as st
import pandas as pd
import unicodedata
import re
import os

# 1. Configuración de la página
st.set_page_config(
    page_title="Tabla Anual - LPF Argentina",
    page_icon="⚽",
    layout="wide"
)

# 2. Links directos a internet
URLS_ESCUDOS = {
    "lpf_logo": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/15/Liga_Profesional_de_F%C3%Batbol_%28Argentina%29_logo.svg/200px-Liga_Profesional_de_F%C3%Batbol_%28Argentina%29_logo.svg.png",
    "argentinos": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/1b/AAAJ_logo.svg/100px-AAAJ_logo.svg.png",
    "atletico_tucuman": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/ae/Escudo_Atl%C3%A9tico_Tucum%C3%A1n_-_2020.svg/100px-Escudo_Atl%C3%A9tico_Tucum%C3%A1n_-_2020.svg.png",
    "banfield": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c8/Escudo_del_Club_Atl%C3%A9tico_Banfield.svg/100px-Escudo_del_Club_Atl%C3%A9tico_Banfield.svg.png",
    "barracas": "https://upload.wikimedia.org/wikipedia/commons/thumb/2/20/Escudo_de_Barracas_Central.svg/100px-Escudo_de_Barracas_Central.svg.png",
    "belgrano": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c3/Escudo_oficial_del_Club_Atl%C3%A9tico_Belgrano.svg/100px-Escudo_oficial_del_Club_Atl%C3%A9tico_Belgrano.svg.png",
    "boca": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/1b/Escudo_del_Club_Atl%C3%A9tico_Boca_Juniors.svg/100px-Escudo_del_Club_Atl%C3%A9tico_Boca_Juniors.svg.png",
    "central_cordoba": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/87/Escudo_de_Central_C%C3%B3rdoba_de_Santiago_del_Estero.svg/100px-Escudo_de_Central_C%C3%B3rdoba_de_Santiago_del_Estero.svg.png",
    "defensa": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/ac/Escudo_del_Club_Social_y_Deportivo_Defensa_y_Justicia.svg/100px-Escudo_del_Club_Social_y_Deportivo_Defensa_y_Justicia.svg.png",
    "riestra": "https://upload.wikimedia.org/wikipedia/commons/thumb/b/b5/Deportivo_Riestra_logo.svg/100px-Deportivo_Riestra_logo.svg.png",
    "estudiantes_lp": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a1/Escudo_de_Estudiantes_de_La_Plata.svg/100px-Escudo_de_Estudiantes_de_La_Plata.svg.png",
    "gimnasia_lp": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/36/Gimnasia_y_Esgrima_de_La_Plata_logo.svg/100px-Gimnasia_y_Esgrima_de_La_Plata_logo.svg.png",
    "gimnasia_mendoza": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a2/Escudo_del_Club_Gimnasia_y_Esgrima_de_Mendoza.svg/100px-Escudo_del_Club_Gimnasia_y_Esgrima_de_Mendoza.svg.png",
    "godoy_cruz": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c2/Escudo_del_Club_Deportivo_Godoy_Cruz_Antonio_Tomba.svg/100px-Escudo_del_Club_Deportivo_Godoy_Cruz_Antonio_Tomba.svg.png",
    "huracan": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a0/Escudo_del_Club_Atl%C3%A9tico_Hurac%C3%A1n.svg/100px-Escudo_del_Club_Atl%C3%A9tico_Hurac%C3%A1n.svg.png",
    "independiente_rivadavia": "https://upload.wikimedia.org/wikipedia/commons/thumb/2/23/Escudo_del_Club_Sportivo_Independiente_Rivadavia.svg/100px-Escudo_del_Club_Sportivo_Independiente_Rivadavia.svg.png",
    "independiente": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/db/Escudo_del_Club_Atl%C3%A9tico_Independiente.svg/100px-Escudo_del_Club_Atl%C3%A9tico_Independiente.svg.png",
    "instituto": "https://upload.wikimedia.org/wikipedia/commons/thumb/f/f3/Escudo_de_Instituto_ACC.svg/100px-Escudo_de_Instituto_ACC.svg.png",
    "lanus": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c1/Escudo_del_Club_Atl%C3%A9tico_Lan%C3%Bas.svg/100px-Escudo_del_Club_Atl%C3%A9tico_Lan%C3%Bas.svg.png",
    "newell": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a2/Escudo_del_Club_Atl%C3%A9tico_Newell%27s_Old_Boys.svg/100px-Escudo_del_Club_Atl%C3%A9tico_Newell%27s_Old_Boys.svg.png",
    "platense": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d4/Escudo_del_Club_Atl%C3%A9tico_Platense.svg/100px-Escudo_del_Club_Atl%C3%A9tico_Platense.svg.png",
    "racing": "https://upload.wikimedia.org/wikipedia/commons/thumb/5/56/Escudo_de_Racing_Club.svg/100px-Escudo_de_Racing_Club.svg.png",
    "river": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/ac/Escudo_del_C_A_River_Plate.svg/100px-Escudo_del_C_A_River_Plate.svg.png",
    "rosario_central": "https://upload.wikimedia.org/wikipedia/commons/thumb/f/f7/Escudo_del_Club_Atl%C3%A9tico_Rosario_Central.svg/100px-Escudo_del_Club_Atl%C3%A9tico_Rosario_Central.svg.png",
    "san_lorenzo": "https://upload.wikimedia.org/wikipedia/commons/thumb/7/77/Escudo_del_Club_Atl%C3%A9tico_San_Lorenzo_de_Almagro.svg/100px-Escudo_del_Club_Atl%C3%A9tico_San_Lorenzo_de_Almagro.svg.png",
    "sarmiento": "https://upload.wikimedia.org/wikipedia/commons/thumb/2/23/Escudo_del_Club_Atl%C3%A9tico_Sarmiento_%28Jun%C3%ADn%29.svg/100px-Escudo_del_Club_Atl%C3%A9tico_Sarmiento_%28Jun%C3%ADn%29.svg.png",
    "talleres": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/07/Escudo_del_Club_Atl%C3%A9tico_Talleres_de_C%C3%B3rdoba.svg/100px-Escudo_del_Club_Atl%C3%A9tico_Talleres_de_C%C3%B3rdoba.svg.png",
    "tigre": "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e0/Escudo_del_Club_Atl%C3%A9tico_Tigre.svg/100px-Escudo_del_Club_Atl%C3%A9tico_Tigre.svg.png",
    "union": "https://upload.wikimedia.org/wikipedia/commons/thumb/7/79/Escudo_del_Club_Atl%C3%A9tico_Uni%C3%B3n_de_Santa_Fe.svg/100px-Escudo_del_Club_Atl%C3%A9tico_Uni%C3%B3n_de_Santa_Fe.svg.png",
    "velez": "https://upload.wikimedia.org/wikipedia/commons/thumb/2/20/Escudo_del_Club_Atl%C3%A9tico_V%C3%A9lez_Sarsfield.svg/100px-Escudo_del_Club_Atl%C3%A9tico_V%C3%A9lez_Sarsfield.svg.png",
    "aldosivi": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/80/Escudo_del_Club_Atl%C3%A9tico_Aldosivi.svg/100px-Escudo_del_Club_Atl%C3%A9tico_Aldosivi.svg.png",
    "san_martin_sj": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/1a/Escudo_del_Club_Atl%C3%A9tico_San_Mart%C3%ADn_de_San_Juan.svg/100px-Escudo_del_Club_Atl%C3%A9tico_San_Mart%C3%ADn_de_San_Juan.svg.png"
}

def normalizar_texto(texto):
    if not isinstance(texto, str): return ""
    texto = re.sub(r'\[.*?\]', '', texto) 
    texto = re.sub(r'\(.*?\)', '', texto) 
    texto = unicodedata.normalize('NFD', texto).encode('ascii', 'ignore').decode("utf-8")
    return texto.lower().strip()

def obtener_url_escudo(nombre_equipo):
    norm = normalizar_texto(nombre_equipo)
    clave = "lpf_logo"
    
    if "independiente riv" in norm or "rivadavia" in norm: clave = "independiente_rivadavia"
    elif "independiente" in norm: clave = "independiente"
    elif "central cordoba" in norm or "sde" in norm or "santiago" in norm: clave = "central_cordoba"
    elif "rosario central" in norm: clave = "rosario_central"
    elif "gimnasia" in norm and "mendoza" in norm: clave = "gimnasia_mendoza"
    elif "gimnasia" in norm: clave = "gimnasia_lp"
    elif "estudiantes" in norm: clave = "estudiantes_lp"
    elif "argentinos" in norm: clave = "argentinos"
    elif "tucuman" in norm: clave = "atletico_tucuman"
    elif "barracas" in norm: clave = "barracas"
    elif "boca" in norm: clave = "boca"
    elif "defensa" in norm: clave = "defensa"
    elif "riestra" in norm: clave = "riestra"
    elif "godoy cruz" in norm: clave = "godoy_cruz"
    elif "huracan" in norm: clave = "huracan"
    elif "instituto" in norm: clave = "instituto"
    elif "lanus" in norm: clave = "lanus"
    elif "newell" in norm: clave = "newell"
    elif "platense" in norm: clave = "platense"
    elif "racing" in norm: clave = "racing"
    elif "river" in norm: clave = "river"
    elif "san lorenzo" in norm: clave = "san_lorenzo"
    elif "sarmiento" in norm: clave = "sarmiento"
    elif "talleres" in norm: clave = "talleres"
    elif "tigre" in norm: clave = "tigre"
    elif "union" in norm: clave = "union"
    elif "velez" in norm: clave = "velez"
    elif "belgrano" in norm: clave = "belgrano"
    elif "banfield" in norm: clave = "banfield"
    elif "aldosivi" in norm: clave = "aldosivi"
    elif "san martin" in norm or "san juan" in norm: clave = "san_martin_sj"
        
    return URLS_ESCUDOS.get(clave, URLS_ESCUDOS["lpf_logo"])

# 3. CSS para que la tabla HTML se vea moderna y prolija
st.markdown("""
<style>
.tabla-lpf { width: 100%; border-collapse: collapse; text-align: center; margin-bottom: 20px;}
.tabla-lpf th { padding: 12px; border-bottom: 2px solid #555; text-align: center !important;}
.tabla-lpf td { padding: 8px; border-bottom: 1px solid #333; vertical-align: middle; }
.tabla-lpf tr:hover { background-color: rgba(255, 255, 255, 0.05); }
</style>
""", unsafe_allow_html=True)

# 4. Encabezado principal
col_lpf, col_title = st.columns([1, 6])
with col_lpf:
    st.markdown(f'<img src="{URLS_ESCUDOS["lpf_logo"]}" width="80">', unsafe_allow_html=True)
with col_title:
    st.title("Tabla Anual - Liga Profesional de Fútbol")
    st.caption("Estadísticas oficiales y predictor de partidos en tiempo real")

st.markdown("---")

# 5. Carga de datos y Tabla HTML Forzada
CSV_PATH = "datos_procesados.csv"

if not os.path.exists(CSV_PATH):
    st.error(f"No se encontró el archivo '{CSV_PATH}'.")
else:
    df = pd.read_csv(CSV_PATH)
    df.columns = df.columns.str.strip()
    
    if "Equipo" in df.columns:
        df["Equipo"] = df["Equipo"].astype(str).apply(lambda x: re.sub(r'\[.*?\]', '', x).strip())
        
        # ACA ESTÁ LA MAGIA: Metemos la etiqueta de imagen HTML directo en la celda del DataFrame
        df["Escudo"] = df["Equipo"].apply(
            lambda x: f'<img src="{obtener_url_escudo(x)}" width="35" style="display:block; margin:auto;">'
        )
        
        # Ordenamos las columnas
        columnas_deseadas = ["Escudo", "Equipo", "Puntos", "PJ", "PG", "PE", "PP", "GF", "GC"]
        cols_existentes = [c for c in columnas_deseadas if c in df.columns]
        otras_cols = [c for c in df.columns if c not in cols_existentes]
        df_mostrar = df[cols_existentes + otras_cols].copy()
        
        # Renderizamos la tabla puenteando la función rota de Streamlit
        html_tabla = df_mostrar.to_html(escape=False, index=False, classes="tabla-lpf")
        st.markdown(html_tabla, unsafe_allow_html=True)

        st.markdown("---")

        # 6. Predictor
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
                url_local = obtener_url_escudo(local)
                url_vis = obtener_url_escudo(visitante)

                c_loc, c_vs, c_vis = st.columns([2, 1, 2])
                with c_loc:
                    st.markdown(f'<img src="{url_local}" width="90">', unsafe_allow_html=True)
                    st.markdown(f"### **{local}**")
                with c_vs:
                    st.markdown("<h2 style='text-align: center; margin-top: 20px;'>VS</h2>", unsafe_allow_html=True)
                with c_vis:
                    st.markdown(f'<img src="{url_vis}" width="90">', unsafe_allow_html=True)
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
