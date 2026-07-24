import streamlit as st
import pandas as pd
import os
import re

st.set_page_config(page_title="Win Predictor - LPF", page_icon="⚽", layout="centered")

st.title("⚽ Win Predictor - Fútbol Argentino")

@st.cache_data(ttl=60)
def cargar_datos():
    if os.path.exists("datos_procesados.csv"):
        return pd.read_csv("datos_procesados.csv")
    return None

df = cargar_datos()

if df is None or df.empty:
    st.error("❌ No se encontraron datos procesados. Por favor ejecutá la actualización en GitHub.")
else:
    # ---------------------------------------------------------
    # DICCIONARIO DE ESCUDOS OFICIALES DE ESPN (CDN ultra rápida y sin bloqueos CORS)
    # ---------------------------------------------------------
    escudos_espn = {
        "Independiente Rivadavia": "https://a.espncdn.com/i/teamlogos/soccer/500/18881.png",
        "Argentinos Juniors": "https://a.espncdn.com/i/teamlogos/soccer/500/1.png",
        "Estudiantes (LP)": "https://a.espncdn.com/i/teamlogos/soccer/500/8.png",
        "Boca Juniors": "https://a.espncdn.com/i/teamlogos/soccer/500/3.png",
        "River Plate": "https://a.espncdn.com/i/teamlogos/soccer/500/16.png",
        "Belgrano": "https://a.espncdn.com/i/teamlogos/soccer/500/240.png",
        "Vélez Sarsfield": "https://a.espncdn.com/i/teamlogos/soccer/500/21.png",
        "Rosario Central": "https://a.espncdn.com/i/teamlogos/soccer/500/17.png",
        "Talleres (C)": "https://a.espncdn.com/i/teamlogos/soccer/500/245.png",
        "Gimnasia (LP)": "https://a.espncdn.com/i/teamlogos/soccer/500/9.png",
        "Independiente": "https://a.espncdn.com/i/teamlogos/soccer/500/10.png",
        "Lanús": "https://a.espncdn.com/i/teamlogos/soccer/500/12.png",
        "Huracán": "https://a.espncdn.com/i/teamlogos/soccer/500/13.png",
        "San Lorenzo": "https://a.espncdn.com/i/teamlogos/soccer/500/18.png",
        "Unión": "https://a.espncdn.com/i/teamlogos/soccer/500/20.png",
        "Racing Club": "https://a.espncdn.com/i/teamlogos/soccer/500/15.png",
        "Instituto": "https://a.espncdn.com/i/teamlogos/soccer/500/242.png",
        "Barracas Central": "https://a.espncdn.com/i/teamlogos/soccer/500/18873.png",
        "Tigre": "https://a.espncdn.com/i/teamlogos/soccer/500/19.png",
        "Defensa y Justicia": "https://a.espncdn.com/i/teamlogos/soccer/500/18874.png",
        "Sarmiento (J)": "https://a.espncdn.com/i/teamlogos/soccer/500/18878.png",
        "Gimnasia (Mendoza)": "https://a.espncdn.com/i/teamlogos/soccer/500/18880.png",
        "Banfield": "https://a.espncdn.com/i/teamlogos/soccer/500/2.png",
        "Platense": "https://a.espncdn.com/i/teamlogos/soccer/500/14.png",
        "Central Córdoba (SdE)": "https://a.espncdn.com/i/teamlogos/soccer/500/18875.png",
        "Newell's Old Boys": "https://a.espncdn.com/i/teamlogos/soccer/500/11.png",
        "Atlético Tucumán": "https://a.espncdn.com/i/teamlogos/soccer/500/18872.png",
        "Deportivo Riestra": "https://a.espncdn.com/i/teamlogos/soccer/500/19912.png",
        "Aldosivi": "https://a.espncdn.com/i/teamlogos/soccer/500/18871.png",
        "Estudiantes (RC)": "https://a.espncdn.com/i/teamlogos/soccer/500/18877.png"
    }

    escudo_defecto = "https://a.espncdn.com/i/teamlogos/soccer/500/default.png"

    # Función flexible que limpia las notas al pie de Wikipedia y vincula el escudo correcto
    def obtener_escudo(nombre_bruto):
        if not isinstance(nombre_bruto, str):
            return escudo_defecto
        
        # Elimina notas entre corchetes como [n. 1], [1], etc.
        nombre = re.sub(r'\[.*?\]', '', nombre_bruto).strip()
        
        if nombre in escudos_espn:
            return escudos_espn[nombre]
            
        nom_lower = nombre.lower()
        if "gimnasia" in nom_lower and ("lp" in nom_lower or "esgrima" in nom_lower):
            return escudos_espn["Gimnasia (LP)"]
        if "gimnasia" in nom_lower and "mendoza" in nom_lower:
            return escudos_espn["Gimnasia (Mendoza)"]
        if "estudiantes" in nom_lower and "lp" in nom_lower:
            return escudos_espn["Estudiantes (LP)"]
        if "estudiantes" in nom_lower and "rc" in nom_lower:
            return escudos_espn["Estudiantes (RC)"]
        if "talleres" in nom_lower:
            return escudos_espn["Talleres (C)"]
        if "belgrano" in nom_lower:
            return escudos_espn["Belgrano"]
        if "sarmiento" in nom_lower:
            return escudos_espn["Sarmiento (J)"]
        if "central c" in nom_lower or "cordoba" in nom_lower:
            return escudos_espn["Central Córdoba (SdE)"]
        if "newell" in nom_lower:
            return escudos_espn["Newell's Old Boys"]
        if "riestra" in nom_lower:
            return escudos_espn["Deportivo Riestra"]
        if "tucuman" in nom_lower or "tucumán" in nom_lower:
            return escudos_espn["Atlético Tucumán"]
        if "independiente riv" in nom_lower:
            return escudos_espn["Independiente Rivadavia"]
        if "independiente" in nom_lower:
            return escudos_espn["Independiente"]
        if "barracas" in nom_lower:
            return escudos_espn["Barracas Central"]
            
        for key, url in escudos_espn.items():
            if key.lower() in nom_lower or nom_lower in key.lower():
                return url
                
        return escudo_defecto

    # ---------------------------------------------------------
    # SECCIÓN 1: PREDICCIÓN DE PARTIDOS
    # ---------------------------------------------------------
    st.markdown("### 🔮 Predicción de Partido")
    st.caption("Cálculo de probabilidades basado en el rendimiento actual.")
    
    lista_equipos = sorted(df["Equipo"].astype(str).unique())
    
    col1, col2 = st.columns(2)
    with col1:
        local = st.selectbox("Seleccionar Local", lista_equipos, index=0)
    with col2:
        idx_vis = 1 if len(lista_equipos) > 1 else 0
        visitante = st.selectbox("Seleccionar Visitante", lista_equipos, index=idx_vis)

    if local == visitante:
        st.warning("⚠️ Elegí dos equipos distintos.")
    else:
        row_loc = df[df["Equipo"] == local].iloc[0]
        row_vis = df[df["Equipo"] == visitante].iloc[0]

        pts_loc = float(row_loc.get("Puntos", 0))
        pj_loc = max(float(row_loc.get("PJ", 1)), 1.0)
        rend_loc = pts_loc / (pj_loc * 3.0)

        pts_vis = float(row_vis.get("Puntos", 0))
        pj_vis = max(float(row_vis.get("PJ", 1)), 1.0)
        rend_vis = pts_vis / (pj_vis * 3.0)

        p_loc = rend_loc + 0.10
        p_vis = rend_vis
        total = p_loc + p_vis + 0.05

        prob_local = round((p_loc / total) * 100, 1)
        prob_vis = round((p_vis / total) * 100, 1)
        prob_empate = round(100.0 - prob_local - prob_vis, 1)

        st.markdown(f"#### 📊 Resultados: **{local}** vs **{visitante}**")
        
        m1, m2, m3 = st.columns(3)
        m1.metric(f"Gana {local}", f"{prob_local}%")
        m2.metric("Empate", f"{prob_empate}%")
        m3.metric(f"Gana {visitante}", f"{prob_vis}%")

    st.markdown("---")
    
    # ---------------------------------------------------------
    # SECCIÓN 2: TABLA ANUAL CON ESCUDOS
    # ---------------------------------------------------------
    st.subheader("⚽ Tabla Anual - Liga Profesional de Fútbol")

    cols_basicas = ["Equipo", "Puntos", "PJ", "PG", "PE", "PP", "GF", "GC"]
    cols_existentes = [c for c in cols_basicas if c in df.columns]
    
    # 1. Copiamos el DataFrame con las columnas existentes
    df_tabla = df[cols_existentes].copy()
    
    # 2. Asignamos el escudo DIRECTAMENTE a la fila de cada equipo (Row-level mapping)
    df_tabla["Escudo"] = df_tabla["Equipo"].apply(obtener_escudo)
    
    # 3. Ordenamos por Puntos (el escudo se moverá automáticamente junto a su equipo)
    df_tabla = df_tabla.sort_values(by="Puntos", ascending=False).reset_index(drop=True)
    
    # 4. Reordenamos para que 'Escudo' sea la primera columna
    columnas_ordenadas = ["Escudo"] + [c for c in df_tabla.columns if c != "Escudo"]
    df_tabla = df_tabla[columnas_ordenadas]

    # 5. Renderizado seguro con ImageColumn
    st.dataframe(
        df_tabla,
        hide_index=True, 
        column_config={
            "Escudo": st.column_config.ImageColumn("🛡️", width="small"),
            "Equipo": st.column_config.TextColumn("Equipo", width="medium"),
        },
        use_container_width=True
    )
