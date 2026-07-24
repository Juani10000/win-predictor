import streamlit as st
import pandas as pd
import unicodedata
import os
import re
import base64

# -----------------------------------------------------------------------------
# 1. Configuración de la página
# -----------------------------------------------------------------------------
st.set_page_config(page_title="Tabla Anual - LPF", layout="wide")
st.title("⚽ Tabla Anual - Liga Profesional")

# -----------------------------------------------------------------------------
# 2. Detección de carpetas y archivos de imágenes
# -----------------------------------------------------------------------------
DIRECTORIO_APP = os.path.dirname(os.path.abspath(__file__))
RUTA_CSV = os.path.join(DIRECTORIO_APP, "datos_procesados.csv")

def obtener_todas_las_imagenes():
    """Busca todas las imágenes en el directorio actual y subcarpetas."""
    extensiones = ('.png', '.jpg', '.jpeg', '.webp')
    imagenes = {}
    
    for raiz, _, archivos in os.walk(DIRECTORIO_APP):
        for archivo in archivos:
            if archivo.lower().endswith(extensiones):
                ruta_completa = os.path.join(raiz, archivo)
                # Guardamos la ruta asociada a su nombre
                imagenes[archivo] = ruta_completa
    return imagenes

DICCIONARIO_IMAGENES = obtener_todas_las_imagenes()

# Panel desplegable de diagnóstico para ver qué detecta
with st.expander("🛠️ Panel de Control de Escudos (Click para verificar)"):
    if DICCIONARIO_IMAGENES:
        st.success(f"✅ Se encontraron {len(DICCIONARIO_IMAGENES)} imagen(es) en tu proyecto:")
        for nombre_arch, ruta_c in DICCIONARIO_IMAGENES.items():
            st.write(f"- `{nombre_arch}` ➔ `{ruta_c}`")
    else:
        st.warning("⚠️ No se encontró ninguna imagen (.png, .jpg) en el proyecto.")

st.markdown("---")

# -----------------------------------------------------------------------------
# 3. Funciones de limpieza y matcheo de escudos
# -----------------------------------------------------------------------------
def limpiar_texto(texto):
    """Limpia tildes, corchetes, extensiones y pasa todo a minúsculas limpia."""
    txt = str(texto)
    # Quitar corchetes o paréntesis del CSV si los hay
    txt = re.sub(r'\[.*?\]|\(.*?\)', '', txt).strip()
    # Quitar extensiones de imagen si vienen pegadas (.png, .jpg, etc.)
    txt = re.sub(r'\.(png|jpg|jpeg|webp)', '', txt, flags=re.IGNORECASE)
    # Sacar tildes
    txt = unicodedata.normalize('NFD', txt).encode('ascii', 'ignore').decode("utf-8").lower()
    # Dejar solo letras y números
    return re.sub(r'[^a-z0-9]', '', txt)

def encontrar_ruta_escudo(nombre_equipo):
    """Busca cuál de las imágenes guardadas coincide mejor con el equipo."""
    if not DICCIONARIO_IMAGENES:
        return None
        
    equipo_clean = limpiar_texto(nombre_equipo)
    
    # 1. Intentar coincidencia exacta o por subcadena
    for nombre_archivo, ruta_completa in DICCIONARIO_IMAGENES.items():
        archivo_clean = limpiar_texto(nombre_archivo)
        
        if not archivo_clean:
            continue
            
        # Si 'boca' está en 'bocajuniors' o viceversa
        if archivo_clean in equipo_clean or equipo_clean in archivo_clean:
            return ruta_completa
            
    return None

def imagen_a_base64(ruta_imagen):
    """Convierte la foto a Base64 para que la tabla de Streamlit la muestre sí o sí."""
    if ruta_imagen and os.path.exists(ruta_imagen):
        try:
            with open(ruta_imagen, "rb") as img_file:
                encoded = base64.b64encode(img_file.read()).decode("utf-8")
            ext = os.path.splitext(ruta_imagen)[1].lower().replace(".", "")
            mime = "image/jpeg" if ext in ["jpg", "jpeg"] else "image/png"
            return f"data:{mime};base64,{encoded}"
        except Exception:
            return None
    return None

# -----------------------------------------------------------------------------
# 4. Carga de Datos y Visualización de la Tabla
# -----------------------------------------------------------------------------
if not os.path.exists(RUTA_CSV):
    st.error(f"⚠️ No se encontró el archivo '{RUTA_CSV}'. Verificá que esté en la misma carpeta que 'app.py'.")
else:
    df = pd.read_csv(RUTA_CSV)
    
    # Limpiar nombres de los equipos
    df["Equipo"] = df["Equipo"].astype(str).apply(lambda x: re.sub(r'\[.*?\]|\(.*?\)', '', x).strip())
    
    # Asignar ruta de escudo y convertir a Base64 para la tabla
    df["Ruta_Local"] = df["Equipo"].apply(encontrar_ruta_escudo)
    df["Escudo"] = df["Ruta_Local"].apply(imagen_a_base64)
    
    # Reordenar columnas para que Escudo aparezca al principio
    cols = df.columns.tolist()
    if "Escudo" in cols:
        cols.insert(0, cols.pop(cols.index("Escudo")))
        df_mostrar = df[cols].drop(columns=["Ruta_Local"], errors="ignore")
    else:
        df_mostrar = df

    st.subheader("📊 Tabla de Posiciones")
    
    st.dataframe(
        df_mostrar,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Escudo": st.column_config.ImageColumn("🛡️", help="Escudo del equipo")
        }
    )
    st.markdown("---")

    # -----------------------------------------------------------------------------
    # 5. Predictor de Enfrentamientos
    # -----------------------------------------------------------------------------
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
            ruta_loc = encontrar_ruta_escudo(local)
            ruta_vis = encontrar_ruta_escudo(visitante)

            c_loc, c_vs, c_vis = st.columns([2, 1, 2])
            
            with c_loc:
                if ruta_loc and os.path.exists(ruta_loc):
                    st.image(ruta_loc, width=120)
                else:
                    st.caption("🛡️ (Sin escudo)")
                st.markdown(f"### **{local}**")
                
            with c_vs:
                st.markdown("<h1 style='text-align: center; margin-top: 20px;'>VS</h1>", unsafe_allow_html=True)
                
            with c_vis:
                if ruta_vis and os.path.exists(ruta_vis):
                    st.image(ruta_vis, width=120)
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

            # Ventaja del local (+15%)
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
