import streamlit as st
import pandas as pd
import unicodedata
import re
import os
import base64

# 1. Configuración de la página Streamlit
st.set_page_config(
    page_title="Tabla Anual - LPF Argentina",
    page_icon="⚽",
    layout="wide"
)

# Función clave para que Streamlit lea imágenes locales en la tabla
def get_image_base64(ruta_imagen):
    if os.path.exists(ruta_imagen):
        with open(ruta_imagen, "rb") as f:
            data = f.read()
        return f"data:image/png;base64,{base64.b64encode(data).decode()}"
    return "" # Si no encuentra la imagen, devuelve vacío

# 2. Diccionario apuntando a tus archivos locales
LOGO_LPF = get_image_base64("escudos/lpf_logo.png")

ESCUDOS_LOCALES = {
    "argentinos": "escudos/argentinos.png",
    "atletico tucuman": "escudos/atletico_tucuman.png",
    "banfield": "escudos/banfield.png",
    "barracas": "escudos/barracas.png",
    "belgrano": "escudos/belgrano.png",
    "boca": "escudos/boca.png",
    "central cordoba": "escudos/central_cordoba.png",
    "defensa": "escudos/defensa.png",
    "riestra": "escudos/riestra.png",
    "estudiantes lp": "escudos/estudiantes_lp.png",
    "gimnasia lp": "escudos/gimnasia_lp.png",
    "godoy cruz": "escudos/godoy_cruz.png",
    "huracan": "escudos/huracan.png",
    "independiente rivadavia": "escudos/independiente_rivadavia.png",
    "independiente": "escudos/independiente.png",
    "instituto": "escudos/instituto.png",
    "lanus": "escudos/lanus.png",
    "newell": "escudos/newell.png",
    "platense": "escudos/platense.png",
    "racing": "escudos/racing.png",
    "river": "escudos/river.png",
    "rosario central": "escudos/rosario_central.png",
    "san lorenzo": "escudos/san_lorenzo.png",
    "sarmiento": "escudos/sarmiento.png",
    "talleres": "escudos/talleres.png",
    "tigre": "escudos/tigre.png",
    "union": "escudos/union.png",
    "velez": "escudos/velez.png",
    "aldosivi": "escudos/aldosivi.png",
    "san martin sj": "escudos/san_martin_sj.png"
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
    ruta = ""
    
    if "independiente riv" in norm or "rivadavia" in norm:
        ruta = ESCUDOS_LOCALES["independiente rivadavia"]
    elif "independiente" in norm:
        ruta = ESCUDOS_LOCALES["independiente"]
    elif "central cordoba" in norm or "sde" in norm or "santiago" in norm:
        ruta = ESCUDOS_LOCALES["central cordoba"]
    elif "rosario central" in norm:
        ruta = ESCUDOS_LOCALES["rosario central"]
    elif "gimnasia" in norm:
        ruta = ESCUDOS_LOCALES["gimnasia lp"]
    elif "estudiantes" in norm:
        ruta = ESCUDOS_LOCALES["estudiantes lp"]
    elif "argentinos" in norm:
        ruta = ESCUDOS_LOCALES["argentinos"]
    elif "atletico tucuman" in norm or "tucuman" in norm:
        ruta = ESCUDOS_LOCALES["atletico tucuman"]
    elif "barracas" in norm:
        ruta = ESCUDOS_LOCALES["barracas"]
    elif "boca" in norm:
        ruta = ESCUDOS_LOCALES["boca"]
    elif "defensa" in norm:
        ruta = ESCUDOS_LOCALES["defensa"]
    elif "riestra" in norm:
        ruta = ESCUDOS_LOCALES["riestra"]
    elif "godoy cruz" in norm:
        ruta = ESCUDOS_LOCALES["godoy cruz"]
    elif "huracan" in norm:
        ruta = ESCUDOS_LOCALES["huracan"]
    elif "instituto" in norm:
        ruta = ESCUDOS_LOCALES["instituto"]
    elif "lanus" in norm:
        ruta = ESCUDOS_LOCALES["lanus"]
    elif "newell" in norm:
        ruta = ESCUDOS_LOCALES["newell"]
    elif "platense" in norm:
        ruta = ESCUDOS_LOCALES["platense"]
    elif "racing" in norm:
        ruta = ESCUDOS_LOCALES["racing"]
    elif "river" in norm:
        ruta = ESCUDOS_LOCALES["river"]
    elif "san lorenzo" in norm:
        ruta = ESCUDOS_LOCALES["san lorenzo"]
    elif "sarmiento" in norm:
        ruta = ESCUDOS_LOCALES["sarmiento"]
    elif "talleres" in norm:
        ruta = ESCUDOS_LOCALES["talleres"]
    elif "tigre" in norm:
        ruta = ESCUDOS_LOCALES["tigre"]
    elif "union" in norm:
        ruta = ESCUDOS_LOCALES["union"]
    elif "velez" in norm:
        ruta = ESCUDOS_LOCALES["velez"]
    elif "belgrano" in norm:
        ruta = ESCUDOS_LOCALES["belgrano"]
    elif "banfield" in norm:
        ruta = ESCUDOS_LOCALES["banfield"]
    elif "aldosivi" in norm:
        ruta = ESCUDOS_LOCALES["aldosivi"]
    elif "san martin" in norm:
        ruta = ESCUDOS_LOCALES["san martin sj"]
        
    # Si encontró la ruta, la convierte a base64 para que Streamlit la muestre sin internet
    if ruta:
        return get_image_base64(ruta)
    return LOGO_LPF

# 3. Encabezado principal
col_lpf, col_title = st.columns([1, 6])
with col_lpf:
    # Mostramos la imagen procesada en base64
    if LOGO_LPF:
        st.markdown(f'<img src="{LOGO_LPF}" width="80">', unsafe_allow_html=True)
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
                    if escudo_local:
                        st.markdown(f'<img src="{escudo_local}" width="90">', unsafe_allow_html=True)
                    st.markdown(f"### **{local}**")
                with c_vs:
                    st.markdown("<h2 style='text-align: center; margin-top: 20px;'>VS</h2>", unsafe_allow_html=True)
                with c_vis:
                    if escudo_vis:
                        st.markdown(f'<img src="{escudo_vis}" width="90">', unsafe_allow_html=True)
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
