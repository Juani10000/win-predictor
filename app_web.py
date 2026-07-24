import streamlit as st
import pandas as pd
import unicodedata
import os
import re
import base64

# 1. Configuración
st.set_page_config(page_title="Tabla Anual - LPF", layout="wide")
st.title("⚽ Tabla Anual - Liga Profesional")
st.markdown("---")

# 2. Forzamos a buscar en la carpeta actual donde abriste la terminal
DIRECTORIO_ACTUAL = os.getcwd()
RUTA_CSV = os.path.join(DIRECTORIO_ACTUAL, "datos_procesados.csv")

# Funciones de limpieza
def limpiar_texto(texto):
    txt = str(texto).lower()
    txt = re.sub(r'\.(png|jpg|jpeg)', '', txt) 
    txt = unicodedata.normalize('NFD', txt).encode('ascii', 'ignore').decode("utf-8")
    return re.sub(r'[^a-z0-9]', '', txt).strip()

def buscar_imagen_local(nombre_equipo):
    """Busca el PNG suelto en la carpeta donde estás ejecutando Streamlit"""
    equipo_limpio = limpiar_texto(nombre_equipo)
    
    try:
        archivos = os.listdir(DIRECTORIO_ACTUAL)
    except:
        return None

    for archivo in archivos:
        if archivo.lower().endswith(('.png', '.jpg', '.jpeg')):
            archivo_limpio = limpiar_texto(archivo)
            if archivo_limpio in equipo_limpio or equipo_limpio in archivo_limpio:
                return os.path.join(DIRECTORIO_ACTUAL, archivo)
    return None

def codificar_imagen(ruta):
    """Convierte la imagen a texto para que la tabla web no la rechace"""
    if ruta and os.path.exists(ruta):
        try:
            with open(ruta, "rb") as f:
                data = f.read()
                b64 = base64.b64encode(data).decode("utf-8")
                ext = os.path.splitext(ruta)[1].lower().replace('.', '')
                mime = "image/jpeg" if ext in ["jpg", "jpeg"] else "image/png"
                return f"data:{mime};base64,{b64}"
        except:
            return None
    return None

# 3. Carga de Datos y Tabla
if not os.path.exists(RUTA_CSV):
    st.error(f"⚠️ No se encontró '{RUTA_CSV}' en la carpeta actual ({DIRECTORIO_ACTUAL}).")
else:
    df = pd.read_csv(RUTA_CSV)
    df["Equipo"] = df["Equipo"].astype(str).apply(lambda x: re.sub(r'\[.*?\]|\(.*?\)', '', x).strip())
    
    # Encontrar las rutas y convertirlas a Base64
    df["Ruta_Local"] = df["Equipo"].apply(buscar_imagen_local)
    df["Escudo"] = df["Ruta_Local"].apply(codificar_imagen)
    
    # Ordenar columnas
    cols = df.columns.tolist()
    if "Escudo" in cols:
        cols.insert(0, cols.pop(cols.index("Escudo")))
        df_mostrar = df[cols].drop(columns=["Ruta_Local"], errors="ignore")
    else:
        df_mostrar = df

    # Mostrar Diagnóstico oculto para ver qué encontró
    imagenes_encontradas = df["Ruta_Local"].dropna().unique()
    if len(imagenes_encontradas) > 0:
        st.success(f"✅ ¡Éxito! Se detectaron {len(imagenes_encontradas)} escudos en: {DIRECTORIO_ACTUAL}")
    else:
        st.warning(f"⚠️ No se detectó ningún escudo. Revisá que los PNG estén sueltos en: {DIRECTORIO_ACTUAL}")

    st.subheader("📊 Tabla de Posiciones")
    st.dataframe(
        df_mostrar,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Escudo": st.column_config.ImageColumn("🛡️")
        }
    )
    st.markdown("---")

    # 4. Predictor
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
            ruta_loc = buscar_imagen_local(local)
            ruta_vis = buscar_imagen_local(visitante)

            c_loc, c_vs, c_vis = st.columns([2, 1, 2])
            
            with c_loc:
                if ruta_loc:
                    st.image(ruta_loc, width=120)
                else:
                    st.caption("🛡️ Sin imagen")
                st.markdown(f"### **{local}**")
                
            with c_vs:
                st.markdown("<h1 style='text-align: center; margin-top: 20px;'>VS</h1>", unsafe_allow_html=True)
                
            with c_vis:
                if ruta_vis:
                    st.image(ruta_vis, width=120)
                else:
                    st.caption("🛡️ Sin imagen")
                st.markdown(f"### **{visitante}**")

            # Cálculo Matemático
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
