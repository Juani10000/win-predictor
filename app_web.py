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

# 2. Enlaces DIRECTOS de ESPN (¡No fallan ni los bloquean!)
LOGO_LPF = "https://a.espncdn.com/i/leaguelogos/soccer/500/1.png"

ESCUDOS_ESPN = {
    "argentinos": "https://a.espncdn.com/i/teamlogos/soccer/500/1.png",
    "atletico tucuman": "https://a.espncdn.com/i/teamlogos/soccer/500/10232.png",
    "banfield": "https://a.espncdn.com/i/teamlogos/soccer/500/2.png",
    "barracas": "https://a.espncdn.com/i/teamlogos/soccer/500/19901.png",
    "belgrano": "https://a.espncdn.com/i/teamlogos/soccer/500/3810.png",
    "boca": "https://a.espncdn.com/i/teamlogos/soccer/500/5.png",
    "central cordoba": "https://a.espncdn.com/i/teamlogos/soccer/500/18848.png",
    "defensa": "https://a.espncdn.com/i/teamlogos/soccer/500/10313.png",
    "riestra": "https://a.espncdn.com/i/teamlogos/soccer/500/20141.png",
    "estudiantes lp": "https://a.espncdn.com/i/teamlogos/soccer/500/8.png",
    "gimnasia lp": "https://a.espncdn.com/i/teamlogos/soccer/500/9.png",
    "godoy cruz": "https://a.espncdn.com/i/teamlogos/soccer/500/3812.png",
    "huracan": "https://a.espncdn.com/i/teamlogos/soccer/500/11.png",
    "independiente rivadavia": "https://a.espncdn.com/i/teamlogos/soccer/500/19899.png",
    "independiente": "https://a.espncdn.com/i/teamlogos/soccer/500/10.png",
    "instituto": "https://a.espncdn.com/i/teamlogos/soccer/500/10258.png",
    "lanus": "https://a.espncdn.com/i/teamlogos/soccer/500/12.png",
    "newell": "https://a.espncdn.com/i/teamlogos/soccer/500/13.png",
    "platense": "https://a.espncdn.com/i/teamlogos/soccer/500/10260.png",
    "racing": "https://a.espncdn.com/i/teamlogos/soccer/500/15.png",
    "river": "https://a.espncdn.com/i/teamlogos/soccer/500/16.png",
    "rosario central": "https://a.espncdn.com/i/teamlogos/soccer/500/17.png",
    "san lorenzo": "https://a.espncdn.com/i/teamlogos/soccer/500/18.png",
    "sarmiento": "https://a.espncdn.com/i/teamlogos/soccer/500/10233.png",
    "talleres": "https://a.espncdn.com/i/teamlogos/soccer/500/3814.png",
    "tigre": "https://a.espncdn.com/i/teamlogos/soccer/500/20.png",
    "union": "https://a.espncdn.com/i/teamlogos/soccer/500/19.png",
    "velez": "https://a.espncdn.com/i/teamlogos/soccer/500/21.png",
    "aldosivi": "https://a.espncdn.com/i/teamlogos/soccer/500/10257.png",
    "san martin": "https://a.espncdn.com/i/teamlogos/soccer/500/3811.png"
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
    
    if "independiente riv" in norm or "rivadavia" in norm: clave = "independiente rivadavia"
    elif "independiente" in norm: clave = "independiente"
    elif "central cordoba" in norm or "sde" in norm or "santiago" in norm: clave = "central cordoba"
    elif "rosario central" in norm: clave = "rosario central"
    elif "gimnasia" in norm: clave = "gimnasia lp"
    elif "estudiantes" in norm: clave = "estudiantes lp"
    elif "argentinos" in norm: clave = "argentinos"
    elif "tucuman" in norm: clave = "atletico tucuman"
    elif "barracas" in norm: clave = "barracas"
    elif "boca" in norm: clave = "boca"
    elif "defensa" in norm: clave = "defensa"
    elif "riestra" in norm: clave = "riestra"
    elif "godoy cruz" in norm: clave = "godoy cruz"
    elif "huracan" in norm: clave = "huracan"
    elif "instituto" in norm: clave = "instituto"
    elif "lanus" in norm: clave = "lanus"
    elif "newell" in norm: clave = "newell"
    elif "platense" in norm: clave = "platense"
    elif "racing" in norm: clave = "racing"
    elif "river" in norm: clave = "river"
    elif "san lorenzo" in norm: clave = "san lorenzo"
    elif "sarmiento" in norm: clave = "sarmiento"
    elif "talleres" in norm: clave = "talleres"
    elif "tigre" in norm: clave = "tigre"
    elif "union" in norm: clave = "union"
    elif "velez" in norm: clave = "velez"
    elif "belgrano" in norm: clave = "belgrano"
    elif "banfield" in norm: clave = "banfield"
    elif "aldosivi" in norm: clave = "aldosivi"
    elif "san martin" in norm or "san juan" in norm: clave = "san martin"
        
    return ESCUDOS_ESPN.get(clave, LOGO_LPF)

# 3. Encabezado principal
col_lpf, col_title = st.columns([1, 6])
with col_lpf:
    st.image(LOGO_LPF, width=80)
with col_title:
    st.title("Tabla Anual - Liga Profesional de Fútbol")
    st.caption("Estadísticas oficiales y predictor de partidos en tiempo real")

st.markdown("---")

# 4. Carga de datos y Tabla
CSV_PATH = "datos_procesados.csv"

if not os.path.exists(CSV_PATH):
    st.error(f"No se encontró el archivo '{CSV_PATH}'.")
else:
    df = pd.read_csv(CSV_PATH)
    df.columns = df.columns.str.strip()
    
    if "Equipo" in df.columns:
        # Limpiar nombres para visualizarlos bien
        df["Equipo"] = df["Equipo"].astype(str).apply(lambda x: re.sub(r'\[.*?\]', '', x).strip())
        
        # Insertar URL del escudo como primera columna
        df.insert(0, "Escudo", df["Equipo"].apply(obtener_url_escudo))
        
        columnas_deseadas = ["Escudo", "Equipo", "Puntos", "PJ", "PG", "PE", "PP", "GF", "GC"]
        cols_existentes = [c for c in columnas_deseadas if c in df.columns]
        otras_cols = [c for c in df.columns if c not in cols_existentes]
        df_mostrar = df[cols_existentes + otras_cols].copy()
        
        # Renderizamos la tabla nativa de Streamlit, configurando explícitamente "Escudo" como imagen
        st.dataframe(
            df_mostrar,
            hide_index=True,
            column_config={
                "Escudo": st.column_config.ImageColumn(
                    "🛡️", 
                    help="Escudo oficial del equipo"
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
                url_local = obtener_url_escudo(local)
                url_vis = obtener_url_escudo(visitante)

                c_loc, c_vs, c_vis = st.columns([2, 1, 2])
                with c_loc:
                    st.image(url_local, width=90)
                    st.markdown(f"### **{local}**")
                with c_vs:
                    st.markdown("<h2 style='text-align: center; margin-top: 20px;'>VS</h2>", unsafe_allow_html=True)
                with c_vis:
                    st.image(url_vis, width=90)
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
