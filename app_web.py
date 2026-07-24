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

# 2. BÚSQUEDA INTELIGENTE DE CARPETAS
DIRECTORIO_SCRIPT = os.path.dirname(os.path.abspath(__file__))
DIRECTORIO_TERMINAL = os.getcwd()

# Python va a buscar en todos estos lugares al mismo tiempo
carpetas_posibles = [
    DIRECTORIO_SCRIPT,
    DIRECTORIO_TERMINAL,
    os.path.join(DIRECTORIO_SCRIPT, "escudos"),
    os.path.join(DIRECTORIO_SCRIPT, "Escudos"),
    os.path.join(DIRECTORIO_TERMINAL, "escudos"),
    os.path.join(DIRECTORIO_TERMINAL, "Escudos")
]

todas_las_imagenes = {}
for carpeta in set(carpetas_posibles):
    if os.path.exists(carpeta):
        try:
            for archivo in os.listdir(carpeta):
                if archivo.lower().endswith(('.png', '.jpg', '.jpeg')):
                    if archivo not in todas_las_imagenes:
                        todas_las_imagenes[archivo] = os.path.join(carpeta, archivo)
        except Exception:
            pass

# Funciones de limpieza
def limpiar_texto(texto):
    txt = str(texto).lower()
    txt = re.sub(r'\.(png|jpg|jpeg)', '', txt) 
    txt = unicodedata.normalize('NFD', txt).encode('ascii', 'ignore').decode("utf-8")
    return re.sub(r'[^a-z0-9]', '', txt).strip()

def buscar_imagen(nombre_equipo):
    """Busca en el diccionario de imágenes que armamos recién"""
    equipo_limpio = limpiar_texto(nombre_equipo)
    
    for nombre_archivo, ruta_completa in todas_las_imagenes.items():
        archivo_limpio = limpiar_texto(nombre_archivo)
        if archivo_limpio in equipo_limpio or equipo_limpio in archivo_limpio:
            return ruta_completa
    return None

def codificar_imagen(ruta):
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
ruta_csv = os.path.join(DIRECTORIO_SCRIPT, "datos_procesados.csv")
if not os.path.exists(ruta_csv):
    ruta_csv = os.path.join(DIRECTORIO_TERMINAL, "datos_procesados.csv")

if not os.path.exists(ruta_csv):
    st.error(f"⚠️ No se encontró 'datos_procesados.csv'.")
else:
    df = pd.read_csv(ruta_csv)
    df["Equipo"] = df["Equipo"].astype(str).apply(lambda x: re.sub(r'\[.*?\]|\(.*?\)', '', x).strip())
    
    # Asignar Escudos
    df["Ruta_Local"] = df["Equipo"].apply(buscar_imagen)
    df["Escudo"] = df["Ruta_Local"].apply(codificar_imagen)
    
    # Ordenar columnas
    cols = df.columns.tolist()
    if "Escudo" in cols:
        cols.insert(0, cols.pop(cols.index("Escudo")))
        df_mostrar = df[cols].drop(columns=["Ruta_Local"], errors="ignore")
    else:
        df_mostrar = df

    # Diagnóstico (Te va a decir exactamente qué encontró)
    if len(todas_las_imagenes) > 0:
        st.success(f"✅ ¡Encontré {len(todas_las_imagenes)} imágenes en tu computadora!")
        with st.expander("Ver lista de imágenes encontradas"):
            for img in todas_las_imagenes.values():
                st.code(img)
    else:
        st.error("❌ No detecté ningún archivo PNG o JPG en las carpetas del proyecto.")

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
            ruta_loc = buscar_imagen(local)
            ruta_vis = buscar_imagen(visitante)

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

            # Matemáticas
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
