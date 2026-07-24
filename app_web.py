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

# 2. CDN de Escudos Oficiales (FotMob CDN)
LOGO_LPF = "https://images.fotmob.com/image_resources/logo/leaguelogo/112.png"

ESCUDOS_EQUIPOS = {
    "argentinos": "https://images.fotmob.com/image_resources/logo/teamlogo/10236.png",
    "atletico tucuman": "https://images.fotmob.com/image_resources/logo/teamlogo/10253.png",
    "banfield": "https://images.fotmob.com/image_resources/logo/teamlogo/10249.png",
    "barracas": "https://images.fotmob.com/image_resources/logo/teamlogo/10260.png",
    "belgrano": "https://images.fotmob.com/image_resources/logo/teamlogo/10250.png",
    "boca": "https://images.fotmob.com/image_resources/logo/teamlogo/10243.png",
    "central cordoba": "https://images.fotmob.com/image_resources/logo/teamlogo/10258.png",
    "defensa": "https://images.fotmob.com/image_resources/logo/teamlogo/10252.png",
    "riestra": "https://images.fotmob.com/image_resources/logo/teamlogo/10262.png",
    "estudiantes lp": "https://images.fotmob.com/image_resources/logo/teamlogo/10241.png",
    "gimnasia lp": "https://images.fotmob.com/image_resources/logo/teamlogo/10240.png",
    "godoy cruz": "https://images.fotmob.com/image_resources/logo/teamlogo/10254.png",
    "huracan": "https://images.fotmob.com/image_resources/logo/teamlogo/10239.png",
    "independiente rivadavia": "https://images.fotmob.com/image_resources/logo/teamlogo/10263.png",
    "independiente": "https://images.fotmob.com/image_resources/logo/teamlogo/10242.png",
    "instituto": "https://images.fotmob.com/image_resources/logo/teamlogo/10261.png",
    "lanus": "https://images.fotmob.com/image_resources/logo/teamlogo/10248.png",
    "newell": "https://images.fotmob.com/image_resources/logo/teamlogo/10237.png",
    "platense": "https://images.fotmob.com/image_resources/logo/teamlogo/10257.png",
    "racing": "https://images.fotmob.com/image_resources/logo/teamlogo/10245.png",
    "river": "https://images.fotmob.com/image_resources/logo/teamlogo/10244.png",
    "rosario central": "https://images.fotmob.com/image_resources/logo/teamlogo/10238.png",
    "san lorenzo": "https://images.fotmob.com/image_resources/logo/teamlogo/10246.png",
    "sarmiento": "https://images.fotmob.com/image_resources/logo/teamlogo/10259.png",
    "talleres": "https://images.fotmob.com/image_resources/logo/teamlogo/10251.png",
    "tigre": "https://images.fotmob.com/image_resources/logo/teamlogo/10256.png",
    "union": "https://images.fotmob.com/image_resources/logo/teamlogo/10255.png",
    "velez": "https://images.fotmob.com/image_resources/logo/teamlogo/10247.png",
    "aldosivi": "https://images.fotmob.com/image_resources/logo/teamlogo/10265.png",
    "san martin sj": "https://images.fotmob.com/image_resources/logo/teamlogo/10266.png"
}

def normalizar_texto(texto):
    if not isinstance(texto, str):
        return ""
    texto = re.sub(r'\[.*?\]', '', texto)
    texto = unicodedata.normalize('NFD', texto).encode('ascii', 'ignore').decode("utf-8")
    return texto.lower().strip()

def obtener_escudo(nombre_equipo):
    norm = normalizar_texto(nombre_equipo)
    
    if "independiente riv" in norm or "rivadavia" in norm:
        return ESCUDOS_EQUIPOS["independiente rivadavia"]
    if "independiente" in norm:
        return ESCUDOS_EQUIPOS["independiente"]
    if "central cordoba" in norm or "sde" in norm or "santiago" in norm:
        return ESCUDOS_EQUIPOS["central cordoba"]
    if "rosario central" in norm:
        return ESCUDOS_EQUIPOS["rosario central"]
    if "gimnasia" in norm and "mendoza" in norm:
        return "https://images.fotmob.com/image_resources/logo/teamlogo/10264.png"
    if "gimnasia" in norm:
        return ESCUDOS_EQUIPOS["gimnasia lp"]
    if "estudiantes" in norm and ("rc" in norm or "cuarto" in norm):
        return "https://images.fotmob.com/image_resources/logo/teamlogo/10265.png"
    if "estudiantes" in norm:
        return ESCUDOS_EQUIPOS["estudiantes lp"]
        
    for clave, url in ESCUDOS_EQUIPOS.items():
        if clave in norm:
            return url
            
    return LOGO_LPF

# 3. Encabezado principal con el Logo Oficial de la LPF
col_lpf, col_title = st.columns([1, 6])
with col_lpf:
    st.image(LOGO_LPF, width=80)
with col_title:
    st.title("Tabla Anual - Liga Profesional de Fútbol")
    st.caption("Estadísticas oficiales y predictor de partidos en tiempo real")

st.markdown("---")

# 4. Carga de datos
CSV_PATH = "datos_procesados.csv"

if not os.path.exists(CSV_PATH):
    st.error(f"No se encontró el archivo '{CSV_PATH}'. Asegúrate de ejecutar primero tu scraper/procesador de datos.")
else:
    df = pd.read_csv(CSV_PATH)
    
    # Limpieza de nombres de columna
    df.columns = df.columns.str.strip()
    
    if "Equipo" in df.columns:
        df["Equipo"] = df["Equipo"].astype(str).apply(lambda x: re.sub(r'\[.*?\]', '', x).strip())
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

        # 5. Sección del Predictor de Partidos
        st.subheader("🔮 Predictor de Enfrentamientos")
        lista_equipos = sorted(df["Equipo"].unique())

        if len(lista_equipos) >= 2:
            col1, col2 = st.columns(2)
            with col1:
                local = st.selectbox("Equipo Local", lista_equipos, index=0)
            with col2:
                visitante = st.selectbox("Equipo Visitante", lista_equipos, index=min(1, len(lista_equipos)-1))

            if local == visitante:
                st.warning("Selecciona dos equipos distintos para predecir el partido.")
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
