import streamlit as st
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder

st.set_page_config(page_title="Win Predictor", page_icon="⚽")

st.title("⚽ Win Predictor - Liga Argentina")
st.write("Seleccioná los equipos para ver el pronóstico de la Inteligencia Artificial basado en sus rachas recientes.")

@st.cache_data
def preparar_modelo():
    # Intenta buscar el archivo procesado con las rachas
    try:
        df = pd.read_csv("datos/datos_procesados.csv")
    except FileNotFoundError:
        df = pd.read_csv("datos_procesados.csv")
    
    # Transformar nombres de equipos a números para la IA
    le = LabelEncoder()
    todos_los_equipos = pd.concat([df["Local"], df["Visitante"]]).unique()
    le.fit(todos_los_equipos)
    
    df["Local_Num"] = le.transform(df["Local"])
    df["Visita_Num"] = le.transform(df["Visitante"])
    
    # El Cerebro: Entrenar con Rachas Recientes
    X = df[["Local_Num", "Visita_Num", "Racha_Local", "Racha_Visita"]]
    y = df["Resultado"]
    
    modelo = RandomForestClassifier(n_estimators=100, random_state=42)
    modelo.fit(X, y)
    
    return df, modelo, le, todos_los_equipos

# Función para calcular los puntos en los últimos 5 partidos de un equipo
def puntos_ultimos_5(df, equipo):
    partidos = df[(df['Local'] == equipo) | (df['Visitante'] == equipo)].tail(5)
    puntos = 0
    for _, fila in partidos.iterrows():
        if fila['Local'] == equipo and fila['Resultado'] == 'L': puntos += 3
        elif fila['Visitante'] == equipo and fila['Resultado'] == 'V': puntos += 3
        elif fila['Resultado'] == 'E': puntos += 1
    return puntos

try:
    df, modelo, le, equipos_unicos = preparar_modelo()
    
    # --- INTERFAZ DE PREDICCIÓN ---
    col1, col2 = st.columns(2)
    with col1:
        local = st.selectbox("🏠 Equipo Local", sorted(equipos_unicos))
    with col2:
        visitante = st.selectbox("✈️ Equipo Visitante", sorted(equipos_unicos), index=1)

    if st.button("🔮 Predecir Partido"):
        if local == visitante:
            st.error("¡Elegí dos equipos distintos!")
        else:
            # Calcular cómo llegan al partido de hoy
            racha_l = puntos_ultimos_5(df, local)
            racha_v = puntos_ultimos_5(df, visitante)
            
            st.info(f"📊 **El Momento:** {local} sacó **{racha_l} pts** en sus últimos 5 partidos. {visitante} sacó **{racha_v} pts**.")
            
            loc_num = le.transform([local])[0]
            vis_num = le.transform([visitante])[0]
            
            datos_hoy = pd.DataFrame([[loc_num, vis_num, racha_l, racha_v]], 
                                     columns=["Local_Num", "Visita_Num", "Racha_Local", "Racha_Visita"])
            
            prediccion = modelo.predict(datos_hoy)[0]
            probabilidades = modelo.predict_proba(datos_hoy)[0]
            clases = list(modelo.classes_)
            
            prob_L = probabilidades[clases.index('L')] * 100
            prob_E = probabilidades[clases.index('E')] * 100
            prob_V = probabilidades[clases.index('V')] * 100
            
            st.subheader("📊 Resultados del Pronóstico")
            
            if prediccion == "L":
                st.success(f"Resultado más probable: 🏆 **Gana {local}**")
            elif prediccion == "V":
                st.success(f"Resultado más probable: 🏆 **Gana {visitante}**")
            else:
                st.warning("Resultado más probable: 🤝 **Empate**")
                
            st.write(f"**Probabilidades:** {local}: **{prob_L:.1f}%** | Empate: **{prob_E:.1f}%** | {visitante}: **{prob_V:.1f}%**")

    # --- TABLA DE POSICIONES REAL ---
    st.divider()
    st.subheader("🏆 Tabla de Posiciones Real")
    
    @st.cache_data(ttl=3600)  # Se actualiza sola cada 1 hora
    def obtener_tabla_real():
        try:
            # Descarga la tabla de posiciones real desde Wikipedia / Promiedos
            url = "https://es.wikipedia.org/wiki/Primera_Divisi%C3%B3n_de_Argentina"
            tablas = pd.read_html(url)
            # Busca la tabla que contenga Pos / Equipo / Pts
            for t in tablas:
                if any("Equipo" in col or "Club" in col for col in t.columns) and any("Pts" in col or "PTS" in col for col in t.columns):
                    return t
            return None
        except Exception:
            return None

    tabla_real = obtener_tabla_real()
    
    if tabla_real is not None:
        st.dataframe(tabla_real, use_container_width=True)
    else:
        # Si no puede conectarse a internet, muestra la tabla acumulada del CSV limpio
        st.write("*(Mostrando tabla calculada del archivo local)*")
        tabla = {}
        for _, fila in df.iterrows():
            loc, vis, res = fila["Local"], fila["Visitante"], fila["Resultado"]
            if loc not in tabla: tabla[loc] = {"Pts": 0, "PJ": 0}
            if vis not in tabla: tabla[vis] = {"Pts": 0, "PJ": 0}
            tabla[loc]["PJ"] += 1
            tabla[vis]["PJ"] += 1
            if res == "L": tabla[loc]["Pts"] += 3
            elif res == "V": tabla[vis]["Pts"] += 3
            else:
                tabla[loc]["Pts"] += 1
                tabla[vis]["Pts"] += 1
        
        df_tabla = pd.DataFrame.from_dict(tabla, orient="index").sort_values(by=["Pts"], ascending=False).reset_index()
        df_tabla = df_tabla.rename(columns={"index": "Equipo"})
        df_tabla.index = df_tabla.index + 1
        st.dataframe(df_tabla, use_container_width=True)

except FileNotFoundError:
    st.error("❌ No se encontró el archivo de datos. Asegurate de correr el robot en GitHub Actions primero.")
